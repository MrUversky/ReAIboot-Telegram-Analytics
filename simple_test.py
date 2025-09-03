#!/usr/bin/env python3
"""
Простой тест CRUD операций
"""

import sys
import os
sys.path.append('src')

from src.app.supabase_client import SupabaseManager

def main():
    print("🔧 ТЕСТ СУПАБЕЙС ПОСЛЕ ОТКЛЮЧЕНИЯ RLS")
    print("=" * 50)

    try:
        manager = SupabaseManager()

        # Тест создания канала
        print("1. Создание канала...")
        result = manager.upsert_channel('@test123', 'Тест канал', 'Тест')
        print(f"   Создание: {'✅' if result else '❌'}")

        # Тест получения каналов
        print("2. Получение каналов...")
        channels = manager.get_channels()
        print(f"   Каналов найдено: {len(channels)}")

        # Тест обновления (если есть каналы)
        if channels:
            print("3. Обновление канала...")
            channel_id = channels[0]['id']
            update_result = manager.update_channel(str(channel_id), {'title': 'Обновленный'})
            print(f"   Обновление: {'✅' if update_result else '❌'}")

            print("4. Удаление канала...")
            delete_result = manager.delete_channel(str(channel_id))
            print(f"   Удаление: {'✅' if delete_result else '❌'}")

        print("\n✅ ТЕСТ ЗАВЕРШЕН!")
        print("Если все операции успешны - RLS отключен правильно")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("RLS все еще активен или проблема с подключением")

if __name__ == "__main__":
    main()

