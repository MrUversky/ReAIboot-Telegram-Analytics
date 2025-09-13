# 🤖 LLM API

Эндпоинты для работы с AI: анализ постов, генерация сценариев, управление промптами.

## Обзор

Раздел `/api/llm` предоставляет доступ к:
- Анализу постов через AI
- Генерации сценариев контента
- Управлению промптами
- Тестированию AI моделей

---

## Быстрый анализ поста

Простой анализ одного поста без сохранения результатов.

**Эндпоинт:** `POST /api/llm/analyze-quick`

**Аутентификация:** API Key

### Request Body

```json
{
  "text": "Текст поста для анализа",
  "channel_title": "Название канала (опционально)",
  "views": 1234,
  "reactions": 56,
  "replies": 12,
  "forwards": 3
}
```

### Response

```json
{
  "success": true,
  "data": {
    "score": 8,
    "reason": "Подробное обоснование оценки",
    "suitable": true,
    "tokens_used": 245,
    "processing_time": 1.2,
    "model": "gpt-4o-mini"
  }
}
```

---

## Полный анализ и генерация

Комплексная обработка поста: фильтрация → анализ → генерация сценариев.

**Эндпоинт:** `POST /api/llm/process`

**Аутентификация:** API Key

### Request Body

```json
{
  "posts": [
    {
      "id": "12345_@channel",
      "text": "Текст поста...",
      "channel_username": "@channel",
      "channel_title": "Название канала",
      "views": 1000,
      "reactions": 50,
      "replies": 10,
      "forwards": 2,
      "date": "2024-12-01T10:00:00Z"
    }
  ],
  "rubric": {
    "id": "instrument_dnya",
    "name": "Инструмент Дня"
  },
  "reel_format": {
    "id": "talking_head",
    "name": "Говорящая Голова"
  },
  "options": {
    "debug_mode": false,
    "step_by_step": false,
    "skip_filter": false,
    "skip_analysis": false
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "post_id": "12345_@channel",
        "filter": {
          "score": 8,
          "suitable": true,
          "reason": "Обоснование"
        },
        "analysis": {
          "success_factors": ["Фактор 1", "Фактор 2"],
          "audience_insights": ["Инсайт 1", "Инсайт 2"],
          "content_ideas": ["Идея 1", "Идея 2"]
        },
        "rubric_selection": {
          "selected_rubric": "instrument_dnya",
          "selected_format": "talking_head",
          "justification": "Обоснование выбора"
        },
        "scenarios": [
          {
            "id": "scenario_123",
            "title": "Название сценария",
            "format": "talking_head",
            "duration": 60,
            "hook": {
              "text": "Текст хука",
              "visual": "Описание визуала",
              "voiceover": "Текст озвучки"
            },
            "insight": {
              "text": "Ключевой инсайт",
              "visual": "Визуальное оформление",
              "voiceover": "Текст озвучки"
            },
            "steps": [
              {
                "step": 1,
                "title": "Название шага",
                "description": "Описание",
                "visual": "Визуальные элементы",
                "voiceover": "Текст озвучки",
                "duration": 5
              }
            ],
            "cta": {
              "text": "Призыв к действию",
              "visual": "Визуальное оформление",
              "voiceover": "Текст озвучки"
            },
            "hashtags": ["#тег1", "#тег2"],
            "music_suggestion": "Рекомендация музыки"
          }
        ]
      }
    ],
    "stats": {
      "total_tokens": 1250,
      "total_time": 15.5,
      "posts_processed": 1,
      "scenarios_generated": 2
    }
  }
}
```

---

## Генерация сценариев на основе анализа

Создание сценариев на основе готового анализа поста.

**Эндпоинт:** `POST /api/llm/generate-scenarios`

**Аутентификация:** API Key

### Request Body

```json
{
  "post_data": {
    "text": "Текст поста...",
    "analysis": {
      "success_factors": ["Фактор 1"],
      "audience_insights": ["Инсайт 1"]
    }
  },
  "rubric": {
    "id": "instrument_dnya",
    "name": "Инструмент Дня",
    "description": "Представление полезного инструмента"
  },
  "format": {
    "id": "talking_head",
    "name": "Говорящая Голова",
    "duration_seconds": 60,
    "description": "Классический формат с говорящим лицом"
  },
  "combination": {
    "justification": "Обоснование выбора комбинации",
    "content_idea": "Идея контента для этой комбинации"
  }
}
```

---

## Расширенная обработка

Продвинутая обработка с дополнительными опциями.

**Эндпоинт:** `POST /api/llm/process-enhanced`

**Аутентификация:** API Key

### Особенности
- Поддержка множественных рубрик и форматов
- Генерация нескольких сценариев
- Детальное логирование процесса
- Асинхронная обработка для больших объемов

---

## Управление промптами

### Получение списка промптов

**Эндпоинт:** `GET /api/prompts`

```json
{
  "success": true,
  "data": [
    {
      "name": "filter_posts_system",
      "title": "Фильтрация постов",
      "category": "analysis",
      "model": "gpt-4o-mini",
      "is_active": true,
      "updated_at": "2024-12-01T10:00:00Z"
    }
  ]
}
```

