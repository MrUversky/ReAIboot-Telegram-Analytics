#!/usr/bin/env python3
"""
Комплексное тестирование всей системы ReAIboot
"""

import sys
import os
import asyncio
import time
import subprocess
sys.path.append('src')

from src.app.supabase_client import SupabaseManager
from src.app.telegram_client import TelegramAnalyzer
from src.app.channel_baseline_analyzer import ChannelBaselineAnalyzer
from src.app.viral_post_detector import ViralPostDetector
from src.app.smart_top_posts_filter import SmartTopPostsFilter

def test_system_components():
    """Тестирует инициализацию всех компонентов системы"""
    print("🔧 ТЕСТИРОВАНИЕ КОМПОНЕНТОВ СИСТЕМЫ")
    print("=" * 50)

    components_status = {}

    # 1. Supabase клиент
    try:
        print("📡 Тест Supabase клиента...")
        supabase = SupabaseManager()
        components_status['supabase'] = supabase.client is not None
        print("✅ Supabase клиент" if components_status['supabase'] else "❌ Supabase клиент")
    except Exception as e:
        print(f"❌ Supabase клиент: {e}")
        components_status['supabase'] = False

    # 2. Telegram клиент
    try:
        print("📱 Тест Telegram клиента...")
        analyzer = TelegramAnalyzer()
        components_status['telegram'] = analyzer.client is not None
        print("✅ Telegram клиент" if components_status['telegram'] else "❌ Telegram клиент")
    except Exception as e:
        print(f"❌ Telegram клиент: {e}")
        components_status['telegram'] = False

    # 3. Viral Detection компоненты
    try:
        print("🔬 Тест Viral Detection компонентов...")
        if components_status.get('supabase', False):
            baseline_analyzer = ChannelBaselineAnalyzer(supabase)
            viral_detector = ViralPostDetector(baseline_analyzer)
            smart_filter = SmartTopPostsFilter(supabase)
            components_status['viral_detection'] = True
            print("✅ Viral Detection компоненты")
        else:
            components_status['viral_detection'] = False
            print("❌ Viral Detection компоненты (нужен Supabase)")
    except Exception as e:
        print(f"❌ Viral Detection компоненты: {e}")
        components_status['viral_detection'] = False

    # 4. API сервер
    try:
        print("🌐 Тест API сервера...")
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        components_status['api_server'] = response.status_code == 200
        print("✅ API сервер" if components_status['api_server'] else "❌ API сервер")
    except Exception as e:
        print(f"❌ API сервер: {e}")
        components_status['api_server'] = False

    return components_status

async def test_parsing_pipeline():
    """Тестирует полный pipeline парсинга"""
    print("\n🔄 ТЕСТИРОВАНИЕ ПАРСИНГОВОГО PIPELINE")
    print("=" * 50)

    try:
        # Инициализация компонентов
        supabase = SupabaseManager()
        analyzer = TelegramAnalyzer()

        # Тестовый канал
        test_channel = '@telegram'
        max_posts = 5

        print(f"📊 Запуск полного pipeline для {test_channel}...")

        # Шаг 1: Парсинг постов
        print("1️⃣ Парсинг постов из Telegram...")
        start_time = time.time()
        posts, channel_info = await analyzer.get_channel_posts(test_channel, max_posts=max_posts)
        parsing_time = time.time() - start_time

        print(f"⏱️ Время парсинга: {parsing_time:.2f} сек")
        if not posts:
            print("❌ Парсинг вернул пустой результат")
            if "error" in channel_info:
                print(f"   Ошибка: {channel_info['error']}")
            return False

        print(f"   Спарсено {len(posts)} постов")

        # Шаг 2: Сохранение в базу
        print("2️⃣ Сохранение в базу данных...")
        saved_posts = []
        for post in posts:
            try:
                post['channel_username'] = test_channel.replace('@', '')
                result = supabase.client.table('posts').upsert(post).execute()
                if result.data:
                    saved_posts.append(result.data[0])
            except Exception as e:
                print(f"   ⚠️ Ошибка сохранения поста: {e}")

        print(f"   Сохранено {len(saved_posts)} постов")

        # Шаг 3: Viral Detection (если база обновлена)
        print("3️⃣ Анализ Viral Detection...")
        try:
            baseline_analyzer = ChannelBaselineAnalyzer(supabase)
            viral_detector = ViralPostDetector(baseline_analyzer)

            # Проверяем базовые метрики канала
            baseline = baseline_analyzer.get_channel_baseline(test_channel.replace('@', ''))
            if not baseline:
                print("   📊 Расчет базовых метрик канала...")
                baseline = baseline_analyzer.calculate_channel_baseline(test_channel.replace('@', ''), posts)
                if baseline:
                    print(f"   ✅ Базовые метрики рассчитаны: avg_engagement={baseline.get('avg_engagement_rate', 0):.4f}")

            # Анализ постов на "залетевшесть"
            viral_posts = []
            for post in saved_posts:
                try:
                    viral_result = viral_detector.analyze_post_for_viral(post)
                    if viral_result.get('is_viral', False):
                        viral_posts.append(viral_result)
                except Exception as e:
                    print(f"   ⚠️ Ошибка анализа поста: {e}")

            print(f"   🎯 Найдено {len(viral_posts)} 'залетевших' постов")

        except Exception as e:
            print(f"   ⚠️ Viral Detection недоступен: {e}")
            print("      Нужно выполнить safe_schema_update.sql")

        # Шаг 4: Тестирование API эндпоинтов
        print("4️⃣ Тест API эндпоинтов...")
        import requests

        # Тест получения постов
        try:
            response = requests.get('http://localhost:8000/api/posts', params={'limit': 5}, timeout=10)
            if response.status_code == 200:
                api_posts = response.json()
                print(f"   ✅ API posts: получено {len(api_posts)} постов")
            else:
                print(f"   ❌ API posts: статус {response.status_code}")
        except Exception as e:
            print(f"   ❌ API posts: {e}")

        return len(saved_posts) > 0

    except Exception as e:
        print(f"❌ Ошибка тестирования pipeline: {e}")
        return False

