# Dockerfile для ReAIboot API
FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/
COPY content_plan.yaml .
COPY prompts_config.yaml . 2>/dev/null || true

# Создание директории для логов и данных
RUN mkdir -p /app/logs /app/data

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV TZ=Asia/Tbilisi

# Запуск приложения
CMD ["python", "-m", "src.api_main"]
