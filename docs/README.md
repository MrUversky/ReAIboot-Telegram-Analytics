# 📚 ReAIboot Documentation

Добро пожаловать в централизованную документацию проекта **ReAIboot** - системы для анализа популярных постов в Telegram и генерации сценариев контента для проекта "ПерепрошИИвка".

## 🗂️ Структура документации

- **[📊 Бизнес-информация](business/)** - аудитория, конкуренты, стратегия
  - [🎯 Целевая аудитория и ICP](business/audience.md)
  - [🏆 Конкурентный анализ](business/competitors.md)
  - [Overview](business/overview.md)
- **[🏗️ Техническая документация](technical/)** - архитектура, API, деплой
  - [📡 API документация](technical/api/overview.md)
  - [🚀 Настройка Supabase для ReAIboot](technical/database/schema.md)
  - [🚀 Руководство по развертыванию ReAIboot](technical/deployment/guide.md)
- **[👥 Руководства пользователей](user-guides/)** - гайды по использованию
  - [👑 Руководство администратора ReAIboot](user-guides/admin-guide.md)
  - [Getting Started](user-guides/getting-started.md)
- **[💻 Для разработчиков](development/)** - настройка, разработка, тестирование

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

## 🤖 Автоматическое обновление документации

Документация поддерживает автоматическое обновление через LLM-агент. При внесении изменений в код:

1. **Cursor Rules** автоматически обнаруживают изменения
2. **LLM-агент** анализирует код и генерирует обновления
3. **Документация** обновляется с актуальной информацией

Подробнее: [Настройка LLM-агента](development/contributing.md#llm-agent)

## 📝 Как внести вклад в документацию

1. **Для технических изменений**: Обновите соответствующий раздел в `technical/`
2. **Для бизнес-информации**: Используйте раздел `business/`
3. **Для пользовательских гайдов**: Раздел `user-guides/`
4. **LLM-агент автоматически** предложит обновления при изменениях кода

### Шаблоны документов
- [Шаблон API эндпоинта](templates/api-endpoint.md)
- [Шаблон руководства](templates/user-guide.md)
- [Шаблон бизнес-документа](templates/business-doc.md)

## 📊 Статус документации

| Раздел | Статус | Актуальность |
|--------|--------|--------------|
| Бизнес-информация | 🟡 В разработке | Требует обновления |
| API документация | 🔴 Отсутствует | Нужно создать |
| Архитектура | 🟡 Частично | Требует дополнения |
| Руководства пользователей | 🟡 Фрагментарно | Нужно систематизировать |
| Документация разработчиков | 🔴 Отсутствует | Нужно создать |

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/MrUversky/ReAIboot-Telegram-Analytics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MrUversky/ReAIboot-Telegram-Analytics/discussions)
- **Telegram**: [@reai_boot_support](https://t.me/reai_boot_support)

---

*Последнее обновление: Декабрь 2024*
