import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from models import IdeaRequest, AnalysisResponse, ReviewRequest, ReviewResponse
from db import init_db, save_idea, save_review, get_reviews, get_idea
from claude_api import analyze_idea

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

BASE_DIR = Path(__file__).resolve().parent.parent

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

@app.get("/debug")
async def debug():
    """Диагностика путей в контейнере (временный эндпоинт)"""
    frontend = BASE_DIR / "frontend"
    info = {
        "base_dir": str(BASE_DIR),
        "cwd": os.getcwd(),
        "resolved_file": str(Path(__file__).resolve()),
        "index_exists": (frontend / "templates" / "index.html").exists(),
        "style_exists": (frontend / "static" / "style.css").exists(),
        "base_dir_contents": sorted(os.listdir(BASE_DIR)) if BASE_DIR.exists() else "BASE_DIR НЕ существует",
        "frontend_contents": sorted(os.listdir(frontend)) if frontend.exists() else "frontend/ НЕ существует",
    }
    return info

@app.post("/api/analyze")
async def analyze(request: IdeaRequest):
    """Анализировать идею через Claude"""
    try:
        idea_text = request.idea.strip()

        if len(idea_text) < 50:
            raise HTTPException(status_code=400, detail="Идея должна быть минимум 50 символов")

        idea_id = save_idea(idea_text)

        analysis_text = analyze_idea(idea_text)

        sections = [
            "Market Size & Trends",
            "Target Customer",
            "Pain Points",
            "Solution",
            "Competition",
            "MVP Scope",
            "Pricing & Business Model",
            "Key Risks & Assumptions"
        ]

        return AnalysisResponse(
            idea_id=idea_id,
            analysis=analysis_text,
            sections=sections
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

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

@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    """Раздача статических файлов"""
    static_path = BASE_DIR / "frontend" / "static" / file_path
    if static_path.exists():
        return FileResponse(str(static_path))
    raise HTTPException(status_code=404, detail="Файл не найден")
