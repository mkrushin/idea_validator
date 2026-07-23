import os
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from models import IdeaRequest, ReviewRequest, ReviewResponse, WaitlistRequest, TrackRequest
from db import init_db, save_idea, save_review, get_reviews, get_idea, save_waitlist_email, save_event, count_events_today, count_ideas_today, get_stats
from claude_api import analyze_idea_stream

app = FastAPI(title="Idea Validator")

@app.on_event("startup")
def startup():
    """Инициализация БД при запуске"""
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Pydantic кладёт в detail список объектов, а фронт ждёт строку и печатает [object Object].
    Приводим к одной понятной фразе."""
    err = (exc.errors() or [{}])[0]
    ctx = err.get("ctx", {})
    kind = err.get("type")
    if kind == "string_too_short":
        msg = f"Слишком короткий текст: минимум {ctx.get('min_length', '?')} символов"
    elif kind == "string_too_long":
        msg = f"Слишком длинный текст: максимум {ctx.get('max_length', '?')} символов"
    elif kind == "string_pattern_mismatch":
        msg = "Неверный формат email"
    else:
        msg = "Проверьте введённые данные"
    return JSONResponse(status_code=422, content={"detail": msg})


BASE_DIR = Path(__file__).resolve().parent.parent

DAILY_GLOBAL_LIMIT = 150   # анализов/сутки на всех
DAILY_SESSION_LIMIT = 5    # анализов/сутки на session_id

@app.get("/")
async def root():
    """Главная страница"""
    html_path = BASE_DIR / "frontend" / "templates" / "index.html"
    try:
        if not html_path.exists():
            raise HTTPException(status_code=500, detail=f"index.html не найден: {html_path}")
        return FileResponse(str(html_path), media_type="text/html")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e} (path={html_path})")

@app.post("/api/analyze")
async def analyze(request: IdeaRequest):
    """Анализировать идею через Claude (с дневными лимитами расхода)."""
    idea_text = request.idea.strip()
    if len(idea_text) < 50:
        raise HTTPException(status_code=400, detail="Идея должна быть минимум 50 символов")

    # Safeguards: проверяем ДО вызова API, чтобы не тратить деньги
    # Глобальный кап считаем по ideas (все анализы, вкл. бессессионные); /stats.analyses_today считает analysis_run (только сессионные) — числа могут расходиться.
    if count_ideas_today() >= DAILY_GLOBAL_LIMIT:
        raise HTTPException(status_code=429, detail="Лимит анализов на сегодня исчерпан. Зайдите завтра.")
    if request.session_id and count_events_today("analysis_run", request.session_id) >= DAILY_SESSION_LIMIT:
        raise HTTPException(status_code=429, detail="Вы использовали лимит анализов на сегодня. Зайдите завтра.")

    idea_id = save_idea(idea_text)

    def generate():
        # Стримим текст по мере генерации — иначе ~60-секундный ответ отваливается
        # по idle-таймауту браузера/прокси. idea_id уходит в заголовке X-Idea-Id.
        for chunk in analyze_idea_stream(idea_text):
            yield chunk
        # Стрим дошёл до конца — серверное событие активации/счётчик расхода
        if request.session_id:
            save_event(request.session_id, "analysis_run", {"idea_id": idea_id})

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Idea-Id": str(idea_id),
            "X-Accel-Buffering": "no",   # не буферизировать на прокси
            "Cache-Control": "no-cache",
        },
    )

@app.post("/api/track")
async def track_event(request: TrackRequest):
    """Записать анонимное событие аналитики (visit / cta_click)."""
    save_event(request.session_id, request.event_type, request.meta)
    return {"ok": True}

@app.get("/api/reviews")
async def get_all_reviews(idea_id: int = None, limit: int = 10):
    """Получить все отзывы или отзывы для конкретной идеи"""
    try:
        reviews = get_reviews(idea_id=idea_id, limit=limit)
        return [
            ReviewResponse(
                id=r["id"],
                idea_id=r["idea_id"],
                text=r["review_text"],
                rating=r["rating"],
                created_at=r["created_at"]
            )
            for r in reviews
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения отзывов: {str(e)}")

@app.post("/api/reviews")
async def create_review(request: ReviewRequest):
    """Создать отзыв"""
    try:
        if len(request.text) < 10:
            raise HTTPException(status_code=400, detail="Отзыв должен быть минимум 10 символов")

        idea = get_idea(request.idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Идея не найдена")

        review_id = save_review(request.idea_id, request.text, request.rating)

        return {
            "id": review_id,
            "idea_id": request.idea_id,
            "text": request.text,
            "rating": request.rating
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения отзыва: {str(e)}")

@app.post("/api/waitlist")
async def join_waitlist(request: WaitlistRequest):
    """Fake-door: сохранить email + записать событие email_submit."""
    is_new = save_waitlist_email(request.email.strip().lower(), request.session_id)
    if request.session_id:
        save_event(request.session_id, "email_submit", {"email_new": is_new})
    return {"ok": True, "already_joined": not is_new}


@app.get("/stats")
async def stats(token: str = ""):
    """Агрегаты эксперимента. Доступ по секретному токену из env STATS_TOKEN."""
    expected = os.getenv("STATS_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Stats не сконфигурированы (нет STATS_TOKEN)")
    if token != expected:
        raise HTTPException(status_code=403, detail="Неверный токен")
    return get_stats()


@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    """Раздача статических файлов"""
    static_path = BASE_DIR / "frontend" / "static" / file_path
    if static_path.exists():
        return FileResponse(str(static_path))
    raise HTTPException(status_code=404, detail="Файл не найден")
