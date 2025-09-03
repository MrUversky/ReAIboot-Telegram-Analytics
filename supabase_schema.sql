-- ReAIboot Telegram Analytics - Supabase Schema
-- This file contains the complete database schema for the application

-- Enable Row Level Security
-- Note: app.jwt_secret is automatically configured by Supabase

-- Create custom types
CREATE TYPE post_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE analysis_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer');
CREATE TYPE channel_baseline_status AS ENUM ('learning', 'ready', 'outdated');

-- SYSTEM SETTINGS TABLE
CREATE TABLE public.system_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    is_editable BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- CHANNEL BASELINES TABLE
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

-- Users table (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role user_role DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Telegram channels to monitor
CREATE TABLE public.channels (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    last_parsed TIMESTAMP WITH TIME ZONE,
    parse_frequency_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Parsed posts from Telegram
CREATE TABLE public.posts (
    id TEXT PRIMARY KEY, -- message_id + channel_username
    message_id BIGINT NOT NULL,
    channel_username TEXT NOT NULL,
    channel_title TEXT,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    text_preview TEXT,
    full_text TEXT,
    views INTEGER DEFAULT 0,
    forwards INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    participants_count INTEGER DEFAULT 0,
    has_media BOOLEAN DEFAULT false,
    media_urls TEXT[],
    permalink TEXT,
    raw_data JSONB,

    -- Viral detection metrics
    viral_score DECIMAL(5,2) DEFAULT 0,
    engagement_rate DECIMAL(5,4) DEFAULT 0,
    zscore DECIMAL(5,2) DEFAULT 0,
    median_multiplier DECIMAL(5,2) DEFAULT 1,
    last_viral_calculation TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,

    -- Indexes for performance
    CONSTRAINT fk_posts_channel FOREIGN KEY (channel_username) REFERENCES channels(username) ON DELETE CASCADE
);

-- Engagement metrics for posts
CREATE TABLE public.post_metrics (
    id SERIAL PRIMARY KEY,
    post_id TEXT REFERENCES public.posts(id) ON DELETE CASCADE,
    view_rate DECIMAL(5,4),
    reaction_rate DECIMAL(5,4),
    reply_rate DECIMAL(5,4),
    forward_rate DECIMAL(5,4),
    overall_score DECIMAL(5,4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,

    UNIQUE(post_id, calculated_at)
);

-- Content rubrics and formats
CREATE TABLE public.rubrics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE TABLE public.reel_formats (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    duration_seconds INTEGER DEFAULT 60,
    structure JSONB, -- JSON with scene breakdown
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Many-to-many relationship between rubrics and formats
CREATE TABLE public.rubric_formats (
    rubric_id TEXT REFERENCES public.rubrics(id) ON DELETE CASCADE,
    format_id TEXT REFERENCES public.reel_formats(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,

    PRIMARY KEY (rubric_id, format_id)
);

-- Post analysis results
CREATE TABLE public.post_analysis (
    id SERIAL PRIMARY KEY,
    post_id TEXT REFERENCES public.posts(id) ON DELETE CASCADE,
    status analysis_status DEFAULT 'pending',
    analysis_type TEXT, -- 'llm_filter', 'llm_analysis', 'llm_generation'

    -- Filter stage results
    is_suitable BOOLEAN,
    suitability_score DECIMAL(3,2),
    filter_reason TEXT,

    -- Analysis stage results
    success_factors JSONB, -- Why the post was successful
    audience_insights JSONB, -- Audience analysis
    content_quality_score DECIMAL(3,2),

    -- Generation stage results
    generated_scenarios JSONB, -- Array of generated scenarios
    selected_rubric_id TEXT,
    selected_format_id TEXT,

    -- LLM usage tracking
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(6,4) DEFAULT 0,
    model_used TEXT,
    processing_time_seconds DECIMAL(6,2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    processed_by UUID REFERENCES public.profiles(id),

    UNIQUE(post_id, analysis_type)
);

-- Generated scenarios/reels
CREATE TABLE public.scenarios (
    id SERIAL PRIMARY KEY,
    post_id TEXT REFERENCES public.posts(id) ON DELETE CASCADE,
    analysis_id INTEGER REFERENCES public.post_analysis(id) ON DELETE CASCADE,

    title TEXT NOT NULL,
    description TEXT,
    duration_seconds INTEGER DEFAULT 60,

    -- Scenario structure
    hook JSONB, -- Hook details
    insight JSONB, -- Key insight from analysis
    content JSONB, -- Main content breakdown
    call_to_action JSONB, -- CTA details

    -- Reel format info
    rubric_id TEXT,
    format_id TEXT,

    -- Quality and ratings
    quality_score DECIMAL(3,2),
    engagement_prediction DECIMAL(3,2),

    -- Status and metadata
    status TEXT DEFAULT 'draft', -- 'draft', 'approved', 'published', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    created_by UUID REFERENCES public.profiles(id),

    -- Full scenario data
    full_scenario JSONB
);

-- System monitoring and logs
CREATE TABLE public.system_logs (
    id SERIAL PRIMARY KEY,
    level TEXT NOT NULL, -- 'info', 'warning', 'error', 'critical'
    component TEXT NOT NULL, -- 'parser', 'llm', 'api', 'ui'
    message TEXT NOT NULL,
    details JSONB,
    user_id UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Token usage tracking
CREATE TABLE public.token_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id),
    model TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_usd DECIMAL(6,4) NOT NULL,
    operation_type TEXT NOT NULL, -- 'filter', 'analysis', 'generation'
    post_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Parsing sessions
CREATE TABLE public.parsing_sessions (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    channels_parsed INTEGER DEFAULT 0,
    posts_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT,
    initiated_by UUID REFERENCES public.profiles(id),
    configuration JSONB -- Store parsing parameters
);

-- Create indexes for better performance
CREATE INDEX idx_posts_channel_date ON public.posts(channel_username, date DESC);
CREATE INDEX idx_posts_date ON public.posts(date DESC);
CREATE INDEX idx_post_metrics_score ON public.post_metrics(overall_score DESC);
CREATE INDEX idx_post_analysis_status ON public.post_analysis(status);
CREATE INDEX idx_post_analysis_post ON public.post_analysis(post_id);
CREATE INDEX idx_scenarios_status ON public.scenarios(status);
CREATE INDEX idx_system_logs_level ON public.system_logs(level);
CREATE INDEX idx_system_logs_created ON public.system_logs(created_at DESC);
CREATE INDEX idx_token_usage_user ON public.token_usage(user_id);
CREATE INDEX idx_token_usage_created ON public.token_usage(created_at DESC);

-- Row Level Security (RLS) policies

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channel_baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reel_formats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rubric_formats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.parsing_sessions ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Channels policies (all authenticated users can read, only admins can modify)
CREATE POLICY "Authenticated users can view channels" ON public.channels
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Only admins can modify channels" ON public.channels
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Posts policies (all authenticated users can read, system can insert/update)
CREATE POLICY "Authenticated users can view posts" ON public.posts
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "System can insert posts" ON public.posts
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "System can update posts" ON public.posts
    FOR UPDATE TO authenticated USING (true);

--- System settings policies (only admins can modify)
CREATE POLICY "Authenticated users can view system settings" ON public.system_settings
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Only admins can modify system settings" ON public.system_settings
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

--- Channel baselines policies (authenticated users can read, system can modify)
CREATE POLICY "Authenticated users can view channel baselines" ON public.channel_baselines
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "System can modify channel baselines" ON public.channel_baselines
    FOR ALL TO authenticated WITH CHECK (true);

-- Allow service role and anon key to modify channel baselines for system operations
CREATE POLICY "Service role can manage channel baselines" ON public.channel_baselines
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Anon can insert channel baselines" ON public.channel_baselines
    FOR INSERT TO anon WITH CHECK (true);

-- Similar policies for other tables...
-- (You can add more specific policies based on your security requirements)

-- Functions for analytics and monitoring

-- Function to get token usage summary
CREATE OR REPLACE FUNCTION get_token_usage_summary(
    p_user_id UUID DEFAULT NULL,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_tokens BIGINT,
    total_cost DECIMAL(10,4),
    avg_cost_per_token DECIMAL(10,6),
    models_used TEXT[],
    operations_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        SUM(tokens_used)::BIGINT as total_tokens,
        SUM(cost_usd)::DECIMAL(10,4) as total_cost,
        (SUM(cost_usd) / NULLIF(SUM(tokens_used), 0))::DECIMAL(10,6) as avg_cost_per_token,
        ARRAY_AGG(DISTINCT model) as models_used,
        COUNT(*)::BIGINT as operations_count
    FROM public.token_usage
    WHERE (p_user_id IS NULL OR user_id = p_user_id)
    AND created_at >= NOW() - INTERVAL '1 day' * p_days;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get system health metrics
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS TABLE (
    total_posts BIGINT,
    posts_today BIGINT,
    active_channels BIGINT,
    recent_analysis BIGINT,
    avg_processing_time DECIMAL(6,2),
    error_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM public.posts)::BIGINT as total_posts,
        (SELECT COUNT(*) FROM public.posts WHERE date >= CURRENT_DATE)::BIGINT as posts_today,
        (SELECT COUNT(*) FROM public.channels WHERE is_active = true)::BIGINT as active_channels,
        (SELECT COUNT(*) FROM public.post_analysis WHERE created_at >= NOW() - INTERVAL '1 hour')::BIGINT as recent_analysis,
        (SELECT AVG(processing_time_seconds) FROM public.post_analysis WHERE processing_time_seconds IS NOT NULL)::DECIMAL(6,2) as avg_processing_time,
        (
            SELECT
                (COUNT(*) FILTER (WHERE status = 'failed')::DECIMAL /
                 NULLIF(COUNT(*), 0)::DECIMAL) * 100
            FROM public.post_analysis
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        )::DECIMAL(5,2) as error_rate;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if post was already processed
CREATE OR REPLACE FUNCTION is_post_processed(p_post_id TEXT, p_analysis_type TEXT DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.post_analysis
        WHERE post_id = p_post_id
        AND (p_analysis_type IS NULL OR analysis_type = p_analysis_type)
        AND status = 'completed'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to relevant tables
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON public.channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON public.posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rubrics_updated_at BEFORE UPDATE ON public.rubrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reel_formats_updated_at BEFORE UPDATE ON public.reel_formats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_analysis_updated_at BEFORE UPDATE ON public.post_analysis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenarios_updated_at BEFORE UPDATE ON public.scenarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON public.system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channel_baselines_updated_at BEFORE UPDATE ON public.channel_baselines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initialize default system settings
INSERT INTO public.system_settings (key, value, description, category) VALUES
('viral_weights', '{
  "forward_rate": 0.5,
  "reaction_rate": 0.3,
  "reply_rate": 0.2
}', 'Веса для расчета engagement rate (пересылки, реакции, комментарии)', 'viral_detection'),

('viral_thresholds', '{
  "min_viral_score": 1.5,
  "min_zscore": 1.5,
  "min_median_multiplier": 2.0,
  "min_views_percentile": 0.001
}', 'Пороги для определения "залетевших" постов', 'viral_detection'),

('baseline_calculation', '{
  "history_days": 30,
  "min_posts_for_baseline": 10,
  "outlier_removal_percentile": 95,
  "baseline_update_interval_hours": 24,
  "auto_baseline_update": true
}', 'Настройки расчета и обновления базовых метрик каналов', 'baseline_calculation'),

('viral_calculation', '{
  "auto_calculate_viral": true,
  "batch_size": 100,
  "update_existing_posts": false,
  "min_views_for_viral": 100
}', 'Настройки автоматического расчета метрик виральности', 'viral_calculation'),

('parsing_settings', '{
  "default_days_back": 30,
  "default_max_posts": 200,
  "auto_calculate_metrics": true,
  "auto_update_baselines": true,
  "concurrent_channels": 3
}', 'Настройки парсинга каналов и автоматической обработки', 'parsing'),

('channel_categories', '{
  "small": {"max_subscribers": 10000, "viral_multiplier": 1.0, "min_baseline_posts": 10},
  "medium": {"max_subscribers": 100000, "viral_multiplier": 1.2, "min_baseline_posts": 15},
  "large": {"max_subscribers": 1000000, "viral_multiplier": 1.5, "min_baseline_posts": 20},
  "huge": {"max_subscribers": 10000000, "viral_multiplier": 2.0, "min_baseline_posts": 25}
}', 'Категории каналов по размеру и их настройки', 'channel_categories'),

('llm_settings', '{
  "default_model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2000,
  "timeout_seconds": 60,
  "retry_attempts": 3,
  "rate_limit_per_minute": 60
}', 'Настройки LLM моделей для анализа и генерации', 'llm'),

('quality_thresholds', '{
  "min_content_score": 0.6,
  "min_engagement_prediction": 0.4,
  "auto_approve_threshold": 0.8,
  "require_human_review": true
}', 'Пороги качества для автоматического одобрения сценариев', 'quality_control')
ON CONFLICT (key) DO NOTHING;

-- ===============================================
-- МИГРАЦИЯ: Обновление существующих настроек
-- ===============================================

-- Обновляем существующие настройки новыми полями
UPDATE public.system_settings
SET value = value::jsonb || '{"baseline_update_interval_hours": 24, "auto_baseline_update": true}'::jsonb
WHERE key = 'baseline_calculation' AND NOT (value::jsonb ? 'baseline_update_interval_hours');

UPDATE public.system_settings
SET value = value::jsonb || '{"auto_calculate_viral": true, "batch_size": 100, "update_existing_posts": false, "min_views_for_viral": 100}'::jsonb
WHERE key = 'viral_calculation' AND NOT (value::jsonb ? 'auto_calculate_viral');

UPDATE public.system_settings
SET value = value::jsonb || '{"default_days_back": 30, "default_max_posts": 200, "auto_calculate_metrics": true, "auto_update_baselines": true, "concurrent_channels": 3}'::jsonb
WHERE key = 'parsing_settings' AND NOT (value::jsonb ? 'default_days_back');

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_posts_viral_score ON public.posts(viral_score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_channel_viral ON public.posts(channel_username, viral_score DESC);
CREATE INDEX IF NOT EXISTS idx_channel_baselines_status ON public.channel_baselines(baseline_status);
CREATE INDEX IF NOT EXISTS idx_posts_engagement_rate ON public.posts(engagement_rate DESC);

-- ===============================================
-- МИГРАЦИЯ: Исправление RLS политики для channel_baselines
-- ===============================================

-- Добавляем политики для service role и anon key
DROP POLICY IF EXISTS "Service role can manage channel baselines" ON public.channel_baselines;
DROP POLICY IF EXISTS "Anon can insert channel baselines" ON public.channel_baselines;
DROP POLICY IF EXISTS "Anon can update channel baselines" ON public.channel_baselines;

CREATE POLICY "Service role can manage channel baselines" ON public.channel_baselines
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Anon can insert channel baselines" ON public.channel_baselines
    FOR INSERT TO anon WITH CHECK (true);

-- Также добавляем политику для UPDATE операций через anon key
CREATE POLICY "Anon can update channel baselines" ON public.channel_baselines
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- ===============================================
-- ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ МИГРАЦИИ
-- ===============================================
--
-- 1. Подключитесь к Supabase SQL Editor
-- 2. Выполните этот файл целиком
-- 3. Или выполните команды по отдельности:
--
-- Для новых проектов:
-- psql -h [host] -U [user] -d [database] -f supabase_schema.sql
--
-- Для существующих проектов (только новые настройки):
-- Выполните блок "МИГРАЦИЯ" начиная со строки 514
--
-- 4. Проверьте, что настройки создались:
-- SELECT key, value FROM system_settings WHERE category = 'viral_detection';
--
-- 5. Для исправления RLS проблем выполните блок "МИГРАЦИЯ RLS" начиная со строки 570
--
-- ===============================================
