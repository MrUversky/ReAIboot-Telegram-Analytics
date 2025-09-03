# Исправление проблемы с RLS (Row Level Security)

## Проблема
Ошибка `new row violates row-level security policy for table "parsing_sessions"` возникает из-за того, что Supabase блокирует вставку записей в таблицу `parsing_sessions` через анонимный ключ.

## Решения (выберите одно)

### Решение 1: Отключить RLS (Быстрое, но менее безопасное)
```sql
-- Запустите в Supabase SQL Editor
ALTER TABLE parsing_sessions DISABLE ROW LEVEL SECURITY;
```

### Решение 2: Использовать Service Role Key (Рекомендуется)
1. Откройте Supabase Dashboard
2. Перейдите в Settings → API
3. Скопируйте **service_role** ключ (не anon key!)
4. Добавьте в `.env` файл:
```
SUPABASE_SERVICE_ROLE_KEY=ваш_service_role_ключ_здесь
```
5. Перезапустите приложение

### Решение 3: Создать правильную RLS политику
```sql
-- Запустите в Supabase SQL Editor
DROP POLICY IF EXISTS "parsing_sessions_insert_policy" ON parsing_sessions;

CREATE POLICY "parsing_sessions_insert_policy" ON parsing_sessions
FOR INSERT WITH CHECK (true);
```

## Проверка исправления
После применения любого решения запустите тест:
```bash
source venv/bin/activate && python test_supabase_connection.py
```

Если тест проходит успешно, парсинг заработает без ошибок 500.

