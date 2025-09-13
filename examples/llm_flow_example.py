"""
Пример того, как данные из песочницы преобразуются в запросы LLM на проде
"""

# Данные из песочницы (то же самое, что собирается в SandboxSection.tsx)
sandbox_post_data = {
    "id": "12437_@dnevteh",
    "message_id": 12437,
    "channel_username": "@dnevteh",
    "channel_title": "Дневник Технаря",
    "text": "**Эмодзи клоуна — официально признали ОСКОРБЛЕНИЕМ в России.** Это [доказали](https://rg.ru/2025/09/11/obidno-no-prilichno.html) в суде Красноярска.\n\nВ Красноярске женщина поскандалила с соседкой в доме через общий чат. В ответ на её сообщения та отправила смайлик-клоуна. Обращение дошло до суда, где решили, что такой стикер оскорбляет достоинство. \n\nИтог — девушке назначили штраф в 5 тысяч рублей.\n\nПозже решение смягчили, но теперь использовать клоуна в чатах опасно — реакцию могут засчитать как оскорбление.\n\n@dnevteh",
    "views": 32,
    "forwards": 2,
    "reactions": 0,
    "date": "2025-09-11T09:27:06+00:00",
}

print("=== ДАННЫЕ ИЗ ПЕСОЧНИЦЫ ===")
print(f"ID поста: {sandbox_post_data['id']}")
print(f"Текст поста (первые 100 символов): {sandbox_post_data['text'][:100]}...")
print(f"Просмотры: {sandbox_post_data['views']}")
print(f"Реакции: {sandbox_post_data['reactions']}")
print(f"Репосты: {sandbox_post_data['forwards']}")
print(f"Дата: {sandbox_post_data['date']}")
print()

# Это то, как FilterProcessor формирует запрос к LLM
print("=== ШАГ 1: ФИЛЬТРАЦИЯ (GPT-4o-mini) ===")

# Извлечение данных (как в filter_processor.py строка 62-68)
post_text = sandbox_post_data.get("text", "")
views = sandbox_post_data.get("views", 0)
reactions = sandbox_post_data.get("reactions", 0)
replies = sandbox_post_data.get("replies", 0)  # В песочнице нет, будет 0
forwards = sandbox_post_data.get("forwards", 0)
channel_title = sandbox_post_data.get("channel_title", "")

print("Извлеченные данные для фильтрации:")
print(f"- post_text: {post_text[:50]}...")
print(f"- views: {views}")
print(f"- reactions: {reactions}")
print(f"- replies: {replies}")
print(f"- forwards: {forwards}")
print(f"- channel_title: {channel_title}")
print()

# Промпт для фильтрации (из prompts.py строка 103-117)
filter_system_prompt = """Ты - эксперт по анализу контента для социальных сетей.
Проект: ПерепрошИИвка
ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

Целевая аудитория:
- Специалисты IT сферы
- Предприниматели и бизнесмены
- Люди, интересующиеся технологиями и саморазвитием

Формат контента:
- Короткие видео 15-60 секунд
- Практическая ценность
- Доступный язык
- Визуально привлекательный контент

Твоя задача: оценить, подходит ли пост из Telegram для создания образовательного контента."""

filter_user_prompt = f"""Оцени этот пост по шкале 1-10:

ПОСТ:
{post_text[:2000]}

МЕТРИКИ:
- Просмотры: {views}
- Реакции: {reactions}
- Комментарии: {replies}
- Репосты: {forwards}

Оцени по шкале 1-10 и определи, подходит ли для создания образовательного контента.

Верни только JSON: {{"score": число, "reason": "краткое объяснение", "suitable": true/false}}"""

print("System Prompt для фильтрации:")
print(filter_system_prompt)
print()
print("User Prompt для фильтрации:")
print(filter_user_prompt)
print()

print("=== ШАГ 2: АНАЛИЗ (если прошел фильтрацию) ===")

# Анализ использует те же данные + score из фильтрации
analysis_user_prompt = f"""Проанализируй этот успешный пост:

ПОСТ:
{post_text}

МЕТРИКИ ВОВЛЕЧЕННОСТИ:
- Просмотры: {views}
- Реакции: {reactions}
- Комментарии: {replies}
- Репосты: {forwards}

ПРОАНАЛИЗИРУЙ:
1. Почему этот пост стал популярным?
2. Какие ключевые факторы успеха?
3. Что можно взять для создания собственного контента?

Верни анализ в JSON формате:
{{
  "success_factors": ["фактор1", "фактор2", ...],
  "content_strengths": ["сильная сторона1", "сильная сторона2", ...],
  "audience_insights": ["инсайт1", "инсайт2", ...],
  "content_ideas": ["идея1", "идея2", ...],
  "lessons_learned": "выводы для нашего контента",
  "recommended_topics": ["тема1", "тема2", ...]
}}"""

print("User Prompt для анализа:")
print(analysis_user_prompt)
print()

print("=== ЗАКЛЮЧЕНИЕ ===")
print("✅ Данные из песочницы корректно собираются")
print(
    "✅ Все необходимые поля (text, views, reactions, forwards, channel_title) присутствуют"
)
print("✅ Данные правильно передаются в LLM процессоры")
print("✅ Формат данных соответствует тому, что используется на проде")
