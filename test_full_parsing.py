#!/usr/bin/env python3
"""
Тест полного цикла парсинга Telegram канала
"""

import asyncio
import sys
import os
sys.path.append('src')

from app.telegram_client import TelegramAnalyzer
from app.supabase_client import SupabaseManager
from app.settings import settings

async def test_full_parsing():
    """Тестируем полный цикл парсинга"""

    print("🚀 Начинаем тестирование полного цикла парсинга")
    print("=" * 50)

    # 1. Создаем сессию в базе данных
    print("1. Создаем сессию парсинга...")
    supabase_manager = SupabaseManager()
    session_data = {
        'started_at': '2025-09-03T01:59:00.000000+00:00',
        'status': 'running',
        'channels_parsed': 1,
        'posts_found': 0,
        'initiated_by': None
    }
    session_result = supabase_manager.save_parsing_session(session_data)
    session_id = session_result['id']
    print(f"✅ Создана сессия #{session_id}")

    # 2. Парсим канал
    print("\n2. Парсим канал @dnevteh...")
    analyzer = TelegramAnalyzer()
    try:
        posts, channel_info = await analyzer.get_messages('@dnevteh', days=30, limit=5)

        print(f"📺 Канал: {channel_info['title']} (@{channel_info['username']})")
        print(f"👥 Подписчиков: {channel_info['participants_count']}")
        print(f"📝 Найдено постов: {len(posts)}")

        # 3. Сохраняем информацию о канале
        print("\n3. Сохраняем информацию о канале...")
        channel_saved = supabase_manager.upsert_channel(
            username=channel_info['username'],
            title=channel_info['title'],
            description=channel_info.get('about', '')
        )
        if channel_saved:
            print("✅ Канал сохранен в базу данных")
        else:
            print("❌ Ошибка сохранения канала")

        # 4. Сохраняем посты в базу
        if posts:
            print("\n4. Сохраняем посты в базу данных...")
            saved_count = supabase_manager.save_posts_batch(posts)
            print(f"💾 Сохранено {saved_count} постов")

            # Показываем первый пост
            first_post = posts[0]
            print("\n📄 Первый пост:")
            print(f"   ID: {first_post.get('message_id')}")
            print(f"   Дата: {first_post.get('date')}")
            print(f"   Текст: {first_post.get('text', '')[:100]}...")
        else:
            print("❌ Посты не найдены")

        # 5. Обновляем сессию
        print("\n5. Обновляем статус сессии...")
        supabase_manager.update_parsing_session(session_id, {
            'status': 'completed',
            'posts_found': len(posts),
            'completed_at': '2025-09-03T01:59:05.000000+00:00'
        })
        print("✅ Сессия обновлена")

    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")

        # Обновляем сессию с ошибкой
        supabase_manager.update_parsing_session(session_id, {
            'status': 'failed',
            'error_message': str(e),
            'completed_at': '2025-09-03T01:59:05.000000+00:00'
        })

    finally:
        await analyzer.disconnect()

    # 6. Финальная проверка
    print("\n6. Финальная проверка сессии...")
    sessions = supabase_manager.client.table('parsing_sessions').select('*').eq('id', session_id).execute()
    if sessions.data:
        session = sessions.data[0]
        print(f"🎯 Сессия #{session_id}: {session['status']}")
        print(f"   Постов найдено: {session['posts_found']}")
        print(f"   Завершена: {session['completed_at']}")

    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_full_parsing())
