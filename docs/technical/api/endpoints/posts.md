# 📊 API Постов

Эндпоинты для работы с постами Telegram: получение, анализ, статистика и управление.

## Обзор

Раздел `/api/posts` предоставляет доступ к:
- Получению списков постов
- Детальной информации о постах
- Статистике вовлеченности
- Расчету виральных метрик

---

## Получение списка постов

Получить список постов с возможностью фильтрации и сортировки.

**Эндпоинт:** `GET /api/posts`

**Аутентификация:** API Key

### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `channel_username` | string | Нет | Фильтр по каналу (@username) |
| `limit` | integer | Нет | Количество постов (1-100, по умолчанию 50) |
| `offset` | integer | Нет | Смещение для пагинации (по умолчанию 0) |
| `sort_by` | string | Нет | Сортировка: `viral_score`, `date`, `views` |
| `sort_order` | string | Нет | Порядок: `asc`, `desc` (по умолчанию desc) |
| `date_from` | string | Нет | Начальная дата (ISO 8601) |
| `date_to` | string | Нет | Конечная дата (ISO 8601) |
| `min_viral_score` | float | Нет | Минимальный виральный скор (0-100) |

### Пример запроса

```bash
curl -X GET "https://api.reai-boot.dev/api/posts?channel_username=@dnevteh&limit=10&sort_by=viral_score" \
  -H "X-API-Key: your_api_key"
```

### Пример ответа

```json
{
  "success": true,
  "data": [
    {
      "id": "12345_@dnevteh",
      "message_id": 12345,
      "channel_username": "@dnevteh",
      "channel_title": "Дневник Технолога",
      "text": "Текст поста...",
      "text_preview": "Превью текста (первые 200 символов)...",
      "views": 15420,
      "reactions": 234,
      "replies": 45,
      "forwards": 12,
      "date": "2024-12-01T10:30:00Z",
      "viral_score": 85.7,
      "engagement_rate": 2.1,
      "link": "https://t.me/dnevteh/12345",
      "media_type": "text",
      "has_media": false,
      "created_at": "2024-12-01T10:35:00Z",
      "updated_at": "2024-12-01T10:35:00Z"
    }
  ],
  "pagination": {
    "total": 1250,
    "limit": 10,
    "offset": 0,
    "has_next": true
  },
  "filters_applied": {
    "channel_username": "@dnevteh",
    "sort_by": "viral_score",
    "sort_order": "desc"
  }
}
```

---

## Получение виральных постов

Получить посты с высоким уровнем вовлеченности.

**Эндпоинт:** `GET /api/posts/viral`

**Аутентификация:** API Key

### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `channel_username` | string | Нет | Фильтр по каналу |
| `min_score` | float | Нет | Минимальный виральный скор (по умолчанию 70) |
| `limit` | integer | Нет | Количество постов (1-50, по умолчанию 20) |
| `period_days` | integer | Нет | Период анализа в днях (1-30, по умолчанию 7) |

### Пример запроса

```bash
curl -X GET "https://api.reai-boot.dev/api/posts/viral?min_score=80&limit=5" \
  -H "X-API-Key: your_api_key"
```

---

## Получение детальной информации о посте

Получить полную информацию о конкретном посте включая анализ.

**Эндпоинт:** `GET /api/posts/{post_id}`

**Аутентификация:** API Key

### Path Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `post_id` | string | ID поста в формате `{message_id}_{channel_username}` |

### Query Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `include_analysis` | boolean | Включить результаты анализа (по умолчанию true) |
| `include_scenarios` | boolean | Включить сгенерированные сценарии (по умолчанию false) |

### Пример ответа

```json
{
  "success": true,
  "data": {
    "id": "12345_@dnevteh",
    "message_id": 12345,
    "channel_username": "@dnevteh",
    "channel_title": "Дневник Технолога",
    "text": "Полный текст поста...",
    "views": 15420,
    "reactions": 234,
    "replies": 45,
    "forwards": 12,
    "date": "2024-12-01T10:30:00Z",
    "viral_score": 85.7,
    "engagement_rate": 2.1,
    "link": "https://t.me/dnevteh/12345",
    "media_type": "photo",
    "has_media": true,
    "media_urls": ["https://cdn.example.com/photo.jpg"],
    "analysis": {
      "filter_score": 8,
      "suitable_for_content": true,
      "success_factors": ["Техническая тема", "Конкретные примеры"],
      "audience_insights": ["Интерес к AI инструментам"],
      "recommended_formats": ["talking_head", "demonstration"]
    },
    "scenarios": [
      {
        "id": "scenario_123",
        "title": "AI инструменты для разработчиков",
        "format": "talking_head",
        "duration": 60,
        "hook": "Текст хука",
        "content": "Основной контент",
        "call_to_action": "Призыв к действию"
      }
    ]
  }
}
```

