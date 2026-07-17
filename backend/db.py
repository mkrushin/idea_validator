import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE_URL = "data/ideas.db"

def get_db_path():
    # На проде (Railway) указывай DATABASE_PATH на примонтированный Volume,
    # чтобы отзывы не сбрасывались при редеплое. Локально — дефолт в data/.
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        return env_path
    return os.path.join(os.path.dirname(__file__), "..", DATABASE_URL)

def init_db():
    """Инициализация БД и создание таблиц"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_text TEXT NOT NULL,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(idea_id) REFERENCES ideas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Миграция: добавить session_id, если таблица waitlist создана раньше без него
    cursor.execute("PRAGMA table_info(waitlist)")
    waitlist_cols = [row[1] for row in cursor.fetchall()]
    if "session_id" not in waitlist_cols:
        cursor.execute("ALTER TABLE waitlist ADD COLUMN session_id TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            meta TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_idea(idea_text: str, analysis: Optional[str] = None) -> int:
    """Сохранить идею в БД"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ideas (idea_text, analysis) VALUES (?, ?)",
        (idea_text, analysis)
    )

    conn.commit()
    idea_id = cursor.lastrowid
    conn.close()

    return idea_id

def get_idea(idea_id: int) -> Optional[Dict[str, Any]]:
    """Получить идею по ID"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def save_review(idea_id: int, review_text: str, rating: int) -> int:
    """Сохранить отзыв"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO reviews (idea_id, review_text, rating) VALUES (?, ?, ?)",
        (idea_id, review_text, rating)
    )

    conn.commit()
    review_id = cursor.lastrowid
    conn.close()

    return review_id

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


def get_reviews(idea_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Получить отзывы (все или для конкретной идеи)"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if idea_id:
        cursor.execute(
            "SELECT * FROM reviews WHERE idea_id = ? ORDER BY created_at DESC LIMIT ?",
            (idea_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM reviews ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


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


def count_ideas_today() -> int:
    """Сколько анализов (строк в ideas) создано сегодня (UTC) — для глобального лимита."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ideas WHERE created_at >= date('now')")
    n = cursor.fetchone()[0]
    conn.close()
    return n


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
