#!/usr/bin/env python3
"""
Запуск всех тестов системы ReAIboot
"""

import sys
import os
import subprocess
import time

def run_test(test_file, description):
    """Запускает отдельный тест"""
    print(f"\n{'='*20} {description} {'='*20}")
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, test_file],
                              capture_output=True, text=True, timeout=60)
        end_time = time.time()

        print(".2f"
        if result.returncode == 0:
            print("✅ ТЕСТ ПРОШЕЛ УСПЕШНО")
            return True
        else:
            print("❌ ТЕСТ ПРОВАЛЕН")
            print("\nSTDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("⏰ ТЕСТ ПРЕВЫСИЛ ВРЕМЯ ОЖИДАНИЯ (60 сек)")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПУСКА ТЕСТА: {e}")
        return False

def main():
    """Основная функция запуска всех тестов"""
    print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ ReAIboot")
    print("=" * 60)

    tests = [
        ("test_database_status.py", "БАЗЫ ДАННЫХ"),
        ("test_telegram_parsing.py", "TELEGRAM И ПАРСИНГА"),
        ("test_full_system.py", "КОМПЛЕКСНОЙ СИСТЕМЫ"),
        ("verify_viral_system.py", "VIRAL DETECTION")
    ]

    results = []

    for test_file, description in tests:
        if os.path.exists(test_file):
            success = run_test(test_file, description)
            results.append((description, success))
        else:
            print(f"⚠️ Тест {test_file} не найден")
            results.append((description, False))

    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    passed = 0
    total = len(results)

    for description, success in results:
        status = "✅ ПРОШЕЛ" if success else "❌ ПРОВАЛЕН"
        print("20")
        if success:
            passed += 1

    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed}/{total} тестов прошли успешно")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("Система готова к работе.")
    elif passed >= total * 0.7:
        print("\n⚠️ БОЛЬШИНСТВО ТЕСТОВ ПРОШЛИ УСПЕШНО")
        print("Система работоспособна, но есть проблемы для исправления.")
    else:
        print("\n❌ МНОГО ПРОБЛЕМ ОБНАРУЖЕНО")
        print("Необходимо исправить критические ошибки перед запуском.")

    # Рекомендации
    print("\n🔧 РЕКОМЕНДАЦИИ:")

    if passed < total:
        print("- Запустите тесты индивидуально для детального анализа")
        print("- Проверьте логи ошибок выше")
        print("- Исправьте выявленные проблемы")

    print("- Для быстрого тестирования запустите: python run_all_tests.py")
    print("- Для запуска системы выполните: ./start_project.sh")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
