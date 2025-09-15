#!/bin/bash

# ReAIboot - Скрипт запуска всего проекта
# Запускает backend API и frontend UI

echo "🚀 Запуск ReAIboot проекта..."
echo "================================="

# Функция для остановки старых процессов
cleanup_old_processes() {
    echo "🧹 Остановка старых процессов..."

    # Останавливаем старые процессы API (включая из виртуального окружения)
    pkill -f "python.*run_api.py" 2>/dev/null && echo "✅ Старые API процессы остановлены"
    pkill -f "scripts/run_api.py" 2>/dev/null && echo "✅ Старые API процессы остановлены"

    # Останавливаем старые процессы npm
    pkill -f "npm.*run.*dev" 2>/dev/null && echo "✅ Старые npm процессы остановлены"

    # Останавливаем процессы на портах 8000, 8001 и 3000
    lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Освобожден порт 8000"
    lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "✅ Освобожден порт 8001"
    lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "✅ Освобожден порт 3000"

    # Удаляем поврежденные файлы сессий
    rm -f session_per.session* 2>/dev/null && echo "✅ Поврежденные сессии удалены"
    rm -f telegram_session.session* 2>/dev/null && echo "✅ Старые Telegram сессии удалены"

    sleep 2
}

# Останавливаем старые процессы
cleanup_old_processes

# Проверка наличия Python виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Создайте его командой: python3 -m venv venv"
    exit 1
fi

# Проверка наличия python в виртуальном окружении
if [ ! -f "venv/bin/python" ]; then
    echo "❌ Python не найден в виртуальном окружении!"
    echo "Пересоздайте виртуальное окружение: rm -rf venv && python3 -m venv venv"
    exit 1
fi

# Проверка наличия зависимостей
if [ ! -f "requirements.txt" ]; then
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка/обновление зависимостей
echo "📦 Проверка зависимостей..."
pip install -r requirements.txt

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте его на основе .env.example"
    echo "Необходимые переменные:"
    echo "  - TELEGRAM_API_ID"
    echo "  - TELEGRAM_API_HASH"
    echo "  - OPENAI_API_KEY"
    echo "  - CLAUDE_API_KEY (опционально)"
    echo "  - SUPABASE_URL (опционально)"
    echo "  - SUPABASE_ANON_KEY (опционально)"
fi

# Запуск backend API в фоне на порту 8001
echo "🔄 Запуск backend API..."
export TEST_USER_ID="299bec46-494d-449e-92d5-c88eb055436a"
PYTHONPATH="$PWD/src" ./venv/bin/python -m uvicorn src.api_main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

# Ожидание запуска API
echo "⏳ Ожидание запуска API сервера..."
sleep 5

# Проверка работы API
if curl -s http://localhost:8001/docs > /dev/null; then
    echo "✅ API сервер запущен на http://localhost:8001"
    echo "📚 Документация API: http://localhost:8001/docs"
else
    echo "❌ Ошибка запуска API сервера!"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Переход в директорию frontend
if [ -d "reai-boot-ui" ]; then
    echo "🎨 Переход в директорию frontend..."
    cd reai-boot-ui

    # Проверка наличия зависимостей frontend
    if [ ! -d "node_modules" ]; then
        echo "📦 Установка зависимостей frontend..."
        npm install
    fi

    # Проверка наличия .env.local
    if [ ! -f ".env.local" ]; then
        echo "⚠️  Файл .env.local не найден в reai-boot-ui/"
        echo "Создайте его на основе env-example.txt"
        echo "Необходимые переменные:"
        echo "  - NEXT_PUBLIC_SUPABASE_URL"
        echo "  - NEXT_PUBLIC_SUPABASE_ANON_KEY"
        echo "  - NEXT_PUBLIC_API_URL=http://localhost:8001"
    fi

    # Запуск frontend в фоне с правильным API URL
    echo "🎨 Запуск Next.js frontend..."
    NEXT_PUBLIC_API_URL=http://localhost:8001 npm run dev &
    FRONTEND_PID=$!

    # Ожидание запуска frontend
    echo "⏳ Ожидание запуска Next.js..."
    sleep 10

    echo ""
    echo "🎉 ПРОЕКТ ЗАПУЩЕН!"
    echo "================================="
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8001"
    echo "📚 API Docs: http://localhost:8001/docs"
    echo ""
    echo "Сервисы запущены в фоне. Для остановки используйте:"
    echo "  ./stop_project.sh"
    echo "================================="

    # Сохраняем PIDs в файл для последующей остановки
    echo "$API_PID" > .running_pids
    echo "$FRONTEND_PID" >> .running_pids

    echo "✅ PIDs сохранены в .running_pids"
    echo "✅ Скрипт завершен - сервисы работают в фоне"
else
    echo "⚠️  Директория reai-boot-ui не найдена!"
    echo "Frontend не будет запущен"
    echo ""
    echo "✅ Backend API запущен на http://localhost:8001"
    echo "📚 Документация: http://localhost:8001/docs"

    # Сохраняем PID API для остановки
    echo "$API_PID" > .running_pids
    echo "✅ PID сохранен в .running_pids"
fi
