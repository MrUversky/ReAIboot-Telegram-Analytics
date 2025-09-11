"""
Процессор выбора рубрик и форматов.
Выбирает наиболее подходящие комбинации рубрик и форматов для поста.
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


class RubricSelectorProcessor(BaseLLMProcessor):
    """Процессор для выбора подходящих рубрик и форматов."""

    def __init__(self):
        """Инициализирует процессор выбора рубрик."""
        # Импортируем prompt_manager
        from ..prompts import prompt_manager
        self.prompt_manager = prompt_manager

        # Получаем модель из настроек промпта
        model_settings = self.prompt_manager.get_model_settings("rubric_selector_system")
        model_name = model_settings.get('model', settings.rubric_model)

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
        Выбирает подходящие рубрики и форматы для поста.

        Args:
            input_data: Данные поста с анализом и доступными рубриками/форматами

        Returns:
            Результат выбора с топ комбинациями
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
            analysis = input_data.get("analysis", {})
            available_rubrics = input_data.get("available_rubrics", [])
            available_formats = input_data.get("available_formats", [])

            if not post_text:
                return ProcessingResult(
                    success=False,
                    error="Текст поста пустой",
                    processing_time=time.time() - start_time
                )

            # Получаем system и user промпты из базы данных
            system_prompt = self.prompt_manager.get_system_prompt("rubric_selector_system", {})

            user_prompt = self.prompt_manager.get_user_prompt("rubric_selector_system", {
                "post_text": post_text[:2000],
                "analysis": str(analysis),
                "views": input_data.get("views", 0),
                "reactions": input_data.get("reactions", 0),
                "replies": input_data.get("replies", 0),
                "forwards": input_data.get("forwards", 0),
                "available_rubrics": str(available_rubrics),
                "available_formats": str(available_formats)
            })

            # Debug: логируем промпты
            logger.debug(f"🧪 RUBRIC PROMPT - System: {system_prompt}")
            logger.debug(f"🧪 RUBRIC PROMPT - User: {user_prompt}")
            logger.debug(f"🧪 RUBRIC INPUT DATA: post_text={post_text[:100]}..., analysis_keys={list(analysis.keys())}, rubrics_count={len(available_rubrics)}")

            # Выполняем запрос
            success, response, error = await self._make_request_with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
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

            # Debug: логируем сырой ответ от LLM
            logger.debug(f"🧪 RUBRIC RAW RESPONSE: {result_text}")
            logger.debug(f"🧪 RUBRIC RESPONSE LENGTH: {len(result_text)} chars")
            logger.debug(f"🧪 RUBRIC TOKENS USED: {tokens_used}")

            # Валидируем ответ по схеме
            schema = self.get_stage_schema("rubric_selection")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "rubric_selector_model": self.model_name
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time,
                    raw_response=result_text
                )
            else:
                logger.warning(f"Rubric selection validation failed: {validation_error}")
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
                            "rubric_selector_model": self.model_name,
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )

                except json.JSONDecodeError:
                    logger.warning(f"Не удалось распарсить JSON от GPT-4o: {result_text[:200]}...")

                    return ProcessingResult(
                        success=True,
                        data={
                            "raw_response": result_text,
                            "rubric_selector_model": self.model_name,
                            "parsing_error": "JSON parsing failed",
                            "validation_error": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )

        except Exception as e:
            logger.error(f"Ошибка в RubricSelectorProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time,
                raw_response=None
            )