---

## Расчет виральных метрик

Пересчитать метрики вовлеченности для поста.

**Эндпоинт:** `POST /api/posts/{post_id}/viral/update`

**Аутентификация:** API Key (админ)

### Пример запроса

```bash
curl -X POST "https://api.reai-boot.dev/api/posts/12345_@dnevteh/viral/update" \
  -H "X-API-Key: your_admin_key"
```

---

## Пакетный расчет метрик

Рассчитать виральные метрики для группы постов.

**Эндпоинт:** `POST /api/posts/calculate-viral-batch`

**Аутентификация:** API Key (админ)

### Request Body

```json
{
  "channel_username": "@dnevteh",
  "limit": 100,
  "force_recalculate": false
}
```

### Параметры

| Поле | Тип | Обязательный | Описание |
|------|-----|--------------|----------|
| `channel_username` | string | Нет | Канал для обработки |
| `limit` | integer | Нет | Количество постов (по умолчанию 100) |
| `force_recalculate` | boolean | Нет | Пересчитать даже если уже рассчитано |

---

## Статистика постов

Получить агрегированную статистику по постам.

**Эндпоинт:** `GET /api/posts/stats`

**Аутентификация:** API Key

### Query Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `channel_username` | string | Фильтр по каналу |
| `date_from` | string | Начальная дата |
| `date_to` | string | Конечная дата |
| `group_by` | string | Группировка: `day`, `week`, `month` |

### Пример ответа

```json
{
  "success": true,
  "data": {
    "total_posts": 1250,
    "avg_viral_score": 65.4,
    "avg_engagement_rate": 1.8,
    "top_channels": [
      {"channel": "@dnevteh", "posts_count": 234, "avg_score": 78.5},
      {"channel": "@vc_ru", "posts_count": 189, "avg_score": 72.1}
    ],
    "viral_distribution": {
      "0-20": 45,
      "21-40": 156,
      "41-60": 389,
      "61-80": 445,
      "81-100": 215
    },
    "time_series": [
      {"date": "2024-12-01", "posts": 45, "avg_score": 68.2},
      {"date": "2024-12-02", "posts": 52, "avg_score": 71.5}
    ]
  }
}
```

---

## Работа с базовыми линиями каналов

### Получение базовой линии канала

**Эндпоинт:** `GET /api/channels/{channel_username}/baseline`

```json
{
  "success": true,
  "data": {
    "channel_username": "@dnevteh",
    "avg_views": 15420,
    "avg_reactions": 234,
    "avg_replies": 45,
    "avg_forwards": 12,
    "avg_engagement_rate": 2.1,
    "sample_size": 1000,
    "last_updated": "2024-12-01T08:00:00Z",
    "confidence_level": 0.95
  }
}
```

### Перерасчет базовой линии

**Эндпоинт:** `POST /api/channels/{channel_username}/baseline/calculate`

**Аутентификация:** API Key (админ)

---

## Коды ошибок

| Код ошибки | HTTP Status | Описание |
|------------|-------------|----------|
| `POST_NOT_FOUND` | 404 | Пост не найден |
| `CHANNEL_NOT_FOUND` | 404 | Канал не найден |
| `INVALID_POST_ID` | 400 | Некорректный формат ID поста |
| `ANALYSIS_NOT_AVAILABLE` | 404 | Анализ поста недоступен |
| `RATE_LIMIT_EXCEEDED` | 429 | Превышен лимит запросов |
| `INSUFFICIENT_PERMISSIONS` | 403 | Недостаточно прав доступа |

---

*Обновлено: Декабрь 2024 | Версия API: 1.0.0*


## Get Sandbox Posts

**Эндпоинт:** `GET /api/sandbox/posts`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_sandbox_posts.

### Детали реализации
```
Function: get_sandbox_posts
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 15:36:28*


## Calculate Viral All Posts

**Эндпоинт:** `POST /api/posts/calculate-viral-all`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта calculate_viral_all_posts.

### Детали реализации
```
Function: calculate_viral_all_posts
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:04:54*


## Calculate Viral Metrics Batch

**Эндпоинт:** `POST /api/posts/calculate-viral-metrics-batch`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта calculate_viral_metrics_batch.

### Детали реализации
```
Function: calculate_viral_metrics_batch
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-16 00:13:50*
