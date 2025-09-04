-- Фикс политик RLS для таблиц rubrics и reel_formats
-- Выполните этот скрипт в Supabase Dashboard -> SQL Editor

-- Политики для таблицы rubrics
CREATE POLICY "Authenticated users can view rubrics" ON rubrics
FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage rubrics" ON rubrics
FOR ALL TO authenticated USING (
    EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
        AND profiles.role = 'admin'
    )
);

-- Политики для таблицы reel_formats
CREATE POLICY "Authenticated users can view formats" ON reel_formats
FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage formats" ON reel_formats
FOR ALL TO authenticated USING (
    EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
        AND profiles.role = 'admin'
    )
);