def test_database_schema():
    """Тестирует схему базы данных"""
    print("\n🗄️ ТЕСТИРОВАНИЕ СХЕМЫ БАЗЫ ДАННЫХ")
    print("=" * 50)

    try:
        supabase = SupabaseManager()

        # Проверка обязательных таблиц
        required_tables = ['posts', 'channels', 'profiles', 'parsing_sessions']
        viral_tables = ['system_settings', 'channel_baselines']

        print("📋 Проверка основных таблиц...")
        for table in required_tables:
            try:
                result = supabase.client.table(table).select('*').limit(1).execute()
                print(f"✅ Таблица {table}")
            except Exception as e:
                print(f"❌ Таблица {table}: {e}")

        print("🔬 Проверка таблиц Viral Detection...")
        for table in viral_tables:
            try:
                result = supabase.client.table(table).select('*').limit(1).execute()
                print(f"✅ Таблица {table}")
            except Exception as e:
                print(f"❌ Таблица {table}: {e}")
                print("   Нужно выполнить safe_schema_update.sql")

        # Проверка новых колонок
        print("🔧 Проверка новых колонок в posts...")
        viral_columns = ['viral_score', 'engagement_rate', 'zscore', 'median_multiplier', 'last_viral_calculation']

        try:
            result = supabase.client.table('posts').select('id, ' + ', '.join(viral_columns)).limit(1).execute()
            if result.data:
                available = [col for col in viral_columns if col in result.data[0]]
                missing = [col for col in viral_columns if col not in result.data[0]]

                if available:
                    print(f"✅ Доступны: {', '.join(available)}")
                if missing:
                    print(f"❌ Отсутствуют: {', '.join(missing)}")
            else:
                print("⚠️ Таблица posts пуста")
        except Exception as e:
            print(f"❌ Ошибка проверки колонок: {e}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования схемы: {e}")
        return False

async def main():
    """Основная функция комплексного тестирования"""
    print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ReAIboot\n")

    # 1. Тест компонентов системы
    components = test_system_components()

    # 2. Тест схемы базы данных
    schema_ok = test_database_schema()

    # 3. Тест полного pipeline
    pipeline_ok = await test_parsing_pipeline()

    # Анализ результатов
    print("\n" + "=" * 60)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    # Сводка компонентов
    working_components = sum(1 for status in components.values() if status)
    total_components = len(components)

    print(f"🔧 Компоненты системы: {working_components}/{total_components}")

    issues = []
    recommendations = []

    # Анализ проблем
    if not components.get('supabase', False):
        issues.append("Проблемы с подключением к Supabase")
        recommendations.append("Проверьте настройки подключения к Supabase")

    if not components.get('telegram', False):
        issues.append("Проблемы с Telegram сессией")
        recommendations.append("Переавторизуйтесь в Telegram или проверьте session_per.session")

    if not components.get('viral_detection', False):
        issues.append("Viral Detection не инициализируется")
        recommendations.append("Выполните safe_schema_update.sql для обновления схемы БД")

    if not components.get('api_server', False):
        issues.append("API сервер недоступен")
        recommendations.append("Запустите python run_api.py")

    if not pipeline_ok:
        issues.append("Парсинговый pipeline не работает")
        recommendations.append("Проверьте доступ к каналам и Telegram API")

    # Вывод результатов
    if issues:
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"   • {issue}")

        print("\n🔧 РЕКОМЕНДАЦИИ:")
        for rec in recommendations:
            print(f"   • {rec}")
    else:
        print("\n🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ КОРРЕКТНО!")

        if working_components == total_components:
            print("\n✅ СИСТЕМА ГОТОВА К РАБОТЕ!")
            print("Можно запускать полный парсинг и анализ.")
        else:
            print("\n⚠️ НЕКОТОРЫЕ КОМПОНЕНТЫ РАБОТАЮТ С ОГРАНИЧЕНИЯМИ")
            print("Рекомендуется устранить оставшиеся проблемы.")

    return len(issues) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
