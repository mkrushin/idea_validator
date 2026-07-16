# Эксперимент A «Валидируем спрос» — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Дёшево проверить спрос на idea-validator через fake-door оффер «$7», анонимную аналитику событий и живой AI-анализ, не строя реальную оплату и реальные данные.

**Architecture:** Расширяем существующий FastAPI + SQLite + ванильный фронт. Добавляем таблицы `events` и `session_id` в `waitlist`; эндпоинты `POST /api/track` (visit/cta_click) и `GET /stats`; `POST /api/analyze` и `POST /api/waitlist` расширяем под session_id, safeguards и серверную запись событий (`analysis_run`, `email_submit`). На фронте — анонимный session_id в localStorage, трекинг, fake-door оффер-блок под вердиктом; старый общий блок «Хочешь больше?» удаляем. Живой вызов Claude готовим в коде, включаем ручным чек-листом перед запуском.

**Tech Stack:** Python 3.12, FastAPI, SQLite (stdlib `sqlite3`), Pydantic v2, anthropic SDK, ванильный HTML/CSS/JS. Тесты: pytest + FastAPI TestClient (httpx). Деплой: Railway (`railway up --detach`).

## Global Constraints

- **Стек не меняем** — только текущий FastAPI + SQLite + ванильный фронт (spec §4).
- **Анонимность:** `session_id` — случайный UUID в localStorage, никакого PII; events хранит только session_id/event_type/meta/created_at (spec §4.1).
- **Ветка:** вся работа в отдельной git-ветке `experiment-a-validate-demand`, НЕ в main (память проекта).
- **Demo остаётся дефолтом:** при отсутствии `ANTHROPIC_API_KEY` `claude_api.py` возвращает заглушку. Живой AI включается ручным чек-листом (решение пользователя: «код сейчас, включить перед запуском»).
- **Параметры живого вызова (spec §4.3, сверено со скиллом claude-api):** модель `claude-sonnet-5`, `max_tokens=6000`, `thinking={"type": "disabled"}` (для Sonnet 5 omission = adaptive ON, поэтому выключаем явно), `output_config={"effort": "medium"}`.
- **Safeguards (решение пользователя):** глобально 150 анализов/сутки, 5 анализов/session_id/сутки, usage-cap на ключе Anthropic $10 (в Console, ручной шаг).
- **Метрики:** `GET /stats?token=…`, токен из env `STATS_TOKEN`; отдаёт JSON-агрегаты без сырых email.
- **Порог значимости эксперимента:** ~100 уникальных визитов; пороги гипотез 50% / 10% / 5% (spec §2) — считаются из `/stats`.
- **Deviation от spec §4.1 (осознанно):** `analysis_run` и `email_submit` пишет БЭКЕНД (server-authoritative — надёжнее и переиспользуется для safeguard-счётчика), фронт шлёт через `/api/track` только `visit` и `cta_click`. `/api/track` принимает только эти два типа.
- **Даты в SQLite — UTC:** `created_at` = `CURRENT_TIMESTAMP`; «сегодня» = `created_at >= date('now')`.
- **Весь пользовательский текст оффера — по-русски, прогнать через skill `humanize`** (без AI-маркеров).

---

### Task 1: Ветка + baseline-коммит незакоммиченного

**Files:**
- Modify: рабочее дерево (git), без правок кода.

**Interfaces:**
- Produces: ветка `experiment-a-validate-demand` с чистым baseline, от которого идут TDD-коммиты.

Сейчас в `main` незакоммичены: финальный промпт `content/analysis_prompt.txt`, спека и план в `docs/superpowers/`, а также ранняя waitlist-заготовка (`backend/*.py`, `frontend/*`). Их нужно перенести на ветку и зафиксировать как отправную точку.

- [ ] **Step 1: Убедиться, что мы в репозитории и на main**

Run: `cd /Users/alexm/vc/idea-validator && git status`
Expected: `On branch main`, список modified/untracked как в контексте сессии.

- [ ] **Step 2: Создать и переключиться на ветку эксперимента**

```bash
cd /Users/alexm/vc/idea-validator
git checkout -b experiment-a-validate-demand
```
Expected: `Switched to a new branch 'experiment-a-validate-demand'`

- [ ] **Step 3: Закоммитить baseline (промпт + спека + план + ранняя waitlist-заготовка)**

```bash
cd /Users/alexm/vc/idea-validator
git add backend/ content/ frontend/ docs/superpowers/
git commit -m "chore: baseline for experiment A (final prompt, spec, plan, prior waitlist scaffolding)"
```
Expected: коммит создан. Проверить: `git status` — рабочее дерево чистое (кроме прочих untracked docs, которые не трогаем).

Примечание: `docs/05_VALIDATION_PLAN_SPEC.md`, `06_ROADMAP_REVISED.md`, `07_LANDING_REDESIGN_SPEC.md` — не относятся к этому эксперименту напрямую; добавлять их в коммит НЕ обязательно (оставить untracked).

---

