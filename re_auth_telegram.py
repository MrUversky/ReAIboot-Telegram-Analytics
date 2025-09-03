#!/usr/bin/env python3
"""
Скрипт для повторной авторизации в Telegram
Запустите этот скрипт для создания новой сессии
"""

import sys
import asyncio
sys.path.append('src')

from src.app.telegram_client import TelegramAnalyzer

async def re_auth_telegram():
    """Повторная авторизация в Telegram"""

    print("🔐 Повторная авторизация в Telegram")
    print("====================================")
    print()
    print("Этот скрипт создаст новую сессию для работы с Telegram API.")
    print("Вам потребуется:")
    print("1. Номер телефона, привязанный к Telegram")
    print("2. Код подтверждения из Telegram")
    print()
    print("⚠️  ВАЖНО: Используйте тот же номер телефона, что и в настройках!")
    print()

    try:
        # Создаем новый экземпляр без существующей сессии
        analyzer = TelegramAnalyzer()

        print("🔌 Подключаемся к Telegram...")
        await analyzer.connect()

        print("✅ Авторизация прошла успешно!")
        print("Теперь можно запускать API сервер.")

    except KeyboardInterrupt:
        print("\n❌ Авторизация отменена пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка авторизации: {e}")
        print("\nВозможные причины:")
        print("1. Неправильные API ключи в .env файле")
        print("2. Номер телефона не привязан к Telegram")
        print("3. Проблемы с интернет-соединением")

if __name__ == "__main__":
    asyncio.run(re_auth_telegram())

