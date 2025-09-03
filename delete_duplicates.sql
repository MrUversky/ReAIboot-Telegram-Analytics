-- SQL скрипт для удаления дубликатов каналов
-- Выполнить в Supabase SQL Editor

-- Удаляем дубликаты каналов (те, что без @ в username)
DELETE FROM channels
WHERE id IN (
    SELECT c1.id
    FROM channels c1
    JOIN channels c2 ON (
        c1.username = ltrim(c2.username, '@')  -- c1 без @, c2 с @
        AND c2.username LIKE '@%'
        AND c1.id != c2.id
    )
    WHERE c1.username NOT LIKE '@%'  -- Только каналы без @
);

-- Проверяем результат
SELECT
    COUNT(*) as total_channels,
    COUNT(DISTINCT ltrim(username, '@')) as unique_usernames
FROM channels;

-- Показываем оставшиеся каналы
SELECT id, username, title
FROM channels
ORDER BY username;

