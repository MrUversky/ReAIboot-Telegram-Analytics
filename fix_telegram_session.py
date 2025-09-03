#!/usr/bin/env python3
"""
Исправление проблем с Telegram сессией
"""

import os
import sys
import shutil
sys.path.append('src')

def fix_session_files():
    """Исправляет проблемы с файлами сессии"""
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С TELEGRAM СЕССИЕЙ")
    print("=" * 50)

    # Проверяем текущие файлы сессии
    session_files = [
        'session_per.session',
        'session_per.session-journal',
        'telegram_session.session'
    ]

    print("📁 Проверка файлов сессии...")
    for file in session_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   {file}: {size} байт")
        else:
            print(f"   {file}: не найден")

    # Создаем резервные копии
    print("\n💾 Создание резервных копий...")
    for file in session_files:
        if os.path.exists(file):
            backup = f"{file}.backup"
            shutil.copy2(file, backup)
            print(f"   {file} → {backup}")

    # Удаляем проблемные файлы
    print("\n🗑️ Удаление проблемных файлов...")
    files_to_remove = ['session_per.session-journal']  # Только journal файл

    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Удален: {file}")

    print("\n✅ Сессия очищена от поврежденных файлов")
    print("Теперь нужно создать новую сессию.")

    return True

def create_new_session():
    """Создает новую Telegram сессию"""
    print("\n🔑 СОЗДАНИЕ НОВОЙ TELEGRAM СЕССИИ")
    print("=" * 50)

    try:
        from src.app.telegram_client import TelegramAnalyzer

        print("📱 Инициализация нового Telegram клиента...")

        # Создаем новую сессию
        analyzer = TelegramAnalyzer()

        if analyzer.client:
            print("✅ Новая сессия создана успешно")
            print("Теперь нужно авторизоваться в Telegram")
            return True
        else:
            print("❌ Не удалось создать новую сессию")
            return False

    except Exception as e:
        print(f"❌ Ошибка создания сессии: {e}")
        return False

def main():
    """Основная функция исправления сессии"""
    print("🚀 ЗАПУСК ИСПРАВЛЕНИЯ TELEGRAM СЕССИИ\n")

    # Шаг 1: Исправление файлов
    if not fix_session_files():
        print("❌ Не удалось исправить файлы сессии")
        return False

    # Шаг 2: Создание новой сессии
    if not create_new_session():
        print("❌ Не удалось создать новую сессию")
        return False

    print("\n" + "=" * 60)
    print("✅ ИСПРАВЛЕНИЕ СЕССИИ ЗАВЕРШЕНО!")
    print("\n🔧 Следующие шаги:")
    print("1. Запустите авторизацию: python setup_telegram_session.py")
    print("2. Следуйте инструкциям для входа в Telegram")
    print("3. После успешной авторизации протестируйте парсинг")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
