# 🗂️ Структура проекта ReAIboot

## Очищенная структура проекта

```
/Users/Igor/ReAIboot TG/
├── 📁 src/                          # Python backend
│   ├── api_main.py                 # FastAPI сервер
│   ├── app/                        # Основная логика
│   │   ├── supabase_client.py      # Supabase интеграция
│   │   ├── llm/                   # LLM архитектура
│   │   └── telegram_client.py      # Telegram API
│   └── main.py                     # CLI интерфейс
├── 📁 reai-boot-ui/               # Next.js frontend
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── page.tsx           # Дашборд
│   │   │   ├── posts/             # Страница постов
│   │   │   ├── auth/              # Аутентификация
│   │   │   └── layout.tsx         # Главный layout
│   │   ├── components/            # UI компоненты
│   │   │   ├── PostCard.tsx       # Карточка поста
│   │   │   ├── Navigation.tsx     # Навигация
│   │   │   └── SupabaseProvider.tsx # Провайдер аутентификации
│   │   └── lib/                   # Утилиты
│   │       ├── api.ts             # API клиент
│   │       └── supabase.ts        # Supabase клиент
│   └── env-setup.txt              # Шаблон переменных окружения
├── 📁 out/                        # Результаты работы
│   ├── all_messages.csv           # Все посты
│   ├── top_overall.csv           # Топ посты
│   └── test_report.json          # Отчеты тестирования
├── 📁 tests/                      # Тесты
├── 📄 supabase_schema.sql         # Схема БД
├── 🚀 start_project.sh           # Скрипт запуска
├── 📚 SUPABASE_SETUP.md          # Настройка Supabase
└── 📋 PROJECT_STATUS.md          # Статус проекта
```

## 🚀 Запуск проекта

### 1. Настройка переменных окружения

**Backend (.env):**
```env
TELEGRAM_API_ID=ваш_id
TELEGRAM_API_HASH=ваш_hash
OPENAI_API_KEY=ваш_key
CLAUDE_API_KEY=ваш_key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=ваш_key
```

**Frontend:**
```bash
cd reai-boot-ui
cp env-setup.txt .env.local
# Отредактируйте .env.local с реальными значениями
```

### 2. Запуск
```bash
# Быстрый запуск всего проекта (рекомендуется)
./start_project.sh

# Или запуск по отдельности:
# Backend
source venv_py39/bin/activate
./venv_py39/bin/python run_api.py

# Frontend (в новом терминале)
cd reai-boot-ui
npm install
npm run dev

# Результат:
# 🌐 Frontend: http://localhost:3000
# 🔧 Backend: http://localhost:8000
# 📚 API Docs: http://localhost:8000/docs
```

## 📁 Описание папок

### `/src/` - Python Backend
- **api_main.py** - FastAPI REST API сервер
- **supabase_client.py** - Интеграция с Supabase БД
- **llm/** - Архитектура обработки текста ИИ
- **telegram_client.py** - Работа с Telegram API
- **fetch.py** - Загрузка и обработка постов

### `/reai-boot-ui/` - Next.js Frontend
- **src/app/** - Страницы приложения
  - `page.tsx` - Главный дашборд
  - `posts/page.tsx` - Просмотр и анализ постов
  - `auth/page.tsx` - Аутентификация
- **src/components/** - Переиспользуемые компоненты
- **src/lib/** - API клиенты и утилиты

### `/out/` - Результаты работы
- **all_messages.csv** - Все собранные посты
- **top_overall.csv** - Лучшие посты по рейтингу
- **scenarios.md** - Сгенерированные сценарии

### `/tests/` - Автоматизированные тесты
- Unit тесты компонентов
- API тесты
- Интеграционные тесты

## 🔧 Основные компоненты

### Backend (Python + FastAPI)
```python
# Основные модули
- Telegram парсер (telegram_client.py)
- LLM обработка (llm/orchestrator.py)
- Supabase интеграция (supabase_client.py)
- REST API (api_main.py)
```

### Frontend (Next.js + TypeScript)
```typescript
// Основные компоненты
- Дашборд с аналитикой
- Просмотр постов с фильтрами
- Управление сценариями
- Аутентификация Supabase
```

### База данных (Supabase)
```sql
-- Основные таблицы
- posts - собранные посты
- post_analysis - результаты LLM
- scenarios - сгенерированные сценарии
- token_usage - отслеживание затрат
```

## 🚀 Workflow проекта

1. **Парсинг** → Telegram каналы → Supabase
2. **Анализ** → LLM фильтр → анализ → генерация
3. **Хранение** → результаты в БД
4. **UI** → просмотр и управление через веб-интерфейс

## 📊 Мониторинг

- **System health** - статус API и БД
- **Token usage** - отслеживание затрат на LLM
- **Performance metrics** - время обработки
- **Error tracking** - логи ошибок

## 🎯 Следующие шаги

1. ✅ **Очистка структуры** - удалены дубликаты
2. 🔄 **Настройка Supabase** - схема готова
3. 🔄 **Тестирование интеграции** - проверка работы
4. 🔄 **Документация** - обновление инструкций

**Проект готов к развертыванию! 🚀**
