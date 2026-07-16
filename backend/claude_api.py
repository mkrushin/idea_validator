import os
import sys
from anthropic import Anthropic

try:
    from dotenv import load_dotenv
    # Грузим .env из корня проекта (на уровень выше backend/)
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # На проде (Railway) переменные приходят из окружения, dotenv не нужен

api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not api_key:
    print("WARNING: ANTHROPIC_API_KEY not set", file=sys.stderr)
    api_key = None

client = Anthropic(api_key=api_key) if api_key else None

def load_prompt_template():
    """Загрузить шаблон промпта из файла"""
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "content",
        "analysis_prompt.txt"
    )

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Промпт не найден: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def analyze_idea(idea_text: str) -> str:
    """
    Отправляет идею в Claude для анализа.
    Возвращает структурированный анализ.
    """
    if not client:
        return get_demo_analysis(idea_text)

    prompt_template = load_prompt_template()
    full_prompt = prompt_template.format(idea=idea_text)

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    return message.content[0].text

def get_demo_analysis(idea_text: str) -> str:
    """Demo режим - возвращает пример анализа для тестирования интерфейса"""
    return """### 1. Market Size & Trends
Рынок приложений для ухода за растениями растет со скоростью 15% в год, но это нишевый сегмент.
- За последние 3 года количество загрузок садоводческих приложений выросло с 2M до 8M
- Основной спрос идет от миллениалов (25-40) в городах с высокой стоимостью жизни
- Next step: Проверь статистику AppStore/PlayStore для растение-ориентированных приложений

### 2. Target Customer (Who will actually buy?)
Целевой покупатель - городской миллениал с комнатными растениями, боящийся их убить.
- Тип: "растение-любитель", живет в квартире, имеет 2-5 растений, тратит на них $10-50 в месяц
- Боль: не знает, когда поливать, что подкормить, как спасти засыхающее растение
- Next step: Опрось 20 человек в местных садоводческих пабах или онлайн сообществах

### 3. Pain Points (Real problems they face?)
Проблема актуальна, но решается гугле-картинками и Reddit, не требует приложения.
- Люди ищут "почему сохнет монстера" вместо того, чтобы открыть приложение
- Установка приложения требует больше усилий, чем быстрый гугл-поиск
- Next step: Спроси 10 пользователей, почему они не используют существующие приложения (Planta, GardenTags)

### 4. Solution (Does your idea solve the problem?)
AI-подсказки - хороший угол, но это не уникально. Planta уже это делает.
- Ты предлагаешь: система уведомлений + AI-диагностика листьев
- Но: Planta делает то же самое за $50/год, и у нее 1M+ установок
- Next step: Что ты сможешь сделать лучше или дешевле? Какое конкретное преимущество?

### 5. Competition (Who else is solving this?)
Рынок уже есть, и есть сильные игроки. Это не greenfield.
- Planta ($5/месяц, 1M установок) - полный функционал, большое комьюнити
- GardenTags (бесплатно, монетизирует через маркетплейс) - похожий концепт
- Простые приложения-календари (бесплатно) - ловят людей ценой
- Next step: Установи Planta на неделю и найди 3 конкретные фичи, которых ей не хватает

### 6. MVP Scope (What's the minimum to test?)
MVP за 2 недели - реально. Но вопрос: что ты будешь тестировать?
- Core: загрузить фото растения → AI определит вид → рекомендует поливку (расписание)
- Skip: соцсеть, маркетплейс, вебверсия, темная тема
- Next step: Забей на готовый код, за 3 дня собери MVP на Firebase + GPT-Vision (дешевле, чем Claude)

### 7. Pricing & Business Model (How do you make money?)
Freemium модель работает, но конверсия в платку - проблема.
- Planta: $5/месяц = $10-15 lifetime value среднего пользователя
- Твой план: скорее всего аналогичный или ниже (новый бренд, нет трастa)
- Next step: Поговори с 5-10 платными пользователями Planta - почему они платят?

### 8. Key Risks & Assumptions (What could go wrong?)
Главный риск: монетизация в переполненном нишевом рынке.
- Риск #1: Люди не готовы платить $5/месяц за приложение. Решение: test freemium, look at retention
- Риск #2: AI-диагностика даст неправильный результат и пользователь убьет растение → reputation risk
- Next step: Создай версию без AI, только расписание. Если даже она не конвертирует - вопрос не в AI.

---

## FINAL VERDICT:

Идея имеет право на жизнь, но не как standalone продукт. Рекомендую либо: (1) собрать MVP за $100-200 на Firebase + GPT Vision, протестировать на 50-100 пользователях, либо (2) интегрировать это как фичу в маркетплейс комнатных растений (если у тебя есть еще компоненты бизнеса). Сначала валидируй, что люди вообще открывают приложение для ухода за растениями, когда им нужна помощь."""
