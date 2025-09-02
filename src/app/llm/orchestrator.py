"""
Оркестратор LLM процессов.
Управляет 3-этапной обработкой: фильтрация → анализ → генерация.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .filter_processor import FilterProcessor
from .analysis_processor import AnalysisProcessor
from .generator_processor import GeneratorProcessor
from ..settings import settings
from ..utils import setup_logger
from ..supabase_client import supabase_client

# Настройка логирования
logger = setup_logger(__name__)


@dataclass
class ProcessingStage:
    """Результат одного этапа обработки."""
    stage_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tokens_used: int = 0
    processing_time: float = 0.0


@dataclass
class OrchestratorResult:
    """Результат полной обработки поста."""
    post_id: str
    overall_success: bool
    stages: List[ProcessingStage]
    final_data: Optional[Dict[str, Any]] = None
    total_tokens: int = 0
    total_time: float = 0.0
    error: Optional[str] = None


class LLMOrchestrator:
    """Оркестратор для управления многоэтапной обработкой постов."""

    def __init__(self):
        """Инициализирует оркестратор."""
        self.filter_processor = FilterProcessor()
        self.analysis_processor = AnalysisProcessor()
        self.generator_processor = GeneratorProcessor()

        # Проверяем доступность процессоров
        self.available_processors = {
            "filter": self.filter_processor.is_processor_available(),
            "analysis": self.analysis_processor.is_processor_available(),
            "generator": self.generator_processor.is_processor_available()
        }

        logger.info(f"Доступность процессоров: {self.available_processors}")

    async def process_post(
        self,
        post_data: Dict[str, Any],
        rubric: Optional[Dict[str, Any]] = None,
        reel_format: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResult:
        """
        Обрабатывает пост через все этапы: фильтрация → анализ → генерация.

        Args:
            post_data: Данные поста
            rubric: Выбранная рубрика (опционально)
            reel_format: Выбранный формат (опционально)

        Returns:
            Результат полной обработки
        """
        post_id = post_data.get("message_id", "unknown")
        start_time = asyncio.get_event_loop().time()
        stages = []
        total_tokens = 0

        logger.info(f"Начинаем обработку поста {post_id}")

        try:
            # Этап 1: Фильтрация
            logger.info(f"Этап 1: Фильтрация поста {post_id}")
            filter_result = await self.filter_processor.process(post_data)

            stages.append(ProcessingStage(
                stage_name="filter",
                success=filter_result.success,
                data=filter_result.data,
                error=filter_result.error,
                tokens_used=filter_result.tokens_used,
                processing_time=filter_result.processing_time
            ))

            total_tokens += filter_result.tokens_used

            # Если фильтрация не прошла или пост не подходит
            if not filter_result.success or not filter_result.data.get("suitable", False):
                reason = filter_result.data.get("reason", "Не прошел фильтрацию") if filter_result.success else filter_result.error

                return OrchestratorResult(
                    post_id=post_id,
                    overall_success=False,
                    stages=stages,
                    total_tokens=total_tokens,
                    total_time=asyncio.get_event_loop().time() - start_time,
                    error=f"Пост не прошел фильтрацию: {reason}"
                )

            # Этап 2: Анализ причин успеха
            logger.info(f"Этап 2: Анализ поста {post_id}")
            analysis_result = await self.analysis_processor.process({
                **post_data,
                "filter_score": filter_result.data.get("score", 0)
            })

            stages.append(ProcessingStage(
                stage_name="analysis",
                success=analysis_result.success,
                data=analysis_result.data,
                error=analysis_result.error,
                tokens_used=analysis_result.tokens_used,
                processing_time=analysis_result.processing_time
            ))

            total_tokens += analysis_result.tokens_used

            # Если анализ не удался, продолжаем без него
            if not analysis_result.success:
                logger.warning(f"Анализ поста {post_id} не удался: {analysis_result.error}")

            # Этап 3: Генерация сценария
            logger.info(f"Этап 3: Генерация сценария для поста {post_id}")
            generator_input = {
                **post_data,
                "analysis": analysis_result.data if analysis_result.success else {},
                "rubric": rubric or {},
                "reel_format": reel_format or {}
            }

            generator_result = await self.generator_processor.process(generator_input)

            stages.append(ProcessingStage(
                stage_name="generator",
                success=generator_result.success,
                data=generator_result.data,
                error=generator_result.error,
                tokens_used=generator_result.tokens_used,
                processing_time=generator_result.processing_time
            ))

            total_tokens += generator_result.tokens_used

            # Формируем финальный результат
            final_data = None
            if generator_result.success and generator_result.data:
                final_data = {
                    "filter": filter_result.data,
                    "analysis": analysis_result.data if analysis_result.success else None,
                    "scenario": generator_result.data,
                    "processing_stats": {
                        "total_tokens": total_tokens,
                        "total_time": asyncio.get_event_loop().time() - start_time,
                        "stages_completed": len([s for s in stages if s.success])
                    }
                }

            return OrchestratorResult(
                post_id=post_id,
                overall_success=generator_result.success,
                stages=stages,
                final_data=final_data,
                total_tokens=total_tokens,
                total_time=asyncio.get_event_loop().time() - start_time
            )

        except Exception as e:
            logger.error(f"Критическая ошибка в оркестраторе для поста {post_id}: {e}", exc_info=True)

            return OrchestratorResult(
                post_id=post_id,
                overall_success=False,
                stages=stages,
                total_tokens=total_tokens,
                total_time=asyncio.get_event_loop().time() - start_time,
                error=f"Критическая ошибка: {str(e)}"
            )

    async def process_posts_batch(
        self,
        posts: List[Dict[str, Any]],
        rubric: Optional[Dict[str, Any]] = None,
        reel_format: Optional[Dict[str, Any]] = None,
        concurrency: int = 3
    ) -> List[OrchestratorResult]:
        """
        Обрабатывает несколько постов параллельно.

        Args:
            posts: Список постов для обработки
            rubric: Рубрика для всех постов
            reel_format: Формат для всех постов
            concurrency: Максимальное количество одновременных обработок

        Returns:
            Список результатов обработки
        """
        logger.info(f"Начинаем пакетную обработку {len(posts)} постов (concurrency: {concurrency})")

        # Создаем семафор для ограничения concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(post_data):
            async with semaphore:
                return await self.process_post(post_data, rubric, reel_format)

        # Обрабатываем все посты параллельно
        tasks = [process_with_semaphore(post) for post in posts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем исключения
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Исключение при обработке поста {i}: {result}")
                final_results.append(OrchestratorResult(
                    post_id=f"post_{i}",
                    overall_success=False,
                    stages=[],
                    error=f"Exception: {str(result)}"
                ))
            else:
                final_results.append(result)

        # Сохраняем результаты в базу данных
        if supabase_client.is_connected():
            await self._save_results_to_database(final_results, posts)

        logger.info(f"Завершена пакетная обработка: {len(final_results)} результатов")
        return final_results

    async def _save_results_to_database(self, results: List[OrchestratorResult], original_posts: List[Dict[str, Any]]):
        """Сохраняет результаты обработки в базу данных."""
        try:
            logger.info(f"Сохранение {len(results)} результатов в базу данных")

            # Создаем словарь для быстрого поиска оригинальных данных поста
            posts_dict = {f"{post['message_id']}_{post['channel_username']}": post for post in original_posts}

            saved_analyses = 0
            saved_scenarios = 0

            for result in results:
                if not result.overall_success:
                    continue

                post_data = posts_dict.get(result.post_id)
                if not post_data:
                    logger.warning(f"Не найдены оригинальные данные для поста {result.post_id}")
                    continue

                # Сохраняем результаты анализа
                for stage in result.stages:
                    if stage.success and stage.data:
                        analysis_data = {
                            'post_id': result.post_id,
                            'analysis_type': stage.stage_name,
                            'status': 'completed',
                            'tokens_used': stage.tokens_used,
                            'processing_time_seconds': stage.processing_time,
                            'created_at': self._get_current_timestamp(),
                            'updated_at': self._get_current_timestamp()
                        }

                        # Добавляем специфичные данные для каждого этапа
                        if stage.stage_name == 'filter':
                            analysis_data.update({
                                'is_suitable': stage.data.get('suitable', False),
                                'suitability_score': stage.data.get('score', 0),
                                'filter_reason': stage.data.get('reason', '')
                            })
                        elif stage.stage_name == 'analysis':
                            analysis_data.update({
                                'success_factors': stage.data.get('success_factors', {}),
                                'audience_insights': stage.data.get('audience_insights', {}),
                                'content_quality_score': stage.data.get('quality_score', 0)
                            })
                        elif stage.stage_name == 'generator':
                            analysis_data.update({
                                'generated_scenarios': stage.data.get('scenarios', []),
                                'selected_rubric_id': stage.data.get('selected_rubric'),
                                'selected_format_id': stage.data.get('selected_format')
                            })

                        # Сохраняем использование токенов
                        if stage.tokens_used > 0:
                            token_data = {
                                'model': self._get_model_for_stage(stage.stage_name),
                                'tokens_used': stage.tokens_used,
                                'cost_usd': self._calculate_cost(stage.stage_name, stage.tokens_used),
                                'operation_type': stage.stage_name,
                                'post_id': result.post_id,
                                'created_at': self._get_current_timestamp()
                            }
                            supabase_client.save_token_usage(token_data)

                        # Сохраняем анализ
                        if supabase_client.save_post_analysis(analysis_data):
                            saved_analyses += 1

                # Сохраняем сценарии
                if result.final_data and result.final_data.get('scenarios'):
                    scenarios_data = []
                    for scenario in result.final_data['scenarios']:
                        scenario_data = {
                            'post_id': result.post_id,
                            'title': scenario.get('title', 'Без названия'),
                            'description': scenario.get('description', ''),
                            'duration_seconds': scenario.get('duration', 60),
                            'hook': scenario.get('hook', {}),
                            'insight': scenario.get('insight', {}),
                            'content': scenario.get('content', {}),
                            'call_to_action': scenario.get('call_to_action', {}),
                            'rubric_id': scenario.get('rubric_id'),
                            'format_id': scenario.get('format_id'),
                            'quality_score': scenario.get('quality_score', 0),
                            'engagement_prediction': scenario.get('engagement_prediction', 0),
                            'status': 'draft',
                            'full_scenario': scenario,
                            'created_at': self._get_current_timestamp(),
                            'updated_at': self._get_current_timestamp()
                        }
                        scenarios_data.append(scenario_data)

                    if supabase_client.save_scenarios(scenarios_data):
                        saved_scenarios += len(scenarios_data)

            logger.info(f"Сохранено в БД: {saved_analyses} анализов, {saved_scenarios} сценариев")

        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов в БД: {e}", exc_info=True)

    def _get_current_timestamp(self) -> str:
        """Возвращает текущую timestamp в формате ISO."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def _get_model_for_stage(self, stage_name: str) -> str:
        """Возвращает модель для указанного этапа."""
        model_mapping = {
            'filter': 'gpt-4o-mini',
            'analysis': 'claude-3-5-sonnet-20241022',
            'generator': 'gpt-4o'
        }
        return model_mapping.get(stage_name, 'unknown')

    def _calculate_cost(self, stage_name: str, tokens: int) -> float:
        """Рассчитывает стоимость использования токенов."""
        # Примерные цены (нужно обновлять актуальные)
        prices_per_1k_tokens = {
            'filter': 0.15,  # GPT-4o-mini
            'analysis': 3.0,  # Claude-3.5-Sonnet
            'generator': 2.5  # GPT-4o
        }

        price = prices_per_1k_tokens.get(stage_name, 0)
        return round((tokens / 1000) * price, 4)

    def get_processor_status(self) -> Dict[str, bool]:
        """Возвращает статус доступности всех процессоров."""
        return self.available_processors.copy()
