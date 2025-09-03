#!/bin/bash

# Скрипт для остановки всех процессов ReAIboot
echo "🛑 ОСТАНОВКА ПРОЕКТА REAIBOOT"
echo "============================"

# Останавливаем процессы
echo "Останавливаем API сервер..."
pkill -9 -f "python.*run_api.py" 2>/dev/null && echo "✅ API остановлен"

echo "Останавливаем UI сервер..."
pkill -9 -f "npm.*run.*dev" 2>/dev/null && echo "✅ UI остановлен"

echo "Освобождаем порты..."
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Порт 8000 освобожден"
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "✅ Порт 3000 освобожден"

echo "Удаляем поврежденные сессии..."
rm -f session_per.session* 2>/dev/null && echo "✅ Сессии удалены"

echo ""
echo "✅ ВСЕ ПРОЦЕССЫ ОСТАНОВЛЕНЫ!"
echo "Теперь можно безопасно запустить проект командой:"
echo "  ./start_project.sh"


