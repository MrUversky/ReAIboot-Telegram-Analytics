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
from .rubric_selector_processor import RubricSelectorProcessor
from ..settings import settings
from ..price_monitor import price_monitor
from ..utils import setup_logger
from ..supabase_client import supabase_client
from ..prompts import prompt_manager

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
        self.rubric_selector = RubricSelectorProcessor()
        self.generator_processor = GeneratorProcessor()

        # Проверяем доступность процессоров
        self.available_processors = {
            "filter": self.filter_processor.is_processor_available(),
            "analysis": self.analysis_processor.is_processor_available(),
            "rubric_selection": self.rubric_selector.is_processor_available(),
            "generator": self.generator_processor.is_processor_available()
        }

        # Debug режим
        self.debug_mode = False
        self.debug_log = []
        self.current_session_id = None

        logger.info(f"Доступность процессоров: {self.available_processors}")

    def enable_debug_mode(self, session_id: Optional[str] = None):
        """Включает debug режим для детального логирования."""
        self.debug_mode = True
        self.debug_log = []
        self.current_session_id = session_id or f"debug_{int(asyncio.get_event_loop().time())}"
        logger.info(f"🧪 Debug режим включен для сессии {self.current_session_id}")

    def disable_debug_mode(self):
        """Выключает debug режим."""
        self.debug_mode = False
        logger.info(f"🧪 Debug режим выключен")

    def get_debug_log(self) -> List[Dict[str, Any]]:
        """Возвращает лог debug сессии."""
        return self.debug_log.copy()

    def _log_debug_step(self, step_name: str, step_type: str, data: Dict[str, Any]):
        """Логирует шаг в debug режиме."""
        if not self.debug_mode:
            return

        debug_entry = {
            "session_id": self.current_session_id,
            "timestamp": asyncio.get_event_loop().time(),
            "step_name": step_name,
            "step_type": step_type,
            "data": data
        }

        self.debug_log.append(debug_entry)
        logger.debug(f"🧪 Debug [{step_type}]: {step_name}")

    async def process_post_enhanced(
        self,
        post_data: Dict[str, Any],
        skip_filter: bool = False,
        skip_analysis: bool = False,
        skip_rubric_selection: bool = False
    ) -> OrchestratorResult:
        """
        4-этапная обработка поста: фильтр → анализ → выбор рубрик → генерация.

        Args:
            post_data: Данные поста
            skip_filter: Пропустить этап фильтрации
            skip_analysis: Пропустить этап анализа
            skip_rubric_selection: Пропустить этап выбора рубрик

        Returns:
            Результат полной обработки
        """
        post_id = f"{post_data.get('message_id', 'unknown')}_{post_data.get('channel_username', 'unknown')}"
        start_time = asyncio.get_event_loop().time()
        stages = []
        total_tokens = 0

        # Debug: Логируем начало обработки
        self._log_debug_step("pipeline_start", "info", {
            "post_id": post_id,
            "input_data": post_data,
            "skip_filter": skip_filter,
            "skip_analysis": skip_analysis,
            "skip_rubric_selection": skip_rubric_selection
        })

        logger.info(f"Начинаем 4-этапную обработку поста {post_id}")

        try:
            # Этап 1: Фильтрация (если не пропускается)
            filter_result = None
            if not skip_filter:
                logger.info(f"Этап 1: Фильтрация поста {post_id}")

                # Debug: Логируем промпты фильтрации
                filter_system_prompt = prompt_manager.get_system_prompt("filter_posts_system", {
                    "views": post_data.get("views", 0),
                    "reactions": post_data.get("reactions", 0),
                    "replies": post_data.get("replies", 0),
                    "forwards": post_data.get("forwards", 0)
                })
                filter_user_prompt = prompt_manager.get_user_prompt("filter_posts_system", {
                    "post_text": post_data.get("text", "")[:2000],
                    "views": post_data.get("views", 0),
                    "reactions": post_data.get("reactions", 0),
                    "replies": post_data.get("replies", 0),
                    "forwards": post_data.get("forwards", 0),
                    "channel_title": post_data.get("channel_title", "")
                })

                self._log_debug_step("filter_prompts", "prompts", {
                    "system_prompt": filter_system_prompt,
                    "user_prompt": filter_user_prompt,
                    "model": self.filter_processor.model_name
                })

                filter_result = await self.filter_processor.process(post_data)

                # Debug: Логируем результат фильтрации
                self._log_debug_step("filter_complete", "llm_response", {
                    "success": filter_result.success,
                    "result": filter_result.data,
                    "error": filter_result.error,
                    "tokens_used": filter_result.tokens_used,
                    "processing_time": filter_result.processing_time
                })

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
            else:
                logger.info(f"Пропускаем фильтрацию для поста {post_id}")
                stages.append(ProcessingStage(
                    stage_name="filter",
                    success=True,
                    data={"suitable": True, "score": 1.0, "reason": "Пропущено"},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Этап 2: Анализ причин успеха (если не пропускается)
            analysis_result = None
            if not skip_analysis:
                logger.info(f"Этап 2: Анализ поста {post_id}")
                filter_score = filter_result.data.get("score", 0) if filter_result else 0

                # Debug: Логируем промпты анализа
                analysis_system_prompt = prompt_manager.get_system_prompt("analyze_success_system", {
                    "score": filter_score
                })
                analysis_user_prompt = prompt_manager.get_user_prompt("analyze_success_system", {
                    "post_text": post_data.get("text", ""),
                    "views": post_data.get("views", 0),
                    "likes": post_data.get("reactions", 0),
                    "forwards": post_data.get("forwards", 0),
                    "replies": post_data.get("replies", 0),
                    "channel_title": post_data.get("channel_title", ""),
                    "score": filter_score
                })

                self._log_debug_step("analysis_prompts", "prompts", {
                    "system_prompt": analysis_system_prompt,
                    "user_prompt": analysis_user_prompt,
                    "model": self.analysis_processor.model_name
                })

                analysis_result = await self.analysis_processor.process({
                    **post_data,
                    "filter_score": filter_score
                })

                # Debug: Логируем результат анализа
                self._log_debug_step("analysis_complete", "llm_response", {
                    "success": analysis_result.success,
                    "result": analysis_result.data,
                    "error": analysis_result.error,
                    "tokens_used": analysis_result.tokens_used,
                    "processing_time": analysis_result.processing_time
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
            else:
                logger.info(f"Пропускаем анализ для поста {post_id}")
                stages.append(ProcessingStage(
                    stage_name="analysis",
                    success=True,
                    data={"skipped": True},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Этап 3: Выбор рубрик и форматов (если не пропускается)
            rubric_result = None
            if not skip_rubric_selection:
                logger.info(f"Этап 3: Выбор рубрик/форматов для поста {post_id}")
                analysis_data = analysis_result.data if analysis_result and analysis_result.success else {}

                # Получаем доступные рубрики и форматы
                available_rubrics = await self._get_available_rubrics()
                available_formats = await self._get_available_formats()

                rubric_selection_data = {
                    **post_data,
                    "analysis": analysis_data,
                    "available_rubrics": available_rubrics,
                    "available_formats": available_formats
                }

                # Debug: Логируем промпты рубрикации
                rubric_system_prompt = prompt_manager.get_system_prompt("rubric_selector_system", {})
                rubric_user_prompt = prompt_manager.get_user_prompt("rubric_selector_system", {
                    "post_text": post_data.get("text", "")[:2000],
                    "analysis": str(analysis_data),
                    "views": post_data.get("views", 0),
                    "reactions": post_data.get("reactions", 0),
                    "replies": post_data.get("replies", 0),
                    "forwards": post_data.get("forwards", 0),
                    "available_rubrics": str(available_rubrics),
                    "available_formats": str(available_formats)
                })

                self._log_debug_step("rubric_selection_prompts", "prompts", {
                    "system_prompt": rubric_system_prompt,
                    "user_prompt": rubric_user_prompt,
                    "model": self.rubric_selector.model_name
                })

                rubric_result = await self.rubric_selector.process(rubric_selection_data)

                # Debug: Логируем результат рубрикации
                self._log_debug_step("rubric_selection_complete", "llm_response", {
                    "success": rubric_result.success,
                    "result": rubric_result.data,
                    "error": rubric_result.error,
                    "tokens_used": rubric_result.tokens_used,
                    "processing_time": rubric_result.processing_time
                })

                stages.append(ProcessingStage(
                    stage_name="rubric_selection",
                    success=rubric_result.success,
                    data=rubric_result.data,
                    error=rubric_result.error,
                    tokens_used=rubric_result.tokens_used,
                    processing_time=rubric_result.processing_time
                ))

                total_tokens += rubric_result.tokens_used

                # Если выбор рубрик не удался, используем дефолтные
                if not rubric_result.success:
                    logger.warning(f"Выбор рубрик для поста {post_id} не удался: {rubric_result.error}")
                    # Debug: Логируем ошибку
                    self._log_debug_step("rubric_selection_error", "error", {
                        "error": rubric_result.error,
                        "stage": "rubric_selection",
                        "post_id": post_id,
                        "details": {
                            "input_data": rubric_selection_data,
                            "tokens_used": rubric_result.tokens_used,
                            "processing_time": rubric_result.processing_time
                        }
                    })
            else:
                logger.info(f"Пропускаем выбор рубрик для поста {post_id}")
                stages.append(ProcessingStage(
                    stage_name="rubric_selection",
                    success=True,
                    data={"skipped": True},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Этап 4: Генерация сценариев (если не пропускается)
            if not skip_rubric_selection:
                logger.info(f"Этап 4: Генерация сценариев для поста {post_id}")
                logger.info(f"Rubric result: {rubric_result.success if rubric_result else 'None'}")
                logger.info(f"Rubric data: {rubric_result.data if rubric_result else 'None'}")
                scenarios = []
                if rubric_result and rubric_result.success:
                    combinations = rubric_result.data.get("combinations", [])[:2]  # Топ-2 комбинации
                    if not combinations:
                        # Попробуем найти в top_combinations или top_3_combinations
                        combinations = rubric_result.data.get("top_combinations", [])[:2]
                        if not combinations:
                            # Обработка формата top_3_combinations
                            top_3_combinations = rubric_result.data.get("top_3_combinations", [])[:2]
                            combinations = []
                            for item in top_3_combinations:
                                if isinstance(item, dict):
                                    # Если item содержит 'combination', берем его
                                    if 'combination' in item:
                                        combinations.append(item['combination'])
                                    # Иначе берем item напрямую (если он уже содержит rubric/format)
                                    elif 'rubric' in item and 'format' in item:
                                        combinations.append(item)
                        logger.info(f"Using alternative combinations field: {len(combinations)} found")
                    logger.info(f"Combinations found: {len(combinations)}")
                    for combo in combinations:
                        logger.info(f"Combination: {combo}")

                    for i, combination in enumerate(combinations):
                        logger.info(f"Генерация сценария {i+1}/{len(combinations)} для поста {post_id}")

                        # Получаем информацию о формате из комбинации
                        format_info = combination.get("format", {})
                        if isinstance(format_info, str):
                            # Если format - строка, используем дефолтные настройки
                            duration = 60
                            format_name = format_info
                        else:
                            # Если format - объект, берем данные из него
                            duration = format_info.get('duration_seconds') or format_info.get('duration', 60)
                            format_name = format_info.get('name', 'Неизвестный формат')

                        logger.info(f"Processing combination: rubric={combination.get('rubric')}, format={format_name}, duration={duration}")

                        # Исправляем формат данных для генератора
                        rubric_data = combination.get("rubric", {})
                        format_data = combination.get("format", {})

                        # Если rubric - строка, преобразуем в объект
                        if isinstance(rubric_data, str):
                            rubric_data = {"name": rubric_data}

                        # Если format - строка, преобразуем в объект
                        if isinstance(format_data, str):
                            format_data = {"name": format_data, "duration": duration}

                        generator_input = {
                            **post_data,
                            "analysis": analysis_result.data if analysis_result and analysis_result.success else {},
                            "rubric": rubric_data,
                            "reel_format": format_data,
                            "combination_score": combination.get("score", 0)
                        }

                        # Debug: Логируем промпты генерации

                        generator_system_prompt = prompt_manager.get_system_prompt("generate_scenario_system", {
                            "duration": duration
                        })
                        # Получаем информацию о рубрике
                        rubric_info = combination.get("rubric", {})
                        if isinstance(rubric_info, str):
                            rubric_name = rubric_info
                        else:
                            rubric_name = rubric_info.get('name', 'Не указана')

                        generator_user_prompt = prompt_manager.get_user_prompt("generate_scenario_system", {
                            "post_text": post_data.get("text", ""),
                            "post_analysis": str(analysis_result.data if analysis_result and analysis_result.success else {}),
                            "rubric_name": rubric_name,
                            "format_name": format_name,
                            "duration": duration
                        })

                        self._log_debug_step(f"generation_{i+1}_prompts", "prompts", {
                            "system_prompt": generator_system_prompt,
                            "user_prompt": generator_user_prompt,
                            "model": self.generator_processor.model_name
                        })

                        scenario_result = await self.generator_processor.process(generator_input)

                        # Debug: Логируем результат генерации
                        self._log_debug_step(f"generation_{i+1}_complete", "llm_response", {
                            "success": scenario_result.success,
                            "result": scenario_result.data,
                            "error": scenario_result.error,
                            "tokens_used": scenario_result.tokens_used,
                            "processing_time": scenario_result.processing_time
                        })

                        if scenario_result.success:
                            scenarios.append({
                                **scenario_result.data,
                                "rubric": combination.get("rubric", {}),
                                "format": combination.get("format", {}),
                                "selection_reason": combination.get("reason", ""),
                                "expected_engagement": combination.get("expected_engagement", 0)
                            })

                        stages.append(ProcessingStage(
                            stage_name=f"generation_{i+1}",
                            success=scenario_result.success,
                            data=scenario_result.data,
                            error=scenario_result.error,
                            tokens_used=scenario_result.tokens_used,
                            processing_time=scenario_result.processing_time
                        ))

                        total_tokens += scenario_result.tokens_used
                else:
                    # Если нет выбранных комбинаций или rubric failed, генерируем с дефолтными параметрами
                    logger.info(f"Генерация сценария с дефолтными параметрами для поста {post_id}")

                    generator_input = {
                        **post_data,
                        "analysis": analysis_result.data if analysis_result and analysis_result.success else {},
                        "rubric": {},
                        "reel_format": {}
                    }

                    scenario_result = await self.generator_processor.process(generator_input)

                    if scenario_result.success:
                        scenarios.append(scenario_result.data)

                    stages.append(ProcessingStage(
                        stage_name="generation",
                        success=scenario_result.success,
                        data=scenario_result.data,
                        error=scenario_result.error,
                        tokens_used=scenario_result.tokens_used,
                        processing_time=scenario_result.processing_time
                    ))

                    total_tokens += scenario_result.tokens_used
            else:
                logger.info(f"Пропускаем генерацию сценариев для поста {post_id}")
                scenarios = []
                stages.append(ProcessingStage(
                    stage_name="generation",
                    success=True,
                    data={"skipped": True},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Формируем финальный результат
            final_data = None
            if scenarios:
                final_data = {
                    "filter": filter_result.data if filter_result else None,
                    "analysis": analysis_result.data if analysis_result and analysis_result.success else None,
                    "rubric_selection": rubric_result.data if rubric_result and rubric_result.success else None,
                    "scenarios": scenarios,
                    "processing_stats": {
                        "total_tokens": total_tokens,
                        "total_time": asyncio.get_event_loop().time() - start_time,
                        "stages_completed": len([s for s in stages if s.success])
                    }
                }

            # Определяем общий успех: если пропускаем генерацию, успех = успеху фильтрации
            if skip_rubric_selection:
                overall_success = filter_result.success if filter_result else False
            else:
                overall_success = len(scenarios) > 0

            # Создаем финальный результат
            final_result = OrchestratorResult(
                post_id=post_id,
                overall_success=overall_success,
                stages=stages,
                final_data=final_data,
                total_tokens=total_tokens,
                total_time=asyncio.get_event_loop().time() - start_time
            )

            # Сохраняем результаты в базу данных если есть успешные результаты
            if overall_success and supabase_client.is_connected():
                await self._save_results_to_database([final_result], [post_data])

            return final_result

        except Exception as e:
            logger.error(f"Критическая ошибка в enhanced оркестраторе для поста {post_id}: {e}", exc_info=True)

            return OrchestratorResult(
                post_id=post_id,
                overall_success=False,
                stages=stages,
                total_tokens=total_tokens,
                total_time=asyncio.get_event_loop().time() - start_time,
                error=f"Критическая ошибка: {str(e)}"
            )

    async def _get_available_rubrics(self) -> List[Dict[str, Any]]:
        """Получает доступные рубрики из базы данных."""
        try:
            if supabase_client.is_connected():
                # Получаем рубрики из Supabase
                result = supabase_client.client.table('rubrics').select('*').eq('is_active', True).execute()
                return result.data or []
            else:
                # Заглушка для тестирования
                return [
                    {"id": "tech_basics", "name": "Основы технологий", "description": "Базовые концепции IT"},
                    {"id": "business_strategy", "name": "Бизнес стратегия", "description": "Стратегическое планирование"},
                    {"id": "personal_growth", "name": "Личное развитие", "description": "Саморазвитие и продуктивность"}
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении рубрик: {e}")
            return []

    async def _get_available_formats(self) -> List[Dict[str, Any]]:
        """Получает доступные форматы из базы данных."""
        try:
            if supabase_client.is_connected():
                # Получаем форматы из Supabase
                result = supabase_client.client.table('reel_formats').select('*').eq('is_active', True).execute()
                return result.data or []
            else:
                # Заглушка для тестирования
                return [
                    {"id": "quick_tip", "name": "Быстрый совет", "duration_seconds": 30, "description": "Короткий практический совет"},
                    {"id": "deep_dive", "name": "Глубокий разбор", "duration_seconds": 60, "description": "Подробный анализ темы"},
                    {"id": "case_study", "name": "Кейс-стади", "duration_seconds": 45, "description": "Анализ реального примера"}
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении форматов: {e}")
            return []

    async def process_post(
        self,
        post_data: Dict[str, Any],
        rubric: Optional[Dict[str, Any]] = None,
        reel_format: Optional[Dict[str, Any]] = None,
        skip_filter: bool = False,
        skip_analysis: bool = False
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
        post_id = f"{post_data.get('message_id', 'unknown')}_{post_data.get('channel_username', 'unknown')}"
        start_time = asyncio.get_event_loop().time()
        stages = []
        total_tokens = 0

        logger.info(f"Начинаем обработку поста {post_id}")

        try:
            # Этап 1: Фильтрация (если не пропускается)
            filter_result = None
            if not skip_filter:
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
            else:
                logger.info(f"Пропускаем фильтрацию для поста {post_id}")
                # Создаем фиктивный успешный результат фильтрации
                stages.append(ProcessingStage(
                    stage_name="filter",
                    success=True,
                    data={"suitable": True, "score": 1.0, "reason": "Пропущено"},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Этап 2: Анализ причин успеха (если не пропускается)
            analysis_result = None
            if not skip_analysis:
                logger.info(f"Этап 2: Анализ поста {post_id}")
                filter_score = filter_result.data.get("score", 0) if filter_result else 0
                analysis_result = await self.analysis_processor.process({
                    **post_data,
                    "filter_score": filter_score
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
            else:
                logger.info(f"Пропускаем анализ для поста {post_id}")
                # Создаем фиктивный результат анализа
                stages.append(ProcessingStage(
                    stage_name="analysis",
                    success=True,
                    data={"skipped": True},
                    tokens_used=0,
                    processing_time=0.0
                ))

            # Этап 3: Генерация сценария
            logger.info(f"Этап 3: Генерация сценария для поста {post_id}")
            analysis_data = analysis_result.data if analysis_result and analysis_result.success else {}
            generator_input = {
                **post_data,
                "analysis": analysis_data,
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
        concurrency: int = 3,
        skip_filter: bool = False,
        skip_analysis: bool = False
    ) -> List[OrchestratorResult]:
        """
        Обрабатывает несколько постов параллельно.

        Args:
            posts: Список постов для обработки
            rubric: Рубрика для всех постов
            reel_format: Формат для всех постов
            concurrency: Максимальное количество одновременных обработок
            skip_filter: Пропустить этап фильтрации (для предварительно отфильтрованных постов)
            skip_analysis: Пропустить этап анализа (только генерация сценариев)

        Returns:
            Список результатов обработки
        """
        logger.info(f"Начинаем пакетную обработку {len(posts)} постов (concurrency: {concurrency})")

        # Создаем семафор для ограничения concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(post_data):
            async with semaphore:
                return await self.process_post(post_data, rubric, reel_format, skip_filter, skip_analysis)

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

                            # Debug: Логируем сохранение токенов
                            self._log_debug_step("db_save_tokens", "db_operation", {
                                "operation": "save_token_usage",
                                "data": token_data,
                                "stage": stage.stage_name
                            })

                            supabase_client.save_token_usage(token_data)

                        # Сохраняем анализ
                        # Debug: Логируем сохранение анализа
                        self._log_debug_step("db_save_analysis", "db_operation", {
                            "operation": "save_post_analysis",
                            "data": analysis_data,
                            "stage": stage.stage_name
                        })

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

                    # Debug: Логируем сохранение сценариев
                    self._log_debug_step("db_save_scenarios", "db_operation", {
                        "operation": "save_scenarios",
                        "scenarios_count": len(scenarios_data),
                        "data": scenarios_data,
                        "post_id": result.post_id
                    })

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
            'analysis': 'claude-3-5-sonnet',
            'rubric_selection': 'gpt-4o',  # Пока оставляем GPT-4o, потом заменим на GPT-4o-mini
            'generator': 'gpt-4o'
        }
        return model_mapping.get(stage_name, 'unknown')

    def _calculate_cost(self, stage_name: str, tokens: int) -> float:
        """Рассчитывает стоимость использования токенов с актуальными ценами."""
        model = self._get_model_for_stage(stage_name)

        # Предполагаем соотношение input/output токенов 70/30
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)

        # Используем новый price_monitor для точного расчета
        usage_data = {
            stage_name: {
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
        }

        cost_report = price_monitor.get_cost_calculation(usage_data)
        stage_cost = cost_report['breakdown'][stage_name]['cost_usd']
        return round(stage_cost, 6)

    def get_processor_status(self) -> Dict[str, bool]:
        """Возвращает статус доступности всех процессоров."""
        return self.available_processors.copy()
