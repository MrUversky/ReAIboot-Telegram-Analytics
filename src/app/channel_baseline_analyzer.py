"""
Анализатор базовых метрик каналов для определения "залетевших" постов.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

from .settings import settings
from .utils import setup_logger
from .supabase_client import SupabaseManager

# Настройка логирования
logger = setup_logger(__name__)

@dataclass
class ChannelBaseline:
    """Базовые метрики канала для определения "залетевших" постов."""
    channel_username: str
    subscribers_count: int
    posts_analyzed: int
    avg_engagement_rate: float
    median_engagement_rate: float
    std_engagement_rate: float
    p75_engagement_rate: float
    p95_engagement_rate: float
    max_engagement_rate: float
    baseline_status: str  # 'learning', 'ready', 'outdated'
    last_calculated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД."""
        return {
            'channel_username': self.channel_username,
            'subscribers_count': self.subscribers_count,
            'posts_analyzed': self.posts_analyzed,
            'avg_engagement_rate': self.avg_engagement_rate,
            'median_engagement_rate': self.median_engagement_rate,
            'std_engagement_rate': self.std_engagement_rate,
            'p75_engagement_rate': self.p75_engagement_rate,
            'p95_engagement_rate': self.p95_engagement_rate,
            'max_engagement_rate': self.max_engagement_rate,
            'baseline_status': self.baseline_status,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }


