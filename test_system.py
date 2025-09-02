#!/usr/bin/env python3
"""
Скрипт для тестирования системы ReAIboot:
- Парсинг Telegram каналов за последние 5 дней
- Генерация сценариев через API
- Проверка работоспособности всех компонентов
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx

from src.app.settings import settings
from src.app.utils import setup_logger
from src.app.telegram_client import TelegramAnalyzer
from src.app.fetch import MessageFetcher
from src.app.metrics import MetricsCalculator
from src.app.mapper import ContentMapper
from src.app.writer import DataWriter

# Настройка логирования
logger = setup_logger(__name__)

class SystemTester:
    """Класс для тестирования всей системы."""

    def __init__(self):
        self.api_url = "http://localhost:8001"
        self.test_results = {
            "parsing": False,
            "metrics": False,
            "mapping": False,
            "llm_api": False,
            "scenarios": False
        }

    async def test_api_health(self) -> bool:
        """Проверка здоровья API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_url}/health")

                if response.status_code == 200:
                    data = response.json()
                    logger.info("✅ API сервер работает")
                    logger.info(f"   Статус: {data.get('status')}")
                    logger.info(f"   Версия: {data.get('version')}")
                    return True
                else:
                    logger.error(f"❌ API сервер вернул {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к API: {e}")
            return False

    async def test_telegram_parsing(self, days: int = 5, limit: int = 50) -> List[Dict]:
        """Тестирование парсинга Telegram каналов."""
        try:
            logger.info(f"🔍 Начинаем парсинг каналов за последние {days} дней...")

            # Загружаем каналы
            channels = settings.load_channels()
            logger.info(f"📋 Загружено {len(channels)} каналов")

            # Создаем fetcher
            async with MessageFetcher() as fetcher:
                messages = await fetcher.fetch_channels_data(
                    channels=channels,
                    days=days,
                    limit=limit
                )

            if messages:
                logger.info(f"✅ Получено {len(messages)} сообщений")
                self.test_results["parsing"] = True
                return messages
            else:
                logger.error("❌ Не удалось получить сообщения")
                return []

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return []

    async def test_metrics_calculation(self, messages: List[Dict]) -> List[Dict]:
        """Тестирование расчета метрик."""
        try:
            logger.info("📊 Расчет метрик вовлеченности...")

            # Загружаем веса
            weights = settings.load_score_weights()

            # Создаем калькулятор
            calculator = MetricsCalculator(weights=weights)
            messages_with_metrics = calculator.compute_metrics(messages)

            # Получаем топовые посты
            top_posts = calculator.get_top_overall(messages_with_metrics, top_n=10)

            if top_posts:
                logger.info(f"✅ Рассчитаны метрики для {len(messages_with_metrics)} сообщений")
                logger.info(f"   Топ постов: {len(top_posts)}")
                logger.info(f"   Лучший score: {max(p.get('score', 0) for p in top_posts):.2f}")
                self.test_results["metrics"] = True
                return top_posts
            else:
                logger.error("❌ Не удалось рассчитать метрики")
                return []

        except Exception as e:
            logger.error(f"❌ Ошибка расчета метрик: {e}")
            return []

    async def test_content_mapping(self, messages: List[Dict]) -> List[Dict]:
        """Тестирование маппинга контента."""
        try:
            logger.info("🗺️ Маппинг сообщений на рубрики...")

            # Загружаем план контента
            content_plan = settings.load_content_plan()

            # Создаем маппер
            mapper = ContentMapper(content_plan=content_plan)
            mapped_messages = mapper.map_messages(messages)

            mapped_count = sum(1 for msg in mapped_messages if msg.get("rubrics"))
            logger.info(f"✅ Маппинг завершен: {mapped_count} из {len(mapped_messages)} сообщений сопоставлены")
            self.test_results["mapping"] = True

            return mapped_messages

        except Exception as e:
            logger.error(f"❌ Ошибка маппинга: {e}")
            return messages

    async def test_llm_processing(self, top_posts: List[Dict]) -> Dict[str, Any]:
        """Тестирование LLM обработки через API."""
        try:
            logger.info("🤖 Тестирование LLM обработки...")

            # Берем первые 3 поста для теста
            test_posts = top_posts[:3]

            # Подготавливаем данные для API
            posts_data = []
            for post in test_posts:
                posts_data.append({
                    "message_id": str(post.get("message_id", "test_id")),
                    "channel_title": post.get("channel_title", "Test Channel"),
                    "text": post.get("text", "Test message"),
                    "views": post.get("views", 100),
                    "reactions": post.get("reactions", 10),
                    "replies": post.get("replies", 5),
                    "forwards": post.get("forwards", 2),
                    "score": post.get("score", 7.5)
                })

            # Отправляем запрос к API
            payload = {
                "posts": posts_data
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"📤 Отправка {len(posts_data)} постов на обработку...")
                response = await client.post(
                    f"{self.api_url}/api/llm/process",
                    json=payload
                )

                if response.status_code == 200:
                    logger.info("✅ LLM обработка запущена успешно")
                    self.test_results["llm_api"] = True

                    # Ждем немного и проверяем статус
                    await asyncio.sleep(5)

                    # Получаем статистику
                    stats_response = await client.get(f"{self.api_url}/api/stats/llm")
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        logger.info("📊 Статистика LLM:")
                        logger.info(f"   Процессоры: {stats.get('processor_status', {})}")

                    return {"success": True, "posts_processed": len(posts_data)}
                else:
                    logger.error(f"❌ Ошибка LLM обработки: {response.status_code}")
                    logger.error(f"   Ответ: {response.text}")
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"❌ Ошибка LLM обработки: {e}")
            return {"success": False, "error": str(e)}

    def save_test_results(self, messages: List[Dict], top_posts: List[Dict], llm_results: Dict):
        """Сохранение результатов тестирования."""
        try:
            logger.info("💾 Сохранение результатов тестирования...")

            writer = DataWriter()

            result_files = writer.save_all_data(
                all_messages=messages,
                top_overall=top_posts,
                top_by_channel=[],
                scenarios=None
            )

            # Сохраняем отчет о тестировании
            test_report = {
                "timestamp": datetime.now().isoformat(),
                "test_results": self.test_results,
                "stats": {
                    "total_messages": len(messages),
                    "top_posts": len(top_posts),
                    "llm_results": llm_results
                }
            }

            report_file = settings.out_dir / "test_report.json"
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(test_report, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Результаты сохранены в {settings.out_dir}")
            return result_files

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            return {}

    def print_summary(self):
        """Вывод итогов тестирования."""
        logger.info("\n" + "="*60)
        logger.info("📋 ИТОГИ ТЕСТИРОВАНИЯ СИСТЕМЫ")
        logger.info("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        for test_name, passed in self.test_results.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {test_name}")

        logger.info("-"*60)
        logger.info(f"Результат: {passed_tests}/{total_tests} тестов пройдено")

        if passed_tests == total_tests:
            logger.info("🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
        else:
            logger.warning("⚠️ Некоторые компоненты требуют внимания")

async def main():
    """Главная функция тестирования."""
    logger.info("🚀 НАЧИНАЕМ ТЕСТИРОВАНИЕ СИСТЕМЫ REAIBOOT")
    logger.info("="*60)

    tester = SystemTester()

    # 1. Проверка API
    logger.info("\n1️⃣ Проверка API сервера...")
    api_ok = await tester.test_api_health()
    if not api_ok:
        logger.error("❌ API сервер недоступен. Запустите: python run_api.py")
        return

    # 2. Парсинг Telegram
    logger.info("\n2️⃣ Тестирование парсинга Telegram...")
    messages = await tester.test_telegram_parsing(days=5, limit=100)
    if not messages:
        logger.error("❌ Парсинг не удался")
        return

    # 3. Расчет метрик
    logger.info("\n3️⃣ Расчет метрик...")
    top_posts = await tester.test_metrics_calculation(messages)
    if not top_posts:
        logger.error("❌ Расчет метрик не удался")
        return

    # 4. Маппинг контента
    logger.info("\n4️⃣ Маппинг контента...")
    mapped_messages = await tester.test_content_mapping(messages)

    # 5. LLM обработка
    logger.info("\n5️⃣ Тестирование LLM обработки...")
    llm_results = await tester.test_llm_processing(top_posts)

    # 6. Сохранение результатов
    logger.info("\n6️⃣ Сохранение результатов...")
    result_files = tester.save_test_results(messages, top_posts, llm_results)

    # 7. Итоги
    tester.print_summary()

    logger.info("\n" + "="*60)
    logger.info("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    logger.info("="*60)

    # Вывод информации о файлах
    if result_files:
        logger.info("\n📁 Сохраненные файлы:")
        for file_type, file_path in result_files.items():
            if file_path:
                logger.info(f"   📄 {file_type}: {file_path}")

if __name__ == "__main__":
    asyncio.run(main())
