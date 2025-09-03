#!/usr/bin/env python3
"""
Исправление схемы через Supabase Management API
"""

import sys
import os
import requests
sys.path.append('src')

def get_supabase_credentials():
    """Получает credentials для Supabase"""
    from src.app.settings import settings

    # Эти переменные должны быть установлены в settings.py или .env
    project_url = getattr(settings, 'supabase_url', None)
    service_role_key = getattr(settings, 'supabase_service_role_key', None)

    if not project_url or not service_role_key:
        print("❌ Не найдены credentials для Supabase Management API")
        print("Нужно установить SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY")
        return None, None

    return project_url, service_role_key

def execute_sql_via_api(sql_query):
    """Выполняет SQL через REST API"""
    project_url, service_role_key = get_supabase_credentials()

    if not project_url or not service_role_key:
        return False

    # Supabase REST API endpoint для выполнения SQL
    url = f"{project_url}/rest/v1/rpc/exec_sql"

    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }

    # Для выполнения произвольного SQL нужно создать RPC функцию
    # Но обычно это делается через SQL Editor в интерфейсе

    print("📡 Попытка выполнения SQL через API...")
    print("⚠️ Для надежности используйте Supabase SQL Editor")
    print(f"SQL для выполнения:\n{sql_query}")

    return False

def main():
    """Основная функция исправления схемы"""
    print("🔧 ИСПРАВЛЕНИЕ СХЕМЫ ТАБЛИЦЫ POSTS")
    print("=" * 50)

    # SQL для добавления колонки
    sql_query = """
    -- Добавление колонки channel_id в таблицу posts
    ALTER TABLE public.posts ADD COLUMN IF NOT EXISTS channel_id BIGINT;

    -- Создание индекса для channel_id
    CREATE INDEX IF NOT EXISTS idx_posts_channel_id ON public.posts(channel_id);
    """

    print("📋 SQL ЗАПРОС ДЛЯ ВЫПОЛНЕНИЯ:")
    print(sql_query)

    print("\n🔧 СПОСОБЫ ВЫПОЛНЕНИЯ:")
    print("1. 📝 Supabase SQL Editor (рекомендуется):")
    print("   - Откройте Supabase Dashboard")
    print("   - Перейдите в SQL Editor")
    print("   - Скопируйте и выполните SQL выше")

    print("\n2. 📄 Через файл:")
    print("   - Содержимое файла fix_posts_schema.sql")
    print("   - Скопируйте в SQL Editor")

    print("\n3. 🔍 После выполнения проверьте:")
    print("   python quick_fix_posts.py")

    # Попытка выполнить через API (может не сработать)
    if execute_sql_via_api(sql_query):
        print("\n✅ Схема обновлена через API!")
    else:
        print("\n⚠️ Используйте SQL Editor для обновления схемы")

if __name__ == "__main__":
    main()
