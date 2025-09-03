#!/usr/bin/env python3
"""
Быстрый тест Telegram сессии
"""

import sys
import asyncio
sys.path.append('src')

async def quick_test():
    """Быстрый тест Telegram подключения"""
    print("🔍 БЫСТРЫЙ ТЕСТ TELEGRAM СЕССИИ")
    print("=" * 40)

    try:
        from src.app.telegram_client import TelegramAnalyzer

        print("📱 Подключение к Telegram...")
        analyzer = TelegramAnalyzer()

        if not analyzer.client:
            print("❌ Клиент не инициализирован")
            return False

        # Простая проверка подключения
        try:
            await analyzer.client.connect()
            connected = analyzer.client.is_connected()

            if connected:
                print("✅ Подключение к Telegram успешно")
                print("Сессия работает корректно!")
                await analyzer.client.disconnect()
                return True
            else:
                print("❌ Не удалось подключиться")
                print("Возможно, нужно переавторизоваться")
                return False

        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            if "database is locked" in str(e):
                print("📝 Сессия заблокирована - нужно создать новую")
                print("Запустите: python setup_telegram_session.py")
            return False

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
