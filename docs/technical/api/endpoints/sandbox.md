# 🧪 Песочница API

Эндпоинты для тестирования и отладки pipeline обработки постов.

## Обзор

Песочница (`/api/sandbox`) предоставляет:
- Тестирование полного pipeline обработки
- Пошаговое выполнение с отладкой
- Просмотр логов и промежуточных результатов
- Управление тестовыми данными

---

## Тестирование pipeline

Запуск полного цикла обработки поста с детальным логированием.

**Эндпоинт:** `POST /api/sandbox/test-pipeline`

**Аутентификация:** API Key

### Request Body

```json
{
  "post_data": {
    "id": "12345_@channel",
    "message_id": 12345,
    "channel_username": "@channel",
    "channel_title": "Название канала",
    "text": "Текст поста для обработки...",
    "views": 1000,
    "reactions": 50,
    "replies": 10,
    "forwards": 2,
    "date": "2024-12-01T10:00:00Z"
  },
  "options": {
    "debug_mode": true,
    "step_by_step": false,
    "skip_filter": false,
    "skip_analysis": false,
    "skip_rubric_selection": false,
    "model_overrides": {
      "filter": "gpt-4o-mini",
      "analysis": "claude-3-sonnet",
      "rubric_selector": "gpt-4o",
      "generator": "gpt-4o"
    }
  }
}
```

### Response

```json
{
  "success": true,
  "post_id": "12345_@channel",
  "session_id": "sandbox_12345_123456",
  "total_tokens": 1250,
  "total_time": 15.5,
  "stages": [
    {
      "step": 1,
      "name": "filter",
      "status": "completed",
      "success": true,
      "tokens_used": 245,
      "processing_time": 1.2,
      "data": {
        "score": 8,
        "suitable": true,
        "reason": "Обоснование фильтрации"
      }
    },
    {
      "step": 2,
      "name": "analysis",
      "status": "completed",
      "success": true,
      "tokens_used": 450,
      "processing_time": 3.8,
      "data": {
        "success_factors": ["Фактор 1", "Фактор 2"],
        "audience_insights": ["Инсайт 1"],
        "content_ideas": ["Идея 1", "Идея 2"]
      }
    }
  ],
  "final_result": {
    "filter": {...},
    "analysis": {...},
    "rubric_selection": {...},
    "scenarios": [...]
  },
  "debug_log": [
    {
      "session_id": "sandbox_12345_123456",
      "timestamp": 123456.789,
      "step_name": "pipeline_start",
      "step_type": "info",
      "data": {
        "message": "Начинаем обработку поста",
        "post_id": "12345_@channel"
      }
    },
    {
      "session_id": "sandbox_12345_123456",
      "timestamp": 123457.123,
      "step_name": "filter_prompts",
      "step_type": "prompts",
      "data": {
        "system_prompt": "Системный промпт...",
        "user_prompt": "Пользовательский промпт...",
        "model": "gpt-4o-mini"
      }
    }
  ]
}
```

---

## Получение списка постов песочницы

**Эндпоинт:** `GET /api/sandbox/posts`

**Аутентификация:** API Key

