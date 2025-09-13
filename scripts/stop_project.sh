#!/bin/bash

# ReAIboot - Скрипт остановки всего проекта

echo "🛑 Остановка ReAIboot проекта..."
echo "================================="

# Функция для остановки процессов
stop_processes() {
    echo "🧹 Остановка всех процессов..."
    # Принудительная остановка всех процессов проекта
    echo "🔨 Принудительная остановка всех процессов проекта..."
    pkill -9 -f "python.*run_api.py" 2>/dev/null && echo "✅ API процессы остановлены"
    pkill -9 -f "scripts/run_api.py" 2>/dev/null && echo "✅ API процессы остановлены"
    pkill -9 -f "npm.*run.*dev" 2>/dev/null && echo "✅ npm процессы остановлены"

    # Освобождаем порты
    lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Порт 8000 освобожден"
    lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "✅ Порт 3000 освобожден"
    lsof -ti:3001 | xargs kill -9 2>/dev/null && echo "✅ Порт 3001 освобожден"

    # Удаляем PID файл и поврежденные сессии
    rm -f .running_pids 2>/dev/null && echo "✅ PID файл удален"
    rm -f session_per.session* 2>/dev/null && echo "✅ Поврежденные сессии удалены"
    rm -f telegram_session.session* 2>/dev/null && echo "✅ Telegram сессии удалены"
}

# Выполняем остановку
stop_processes

echo ""
echo "✅ Все сервисы остановлены!"
echo "================================="
echo "Для запуска используйте:"
echo "  ./start_project.sh"
