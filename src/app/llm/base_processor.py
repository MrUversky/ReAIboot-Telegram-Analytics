"""
Базовый класс для LLM процессоров.
Содержит общую логику для работы с различными моделями.
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import jsonschema
from jsonschema import validate, ValidationError

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

    def validate_json_response(self, response_text: str, schema: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Валидирует JSON ответ по схеме.

        Args:
            response_text: Текст ответа для валидации
            schema: JSON схема для валидации

        Returns:
            Кортеж (успех, данные, ошибка)
        """
        try:
            # Очищаем от markdown оберток
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            # Парсим JSON
            data = json.loads(cleaned_text)

            # Валидируем по схеме
            validate(instance=data, schema=schema)

            return True, data, ""

        except json.JSONDecodeError as e:
            error_msg = f"Некорректный JSON: {str(e)}"
            logger.warning(f"JSON validation failed: {error_msg}")
            return False, None, error_msg

        except ValidationError as e:
            error_msg = f"Схема валидации не пройдена: {e.message}"
            logger.warning(f"Schema validation failed: {error_msg}")
            return False, None, error_msg

        except Exception as e:
            error_msg = f"Ошибка валидации: {str(e)}"
            logger.error(f"Validation error: {error_msg}", exc_info=True)
            return False, None, error_msg

    def get_default_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает стандартные схемы валидации для каждого этапа пайплайна.

        Returns:
            Словарь с схемами для каждого этапа
        """
        return {
            "filter": {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "minimum": 1, "maximum": 10},
                    "reason": {"type": "string"},
                    "suitable": {"type": "boolean"}
                },
                "required": ["score", "reason", "suitable"]
            },
            "analysis": {
                "type": "object",
                "properties": {
                    "success_factors": {"type": "array", "items": {"type": "string"}},
                    "content_strengths": {"type": "array", "items": {"type": "string"}},
                    "audience_insights": {"type": "array", "items": {"type": "string"}},
                    "content_ideas": {"type": "array", "items": {"type": "string"}},
                    "lessons_learned": {"type": "string"},
                    "recommended_topics": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["success_factors", "content_strengths", "audience_insights"]
            },
            "generation": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "duration": {"type": "number"},
                    "hook": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "visual": {"type": "string"},
                            "voiceover": {"type": "string"}
                        }
                    },
                    "insight": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "visual": {"type": "string"},
                            "voiceover": {"type": "string"}
                        }
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step": {"type": "number"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "visual": {"type": "string"},
                                "voiceover": {"type": "string"},
                                "duration": {"type": "number"}
                            }
                        }
                    },
                    "cta": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "visual": {"type": "string"},
                            "voiceover": {"type": "string"}
                        }
                    },
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "music_suggestion": {"type": "string"}
                },
                "required": ["title", "duration", "hook", "insight", "steps", "cta"]
            }
        }

    def get_stage_schema(self, stage_name: str) -> Dict[str, Any]:
        """
        Возвращает схему валидации для указанного этапа.

        Args:
            stage_name: Название этапа (filter, analysis, generation)

        Returns:
            JSON схема для валидации
        """
        schemas = self.get_default_schemas()
        return schemas.get(stage_name, {})
