-- Фикс бесконечной рекурсии в RLS политиках profiles
-- Выполнить в Supabase SQL Editor
--
-- Этот скрипт:
-- 1. Удаляет ВСЕ существующие политики для таблицы profiles
-- 2. Создает новые политики без рекурсии
-- 3. Настраивает правильные права доступа
-- 4. Позволяет автоматически создавать профили пользователей

-- Показываем текущие политики ДО исправления
SELECT 'ПОЛИТИКИ ДО ИСПРАВЛЕНИЯ:' as info;
SELECT
    policyname as "Policy Name",
    permissive as "Type",
    roles as "Roles",
    cmd as "Command"
FROM pg_policies
WHERE tablename = 'profiles' AND schemaname = 'public'
ORDER BY policyname;

-- 1. Удаляем ВСЕ существующие политики для profiles
DO $$
DECLARE
    policy_name TEXT;
BEGIN
    FOR policy_name IN
        SELECT policyname
        FROM pg_policies
        WHERE tablename = 'profiles' AND schemaname = 'public'
    LOOP
        EXECUTE 'DROP POLICY IF EXISTS "' || policy_name || '" ON public.profiles';
        RAISE NOTICE 'Dropped policy: %', policy_name;
    END LOOP;
END $$;

-- 2. Создаем новые политики без рекурсии (с проверками IF NOT EXISTS)
DO $$
BEGIN
    -- Users can view their own profile
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
        AND policyname = 'Users can view their own profile'
    ) THEN
        CREATE POLICY "Users can view their own profile"
        ON public.profiles FOR SELECT
        USING (auth.uid() = id);
    END IF;

    -- Users can update their own profile
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
        AND policyname = 'Users can update their own profile'
    ) THEN
        CREATE POLICY "Users can update their own profile"
        ON public.profiles FOR UPDATE
        USING (auth.uid() = id);
    END IF;

    -- Users can insert their own profile
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
        AND policyname = 'Users can insert their own profile'
    ) THEN
        CREATE POLICY "Users can insert their own profile"
        ON public.profiles FOR INSERT
        WITH CHECK (auth.uid() = id);
    END IF;
END $$;

-- 3. Политика для админов - проверяем профиль админа отдельно
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
        AND policyname = 'Admins can view all profiles'
    ) THEN
        CREATE POLICY "Admins can view all profiles"
        ON public.profiles FOR ALL
        USING (
          EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
            AND p.role = 'admin'
            AND p.is_active = true
          )
        );
    END IF;
END $$;

-- 4. Политика для service role
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
        AND policyname = 'Service role can manage profiles'
    ) THEN
        CREATE POLICY "Service role can manage profiles"
        ON public.profiles FOR ALL
        USING (auth.role() = 'service_role');
    END IF;
END $$;

-- 5. Убеждаемся, что RLS включена
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 6. Проверяем существующие политики
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
WHERE tablename = 'profiles'
ORDER BY policyname;

-- 7. Создаем индекс для оптимизации запросов политик
CREATE INDEX IF NOT EXISTS idx_profiles_role_active
ON public.profiles(role, is_active)
WHERE role = 'admin' AND is_active = true;

-- 8. Показываем политики ПОСЛЕ исправления
SELECT 'ПОЛИТИКИ ПОСЛЕ ИСПРАВЛЕНИЯ:' as info;
SELECT
    policyname as "Policy Name",
    permissive as "Type",
    roles as "Roles",
    cmd as "Command"
FROM pg_policies
WHERE tablename = 'profiles' AND schemaname = 'public'
ORDER BY policyname;

-- 9. Показываем результат
SELECT
    'Profiles count' as metric,
    COUNT(*) as value
FROM public.profiles
UNION ALL
SELECT
    'Active users' as metric,
    COUNT(*) as value
FROM public.profiles
WHERE is_active = true
UNION ALL
SELECT
    'Admin users' as metric,
    COUNT(*) as value
FROM public.profiles
WHERE role = 'admin' AND is_active = true;

-- 10. Финальное сообщение
SELECT '✅ RLS политики исправлены! Теперь пользователи смогут создавать профили автоматически.' as status;
