#!/usr/bin/env python3
"""
Очистка дублированных каналов в базе данных
"""

import sys
sys.path.append('src')

from app.supabase_client import SupabaseManager

def cleanup_duplicate_channels():
    """Удаляем дубликаты каналов, оставляя версию с @"""

    manager = SupabaseManager()

    # Получаем все каналы
    channels = manager.client.table('channels').select('*').execute()

    # Группируем по username без @
    channel_groups = {}
    for channel in channels.data:
        username = channel['username'].lstrip('@')
        if username not in channel_groups:
            channel_groups[username] = []
        channel_groups[username].append(channel)

    # Обрабатываем дубликаты
    deleted_count = 0

    for username, channels_list in channel_groups.items():
        if len(channels_list) > 1:
            print(f'\nОбработка дубликатов для {username}:')

            # Находим канал с @ (правильный) и без @
            with_at = None
            without_at = None

            for channel in channels_list:
                if channel['username'].startswith('@'):
                    with_at = channel
                else:
                    without_at = channel

            # Если есть оба варианта, удаляем версию без @
            if with_at and without_at:
                print(f'  Удаляем ID {without_at["id"]} (без @): "{without_at["username"]}"')
                print(f'  Оставляем ID {with_at["id"]} (с @): "{with_at["username"]}"')

                try:
                    manager.client.table('channels').delete().eq('id', without_at['id']).execute()
                    deleted_count += 1
                    print('  ✅ Удалено успешно')
                except Exception as e:
                    print(f'  ❌ Ошибка удаления: {e}')

    print(f'\n🎉 Очистка завершена! Удалено {deleted_count} дубликатов.')

if __name__ == "__main__":
    cleanup_duplicate_channels()
