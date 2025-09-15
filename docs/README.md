# 📚 ReAIboot Documentation

Добро пожаловать в централизованную документацию проекта **ReAIboot** - системы для анализа популярных постов в Telegram и генерации сценариев контента для проекта "ПерепрошИИвка".

## 🗂️ Структура документации

- **[📊 Бизнес-информация](business/)** - аудитория, конкуренты, стратегия
  - [🎯 Целевая аудитория и ICP](business/audience.md)
  - [🏆 Конкурентный анализ](business/competitors.md)
  - [Content Strategy](business/content-strategy.md)
  - [Future Ideas](business/future-ideas.md)
  - [Overview](business/overview.md)
  - [📋 ReAIboot - План развития проекта](business/project-plan.md)
  - [Youtube Strategy](business/youtube-strategy.md)
- **[🏗️ Техническая документация](technical/)** - архитектура, API, деплой
  - [Архитектура системы](technical/architecture/components.md)
  - [Интеграция с LLM](technical/architecture/llm-integration.md)
  - [🗂️ Структура проекта ReAIboot](technical/architecture/project-structure.md)
  - [🦠 Система определения "залетевших" постов (Viral Detection System)](technical/architecture/viral-detection.md)
  - [📡 API документация](technical/api/overview.md)
  - [🚀 Настройка Supabase для ReAIboot](technical/database/schema.md)
  - [🚀 Настройка Supabase для ReAIboot](technical/database/supabase-setup.md)
  - [🚀 Руководство по развертыванию ReAIboot](technical/deployment/guide.md)
- **[👥 Руководства пользователей](user-guides/)** - гайды по использованию
  - [👑 Руководство администратора ReAIboot](user-guides/admin-guide.md)
  - [Getting Started](user-guides/getting-started.md)
- **[💻 Для разработчиков](development/)** - настройка, разработка, тестирование
  - [🤝 Вклад в разработку ReAIboot](development/contributing.md)

## 🔍 Быстрый поиск

### Популярные темы
- [Как начать работу](user-guides/getting-started.md)
- [API для работы с постами](technical/api/endpoints/posts.md)
- [Управление промптами](user-guides/admin-guide.md#prompts)
- [Архитектура системы](technical/architecture/overview.md)

### Поиск по API
| Раздел | Эндпоинт | Описание |
|--------|----------|----------|
| Здоровье | `GET /health` | Проверка работоспособности |
| Посты | `GET /api/posts` | Получение списка постов |
| LLM | `POST /api/llm/process` | Обработка постов через LLM |
| Песочница | `POST /api/sandbox/test-pipeline` | Тестирование pipeline |
| Админ | `GET /admin/current-prompt/{name}` | Управление промптами |

## 🤖 Автоматическая система документации

Проект ReAIboot оснащен продвинутой системой автоматического обновления документации с AI-генерацией описаний компонентов.

### Как работает система:

#### 🎯 **Интеллектуальный анализ кода**
- Автоматическое обнаружение новых классов, функций, API эндпоинтов
- Анализ зависимостей и взаимодействий между компонентами
- Отслеживание изменений в бизнес-логике и LLM интеграциях

#### 🧠 **AI-генерация описаний**
- **Модель:** GPT-3.5-turbo (оптимизирована для стоимости)
- **Контекст:** Умное извлечение релевантной информации вместо сырых данных
- **Экономия:** 85-90% от первоначальной стоимости токенов
- **Качество:** Структурированные описания на русском языке

#### ⚡ **Оптимизация расходов**
- AI вызывается только для новых компонентов
- Умное кеширование уже документированных элементов
- Ограничение контекста до 1500 токенов вместо 2000+
- `--force-ai` флаг для принудительной перегенерации

### Запуск системы:

```bash
# Автоматическое обновление (только новые компоненты)
python3 .cursorrules/update_docs.py --all

# Принудительная AI перегенерация (дорого!)
python3 .cursorrules/update_docs.py --force-ai --all

# Анализ конкретных файлов
python3 .cursorrules/update_docs.py --files src/app/orchestrator.py

# Предварительный просмотр изменений
python3 .cursorrules/update_docs.py --dry-run --files src/app/orchestrator.py
```

### Автоматическая интеграция:
- **Pre-commit hooks** - автоматический запуск перед каждым коммитом
- **GitHub Actions** - CI/CD обновление документации
- **Cursor Rules** - интеграция с IDE

Подробнее: [Руководство для разработчиков](development/contributing.md) | [Для LLM](LLM_README.md#система-автоматической-документации)

## 📝 Как внести вклад в документацию

Подробное руководство: **[Вклад в разработку](development/contributing.md)**

### Кратко:
1. **Техническая документация** - обновляется автоматически AI системой
2. **Бизнес-информация** - редактируйте в разделе `business/`
3. **Пользовательские гайды** - раздел `user-guides/`
4. **При разработке** - система автоматически документирует новые компоненты

### Шаблоны документов
- [Шаблон API эндпоинта](templates/api-endpoint.md)
- [Шаблон бизнес-документа](templates/business-doc.md)
- [Руководство для разработчиков](development/contributing.md)

## 📊 Статус документации

| Раздел | Статус | Актуальность |
|--------|--------|--------------|
| **Автоматическая система документации** | 🟢 Полностью готова | AI-генерация + оптимизация |
| API документация | 🟢 Автоматическая | 12+ эндпоинтов документированы |
| Архитектурная документация | 🟢 Автоматическая | 20+ компонентов с AI описаниями |
| Бизнес-информация | 🟡 В разработке | Требует обновления |
| Руководства пользователей | 🟡 Фрагментарно | Нужно систематизировать |
| Мониторинг системы | 🟢 Автоматический | Метрики производительности |
| LLM интеграция | 🟢 Полная документация | Все процессоры описаны |

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/MrUversky/ReAIboot-Telegram-Analytics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MrUversky/ReAIboot-Telegram-Analytics/discussions)
- **Telegram**: [@reai_boot_support](https://t.me/reai_boot_support)

---

*Последнее обновление: Сентябрь 2025 - AI система документации полностью готова*
