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

async def simple_test():
    try:
        print("=== SIMPLE TELEGRAM TEST ===")

        from src.app.telegram_client import TelegramAnalyzer
        print("1. Импорт успешен")

        analyzer = TelegramAnalyzer()
        print("2. Создание analyzer успешно")

        # Проверяем сессию
        needs_auth = await analyzer.needs_authorization()
        print(f"3. Needs auth: {needs_auth}")

        # Проверяем подключение
        if not needs_auth:
            await analyzer.connect()
            print("4. Подключение успешно")
        else:
            print("4. Авторизация нужна - пробуем send_code")

            result = await analyzer.send_code('+79001234567')
            print(f"5. Send code result: {result}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
