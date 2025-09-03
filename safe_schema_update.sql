-- БЕЗОПАСНОЕ ОБНОВЛЕНИЕ СХЕМЫ ReAIboot
-- Этот скрипт проверяет существующие объекты и создает только недостающие

-- 1. ПРОВЕРКА И СОЗДАНИЕ ТИПОВ (с проверкой существования)
DO $$
BEGIN
    -- Создаем тип channel_baseline_status, если он не существует
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_baseline_status') THEN
        CREATE TYPE public.channel_baseline_status AS ENUM ('learning', 'ready', 'outdated');
        RAISE NOTICE 'Created type: channel_baseline_status';
    ELSE
        RAISE NOTICE 'Type channel_baseline_status already exists - skipping';
    END IF;
END $$;

-- 2. СОЗДАНИЕ ТАБЛИЦЫ SYSTEM_SETTINGS (с проверкой)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_name = 'system_settings') THEN
        CREATE TABLE public.system_settings (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            is_editable BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        RAISE NOTICE 'Created table: system_settings';
    ELSE
        RAISE NOTICE 'Table system_settings already exists - skipping';
    END IF;
END $$;

-- 3. СОЗДАНИЕ ТАБЛИЦЫ CHANNEL_BASELINES (с проверкой)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_name = 'channel_baselines') THEN
        CREATE TABLE public.channel_baselines (
            channel_username TEXT PRIMARY KEY,
            subscribers_count INTEGER,
            posts_analyzed INTEGER DEFAULT 0,
            avg_engagement_rate DECIMAL(5,4) DEFAULT 0,
            median_engagement_rate DECIMAL(5,4) DEFAULT 0,
            std_engagement_rate DECIMAL(5,4) DEFAULT 0,
            p75_engagement_rate DECIMAL(5,4) DEFAULT 0,
            p95_engagement_rate DECIMAL(5,4) DEFAULT 0,
            max_engagement_rate DECIMAL(5,4) DEFAULT 0,
            baseline_status channel_baseline_status DEFAULT 'learning',
            calculation_period_days INTEGER DEFAULT 30,
            min_posts_for_baseline INTEGER DEFAULT 10,
            last_calculated TIMESTAMP WITH TIME ZONE,
            next_calculation TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        RAISE NOTICE 'Created table: channel_baselines';
    ELSE
        RAISE NOTICE 'Table channel_baselines already exists - skipping';
    END IF;
END $$;

-- 4. ДОБАВЛЕНИЕ КОЛОНОК В СУЩЕСТВУЮЩУЮ ТАБЛИЦУ POSTS (с проверкой)
DO $$
BEGIN
    -- Проверяем и добавляем колонку viral_score
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'viral_score') THEN
        ALTER TABLE public.posts ADD COLUMN viral_score DECIMAL(5,2) DEFAULT 0;
        RAISE NOTICE 'Added column: posts.viral_score';
    ELSE
        RAISE NOTICE 'Column posts.viral_score already exists - skipping';
    END IF;

    -- Проверяем и добавляем колонку engagement_rate
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'engagement_rate') THEN
        ALTER TABLE public.posts ADD COLUMN engagement_rate DECIMAL(5,4) DEFAULT 0;
        RAISE NOTICE 'Added column: posts.engagement_rate';
    ELSE
        RAISE NOTICE 'Column posts.engagement_rate already exists - skipping';
    END IF;

    -- Проверяем и добавляем колонку zscore
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'zscore') THEN
        ALTER TABLE public.posts ADD COLUMN zscore DECIMAL(5,2) DEFAULT 0;
        RAISE NOTICE 'Added column: posts.zscore';
    ELSE
        RAISE NOTICE 'Column posts.zscore already exists - skipping';
    END IF;

    -- Проверяем и добавляем колонку median_multiplier
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'median_multiplier') THEN
        ALTER TABLE public.posts ADD COLUMN median_multiplier DECIMAL(5,2) DEFAULT 1;
        RAISE NOTICE 'Added column: posts.median_multiplier';
    ELSE
        RAISE NOTICE 'Column posts.median_multiplier already exists - skipping';
    END IF;

    -- Проверяем и добавляем колонку last_viral_calculation
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'last_viral_calculation') THEN
        ALTER TABLE public.posts ADD COLUMN last_viral_calculation TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added column: posts.last_viral_calculation';
    ELSE
        RAISE NOTICE 'Column posts.last_viral_calculation already exists - skipping';
    END IF;
END $$;

-- 5. ВКЛЮЧЕНИЕ RLS ДЛЯ НОВЫХ ТАБЛИЦ
DO $$
BEGIN
    -- Включаем RLS для system_settings
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
                   WHERE n.nspname = 'public' AND c.relname = 'system_settings' AND c.relrowsecurity = true) THEN
        ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'Enabled RLS for system_settings';
    ELSE
        RAISE NOTICE 'RLS already enabled for system_settings';
    END IF;

    -- Включаем RLS для channel_baselines
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
                   WHERE n.nspname = 'public' AND c.relname = 'channel_baselines' AND c.relrowsecurity = true) THEN
        ALTER TABLE public.channel_baselines ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'Enabled RLS for channel_baselines';
    ELSE
        RAISE NOTICE 'RLS already enabled for channel_baselines';
    END IF;
