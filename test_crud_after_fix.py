#!/usr/bin/env python3
"""
Тест CRUD операций после исправления RLS политик
"""

import sys
sys.path.append('src')

from src.app.supabase_client import SupabaseManager

def test_crud_operations():
    """Тестируем все CRUD операции"""

    manager = SupabaseManager()

    print("🧪 ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ ПОСЛЕ ИСПРАВЛЕНИЯ RLS")
    print("=" * 60)

    # 1. Создание канала
    print("\n1️⃣ Создание тестового канала...")
    test_channel = manager.upsert_channel('@test_channel_crud', 'Тестовый канал', 'Тест CRUD')
    print(f"   ✅ Создание: {'УСПЕШНО' if test_channel else 'ПРОБЛЕМА'}")

    # 2. Получение каналов
    print("\n2️⃣ Получение списка каналов...")
    channels = manager.get_channels()
    print(f"   ✅ Получение: {len(channels)} каналов найдено")

    # 3. Обновление канала
    if channels:
        channel_id = channels[0]['id']
        print(f"\n3️⃣ Обновление канала ID {channel_id}...")
        update_success = manager.update_channel(channel_id, {'title': 'Обновленный тестовый канал'})
        print(f"   ✅ Обновление: {'УСПЕШНО' if update_success else 'ПРОБЛЕМА'}")

    # 4. Создание поста
    print("\n4️⃣ Создание тестового поста...")
    test_post = {
        'message_id': 999999,
        'channel_username': '@test_channel_crud',
        'channel_title': 'Тестовый канал',
        'date': '2024-01-01T12:00:00Z',
        'text_preview': 'Тестовый пост для проверки CRUD',
        'full_text': 'Полный текст тестового поста',
        'views': 100,
        'forwards': 0,
        'replies': 0,
        'reactions': 5,
        'participants_count': 1000,
        'has_media': False,
        'permalink': 'https://t.me/test/999999',
        'raw_data': '{"test": true}'
    }

    post_success = manager.save_posts_batch('@test_channel_crud', [test_post])
    print(f"   ✅ Создание поста: {'УСПЕШНО' if post_success else 'ПРОБЛЕМА'}")

    # 5. Получение постов
    print("\n5️⃣ Получение постов...")
    posts = manager.get_posts(limit=10)
    print(f"   ✅ Получение постов: {len(posts)} постов найдено")

    # 6. Удаление канала (если он был создан нами)
    if test_channel:
        print("\n6️⃣ Удаление тестового канала...")
        delete_success = manager.delete_channel(str(channel_id) if 'channel_id' in locals() else 'test')
        print(f"   ✅ Удаление: {'УСПЕШНО' if delete_success else 'ПРОБЛЕМА'}")

    print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("Если все операции УСПЕШНЫ - RLS исправлен!")
    print("Если есть ПРОБЛЕМЫ - нужно выполнить SQL скрипт в Supabase")

if __name__ == "__main__":
    test_crud_operations()

