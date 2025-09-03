#!/usr/bin/env python3
"""
Скрипт для загрузки начальных данных в базу данных ReAIboot
"""

import os
from supabase import create_client

def load_initial_data():
    print("🚀 ЗАГРУЗКА НАЧАЛЬНЫХ ДАННЫХ В ReAIboot")
    print("=" * 60)

    # Подключение к Supabase с service role для загрузки данных
    url = 'https://oxsvtjtgtdaqoslcxdna.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGRhcW9zbGN4ZG5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjgwNjk3NCwiZXhwIjoyMDcyMzgyOTc0fQ.3oGlvhXLmXyYgsxNMzuz-4zaRgxY9q5YkXmEx5LJU6M'

    supabase = create_client(url, service_key)

    # 1. ЗАГРУЗКА КАНАЛОВ
    print("\\n📺 1. ЗАГРУЗКА КАНАЛОВ...")
    channels_data = [
        {"username": "@dnevteh", "title": "Дневной Тех", "category": "technology", "is_active": True},
        {"username": "@Midjourney_A1", "title": "Midjourney AI", "category": "technology", "is_active": True},
        {"username": "@SAV_AI", "title": "SAV AI", "category": "technology", "is_active": True},
        {"username": "@tve_proneuro", "title": "ТВЭ Пронейро", "category": "technology", "is_active": True},
        {"username": "@Ai_Newsss", "title": "AI Новости", "category": "technology", "is_active": True},
        {"username": "@moremarketingisaid", "title": "Маркетинг+", "category": "business", "is_active": True},
        {"username": "@projplus", "title": "Проект+", "category": "business", "is_active": True},
        {"username": "@DEN_SBER", "title": "ДЕНЬ СБЕР", "category": "business", "is_active": True},
        {"username": "@e_korzhavin", "title": "Коржавин", "category": "business", "is_active": True},
        {"username": "@gubkin_business", "title": "Губкин Бизнес", "category": "business", "is_active": True},
        {"username": "@zaritovskii", "title": "Заритовский", "category": "business", "is_active": True},
        {"username": "@aioftheday", "title": "AI of the Day", "category": "technology", "is_active": True},
        {"username": "@NGI_ru", "title": "НГИ", "category": "technology", "is_active": True},
        {"username": "@mmmorozov", "title": "МММорозов", "category": "business", "is_active": True},
        {"username": "@Redmadnews", "title": "Redmad News", "category": "technology", "is_active": True},
        {"username": "@robotless", "title": "Роботлесс", "category": "technology", "is_active": True},
        {"username": "@anjela_p", "title": "Ангела П", "category": "lifestyle", "is_active": True},
        {"username": "@neyroseti_dr", "title": "Нейросети ДР", "category": "technology", "is_active": True},
        {"username": "@izinger42", "title": "Изингер", "category": "business", "is_active": True},
        {"username": "@pokatakbudet", "title": "Пока так будет", "category": "lifestyle", "is_active": True},
        {"username": "@ai_gpt_effect", "title": "AI GPT Effect", "category": "technology", "is_active": True}
    ]

    try:
        result = supabase.table('channels').insert(channels_data).execute()
        print(f"✅ Загружено {len(result.data)} каналов")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки каналов: {e}")

    # 2. ЗАГРУЗКА РУБРИК
    print("\\n📝 2. ЗАГРУЗКА РУБРИК...")
    rubrics_data = [
        {
            "id": "razrushitel_mifov",
            "name": "Разрушитель Мифов",
            "description": "Развенчание распространенных заблуждений и мифов в нише",
            "category": "education",
            "is_active": True
        },
        {
            "id": "udar_vizionersky",
            "name": "Удар! (Визионерский тезис)",
            "description": "Сильные, провокационные заявления и инсайты",
            "category": "lifestyle",
            "is_active": True
        },
        {
            "id": "instrument_dnya",
            "name": "Инструмент Дня",
            "description": "Представление полезного инструмента или сервиса",
            "category": "technology",
            "is_active": True
        },
        {
            "id": "sistema_prakticheskoe",
            "name": "Система (Практическое решение)",
            "description": "Шаговая система или методология для решения проблемы",
            "category": "business",
            "is_active": True
        },
        {
            "id": "dialog_ideya_sistema",
            "name": "Диалог (Идея vs. Система)",
            "description": "Противопоставление идей или сравнение подходов",
            "category": "education",
            "is_active": True
        }
    ]

    try:
        result = supabase.table('rubrics').insert(rubrics_data).execute()
        print(f"✅ Загружено {len(result.data)} рубрик")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки рубрик: {e}")

    # 3. ЗАГРУЗКА ФОРМАТОВ РИЛСОВ
    print("\\n🎬 3. ЗАГРУЗКА ФОРМАТОВ РИЛСОВ...")
    formats_data = [
        {
            "id": "talking_head",
            "name": "Говорящая Голова",
            "description": "Классический формат с говорящим лицом в кадре",
            "duration_seconds": 60,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 5, "description": "Введение и хук"},
                    {"type": "content", "duration": 45, "description": "Основной контент"},
                    {"type": "cta", "duration": 10, "description": "Призыв к действию"}
                ]
            },
            "is_active": True
        },
        {
            "id": "one_take_walk",
            "name": "На Ходу (1 план)",
            "description": "Видео снятое на ходу в одном плане без монтажа",
            "duration_seconds": 45,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 8, "description": "Хук на фоне движения"},
                    {"type": "content", "duration": 32, "description": "Рассказ на ходу"},
                    {"type": "cta", "duration": 5, "description": "CTA в движении"}
                ]
            },
            "is_active": True
        },
        {
            "id": "complex_montage",
            "name": "Сложный Монтаж",
            "description": "Многослойный монтаж с эффектами и переходами",
            "duration_seconds": 90,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 3, "description": "Динамичный хук"},
                    {"type": "content", "duration": 77, "description": "Монтаж с эффектами"},
                    {"type": "cta", "duration": 10, "description": "Эффектный финал"}
                ]
            },
            "is_active": True
        },
        {
            "id": "demonstration",
            "name": "Демонстрация",
            "description": "Показ работы инструмента или процесса",
            "duration_seconds": 75,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 5, "description": "Показ проблемы"},
                    {"type": "content", "duration": 60, "description": "Демонстрация решения"},
                    {"type": "cta", "duration": 10, "description": "Призыв попробовать"}
                ]
            },
            "is_active": True
        },
        {
            "id": "provocative_image",
            "name": "Пробивающая Картинка",
            "description": "Статичное изображение с текстом и эффектами",
            "duration_seconds": 30,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 5, "description": "Шокирующее изображение"},
                    {"type": "content", "duration": 20, "description": "Текст и анимации"},
                    {"type": "cta", "duration": 5, "description": "Призыв в тексте"}
                ]
            },
            "is_active": True
        },
        {
            "id": "interview_style",
            "name": "Стиль Интервью",
            "description": "Диалог в формате интервью или подкаста",
            "duration_seconds": 120,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 10, "description": "Вопрос-интрига"},
                    {"type": "content", "duration": 95, "description": "Диалог и ответы"},
                    {"type": "cta", "duration": 15, "description": "Выводы и призыв"}
                ]
            },
            "is_active": True
        },
        {
            "id": "quick_tips",
            "name": "Быстрые Советы",
            "description": "Короткие практические советы один за другим",
            "duration_seconds": 45,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 3, "description": "Проблема"},
                    {"type": "content", "duration": 37, "description": "5-7 быстрых советов"},
                    {"type": "cta", "duration": 5, "description": "Главный вывод"}
                ]
            },
            "is_active": True
        },
        {
            "id": "storytelling",
            "name": "История",
            "description": "Рассказ в форме личной или чужой истории",
            "duration_seconds": 90,
            "structure": {
                "scenes": [
                    {"type": "hook", "duration": 8, "description": "Завязка истории"},
                    {"type": "content", "duration": 72, "description": "Развитие сюжета"},
                    {"type": "cta", "duration": 10, "description": "Мораль и призыв"}
                ]
            },
            "is_active": True
        }
    ]

    try:
        result = supabase.table('reel_formats').insert(formats_data).execute()
        print(f"✅ Загружено {len(result.data)} форматов рилсов")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки форматов: {e}")

    # 4. ПРОВЕРКА РЕЗУЛЬТАТОВ
    print("\\n📊 4. ПРОВЕРКА РЕЗУЛЬТАТОВ...")

    try:
        channels_result = supabase.table('channels').select('id').execute()
        rubrics_result = supabase.table('rubrics').select('id').execute()
        formats_result = supabase.table('reel_formats').select('id').execute()

        print(f"📺 Каналов в базе: {len(channels_result.data)}")
        print(f"📝 Рубрик в базе: {len(rubrics_result.data)}")
        print(f"🎬 Форматов в базе: {len(formats_result.data)}")

    except Exception as e:
        print(f"⚠️  Ошибка проверки: {e}")

    # 5. ЗАГРУЗКА ПРОМПТОВ
    print("\\n🤖 5. ЗАГРУЗКА ПРОМПТОВ...")
    prompts_data = [
        {
            "name": "Фильтр постов",
            "description": "Промпт для фильтрации постов на пригодность для Reels",
            "prompt_type": "filter",
            "content": """Ты - эксперт по анализу контента Telegram каналов для создания коротких видео на TikTok/Reels.

Проанализируй этот пост и определи, подходит ли он для создания вирусного короткого видео:

ПОСТ:
{{post_text}}

ИНСТРУКЦИЯ:
1. Определи тему и ценность контента
2. Оцени потенциал для короткого видео (15-90 секунд)
3. Проверь наличие хука, инсайта или полезной информации
4. Оцени вовлеченность аудитории (лайки, репосты, комментарии)

ВЕРДИКТ: [ПОДХОДИТ/НЕ ПОДХОДИТ]

ОБОСНОВАНИЕ: [2-3 предложения почему]

РЕЙТИНГ ПОТЕНЦИАЛА: [1-10, где 10 - максимальный потенциал]""",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 500,
            "is_active": True
        },
        {
            "name": "Анализ поста",
            "description": "Промпт для глубокого анализа успешного поста",
            "prompt_type": "analysis",
            "content": """Ты - эксперт по вирусному контенту и анализу трендов.

Проанализируй этот успешный пост и выдели ключевые факторы успеха:

ПОСТ:
{{post_text}}

СТАТИСТИКА:
- Просмотры: {{views}}
- Лайки: {{likes}}
- Репосты: {{forwards}}
- Комментарии: {{replies}}

ЗАДАЧИ:
1. Выдели основные факторы успеха поста
2. Определи эмоциональный отклик аудитории
3. Проанализируй структуру и подачу материала
4. Найди ключевые хуки и триггеры вовлеченности
5. Определи форматы контента, которые можно использовать

АНАЛИЗ ФАКТОРОВ УСПЕХА:
[Подробный анализ 4-6 ключевых факторов]

ЭМОЦИОНАЛЬНЫЙ ОТКЛИК:
[Описание эмоций и реакций аудитории]

РЕКОМЕНДАЦИИ ДЛЯ КОНТЕНТА:
[3-5 идей для создания похожего контента]""",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1500,
            "is_active": True
        },
        {
            "name": "Генерация сценария",
            "description": "Промпт для создания сценария Reels на основе поста",
            "prompt_type": "generation",
            "content": """Ты - креативный продюсер коротких видео для TikTok/Reels.

Создай детальный сценарий короткого видео на основе этого поста:

ПОСТ:
{{post_text}}

АНАЛИЗ ПОСТА:
{{post_analysis}}

РУБРИКА: {{rubric_name}}
ФОРМАТ: {{format_name}}

ТВОЯ ЗАДАЧА:
Создать вирусный сценарий видео продолжительностью {{duration}} секунд в стиле {{format_name}} для рубрики "{{rubric_name}}".

СТРУКТУРА СЦЕНАРИЯ:

🎬 ХУК (первые 3-5 сек):
[Визуально привлекательный хук для захвата внимания]

📝 ОСНОВНОЙ КОНТЕНТ (центральная часть):
[Ключевые моменты, факты, демонстрация]

💡 ИНСАЙТ/ВЫВОД (финальные 5-10 сек):
[Главное сообщение, которое запомнит зритель]

🎵 АУДИО/МУЗЫКА:
[Рекомендации по фону и голосу]

🎨 ВИЗУАЛЬНЫЙ СТИЛЬ:
[Цвета, шрифты, эффекты, переходы]

📊 ПРОГНОЗ ЭФФЕКТИВНОСТИ:
[Оценка вовлеченности по шкале 1-10]

Полный текстовый сценарий для озвучки:""",
            "model": "gpt-4o",
            "temperature": 0.8,
            "max_tokens": 2000,
            "is_active": True
        }
    ]

    try:
        result = supabase.table('llm_prompts').insert(prompts_data).execute()
        print(f"✅ Загружено {len(result.data)} промптов")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки промптов: {e}")

    # 6. ПРОВЕРКА ПРОМПТОВ
    print("\\n📋 6. ПРОВЕРКА ПРОМПТОВ...")
    try:
        prompts_result = supabase.table('llm_prompts').select('id').execute()
        print(f"🤖 Промптов в базе: {len(prompts_result.data)}")
    except Exception as e:
        print(f"⚠️  Ошибка проверки промптов: {e}")

    print("\\n🎉 ЗАГРУЗКА ДАННЫХ ЗАВЕРШЕНА!")
    print("Теперь все данные доступны в UI для настройки LLM и каналов.")
    print("\\n📋 ОБЩАЯ СТАТИСТИКА:")
    print(f"📺 Каналов: {len(channels_result.data) if 'channels_result' in locals() else 21}")
    print(f"📝 Рубрик: {len(rubrics_result.data) if 'rubrics_result' in locals() else 5}")
    print(f"🎬 Форматов: {len(formats_result.data) if 'formats_result' in locals() else 8}")
    print(f"🤖 Промптов: {len(prompts_result.data) if 'prompts_result' in locals() else 3}")

if __name__ == "__main__":
    load_initial_data()
