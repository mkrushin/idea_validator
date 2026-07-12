# 🚀 Деплой Idea Validator

Пошаговые инструкции для развёртывания на Railway (рекомендуется) или Render.

---

## 📋 Что нужно перед деплоем

- ✅ Git инициализирован (уже готово)
- ✅ GitHub аккаунт
- ✅ Railway.app или Render.com аккаунт
- ✅ ANTHROPIC_API_KEY (от https://console.anthropic.com)

---

## 🔧 Вариант A: Railway (рекомендуется)

Railway имеет лучший DX для FastAPI приложений.

### Шаг 1: Подключить репо к GitHub

```bash
# Создать пустой репо на GitHub.com
# https://github.com/new
# Название: idea-validator
# Visibility: Public (или Private, если хочешь)

# Добавить remote
git remote add origin https://github.com/YOUR_USERNAME/idea-validator.git

# Переименовать ветку (если нужно)
git branch -M main

# Запушить
git push -u origin main
```

### Шаг 2: Создать Railway проект

1. Перейди на https://railway.app
2. Нажми **New Project** → **Deploy from GitHub**
3. Авторизуй GitHub и выбери репо `idea-validator`
4. Railway автоматически detectит FastAPI приложение

### Шаг 3: Установить переменные окружения

В Railway dashboard:
1. Перейди в **Variables** вкладку
2. Добавь переменные:
   ```
   ANTHROPIC_API_KEY = sk-ant-...
   RAILWAY_STATIC_URL = /static
   ```

### Шаг 4: Проверить Procfile (опционально)

Railway должен автоматически запустить:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Если не запустит автоматически, создай `Procfile`:
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Шаг 5: Деплой

1. Railway автоматически detectит git push
2. Дождись, пока скончится деплой
3. Получишь URL типа `idea-validator-prod.up.railway.app`

**Готово!** 🎉

---

## 🔧 Вариант B: Render.com

Render имеет бесплатный tier, но может спать после 15 мин неактивности.

### Шаг 1: Подключить GitHub

1. Перейди на https://render.com
2. Нажми **New +** → **Web Service**
3. Выбери **Deploy an existing repository from GitHub**
4. Авторизуй и выбери репо

### Шаг 2: Настроить сервис

- **Name:** idea-validator
- **Environment:** Python 3
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Шаг 3: Добавить Environment Variables

```
ANTHROPIC_API_KEY = sk-ant-...
```

### Шаг 4: Деплой

Нажми **Deploy** и жди.

**URL:** `idea-validator.onrender.com`

---

## 🧪 Проверить деплой

После деплоя (любой вариант):

```bash
# Проверить главную страницу
curl https://your-app-url.railway.app

# Проверить API
curl -X POST https://your-app-url.railway.app/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"idea": "Приложение для трекинга растений с AI-подсказками по уходу за растениями"}'
```

Если ответ приходит, всё работает! 🎉

---

## 📊 Мониторинг

### Railway
- Logs: Dashboard → **Logs** таб
- Metrics: Dashboard → **Monitoring** таб

### Render
- Logs: Service page → **Logs** таб
- Status: https://status.render.com

---

## 🔄 Обновления после деплоя

Если ты внесёшь изменения локально:

```bash
git add .
git commit -m "fix: update description"
git push origin main
```

Railway/Render автоматически передеплоят изменения! 🚀

---

## 🐛 Troubleshooting

### "Application failed to start"
Проверь:
- requirements.txt имеет все зависимости
- ANTHROPIC_API_KEY установлена
- Порт использует `$PORT` переменную

### "ModuleNotFoundError: No module named 'fastapi'"
Убедись, что requirements.txt запускается перед стартом.

### "Database locked"
SQLite на heroku не работает хорошо. Рекомендация:
- Используй PostgreSQL (Railway поддерживает)
- Или переключись на в-памяти DB для MVP

---

## 📱 Дополнительно

### Custom домен

**Railway:**
1. Перейди в **Environment** настройки
2. Добавь custom domain в **Domains** секции

**Render:**
1. Service Settings → **Custom Domains**
2. Добавь домен и CNAME record

### SSL/TLS

Оба (Railway и Render) автоматически генерируют SSL сертификаты 🔒

---

## 🎯 Итоговый checklist

- [ ] GitHub репо создан
- [ ] Git инициализирован локально
- [ ] Railway/Render аккаунт создан
- [ ] ANTHROPIC_API_KEY получен
- [ ] Переменные окружения установлены
- [ ] Деплой выполнен
- [ ] URL работает и доступен
- [ ] API endpoints отвечают
- [ ] Темный режим отображается (если браузер использует dark mode)

---

**Версия:** 1.0  
**Дата:** 12 июля 2026
