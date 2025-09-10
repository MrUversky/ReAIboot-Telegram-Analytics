-- ПОЛНАЯ МИГРАЦИЯ: Применить все изменения к базе данных Supabase
-- Выполнить в Supabase SQL Editor в следующем порядке:

-- ============================================================
-- ШАГ 1: Добавляем недостающие колонки к таблице llm_prompts
-- ============================================================

ALTER TABLE public.llm_prompts
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general',
ADD COLUMN IF NOT EXISTS variables JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS model_settings JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;

-- ============================================================
-- ШАГ 2: Добавляем индексы для новых полей
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_llm_prompts_name ON public.llm_prompts(name);

-- ============================================================
-- ШАГ 3: Обновляем существующие записи
-- ============================================================

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

-- ============================================================
-- ШАГ 4: Проверяем результат миграции
-- ============================================================

SELECT
  'Миграция выполнена успешно!' as status,
  COUNT(*) as total_prompts,
  COUNT(CASE WHEN model_settings IS NOT NULL THEN 1 END) as prompts_with_settings,
  COUNT(CASE WHEN category IS NOT NULL THEN 1 END) as prompts_with_category
FROM public.llm_prompts;

-- Показываем обновленные промпты
SELECT
  id,
  name,
  prompt_type,
  category,
  is_system,
  jsonb_pretty(model_settings) as model_settings,
  variables
FROM public.llm_prompts
ORDER BY id;

