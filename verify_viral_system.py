#!/usr/bin/env python3
"""
Проверка готовности системы Viral Detection после обновления базы данных
"""

import sys
import os
sys.path.append('src')

def check_viral_system():
    """Проверяет готовность системы Viral Detection"""
    print("🔍 ПРОВЕРКА ГОТОВНОСТИ VIRAL DETECTION СИСТЕМЫ")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    # 1. Проверка импортов
    total_checks += 1
    try:
        from src.app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        from src.app.viral_post_detector import ViralPostDetector
        from src.app.smart_top_posts_filter import SmartTopPostsFilter
        from src.app.supabase_client import SupabaseManager
        print("✅ Импорт модулей прошел успешно")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

    # 2. Проверка подключения к Supabase
    total_checks += 1
    try:
        supabase = SupabaseManager()
        if supabase.client:
            print("✅ Подключение к Supabase успешно")
            checks_passed += 1
        else:
            print("❌ Подключение к Supabase не удалось")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        return False

    # 3. Проверка существования таблиц
    total_checks += 1
    try:
        # Проверяем system_settings
        settings = supabase.get_system_setting('viral_weights')
        if settings:
            print("✅ Таблица system_settings существует и содержит данные")
            checks_passed += 1
        else:
            print("⚠️ Таблица system_settings существует, но нет данных")
            print("   Выполните safe_schema_update.sql для инициализации настроек")
    except Exception as e:
        print(f"❌ Ошибка проверки таблицы system_settings: {e}")

    # 4. Проверка структуры таблицы posts
    total_checks += 1
    try:
        # Пробуем выполнить запрос к posts с новыми колонками
        result = supabase.client.table('posts').select(
            'id, viral_score, engagement_rate, zscore'
        ).limit(1).execute()

        if result.data is not None:
            print("✅ Таблица posts содержит колонки для viral detection")
            checks_passed += 1
        else:
            print("❌ Таблица posts не содержит нужных колонок")
    except Exception as e:
        print(f"❌ Ошибка проверки таблицы posts: {e}")
        print("   Возможно, нужно выполнить safe_schema_update.sql")

    # 5. Проверка инициализации классов
    total_checks += 1
    try:
        baseline_analyzer = ChannelBaselineAnalyzer(supabase)
        viral_detector = ViralPostDetector(baseline_analyzer)
        smart_filter = SmartTopPostsFilter(supabase)
        print("✅ Все классы системы успешно инициализированы")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Ошибка инициализации классов: {e}")

    # 6. Проверка настроек
    total_checks += 1
    try:
        weights = baseline_analyzer.settings.get('viral_weights')
        thresholds = viral_detector.settings

        if weights and thresholds:
            print("✅ Настройки системы загружены корректно")
            print(f"   Веса: forward={weights['forward_rate']}, reaction={weights['reaction_rate']}, reply={weights['reply_rate']}")
            print(f"   Порог viral_score: {thresholds['min_viral_score']}")
            checks_passed += 1
        else:
            print("⚠️ Настройки системы неполные")
    except Exception as e:
        print(f"❌ Ошибка проверки настроек: {e}")

    # Результаты
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ: {checks_passed}/{total_checks} тестов пройдено")

    if checks_passed == total_checks:
        print("🎉 СИСТЕМА VIRAL DETECTION ПОЛНОСТЬЮ ГОТОВА К РАБОТЕ!")
        print("\n🚀 Следующие шаги:")
        print("1. Запустите API сервер: python run_api.py")
        print("2. Откройте админку и перейдите в 'Viral Detection'")
        print("3. Запустите парсинг каналов для расчета базовых метрик")
        return True
    else:
        print("⚠️ СИСТЕМА НУЖДАЕТСЯ В ДОНАСТРОЙКЕ")
        print("\n🔧 Рекомендации:")
        if checks_passed < total_checks * 0.8:
            print("- Выполните safe_schema_update.sql в Supabase SQL Editor")
        print("- Проверьте подключение к базе данных")
        print("- Убедитесь, что все зависимости установлены")
        return False

if __name__ == "__main__":
    success = check_viral_system()
    sys.exit(0 if success else 1)
