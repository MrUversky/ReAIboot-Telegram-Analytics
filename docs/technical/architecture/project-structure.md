# 🗂️ Структура проекта ReAIboot

## Описание проекта

**ReAIboot** - система автоматизированного анализа популярных постов в Telegram и генерации сценариев для контента проекта "ПерепрошИИвка".

### Основные компоненты
- **Backend**: FastAPI (Python) + Supabase
- **Frontend**: Next.js (TypeScript) + Supabase Auth
- **База данных**: PostgreSQL (Supabase)
- **Документация**: Автоматизированная система генерации

---

## 📁 Структура директорий

```
/
├── 📁 src/                          # Python backend (FastAPI)
│   ├── api_main.py                 # Главный сервер FastAPI
│   ├── app/                        # Основная логика приложения
│   │   ├── supabase_client.py      # Клиент Supabase
│   │   ├── llm/                   # LLM архитектура
│   │   │   ├── orchestrator.py    # Основной оркестратор пайплайна
│   │   │   ├── generator_processor.py # Генерация сценариев
│   │   │   └── prompt_manager.py   # Управление промптами
│   │   ├── telegram_client.py      # Telegram API клиент
│   │   ├── settings.py             # Конфигурация приложения
│   │   └── main.py                 # CLI интерфейс
│   └── main.py                     # Точка входа
├── 📁 reai-boot-ui/               # Next.js frontend
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── page.tsx           # Главная страница
│   │   │   ├── posts/             # Страница постов
│   │   │   ├── scenarios/         # Страница сценариев
│   │   │   ├── auth/              # Аутентификация
│   │   │   ├── admin/             # Админ-панель
│   │   │   ├── api/               # Next.js API routes
│   │   │   └── layout.tsx         # Главный layout
│   │   ├── components/            # React компоненты
│   │   │   ├── admin/             # Компоненты админки
│   │   │   ├── ui/                # UI компоненты
│   │   │   └── PostCard.tsx       # Карточка поста
│   │   └── lib/                   # Утилиты
│   │       ├── api.ts             # API клиент
│   │       └── supabase.ts        # Supabase клиент
│   └── package.json               # Зависимости frontend
├── 📁 docs/                       # Документация
│   ├── README.md                  # Введение в документацию
│   ├── DASHBOARD.md               # Центральная панель
│   ├── LLM_README.md              # Руководство для LLM
│   ├── business/                  # Бизнес-документация
│   ├── technical/                 # Техническая документация
│   ├── user-guides/               # Руководства пользователя
│   ├── development/               # Документация разработки
│   ├── monitoring/                # Мониторинг и метрики
│   ├── metrics/                   # Метрики производительности
│   ├── templates/                 # Шаблоны документации
│   └── wiki-architecture/         # Архитектурные решения
├── 📁 configs/                    # Конфигурационные файлы
│   ├── content_plan.yaml          # План контента (рубрики)
│   ├── score.yaml                 # Весовые коэффициенты метрик
│   └── README.md                  # Описание конфигураций
├── 📁 migrations/                 # Миграции базы данных
│   ├── README.md                  # Руководство по миграциям
│   └── (SQL файлы миграций)       # Инкрементальные изменения
├── 📁 scripts/                    # Скрипты проекта
├── 📁 examples/                   # Примеры использования
├── 📁 temp/                       # Временные файлы
├── 📁 .cursorrules/               # Правила для Cursor IDE
├── 📁 .github/workflows/          # CI/CD пайплайны
├── 📁 .pre-commit-config.yaml     # Pre-commit hooks
├── 📄 supabase_schema.sql         # Актуальная схема БД
├── 📄 pyrightconfig.json          # Конфигурация Pyright
├── 📄 requirements.txt            # Python зависимости
└── 📄 README.md                   # Основной README проекта
```

---

## 🚀 Запуск проекта

### Предварительные требования
- Python 3.9+
- Node.js 18+
- Supabase аккаунт
- API ключи: Telegram, OpenAI, Claude

### Быстрый старт

1. **Установка зависимостей:**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd reai-boot-ui && npm install
```

2. **Настройка переменных окружения:**
```bash
# Создать .env файлы (см. docker_env_example.txt)
cp docker_env_example.txt .env
```

3. **Запуск базы данных:**
```bash
# Применить схему в Supabase
# Использовать supabase_schema.sql
```

4. **Запуск сервисов:**
```bash
# Backend
python src/main.py

# Frontend (в новом терминале)
cd reai-boot-ui && npm run dev
```

---

## 🏗️ Архитектурные решения

### Backend (FastAPI)
- **Модульная структура** с разделением ответственности
- **Асинхронная обработка** LLM запросов
- **Интеграция с Supabase** для хранения данных
- **Обработка ошибок** с graceful degradation

### Frontend (Next.js)
- **App Router** для современных React паттернов
- **TypeScript** для типобезопасности
- **Tailwind CSS** для стилизации
- **Supabase Auth** для аутентификации

### База данных (Supabase)
- **15 таблиц** с Row Level Security
- **Автоматическое логирование** использования токенов
- **Мониторинг производительности** LLM

### Документация
- **Автоматизированная генерация** описаний компонентов
- **Структурированное хранение** по разделам
- **Интеграция с Git** через pre-commit hooks

---

## 📊 Ключевые метрики

- **LLM пайплайн**: 3 этапа (фильтрация → анализ → генерация)
- **Стоимость**: < $1-2 в день на 100 постов
- **Производительность**: < 30 сек на пост
- **Точность**: > 80% фильтрации

---

## 🔧 Разработка

### Добавление новых функций
1. Создать задачу в `TODO_ISSUES.md`
2. Написать код с тестами
3. Обновить документацию
4. Создать миграцию БД (при необходимости)

### Работа с документацией
```bash
# Автоматическое обновление документации
python .cursorrules/update_docs.py

# Проверка качества документации
python .cursorrules/check_docs.py
```

---

## 🚀 Деплоймент

- **Backend**: Railway, Render, или VPS
- **Frontend**: Vercel или Netlify
- **База данных**: Supabase (managed PostgreSQL)
- **CI/CD**: GitHub Actions

---

## 📞 Поддержка

- **Документация**: `docs/README.md`
- **API документация**: `docs/technical/api/`
- **Руководства**: `docs/user-guides/`
- **Архитектура**: `docs/technical/architecture/`
