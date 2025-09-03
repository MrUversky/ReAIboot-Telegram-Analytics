"""
Главный модуль приложения - точка входа.
"""

import asyncio
import logging
import sys
import time
from typing import Dict, List, Any, Optional
import argparse
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    tqdm = lambda x, **kwargs: x  # fallback без progress bar

from src.app.settings import settings
from src.app.utils import setup_logger
from src.app.telegram_client import TelegramAnalyzer
from src.app.fetch import MessageFetcher
from src.app.metrics import MetricsCalculator
from src.app.mapper import ContentMapper
from src.app.llm import LLMProcessor
from src.app.writer import DataWriter
from src.app.cli import CLI
from src.app.smart_top_posts_filter import SmartTopPostsFilter
from src.app.supabase_client import SupabaseManager

# Настройка логирования
logger = setup_logger(__name__)


async def run_analysis(args: argparse.Namespace) -> None:
    """
    Основная функция для запуска анализа.
    
    Args:
        args: Аргументы командной строки.
    """
    
    try:
        # Настройка параметров
        days = args.days
        top_overall_n = args.top_overall
        top_per_channel_n = args.top_per_channel
        limit_per_channel = args.limit
        use_llm = not args.no_llm
        
        # Загрузка списка каналов
        channels = settings.load_channels(args.channels_file)
        logger.info(f"Загружено {len(channels)} каналов для анализа")
        
        # Загрузка весов для расчета метрик
        weights = settings.load_score_weights(args.score_config)
        
        # Загрузка плана контента
        content_plan = settings.load_content_plan(args.content_plan)
        
        # 1. Сбор данных из каналов
        logger.info(f"Начинаем сбор данных за последние {days} дней (лимит: {limit_per_channel} сообщений)")
        
        async with MessageFetcher() as fetcher:
            messages = await fetcher.fetch_channels_data(
                channels=channels,
                days=days,
                limit=limit_per_channel
            )
        
        if not messages:
            logger.error("Не удалось получить сообщения из каналов")
            return
        
        logger.info(f"Получено {len(messages)} сообщений из {len(channels)} каналов")
        
        # 2. Расчет метрик вовлеченности
        logger.info("Расчет метрик вовлеченности")
        
        calculator = MetricsCalculator(weights=weights)
        messages_with_metrics = calculator.compute_metrics(messages)
        
        # 3. Выбор лучших сообщений
        logger.info(f"Выбор лучших {top_overall_n} сообщений и топ-{top_per_channel_n} для каждого канала")
        
        top_overall = calculator.get_top_overall(messages_with_metrics, top_n=top_overall_n)
        top_by_channel = calculator.get_top_by_channel(messages_with_metrics, top_n=top_per_channel_n)
        
        # 4. Маппинг сообщений на рубрики
        logger.info("Сопоставление сообщений с рубриками")

        mapper = ContentMapper(content_plan=content_plan)

        # Маппинг всех сообщений
        messages_with_metrics = mapper.map_messages(messages_with_metrics)

        # 5. УМНАЯ ФИЛЬТРАЦИЯ САМЫХ "ЗАЛЕТЕВШИХ" ПОСТОВ
        logger.info("Умная фильтрация самых 'залетевших' постов на основе базовых метрик каналов")

        # Инициализируем умный фильтр
        supabase_manager = SupabaseManager()
        smart_filter = SmartTopPostsFilter(supabase_manager)

        # Применяем умную фильтрацию
        filter_result = smart_filter.filter_top_posts(
            all_posts=messages_with_metrics,
            max_posts_per_channel=3,  # Максимум 3 поста с канала
            max_total_posts=top_overall_n  # Общее ограничение
        )

        # Получаем отфильтрованные посты для дальнейшей обработки
        top_posts_for_llm = filter_result.selected_posts

        # Обновляем топы для совместимости с существующим кодом
        top_overall = calculator.get_top_overall(messages_with_metrics, top_n=top_overall_n)
        top_by_channel = calculator.get_top_by_channel(messages_with_metrics, top_n=top_per_channel_n)

        # Выводим статистику фильтрации
        filter_stats = smart_filter.get_filter_stats(filter_result)
        logger.info("=== СТАТИСТИКА УМНОЙ ФИЛЬТРАЦИИ ===")
        logger.info(f"Всего постов: {filter_stats['input_posts']}")
        logger.info(f"Каналов обработано: {filter_stats['channels_processed']}")
        logger.info(f"Отфильтровано: {filter_stats['filtered_out']}")
        logger.info(f"Выбрано для LLM: {filter_stats['selected']}")
        logger.info(f"Эффективность фильтрации: {filter_stats['filter_efficiency']:.1%}")
        logger.info(".2f")
        logger.info("Причины отсева:")
        for reason, count in filter_result.filtered_out.items():
            if count > 0:
                logger.info(f"  - {reason}: {count}")
        logger.info("=" * 30)
        
        # 6. Генерация сценариев через LLM (если включено)
        scenarios = {}

        if use_llm:
            logger.info("Генерация сценариев через LLM для отфильтрованных постов")

            llm_processor = LLMProcessor()

            if not llm_processor.is_llm_available():
                logger.warning("LLM недоступен. Сценарии не будут сгенерированы.")
            else:
                # Обрабатываем только предварительно отфильтрованные "залетевшие" посты
                logger.info(f"LLM обработка {len(top_posts_for_llm)} отфильтрованных постов")

                for message in tqdm(top_posts_for_llm, desc="Генерация сценариев"):
                    message_id = message.get("message_id")

                    # Получаем рубрики для сообщения с помощью LLM
                    rubrics = await llm_processor.classify_message(message, mapper.get_all_rubrics())

                    # Если рубрики не определены через LLM, используем рубрики из эвристического маппинга
                    if not rubrics and "rubrics" in message:
                        rubrics = message["rubrics"]

                    # Если есть хотя бы одна рубрика, генерируем сценарий
                    if rubrics:
                        # Берем первую рубрику для сценария
                        rubric_id = rubrics[0]

                        # Генерируем сценарий
                        scenario = await llm_processor.generate_scenarios(message, rubric_id)
                        scenarios[str(message_id)] = scenario
                    else:
                        logger.warning(f"Не удалось определить рубрику для сообщения {message_id}")

                logger.info(f"Сгенерировано сценариев: {len(scenarios)} из {len(top_posts_for_llm)} постов")
        
        # 7. Сохранение результатов
        logger.info("Сохранение результатов")

        writer = DataWriter()
        result_files = writer.save_all_data(
            all_messages=messages_with_metrics,
            top_overall=top_overall,
            top_by_channel=top_by_channel,
            scenarios=scenarios if use_llm else None,
            filtered_posts=top_posts_for_llm if use_llm else None
        )
        
        # Выводим информацию о сохраненных файлах
        logger.info("Анализ завершен. Результаты сохранены:")
        for file_type, file_path in result_files.items():
            if file_path:
                logger.info(f"  - {file_type}: {file_path}")
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении анализа: {e}", exc_info=True)


def main():
    """Точка входа в приложение."""
    
    try:
        # Создаем CLI обработчик
        cli = CLI()
        
        # Запускаем основную функцию с аргументами командной строки
        cli.parse_and_run(run_analysis)
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
