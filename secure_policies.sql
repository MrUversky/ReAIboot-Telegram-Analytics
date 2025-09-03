-- 🛡️ БЕЗОПАСНЫЕ RLS ПОЛИТИКИ
-- Выполнить в Supabase SQL Editor

-- ОЧИСТИТЬ СТАРЫЕ ПОЛИТИКИ
DO $$
DECLARE
    policy_record RECORD;
BEGIN
    FOR policy_record IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'profiles'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
                      policy_record.policyname,
                      policy_record.schemaname,
                      policy_record.tablename);
        RAISE NOTICE 'Удалена политика: %', policy_record.policyname;
    END LOOP;
END $$;

-- СОЗДАТЬ БЕЗОПАСНЫЕ ПОЛИТИКИ
-- 1. Service role имеет полный доступ (для админки)
CREATE POLICY "service_role_full_access" ON public.profiles
FOR ALL USING (auth.role() = 'service_role');

-- 2. Пользователи могут читать ТОЛЬКО свой профиль
CREATE POLICY "user_read_own" ON public.profiles
FOR SELECT USING (auth.uid() = id);

-- 3. Пользователи могут обновлять ТОЛЬКО свой профиль
CREATE POLICY "user_update_own" ON public.profiles
FOR UPDATE USING (auth.uid() = id);

-- 4. Пользователи могут создавать ТОЛЬКО свой профиль
CREATE POLICY "user_create_own" ON public.profiles
FOR INSERT WITH CHECK (auth.uid() = id);

-- 5. Администраторы могут читать все профили
CREATE POLICY "admin_read_all" ON public.profiles
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid()
        AND role = 'admin'
        AND is_active = true
    )
);

-- 6. Администраторы могут обновлять все профили
CREATE POLICY "admin_update_all" ON public.profiles
FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid()
        AND role = 'admin'
        AND is_active = true
    )
);

-- ПРОВЕРКА РЕЗУЛЬТАТА
SELECT
    '✅ Новые политики:' as status,
    COUNT(*) as count
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'profiles';
