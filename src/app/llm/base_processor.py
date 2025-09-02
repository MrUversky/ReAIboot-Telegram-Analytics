"""
Базовый класс для LLM процессоров.
Содержит общую логику для работы с различными моделями.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..settings import settings
from ..utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)


@dataclass
class ProcessingResult:
    """Результат обработки поста."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tokens_used: int = 0
    processing_time: float = 0.0


class BaseLLMProcessor(ABC):
    """Базовый класс для всех LLM процессоров."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Инициализирует процессор.

        Args:
            model_name: Название модели
            api_key: API ключ (если не передан, берется из настроек)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.is_available = bool(self.api_key)

        if not self.is_available:
            logger.warning(f"API ключ для {model_name} не найден. Процессор недоступен.")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """
        Обрабатывает входные данные.

        Args:
            input_data: Входные данные для обработки

        Returns:
            Результат обработки
        """
        pass

    def is_processor_available(self) -> bool:
        """Проверяет доступность процессора."""
        return self.is_available

    async def _make_request_with_retry(
        self,
        request_func,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Tuple[bool, Any, str]:
        """
        Выполняет запрос с повторными попытками.

        Args:
            request_func: Функция для выполнения запроса
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками

        Returns:
            Кортеж (успех, результат, ошибка)
        """
        for attempt in range(max_retries):
            try:
                result = await request_func()
                return True, result, ""
            except Exception as e:
                error_msg = f"Попытка {attempt + 1}/{max_retries} failed: {str(e)}"
                logger.warning(error_msg)

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Экспоненциальная задержка

        return False, None, f"Все {max_retries} попыток исчерпаны"

    def _calculate_tokens(self, input_text: str, output_text: str = "") -> int:
        """
        Примерная оценка количества токенов.
        В реальном проекте лучше использовать tiktoken.

        Args:
            input_text: Входной текст
            output_text: Выходной текст

        Returns:
            Примерное количество токенов
        """
        # Примерная оценка: 1 токен ≈ 4 символа для английского текста
        # Для русского текста коэффициент может быть выше
        total_chars = len(input_text) + len(output_text)
        estimated_tokens = total_chars // 3  # Консервативная оценка
        return estimated_tokens