### Query Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `limit` | integer | Количество постов (по умолчанию 50) |
| `offset` | integer | Смещение (по умолчанию 0) |
| `status` | string | Фильтр по статусу: `processed`, `failed`, `pending` |
| `channel_username` | string | Фильтр по каналу |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "12345_@channel",
      "channel_username": "@channel",
      "text_preview": "Превью текста поста...",
      "status": "processed",
      "created_at": "2024-12-01T10:00:00Z",
      "processed_at": "2024-12-01T10:15:30Z",
      "total_tokens": 1250,
      "processing_time": 15.5,
      "success": true
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_next": true
  }
}
```

---

## Получение детальной информации о посте

**Эндпоинт:** `GET /api/sandbox/post/{post_id}`

**Аутентификация:** API Key

### Response

```json
{
  "success": true,
  "data": {
    "id": "12345_@channel",
    "post_data": {
      "text": "Полный текст поста...",
      "views": 1000,
      "reactions": 50
    },
    "processing_result": {
      "success": true,
      "stages": [...],
      "final_result": {...},
      "debug_log": [...]
    },
    "metadata": {
      "created_at": "2024-12-01T10:00:00Z",
      "processed_at": "2024-12-01T10:15:30Z",
      "session_id": "sandbox_12345_123456",
      "total_tokens": 1250,
      "processing_time": 15.5
    }
  }
}
```

---

## Пошаговое выполнение

### Запуск пошаговой обработки

**Эндпоинт:** `POST /api/sandbox/step-by-step/start`

```json
{
  "post_data": {...},
  "start_step": "filter"
}
```

### Выполнение следующего шага

**Эндпоинт:** `POST /api/sandbox/step-by-step/{session_id}/next`

### Получение состояния сессии

**Эндпоинт:** `GET /api/sandbox/step-by-step/{session_id}`

```json
{
  "success": true,
  "data": {
    "session_id": "step_by_step_123456",
    "current_step": "analysis",
    "completed_steps": ["filter"],
    "pending_steps": ["rubric_selection", "generation"],
    "current_data": {
      "filter_result": {...},
      "analysis_result": {...}
    },
    "available_actions": [
      {
        "action": "continue",
        "description": "Продолжить на следующий шаг"
      },
      {
        "action": "edit_data",
        "description": "Изменить данные перед следующим шагом"
      },
      {
        "action": "restart",
        "description": "Начать заново"
      }
    ]
  }
}
```

### Редактирование данных между шагами

**Эндпоинт:** `PUT /api/sandbox/step-by-step/{session_id}/data`

```json
{
  "step": "analysis",
  "data": {
    "custom_analysis": {
      "success_factors": ["Пользовательский фактор"],
      "audience_insights": ["Пользовательский инсайт"]
    }
  }
}
```

---

## Управление сессиями

### Получение списка активных сессий

**Эндпоинт:** `GET /api/sandbox/sessions`

```json
{
  "success": true,
  "data": [
    {
      "session_id": "sandbox_12345_123456",
      "post_id": "12345_@channel",
      "status": "active",
      "current_step": "generation",
      "created_at": "2024-12-01T10:00:00Z",
      "last_activity": "2024-12-01T10:15:30Z"
    }
  ]
}
```

### Удаление сессии

**Эндпоинт:** `DELETE /api/sandbox/sessions/{session_id}`

---

## Отладочные инструменты

### Получение логов сессии

**Эндпоинт:** `GET /api/sandbox/logs/{session_id}`

**Query Parameters:**
- `step_type` - Фильтр по типу: `info`, `prompts`, `llm_response`, `error`, `db_operation`, `warning`
- `limit` - Количество записей (по умолчанию 100)

### Поиск по логам

**Эндпоинт:** `GET /api/sandbox/logs/search`

**Query Parameters:**
- `query` - Поисковый запрос
- `step_type` - Тип шага
- `date_from` - Начальная дата
- `date_to` - Конечная дата

### Экспорт логов

**Эндпоинт:** `GET /api/sandbox/logs/{session_id}/export`

**Query Parameters:**
- `format` - Формат экспорта: `json`, `csv`, `txt`

---

## Тестовые данные

### Получение списка тестовых постов

**Эндпоинт:** `GET /api/sandbox/test-data/posts`

### Создание тестового поста

**Эндпоинт:** `POST /api/sandbox/test-data/posts`

```json
{
  "channel_username": "@test_channel",
  "text": "Тестовый пост для проверки pipeline",
  "views": 100,
  "reactions": 10,
  "replies": 2,
  "forwards": 1,
  "tags": ["test", "viral"]
}
```

### Импорт тестовых данных

**Эндпоинт:** `POST /api/sandbox/test-data/import`

```json
{
  "source": "file",
  "file_path": "/path/to/test_data.json"
}
```

---

## Метрики песочницы

**Эндпоинт:** `GET /api/sandbox/metrics`

### Response

```json
{
  "success": true,
  "data": {
    "total_sessions": 1250,
    "active_sessions": 15,
    "success_rate": 0.87,
    "avg_processing_time": 12.3,
    "popular_channels": [
      {"channel": "@dnevteh", "sessions": 234},
      {"channel": "@vc_ru", "sessions": 189}
    ],
    "error_distribution": {
      "filter_failed": 45,
      "analysis_timeout": 23,
      "generation_error": 12
    },
    "performance_trends": [
      {"date": "2024-12-01", "avg_time": 14.2, "success_rate": 0.85}
    ]
  }
}
```

---

## Лучшие практики использования песочницы

### 1. Тестирование новых промптов

```bash
# Тестируйте промпты перед продакшном
curl -X POST "https://api.reai-boot.dev/api/sandbox/test-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "post_data": {"text": "Тестовый пост"},
    "options": {"debug_mode": true}
  }'
```

### 2. Отладка проблем

```bash
# Используйте детальное логирование
curl -X GET "https://api.reai-boot.dev/api/sandbox/logs/sandbox_12345_123456?step_type=error"
```

### 3. Пошаговая разработка

```python
# Создайте сессию пошаговой обработки
session = await api.sandbox_start_step_by_step(post_data)

# Выполняйте шаги по одному
while session['current_step']:
    result = await api.sandbox_execute_step(session['session_id'])
    if result['success']:
        # Анализируйте промежуточные результаты
        print(f"Шаг {session['current_step']} завершен")
        session = await api.sandbox_get_session(session['session_id'])
    else:
        # Исправьте данные и продолжите
        await api.sandbox_edit_data(session['session_id'], fixed_data)
```

### 4. Мониторинг производительности

```python
# Отслеживайте метрики
metrics = await api.sandbox_get_metrics()

if metrics['avg_processing_time'] > 20:
    logger.warning("Замедление обработки в песочнице")

if metrics['success_rate'] < 0.8:
    logger.error("Высокий уровень ошибок")
```

---

## Безопасность песочницы

### Изоляция данных
- Тестовые данные не влияют на продакшн
- Отдельная база данных для песочницы
- Ограниченный доступ к реальным данным

### Ограничения использования
- Максимум 100 одновременных сессий
- Ограничение на размер входных данных
- Timeouts для предотвращения зависаний

### Аудит действий
- Все действия логируются
- История изменений сохраняется
- Возможность отката изменений

---

*Обновлено: Декабрь 2024 | Версия API: 1.0.0*
