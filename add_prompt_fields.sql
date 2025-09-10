-- Добавляем поля system_prompt и user_prompt в таблицу llm_prompts
ALTER TABLE public.llm_prompts
ADD COLUMN IF NOT EXISTS system_prompt TEXT,
ADD COLUMN IF NOT EXISTS user_prompt TEXT;

-- Обновляем RLS политики если нужно
-- (политики уже должны быть настроены для таблицы)

