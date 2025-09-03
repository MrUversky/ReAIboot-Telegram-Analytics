-- ИСПРАВЛЕНИЕ СХЕМЫ ТАБЛИЦЫ POSTS
-- Добавление недостающей колонки channel_id

-- Проверяем и добавляем колонку channel_id
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'posts' AND column_name = 'channel_id') THEN
        ALTER TABLE public.posts ADD COLUMN channel_id BIGINT;
        RAISE NOTICE '✅ Добавлена колонка: posts.channel_id';
    ELSE
        RAISE NOTICE 'ℹ️ Колонка posts.channel_id уже существует';
    END IF;
END $$;

-- Проверяем и добавляем индекс для channel_id
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes
                   WHERE schemaname = 'public' AND tablename = 'posts' AND indexname = 'idx_posts_channel_id') THEN
        CREATE INDEX idx_posts_channel_id ON public.posts(channel_id);
        RAISE NOTICE '✅ Создан индекс: idx_posts_channel_id';
    ELSE
        RAISE NOTICE 'ℹ️ Индекс idx_posts_channel_id уже существует';
    END IF;
END $$;

-- Проверяем результат
SELECT
    'СТАТУС ОБНОВЛЕНИЯ:' as status,
    NOW() as updated_at;

-- Показываем структуру таблицы posts
SELECT
    column_name,
    data_type,
    is_nullable,
    CASE
        WHEN column_name IN ('viral_score', 'engagement_rate', 'zscore', 'median_multiplier', 'last_viral_calculation', 'channel_id')
        THEN '✅ VIRAL DETECTION'
        WHEN column_name IN ('id', 'message_id', 'channel_username', 'text_preview', 'views', 'reactions', 'replies', 'forwards')
        THEN '✅ ОСНОВНАЯ СИСТЕМА'
        ELSE 'ℹ️ СУЩЕСТВУЮЩАЯ'
    END as purpose
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'posts'
ORDER BY ordinal_position;
