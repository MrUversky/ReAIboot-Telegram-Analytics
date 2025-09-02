# 👑 Руководство администратора ReAIboot

## Управление правами пользователей

### 🎯 Роли пользователей

| Роль | Права доступа | Возможности |
|------|---------------|-------------|
| `viewer` | Только просмотр | Демо режим, просмотр документации |
| `user` | Полный доступ | Парсинг, анализ, генерация сценариев |
| `admin` | Админ права | Все возможности + управление пользователями |

### 🔧 Назначение прав через Supabase

#### 1. Переход в Supabase Dashboard
```
https://supabase.com/dashboard/project/oxsvtjtgtdaqoslcxdna
```

#### 2. Открытие SQL Editor
- Перейдите в раздел **SQL Editor**
- Выполните запросы для управления правами

#### 3. Просмотр всех пользователей
```sql
-- Посмотреть всех пользователей и их роли
SELECT
    p.id,
    p.email,
    p.full_name,
    p.role,
    p.is_active,
    p.created_at,
    p.last_login
FROM public.profiles p
ORDER BY p.created_at DESC;
```

#### 4. Изменение роли пользователя
```sql
-- Назначить пользователю полные права (user)
UPDATE public.profiles
SET role = 'user'
WHERE email = 'user@example.com';

-- Назначить админ права
UPDATE public.profiles
SET role = 'admin'
WHERE email = 'admin@example.com';

-- Вернуть в демо режим
UPDATE public.profiles
SET role = 'viewer'
WHERE email = 'user@example.com';
```

#### 5. Блокировка пользователя
```sql
-- Заблокировать пользователя
UPDATE public.profiles
SET is_active = false
WHERE email = 'user@example.com';

-- Разблокировать пользователя
UPDATE public.profiles
SET is_active = true
WHERE email = 'user@example.com';
```

### 📊 Мониторинг пользователей

#### Активные пользователи
```sql
SELECT
    role,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE last_login > NOW() - INTERVAL '7 days') as active_last_week
FROM public.profiles
WHERE is_active = true
GROUP BY role;
```

#### Статистика использования по пользователям
```sql
SELECT
    p.email,
    p.role,
    COUNT(tu.*) as total_requests,
    SUM(tu.tokens_used) as total_tokens,
    SUM(tu.cost_usd) as total_cost
FROM public.profiles p
LEFT JOIN public.token_usage tu ON p.id = tu.user_id
WHERE p.is_active = true
GROUP BY p.id, p.email, p.role
ORDER BY total_cost DESC;
```

### 🔒 Управление безопасностью

#### Просмотр неудачных попыток входа
```sql
-- В Supabase Dashboard → Authentication → Logs
-- Или через API logs
```

#### Очистка старых данных
```sql
-- Удалить неактивных пользователей старше 30 дней
DELETE FROM public.profiles
WHERE is_active = false
AND last_login < NOW() - INTERVAL '30 days';

-- Очистить старые логи токенов (старше 90 дней)
DELETE FROM public.token_usage
WHERE created_at < NOW() - INTERVAL '90 days';
```

### 🚀 Управление системой

#### Перезапуск парсинга
```sql
-- Остановить все активные сессии парсинга
UPDATE public.parsing_sessions
SET status = 'completed',
    completed_at = NOW()
WHERE status = 'running';

-- Проверить статус каналов
SELECT username, last_parsed, parse_frequency_hours
FROM public.channels
WHERE is_active = true
ORDER BY last_parsed DESC NULLS FIRST;
```

#### Управление каналами
```sql
-- Добавить новый канал для мониторинга
INSERT INTO public.channels (username, title, category, is_active)
VALUES ('@new_channel', 'Название канала', 'Категория', true);

-- Изменить частоту парсинга
UPDATE public.channels
SET parse_frequency_hours = 6
WHERE username = '@important_channel';

-- Отключить канал
UPDATE public.channels
SET is_active = false
WHERE username = '@old_channel';
```

### 📈 Аналитика системы

#### Общая статистика
```sql
-- Количество постов по дням
SELECT
    DATE(created_at) as date,
    COUNT(*) as posts_count
FROM public.posts
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Использование токенов по моделям
SELECT
    model,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost,
    COUNT(*) as requests_count
FROM public.token_usage
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY model
ORDER BY total_cost DESC;
```

#### Производительность LLM
```sql
SELECT
    analysis_type,
    COUNT(*) as total_analyses,
    AVG(processing_time_seconds) as avg_time,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost,
    COUNT(*) FILTER (WHERE status = 'completed')::float / COUNT(*) * 100 as success_rate
FROM public.post_analysis
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY analysis_type;
```

### 🔧 Техническое обслуживание

#### Резервное копирование
```bash
# Создать резервную копию базы данных
pg_dump "postgresql://postgres:[password]@db.oxsvtjtgtdaqoslcxdna.supabase.co:5432/postgres" > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Мониторинг дискового пространства
```sql
-- Размер таблиц
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 📞 Поддержка пользователей

#### Шаблон ответа для новых пользователей
```
Здравствуйте!

Ваш аккаунт создан в демо-режиме системы ReAIboot.
Для получения полных прав доступа обратитесь к администратору:

📧 Email: admin@reaiboot.com
💬 Telegram: @admin_username

После подтверждения прав вы сможете:
✅ Запускать парсинг Telegram каналов
✅ Анализировать посты с помощью ИИ
✅ Генерировать сценарии для Reels
✅ Просматривать статистику использования

Спасибо за интерес к нашей системе!
```

### 🚨 Аварийные ситуации

#### При проблемах с аутентификацией
```sql
-- Проверить настройки в Supabase Dashboard
-- Перепроверить переменные окружения
-- Очистить кэш браузера
```

#### При перегрузке системы
```sql
-- Ограничить количество одновременных запросов
-- Временно отключить неважные каналы
-- Мониторить использование токенов
```

---

## 📋 Быстрые команды

### Управление пользователями
```sql
-- Дать права пользователю
UPDATE public.profiles SET role = 'user' WHERE email = 'user@example.com';

-- Сделать админом
UPDATE public.profiles SET role = 'admin' WHERE email = 'user@example.com';

-- Заблокировать
UPDATE public.profiles SET is_active = false WHERE email = 'user@example.com';
```

### Мониторинг
```sql
-- Активные пользователи
SELECT email, role FROM public.profiles WHERE is_active = true;

-- Использование токенов сегодня
SELECT SUM(tokens_used), SUM(cost_usd) FROM public.token_usage WHERE DATE(created_at) = CURRENT_DATE;
```

---

*Обновлено: $(date)*
