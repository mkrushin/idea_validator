# 💡 Idea Validator — MVP

Веб-приложение для анализа стартап-идей с помощью AI.

## ✅ Статус

**MVP готов к использованию!**

Протестировано:
- ✓ Форма ввода идеи работает
- ✓ Анализ 8 разделов отображается
- ✓ Оставление отзывов работает
- ✓ Рейтинг 1-5 звёзд работает
- ✓ Список отзывов сохраняется в БД SQLite
- ✓ Интерфейс красивый и отзывчивый

## 🚀 Как запустить локально

### Предварительные требования
- Python 3.8+
- pip

### Установка

```bash
# Перейти в папку проекта
cd /Users/alexm/vc/idea-validator

# Создать виртуальное окружение (если еще не создано)
python3 -m venv venv

# Активировать окружение
source venv/bin/activate

# Установить зависимости
pip install -r backend/requirements.txt
```

### Запуск

```bash
# Активировать окружение
source venv/bin/activate

# Запустить сервер
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Откроешь браузер на **http://localhost:8000**

## 🔐 API Ключ (опционально)

### Для анализа с реальным Claude API:

1. Получи API ключ на https://console.anthropic.com
2. Установи переменную окружения:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Сервер автоматически будет использовать реальный API вместо демо-режима

### Для демо-тестирования:
- Просто запусти без ключа — приложение использует встроенный пример анализа

## 📁 Структура проекта

```
idea-validator/
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── db.py               # SQLite работа
│   ├── claude_api.py        # Интеграция с Claude
│   ├── models.py            # Pydantic схемы
│   └── requirements.txt      # Зависимости
├── frontend/
│   ├── templates/
│   │   └── index.html       # Главная страница
│   └── static/
│       └── style.css        # Стили
├── data/
│   └── ideas.db            # SQLite база
├── content/
│   └── analysis_prompt.txt  # Промпт для Claude
└── venv/                    # Виртуальное окружение Python
```

## 📊 API Endpoints

| Метод | URL | Что делает |
|-------|-----|-----------|
| GET | `/` | Главная страница (HTML) |
| POST | `/api/analyze` | Анализировать идею (принимает JSON) |
| GET | `/api/reviews` | Получить отзывы |
| POST | `/api/reviews` | Сохранить отзыв |

### Пример запроса анализа

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"idea": "Приложение для отслеживания растений с AI-подсказками по уходу за растениями"}'
```

### Ответ

```json
{
  "idea_id": 1,
  "analysis": "### 1. Market Size & Trends\n...",
  "sections": ["Market Size & Trends", "Target Customer", ...]
}
```

## 🗄️ БД Schema

### Таблица `ideas`
```sql
CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_text TEXT NOT NULL,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `reviews`
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

## 🚀 Деплой

### На Railway (рекомендуется)

1. Push код на GitHub
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Idea Validator MVP"
   git push -u origin main
   ```

2. Подключи Railway к репо (https://railway.app)

3. Установи переменную окружения в Railway:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

4. Deploy!

Получишь публичный URL типа `idea-validator-prod.up.railway.app`

### На Render (альтернатива)

Аналогично Railway, бесплатный tier доступен.

## 📝 Что дальше (Phase 2+)

- [ ] Запуск на Трумане (пилот)
- [ ] Интеграция с Reddit/Telegram для реал-тайм фидбека
- [ ] Платная версия с доп функциями
- [ ] Улучшенная аналитика результатов

## 🛠️ Стек

- **Backend:** FastAPI, Python 3.14, SQLite
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **AI:** Anthropic Claude API (claude-3-5-sonnet-20241022)
- **Deploy:** Railway или Render

## 📄 Лицензия

MIT
