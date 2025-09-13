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
from ..prompts import prompt_manager

# Настройка логирования
logger = setup_logger(__name__)


class GeneratorProcessor(BaseLLMProcessor):
    """Процессор для генерации сценариев с помощью GPT-4o."""

    def __init__(self):
        """Инициализирует процессор генерации."""
        # Импортируем prompt_manager
        from ..prompts import prompt_manager
        self.prompt_manager = prompt_manager

        # Получаем модель из настроек промпта
        model_settings = self.prompt_manager.get_model_settings("generate_scenario_system")
        model_name = model_settings.get('model', settings.generator_model)

        super().__init__(
            model_name=model_name,
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
            # Извлекаем данные - проверяем разные поля для текста поста
            post_text = input_data.get("text", "") or input_data.get("full_text", "") or input_data.get("post_text", "")
            rubric = input_data.get("rubric", {})
            reel_format = input_data.get("reel_format", {})
            analysis = input_data.get("analysis", {})

            # Логируем входные данные для отладки
            logger.info(f"GeneratorProcessor input_data keys: {list(input_data.keys())}")
            logger.info(f"Post text length: {len(post_text)}")
            logger.info(f"Post text preview: {post_text[:200] if post_text else 'EMPTY'}")
            logger.info(f"Rubric: {rubric}")
            logger.info(f"Reel format: {reel_format}")

            if not post_text:
                return ProcessingResult(
                    success=False,
                    error="Текст поста пустой",
                    processing_time=time.time() - start_time
                )

            # Получаем system и user промпты из базы данных

            # Определяем длительность по формату или используем дефолт
            # Проверяем оба возможных названия поля: duration_seconds и duration
            duration = reel_format.get('duration_seconds') or reel_format.get('duration')
            if duration is None:
                duration = 60  # Default to 60 seconds if not found

            system_prompt = self.prompt_manager.get_system_prompt("generate_scenario_system", {
                "duration": duration
            })

            # Используем все новые переменные, которые передаются из orchestrator
            user_prompt = self.prompt_manager.get_user_prompt("generate_scenario_system", {
                "post_text": post_text,
                "post_analysis": input_data.get("post_analysis", str(analysis)),
                "rubric_selection_analysis": input_data.get("rubric_selection_analysis", ""),
                "rubric_name": rubric.get('name', 'Не указана'),
                "rubric_description": input_data.get("rubric_description", ""),
                "rubric_examples": input_data.get("rubric_examples", ""),
                "format_name": reel_format.get('name', 'Не указан'),
                "format_description": input_data.get("format_description", ""),
                "format_duration": input_data.get("format_duration", str(duration)),
                "combination_justification": input_data.get("combination_justification", ""),
                "combination_content_idea": input_data.get("combination_content_idea", ""),
                "duration": duration
            })

            # Debug: логируем промпты
            print(f"🧪 GENERATOR PROMPT - System: {system_prompt}")
            print(f"🧪 GENERATOR PROMPT - User: {user_prompt}")
            print(f"🧪 GENERATOR INPUT DATA: post_text={post_text[:100]}..., rubric={rubric.get('name')}, format={reel_format.get('name')}, duration={duration}")

            # Debug: логируем ключевые переменные из input_data
            print(f"🧪 GENERATOR DEBUG - rubric_description: '{input_data.get('rubric_description', 'NOT_FOUND')}'")
            print(f"🧪 GENERATOR DEBUG - rubric_examples: '{input_data.get('rubric_examples', 'NOT_FOUND')}'")
            print(f"🧪 GENERATOR DEBUG - format_description: '{input_data.get('format_description', 'NOT_FOUND')}'")
            print(f"🧪 GENERATOR DEBUG - format_duration: '{input_data.get('format_duration', 'NOT_FOUND')}'")
            print(f"🧪 GENERATOR DEBUG - combination_justification: '{input_data.get('combination_justification', 'NOT_FOUND')[:100]}...'")
            print(f"🧪 GENERATOR DEBUG - combination_content_idea: '{input_data.get('combination_content_idea', 'NOT_FOUND')[:100]}...'")

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
                ),
                timeout=90.0  # Таймаут 90 секунд для генерации (самый долгий этап)
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

            # Debug: логируем сырой ответ от LLM
            logger.debug(f"🧪 GENERATOR RAW RESPONSE: {result_text}")
            logger.debug(f"🧪 GENERATOR RESPONSE LENGTH: {len(result_text)} chars")
            logger.debug(f"🧪 GENERATOR TOKENS USED: {tokens_used}")

            # Валидируем ответ по схеме
            schema = self.get_stage_schema("generation")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "generator_model": self.model_name,
                        "source_post": {
                            "text_preview": post_text[:200],
                            "rubric": rubric.get("name"),
                            "format": reel_format.get("name")
                        }
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time,
                    raw_response=result_text
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
                            "generator_model": self.model_name,
                            "source_post": {
                                "text_preview": post_text[:200],
                                "rubric": rubric.get("name"),
                                "format": reel_format.get("name")
                            },
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
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
                                    "generator_model": self.model_name,
                                    "source_post": {
                                        "text_preview": post_text[:200],
                                        "rubric": rubric.get("name"),
                                        "format": reel_format.get("name")
                                    },
                                    "validation_warning": validation_error
                                },
                                tokens_used=tokens_used,
                                processing_time=time.time() - start_time,
                                raw_response=result_text
                            )
                        except:
                            pass

                    # Возвращаем сырой текст как fallback
                    return ProcessingResult(
                        success=True,
                        data={
                            "raw_scenario": result_text,
                            "generator_model": self.model_name,
                            "parsing_error": "JSON parsing failed",
                            "validation_error": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )

        except Exception as e:
            logger.error(f"Ошибка в GeneratorProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time,
                raw_response=None
            )
