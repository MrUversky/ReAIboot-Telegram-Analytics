# General API - Общие эндпоинты

## Обзор

Общие API эндпоинты для статистики, здоровья системы и вспомогательных функций.

### Назначение
Мониторинг системы, получение общей статистики, вспомогательные функции.

### Аутентификация
Все эндпоинты требуют валидной аутентификации через API ключи или Bearer токены.

### Формат данных
- **Request/Response**: JSON
- **Encoding**: UTF-8
- **Errors**: Стандартный формат ошибок API

---

## Эндпоинты


## Get Formats

**Эндпоинт:** `GET /api/formats`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_formats.

### Детали реализации
```
Function: get_formats
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 15:36:28*


## Get Rubrics

**Эндпоинт:** `GET /api/rubrics`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_rubrics.

### Детали реализации
```
Function: get_rubrics
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:04:54*


## Delete Channel

**Эндпоинт:** `DELETE /api/channels/{channel_id}`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта delete_channel.

### Детали реализации
```
Function: delete_channel
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:07:52*


## Update Channel Settings

**Эндпоинт:** `PUT /api/channels/{channel_id}`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта update_channel_settings.

### Детали реализации
```
Function: update_channel_settings
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:10:20*


## Get Parsing Session Status

**Эндпоинт:** `GET /api/parsing/session/{session_id}`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_parsing_session_status.

### Детали реализации
```
Function: get_parsing_session_status
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:17:18*


## Parse Multiple Channels

**Эндпоинт:** `POST /api/parsing/bulk`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта parse_multiple_channels.

### Детали реализации
```
Function: parse_multiple_channels
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 16:21:20*


## Parse Single Channel

**Эндпоинт:** `POST /api/parsing/channel`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта parse_single_channel.

### Детали реализации
```
Function: parse_single_channel
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 21:02:47*


## Get Token Usage Stats

**Эндпоинт:** `GET /api/stats/tokens`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_token_usage_stats.

### Детали реализации
```
Function: get_token_usage_stats
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-13 21:02:59*


## Create Channels From Folder

**Эндпоинт:** `POST /api/channels/from-folder`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта create_channels_from_folder.

### Детали реализации
```
Function: create_channels_from_folder
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-15 20:38:16*


## Create Channels From User Folder

**Эндпоинт:** `POST /api/channels/from-user-folder`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта create_channels_from_user_folder.

### Детали реализации
```
Function: create_channels_from_user_folder
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-15 21:02:53*


## Create Channels From User Channels

**Эндпоинт:** `POST /api/channels/from-user-channels`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта create_channels_from_user_channels.

### Детали реализации
```
Function: create_channels_from_user_channels
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-15 21:18:22*


## Debug Folders

**Эндпоинт:** `GET /api/debug/folders`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта debug_folders.

### Детали реализации
```
Function: debug_folders
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-15 21:38:03*


## Get User Folders

**Эндпоинт:** `GET /api/folders`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_user_folders.

### Детали реализации
```
Function: get_user_folders
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-15 21:56:45*


## Get User Channels

**Эндпоинт:** `GET /api/user-channels`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта get_user_channels.

### Детали реализации
```
Function: get_user_channels
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-16 00:13:50*


## Create Channel

**Эндпоинт:** `POST /api/channels`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта create_channel.

### Детали реализации
```
Function: create_channel
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-16 00:14:43*


## Cancel Parsing Session

**Эндпоинт:** `PUT /api/parsing/session/{session_id}/cancel`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта cancel_parsing_session.

### Детали реализации
```
Function: cancel_parsing_session
Location: Unknown
```

---

*Сгенерировано автоматически: 2025-09-16 00:28:40*
