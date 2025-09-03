-- Правильные RLS политики для Supabase
-- Выполнить ПОСЛЕ выполнения fix_supabase_issues.sql

-- 1. Включение RLS для всех таблиц
ALTER TABLE parsing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_analysis ENABLE ROW LEVEL SECURITY;

-- 2. Универсальные политики для всех таблиц (позволяют все операции)
-- parsing_sessions
CREATE POLICY "parsing_sessions_all" ON parsing_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- channels
CREATE POLICY "channels_all" ON channels
    FOR ALL USING (true) WITH CHECK (true);

-- posts
CREATE POLICY "posts_all" ON posts
    FOR ALL USING (true) WITH CHECK (true);

-- post_analysis
CREATE POLICY "post_analysis_all" ON post_analysis
    FOR ALL USING (true) WITH CHECK (true);

-- 3. Проверка политик
SELECT get_rls_policies('parsing_sessions');
SELECT get_rls_policies('channels');
SELECT get_rls_policies('posts');
SELECT get_rls_policies('post_analysis');

-- 4. Финальная проверка
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('parsing_sessions', 'channels', 'posts', 'post_analysis');

