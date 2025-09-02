# ReAIboot UI - Next.js Frontend

Полнофункциональный веб-интерфейс для системы анализа Telegram постов и генерации сценариев Reels.

## 🚀 Функциональность

### 📊 Дашборд
- **Статистика системы** - метрики постов, каналов, анализов
- **Мониторинг LLM** - статус процессоров, время обработки
- **Аналитика токенов** - затраты, использование моделей
- **Быстрые действия** - навигация к основным разделам

### 📝 Управление постами
- **Просмотр всех постов** - с фильтрацией и поиском
- **Топ постов** - лучшие посты по рейтингу вовлеченности
- **Анализ постов** - запуск LLM анализа для генерации сценариев
- **Статистика каналов** - просмотры, реакции, репосты

### 🎬 Сценарии Reels
- **Генерация сценариев** - на основе анализа успешных постов
- **Управление статусом** - draft → approved → published
- **Детальный просмотр** - hook, insight, content, call-to-action
- **Экспорт и редактирование** - подготовка к публикации

### ⚙️ Админ-панель
- **Мониторинг системы** - логи, ошибки, производительность
- **Управление каналами** - добавление, настройка частоты парсинга
- **Статистика токенов** - детальный анализ затрат
- **Настройки промптов** - редактирование LLM инструкций

### 🔐 Аутентификация
- **Supabase Auth** - безопасная аутентификация
- **Ролевая модель** - admin, user, viewer
- **Социальный вход** - Google, GitHub
- **Защита маршрутов** - проверка доступа

## 🛠️ Технологии

- **Next.js 14** - React фреймворк с App Router
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - утилитарный CSS фреймворк
- **Supabase** - Backend-as-a-Service (БД + Auth)
- **Lucide React** - иконки
- **Custom UI Components** - переиспользуемые компоненты

## 📋 Предварительные требования

1. **Node.js** >= 18.0.0
2. **npm** или **yarn**
3. **Supabase проект** с настроенной базой данных
4. **API сервер** ReAIboot (localhost:8001)

## 🚀 Установка и запуск

### 1. Клонирование и установка зависимостей

```bash
# Клонировать репозиторий
git clone <repository-url>
cd reai-boot-ui

# Установить зависимости
npm install
```

### 2. Настройка переменных окружения

```bash
# Скопировать пример файла
cp env-example.txt .env.local

# Редактировать переменные
nano .env.local
```

**Обязательные переменные:**
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 3. Настройка Supabase

1. **Создать проект** на [supabase.com](https://supabase.com)
2. **Выполнить SQL схему** из файла `../supabase_schema.sql`
3. **Настроить аутентификацию** в Supabase Dashboard
4. **Добавить ключи** в `.env.local`

### 4. Запуск приложения

```bash
# Development режим
npm run dev

# Production сборка
npm run build
npm start

# Открыть в браузере: http://localhost:3000
```

## 📁 Структура проекта

```
reai-boot-ui/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── auth/              # Страницы аутентификации
│   │   ├── posts/             # Страница постов
│   │   ├── scenarios/         # Страница сценариев
│   │   ├── admin/             # Админ панель
│   │   ├── layout.tsx         # Главный layout
│   │   └── page.tsx           # Главная страница (дашборд)
│   ├── components/            # Переиспользуемые компоненты
│   │   ├── ui/               # UI компоненты (Card, Button, etc.)
│   │   ├── PostCard.tsx      # Карточка поста
│   │   ├── ScenarioCard.tsx  # Карточка сценария
│   │   ├── Navigation.tsx    # Навигационная панель
│   │   └── SupabaseProvider.tsx # Провайдер аутентификации
│   └── lib/                  # Утилиты и конфигурации
│       ├── supabase.ts       # Supabase клиент
│       └── api.ts            # API клиент для backend
├── public/                   # Статические файлы
├── .env.local               # Переменные окружения
└── package.json
```

## 🔧 Настройка

### Добавление новых каналов

```typescript
// В Supabase Dashboard или через API
const { data, error } = await supabase
  .from('channels')
  .insert([
    {
      username: 'new_channel',
      title: 'Название канала',
      category: 'Категория',
      is_active: true
    }
  ])
```

### Настройка промптов

```typescript
// Через админ панель или API
const { data, error } = await supabase
  .from('prompts')
  .update({
    system_prompt: 'Новый системный промпт...',
    user_prompt: 'Новый пользовательский промпт...'
  })
  .eq('name', 'filter_prompt')
```

## 🚀 Развертывание

### Vercel (рекомендуется)

```bash
# Установить Vercel CLI
npm i -g vercel

# Развернуть
vercel --prod

# Настроить переменные окружения в Vercel Dashboard
```

### Другие платформы

- **Netlify**: Поддерживает Next.js
- **Railway**: Полный стек с базой данных
- **Docker**: Для контейнеризации

## 📊 Мониторинг и отладка

### Логи приложения
```bash
# Development логи
npm run dev

# Production логи через Vercel
vercel logs
```

### Проверка API
```bash
# Health check
curl http://localhost:8001/health

# Тест API
curl http://localhost:8001/api/stats/llm
```

## 🤝 Разработка

### Добавление новых функций

1. **Создать компонент** в `src/components/`
2. **Добавить страницу** в `src/app/`
3. **Обновить API** в `src/lib/api.ts`
4. **Добавить типы** в соответствующие файлы

### Стиль кода

- **TypeScript** для всех новых файлов
- **Tailwind CSS** для стилизации
- **Компонентный подход** для переиспользования
- **Responsive design** для мобильных устройств

## 📞 Поддержка

### Документация
- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Полезные ссылки
- [ReAIboot API](http://localhost:8001/docs) - документация API
- [Supabase Dashboard](https://supabase.com/dashboard) - управление БД
- [Vercel Dashboard](https://vercel.com/dashboard) - развертывание

## 📝 Лицензия

MIT License - см. файл LICENSE для подробностей.