-- ПРОСТОЙ СКРИПТ ДЛЯ ИСПРАВЛЕНИЯ ПРОБЛЕМ С SUPABASE
-- СКОПИРУЙТЕ И ВЫПОЛНИТЕ В SUPABASE SQL EDITOR

-- 1. ОТКЛЮЧИТЬ RLS ПОЛИТИКИ (ГЛАВНАЯ ПРОБЛЕМА)
ALTER TABLE parsing_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE channels DISABLE ROW LEVEL SECURITY;
ALTER TABLE posts DISABLE ROW LEVEL SECURITY;
ALTER TABLE post_analysis DISABLE ROW LEVEL SECURITY;

-- 2. УДАЛИТЬ ДУБЛИКАТЫ КАНАЛОВ
DELETE FROM channels
WHERE id IN (
    SELECT c1.id
    FROM channels c1
    JOIN channels c2 ON (
        c1.username = ltrim(c2.username, '@')
        AND c2.username LIKE '@%'
        AND c1.id != c2.id
    )
    WHERE c1.username NOT LIKE '@%'
);

-- 3. ПРОВЕРИТЬ РЕЗУЛЬТАТ
SELECT
    'channels' as table_name,
    COUNT(*) as total_count
FROM channels
UNION ALL
SELECT
    'posts' as table_name,
    COUNT(*) as total_count
FROM posts;

-- 4. ПРОВЕРИТЬ НА ДУБЛИКАТЫ
SELECT
    ltrim(username, '@') as base_username,
    COUNT(*) as count,
    STRING_AGG(username, ', ') as usernames
FROM channels
GROUP BY ltrim(username, '@')
HAVING COUNT(*) > 1;


