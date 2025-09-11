"""
Процессор анализа постов.
Использует Claude для глубокого анализа причин успеха поста.
"""

import time
import logging
from typing import Dict, Any, Optional

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

from .base_processor import BaseLLMProcessor, ProcessingResult
from ..settings import settings
from ..utils import setup_logger
from ..prompts import prompt_manager

# Настройка логирования
logger = setup_logger(__name__)


class AnalysisProcessor(BaseLLMProcessor):
    """Процессор для анализа постов с помощью Claude."""

    def __init__(self):
        """Инициализирует процессор анализа."""
        # Импортируем prompt_manager
        from ..prompts import prompt_manager
        self.prompt_manager = prompt_manager

        # Получаем модель из настроек промпта
        model_settings = self.prompt_manager.get_model_settings("analyze_success")
        model_name = model_settings.get('model', settings.analysis_model)

        super().__init__(
            model_name=model_name,
            api_key=settings.anthropic_api_key
        )

        if ANTHROPIC_AVAILABLE and self.is_available:
            self.client = AsyncAnthropic(api_key=self.api_key)

    async def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """
        Анализирует причины успеха поста.

        Args:
            input_data: Данные поста с метриками

        Returns:
            Результат анализа
        """
        start_time = time.time()

        if not self.is_available:
            return ProcessingResult(
                success=False,
                error="Claude недоступен (нет API ключа)",
                processing_time=time.time() - start_time
            )

        try:
            # Извлекаем данные поста
            post_text = input_data.get("text", "")
            views = input_data.get("views", 0)
            reactions = input_data.get("reactions", 0)
            replies = input_data.get("replies", 0)
            forwards = input_data.get("forwards", 0)
            channel_title = input_data.get("channel_title", "")
            score = input_data.get("score", 0)

            if not post_text:
                return ProcessingResult(
                    success=False,
                    error="Текст поста пустой",
                    processing_time=time.time() - start_time
                )

            # Получаем system и user промпты из базы данных
            system_prompt = self.prompt_manager.get_system_prompt("analyze_success", {
                "score": score
            })

            user_prompt = self.prompt_manager.get_user_prompt("analyze_success", {
                "post_text": post_text,
                "views": views,
                "likes": reactions,  # используем reactions как likes
                "forwards": forwards,
                "replies": replies,
                "channel_title": channel_title,
                "score": score
            })

            # Debug: логируем промпты
            logger.debug(f"🧪 ANALYSIS PROMPT - System: {system_prompt}")
            logger.debug(f"🧪 ANALYSIS PROMPT - User: {user_prompt}")
            logger.debug(f"🧪 ANALYSIS INPUT DATA: post_text={post_text[:100]}..., views={views}, reactions={reactions}, score={score}")

            # Выполняем запрос к Claude
            success, response, error = await self._make_request_with_retry(
                lambda: self.client.messages.create(
                    model=self.model_name,
                    max_tokens=2000,
                    temperature=0.4,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                ),
                timeout=45.0  # Таймаут 45 секунд для анализа
            )

            if not success:
                return ProcessingResult(
                    success=False,
                    error=f"Ошибка Claude API: {error}",
                    processing_time=time.time() - start_time
                )

            # Парсим и валидируем ответ
            result_text = response.content[0].text
            tokens_used = self._calculate_tokens(user_prompt, result_text)

            # Debug: логируем сырой ответ от LLM
            logger.debug(f"🧪 ANALYSIS RAW RESPONSE: {result_text}")
            logger.debug(f"🧪 ANALYSIS RESPONSE LENGTH: {len(result_text)} chars")
            logger.debug(f"🧪 ANALYSIS TOKENS USED: {tokens_used}")

            # Валидируем ответ по схеме
            schema = self.get_stage_schema("analysis")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "analysis_model": "claude-3-5-sonnet"
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time,
                    raw_response=result_text
                )
            else:
                logger.warning(f"Analysis validation failed: {validation_error}")
                # Попытка fallback парсинга
                try:
                    import json
                    fallback_data = json.loads(result_text)

                    return ProcessingResult(
                        success=True,
                        data={
                            **fallback_data,
                            "analysis_model": "claude-3-5-sonnet",
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Не удалось распарсить JSON от Claude: {result_text}")

                    # Возвращаем сырой текст как fallback
                    return ProcessingResult(
                        success=True,
                        data={
                            "raw_analysis": result_text,
                            "analysis_model": "claude-3-5-sonnet",
                            "parsing_error": "JSON parsing failed",
                            "validation_error": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )

        except Exception as e:
            logger.error(f"Ошибка в AnalysisProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time,
                raw_response=None
            )
