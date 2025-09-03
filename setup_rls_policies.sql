    -- Настройка RLS политик для корректной работы парсинга
    -- Запустите этот скрипт в Supabase SQL Editor

    -- 1. Включаем RLS для всех таблиц (если отключено)
    ALTER TABLE parsing_sessions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
    ALTER TABLE post_analysis ENABLE ROW LEVEL SECURITY;
    ALTER TABLE channels ENABLE ROW LEVEL SECURITY;

    -- 2. Удаляем существующие политики для parsing_sessions
    DROP POLICY IF EXISTS "parsing_sessions_select_policy" ON parsing_sessions;
    DROP POLICY IF EXISTS "parsing_sessions_insert_policy" ON parsing_sessions;
    DROP POLICY IF EXISTS "parsing_sessions_update_policy" ON parsing_sessions;
    DROP POLICY IF EXISTS "parsing_sessions_delete_policy" ON parsing_sessions;

    -- 3. Создаем новые политики для parsing_sessions
    -- Политика SELECT: все могут читать
    CREATE POLICY "parsing_sessions_select_policy" ON parsing_sessions
    FOR SELECT USING (true);

    -- Политика INSERT: все могут вставлять (для анонимного доступа)
    CREATE POLICY "parsing_sessions_insert_policy" ON parsing_sessions
    FOR INSERT WITH CHECK (true);

    -- Политика UPDATE: все могут обновлять
    CREATE POLICY "parsing_sessions_update_policy" ON parsing_sessions
    FOR UPDATE USING (true) WITH CHECK (true);

    -- Политика DELETE: все могут удалять
    CREATE POLICY "parsing_sessions_delete_policy" ON parsing_sessions
    FOR DELETE USING (true);

    -- 4. Аналогично для других таблиц
    -- Channels
    DROP POLICY IF EXISTS "channels_select_policy" ON channels;
    DROP POLICY IF EXISTS "channels_insert_policy" ON channels;
    DROP POLICY IF EXISTS "channels_update_policy" ON channels;

    CREATE POLICY "channels_select_policy" ON channels FOR SELECT USING (true);
    CREATE POLICY "channels_insert_policy" ON channels FOR INSERT WITH CHECK (true);
    CREATE POLICY "channels_update_policy" ON channels FOR UPDATE USING (true) WITH CHECK (true);

    -- Posts
    DROP POLICY IF EXISTS "posts_select_policy" ON posts;
    DROP POLICY IF EXISTS "posts_insert_policy" ON posts;

    CREATE POLICY "posts_select_policy" ON posts FOR SELECT USING (true);
    CREATE POLICY "posts_insert_policy" ON posts FOR INSERT WITH CHECK (true);

    -- Post Analysis
    DROP POLICY IF EXISTS "post_analysis_select_policy" ON post_analysis;
    DROP POLICY IF EXISTS "post_analysis_insert_policy" ON post_analysis;

    CREATE POLICY "post_analysis_select_policy" ON post_analysis FOR SELECT USING (true);
    CREATE POLICY "post_analysis_insert_policy" ON post_analysis FOR INSERT WITH CHECK (true);

    -- Настройка политик для таблицы posts
DROP POLICY IF EXISTS "posts_select_policy" ON posts;
DROP POLICY IF EXISTS "posts_insert_policy" ON posts;
DROP POLICY IF EXISTS "posts_update_policy" ON posts;

CREATE POLICY "posts_select_policy" ON posts FOR SELECT USING (true);
CREATE POLICY "posts_insert_policy" ON posts FOR INSERT WITH CHECK (true);
CREATE POLICY "posts_update_policy" ON posts FOR UPDATE USING (true) WITH CHECK (true);

-- Настройка политик для таблицы post_analysis
DROP POLICY IF EXISTS "post_analysis_select_policy" ON post_analysis;
DROP POLICY IF EXISTS "post_analysis_insert_policy" ON post_analysis;
DROP POLICY IF EXISTS "post_analysis_update_policy" ON post_analysis;

CREATE POLICY "post_analysis_select_policy" ON post_analysis FOR SELECT USING (true);
CREATE POLICY "post_analysis_insert_policy" ON post_analysis FOR INSERT WITH CHECK (true);
CREATE POLICY "post_analysis_update_policy" ON post_analysis FOR UPDATE USING (true) WITH CHECK (true);

-- 5. Проверяем статус политик
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
WHERE tablename IN ('parsing_sessions', 'channels', 'posts', 'post_analysis')
ORDER BY tablename, policyname;

-- 6. Проверяем статус RLS
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE tablename IN ('parsing_sessions', 'channels', 'posts', 'post_analysis');
