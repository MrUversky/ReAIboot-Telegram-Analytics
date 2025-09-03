#!/usr/bin/env python3
"""
Скрипт для исправления проблем с Telegram авторизацией
Запустите этот скрипт для создания новой чистой сессии
"""

import sys
import os
import logging
sys.path.append('src')

def main():
    """Исправляем проблемы с Telegram сессией"""

    print("🔧 Исправление проблем с Telegram авторизацией")
    print("=" * 50)

    # Шаг 1: Удаляем все старые файлы сессий
    print("\n1️⃣ Удаляем старые файлы сессий...")
    session_files = [
        "session_per.session",
        "session_new.session",
        "session_fresh.session",
        "session_clean.session"
    ]

    for session_file in session_files:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"   ✅ Удален: {session_file}")

    # Шаг 2: Проверяем переменные окружения
    print("\n2️⃣ Проверяем настройки Telegram...")

    # Загружаем переменные из .env файла если они не установлены
    if not os.getenv("TELEGRAM_API_ID") or not os.getenv("TELEGRAM_API_HASH"):
        from dotenv import load_dotenv
        load_dotenv()

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("   ❌ Ошибка: TELEGRAM_API_ID или TELEGRAM_API_HASH не установлены")
        print("   📝 Добавьте их в файл .env:")
        print("   TELEGRAM_API_ID=ваш_api_id")
        print("   TELEGRAM_API_HASH=ваш_api_hash")
        return False

    print("   ✅ API ключи найдены")
    print(f"   📱 API ID: {api_id}")
    print(f"   🔑 API Hash: {api_hash[:10]}...")

    # Шаг 3: Пробуем создать новую сессию
    print("\n3️⃣ Создаем новую сессию...")

    try:
        from src.app.telegram_client import TelegramAnalyzer

        print("   🔄 Инициализируем TelegramAnalyzer...")
        analyzer = TelegramAnalyzer()

        print("   🔌 Подключаемся к Telegram...")
        import asyncio
        asyncio.run(analyzer.connect())

        print("   ✅ Успешно! Новая сессия создана")
        return True

    except Exception as e:
        print(f"   ❌ Ошибка при создании сессии: {e}")
        print("\nВозможные причины:")
        print("   • Неправильные API ключи")
        print("   • Проблемы с интернет-соединением")
        print("   • Telethon несовместим с Python версией")
        return False

    # Шаг 4: Инструкции для пользователя
    print("\n4️⃣ Следующие шаги:")
    print("   • Перезапустите API командой: ./start_project.sh")
    print("   • Проверьте статус: curl http://localhost:8000/api/health")
    print("   • Если все еще проблемы - попробуйте другой подход")

if __name__ == "__main__":
    success = main()

    if success:
        print("\n🎉 Telegram авторизация исправлена!")
        print("Теперь можно перезапустить проект.")
    else:
        print("\n❌ Не удалось исправить авторизацию.")
        print("Попробуйте проверить API ключи или использовать другую версию Python.")
