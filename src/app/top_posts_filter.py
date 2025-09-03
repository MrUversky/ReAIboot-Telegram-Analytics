"""
Модуль предварительной фильтрации самых "залетевших" постов.
Отбирает топ-посты перед отправкой на LLM обработку для оптимизации расходов.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .settings import settings
from .utils import setup_logger
from .metrics import MetricsCalculator

# Настройка логирования
logger = setup_logger(__name__)

@dataclass
class FilterCriteria:
    """Критерии фильтрации топ-постов."""
    min_score: float = 0.01
    min_views: int = 100
    min_reactions: int = 5
    min_reaction_rate: float = 0.001
    max_posts_per_channel: int = 3
    max_total_posts: int = 50
    min_post_age_hours: int = 1
    max_post_age_days: int = 30

@dataclass
class FilteredPostsResult:
    """Результат фильтрации постов."""
    selected_posts: List[Dict[str, Any]]
    filtered_out: Dict[str, int]  # причины отсева
    stats: Dict[str, Any]

class TopPostsFilter:
    """Фильтр для отбора самых "залетевших" постов."""

    def __init__(self, criteria: Optional[FilterCriteria] = None):
        """
        Инициализирует фильтр топ-постов.

        Args:
            criteria: Критерии фильтрации
        """
        self.criteria = criteria or FilterCriteria()
        self.metrics_calculator = MetricsCalculator()
        logger.info(f"Инициализирован фильтр с критериями: {self.criteria}")

    def filter_posts(self, all_posts: List[Dict[str, Any]]) -> FilteredPostsResult:
        """
        Фильтрует посты по критериям "залетевших" постов.

        Args:
            all_posts: Все собранные посты

        Returns:
            Результат фильтрации с отобранными постами
        """
        logger.info(f"Начинаем фильтрацию {len(all_posts)} постов")

        filtered_out = {
            "low_score": 0,
            "low_views": 0,
            "low_reactions": 0,
            "old_post": 0,
            "too_recent": 0,
            "no_text": 0,
            "channel_limit": 0
        }

        # Этап 1: Предварительная фильтрация
        candidates = []
        for post in all_posts:
            if self._passes_basic_filters(post, filtered_out):
                candidates.append(post)

        logger.info(f"После предварительной фильтрации: {len(candidates)} кандидатов")

        # Этап 2: Расчет метрик вовлеченности
        candidates_with_metrics = self.metrics_calculator.compute_metrics(candidates)

        # Этап 3: Выбор топ-постов по каналам
        selected_posts = self._select_top_per_channel(candidates_with_metrics)

        # Этап 4: Финальный отбор по общему рейтингу
        final_selection = self._select_final_top(selected_posts)

        stats = {
            "total_input": len(all_posts),
            "candidates_after_basic": len(candidates),
            "selected_per_channel": len(selected_posts),
            "final_selection": len(final_selection),
            "filter_reasons": filtered_out
        }

        logger.info(f"Фильтрация завершена: {len(final_selection)} постов отобрано")
        logger.info(f"Статистика фильтрации: {stats}")

        return FilteredPostsResult(
            selected_posts=final_selection,
            filtered_out=filtered_out,
            stats=stats
        )

    def _passes_basic_filters(self, post: Dict[str, Any], filter_stats: Dict[str, int]) -> bool:
        """Проверяет пост на соответствие базовым критериям."""
        # Проверка наличия текста
        if not post.get("text", "").strip():
            filter_stats["no_text"] += 1
            return False

        # Проверка возраста поста
        post_date = post.get("date")
        if post_date:
            try:
                if isinstance(post_date, str):
                    post_datetime = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                else:
                    post_datetime = post_date

                now = datetime.now(post_datetime.tzinfo) if post_datetime.tzinfo else datetime.now()

                # Слишком старый пост
                if (now - post_datetime) > timedelta(days=self.criteria.max_post_age_days):
                    filter_stats["old_post"] += 1
                    return False

                # Слишком свежий пост (меньше 1 часа)
                if (now - post_datetime) < timedelta(hours=self.criteria.min_post_age_hours):
                    filter_stats["too_recent"] += 1
                    return False

            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка парсинга даты поста: {e}")
                # Если не можем распарсить дату, пропускаем пост
                filter_stats["old_post"] += 1
                return False

        # Проверка минимальных просмотров
        views = post.get("views", 0) or 0
        if views < self.criteria.min_views:
            filter_stats["low_views"] += 1
            return False

        # Проверка минимальных реакций
        reactions = post.get("reactions", 0) or 0
        if reactions < self.criteria.min_reactions:
            filter_stats["low_reactions"] += 1
            return False

        return True

    def _select_top_per_channel(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Выбирает топ-посты для каждого канала."""
        from collections import defaultdict

        # Группируем посты по каналам
        posts_by_channel = defaultdict(list)
        for post in posts:
            channel_id = post.get("channel_username", "unknown")
            posts_by_channel[channel_id].append(post)

        selected = []

        for channel_id, channel_posts in posts_by_channel.items():
            # Сортируем посты канала по score
            sorted_posts = sorted(channel_posts, key=lambda x: x.get("score", 0), reverse=True)

            # Выбираем топ-N для этого канала
            top_for_channel = sorted_posts[:self.criteria.max_posts_per_channel]
            selected.extend(top_for_channel)

            logger.debug(f"Канал {channel_id}: {len(channel_posts)} постов → выбрано {len(top_for_channel)}")

        return selected

    def _select_final_top(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Финальный отбор топ-постов по общему рейтингу."""
        # Сортируем все отобранные посты по score
        sorted_posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)

        # Выбираем финальный топ
        final_top = sorted_posts[:self.criteria.max_total_posts]

        # Добавляем дополнительную информацию для каждого поста
        for i, post in enumerate(final_top):
            post["top_rank"] = i + 1
            post["filter_criteria"] = {
                "min_score": self.criteria.min_score,
                "min_views": self.criteria.min_views,
                "min_reactions": self.criteria.min_reactions,
                "filtered_at": datetime.now().isoformat()
            }

        return final_top

    def get_filter_stats(self, result: FilteredPostsResult) -> Dict[str, Any]:
        """Возвращает детальную статистику фильтрации."""
        total_filtered = sum(result.filtered_out.values())
        total_input = result.stats["total_input"]

        return {
            "input_posts": total_input,
            "filtered_out": total_filtered,
            "selected": len(result.selected_posts),
            "filter_efficiency": len(result.selected_posts) / total_input if total_input > 0 else 0,
            "reasons_breakdown": result.filtered_out,
            "avg_score_selected": sum(p.get("score", 0) for p in result.selected_posts) / len(result.selected_posts) if result.selected_posts else 0,
            "channels_covered": len(set(p.get("channel_username") for p in result.selected_posts))
        }
