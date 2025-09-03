#!/usr/bin/env python3
"""
Быстрое исправление схемы таблицы posts
"""

import sys
import os
sys.path.append('src')

def check_posts_schema():
    """Проверяет схему таблицы posts"""
    print("🔍 ПРОВЕРКА СХЕМЫ ТАБЛИЦЫ POSTS")
    print("=" * 40)

    from src.app.supabase_client import SupabaseManager

    supabase = SupabaseManager()

    try:
        # Проверяем доступные колонки
        result = supabase.client.table('posts').select('*').limit(1).execute()

        if result.data:
            available_columns = list(result.data[0].keys())
            print("📋 Доступные колонки:")
            for col in available_columns:
                print(f"   • {col}")
        else:
            print("⚠️ Таблица posts пуста")

        # Проверяем необходимые колонки
        required_columns = ['channel_id', 'viral_score', 'engagement_rate', 'zscore', 'median_multiplier']
        missing_columns = []

        for col in required_columns:
            if col not in available_columns:
                missing_columns.append(col)

        if missing_columns:
            print(f"\n❌ Отсутствуют колонки: {', '.join(missing_columns)}")
            print("\n🔧 РЕШЕНИЕ:")
            print("Нужно выполнить SQL скрипт в Supabase SQL Editor:")
            print("Содержимое файла fix_posts_schema.sql")
            return False
        else:
            print("\n✅ Все необходимые колонки присутствуют")
            return True

    except Exception as e:
        print(f"❌ Ошибка проверки схемы: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 БЫСТРАЯ ПРОВЕРКА СХЕМЫ POSTS\n")

    if check_posts_schema():
        print("\n🎉 СХЕМА В ПОРЯДКЕ!")
        print("Можно запускать парсинг.")
    else:
        print("\n⚠️ НУЖНО ОБНОВИТЬ СХЕМУ!")
        print("Следуйте инструкциям выше.")

if __name__ == "__main__":
    main()
