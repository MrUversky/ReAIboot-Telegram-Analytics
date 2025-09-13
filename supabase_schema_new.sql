-- ReAIboot Telegram Analytics - АКТУАЛЬНАЯ СХЕМА БАЗЫ ДАННЫХ
-- Сгенерировано автоматически из Supabase на 2025-09-13
-- НЕ РЕДАКТИРОВАТЬ ВРУЧНУЮ - используется для развертывания

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

-- Enable RLS
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;

-- Create policies for system_settings
CREATE POLICY "Authenticated users can view system_settings" ON system_settings
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Only admins can modify system_settings" ON system_settings
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- CHANNELS TABLE
CREATE TABLE public.channels (
    username TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    category TEXT,
    last_parsed TIMESTAMP WITH TIME ZONE,
    id SERIAL PRIMARY KEY,
    is_active BOOLEAN DEFAULT true,
    parse_frequency_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;

-- Create policies for channels
CREATE POLICY "Authenticated users can view channels" ON channels
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage channels" ON channels
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- PROFILES TABLE (extends auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    role user_role DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}'
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for profiles
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON profiles
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- POSTS TABLE
CREATE TABLE public.posts (
    id TEXT PRIMARY KEY,
    message_id BIGINT NOT NULL,
    channel_username TEXT NOT NULL,
    channel_title TEXT,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    text_preview TEXT,
    full_text TEXT,
    media_urls TEXT[],
    permalink TEXT,
    raw_data JSONB,
    views INTEGER DEFAULT 0,
    forwards INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    participants_count INTEGER DEFAULT 0,
    has_media BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    viral_score NUMERIC DEFAULT 0,
    engagement_rate NUMERIC DEFAULT 0,
    zscore NUMERIC,
    median_multiplier NUMERIC DEFAULT 1,
    last_viral_calculation TIMESTAMP WITH TIME ZONE
);

-- Enable RLS
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

-- Create policies for posts
CREATE POLICY "Authenticated users can view posts" ON posts
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage posts" ON posts
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.posts ADD CONSTRAINT fk_posts_channel
    FOREIGN KEY (channel_username) REFERENCES public.channels(username);

-- POST_METRICS TABLE
CREATE TABLE public.post_metrics (
    post_id TEXT,
    view_rate NUMERIC,
    reaction_rate NUMERIC,
    reply_rate NUMERIC,
    forward_rate NUMERIC,
    overall_score NUMERIC,
    id SERIAL PRIMARY KEY,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.post_metrics ENABLE ROW LEVEL SECURITY;

-- Create policies for post_metrics
CREATE POLICY "Authenticated users can view post_metrics" ON post_metrics
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage post_metrics" ON post_metrics
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.post_metrics ADD CONSTRAINT post_metrics_post_id_fkey
    FOREIGN KEY (post_id) REFERENCES public.posts(id);

-- RUBRICS TABLE
CREATE TABLE public.rubrics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.rubrics ENABLE ROW LEVEL SECURITY;

-- Create policies for rubrics
CREATE POLICY "Authenticated users can view rubrics" ON rubrics
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage rubrics" ON rubrics
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- REEL_FORMATS TABLE
CREATE TABLE public.reel_formats (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    structure JSONB,
    duration_seconds INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.reel_formats ENABLE ROW LEVEL SECURITY;

-- Create policies for reel_formats
CREATE POLICY "Authenticated users can view reel_formats" ON reel_formats
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage reel_formats" ON reel_formats
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- RUBRIC_FORMATS TABLE (junction table)
CREATE TABLE public.rubric_formats (
    rubric_id TEXT NOT NULL,
    format_id TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    PRIMARY KEY (rubric_id, format_id)
);

-- Enable RLS
ALTER TABLE public.rubric_formats ENABLE ROW LEVEL SECURITY;

-- Create policies for rubric_formats
CREATE POLICY "Authenticated users can view rubric_formats" ON rubric_formats
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage rubric_formats" ON rubric_formats
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraints
ALTER TABLE public.rubric_formats ADD CONSTRAINT rubric_formats_rubric_id_fkey
    FOREIGN KEY (rubric_id) REFERENCES public.rubrics(id);

ALTER TABLE public.rubric_formats ADD CONSTRAINT rubric_formats_format_id_fkey
    FOREIGN KEY (format_id) REFERENCES public.reel_formats(id);

-- POST_ANALYSIS TABLE
CREATE TABLE public.post_analysis (
    post_id TEXT,
    analysis_type TEXT,
    is_suitable BOOLEAN,
    suitability_score NUMERIC,
    filter_reason TEXT,
    success_factors JSONB,
    audience_insights JSONB,
    content_quality_score NUMERIC,
    generated_scenarios JSONB,
    selected_rubric_id TEXT,
    selected_format_id TEXT,
    model_used TEXT,
    processing_time_seconds NUMERIC,
    processed_by UUID,
    id SERIAL PRIMARY KEY,
    status analysis_status DEFAULT 'pending',
    tokens_used INTEGER DEFAULT 0,
    cost_usd NUMERIC DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.post_analysis ENABLE ROW LEVEL SECURITY;

-- Create policies for post_analysis
CREATE POLICY "Authenticated users can view post_analysis" ON post_analysis
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage post_analysis" ON post_analysis
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraints
ALTER TABLE public.post_analysis ADD CONSTRAINT post_analysis_post_id_fkey
    FOREIGN KEY (post_id) REFERENCES public.posts(id);

ALTER TABLE public.post_analysis ADD CONSTRAINT post_analysis_processed_by_fkey
    FOREIGN KEY (processed_by) REFERENCES public.profiles(id);

-- SCENARIOS TABLE
CREATE TABLE public.scenarios (
    post_id TEXT,
    analysis_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    hook JSONB,
    insight JSONB,
    content JSONB,
    call_to_action JSONB,
    rubric_id TEXT,
    format_id TEXT,
    quality_score NUMERIC,
    engagement_prediction NUMERIC,
    created_by UUID,
    full_scenario JSONB,
    id SERIAL PRIMARY KEY,
    duration_seconds INTEGER DEFAULT 60,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.scenarios ENABLE ROW LEVEL SECURITY;

-- Create policies for scenarios
CREATE POLICY "Authenticated users can view scenarios" ON scenarios
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can create scenarios" ON scenarios
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Users can update their own scenarios" ON scenarios
    FOR UPDATE TO authenticated USING (created_by = auth.uid());

CREATE POLICY "Admins can manage all scenarios" ON scenarios
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraints
ALTER TABLE public.scenarios ADD CONSTRAINT scenarios_post_id_fkey
    FOREIGN KEY (post_id) REFERENCES public.posts(id);

ALTER TABLE public.scenarios ADD CONSTRAINT scenarios_analysis_id_fkey
    FOREIGN KEY (analysis_id) REFERENCES public.post_analysis(id);

ALTER TABLE public.scenarios ADD CONSTRAINT scenarios_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES public.profiles(id);

-- SYSTEM_LOGS TABLE
CREATE TABLE public.system_logs (
    level TEXT NOT NULL,
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    user_id UUID,
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for system_logs
CREATE POLICY "Admins can view system_logs" ON system_logs
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.system_logs ADD CONSTRAINT system_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.profiles(id);

-- TOKEN_USAGE TABLE
CREATE TABLE public.token_usage (
    user_id UUID,
    model TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_usd NUMERIC NOT NULL,
    operation_type TEXT NOT NULL,
    post_id TEXT,
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;

-- Create policies for token_usage
CREATE POLICY "Users can view their own token_usage" ON token_usage
    FOR SELECT TO authenticated USING (user_id = auth.uid());

CREATE POLICY "Admins can view all token_usage" ON token_usage
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.token_usage ADD CONSTRAINT token_usage_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.profiles(id);

-- PARSING_SESSIONS TABLE
CREATE TABLE public.parsing_sessions (
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    initiated_by UUID,
    configuration JSONB,
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    channels_parsed INTEGER DEFAULT 0,
    posts_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running'
);

-- Enable RLS
ALTER TABLE public.parsing_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies for parsing_sessions
CREATE POLICY "Users can view their own parsing_sessions" ON parsing_sessions
    FOR SELECT TO authenticated USING (initiated_by = auth.uid());

CREATE POLICY "Admins can view all parsing_sessions" ON parsing_sessions
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.parsing_sessions ADD CONSTRAINT parsing_sessions_initiated_by_fkey
    FOREIGN KEY (initiated_by) REFERENCES public.profiles(id);

-- LLM_PROMPTS TABLE
CREATE TABLE public.llm_prompts (
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    prompt_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_by UUID,
    id SERIAL PRIMARY KEY,
    model TEXT DEFAULT 'gpt-4o-mini',
    temperature NUMERIC DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    version INTEGER DEFAULT 1,
    category TEXT DEFAULT 'general',
    variables JSONB DEFAULT '{}',
    model_settings JSONB DEFAULT '{}',
    is_system BOOLEAN DEFAULT false,
    system_prompt TEXT,
    user_prompt TEXT
);

-- Enable RLS
ALTER TABLE public.llm_prompts ENABLE ROW LEVEL SECURITY;

-- Create policies for llm_prompts
CREATE POLICY "Authenticated users can view llm_prompts" ON llm_prompts
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can create llm_prompts" ON llm_prompts
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Users can update their own llm_prompts" ON llm_prompts
    FOR UPDATE TO authenticated USING (created_by = auth.uid());

CREATE POLICY "Admins can manage all llm_prompts" ON llm_prompts
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Foreign key constraint
ALTER TABLE public.llm_prompts ADD CONSTRAINT llm_prompts_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES public.profiles(id);

-- CHANNEL_BASELINES TABLE
CREATE TABLE public.channel_baselines (
    channel_username TEXT PRIMARY KEY,
    subscribers_count INTEGER,
    last_calculated TIMESTAMP WITH TIME ZONE,
    next_calculation TIMESTAMP WITH TIME ZONE,
    posts_analyzed INTEGER DEFAULT 0,
    avg_engagement_rate NUMERIC DEFAULT 0,
    median_engagement_rate NUMERIC DEFAULT 0,
    std_engagement_rate NUMERIC DEFAULT 0,
    p75_engagement_rate NUMERIC DEFAULT 0,
    p95_engagement_rate NUMERIC DEFAULT 0,
    max_engagement_rate NUMERIC DEFAULT 0,
    baseline_status channel_baseline_status DEFAULT 'learning',
    calculation_period_days INTEGER DEFAULT 30,
    min_posts_for_baseline INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.channel_baselines ENABLE ROW LEVEL SECURITY;

-- Create policies for channel_baselines
CREATE POLICY "Authenticated users can view channel_baselines" ON channel_baselines
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admins can manage channel_baselines" ON channel_baselines
    FOR ALL TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- Create indexes for better performance
CREATE INDEX idx_posts_channel_username ON posts(channel_username);
CREATE INDEX idx_posts_date ON posts(date);
CREATE INDEX idx_posts_viral_score ON posts(viral_score);
CREATE INDEX idx_post_analysis_post_id ON post_analysis(post_id);
CREATE INDEX idx_scenarios_post_id ON scenarios(post_id);
CREATE INDEX idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX idx_parsing_sessions_initiated_by ON parsing_sessions(initiated_by);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
