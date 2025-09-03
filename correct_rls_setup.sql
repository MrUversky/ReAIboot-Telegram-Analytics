-- ПРАВИЛЬНАЯ НАСТРОЙКА RLS ПОЛИТИК ДЛЯ SUPABASE
-- Выполнить в Supabase SQL Editor

-- 1. ВКЛЮЧИТЬ RLS ДЛЯ ВСЕХ ТАБЛИЦ
ALTER TABLE parsing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_analysis ENABLE ROW LEVEL SECURITY;

-- 2. НАСТРОИТЬ ПРАВИЛЬНЫЕ ПОЛИТИКИ

-- CHANNELS: Разрешить все операции
DROP POLICY IF EXISTS "channels_allow_all" ON channels;
CREATE POLICY "channels_allow_all" ON channels
    FOR ALL USING (true) WITH CHECK (true);

-- POSTS: Разрешить все операции
DROP POLICY IF EXISTS "posts_allow_all" ON posts;
CREATE POLICY "posts_allow_all" ON posts
    FOR ALL USING (true) WITH CHECK (true);

-- PARSING_SESSIONS: Разрешить все операции
DROP POLICY IF EXISTS "parsing_sessions_allow_all" ON parsing_sessions;
CREATE POLICY "parsing_sessions_allow_all" ON parsing_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- POST_ANALYSIS: Разрешить все операции
DROP POLICY IF EXISTS "post_analysis_allow_all" ON post_analysis;
CREATE POLICY "post_analysis_allow_all" ON post_analysis
    FOR ALL USING (true) WITH CHECK (true);

-- 3. ПРОВЕРИТЬ РЕЗУЛЬТАТ
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('parsing_sessions', 'channels', 'posts', 'post_analysis');

-- 4. ПРОВЕРИТЬ ПОЛИТИКИ
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('parsing_sessions', 'channels', 'posts', 'post_analysis')
ORDER BY tablename, policyname;

