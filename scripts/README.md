# 🛠️ Scripts - Скрипты управления проектом

Эта папка содержит скрипты для запуска, остановки и управления проектом.

## 📄 Содержимое

### `run_api.py`
- **Описание**: Запуск FastAPI сервера backend
- **Использование**: `python scripts/run_api.py`

### `start_project.sh`
- **Описание**: Полный запуск проекта (backend + frontend + БД)
- **Использование**: `./scripts/start_project.sh`
- **Требует**: Docker и docker-compose

### `stop_project.sh`
- **Описание**: Остановка всех сервисов проекта
- **Использование**: `./scripts/stop_project.sh`
- **Останавливает**: Docker контейнеры

## 🚀 Использование

```bash
# Быстрый запуск API сервера
python scripts/run_api.py

# Полный запуск проекта
./scripts/start_project.sh

# Остановка проекта
./scripts/stop_project.sh
```

## 📝 Рекомендации

- Скрипты должны быть executable: `chmod +x script.sh`
- Использовать shebang: `#!/bin/bash` или `#!/usr/bin/env python3`
- Добавлять обработку ошибок и логирование
