-- 🔒 АУДИТ БЕЗОПАСНОСТИ RLS ПОЛИТИК
-- Выполнить в Supabase SQL Editor

-- 1. ПРОВЕРИТЬ ТЕКУЩИЕ ПОЛИТИКИ
SELECT
    '📋 ТЕКУЩИЕ ПОЛИТИКИ profiles:' as info,
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'profiles'
ORDER BY policyname;

-- 2. ПРОВЕРИТЬ СОДЕРЖИМОЕ ПРОФИЛЕЙ (анонимный доступ)
SELECT '👥 ПРОФИЛИ ВИДИМЫЕ АНОНИМАМ:' as info, COUNT(*) as count FROM public.profiles;

-- 3. ПРОВЕРИТЬ RLS ВКЛЮЧЕН
SELECT
    '🔐 RLS СТАТУС:' as info,
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'profiles';

-- 4. ТЕСТ ПОЛИТИК ЧЕРЕЗ АУТЕНТИФИКАЦИЮ
-- (Это нужно выполнить отдельно в приложении)
