#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Supabase и проверки RLS политик.
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

from src.app.supabase_client import SupabaseClient
from src.app.settings import settings

def test_supabase_connection():
    """Тестируем подключение к Supabase."""
    print("🔧 Тестирование подключения к Supabase...")

            # Проверяем настройки
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"Supabase Anon Key: {'*' * 20 if settings.supabase_anon_key else 'None'}")
    print(f"Service Role Key: {'*' * 20 if settings.supabase_service_role_key else 'None'}")
    print(f"Will use: {'Service Role' if settings.supabase_service_role_key else 'Anonymous'} key")

    if not settings.supabase_service_role_key:
        print("\n⚠️  WARNING: Using anonymous key!")
        print("   This may cause RLS policy violations.")
        print("   Consider adding SUPABASE_SERVICE_ROLE_KEY to .env")
        print("   Or run setup_rls_policies.sql in Supabase SQL Editor")

    # Создаем клиент
    client = SupabaseClient()

    # Проверяем подключение
    if not client.is_connected():
        print("❌ Не удалось подключиться к Supabase")
        return False

    print("✅ Подключение к Supabase успешно")

    # Пробуем создать тестовую сессию парсинга
    print("\n🔧 Тестирование создания сессии парсинга...")
    try:
        test_data = {
            'started_at': '2025-01-01T00:00:00.000Z',
            'status': 'test',
            'channels_parsed': 0,
            'posts_found': 0,
            'initiated_by': None
        }

        result = client.save_parsing_session(test_data)
        print(f"✅ Сессия создана успешно: {result}")

        # Удаляем тестовую сессию
        if 'id' in result:
            session_id = result['id']
            success = client.update_parsing_session(session_id, {'status': 'deleted'})
            print(f"✅ Тестовая сессия удалена: {success}")

        return True

    except Exception as e:
        print(f"❌ Ошибка при создании сессии: {e}")
        print("\n💡 Возможные решения:")
        print("1. Запустите скрипт fix_rls_parsing_sessions.sql в Supabase SQL Editor")
        print("2. Или добавьте SUPABASE_SERVICE_ROLE_KEY в .env файл")
        return False

def main():
    """Основная функция."""
    load_dotenv()

    print("🚀 Тест подключения к Supabase для ReAIboot")
    print("=" * 50)

    success = test_supabase_connection()

    print("\n" + "=" * 50)
    if success:
        print("✅ Все тесты пройдены успешно!")
    else:
        print("❌ Обнаружены проблемы с подключением")
        sys.exit(1)

if __name__ == "__main__":
    main()
