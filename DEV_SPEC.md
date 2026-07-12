# Idea Validator — Developer Spec для MVP (Python)

**Дата:** 2026-07-11  
**Статус:** Готово к разработке  
**Стек:** FastAPI (Python) + SQLite + HTML/JS фронт  
**Цель:** MVP за 2–3 дня, пилот на Трумане

---

## 🎯 Что нужно сделать в первую очередь (MVP Phase 1)

**Цель:** Рабочий сайт, где:
1. Пользователь вводит идею (форма)
2. Нажимает "Анализировать"
3. Получает отчёт из 8 разделов (AI-анализ через Claude)
4. Может оставить отзыв внизу
5. Отзывы видны всем следующим пользователям

**Успех:** Ты сам прошёл через форму → получил отчёт → оставил отзыв → всё работает.

---

## 📦 Архитектура

```
idea-validator/
│
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── requirements.txt      # зависимости (fastapi, uvicorn, anthropic, sqlite3)
│   ├── db.py               # функции работы с SQLite
│   ├── claude_api.py        # интеграция с Claude API
│   └── models.py            # Pydantic schemas (IdeaRequest, ReviewResponse)
│
├── frontend/
│   ├── templates/
│   │   └── index.html       # главная форма + отчёт + отзывы
│   └── static/
│       └── style.css        # базовый стиль (Tailwind или простой CSS)
│
├── data/
│   └── ideas.db            # SQLite база (ideas, reviews таблицы)
│
└── content/
    └── analysis_prompt.txt  # 8-разделный промпт для Claude (уже готов)
```

---

## 🔧 Технические требования

### Backend (FastAPI)

**Зависимости:**
```
fastapi==0.104.0
uvicorn==0.24.0
anthropic==0.7.0
pydantic==2.4.0
python-multipart==0.0.6
```

**API endpoints:**

| Метод | URL | Что делает |
|-------|-----|-----------|
| POST | `/api/analyze` | Принимает идею (JSON: `{"idea": "..."}`) → отправляет Claude → возвращает отчёт |
| GET | `/api/reviews` | Возвращает все отзывы (JSON: `[{id, idea_id, text, rating, created_at}]`) |
| POST | `/api/reviews` | Принимает отзыв (JSON: `{"idea_id": 1, "text": "...", "rating": 5}`) → сохраняет |
| GET | `/` | Возвращает HTML форму (index.html) |

**Детали POST /api/analyze:**

Input:
```json
{
  "idea": "Приложение для отслеживания растений с AI-подсказками"
}
```

Output:
```json
{
  "idea_id": 1,
  "analysis": "## Рынок\n...\n## Целевой покупатель\n...",
  "sections": ["Рынок", "Целевой покупатель", "Боли", "Решение", "Конкуренты", "MVP", "Цена", "Риски"]
}
```

### Frontend (HTML/JS)

**Макет:**
1. Форма вверху: textarea "Опиши идею" (min 50 символов) + кнопка "Анализировать"
2. Loading spinner пока ждём Claude (2–5 сек)
3. Отчёт: 8 секций (каждая как блок H3 + текст)
4. Форма отзыва внизу: текст + рейтинг (1–5 звёзд) + кнопка "Отправить"
5. Список отзывов: последние 10 отзывов, отсортированы по дате (новые вверху)

**JS функционал (минимум):**
- POST к `/api/analyze` при нажатии кнопки
- Отобрази результат красиво
- POST к `/api/reviews` при отправке отзыва
- GET `/api/reviews` при загрузке → покажи список

**Стиль:** Простой, читаемый. Можно Tailwind CDN или простой CSS (без фреймворка).

### БД (SQLite)

**Таблица `ideas`:**
```sql
CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_text TEXT NOT NULL,
    analysis TEXT,  -- результат Claude
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Таблица `reviews`:**
```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    review_text TEXT NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(idea_id) REFERENCES ideas(id)
);
```

---

## 🧠 Claude API интеграция

**Файл:** `backend/claude_api.py`

**Функция:**
```python
def analyze_idea(idea_text: str) -> str:
    """
    Отправляет идею в Claude с 8-разделным промптом.
    Возвращает структурированный анализ (текст, 8 разделов).
    """
    # Читаем промпт из content/analysis_prompt.txt
    # Подставляем идею клиента
    # Отправляем в Claude API (claude-3-5-sonnet-20241022)
    # Возвращаем response.content[0].text
