-- Удаляем колонку content из таблицы llm_prompts
-- поскольку теперь используем system_prompt и user_prompt
ALTER TABLE public.llm_prompts DROP COLUMN IF EXISTS content;

