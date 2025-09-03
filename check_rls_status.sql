-- Проверка статуса RLS и политик для таблицы parsing_sessions
-- Запустите этот скрипт в Supabase SQL Editor

-- 1. Проверяем статус RLS для таблицы
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'parsing_sessions';

-- 2. Проверяем существующие политики
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'parsing_sessions';

-- 3. Проверяем структуру таблицы
\d parsing_sessions;

-- 4. Проверяем, можем ли мы вставить тестовую запись напрямую
-- (раскомментируйте для тестирования)
/*
INSERT INTO parsing_sessions (started_at, status, channels_parsed, posts_found)
VALUES (NOW(), 'test', 1, 0);
*/

-- 5. Если все еще не работает, полностью отключаем RLS
-- ALTER TABLE parsing_sessions DISABLE ROW LEVEL SECURITY;

