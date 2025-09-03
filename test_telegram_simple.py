#!/usr/bin/env python3

import asyncio
import os
import sys

# Добавляем src в путь
sys.path.insert(0, 'src')

# Устанавливаем переменные окружения
os.environ['TELEGRAM_API_ID'] = '22287918'
os.environ['TELEGRAM_API_HASH'] = 'bfb2c1383584f7bf73ec27f1341d1891'
os.environ['TELEGRAM_SESSION'] = 'telegram_session'

async def test_telegram():
    try:
        print("🔄 Тестирую подключение к Telegram...")
        from src.app.telegram_client import TelegramAnalyzer

        analyzer = TelegramAnalyzer()
        print("✅ TelegramAnalyzer создан")

        await analyzer.connect()
        print("✅ Подключение к Telegram успешно!")

        # Проверяем авторизацию
        me = await analyzer.client.get_me()
        print(f"✅ Авторизован как: {me.first_name} (@{me.username})")

        await analyzer.disconnect()
        print("✅ Отключение успешно")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_telegram())
