-- Комплексное исправление проблем Supabase
-- Выполнить в Supabase SQL Editor

-- 1. Сброс всех RLS политик
DROP POLICY IF EXISTS "parsing_sessions_insert" ON parsing_sessions;
DROP POLICY IF EXISTS "parsing_sessions_select" ON parsing_sessions;
DROP POLICY IF EXISTS "parsing_sessions_update" ON parsing_sessions;

DROP POLICY IF EXISTS "channels_insert" ON channels;
DROP POLICY IF EXISTS "channels_select" ON channels;
DROP POLICY IF EXISTS "channels_update" ON channels;
DROP POLICY IF EXISTS "channels_delete" ON channels;

DROP POLICY IF EXISTS "posts_insert" ON posts;
DROP POLICY IF EXISTS "posts_select" ON posts;
DROP POLICY IF EXISTS "posts_update" ON posts;
DROP POLICY IF EXISTS "posts_delete" ON posts;

DROP POLICY IF EXISTS "post_analysis_insert" ON post_analysis;
DROP POLICY IF EXISTS "post_analysis_select" ON post_analysis;
DROP POLICY IF EXISTS "post_analysis_update" ON post_analysis;
DROP POLICY IF EXISTS "post_analysis_delete" ON post_analysis;

-- 2. Отключение RLS для всех таблиц (временное решение)
ALTER TABLE parsing_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE channels DISABLE ROW LEVEL SECURITY;
ALTER TABLE posts DISABLE ROW LEVEL SECURITY;
ALTER TABLE post_analysis DISABLE ROW LEVEL SECURITY;

-- 3. Создание функции для проверки RLS политик
CREATE OR REPLACE FUNCTION get_rls_policies(table_name TEXT)
RETURNS TABLE (
    policy_name TEXT,
    cmd TEXT,
    roles TEXT[],
    using_expr TEXT,
    check_expr TEXT
) AS $$
BEGIN
    RETURN QUERY
    EXECUTE format('
        SELECT
            p.policyname::TEXT,
            CASE p.cmd
                WHEN ''r'' THEN ''SELECT''
                WHEN ''a'' THEN ''INSERT''
                WHEN ''w'' THEN ''UPDATE''
                WHEN ''d'' THEN ''DELETE''
                ELSE p.cmd
            END,
            ARRAY_AGG(r.rolname)::TEXT[],
            p.qual::TEXT,
            p.with_check::TEXT
        FROM pg_policies p
        LEFT JOIN pg_roles r ON r.oid = ANY(p.roles)
        WHERE p.tablename = %L
        GROUP BY p.policyname, p.cmd, p.qual, p.with_check
    ', table_name);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Создание функции для очистки дубликатов каналов
CREATE OR REPLACE FUNCTION cleanup_duplicate_channels()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    channel_record RECORD;
BEGIN
    -- Удаляем дубликаты каналов (те, что без @)
    FOR channel_record IN
        SELECT c1.id
        FROM channels c1
        JOIN channels c2 ON (
            c1.username = ltrim(c2.username, '@')
            AND c2.username LIKE '@%'
            AND c1.id != c2.id
        )
        WHERE c1.username NOT LIKE '@%'
    LOOP
        DELETE FROM channels WHERE id = channel_record.id;
        deleted_count := deleted_count + 1;
    END LOOP;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Выполнение очистки
SELECT cleanup_duplicate_channels() as deleted_duplicates;

-- 6. Проверка результатов
SELECT
    'channels' as table_name,
    COUNT(*) as total_count
FROM channels
UNION ALL
SELECT
    'posts' as table_name,
    COUNT(*) as total_count
FROM posts
UNION ALL
SELECT
    'parsing_sessions' as table_name,
    COUNT(*) as total_count
FROM parsing_sessions;

-- 7. Проверка на дубликаты
SELECT
    ltrim(username, '@') as base_username,
    COUNT(*) as count,
    STRING_AGG(username, ', ') as usernames
FROM channels
GROUP BY ltrim(username, '@')
HAVING COUNT(*) > 1;

