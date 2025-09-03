"""
Умный фильтр топ-постов на основе базовых метрик каналов.
Заменяет старый TopPostsFilter новой логикой определения 'залетевших' постов.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .channel_baseline_analyzer import ChannelBaselineAnalyzer
from .viral_post_detector import ViralPostDetector
from .supabase_client import SupabaseManager
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)

@dataclass
class SmartFilterResult:
    """Результат умной фильтрации постов."""
    selected_posts: List[Dict[str, Any]]
    filtered_out: Dict[str, int]  # причины отсева
    stats: Dict[str, Any]
    channels_processed: Dict[str, Dict[str, Any]]  # статистика по каналам

class SmartTopPostsFilter:
    """Умный фильтр топ-постов на основе 'залетевшести'."""

    def __init__(self, supabase_manager: SupabaseManager):
        """
        Инициализирует умный фильтр топ-постов.

        Args:
            supabase_manager: Менеджер Supabase для работы с БД
        """
        self.supabase = supabase_manager
        self.baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
        self.viral_detector = ViralPostDetector(self.baseline_analyzer)
        self.settings = self._load_settings()
        logger.info("Инициализирован SmartTopPostsFilter")

    def _load_settings(self) -> Dict[str, Any]:
        """Загружает настройки фильтрации."""
        try:
            viral_thresholds = self.supabase.get_system_setting('viral_thresholds') or {
                "min_viral_score": 1.5,
                "min_zscore": 1.5,
                "min_median_multiplier": 2.0,
                "min_views_percentile": 0.001
            }

            baseline_calculation = self.supabase.get_system_setting('baseline_calculation') or {
                "history_days": 30,
                "min_posts_for_baseline": 10,
                "outlier_removal_percentile": 95
            }

            return {
                'viral_thresholds': viral_thresholds,
                'baseline_calculation': baseline_calculation
            }
        except Exception as e:
            logger.warning(f"Не удалось загрузить настройки: {e}. Используем значения по умолчанию.")
            return {
                'viral_thresholds': {
                    "min_viral_score": 1.5,
                    "min_zscore": 1.5,
                    "min_median_multiplier": 2.0,
                    "min_views_percentile": 0.001
                },
                'baseline_calculation': {
                    "history_days": 30,
                    "min_posts_for_baseline": 10,
                    "outlier_removal_percentile": 95
                }
            }

    def filter_top_posts(self, all_posts: List[Dict[str, Any]],
                        max_posts_per_channel: int = 3,
                        max_total_posts: int = 50) -> SmartFilterResult:
        """
        Умная фильтрация топ-постов на основе 'залетевшести'.

        Args:
            all_posts: Все собранные посты
            max_posts_per_channel: Максимум постов с одного канала
            max_total_posts: Максимум постов всего

        Returns:
            Результат фильтрации с отобранными постами
        """
        logger.info(f"Начинаем умную фильтрацию {len(all_posts)} постов")

        filtered_out = {
            "no_baseline": 0,
            "low_viral_score": 0,
            "old_post": 0,
            "low_views": 0,
            "channel_limit": 0,
            "baseline_learning": 0
        }

        channels_processed = {}
        viral_posts = []

        # Группируем посты по каналам
        posts_by_channel = self._group_posts_by_channel(all_posts)

        # Обрабатываем каждый канал
        for channel_username, channel_posts in posts_by_channel.items():
            logger.debug(f"Обработка канала {channel_username}: {len(channel_posts)} постов")

            channel_stats = self._process_channel_posts(
                channel_username, channel_posts, filtered_out, max_posts_per_channel
            )

            channels_processed[channel_username] = channel_stats

            # Добавляем отобранные посты канала
            viral_posts.extend(channel_stats['selected_posts'])

        # Финальная сортировка и ограничение по общему количеству
        viral_posts.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
        final_selection = viral_posts[:max_total_posts]

        # Обновляем ранги в финальном списке
        for i, post in enumerate(final_selection):
            post['top_rank'] = i + 1
            post['filter_criteria'] = {
                'method': 'smart_viral_detection',
                'min_viral_score': self.settings['viral_thresholds']['min_viral_score'],
                'filtered_at': datetime.now().isoformat()
            }

        stats = {
            "total_input": len(all_posts),
            "channels_processed": len(channels_processed),
            "viral_posts_found": len(viral_posts),
            "final_selection": len(final_selection),
            "filter_reasons": filtered_out,
            "avg_viral_score_selected": sum(p.get('viral_score', 0) for p in final_selection) / len(final_selection) if final_selection else 0
        }

        logger.info(f"Умная фильтрация завершена: {len(final_selection)} постов отобрано")
        logger.info(f"Средний viral_score отобранных постов: {stats['avg_viral_score_selected']:.2f}")

        return SmartFilterResult(
            selected_posts=final_selection,
            filtered_out=filtered_out,
            stats=stats,
            channels_processed=channels_processed
        )

    def _group_posts_by_channel(self, posts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группирует посты по каналам."""
        posts_by_channel = {}
        for post in posts:
            channel_username = post.get('channel_username', 'unknown')
            if channel_username not in posts_by_channel:
                posts_by_channel[channel_username] = []
            posts_by_channel[channel_username].append(post)

        return posts_by_channel

    def _process_channel_posts(self, channel_username: str, posts: List[Dict[str, Any]],
                              filter_stats: Dict[str, int], max_posts_per_channel: int) -> Dict[str, Any]:
        """Обрабатывает посты одного канала."""
        # Проверяем базовые метрики канала
        baseline = self.baseline_analyzer.get_channel_baseline(channel_username)

        if not baseline:
            # Пытаемся рассчитать базовые метрики
            baseline = self.baseline_analyzer.calculate_channel_baseline(channel_username, posts)

            if baseline:
                # Сохраняем рассчитанные метрики
                self.baseline_analyzer.save_channel_baseline(baseline)
                logger.info(f"Рассчитаны базовые метрики для канала {channel_username}")
            else:
                filter_stats["no_baseline"] += len(posts)
                return {
                    'selected_posts': [],
                    'baseline_status': 'none',
                    'posts_processed': len(posts),
                    'viral_found': 0
                }

        # Проверяем статус базовых метрик
        if baseline.baseline_status == 'learning':
            filter_stats["baseline_learning"] += len(posts)
            logger.debug(f"Канал {channel_username} в режиме обучения")
            return {
                'selected_posts': [],
                'baseline_status': 'learning',
                'posts_processed': len(posts),
                'viral_found': 0
            }

        # Анализируем посты на 'залетевшесть'
        viral_results = self.viral_detector.detect_viral_posts(posts, channel_username)

        # Отбираем 'залетевшие' посты
        viral_posts = []
        for post, result in zip(posts, viral_results):
            if result.is_viral:
                # Добавляем метрики в пост
                post.update({
                    'viral_score': result.viral_score,
                    'engagement_rate': result.engagement_rate,
                    'zscore': result.zscore,
                    'median_multiplier': result.median_multiplier,
                    'virality_reasons': result.reasons
                })
                viral_posts.append(post)

                # Обновляем метрики поста в БД
                viral_data = {
                    'viral_score': result.viral_score,
                    'engagement_rate': result.engagement_rate,
                    'zscore': result.zscore,
                    'median_multiplier': result.median_multiplier
                }
                self.supabase.update_post_viral_metrics(post['id'], viral_data)
            else:
                # Подсчитываем причины отсева
                if result.viral_score < self.settings['viral_thresholds']['min_viral_score']:
                    filter_stats["low_viral_score"] += 1

        # Ограничиваем количество постов с канала
        viral_posts.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
        selected_posts = viral_posts[:max_posts_per_channel]

        if len(viral_posts) > max_posts_per_channel:
            filter_stats["channel_limit"] += len(viral_posts) - max_posts_per_channel

        logger.debug(f"Канал {channel_username}: найдено {len(viral_posts)} viral постов, отобрано {len(selected_posts)}")

        return {
            'selected_posts': selected_posts,
            'baseline_status': baseline.baseline_status,
            'posts_processed': len(posts),
            'viral_found': len(viral_posts),
            'baseline_metrics': {
                'avg_engagement_rate': baseline.avg_engagement_rate,
                'median_engagement_rate': baseline.median_engagement_rate,
                'std_engagement_rate': baseline.std_engagement_rate
            }
        }

    def update_channel_baselines(self, channels: List[str]) -> Dict[str, Any]:
        """
        Обновляет базовые метрики для списка каналов.

        Args:
            channels: Список username каналов

        Returns:
            Статистика обновления
        """
        logger.info(f"Обновление базовых метрик для {len(channels)} каналов")

        stats = {
            'processed': 0,
            'updated': 0,
            'failed': 0,
            'new_baselines': 0
        }

        for channel_username in channels:
            try:
                stats['processed'] += 1

                # Проверяем, есть ли уже базовые метрики
                existing_baseline = self.baseline_analyzer.get_channel_baseline(channel_username)

                # Рассчитываем новые метрики
                new_baseline = self.baseline_analyzer.calculate_channel_baseline(channel_username)

                if new_baseline:
                    if existing_baseline:
                        stats['updated'] += 1
                        logger.debug(f"Обновлены базовые метрики канала {channel_username}")
                    else:
                        stats['new_baselines'] += 1
                        logger.debug(f"Созданы базовые метрики канала {channel_username}")

                    # Сохраняем метрики
                    self.baseline_analyzer.save_channel_baseline(new_baseline)
                else:
                    stats['failed'] += 1
                    logger.warning(f"Не удалось рассчитать базовые метрики для канала {channel_username}")

            except Exception as e:
                stats['failed'] += 1
                logger.error(f"Ошибка при обновлении метрик канала {channel_username}: {e}")

        logger.info(f"Обновление базовых метрик завершено: {stats}")
        return stats

    def get_filter_stats(self, result: SmartFilterResult) -> Dict[str, Any]:
        """Возвращает детальную статистику фильтрации."""
        total_filtered = sum(result.filtered_out.values())
        total_input = result.stats["total_input"]

        return {
            "input_posts": total_input,
            "filtered_out": total_filtered,
            "selected": len(result.selected_posts),
            "filter_efficiency": len(result.selected_posts) / total_input if total_input > 0 else 0,
            "channels_processed": result.stats["channels_processed"],
            "avg_viral_score_selected": result.stats["avg_viral_score_selected"],
            "reasons_breakdown": result.filtered_out,
            "channels_stats": result.channels_processed
        }
