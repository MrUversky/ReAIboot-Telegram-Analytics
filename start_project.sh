#!/bin/bash

# ReAIboot - Скрипт запуска всего проекта
# Запускает backend API и frontend UI

echo "🚀 Запуск ReAIboot проекта..."
echo "================================="

# Проверка наличия Python виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Создайте его командой: python -m venv venv"
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

# Запуск backend API в фоне
echo "🔄 Запуск backend API..."
python run_api.py &
API_PID=$!

# Ожидание запуска API
echo "⏳ Ожидание запуска API сервера..."
sleep 5

# Проверка работы API
if curl -s http://localhost:8001/health > /dev/null; then
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

    # Запуск frontend в фоне
    echo "🎨 Запуск Next.js frontend..."
    npm run dev &
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
    echo "Для остановки нажмите Ctrl+C"
    echo "================================="

    # Функция очистки при завершении
    cleanup() {
        echo ""
        echo "🛑 Остановка сервисов..."
        kill $API_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Все сервисы остановлены"
        exit 0
    }

    # Обработка сигналов завершения
    trap cleanup SIGINT SIGTERM

    # Ожидание завершения
    wait
else
    echo "⚠️  Директория reai-boot-ui не найдена!"
    echo "Frontend не будет запущен"
    echo ""
    echo "✅ Backend API запущен на http://localhost:8001"
    echo "📚 Документация: http://localhost:8001/docs"
    echo ""
    echo "Для остановки нажмите Ctrl+C"

    # Ожидание завершения
    wait $API_PID
fi
