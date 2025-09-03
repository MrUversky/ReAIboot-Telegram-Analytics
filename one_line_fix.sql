-- ОДНА СТРОКА РЕШЕНИЯ ПРОБЛЕМЫ
-- Просто скопируйте и выполните В ЭТОЙ ПОСЛЕДОВАТЕЛЬНОСТИ:

-- 1. ОТКЛЮЧИТЬ RLS (ОСНОВНАЯ ПРОБЛЕМА)
ALTER TABLE channels DISABLE ROW LEVEL SECURITY;
ALTER TABLE posts DISABLE ROW LEVEL SECURITY;
ALTER TABLE parsing_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE post_analysis DISABLE ROW LEVEL SECURITY;