### Task 2: Таблица `events`, функции БД, эндпоинт `POST /api/track`

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/models.py`
- Modify: `backend/main.py`
- Create: `tests/conftest.py`
- Create: `tests/test_events.py`
- Modify: `requirements.txt` (dev-заметка) — тест-зависимости ставятся локально, не в прод.

**Interfaces:**
- Produces:
  - `db.save_event(session_id: str, event_type: str, meta: dict | None = None) -> int`
  - `db.count_events_today(event_type: str, session_id: str | None = None) -> int`
  - Pydantic `TrackRequest{ session_id: str, event_type: Literal["visit","cta_click"], meta: dict | None }`
  - `POST /api/track` → `{"ok": true}`
  - Таблица `events(id, session_id TEXT NOT NULL, event_type TEXT NOT NULL, meta TEXT, created_at TIMESTAMP)`

- [ ] **Step 1: Установить тест-зависимости локально**

```bash
cd /Users/alexm/vc/idea-validator && ./venv/bin/pip install pytest httpx
```
Expected: успешная установка pytest и httpx. (В прод `requirements.txt` НЕ добавляем — тест-зависимости не нужны на Railway.)

- [ ] **Step 2: Написать conftest с временной БД**

Create `tests/conftest.py`:
```python
import os
import sys
import tempfile
import importlib
import pytest
from fastapi.testclient import TestClient

# backend/ импортируется как top-level модули (db, main, claude_api) —
# так же, как это делает сам backend/main.py через sys.path.insert.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


