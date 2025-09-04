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

# Настройка логирования
logger = setup_logger(__name__)


class FilterProcessor(BaseLLMProcessor):
    """Процессор для фильтрации постов с помощью GPT-4o-mini."""

    def __init__(self):
        """Инициализирует процессор фильтрации."""
        super().__init__(
            model_name="gpt-4o-mini",
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

            # Формируем промпт для фильтрации
            system_prompt = """Ты - эксперт по анализу контента для социальных сетей.
Твоя задача: оценить, подходит ли пост из Telegram для создания контента проекта "ПерепрошИИвка".

Проект "ПерепрошИИвка" создает образовательный контент о технологиях, бизнесе и саморазвитии.
Мы делаем видео-ролики о: основах технологий, практике применения, инструментах, трендах, кейсах и инсайтах.

Оцени пост по шкале 1-10:
- 1-3: Совсем не подходит (неинтересная тема, низкое качество)
- 4-6: Сомнительно (нужно доработать, но есть потенциал)
- 7-10: Подходит (хорошая тема, можно создать качественный контент)

Учитывай:
- Актуальность темы для IT/бизнеса/технологий
- Качество контента и наличие полезной информации
- Потенциал для создания образовательного видео
- Метрики вовлеченности (просмотры, реакции)

Верни только JSON: {"score": число, "reason": "краткое объяснение", "suitable": true/false}"""

            user_prompt = f"""Оцени этот пост из Telegram-канала "{channel_title}":

ПОСТ:
{post_text[:2000]}

МЕТРИКИ:
- Просмотры: {views}
- Реакции: {reactions}
- Комментарии: {replies}
- Репосты: {forwards}

Оцени по шкале 1-10 и определи, подходит ли для создания образовательного контента."""

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
            schema = self.get_stage_schema("filter")
            success, validated_data, validation_error = self.validate_json_response(result_text, schema)

            if success and validated_data:
                return ProcessingResult(
                    success=True,
                    data={
                        **validated_data,
                        "filter_model": "gpt-4o-mini"
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time
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
                            "filter_model": "gpt-4o-mini",
                            "validation_warning": validation_error
                        },
                        tokens_used=tokens_used,
                        processing_time=time.time() - start_time
                    )
                except json.JSONDecodeError:
                    return ProcessingResult(
                        success=False,
                        error=f"Не удалось распарсить JSON ответ: {result_text}. Ошибка валидации: {validation_error}",
                        processing_time=time.time() - start_time
                    )

        except Exception as e:
            logger.error(f"Ошибка в FilterProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time
            )
