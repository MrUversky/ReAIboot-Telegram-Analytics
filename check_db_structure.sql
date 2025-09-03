-- ПРОВЕРКА ТЕКУЩЕЙ СТРУКТУРЫ БАЗЫ ДАННЫХ
-- Выполните этот скрипт в Supabase SQL Editor

-- 1. ПРОВЕРКА СУЩЕСТВУЮЩИХ ТИПОВ
SELECT
    t.typname as type_name,
    t.typtype as type_type,
    CASE
        WHEN t.typtype = 'e' THEN 'enum'
        WHEN t.typtype = 'c' THEN 'composite'
        WHEN t.typtype = 'd' THEN 'domain'
        ELSE 'other'
    END as type_description
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY t.typname;

-- 2. ПРОВЕРКА СУЩЕСТВУЮЩИХ ТАБЛИЦ
SELECT
    schemaname,
    tablename,
    tableowner,
    tablespace,
    hasindexes,
    hasrules,
    hastriggers,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 3. ПРОВЕРКА СТОЛБЦОВ В КЛЮЧЕВЫХ ТАБЛИЦАХ
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN ('posts', 'channels', 'profiles')
ORDER BY table_name, ordinal_position;

-- 4. ПРОВЕРКА ИНДЕКСОВ
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 5. ПРОВЕРКА ОГРАНИЧЕНИЙ
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;
