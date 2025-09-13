# 🚀 Настройка Supabase для ReAIboot

## ⚡ Быстрая настройка (5 минут)

### 1. Создание проекта Supabase
```bash
# Перейдите на https://supabase.com
# Нажмите "New Project"
# Заполните:
# - Name: ReAIboot
# - Database Password: придумайте надежный пароль
# - Region: Europe (Frankfurt) или другой близкий регион
```

### 2. Выполнение схемы базы данных
```sql
-- Откройте Supabase Dashboard → SQL Editor
-- Скопируйте и выполните содержимое файла supabase_schema.sql
-- Схема создаст все необходимые таблицы, индексы и политики безопасности
```

### 3. Настройка аутентификации
```bash
# В Dashboard → Authentication → Settings
# В разделе "Site URL" добавьте:
# - Site URL: http://localhost:3000 (для разработки)
# - Redirect URLs: http://localhost:3000/auth/callback

# В разделе "Auth Providers" включите:
# - Enable email confirmations: ON
# - Enable Google provider (опционально)
# - Enable GitHub provider (опционально)
```

### 4. Получение ключей API
```bash
# В Dashboard → Settings → API
# Скопируйте:
# - Project URL: https://xxxxx.supabase.co
# - anon/public key: eyJ...
# - service_role key: eyJ... (для админских операций)
```

### 5. Настройка переменных окружения

**Создайте файл `.env` в корне проекта:**
```env
# Backend переменные
TELEGRAM_API_ID=ваш_telegram_api_id
TELEGRAM_API_HASH=ваш_telegram_api_hash
OPENAI_API_KEY=ваш_openai_api_key
CLAUDE_API_KEY=ваш_claude_api_key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=ваш_anon_key
SUPABASE_SERVICE_ROLE_KEY=ваш_service_role_key
```

**Создайте файл `reai-boot-ui/.env.local`:**
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=ваш_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 6. Запуск проекта
```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск всего проекта
./start_project.sh

# Или по отдельности:
python scripts/run_api.py &  # Backend
cd reai-boot-ui && npm run dev  # Frontend
```

## 🔐 Безопасность

### Row Level Security (RLS)
- Автоматически настроена на всех таблицах
- Пользователи видят только свои данные
- Админы имеют расширенные права

### Переменные окружения
- Никогда не коммитьте `.env` файлы
- Используйте разные ключи для разработки и продакшена
- Регулярно обновляйте API ключи

## 🐛 Возможные проблемы

### Ошибка подключения
```bash
# Проверьте ключи в .env файлах
# Убедитесь что Supabase проект активен
# Проверьте интернет соединение
```

### Ошибка аутентификации
```bash
# Проверьте настройки в Authentication → Settings
# Убедитесь что Site URL правильный
# Проверьте что redirect URLs корректны
```

### Ошибка выполнения SQL схемы
```bash
# Выполняйте команды по одной в SQL Editor
# Убедитесь что у вас есть права на создание таблиц
# Проверьте что все предыдущие команды выполнены успешно
```

## 📊 Проверка работоспособности

### Тест подключения к БД
```bash
# В Supabase Dashboard → Table Editor
# Проверьте что все таблицы созданы:
# - profiles, channels, posts, post_analysis, scenarios
# - token_usage, system_logs, parsing_sessions
```

### Тест API
```bash
# Проверьте health check
curl http://localhost:8001/health

# Проверьте LLM статус
curl http://localhost:8001/api/stats/llm
```

## 🚀 Следующие шаги

1. **Запустите парсинг**: Откройте http://localhost:3000 → Парсинг
2. **Протестируйте анализ**: Выберите посты для LLM обработки
3. **Создайте сценарии**: Просмотрите сгенерированные Reels сценарии
4. **Настройте каналы**: Добавьте свои Telegram каналы для мониторинга

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в терминале
2. Посмотрите Supabase Dashboard → Logs
3. Проверьте настройки в `.env` файлах

**Схема обновлена и готова к использованию! 🎉**
