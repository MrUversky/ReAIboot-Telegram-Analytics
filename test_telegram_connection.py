#!/usr/bin/env python3
"""
Тест подключения к Telegram API.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.telegram_client import TelegramAnalyzer
from src.app.settings import settings

async def test_telegram_connection():
    """Тестирует подключение к Telegram."""

    print("🔍 Тестирование подключения к Telegram API")
    print("=" * 50)

    try:
        # Создаем анализатор
        analyzer = TelegramAnalyzer()
        print("✅ TelegramAnalyzer создан успешно")

        # Проверяем сессию
        session_file = analyzer.client.session.filename
        print(f"📁 Файл сессии: {session_file}")

        import os
        if os.path.exists(session_file):
            print("✅ Файл сессии существует")
        else:
            print("❌ Файл сессии не найден")

        # Пытаемся подключиться
        print("🔄 Подключение к Telegram...")
        await analyzer.connect()
        print("✅ Подключение успешно")

        # Проверяем авторизацию
        me = await analyzer.client.get_me()
        print(f"👤 Авторизован как: {me.first_name} (@{me.username})")

        # Проверяем канал
        print("🔍 Проверка канала @dnevteh...")
        channel_info = await analyzer.get_channel_info("@dnevteh")
        if "error" in channel_info:
            print(f"❌ Ошибка при получении канала: {channel_info['error']}")
        else:
            print(f"✅ Канал найден: {channel_info.get('title', 'Без названия')}")
            print(f"📊 Подписчиков: {channel_info.get('participants_count', 0)}")

        # Пробуем получить посты за разные периоды
        print("📄 Получение постов за последний день...")
        messages, _ = await analyzer.get_messages("@dnevteh", days=1, limit=3)
        print(f"📊 Найдено постов за 1 день: {len(messages)}")

        if messages:
            for i, msg in enumerate(messages[:3]):
                print(f"  {i+1}. {msg.get('text_preview', 'Без текста')[:100]}...")
        else:
            print("📄 Попробуем за последние 7 дней...")
            messages, _ = await analyzer.get_messages("@dnevteh", days=7, limit=3)
            print(f"📊 Найдено постов за 7 дней: {len(messages)}")

            if messages:
                for i, msg in enumerate(messages[:3]):
                    print(f"  {i+1}. {msg.get('text_preview', 'Без текста')[:100]}...")
            else:
                print("📄 Попробуем за последние 30 дней...")
                messages, _ = await analyzer.get_messages("@dnevteh", days=30, limit=3)
                print(f"📊 Найдено постов за 30 дней: {len(messages)}")

                if messages:
                    for i, msg in enumerate(messages[:3]):
                        print(f"  {i+1}. {msg.get('text_preview', 'Без текста')[:100]}...")
                else:
                    print("❌ Посты не найдены даже за 30 дней")

        await analyzer.disconnect()
        print("✅ Тест завершен успешно")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
