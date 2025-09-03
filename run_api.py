#!/usr/bin/env python3
"""
Скрипт для запуска ReAIboot API сервера.
"""

import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    from src.api_main import app
    import uvicorn

    print("🚀 Запуск ReAIboot API...")
    print("📱 Документация API: http://localhost:8000/docs")
    print("🔄 Альтернативная документация: http://localhost:8000/redoc")
    print("❤️  Health check: http://localhost:8000/health")
    print()

    uvicorn.run(
        "src.api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )
