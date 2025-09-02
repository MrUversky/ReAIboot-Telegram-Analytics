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

            # Формируем промпт для генерации сценария
            system_prompt = f"""Ты - креативный директор по контенту для TikTok/Reels/YouTube Shorts.
Твоя задача: создать детальный сценарий короткого видео на основе успешного поста.

КОНТЕКСТ ПРОЕКТА "ПерепрошИИвка":
- Образовательный контент о технологиях, бизнесе, саморазвитии
- Формат: вертикальные видео 15-60 секунд
- Стиль: профессиональный, но доступный
- Цель: давать реальную пользу зрителям

РУБРИКА: {rubric.get('name', 'Не указана')}
ФОРМАТ: {reel_format.get('name', 'Не указан')}

Создай сценарий с:
1. Хук (цепляющее начало)
2. Основная идея (ключевой инсайт)
3. Структура видео (шаги/сцены)
4. Текст для озвучки
5. Визуальные элементы
6. Призыв к действию

Учитывай анализ успеха поста: {analysis.get('success_factors', [])}"""

            user_prompt = f"""Создай сценарий Reels на основе этого поста:

ПОСТ:
{post_text[:2000]}

АНАЛИЗ УСПЕХА:
{analysis.get('lessons_learned', 'Анализ не доступен')}

КЛЮЧЕВЫЕ ФАКТОРЫ УСПЕХА:
{', '.join(analysis.get('success_factors', ['Не определены']))}

СОЗДАЙ СЦЕНАРИЙ ДЛЯ:
- Рубрика: {rubric.get('name', 'Общая')}
- Формат: {reel_format.get('name', 'Общий')}
- Длительность: {reel_format.get('duration_options', [30])[0]} секунд

СТРУКТУРА СЦЕНАРИЯ:
1. Hook (3-5 секунд)
2. Problem/Insight (5-10 секунд)
3. Solution/Steps (10-15 секунд)
4. CTA (3-5 секунд)

ВЕРНИ В ФОРМАТЕ JSON:
{{
  "title": "Название видео",
  "duration": 30,
  "hook": {{
    "text": "Текст хука",
    "visual": "Описание визуала",
    "voiceover": "Текст для озвучки"
  }},
  "insight": {{
    "text": "Ключевой инсайт",
    "visual": "Визуальное оформление",
    "voiceover": "Текст для озвучки"
  }},
  "steps": [
    {{
      "step": 1,
      "title": "Название шага",
      "description": "Описание",
      "visual": "Визуальные элементы",
      "voiceover": "Текст для озвучки",
      "duration": 5
    }}
  ],
  "cta": {{
    "text": "Призыв к действию",
    "visual": "Визуальное оформление",
    "voiceover": "Текст для озвучки"
  }},
  "hashtags": ["#тег1", "#тег2"],
  "music_suggestion": "Рекомендация музыки"
}}"""

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

            # Парсим ответ
            result_text = response.choices[0].message.content
            tokens_used = self._calculate_tokens(user_prompt, result_text)

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

                scenario_data = json.loads(cleaned_text)

                return ProcessingResult(
                    success=True,
                    data={
                        **scenario_data,
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

            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON от GPT-4o: {result_text[:200]}... Error: {e}")

                # Пытаемся извлечь JSON из текста
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        scenario_data = json.loads(json_match.group())
                        return ProcessingResult(
                            success=True,
                            data={
                                **scenario_data,
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
                    except:
                        pass

                # Возвращаем сырой текст как fallback
                return ProcessingResult(
                    success=True,
                    data={
                        "raw_scenario": result_text,
                        "generator_model": "gpt-4o",
                        "parsing_error": "JSON parsing failed"
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