@pytest.fixture
def client(monkeypatch):
    """TestClient с изолированной временной БД, гарантированно demo-режим."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_PATH", path)
    monkeypatch.setenv("STATS_TOKEN", "test-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    import db
    import claude_api
    import main
    importlib.reload(db)
    importlib.reload(main)
    # Форсим demo независимо от локального .env (иначе эндпоинт-тесты пойдут в живой API)
    monkeypatch.setattr(claude_api, "client", None, raising=False)

    with TestClient(main.app) as c:
        yield c

    os.remove(path)
```

- [ ] **Step 3: Написать падающий тест на `/api/track` и счётчик событий**

Create `tests/test_events.py`:
```python
def test_track_visit_writes_event(client):
    r = client.post("/api/track", json={"session_id": "s1", "event_type": "visit"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_track_rejects_unknown_event_type(client):
    r = client.post("/api/track", json={"session_id": "s1", "event_type": "analysis_run"})
    assert r.status_code == 422  # analysis_run пишет только бэкенд


def test_count_events_today(client):
    client.post("/api/track", json={"session_id": "s1", "event_type": "visit"})
    client.post("/api/track", json={"session_id": "s2", "event_type": "visit"})
    client.post("/api/track", json={"session_id": "s1", "event_type": "cta_click"})

    import db
    assert db.count_events_today("visit") == 2
    assert db.count_events_today("cta_click") == 1
    assert db.count_events_today("visit", session_id="s1") == 1
```

- [ ] **Step 4: Прогнать тесты — убедиться, что падают**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_events.py -v`
Expected: FAIL (нет `/api/track`, нет `save_event`/`count_events_today`).

- [ ] **Step 5: Добавить таблицу `events` в `init_db` (backend/db.py)**

В `init_db()`, после блока создания таблицы `waitlist`, перед `conn.commit()`, добавить:
```python
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            meta TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

- [ ] **Step 6: Добавить `save_event` и `count_events_today` в backend/db.py**

Добавить `import json` вверху файла (рядом с существующими импортами), затем в конец файла:
```python
def save_event(session_id: str, event_type: str, meta: Optional[Dict[str, Any]] = None) -> int:
    """Записать анонимное событие аналитики."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    meta_json = json.dumps(meta, ensure_ascii=False) if meta else None
    cursor.execute(
        "INSERT INTO events (session_id, event_type, meta) VALUES (?, ?, ?)",
        (session_id, event_type, meta_json),
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id


def count_events_today(event_type: str, session_id: Optional[str] = None) -> int:
    """Сколько событий данного типа записано сегодня (UTC). Опц. по session_id."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if session_id:
        cursor.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE event_type = ? AND session_id = ? AND created_at >= date('now')",
            (event_type, session_id),
        )
    else:
        cursor.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE event_type = ? AND created_at >= date('now')",
            (event_type,),
        )
    n = cursor.fetchone()[0]
    conn.close()
    return n
```

- [ ] **Step 7: Добавить модель `TrackRequest` в backend/models.py**

В начало файла к импортам добавить `Literal`:
```python
from typing import Optional, Literal
```
В конец файла:
```python
class TrackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    event_type: Literal["visit", "cta_click"]
    meta: Optional[dict] = None
```

- [ ] **Step 8: Добавить эндпоинт `/api/track` в backend/main.py**

В импорт из `models` добавить `TrackRequest`; в импорт из `db` добавить `save_event, count_events_today`. Затем добавить эндпоинт (например, после `/api/analyze`):
```python
@app.post("/api/track")
async def track_event(request: TrackRequest):
    """Записать анонимное событие аналитики (visit / cta_click)."""
    save_event(request.session_id, request.event_type, request.meta)
    return {"ok": True}
```

- [ ] **Step 9: Прогнать тесты — убедиться, что проходят**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_events.py -v`
Expected: PASS (3 теста).

- [ ] **Step 10: Проверить синтаксис и закоммитить**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/python -m py_compile backend/db.py backend/models.py backend/main.py
git add backend/db.py backend/models.py backend/main.py tests/
git commit -m "feat: events table + /api/track endpoint (anonymous analytics)"
```
Expected: py_compile без ошибок, коммит создан.

---

### Task 3: `session_id` в `waitlist`, `/api/waitlist` пишет `email_submit`

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/models.py`
- Modify: `backend/main.py`
- Create: `tests/test_waitlist.py`

**Interfaces:**
- Consumes: `db.save_event` (Task 2).
- Produces:
  - `db.save_waitlist_email(email: str, session_id: str | None = None) -> bool`
  - `WaitlistRequest{ email: str, session_id: str | None }` (расширение существующей модели)
  - `POST /api/waitlist` пишет строку в `waitlist` (с session_id) + событие `email_submit`; возвращает `{"ok": true, "already_joined": bool}`
  - Миграция: колонка `session_id` в таблице `waitlist`

- [ ] **Step 1: Написать падающий тест**

Create `tests/test_waitlist.py`:
```python
def test_waitlist_saves_email_and_logs_event(client):
    r = client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s1"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["already_joined"] is False

    import db
    assert db.count_events_today("email_submit", session_id="s1") == 1


def test_waitlist_duplicate_email_still_logs_event(client):
    client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s1"})
    r = client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s2"})
    assert r.status_code == 200
    assert r.json()["already_joined"] is True

    import db
    # Событие пишется при каждом submit (сигнал намерения), даже для дубля email
    assert db.count_events_today("email_submit") == 2


def test_waitlist_accepts_missing_session_id(client):
    r = client.post("/api/waitlist", json={"email": "c@d.com"})
    assert r.status_code == 200
```

- [ ] **Step 2: Прогнать — убедиться, что падают**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_waitlist.py -v`
Expected: FAIL (нет session_id в модели/БД, событие не пишется).

- [ ] **Step 3: Миграция таблицы `waitlist` в `init_db` (backend/db.py)**

Сразу после блока `CREATE TABLE IF NOT EXISTS waitlist (...)` добавить идемпотентную миграцию:
```python
    # Миграция: добавить session_id, если таблица waitlist создана раньше без него
    cursor.execute("PRAGMA table_info(waitlist)")
    waitlist_cols = [row[1] for row in cursor.fetchall()]
    if "session_id" not in waitlist_cols:
        cursor.execute("ALTER TABLE waitlist ADD COLUMN session_id TEXT")
```
(Оставить `email TEXT UNIQUE NOT NULL` как есть — дубль email вернёт `already_joined`.)

- [ ] **Step 4: Обновить `save_waitlist_email` (backend/db.py)**

Заменить существующую функцию на:
```python
def save_waitlist_email(email: str, session_id: Optional[str] = None) -> bool:
    """Сохранить email в waitlist. Возвращает False, если email уже есть."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO waitlist (email, session_id) VALUES (?, ?)",
            (email, session_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # email уже в списке
    finally:
        conn.close()
```

- [ ] **Step 5: Расширить `WaitlistRequest` (backend/models.py)**

Заменить модель на:
```python
class WaitlistRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    session_id: Optional[str] = Field(None, max_length=64)
```

- [ ] **Step 6: Обновить эндпоинт `/api/waitlist` (backend/main.py)**

Заменить тело `join_waitlist` на:
```python
@app.post("/api/waitlist")
async def join_waitlist(request: WaitlistRequest):
    """Fake-door: сохранить email + записать событие email_submit."""
    is_new = save_waitlist_email(request.email.strip().lower(), request.session_id)
    if request.session_id:
        save_event(request.session_id, "email_submit", {"email_new": is_new})
    return {"ok": True, "already_joined": not is_new}
```

- [ ] **Step 7: Прогнать тесты (весь набор) — убедиться, что проходят**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest -v`
Expected: PASS (Task 2 + Task 3 тесты).

- [ ] **Step 8: py_compile и коммит**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/python -m py_compile backend/db.py backend/models.py backend/main.py
git add backend/ tests/test_waitlist.py
git commit -m "feat: waitlist session_id + email_submit event (fake-door wiring)"
```
Expected: без ошибок, коммит создан.

---

### Task 4: `/api/analyze` — session_id, safeguards, серверный `analysis_run`

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/db.py`
- Modify: `backend/main.py`
- Create: `tests/test_analyze_guards.py`

**Interfaces:**
- Consumes: `db.save_event`, `db.count_events_today`.
- Produces:
  - `IdeaRequest{ idea: str, session_id: str | None }` (расширение)
  - Константы в `main.py`: `DAILY_GLOBAL_LIMIT = 150`, `DAILY_SESSION_LIMIT = 5`
  - `/api/analyze`: проверка лимитов ДО вызова Claude → при превышении `429` с мягким текстом; на успех — запись события `analysis_run` (с session_id).

- [ ] **Step 1: Написать падающие тесты (лимиты + запись analysis_run)**

Create `tests/test_analyze_guards.py`:
```python
IDEA = "Мобильное приложение для трекинга привычек с ИИ-напоминаниями и аналитикой прогресса пользователя"


def test_analyze_writes_analysis_run_event(client):
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"})
    assert r.status_code == 200
    import db
    assert db.count_events_today("analysis_run", session_id="s1") == 1


def test_analyze_per_session_limit(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "DAILY_SESSION_LIMIT", 2)
    for _ in range(2):
        assert client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"}).status_code == 200
    # 3-й запрос той же сессии — мягкий отказ, без вызова анализа
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"})
    assert r.status_code == 429


def test_analyze_global_limit(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "DAILY_GLOBAL_LIMIT", 1)
    assert client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"}).status_code == 200
    # другая сессия, но глобальный лимit исчерпан
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s2"})
    assert r.status_code == 429


def test_analyze_works_without_session_id(client):
    r = client.post("/api/analyze", json={"idea": IDEA})
    assert r.status_code == 200
```

- [ ] **Step 2: Прогнать — убедиться, что падают**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_analyze_guards.py -v`
Expected: FAIL (нет лимитов, нет записи analysis_run, IdeaRequest не принимает session_id).

- [ ] **Step 3: Расширить `IdeaRequest` (backend/models.py)**

```python
class IdeaRequest(BaseModel):
    idea: str = Field(..., min_length=50, max_length=5000)
    session_id: Optional[str] = Field(None, max_length=64)
```

- [ ] **Step 4: Добавить лимиты и переписать `/api/analyze` (backend/main.py)**

Убедиться, что в импорте из `db` есть `save_event, count_events_today`. Рядом с `BASE_DIR` добавить константы:
```python
DAILY_GLOBAL_LIMIT = 150   # анализов/сутки на всех
DAILY_SESSION_LIMIT = 5    # анализов/сутки на session_id
```
Заменить функцию `analyze` на:
```python
@app.post("/api/analyze")
async def analyze(request: IdeaRequest):
    """Анализировать идею через Claude (с дневными лимитами расхода)."""
    idea_text = request.idea.strip()
    if len(idea_text) < 50:
        raise HTTPException(status_code=400, detail="Идея должна быть минимум 50 символов")

    # Safeguards: проверяем ДО вызова API, чтобы не тратить деньги
    if count_events_today("analysis_run") >= DAILY_GLOBAL_LIMIT:
        raise HTTPException(status_code=429, detail="Лимит анализов на сегодня исчерпан. Зайдите завтра.")
    if request.session_id and count_events_today("analysis_run", request.session_id) >= DAILY_SESSION_LIMIT:
        raise HTTPException(status_code=429, detail="Вы использовали лимит анализов на сегодня. Зайдите завтра.")

    try:
        idea_id = save_idea(idea_text)
        analysis_text = analyze_idea(idea_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

    # Успех — записываем серверное событие (метрика активации + счётчик расхода)
    if request.session_id:
        save_event(request.session_id, "analysis_run", {"idea_id": idea_id})

    sections = [
        "Market Size & Trends", "Target Customer", "Pain Points", "Solution",
        "Competition", "MVP Scope", "Pricing & Business Model", "Key Risks & Assumptions",
    ]
    return AnalysisResponse(idea_id=idea_id, analysis=analysis_text, sections=sections)
```

Примечание: `429`-исключения (лимит) не должны перехватываться `except Exception` — поэтому проверки лимитов вынесены ДО `try`, а внутри `try` есть `except HTTPException: raise`.

- [ ] **Step 5: Прогнать все тесты**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest -v`
Expected: PASS (все задачи 2–4).

- [ ] **Step 6: py_compile и коммит**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/python -m py_compile backend/models.py backend/main.py
git add backend/ tests/test_analyze_guards.py
git commit -m "feat: analyze session_id + daily safeguards + server-side analysis_run event"
```
Expected: без ошибок, коммит создан.

---

### Task 5: Живой AI в `claude_api.py` (параметры вызова)

**Files:**
- Modify: `backend/claude_api.py`
- Create: `tests/test_claude_api.py`

**Interfaces:**
- Produces: `analyze_idea` при наличии клиента вызывает `client.messages.create` с `model="claude-sonnet-5"`, `max_tokens=6000`, `thinking={"type": "disabled"}`, `output_config={"effort": "medium"}`. При отсутствии клиента — demo (без изменений).

Живой вызов НЕ запускается сейчас (ключ добавляется в Task 8). Здесь только готовим и тестируем формирование запроса через подставной клиент.

- [ ] **Step 1: Написать падающий тест на параметры вызова (через fake-клиент)**

Create `tests/test_claude_api.py`:
```python
import types
import claude_api as capi


def test_demo_when_no_client(monkeypatch):
    monkeypatch.setattr(capi, "client", None)
    out = capi.analyze_idea("любая идея длиннее пятидесяти символов для проверки демо-режима сейчас")
    assert isinstance(out, str) and len(out) > 0


def test_live_call_params(monkeypatch):
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(content=[types.SimpleNamespace(text="LIVE-OK")])

    fake_client = types.SimpleNamespace(messages=FakeMessages())
    monkeypatch.setattr(capi, "client", fake_client)

    out = capi.analyze_idea("Сервис доставки здоровой еды по подписке для офисов в крупных городах России")
    assert out == "LIVE-OK"
    assert captured["model"] == "claude-sonnet-5"
    assert captured["max_tokens"] == 6000
    assert captured["thinking"] == {"type": "disabled"}
    assert captured["output_config"] == {"effort": "medium"}
    # промпт должен содержать текст идеи
    assert "доставки здоровой еды" in captured["messages"][0]["content"]
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_claude_api.py -v`
Expected: `test_live_call_params` FAIL (сейчас нет max_tokens=6000/thinking/effort), `test_demo_when_no_client` PASS.

- [ ] **Step 3: Обновить `analyze_idea` (backend/claude_api.py)**

Заменить блок вызова `client.messages.create(...)` на:
```python
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=6000,
        thinking={"type": "disabled"},
        output_config={"effort": "medium"},
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )
```
(Остальное — загрузка промпта, `.format(idea=...)`, `return message.content[0].text` — без изменений.)

- [ ] **Step 4: Прогнать — убедиться, что проходит**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_claude_api.py -v`
Expected: PASS (оба теста).

- [ ] **Step 5: Проверить, что в промпте нет «лишних» фигурных скобок (кроме `{idea}`)**

Run: `cd /Users/alexm/vc/idea-validator && grep -n "{" content/analysis_prompt.txt`
Expected: единственное совпадение — `{idea}` (иначе `.format()` даст KeyError при живом вызове). Если найдутся другие `{`/`}` — экранировать их как `{{`/`}}`. (На момент написания плана — только `{idea}`.)

- [ ] **Step 6: py_compile и коммит**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/python -m py_compile backend/claude_api.py
git add backend/claude_api.py tests/test_claude_api.py
git commit -m "feat: live Claude call params (max_tokens=6000, thinking off, effort medium)"
```
Expected: без ошибок, коммит создан.

---

### Task 6: `GET /stats` с токеном + агрегаты метрик

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/main.py`
- Create: `tests/test_stats.py`

**Interfaces:**
- Consumes: `db.save_event`, `db.save_waitlist_email`.
- Produces:
  - `db.get_stats() -> dict` с ключами: `visits`, `analyses`, `activation_pct`, `return_7d_pct`, `cta_ctr_pct`, `emails`, `analyses_today`.
  - `GET /stats?token=…` → JSON `get_stats()`; при неверном/отсутствующем токене → `403`; при неустановленном `STATS_TOKEN` → `503`.

Метрики (по spec §2): активация = уник. сессии с `analysis_run` / уник. сессии с `visit`; CTR = уник. сессии с `cta_click` / уник. сессии с `analysis_run`; возврат-7д = сессии с визитами в ≥2 разных календарных дня за 7 дней / уник. сессии с `visit`.

- [ ] **Step 1: Написать падающий тест**

Create `tests/test_stats.py`:
```python
def _seed(client):
    # 4 визита (s1..s4), 2 анализа (s1,s2), 1 клик (s1), 1 email (s1)
    for s in ["s1", "s2", "s3", "s4"]:
        client.post("/api/track", json={"session_id": s, "event_type": "visit"})
    idea = "Платформа онлайн-курсов по программированию с менторами и проверкой домашних заданий на практике"
    client.post("/api/analyze", json={"idea": idea, "session_id": "s1"})
    client.post("/api/analyze", json={"idea": idea, "session_id": "s2"})
    client.post("/api/track", json={"session_id": "s1", "event_type": "cta_click"})
    client.post("/api/waitlist", json={"email": "s1@x.com", "session_id": "s1"})


def test_stats_requires_token(client):
    assert client.get("/stats").status_code == 403
    assert client.get("/stats?token=wrong").status_code == 403


def test_stats_aggregates(client):
    _seed(client)
    r = client.get("/stats?token=test-token")
    assert r.status_code == 200
    d = r.json()
    assert d["visits"] == 4
    assert d["analyses"] == 2
    assert d["activation_pct"] == 50.0   # 2/4
    assert d["cta_ctr_pct"] == 50.0      # 1/2
    assert d["emails"] == 1
    assert "return_7d_pct" in d
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest tests/test_stats.py -v`
Expected: FAIL (нет `/stats`, нет `get_stats`).

- [ ] **Step 3: Добавить `get_stats` в backend/db.py**

В конец файла:
```python
def get_stats() -> Dict[str, Any]:
    """Агрегаты эксперимента для решения по дереву гипотез (без сырых email)."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def uniq(event_type: str) -> int:
        cursor.execute(
            "SELECT COUNT(DISTINCT session_id) FROM events WHERE event_type = ?",
            (event_type,),
        )
        return cursor.fetchone()[0]

    visits = uniq("visit")
    analyses = uniq("analysis_run")
    cta = uniq("cta_click")

    cursor.execute("SELECT COUNT(*) FROM waitlist")
    emails = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT session_id FROM events "
        "  WHERE event_type = 'visit' AND created_at >= date('now', '-7 days') "
        "  GROUP BY session_id HAVING COUNT(DISTINCT date(created_at)) >= 2"
        ")"
    )
    returns_7d = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM events WHERE event_type = 'analysis_run' AND created_at >= date('now')"
    )
    analyses_today = cursor.fetchone()[0]
    conn.close()

    def pct(num: int, den: int) -> float:
        return round(100.0 * num / den, 1) if den else 0.0

    return {
        "visits": visits,
        "analyses": analyses,
        "activation_pct": pct(analyses, visits),
        "return_7d_pct": pct(returns_7d, visits),
        "cta_ctr_pct": pct(cta, analyses),
        "emails": emails,
        "analyses_today": analyses_today,
    }
```

- [ ] **Step 4: Добавить эндпоинт `/stats` в backend/main.py**

В импорт из `db` добавить `get_stats`. Добавить (например, перед `/static`):
```python
@app.get("/stats")
async def stats(token: str = ""):
    """Агрегаты эксперимента. Доступ по секретному токену из env STATS_TOKEN."""
    expected = os.getenv("STATS_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Stats не сконфигурированы (нет STATS_TOKEN)")
    if token != expected:
        raise HTTPException(status_code=403, detail="Неверный токен")
    return get_stats()
```
(`os` уже импортирован в main.py.)

- [ ] **Step 5: Прогнать все тесты**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest -v`
Expected: PASS (все задачи 2–6).

- [ ] **Step 6: py_compile и коммит**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/python -m py_compile backend/db.py backend/main.py
git add backend/ tests/test_stats.py
git commit -m "feat: GET /stats with token-gated experiment metrics"
```
Expected: без ошибок, коммит создан.

---

### Task 7: Фронт — session_id, трекинг, fake-door оффер; удалить старый waitlist-блок

**Files:**
- Modify: `frontend/templates/index.html`
- Modify: `frontend/static/style.css`

**Interfaces:**
- Consumes: `POST /api/track` (visit, cta_click), `POST /api/analyze` (session_id), `POST /api/waitlist` (email, session_id).
- Produces: рабочий UX — визит трекается, анализ шлёт session_id, под вердиктом появляется оффер-блок с fake-door email-формой; старый общий блок «Хочешь больше?» удалён.

- [ ] **Step 1: Удалить старый блок `#waitlistCard`**

В `frontend/templates/index.html` удалить весь блок `<!-- WAITLIST -->` … `</div>` (строки блока `<div class="card" id="waitlistCard">` целиком, ~строки 140–150).

- [ ] **Step 2: Добавить оффер-блок под карточкой анализа**

Сразу ПОСЛЕ `<!-- РЕЗУЛЬТАТЫ АНАЛИЗА -->` `<div class="card hidden" id="analysisCard">…</div>` вставить:
```html
        <!-- ОФФЕР (fake-door) -->
        <div class="card hidden" id="offerCard">
            <div class="offer-badge">Следующий шаг</div>
            <h2>Данные + план проверки — <span class="offer-price">$7</span></h2>
            <p class="offer-lead">Разбор показал, что стоит проверить. Дальше — не гадать, а собрать факты и поговорить с людьми. За $7 даю пакет под твою идею:</p>
            <div class="offer-cols">
                <div class="offer-col">
                    <h3>Живые данные из сети</h3>
                    <ul>
                        <li>Кто уже это делает и сколько берёт</li>
                        <li>На что жалуются их клиенты в реальных отзывах</li>
                        <li>Где сидит твоя аудитория — конкретные сообщества</li>
                    </ul>
                </div>
                <div class="offer-col">
                    <h3>План проверки</h3>
                    <ul>
                        <li>Кого спросить и 5 вопросов по The Mom Test</li>
                        <li>Готовый шаблон, чтобы позвать на разговор</li>
                        <li>Пороги «идти / стоп» и чеклист-трекер</li>
                    </ul>
                </div>
            </div>
            <button type="button" class="button" id="offerCtaBtn">Получить план за $7</button>

            <div class="offer-email hidden" id="offerEmailBlock">
                <p class="offer-email-note">Фича в разработке — денег пока не беру. Оставь email: дам знать первым и первым дам бесплатно.</p>
                <form id="offerEmailForm" class="waitlist-form">
                    <input type="email" id="offerEmail" name="email" placeholder="you@example.com" required>
                    <button type="submit" class="button" id="offerEmailBtn">Уведомить меня</button>
                </form>
                <div class="error" id="offerEmailError"></div>
                <div class="success-message" id="offerEmailSuccess">✓ Готово! Напишу первым, как будет готово.</div>
            </div>
        </div>
```
> Текст оффера — черновик. Перед коммитом прогнать через skill `humanize` (убрать AI-маркеры), сохранив смысл и структуру.

- [ ] **Step 3: Добавить session_id + трекинг визита в inline-скрипт**

В `<script>`, в самое начало (перед `let currentIdeaId = null;`) добавить:
```javascript
        // Анонимный session_id (UUID в localStorage) — только для метрик, без PII
        function getSessionId() {
            let sid = localStorage.getItem('iv_session_id');
            if (!sid) {
                sid = (crypto.randomUUID && crypto.randomUUID()) ||
                      ('s-' + Date.now() + '-' + Math.random().toString(36).slice(2));
                localStorage.setItem('iv_session_id', sid);
            }
            return sid;
        }
        const SESSION_ID = getSessionId();

        function track(eventType, meta) {
            fetch('/api/track', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: SESSION_ID, event_type: eventType, meta: meta || null })
            }).catch(() => {});  // аналитика не должна ломать UX
        }

        track('visit');
```

- [ ] **Step 4: Прокинуть session_id в `/api/analyze`**

В обработчике `ideaForm submit`, в `body: JSON.stringify({ idea })` заменить на:
```javascript
                    body: JSON.stringify({ idea, session_id: SESSION_ID })
```
В том же обработчике, ПОСЛЕ успешного `displayAnalysis(data.analysis);` добавить показ оффера:
```javascript
                document.getElementById('offerCard').classList.remove('hidden');
```
(Событие `analysis_run` пишет бэкенд — на фронте его слать НЕ нужно.)

- [ ] **Step 5: Добавить логику fake-door (cta_click + email)**

В конец `<script>` (после блока чипов-примеров; блок старого waitlist уже удалён) добавить:
```javascript
        // Fake-door оффер
        const offerCtaBtn = document.getElementById('offerCtaBtn');
        const offerEmailBlock = document.getElementById('offerEmailBlock');
        const offerEmailForm = document.getElementById('offerEmailForm');
        const offerEmail = document.getElementById('offerEmail');
        const offerEmailError = document.getElementById('offerEmailError');
        const offerEmailSuccess = document.getElementById('offerEmailSuccess');

        offerCtaBtn.addEventListener('click', () => {
            track('cta_click', { idea_id: currentIdeaId });
            offerEmailBlock.classList.remove('hidden');
            offerEmail.focus();
        });

        offerEmailForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideError(offerEmailError);
            const email = offerEmail.value.trim();
            try {
                const response = await fetch('/api/waitlist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, session_id: SESSION_ID })
                });
                if (!response.ok) throw new Error('Проверь, что email введён правильно');
                const data = await response.json();
                showSuccess(data.already_joined ? '✓ Ты уже в списке — спасибо!' : '✓ Готово! Напишу первым, как будет готово.', offerEmailSuccess);
                offerEmail.value = '';
                setTimeout(() => hideSuccess(offerEmailSuccess), 4000);
            } catch (err) {
                showError(`Ошибка: ${err.message}`, offerEmailError);
            }
        });
```

- [ ] **Step 6: Добавить стили оффера в frontend/static/style.css**

Добавить в конец файла (использует существующие CSS-переменные проекта; при их отсутствии — заменить на реальные имена из :root):
```css
/* Fake-door оффер */
.offer-badge { display: inline-block; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--accent, #6c5ce7); margin-bottom: 8px; }
.offer-price { color: var(--accent, #6c5ce7); }
.offer-lead { color: var(--text-secondary, #555); margin-bottom: 20px; }
.offer-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.offer-col h3 { font-size: 1rem; margin-bottom: 8px; }
.offer-col ul { margin: 0; padding-left: 18px; color: var(--text-secondary, #555); }
.offer-col li { margin-bottom: 6px; }
.offer-email { margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border, #eee); }
.offer-email-note { color: var(--text-secondary, #555); margin-bottom: 12px; }
@media (max-width: 600px) { .offer-cols { grid-template-columns: 1fr; } }
```

- [ ] **Step 7: Прогнать оффер через humanize и вычитать тексты**

Invoke skill `humanize` на текстах оффер-блока (заголовок, lead, пункты, email-note, success-сообщения). Заменить в HTML на очеловеченные версии. Перечитать глазами — нет AI-маркеров, честный тон fake-door.

- [ ] **Step 8: Ручная проверка в браузере**

```bash
cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m uvicorn backend.main:app --port 8010
```
Открыть http://localhost:8010, затем проверить (demo-режим, без ключа):
1. Ввести идею → «Анализировать» → появляется разбор + оффер-блок под ним.
2. Клик «Получить план за $7» → появляется email-форма.
3. Ввести email → «Уведомить меня» → success-сообщение.
4. В другой вкладке: `curl "http://localhost:8010/stats?token=$STATS_TOKEN"` (или временно экспортировать `STATS_TOKEN=local`) → JSON с `visits>=1`, `analyses>=1`, `cta_ctr_pct`, `emails>=1`.
5. Старого блока «Хочешь больше?» на странице НЕТ.

Остановить сервер (Ctrl+C).

- [ ] **Step 9: Коммит**

```bash
cd /Users/alexm/vc/idea-validator
git add frontend/
git commit -m "feat: front-end session tracking + fake-door offer block; remove old waitlist block"
```
Expected: коммит создан.

---

### Task 8: Ручной чек-лист включения живого AI + деплой (не код)

**Files:**
- Modify: `requirements.txt` (пин свежей версии anthropic)
- Modify: `backend/main.py` (только если смоук-тест выявит несовместимость параметров — фолбэк)

**Interfaces:**
- Consumes: весь предыдущий код.
- Produces: прод на Railway с живым AI, безопасными лимитами, `/stats`.

Это действия пользователя + деплой. Выполняется, когда пользователь готов потратить ~$5 и запускать эксперимент.

- [ ] **Step 1: Обновить SDK anthropic и запинить версию**

```bash
cd /Users/alexm/vc/idea-validator
./venv/bin/pip install -U anthropic
./venv/bin/pip show anthropic | grep -i version
```
В `requirements.txt` заменить строку `anthropic>=0.7.0` на `anthropic>=<установленная_версия>` (взять из вывода выше), чтобы Railway поставил SDK с поддержкой `output_config`/`thinking`.

- [ ] **Step 2 (пользователь): Пополнить баланс Anthropic (~$5) и выставить usage-cap $10**

В Anthropic Console → Billing: пополнить ~$5. В Settings → Limits (usage cap): выставить жёсткий потолок расхода **$10** на ключ. Это hard-backstop поверх дневных лимитов приложения.

- [ ] **Step 3: Локальный смоук-тест живого вызова**

Временно экспортировать реальный ключ и прогнать один живой анализ:
```bash
cd /Users/alexm/vc/idea-validator
ANTHROPIC_API_KEY="<real_key>" ./venv/bin/python -c "
import backend.claude_api as c
print(c.analyze_idea('Сервис аренды инструментов между соседями через мобильное приложение с доставкой и страховкой'))
"
```
Expected: приходит развёрнутый разбор (начинается с `---`, 8 разделов + вердикт), без ошибки `400`.
Если `400` про `output_config`/`thinking`/`effort` — свериться со скиллом `claude-api` и поправить параметры в `backend/claude_api.py` (например, убрать `output_config`, если конкретная версия SDK/модель его не принимает вместе с disabled thinking), затем повторить смоук-тест и обновить `tests/test_claude_api.py`.

- [ ] **Step 4 (пользователь): Прописать переменные в Railway**

В Railway → проект `serene-sparkle` → сервис `idea_validator` → Variables:
- `ANTHROPIC_API_KEY` = реальный ключ
- `STATS_TOKEN` = случайная длинная строка (сгенерировать: `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`)
- Проверить, что `DATABASE_PATH` указывает внутрь `/app/data` (Volume) — иначе события/waitlist сбросятся при редеплое.

- [ ] **Step 5: Коммит требований и деплой**

```bash
cd /Users/alexm/vc/idea-validator
git add requirements.txt backend/claude_api.py tests/
git commit -m "chore: pin anthropic SDK; enable live AI"
railway link -p serene-sparkle
railway up --detach
```
Expected: билд 1–3 мин, деплой успешен. (git push НЕ триггерит автодеплой — только `railway up`.)

- [ ] **Step 6: Прод-проверка**

```bash
# заменить <PROD_URL> и <STATS_TOKEN> на реальные
curl -s "<PROD_URL>/stats?token=<STATS_TOKEN>"
```
Expected: `200` с JSON-агрегатами.
Открыть прод в браузере: прогнать один анализ (живой разбор, не demo), проверить оффер-блок и email-форму, затем `/stats` показывает `analyses>=1`.

---

### Task 9: Финальная проверка

**Files:** нет правок.

- [ ] **Step 1: Весь набор тестов зелёный**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m pytest -v`
Expected: PASS, все тесты задач 2–6.

- [ ] **Step 2: py_compile всех изменённых модулей**

Run: `cd /Users/alexm/vc/idea-validator && ./venv/bin/python -m py_compile backend/db.py backend/models.py backend/main.py backend/claude_api.py`
Expected: без ошибок.

- [ ] **Step 3: История коммитов на ветке**

Run: `cd /Users/alexm/vc/idea-validator && git log --oneline experiment-a-validate-demand -12`
Expected: baseline + по коммиту на задачу; ветка НЕ смёржена в main (решение по мержу — отдельно, после сбора метрик).

- [ ] **Step 4: Чек-лист самопроверки (перечислить пользователю)**

Подтвердить: таблицы `events`/`waitlist(session_id)` ✓, эндпоинты `/api/track`,`/api/waitlist`,`/api/analyze(session_id)`,`/stats` ✓, safeguards 150/5 ✓, живой AI-параметры ✓, fake-door оффер + удалён старый блок ✓, нет хардкода секретов (ключ/STATS_TOKEN в env) ✓, тесты зелёные ✓.

---

## Что НЕ строим (spec §3, только при 🟢)

Реальная оплата (Stripe/Lemon Squeezy), контент «Плана валидации», данные через веб-поиск (направление B), continuous-фичи/аккаунты/история, редизайн лендинга, сложные дашборды. Также параллельно (не код, действия пользователя): 5–10 живых разговоров по The Mom Test (spec §5.1) и Reddit-пост (spec §5).
