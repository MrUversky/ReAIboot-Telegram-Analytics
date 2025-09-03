# Создание таблицы промптов в Supabase

## Шаг 1: Откройте Supabase Dashboard

Перейдите в ваш проект Supabase: https://supabase.com/dashboard/project/YOUR_PROJECT_REF

## Шаг 2: Откройте SQL Editor

В левом меню выберите "SQL Editor"

## Шаг 3: Выполните SQL код

Скопируйте и вставьте следующий SQL код:

```sql
-- Таблица для хранения промптов
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

-- RLS политика
ALTER TABLE public.llm_prompts ENABLE ROW LEVEL SECURITY;

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
```

## Шаг 4: Нажмите "Run"

Нажмите кнопку "Run" для выполнения SQL кода.

## Шаг 5: Проверьте результат

Если код выполнился успешно, вы увидите сообщение "Success. No rows returned."

## Шаг 6: Загрузите базовые промпты

Теперь запустите скрипт для загрузки базовых промптов:

```bash
cd "ReAIboot TG "
source venv/bin/activate
python load_initial_data.py
```

## Готово! 🎉

Теперь в админ панели доступна третья вкладка "Промпты LLM" где вы можете:
- Просматривать все промпты
- Редактировать существующие
- Создавать новые промпты
- Настраивать параметры моделей

## Структура промптов

**Типы промптов:**
- `filter` - фильтрация постов на пригодность для Reels
- `analysis` - глубокий анализ успешного поста
- `generation` - генерация сценария Reels
- `custom` - пользовательские промпты

**Настраиваемые параметры:**
- Модель (GPT-4o, Claude, etc.)
- Temperature (0.0 - 2.0)
- Max Tokens (100 - 4000)
- Активность промпта
