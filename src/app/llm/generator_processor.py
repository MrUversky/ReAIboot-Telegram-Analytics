"""
Процессор генерации сценариев.
Использует GPT-4o для создания детальных сценариев Reels.
"""

import time
import logging
from typing import Dict, Any, Optional, List

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from .base_processor import BaseLLMProcessor, ProcessingResult
from ..settings import settings
from ..utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)


class GeneratorProcessor(BaseLLMProcessor):
    """Процессор для генерации сценариев с помощью GPT-4o."""

    def __init__(self):
        """Инициализирует процессор генерации."""
        super().__init__(
            model_name="gpt-4o",
            api_key=settings.openai_api_key
        )

        if OPENAI_AVAILABLE and self.is_available:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=settings.openai_base_url
            )

    async def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """
        Генерирует сценарий для Reels на основе поста и выбранной рубрики.

        Args:
            input_data: Данные поста + выбранная рубрика/формат

        Returns:
            Сгенерированный сценарий
        """
        start_time = time.time()

        if not self.is_available:
            return ProcessingResult(
                success=False,
                error="GPT-4o недоступен (нет API ключа)",
                processing_time=time.time() - start_time
            )

        try:
            # Извлекаем данные
            post_text = input_data.get("text", "")
            rubric = input_data.get("rubric", {})
            reel_format = input_data.get("reel_format", {})
            analysis = input_data.get("analysis", {})

            if not post_text:
                return ProcessingResult(
                    success=False,
                    error="Текст поста пустой",
                    processing_time=time.time() - start_time
                )

            # Получаем system и user промпты из базы данных
            from ..prompts import prompt_manager
            system_prompt = prompt_manager.get_system_prompt("generate_scenario_system", {
                "duration": duration
            })

            user_prompt = prompt_manager.get_user_prompt("generate_scenario_system", {
                "post_text": post_text,
                "post_analysis": str(analysis),  # передаем анализ как строку
                "rubric_name": rubric.get('name', 'Не указана'),
                "format_name": reel_format.get('name', 'Не указан'),
                "duration": duration
            })

            # Выполняем запрос
            success, response, error = await self._make_request_with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
            )

            if not success:
                return ProcessingResult(
                    success=False,
                    error=f"Ошибка API: {error}",
                    processing_time=time.time() - start_time
                )

            # Парсим и валидируем ответ
            result_text = response.choices[0].message.content
            tokens_used = self._calculate_tokens(user_prompt, result_text)

            # Валидируем ответ по схеме
            schema = self.get_stage_schema("generation")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "generator_model": "gpt-4o",
                        "source_post": {
                            "text_preview": post_text[:200],
                            "rubric": rubric.get("name"),
                            "format": reel_format.get("name")
                        }
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time
                )
            else:
                logger.warning(f"Generation validation failed: {validation_error}")
                # Попытка fallback парсинга
                try:
                    import json
                    import re

                    # Очищаем от markdown оберток
                    cleaned_text = result_text.strip()
                    if cleaned_text.startswith('```json'):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.startswith('```'):
                        cleaned_text = cleaned_text[3:]
                    if cleaned_text.endswith('```'):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()

                    fallback_data = json.loads(cleaned_text)

                    return ProcessingResult(
                        success=True,
                        data={
                            **fallback_data,
                            "generator_model": "gpt-4o",
                            "source_post": {
                                "text_preview": post_text[:200],
                                "rubric": rubric.get("name"),
                                "format": reel_format.get("name")
                            },
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time
                    )

                except json.JSONDecodeError:
                    logger.warning(f"Не удалось распарсить JSON от GPT-4o: {result_text[:200]}...")

                    # Пытаемся извлечь JSON из текста
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        try:
                            fallback_data = json.loads(json_match.group())
                            return ProcessingResult(
                                success=True,
                                data={
                                    **fallback_data,
                                    "generator_model": "gpt-4o",
                                    "source_post": {
                                        "text_preview": post_text[:200],
                                        "rubric": rubric.get("name"),
                                        "format": reel_format.get("name")
                                    },
                                    "validation_warning": validation_error
                                },
                                tokens_used=tokens_used,
                                processing_time=time.time() - start_time
                            )
                        except:
                            pass

                    # Возвращаем сырой текст как fallback
                    return ProcessingResult(
                        success=True,
                        data={
                            "raw_scenario": result_text,
                            "generator_model": "gpt-4o",
                            "parsing_error": "JSON parsing failed",
                            "validation_error": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time
                    )

        except Exception as e:
            logger.error(f"Ошибка в GeneratorProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time
            )
