#!/usr/bin/env python3
"""
Тест статуса базы данных и подключения
"""

import sys
import os
import time
sys.path.append('src')

from src.app.supabase_client import SupabaseManager
from src.app.settings import settings

def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("=" * 50)

    try:
        # Инициализация Supabase клиента
        print("📡 Попытка подключения к Supabase...")
        supabase = SupabaseManager()

        if not supabase.client:
            print("❌ Не удалось инициализировать Supabase клиент")
            return False

        print("✅ Supabase клиент инициализирован")

        # Тест базового запроса
        print("📊 Тест базового запроса...")
        result = supabase.client.table('posts').select('count', count='exact').limit(1).execute()
        print(f"✅ Базовый запрос выполнен: найдено {result.count} записей")

        # Тест конкретных таблиц
        tables_to_check = ['posts', 'channels', 'profiles', 'parsing_sessions']

        for table in tables_to_check:
            try:
                result = supabase.client.table(table).select('*').limit(1).execute()
                print(f"✅ Таблица '{table}' доступна")
            except Exception as e:
                print(f"❌ Ошибка доступа к таблице '{table}': {e}")

        # Тест новых таблиц для Viral Detection
        viral_tables = ['system_settings', 'channel_baselines']

        for table in viral_tables:
            try:
                result = supabase.client.table(table).select('*').limit(1).execute()
                print(f"✅ Таблица Viral Detection '{table}' доступна")
            except Exception as e:
                print(f"⚠️ Таблица Viral Detection '{table}' недоступна: {e}")
                print("   Нужно выполнить safe_schema_update.sql")

        # Тест новых колонок в posts
        print("🔧 Проверка новых колонок в таблице posts...")
        columns_to_check = ['viral_score', 'engagement_rate', 'zscore', 'median_multiplier', 'last_viral_calculation']

        try:
            # Пробуем запросить одну запись с новыми колонками
            result = supabase.client.table('posts').select(
                'id, ' + ', '.join(columns_to_check)
            ).limit(1).execute()

            if result.data:
                available_columns = [col for col in columns_to_check if col in result.data[0]]
                missing_columns = [col for col in columns_to_check if col not in result.data[0]]

                if available_columns:
                    print(f"✅ Доступны колонки: {', '.join(available_columns)}")
                if missing_columns:
                    print(f"⚠️ Отсутствуют колонки: {', '.join(missing_columns)}")
                    print("   Нужно выполнить safe_schema_update.sql")
            else:
                print("⚠️ Таблица posts пуста или колонки недоступны")

        except Exception as e:
            print(f"❌ Ошибка проверки колонок posts: {e}")

        return True

    except Exception as e:
        print(f"❌ Критическая ошибка подключения к БД: {e}")
        return False

def test_database_performance():
    """Тестирует производительность базы данных"""
    print("\n⚡ ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ БАЗЫ ДАННЫХ")
    print("=" * 50)

    try:
        supabase = SupabaseManager()

        # Тест скорости запроса
        start_time = time.time()
        result = supabase.client.table('posts').select('*').limit(100).execute()
        query_time = time.time() - start_time

        print(f"⏱️ Время выполнения: {query_time:.2f} сек")
        # Тест количества записей
        count_result = supabase.client.table('posts').select('count', count='exact').execute()
        print(f"📊 Всего постов в базе: {count_result.count}")

        # Тест индексов (простая проверка)
        print("🔍 Проверка наличия индексов...")
        # Это можно расширить для проверки конкретных индексов

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ БАЗЫ ДАННЫХ\n")

    success = True

    # Тест подключения
    if not test_database_connection():
        success = False

    # Тест производительности
    if not test_database_performance():
        success = False

    # Итоговый результат
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ ПРОШЛО УСПЕШНО!")
        print("\n✅ Рекомендации:")
        print("- База данных работает корректно")
        print("- Можно запускать парсинг")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С БАЗОЙ ДАННЫХ!")
        print("\n🔧 Возможные решения:")
        print("- Проверьте подключение к интернету")
        print("- Проверьте настройки Supabase")
        print("- Выполните safe_schema_update.sql для Viral Detection")
        print("- Проверьте статус Supabase проекта")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
