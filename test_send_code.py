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

async def test_send_code():
    try:
        from src.app.telegram_client import TelegramAnalyzer
        analyzer = TelegramAnalyzer()

        print('Testing send_code...')
        result = await analyzer.send_code('+79001234567')
        print(f'SUCCESS: {result}')

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_send_code())
