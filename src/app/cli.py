"""
Модуль для работы с командной строкой.
"""

import argparse
import logging
import sys
import asyncio
from typing import Dict, Any, Optional

from .settings import settings
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)


class CLI:
    """Класс для обработки аргументов командной строки."""
    
    def __init__(self):
        """Инициализирует обработчик командной строки."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Создает парсер аргументов командной строки.
        
        Returns:
            Настроенный парсер аргументов.
        """
        
        parser = argparse.ArgumentParser(
            description="ReAIboot Telegram Analytics - анализатор Telegram-каналов и генератор идей для контента",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        # Основные параметры
        parser.add_argument(
            "--days", type=int, default=7,
            help="Количество дней для анализа"
        )
        
        parser.add_argument(
            "--top-overall", type=int, default=30,
            help="Количество лучших постов в общем рейтинге"
        )
        
        parser.add_argument(
            "--top-per-channel", type=int, default=5,
            help="Количество лучших постов для каждого канала"
        )
        
        parser.add_argument(
            "--limit", type=int, default=100,
            help="Максимальное количество сообщений для загрузки из канала"
        )
        
        # Пути к файлам конфигурации
        parser.add_argument(
            "--channels-file", type=str, default=None,
            help="Путь к файлу со списком каналов"
        )
        
        parser.add_argument(
            "--content-plan", type=str, default=None,
            help="Путь к файлу с планом контента"
        )
        
        parser.add_argument(
            "--score-config", type=str, default=None,
            help="Путь к файлу с весами для расчета метрик"
        )
        
        # Другие параметры
        parser.add_argument(
            "--tz", type=str, default=None,
            help="Часовой пояс (по умолчанию из .env или Asia/Tbilisi)"
        )
        
        parser.add_argument(
            "--no-llm", action="store_true",
            help="Отключить использование LLM для генерации сценариев"
        )
        
        # Заглушка для будущих интеграций
        parser.add_argument(
            "--export", choices=["notion", "sheets"], default=None,
            help="Экспорт данных в Notion или Google Sheets (пока не реализовано)"
        )
        
        return parser
    
    def parse_args(self, args=None) -> argparse.Namespace:
        """
        Разбирает аргументы командной строки.
        
        Args:
            args: Аргументы для разбора. По умолчанию берутся из sys.argv.
            
        Returns:
            Объект с разобранными аргументами.
        """
        
        return self.parser.parse_args(args)
    
    def convert_args_to_dict(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Преобразует объект аргументов в словарь.
        
        Args:
            args: Объект с разобранными аргументами.
            
        Returns:
            Словарь с аргументами.
        """
        
        return vars(args)
    
    def parse_and_run(self, main_func) -> None:
        """
        Разбирает аргументы и запускает главную функцию.
        
        Args:
            main_func: Асинхронная функция для запуска.
        """
        
        try:
            # Разбираем аргументы
            args = self.parse_args()
            
            # Выводим информацию о запуске
            logger.info("Запуск с параметрами:")
            for arg_name, arg_value in vars(args).items():
                logger.info(f"  {arg_name} = {arg_value}")
            
            # Запускаем асинхронную функцию
            asyncio.run(main_func(args))
            
        except KeyboardInterrupt:
            logger.info("Операция прервана пользователем")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Точка входа для запуска как самостоятельного модуля."""
    cli = CLI()
    args = cli.parse_args()
    print("Аргументы:", vars(args))
    print("Для запуска используйте: python -m src.main")


if __name__ == "__main__":
    main()