END $$;

-- 6. СОЗДАНИЕ ПОЛИТИК RLS (с проверкой существования)
DO $$
BEGIN
    -- Политики для system_settings
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'system_settings' AND policyname = 'Authenticated users can view system settings') THEN
        CREATE POLICY "Authenticated users can view system settings" ON public.system_settings
            FOR SELECT TO authenticated USING (true);
        RAISE NOTICE 'Created policy: system_settings view';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'system_settings' AND policyname = 'Only admins can modify system settings') THEN
        CREATE POLICY "Only admins can modify system settings" ON public.system_settings
            FOR ALL TO authenticated USING (
                EXISTS (
                    SELECT 1 FROM public.profiles
                    WHERE id = auth.uid() AND role = 'admin'
                )
            );
        RAISE NOTICE 'Created policy: system_settings modify';
    END IF;

    -- Политики для channel_baselines
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'channel_baselines' AND policyname = 'Authenticated users can view channel baselines') THEN
        CREATE POLICY "Authenticated users can view channel baselines" ON public.channel_baselines
            FOR SELECT TO authenticated USING (true);
        RAISE NOTICE 'Created policy: channel_baselines view';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'channel_baselines' AND policyname = 'System can modify channel baselines') THEN
        CREATE POLICY "System can modify channel baselines" ON public.channel_baselines
            FOR ALL TO authenticated WITH CHECK (true);
        RAISE NOTICE 'Created policy: channel_baselines modify';
    END IF;
END $$;

-- 7. СОЗДАНИЕ ТРИГГЕРОВ (с проверкой существования)
DO $$
BEGIN
    -- Триггер для system_settings
    IF NOT EXISTS (SELECT 1 FROM information_schema.triggers
                   WHERE event_object_table = 'system_settings' AND trigger_name = 'update_system_settings_updated_at') THEN
        CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON public.system_settings
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Created trigger: system_settings updated_at';
    END IF;

    -- Триггер для channel_baselines
    IF NOT EXISTS (SELECT 1 FROM information_schema.triggers
                   WHERE event_object_table = 'channel_baselines' AND trigger_name = 'update_channel_baselines_updated_at') THEN
        CREATE TRIGGER update_channel_baselines_updated_at BEFORE UPDATE ON public.channel_baselines
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Created trigger: channel_baselines updated_at';
    END IF;
END $$;

-- 8. ИНИЦИАЛИЗАЦИЯ НАСТРОЕК ПО УМОЛЧАНИЮ
INSERT INTO public.system_settings (key, value, description, category) VALUES
('viral_weights', '{
  "forward_rate": 0.5,
  "reaction_rate": 0.3,
  "reply_rate": 0.2
}', 'Веса для расчета engagement rate', 'viral_detection')
ON CONFLICT (key) DO NOTHING;

INSERT INTO public.system_settings (key, value, description, category) VALUES
('viral_thresholds', '{
  "min_viral_score": 1.5,
  "min_zscore": 1.5,
  "min_median_multiplier": 2.0,
  "min_views_percentile": 0.001
}', 'Пороги для определения "залетевших" постов', 'viral_detection')
ON CONFLICT (key) DO NOTHING;

INSERT INTO public.system_settings (key, value, description, category) VALUES
('baseline_calculation', '{
  "history_days": 30,
  "min_posts_for_baseline": 10,
  "outlier_removal_percentile": 95
}', 'Настройки расчета базовых метрик каналов', 'baseline_calculation')
ON CONFLICT (key) DO NOTHING;

INSERT INTO public.system_settings (key, value, description, category) VALUES
('channel_categories', '{
  "small": {"max_subscribers": 10000, "viral_multiplier": 1.0},
  "medium": {"max_subscribers": 100000, "viral_multiplier": 1.2},
  "large": {"max_subscribers": 1000000, "viral_multiplier": 1.5}
}', 'Категории каналов по размеру', 'channel_categories')
ON CONFLICT (key) DO NOTHING;

-- 9. ПРОВЕРКА РЕЗУЛЬТАТА
SELECT 'SYSTEM UPDATE COMPLETED' as status, NOW() as completed_at;

-- Показываем созданные объекты
SELECT
    'Tables created/updated:' as info,
    COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('system_settings', 'channel_baselines');

-- Показываем новые колонки в posts
SELECT
    'New columns in posts:' as info,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'posts'
AND column_name IN ('viral_score', 'engagement_rate', 'zscore', 'median_multiplier', 'last_viral_calculation')
ORDER BY column_name;