```

**Промпт:** Используешь из `/Users/alexm/vc/idea-validator/content/analysis_prompt.txt` (или пишешь свой из 8 шагов ShipFit: Рынок, Целевой покупатель, Боли, Решение, Конкуренты, MVP, Цена, Риски).

**Rate limiting:** Можешь не делать на пилоте, но учти — API не безлимитный.

---

## 📋 Чек-лист для MVP (Phase 1)

- [ ] Инит проекта: папка `backend/`, `frontend/`, `data/`
- [ ] `requirements.txt` + вирт окружение Python
- [ ] `backend/main.py` с FastAPI и endpoints
- [ ] `backend/db.py` — создание таблиц, функции CRUD
- [ ] `backend/claude_api.py` — интеграция с Claude API
- [ ] `frontend/templates/index.html` — форма + отчёт + отзывы
- [ ] Запуск на `localhost:8000`
- [ ] Протестировал сам: идея → отчёт → отзыв
- [ ] Деплой на Railway или Render (получаешь публичный URL)

---

## 🚀 Как запустить локально (для тебя)

```bash
# Инит
cd /Users/alexm/vc/idea-validator
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Запуск
uvicorn backend.main:app --reload

# Открыть браузер
# http://localhost:8000
```

---

## 📤 Деплой (после MVP работает)

**Вариант A: Railway (рекомендую)**
1. Push код на GitHub
2. Подключи Railway к репо
3. Установи `ANTHROPIC_API_KEY` в Environment
4. Deploy
5. Получаешь публичный URL типа `idea-validator-prod.up.railway.app`

**Вариант B: Render**
1. Аналогично Railway
2. Бесплатный tier, но может спать после 15 мин неактивности

---

## 🔐 Переменные окружения

Нужно установить в `.env` (локально) и в деплое:

```
ANTHROPIC_API_KEY=sk-ant-...  # твой API ключ
DATABASE_URL=sqlite:///data/ideas.db  # путь БД (SQLite)
```

---

## ⚠️ Важные детали

1. **Промпт для Claude:** Используй из `content/analysis_prompt.txt`, где уже описаны 8 разделов. Если файла нет — пишешь свой по мотивам ShipFit.

2. **CORS:** FastAPI должен разрешить запросы с фронта (добавь `CORSMiddleware` или раздавай фронт из `static/`).

3. **Время ответа:** Claude может отвечать 2–5 сек. Покажи spinner или "Думаю..." на фронте.

4. **Валидация:** Идея не меньше 50 символов, отзыв не меньше 10 символов (на фронте + на бэке).

5. **Ошибки:** Если Claude недоступен — показать friendly сообщение, не крашить.

---

## 📚 Ресурсы, которые уже готовы

- **Промпт анализа:** `/Users/alexm/vc/idea-validator/content/analysis_prompt.txt` (если готов, используй; если нет — напиши сам)
- **Спека продукта:** `/Users/alexm/vc/idea-validator/docs/01_PRODUCT_SPEC.md`
- **Ссылка на документы:** `/Users/alexm/vc/idea-validator/docs/`

---

## 🎬 Следующие фазы (после MVP)

**Фаза 2:** Запуск на Трумане (когда MVP готов и работает)  
**Фаза 3:** Интеграция живого фидбека из Reddit/Telegram (дальше)  
**Фаза 4:** Платный переход (когда будут отзывы)

---

## 📝 Как передать задачу

Скопируй этот документ целиком в новый чат Claude Code и скажи:

> "Вот спека для разработки. Напиши код сейчас. Стартуй с инита проекта и главного файла."

Всё остальное (вопросы, уточнения) — Claude разберётся по спеке.

---

**Версия:** 1.0 (от 2026-07-11)  
**Автор:** Alex (первичная спека) → Claude (разработка)
