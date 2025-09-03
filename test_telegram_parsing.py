#!/usr/bin/env python3
"""
Тест Telegram сессии и функций парсинга
"""

import sys
import os
import asyncio
import time
sys.path.append('src')

from src.app.telegram_client import TelegramAnalyzer
from src.app.supabase_client import SupabaseManager

async def test_telegram_session():
    """Тестирует Telegram сессию"""
    print("📱 ТЕСТИРОВАНИЕ TELEGRAM СЕССИИ")
    print("=" * 50)

    try:
        print("🔑 Инициализация Telegram клиента...")
        analyzer = TelegramAnalyzer()

        if not analyzer.client:
            print("❌ Не удалось инициализировать Telegram клиент")
            return False

        print("✅ Telegram клиент инициализирован")

        # Тест подключения
        print("🌐 Тест подключения к Telegram...")
        await analyzer.client.connect()

        if await analyzer.client.is_connected():
            print("✅ Подключение к Telegram успешно")
        else:
            print("❌ Не удалось подключиться к Telegram")
            return False

        # Тест получения информации о себе
        print("👤 Получение информации об аккаунте...")
        try:
            me = await analyzer.client.get_me()
            print(f"✅ Авторизован как: {me.username or me.first_name}")
        except Exception as e:
            print(f"❌ Ошибка получения информации об аккаунте: {e}")
            return False

        # Тест доступа к каналу (простой тест)
        test_channels = ['@telegram']  # Публичный канал для теста

        for channel_username in test_channels:
            print(f"📺 Тест доступа к каналу {channel_username}...")
            try:
                # Попытка получить информацию о канале
                channel = await analyzer.client.get_entity(channel_username)
                print(f"✅ Доступ к каналу {channel_username} получен")
                print(f"   Название: {channel.title}")
                print(f"   Подписчиков: {getattr(channel, 'participants_count', 'N/A')}")
            except Exception as e:
                print(f"❌ Ошибка доступа к каналу {channel_username}: {e}")

        await analyzer.client.disconnect()
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка Telegram сессии: {e}")
        return False

async def test_parsing_function():
    """Тестирует функцию парсинга"""
    print("\n🔍 ТЕСТИРОВАНИЕ ФУНКЦИЙ ПАРСИНГА")
    print("=" * 50)

    try:
        analyzer = TelegramAnalyzer()

        # Тест парсинга небольшого канала
        test_channel = '@telegram'  # Публичный канал для теста
        max_posts = 3  # Маленькое количество для быстрого теста

        print(f"📊 Тест парсинга канала {test_channel} (макс {max_posts} постов)...")

        start_time = time.time()
        posts, channel_info = await analyzer.get_channel_posts(test_channel, max_posts=max_posts)
        parsing_time = time.time() - start_time

        print(f"⏱️ Время парсинга: {parsing_time:.2f} сек")
        if posts:
            print(f"✅ Успешно спарсено {len(posts)} постов")
            for i, post in enumerate(posts[:3]):  # Показываем первые 3 поста
                print(f"   Пост {i+1}: ID={post.get('message_id')}, просмотры={post.get('views', 'N/A')}")
        else:
            print("⚠️ Парсинг вернул пустой результат")
            print("   Возможные причины:")
            print("   - Канал не найден или недоступен")
            print("   - Проблемы с Telegram API")
            print("   - Ограничения доступа")

        # Тест сохранения в базу данных
        if posts:
            print("💾 Тест сохранения в базу данных...")
            supabase = SupabaseManager()

            try:
                saved_count = 0
                for post in posts:
                    # Добавляем информацию о канале
                    post['channel_username'] = test_channel.replace('@', '')

                    # Сохраняем пост
                    result = supabase.client.table('posts').upsert(post).execute()
                    if result.data:
                        saved_count += 1

                print(f"✅ Успешно сохранено {saved_count} постов в базу данных")

            except Exception as e:
                print(f"❌ Ошибка сохранения в БД: {e}")

        return len(posts) > 0

    except Exception as e:
        print(f"❌ Ошибка тестирования парсинга: {e}")
        return False

async def test_channel_list():
    """Тестирует список каналов для парсинга"""
    print("\n📋 ТЕСТИРОВАНИЕ СПИСКА КАНАЛОВ")
    print("=" * 50)

    try:
        # Читаем список каналов
        channels_file = 'channels.txt'

        if os.path.exists(channels_file):
            with open(channels_file, 'r', encoding='utf-8') as f:
                channels = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            print(f"📄 Найдено {len(channels)} каналов в файле {channels_file}")

            # Показываем первые несколько каналов
            for i, channel in enumerate(channels[:5]):
                print(f"   {i+1}. {channel}")

            if len(channels) > 5:
                print(f"   ... и ещё {len(channels) - 5} каналов")

            # Тест валидности каналов
            analyzer = TelegramAnalyzer()
            valid_channels = []

            print("🔍 Проверка доступности каналов...")
            for channel in channels[:3]:  # Проверяем только первые 3 для скорости
                try:
                    await analyzer.client.connect()
                    channel_entity = await analyzer.client.get_entity(channel)
                    valid_channels.append(channel)
                    print(f"✅ {channel} - доступен")
                    await analyzer.client.disconnect()
                except Exception as e:
                    print(f"❌ {channel} - недоступен: {str(e)[:50]}...")

            print(f"\n📊 Результат проверки: {len(valid_channels)}/{len(channels[:3])} каналов доступны")

            return len(valid_channels) > 0
        else:
            print(f"❌ Файл {channels_file} не найден")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки списка каналов: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ TELEGRAM И ПАРСИНГА\n")

    success = True

    # Тест Telegram сессии
    if not await test_telegram_session():
        success = False

    # Тест функций парсинга
    if not await test_parsing_function():
        success = False

    # Тест списка каналов
    if not await test_channel_list():
        success = False

    # Итоговый результат
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ TELEGRAM ПРОШЛО УСПЕШНО!")
        print("\n✅ Система готова к парсингу")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С TELEGRAM!")
        print("\n🔧 Возможные решения:")
        print("- Проверьте файл сессии session_per.session")
        print("- Переавторизуйтесь в Telegram")
        print("- Проверьте список каналов в channels.txt")
        print("- Проверьте доступ к каналам")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
