-- ДОБАВЛЕНИЕ ТАБЛИЦЫ ПРОМПТОВ

-- Таблица для хранения промптов
CREATE TABLE public.llm_prompts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    prompt_type TEXT NOT NULL, -- 'filter', 'analysis', 'generation', 'custom'
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

-- RLS политика для промптов
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

-- Индексы для производительности
CREATE INDEX idx_llm_prompts_type ON public.llm_prompts(prompt_type);
CREATE INDEX idx_llm_prompts_active ON public.llm_prompts(is_active);

-- Триггер для updated_at
CREATE TRIGGER update_llm_prompts_updated_at BEFORE UPDATE ON public.llm_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
