#!/usr/bin/env python3
"""
Создание таблицы промптов простым способом
"""

from supabase import create_client

def create_prompts_table():
    print("📝 СОЗДАНИЕ ТАБЛИЦЫ ПРОМПТОВ...")

    url = 'https://oxsvtjtgtdaqoslcxdna.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGRhcW9zbGN4ZG5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjgwNjk3NCwiZXhwIjoyMDcyMzgyOTc0fQ.3oGlvhXLmXyYgsxNMzuz-4zaRgxY9q5YkXmEx5LJU6M'

    supabase = create_client(url, service_key)

    # Попробуем создать тестовую запись - если таблица не существует, будет ошибка
    test_data = {
        "name": "Тестовый промпт",
        "description": "Тест",
        "prompt_type": "test",
        "content": "Тестовый контент",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True
    }

    try:
        result = supabase.table('llm_prompts').insert([test_data]).execute()
        print("✅ Таблица llm_prompts существует")
        # Удалим тестовую запись
        supabase.table('llm_prompts').delete().eq('name', 'Тестовый промпт').execute()
        print("✅ Тестовая запись удалена")
    except Exception as e:
        if "relation \"public.llm_prompts\" does not exist" in str(e):
            print("❌ Таблица llm_prompts не существует")
            print("📋 Создайте таблицу вручную в Supabase Dashboard:")
            print("""
CREATE TABLE public.llm_prompts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    prompt_type TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT DEFAULT 'gpt-4o-mini',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    created_by UUID REFERENCES public.profiles(id),
    UNIQUE(name, prompt_type)
);
            """)
        else:
            print(f"❌ Другая ошибка: {e}")

if __name__ == "__main__":
    create_prompts_table()
