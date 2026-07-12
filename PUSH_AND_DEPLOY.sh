#!/bin/bash
# Idea Validator: Push на GitHub и деплой на Railway
# Выполни эти команды в терминале

set -e

echo "🚀 Idea Validator - Push & Deploy"
echo "=================================="
echo ""

# Шаг 1: Проверить статус git
echo "✓ Проверяю git статус..."
git status

echo ""
echo "📋 ШАГИ ДЛЯ ДЕПЛОЯ:"
echo "=================================="
echo ""

echo "1️⃣  СОЗДАЙ GITHUB РЕПО"
echo "   - Перейди на https://github.com/new"
echo "   - Создай репо: idea-validator"
echo "   - Скопируй HTTPS URL"
echo ""

echo "2️⃣  ЗАПУСТИ ЭТИ КОМАНДЫ:"
echo ""
echo "   # Добавь remote (замени URL на твой)"
echo "   git remote add origin https://github.com/YOUR_USERNAME/idea-validator.git"
echo ""
echo "   # Переименуй ветку если нужно"
echo "   git branch -M main"
echo ""
echo "   # Запушь код на GitHub"
echo "   git push -u origin main"
echo ""

echo "3️⃣  СОЗДАЙ RAILWAY ПРОЕКТ"
echo "   - Перейди на https://railway.app"
echo "   - Нажми: New Project → Deploy from GitHub"
echo "   - Выбери: idea-validator репо"
echo "   - Railway автоматически detectит FastAPI"
echo ""

echo "4️⃣  УСТАНОВИ ENVIRONMENT VARIABLES в Railway:"
echo ""
echo "   ANTHROPIC_API_KEY = sk-ant-YOUR_KEY_HERE"
echo ""
echo "   (Получи ключ на https://console.anthropic.com)"
echo ""

echo "5️⃣  ДОЖДИСЬ ДЕПЛОЯ И ПОЛУЧИ URL"
echo "   - Railway выполнит деплой автоматически"
echo "   - Получишь URL вроде: idea-validator-prod.up.railway.app"
echo "   - Готово! 🎉"
echo ""

echo "6️⃣  ПРОВЕРЬ ЧТО РАБОТАЕТ:"
echo ""
echo "   curl https://YOUR_RAILWAY_URL/"
echo ""
echo "   # Должен вернуть HTML страничку"
echo ""

echo "📊 СТАТУС ПРОЕКТА:"
echo "=================================="
git log --oneline | head -5
echo ""
echo "📁 Структура готова к деплою:"
ls -lh backend/ frontend/ *.md .gitignore 2>/dev/null | grep -E '\.py$|\.html$|\.css$|\.md$|\.gitignore'
echo ""
echo "✅ Проект готов к production!"
echo ""