class ChannelBaselineAnalyzer:
    """Анализатор базовых метрик каналов."""

    def __init__(self, supabase_manager: SupabaseManager):
        """
        Инициализирует анализатор базовых метрик.

        Args:
            supabase_manager: Менеджер Supabase для работы с БД
        """
        self.supabase = supabase_manager
        self.settings = self._load_settings()
        logger.info("Инициализирован ChannelBaselineAnalyzer")

    def _load_settings(self) -> Dict[str, Any]:
        """Загружает настройки из базы данных."""
        try:
            # Получаем настройки из БД
            viral_weights = self.supabase.get_system_setting('viral_weights') or {
                "forward_rate": 0.5,
                "reaction_rate": 0.3,
                "reply_rate": 0.2
            }

            baseline_calculation = self.supabase.get_system_setting('baseline_calculation') or {
                "history_days": 30,
                "min_posts_for_baseline": 10,
                "outlier_removal_percentile": 95
            }

            return {
                'viral_weights': viral_weights,
                'baseline_calculation': baseline_calculation
            }
        except Exception as e:
            logger.warning(f"Не удалось загрузить настройки из БД: {e}. Используем значения по умолчанию.")
            return {
                'viral_weights': {"forward_rate": 0.5, "reaction_rate": 0.3, "reply_rate": 0.2},
                'baseline_calculation': {"history_days": 30, "min_posts_for_baseline": 10, "outlier_removal_percentile": 95}
            }

    def calculate_channel_baseline(self, channel_username: str, posts: List[Dict[str, Any]] = None) -> Optional[ChannelBaseline]:
        """
        Рассчитывает базовые метрики канала.

        Args:
            channel_username: Username канала
            posts: Список постов для анализа (опционально, если None - берет из БД)

        Returns:
            ChannelBaseline или None если недостаточно данных
        """
        try:
            logger.info(f"Расчет базовых метрик для канала {channel_username}")

            # Если посты не переданы, получаем из БД
            if posts is None:
                posts = self._get_channel_posts_history(channel_username)

            if not posts:
                logger.warning(f"Нет постов для анализа канала {channel_username}")
                return None

            # Рассчитываем engagement rate для каждого поста
            engagement_rates = []
            for post in posts:
                engagement_rate = self._calculate_post_engagement_rate(post)
                if engagement_rate is not None:
                    engagement_rates.append(engagement_rate)

            if len(engagement_rates) < self.settings['baseline_calculation']['min_posts_for_baseline']:
                logger.info(f"Недостаточно постов для канала {channel_username}: {len(engagement_rates)} < {self.settings['baseline_calculation']['min_posts_for_baseline']}")
                return None

            # Удаляем выбросы
            engagement_rates_clean = self._remove_outliers(engagement_rates)

            # Рассчитываем статистические показатели
            baseline = self._calculate_baseline_stats(channel_username, engagement_rates_clean, len(posts))

            logger.info(f"Рассчитаны базовые метрики для канала {channel_username}: "
                       f"median={baseline.median_engagement_rate:.4f}, "
                       f"std={baseline.std_engagement_rate:.4f}")

            return baseline

        except Exception as e:
            logger.error(f"Ошибка при расчете базовых метрик для канала {channel_username}: {e}")
            return None

    def _get_channel_posts_history(self, channel_username: str) -> List[Dict[str, Any]]:
        """Получает историю постов канала из БД."""
        try:
            days_back = self.settings['baseline_calculation']['history_days']

            # Получаем посты за указанный период
            posts = self.supabase.client.table('posts').select('*').eq(
                'channel_username', channel_username
            ).gte(
                'date', (datetime.now() - timedelta(days=days_back)).isoformat()
            ).execute()

            return posts.data if posts.data else []

        except Exception as e:
            logger.error(f"Ошибка при получении истории постов для канала {channel_username}: {e}")
            return []

    def _calculate_post_engagement_rate(self, post: Dict[str, Any]) -> Optional[float]:
        """
        Рассчитывает engagement rate для поста.

        Формула: (forwards * 0.5 + reactions * 0.3 + replies * 0.2) / views
        """
        try:
            views = post.get('views', 0)
            if views <= 0:
                return None

            forwards = post.get('forwards', 0)
            reactions = post.get('reactions', 0)
            replies = post.get('replies', 0)

            # Взвешенная сумма engagement
            weighted_engagement = (
                forwards * self.settings['viral_weights']['forward_rate'] +
                reactions * self.settings['viral_weights']['reaction_rate'] +
                replies * self.settings['viral_weights']['reply_rate']
            )

            engagement_rate = weighted_engagement / views

            return min(engagement_rate, 1.0)  # Ограничиваем максимумом 100%

        except Exception as e:
            logger.warning(f"Ошибка при расчете engagement rate для поста {post.get('id')}: {e}")
            return None

    def _remove_outliers(self, engagement_rates: List[float]) -> List[float]:
        """Удаляет выбросы из списка engagement rates."""
        if not engagement_rates:
            return engagement_rates

        # Используем percentile для удаления выбросов
        percentile_threshold = self.settings['baseline_calculation']['outlier_removal_percentile']

        if len(engagement_rates) >= 10:  # Только если достаточно данных
            threshold_value = np.percentile(engagement_rates, percentile_threshold)
            return [rate for rate in engagement_rates if rate <= threshold_value]

        return engagement_rates

    def _calculate_baseline_stats(self, channel_username: str, engagement_rates: List[float], total_posts: int) -> ChannelBaseline:
        """Рассчитывает статистические показатели базовых метрик."""
        rates_array = np.array(engagement_rates)

        return ChannelBaseline(
            channel_username=channel_username,
            subscribers_count=0,  # TODO: получить из канала
            posts_analyzed=total_posts,
            avg_engagement_rate=float(np.mean(rates_array)),
            median_engagement_rate=float(np.median(rates_array)),
            std_engagement_rate=float(np.std(rates_array)),
            p75_engagement_rate=float(np.percentile(rates_array, 75)),
            p95_engagement_rate=float(np.percentile(rates_array, 95)),
            max_engagement_rate=float(np.max(rates_array)),
            baseline_status='ready',
            last_calculated=datetime.now()
        )

    def save_channel_baseline(self, baseline: ChannelBaseline) -> bool:
        """
        Сохраняет базовые метрики канала в БД.

        Args:
            baseline: Базовые метрики для сохранения

        Returns:
            True если сохранение успешно
        """
        try:
            data = baseline.to_dict()
            data['updated_at'] = datetime.now().isoformat()

            result = self.supabase.client.table('channel_baselines').upsert(
                data,
                on_conflict='channel_username'
            ).execute()

            logger.info(f"Сохранены базовые метрики для канала {baseline.channel_username}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при сохранении базовых метрик для канала {baseline.channel_username}: {e}")
            return False

    def get_channel_baseline(self, channel_username: str) -> Optional[ChannelBaseline]:
        """
        Получает базовые метрики канала из БД.

        Args:
            channel_username: Username канала

        Returns:
            ChannelBaseline или None если не найдено
        """
        try:
            result = self.supabase.client.table('channel_baselines').select('*').eq(
                'channel_username', channel_username
            ).execute()

            if result.data and len(result.data) > 0:
                data = result.data[0]
                return ChannelBaseline(
                    channel_username=data['channel_username'],
                    subscribers_count=data.get('subscribers_count', 0),
                    posts_analyzed=data.get('posts_analyzed', 0),
                    avg_engagement_rate=data.get('avg_engagement_rate', 0),
                    median_engagement_rate=data.get('median_engagement_rate', 0),
                    std_engagement_rate=data.get('std_engagement_rate', 0),
                    p75_engagement_rate=data.get('p75_engagement_rate', 0),
                    p95_engagement_rate=data.get('p95_engagement_rate', 0),
                    max_engagement_rate=data.get('max_engagement_rate', 0),
                    baseline_status=data.get('baseline_status', 'learning'),
                    last_calculated=datetime.fromisoformat(data['last_calculated']) if data.get('last_calculated') else None
                )

            return None

        except Exception as e:
            logger.error(f"Ошибка при получении базовых метрик для канала {channel_username}: {e}")
            return None

    def is_baseline_ready(self, channel_username: str) -> bool:
        """
        Проверяет, готовы ли базовые метрики канала для использования.

        Args:
            channel_username: Username канала

        Returns:
            True если базовые метрики готовы
        """
        baseline = self.get_channel_baseline(channel_username)
        if not baseline:
            return False

        return (
            baseline.baseline_status == 'ready' and
            baseline.posts_analyzed >= self.settings['baseline_calculation']['min_posts_for_baseline'] and
            baseline.median_engagement_rate > 0
        )
