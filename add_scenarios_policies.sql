-- Добавление политик безопасности для таблицы scenarios
-- Выполнить в Supabase SQL Editor

-- Удалить существующие политики если они есть
DROP POLICY IF EXISTS "Authenticated users can view scenarios" ON public.scenarios;
DROP POLICY IF EXISTS "Only admins can modify scenarios" ON public.scenarios;

-- Создать политики для чтения сценариев аутентифицированными пользователями
CREATE POLICY "Authenticated users can view scenarios" ON public.scenarios
    FOR SELECT TO authenticated USING (true);

-- Только админы могут изменять сценарии
CREATE POLICY "Only admins can modify scenarios" ON public.scenarios
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Сервис роль может управлять сценариями для системных операций
CREATE POLICY "Service role can manage scenarios" ON public.scenarios
    FOR ALL TO service_role USING (true) WITH CHECK (true);

