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

# Настройка логирования
logger = setup_logger(__name__)


class AnalysisProcessor(BaseLLMProcessor):
    """Процессор для анализа постов с помощью Claude."""

    def __init__(self):
        """Инициализирует процессор анализа."""
        super().__init__(
            model_name="claude-3-5-sonnet-20241022",
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

            # Формируем промпт для анализа
            system_prompt = """Ты - опытный аналитик контента для социальных сетей.
Твоя задача: глубоко проанализировать почему пост стал популярным и какие уроки можно извлечь.

Проанализируй:
1. Содержательные факторы (тема, качество текста, полезность)
2. Презентационные факторы (структура, язык, формат)
3. Психологические факторы (эмоциональный отклик, актуальность)
4. Технические факторы (время публикации, оформление)

Верни детальный анализ в формате JSON."""

            user_prompt = f"""Проанализируй этот успешный пост (score: {score}/10):

КАНАЛ: {channel_title}
ПОСТ:
{post_text[:3000]}

МЕТРИКИ ВОВЛЕЧЕННОСТИ:
- Просмотры: {views:,}
- Реакции: {reactions:,}
- Комментарии: {replies:,}
- Репосты: {forwards:,}

ПРОАНАЛИЗИРУЙ:
1. Почему этот пост стал популярным?
2. Какие ключевые факторы успеха?
3. Что можно взять для создания собственного контента?
4. Какие уроки для будущих постов?

Верни анализ в JSON формате:
{{
  "success_factors": ["фактор1", "фактор2", ...],
  "content_strengths": ["сильная сторона1", "сильная сторона2", ...],
  "audience_insights": ["инсайт1", "инсайт2", ...],
  "content_ideas": ["идея1", "идея2", ...],
  "lessons_learned": "выводы для нашего контента",
  "recommended_topics": ["тема1", "тема2", ...]
}}"""

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
                )
            )

            if not success:
                return ProcessingResult(
                    success=False,
                    error=f"Ошибка Claude API: {error}",
                    processing_time=time.time() - start_time
                )

            # Парсим ответ
            result_text = response.content[0].text
            tokens_used = self._calculate_tokens(user_prompt, result_text)

            try:
                import json
                result_json = json.loads(result_text)

                return ProcessingResult(
                    success=True,
                    data={
                        **result_json,
                        "analysis_model": "claude-3-5-sonnet"
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time
                )

            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить JSON от Claude: {result_text}")

                # Возвращаем сырой текст как fallback
                return ProcessingResult(
                    success=True,
                    data={
                        "raw_analysis": result_text,
                        "analysis_model": "claude-3-5-sonnet",
                        "parsing_error": "JSON parsing failed"
                    },
                    tokens_used=tokens_used,
                    processing_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"Ошибка в AnalysisProcessor: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Внутренняя ошибка: {str(e)}",
                processing_time=time.time() - start_time
            )
