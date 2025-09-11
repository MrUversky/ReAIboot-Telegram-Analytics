"""
Процессор фильтрации постов.
Использует GPT-4o-mini для быстрой оценки пригодности поста.
"""

import time
import logging
from typing import Dict, Any, Optional

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


class FilterProcessor(BaseLLMProcessor):
    """Процессор для фильтрации постов с помощью GPT-4o-mini."""

    def __init__(self):
        """Инициализирует процессор фильтрации."""
        # Импортируем prompt_manager
        from ..prompts import prompt_manager
        self.prompt_manager = prompt_manager

        # Получаем модель из настроек промпта
        model_settings = self.prompt_manager.get_model_settings("filter_posts_system")
        model_name = model_settings.get('model', settings.filter_model)

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
        Фильтрует пост на пригодность для ПерепрошИИвка.

        Args:
            input_data: Данные поста

        Returns:
            Результат фильтрации
        """
        start_time = time.time()

        if not self.is_available:
            return ProcessingResult(
                success=False,
                error="GPT-4o-mini недоступен (нет API ключа)",
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

            if not post_text:
                return ProcessingResult(
                    success=False,
                    error="Текст поста пустой",
                    processing_time=time.time() - start_time
                )

            # Получаем system и user промпты из базы данных
            system_prompt = self.prompt_manager.get_system_prompt("filter_posts_system", {
                "views": views,
                "reactions": reactions,
                "replies": replies,
                "forwards": forwards
            })

            user_prompt = self.prompt_manager.get_user_prompt("filter_posts_system", {
                "post_text": post_text[:2000],
                "views": views,
                "reactions": reactions,
                "replies": replies,
                "forwards": forwards,
                "channel_title": channel_title
            })

            # Debug: логируем промпты
            logger.debug(f"🧪 FILTER PROMPT - System: {system_prompt}")
            logger.debug(f"🧪 FILTER PROMPT - User: {user_prompt}")
            logger.debug(f"🧪 FILTER INPUT DATA: post_text={post_text[:100]}..., views={views}, reactions={reactions}, forwards={forwards}")

            # Выполняем запрос
            success, response, error = await self._make_request_with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                ),
                timeout=30.0  # Таймаут 30 секунд для быстрого фильтра
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
            logger.debug(f"🧪 FILTER RAW RESPONSE: {result_text}")
            logger.debug(f"🧪 FILTER RESPONSE LENGTH: {len(result_text)} chars")
            logger.debug(f"🧪 FILTER TOKENS USED: {tokens_used}")

            # Валидируем ответ по схеме
            schema = self.get_stage_schema("filter")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "filter_model": self.model_name
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time,
                    raw_response=result_text
                )
            else:
                logger.warning(f"Filter validation failed: {validation_error}")
                # Попытка fallback парсинга
                try:
                    import json
                    fallback_data = json.loads(result_text)
                    score = fallback_data.get("score", 0)
                    suitable = fallback_data.get("suitable", score >= 7)
                    reason = fallback_data.get("reason", "Оценка не определена")

                    return ProcessingResult(
                        success=True,
                        data={
                            "score": score,
                            "suitable": suitable,
                            "reason": reason,
                            "filter_model": self.model_name,
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )
                except json.JSONDecodeError:
                    return ProcessingResult(
                        success=False,
                        error=f"Не удалось распарсить JSON ответ: {result_text}. Ошибка валидации: {validation_error}",
                        processing_time=time.time() - start_time,
                        raw_response=result_text
                    )

        except Exception as e:
            logger.error(f"Ошибка в FilterProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time,
                raw_response=None
            )
