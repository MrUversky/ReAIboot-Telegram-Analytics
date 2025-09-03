-- Выполнить в Supabase SQL Editor

-- 1. ОБНОВИТЬ ВСЕ ПОСТЫ С НЕПРАВИЛЬНЫМ channel_username
UPDATE posts
SET channel_username = '@robotless'
WHERE channel_username = 'robotless';

-- 2. ОБНОВИТЬ КАНАЛ НА ПРАВИЛЬНЫЙ username
UPDATE channels
SET username = '@robotless'
WHERE id = 44;

-- 3. ПРОВЕРИТЬ РЕЗУЛЬТАТ
SELECT
    'channels' as table_name,
    COUNT(*) as total_count
FROM channels
WHERE username LIKE '%robotless%'
UNION ALL
SELECT
    'posts' as table_name,
    COUNT(*) as total_count
FROM posts
WHERE channel_username LIKE '%robotless%';

-- 4. ПРОВЕРИТЬ СОВПАДЕНИЯ
SELECT
    c.username as channel_username,
    COUNT(p.id) as posts_count
FROM channels c
LEFT JOIN posts p ON p.channel_username = c.username
WHERE c.username LIKE '%robotless%'
GROUP BY c.username;

