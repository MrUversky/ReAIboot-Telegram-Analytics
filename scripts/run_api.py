#!/usr/bin/env python3
"""
Скрипт для запуска ReAIboot API сервера.
"""

import os
import sys
from pathlib import Path

# Получаем абсолютный путь к корневой директории проекта
script_dir = Path(__file__).parent
project_root = script_dir.parent

# Добавляем src в путь для импортов
sys.path.insert(0, str(project_root / "src"))

if __name__ == "__main__":
    try:
        print("🚀 Запуск ReAIboot API...")
        print("📱 Документация API: http://localhost:8000/docs")
        print("🔄 Альтернативная документация: http://localhost:8000/redoc")
        print("❤️  Health check: http://localhost:8000/health")
        print("📊 Подробный health: http://localhost:8000/api/health")
        print()

        # Запускаем uvicorn напрямую через subprocess
        import subprocess
        import sys

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api_main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
            "--reload-dir",
            str(project_root / "src"),
            "--log-level",
            "info",
        ]

        subprocess.run(cmd)

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь что вы находитесь в корневой директории проекта")
        print("Или активируйте виртуальное окружение: source venv/bin/activate")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