### Получение конкретного промпта

**Эндпоинт:** `GET /api/prompts/{template_name}`

### Обновление промпта

**Эндпоинт:** `PUT /api/prompts/{template_name}`

**Аутентификация:** API Key (админ)

```json
{
  "system_prompt": "Новый системный промпт",
  "user_prompt": "Новый пользовательский промпт",
  "model_settings": {
    "model": "gpt-4o",
    "temperature": 0.8,
    "max_tokens": 2000
  }
}
```

### Тестирование промпта

**Эндпоинт:** `POST /api/prompts/test/{template_name}`

```json
{
  "variables": {
    "post_text": "Текст для тестирования",
    "channel_title": "Название канала"
  }
}
```

---

## Управление промптами в базе данных

### Получение всех промптов из БД

**Эндпоинт:** `GET /api/prompts/db`

### Получение промпта по ID

**Эндпоинт:** `GET /api/prompts/db/{prompt_id}`

### Создание нового промпта

**Эндпоинт:** `POST /api/prompts`

### Обновление промпта

**Эндпоинт:** `PUT /api/prompts/db/{prompt_id}`

### Удаление промпта

**Эндпоинт:** `DELETE /api/prompts/db/{prompt_id}`

---

## Тестирование шаблонов промптов

**Эндпоинт:** `POST /api/llm/test/{template_name}`

**Аутентификация:** API Key (админ)

### Request Body

```json
{
  "variables": {
    "post_text": "Текст поста для тестирования",
    "analysis": "Результаты анализа",
    "rubric_name": "Название рубрики",
    "format_name": "Название формата"
  },
  "model_override": "gpt-4o"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "template_name": "generate_scenario_system",
    "input_variables": {...},
    "output": "Сгенерированный текст...",
    "tokens_used": 450,
    "processing_time": 2.1,
    "model_used": "gpt-4o"
  }
}
```

---

## Проектный контекст

### Получение контекста проекта

**Эндпоинт:** `GET /api/context/project`

### Обновление контекста проекта

**Эндпоинт:** `PUT /api/context/project`

**Аутентификация:** API Key (админ)

---

## Статистика использования LLM

**Эндпоинт:** `GET /api/stats/llm`

**Аутентификация:** API Key (админ)

### Response

```json
{
  "success": true,
  "data": {
    "total_requests": 1250,
    "total_tokens": 45000,
    "avg_response_time": 3.2,
    "error_rate": 0.05,
    "model_usage": {
      "gpt-4o": 650,
      "gpt-4o-mini": 450,
      "claude-3-sonnet": 150
    },
    "daily_stats": [
      {
        "date": "2024-12-01",
        "requests": 45,
        "tokens": 1200,
        "errors": 1
      }
    ]
  }
}
```

---

## Использование токенов

**Эндпоинт:** `GET /api/stats/tokens`

**Аутентификация:** API Key (админ)

### Query Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | string | Фильтр по пользователю |
| `days` | integer | Период в днях (по умолчанию 30) |

---

## Коды ошибок

| Код ошибки | HTTP Status | Описание |
|------------|-------------|----------|
| `INVALID_PROMPT_TEMPLATE` | 400 | Некорректный шаблон промпта |
| `MODEL_NOT_AVAILABLE` | 503 | Модель временно недоступна |
| `QUOTA_EXCEEDED` | 429 | Превышена квота использования |
| `CONTENT_FILTERED` | 400 | Контент отфильтрован модерацией |
| `PROMPT_TOO_LONG` | 400 | Промпт превышает лимит токенов |
| `INVALID_VARIABLES` | 400 | Некорректные переменные для шаблона |

---

## Rate Limiting для LLM

| Операция | Лимит | Период |
|----------|--------|--------|
| Анализ поста | 100 | час |
| Генерация сценария | 50 | час |
| Тестирование промпта | 20 | час |
| Управление промптами | 200 | час |

---

## Лучшие практики

### 1. Оптимизация промптов
```python
# Используйте переменные для динамического контента
prompt_vars = {
    "post_text": post.text[:2000],  # Ограничьте длину
    "analysis": json.dumps(analysis_data),
    "rubric_name": rubric.get('name', ''),
    "format_name": format.get('name', '')
}
```

### 2. Обработка ошибок
```python
try:
    result = await api.llm_process(post_data)
except Exception as e:
    if "quota_exceeded" in str(e):
        # Обработка превышения квоты
        await asyncio.sleep(60)  # Ожидание
        result = await api.llm_process(post_data)
    elif "model_unavailable" in str(e):
        # Fallback на другую модель
        result = await api.llm_process(post_data, model="gpt-4o-mini")
```

### 3. Мониторинг использования
```python
# Проверяйте статистику регулярно
stats = await api.get_llm_stats()
if stats['error_rate'] > 0.1:
    logger.warning("Высокий уровень ошибок LLM")

if stats['avg_response_time'] > 10:
    logger.warning("Замедление ответов LLM")
```

---

*Обновлено: Декабрь 2024 | Версия API: 1.0.0*
