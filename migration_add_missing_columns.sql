-- Миграция: Добавление недостающих колонок к таблице llm_prompts
-- Выполнить в Supabase SQL Editor

-- Добавляем недостающие колонки к таблице llm_prompts
ALTER TABLE public.llm_prompts
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general',
ADD COLUMN IF NOT EXISTS variables JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS model_settings JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;

-- Добавляем индексы для новых полей
CREATE INDEX IF NOT EXISTS idx_llm_prompts_name ON public.llm_prompts(name);

-- Обновляем существующие записи, создавая model_settings из старых полей
UPDATE public.llm_prompts
SET
  category = CASE
    WHEN prompt_type = 'filter' THEN 'filtering'
    WHEN prompt_type = 'analysis' THEN 'analysis'
    WHEN prompt_type = 'generation' THEN 'generation'
    ELSE 'general'
  END,
  is_system = true,  -- Все существующие промпты считаем системными
  version = 1,
  model_settings = jsonb_build_object(
    'model', COALESCE(model, 'gpt-4o-mini'),
    'temperature', COALESCE(temperature, 0.7),
    'max_tokens', COALESCE(max_tokens, 2000)
  ),
  variables = '{}'::jsonb;

-- Проверяем результат
SELECT
  id,
  name,
  prompt_type,
  category,
  is_system,
  model_settings,
  variables
FROM public.llm_prompts;

-- Выводим сообщение об успешной миграции
SELECT 'Миграция llm_prompts завершена успешно!' as status;
