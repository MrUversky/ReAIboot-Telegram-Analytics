#!/usr/bin/env python3
"""
Создание таблицы промптов
"""

import requests
import json

def create_prompts_table():
    print("📝 СОЗДАНИЕ ТАБЛИЦЫ ПРОМПТОВ...")

    url = 'https://oxsvtjtgtdaqoslcxdna.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGRhcW9zbGN4ZG5hIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjgwNjk3NCwiZXhwIjoyMDcyMzgyOTc0fQ.3oGlvhXLmXyYgsxNMzuz-4zaRgxY9q5YkXmEx5LJU6M'

    headers = {
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'apikey': service_key
    }

    sql = '''
    -- Таблица для хранения промптов
    CREATE TABLE IF NOT EXISTS public.llm_prompts (
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

    -- RLS политика
    ALTER TABLE public.llm_prompts ENABLE ROW LEVEL SECURITY;

    DROP POLICY IF EXISTS "Authenticated users can view prompts" ON public.llm_prompts;
    DROP POLICY IF EXISTS "Admins can manage prompts" ON public.llm_prompts;

    CREATE POLICY "Authenticated users can view prompts" ON public.llm_prompts
        FOR SELECT TO authenticated USING (true);

    CREATE POLICY "Admins can manage prompts" ON public.llm_prompts
        FOR ALL TO authenticated USING (
            EXISTS (
                SELECT 1 FROM public.profiles
                WHERE id = auth.uid() AND role = 'admin'
            )
        );

    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_llm_prompts_type ON public.llm_prompts(prompt_type);
    CREATE INDEX IF NOT EXISTS idx_llm_prompts_active ON public.llm_prompts(is_active);

    -- Триггер для updated_at
    DROP TRIGGER IF EXISTS update_llm_prompts_updated_at ON public.llm_prompts;
    CREATE TRIGGER update_llm_prompts_updated_at BEFORE UPDATE ON public.llm_prompts
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    '''

    try:
        response = requests.post(
            f'{url}/rest/v1/rpc/exec_sql',
            json={'query': sql},
            headers=headers
        )
        print(f'Статус: {response.status_code}')
        if response.status_code == 200:
            print('✅ Таблица промптов создана успешно')
        else:
            print(f'❌ Ошибка: {response.text[:300]}')
    except Exception as e:
        print(f'❌ Ошибка подключения: {e}')

if __name__ == "__main__":
    create_prompts_table()
