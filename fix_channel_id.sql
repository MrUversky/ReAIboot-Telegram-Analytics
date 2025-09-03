-- УДАЛЕНИЕ ЛИШНЕЙ КОЛОНКИ channel_id ИЗ ТАБЛИЦЫ posts
-- Выполните этот скрипт в Supabase SQL Editor

-- Удаляем колонку channel_id, которая не нужна
ALTER TABLE public.posts DROP COLUMN IF EXISTS channel_id;

-- Проверяем результат
SELECT
    'КОЛОНКИ ПОСЛЕ УДАЛЕНИЯ:' as status,
    column_name
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'posts'
AND column_name IN ('channel_id', 'channel_username')
ORDER BY column_name;

-- Проверяем foreign key constraint
SELECT
    'FOREIGN KEY CONSTRAINTS:' as status,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as referenced_table,
    ccu.column_name as referenced_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_schema = 'public'
AND tc.table_name = 'posts'
AND tc.constraint_type = 'FOREIGN KEY';
