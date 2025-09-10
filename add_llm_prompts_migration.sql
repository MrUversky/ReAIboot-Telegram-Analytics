-- Миграция: Добавление таблицы llm_prompts для хранения системных промптов
-- Выполнить эти команды в Supabase SQL Editor или через psql

-- Создание таблицы llm_prompts
CREATE TABLE IF NOT EXISTS public.llm_prompts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    prompt_type TEXT NOT NULL DEFAULT 'system',
    category TEXT DEFAULT 'general',
    content TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    model_settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Включение RLS
ALTER TABLE public.llm_prompts ENABLE ROW LEVEL SECURITY;

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_llm_prompts_type ON public.llm_prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_llm_prompts_category ON public.llm_prompts(category);
CREATE INDEX IF NOT EXISTS idx_llm_prompts_active ON public.llm_prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_prompts_system ON public.llm_prompts(is_system);

-- Создание триггера для updated_at
CREATE OR REPLACE FUNCTION update_llm_prompts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_llm_prompts_updated_at
    BEFORE UPDATE ON public.llm_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_prompts_updated_at();

-- Создание политик RLS
CREATE POLICY "Authenticated users can view LLM prompts" ON public.llm_prompts
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Only admins can modify LLM prompts" ON public.llm_prompts
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Service role can manage LLM prompts" ON public.llm_prompts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Вставка системных промптов
INSERT INTO public.llm_prompts (name, description, prompt_type, category, content, variables, model_settings, is_system) VALUES
('project_context_system', 'Системный промпт с контекстом проекта ПерепрошИИвка', 'system', 'project_context',
'Ты - эксперт по анализу контента для социальных сетей.
Проект: ПерепрошИИвка
ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

Целевая аудитория:
- Специалисты IT сферы
- Предприниматели и бизнесмены
- Люди, интересующиеся технологиями и саморазвитием

Формат контента:
- Короткие видео 15-60 секунд
- Практическая ценность
- Доступный язык
- Визуально привлекательный контент

Принципы контента:
- Фокус на практической пользе
- Простой и понятный язык
- Визуально привлекательные материалы
- Эмоциональная вовлеченность зрителя
- Конкретные actionable советы

Брендовый стиль:
- Профессиональный, но дружелюбный
- Доступный, без сложного жаргона
- Вдохновляющий и мотивирующий
- Фокус на результатах и пользе',
'{}', '{}', true),

('filter_posts_system', 'Системный промпт для фильтрации постов', 'system', 'filtering',
'Ты - эксперт по анализу контента для социальных сетей.
Проект: ПерепрошИИвка
ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

Твоя задача: оценить, подходит ли пост из Telegram для создания образовательного контента.',
'{"post_text": "", "views": 0, "reactions": 0, "replies": 0, "forwards": 0}',
'{"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 300}', true),

('analyze_success_system', 'Системный промпт для анализа успешных постов', 'system', 'analysis',
'Ты - опытный аналитик контента для социальных сетей.
Проект: ПерепрошИИвка
ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

Твоя задача: глубоко проанализировать почему пост стал популярным.',
'{"post_text": "", "views": 0, "reactions": 0, "replies": 0, "forwards": 0, "analysis": ""}',
'{"model": "claude-3-5-sonnet-20241022", "temperature": 0.4, "max_tokens": 2000}', true),

('generate_scenario_system', 'Системный промпт для генерации сценариев', 'system', 'generation',
'Ты - креативный директор по контенту для TikTok/Reels.
Проект: ПерепрошИИвка
ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

Профессиональный, но дружелюбный
Доступный, без сложного жаргона
Вдохновляющий и мотивирующий
Фокус на результатах и пользе

Создай сценарий с хуком, основной идеей и раскадровкой.',
'{"post_text": "", "analysis": "", "rubric_name": "", "format_name": "", "duration": 30}',
'{"model": "gpt-4o", "temperature": 0.7, "max_tokens": 3000}', true)
ON CONFLICT (name) DO NOTHING;

-- Вывод информации о миграции
SELECT 'Миграция llm_prompts выполнена успешно' as message;
SELECT COUNT(*) as total_prompts FROM public.llm_prompts;

