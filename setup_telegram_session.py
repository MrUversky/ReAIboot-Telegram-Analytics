#!/usr/bin/env python3
"""
Скрипт для настройки Telegram сессии.
Используется для создания session файла для работы с Telegram API.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.telegram_client import TelegramAnalyzer
from src.app.settings import settings

async def setup_session():
    """Настраивает Telegram сессию."""

    print("🚀 Настройка Telegram сессии для ReAIboot")
    print("=" * 50)

    # Проверяем настройки
    if not settings.telegram_api_id:
        print("❌ TELEGRAM_API_ID не найден в настройках")
        print("Получите его на https://my.telegram.org")
        return

    if not settings.telegram_api_hash:
        print("❌ TELEGRAM_API_HASH не найден в настройках")
        print("Получите его на https://my.telegram.org")
        return

    print(f"📱 API ID: {settings.telegram_api_id}")
    print(f"🔑 API Hash: {settings.telegram_api_hash[:10]}...")
    print()

    # Создаем клиент
    analyzer = TelegramAnalyzer()

    try:
        # Запрашиваем номер телефона
        phone = input("📞 Введите номер телефона (+7XXXXXXXXXX): ").strip()

        if not phone:
            print("❌ Номер телефона обязателен")
            return

        # Начинаем авторизацию
        print("📤 Отправляем код подтверждения...")
        result = await analyzer.manual_auth(phone)
        print(result)

        if "Код подтверждения отправлен" in result:
            # Запрашиваем код
            code = input("🔢 Введите код из Telegram: ").strip()

            if not code:
                print("❌ Код обязателен")
                return

            # Отправляем код
            print("✅ Подтверждаем код...")
            result = await analyzer.send_code(code)
            print(result)

            if "успешна" in result:
                print("🎉 Сессия успешно настроена!")
                print("Теперь вы можете использовать ReAIboot для парсинга каналов.")
            else:
                print("❌ Авторизация не удалась")

        elif "Уже авторизован" in result:
            print("✅ Сессия уже активна!")

        else:
            print(f"❌ Ошибка: {result}")

    except KeyboardInterrupt:
        print("\n🛑 Отменено пользователем")
    except Exception as e:
        print(f"❌ Ошибка при настройке сессии: {e}")
    finally:
        await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_session())
