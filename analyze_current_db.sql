-- АНАЛИЗ ТЕКУЩЕЙ СТРУКТУРЫ БАЗЫ ДАННЫХ ReAIboot
-- Выполните этот скрипт в Supabase SQL Editor для диагностики

-- 1. АНАЛИЗ СУЩЕСТВУЮЩИХ ОБЪЕКТОВ
SELECT '=== АНАЛИЗ СТРУКТУРЫ БАЗЫ ДАННЫХ ===' as header;

-- 2. ПРОВЕРКА ТИПОВ
SELECT
    'ТИПЫ:' as section,
    t.typname as name,
    CASE
        WHEN t.typtype = 'e' THEN 'ENUM'
        WHEN t.typtype = 'c' THEN 'COMPOSITE'
        WHEN t.typtype = 'd' THEN 'DOMAIN'
        ELSE 'OTHER'
    END as type,
    CASE
        WHEN t.typname LIKE '%status' THEN '✅ НУЖЕН ДЛЯ VIRAL DETECTION'
        ELSE 'ℹ️ СУЩЕСТВУЮЩИЙ'
    END as status
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY t.typname;

-- 3. ПРОВЕРКА ТАБЛИЦ
SELECT
    'ТАБЛИЦЫ:' as section,
    tablename as name,
    CASE
        WHEN tablename IN ('system_settings', 'channel_baselines') THEN '✅ НУЖНА ДЛЯ VIRAL DETECTION'
        WHEN tablename IN ('posts', 'channels', 'profiles') THEN '✅ ОСНОВНАЯ СИСТЕМА'
        ELSE 'ℹ️ СУЩЕСТВУЮЩАЯ'
    END as status,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 4. ПРОВЕРКА КОЛОНОК В POSTS (КЛЮЧЕВАЯ ТАБЛИЦА)
SELECT
    'КОЛОНКИ POSTS:' as section,
    column_name as name,
    data_type,
    is_nullable,
    CASE
        WHEN column_name IN ('viral_score', 'engagement_rate', 'zscore', 'median_multiplier', 'last_viral_calculation') THEN '✅ НУЖНА ДЛЯ VIRAL DETECTION'
        WHEN column_name IN ('id', 'message_id', 'channel_username', 'text_preview', 'views', 'reactions', 'replies', 'forwards') THEN '✅ ОСНОВНАЯ СИСТЕМА'
        ELSE 'ℹ️ СУЩЕСТВУЮЩАЯ'
    END as status
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'posts'
ORDER BY ordinal_position;

-- 5. ПРОВЕРКА ПОЛИТИК RLS
SELECT
    'POLICIES RLS:' as section,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 6. РЕЗЮМЕ ПО ГОТОВНОСТИ К VIRAL DETECTION
WITH checks AS (
    SELECT
        'system_settings table' as check_name,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables
                         WHERE table_schema = 'public' AND table_name = 'system_settings')
             THEN '✅ СУЩЕСТВУЕТ' ELSE '❌ НЕТ - НУЖНО СОЗДАТЬ' END as status
    UNION ALL
    SELECT
        'channel_baselines table' as check_name,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables
                         WHERE table_schema = 'public' AND table_name = 'channel_baselines')
             THEN '✅ СУЩЕСТВУЕТ' ELSE '❌ НЕТ - НУЖНО СОЗДАТЬ' END as status
    UNION ALL
    SELECT
        'channel_baseline_status type' as check_name,
        CASE WHEN EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_baseline_status')
             THEN '✅ СУЩЕСТВУЕТ' ELSE '❌ НЕТ - НУЖНО СОЗДАТЬ' END as status
    UNION ALL
    SELECT
        'viral_score column in posts' as check_name,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'viral_score')
             THEN '✅ СУЩЕСТВУЕТ' ELSE '❌ НЕТ - НУЖНО ДОБАВИТЬ' END as status
    UNION ALL
    SELECT
        'engagement_rate column in posts' as check_name,
        CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'engagement_rate')
             THEN '✅ СУЩЕСТВУЕТ' ELSE '❌ НЕТ - НУЖНО ДОБАВИТЬ' END as status
)
SELECT
    '=== ГОТОВНОСТЬ К VIRAL DETECTION ===' as header,
    check_name,
    status
FROM checks
ORDER BY
    CASE
        WHEN status LIKE '❌%' THEN 1
        WHEN status LIKE '✅%' THEN 2
        ELSE 3
    END;

-- 7. РЕКОМЕНДАЦИИ
SELECT '=== РЕКОМЕНДАЦИИ ===' as header;

-- Проверяем, нужно ли выполнять основной скрипт или безопасный
SELECT
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'system_settings')
             OR NOT EXISTS (SELECT 1 FROM information_schema.tables
                           WHERE table_schema = 'public' AND table_name = 'channel_baselines')
             OR NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'viral_score')
        THEN '⚠️ ВЫПОЛНИТЕ safe_schema_update.sql ДЛЯ ДОБАВЛЕНИЯ НЕДОСТАЮЩИХ ОБЪЕКТОВ'
        ELSE '✅ ВСЕ НЕОБХОДИМЫЕ ОБЪЕКТЫ СУЩЕСТВУЮТ - VIRAL DETECTION ГОТОВ К РАБОТЕ'
    END as recommendation;

-- Проверяем данные в настройках
SELECT
    CASE
        WHEN NOT EXISTS (SELECT 1 FROM public.system_settings WHERE key = 'viral_weights')
        THEN '⚠️ НЕТ НАСТРОЕК VIRAL WEIGHTS - БУДУТ ИСПОЛЬЗОВАНЫ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ'
        ELSE '✅ НАСТРОЙКИ VIRAL WEIGHTS СУЩЕСТВУЮТ'
    END as settings_status;
