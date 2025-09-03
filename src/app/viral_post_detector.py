"""
Детектор 'залетевших' постов на основе базовых метрик каналов.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .channel_baseline_analyzer import ChannelBaselineAnalyzer, ChannelBaseline
from .settings import settings
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)

@dataclass
class ViralPostResult:
    """Результат анализа поста на 'залетевшесть'."""
    post_id: str
    is_viral: bool
    viral_score: float
    engagement_rate: float
    zscore: float
    median_multiplier: float
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения."""
        return {
            'post_id': self.post_id,
            'is_viral': self.is_viral,
            'viral_score': self.viral_score,
            'engagement_rate': self.engagement_rate,
            'zscore': self.zscore,
            'median_multiplier': self.median_multiplier,
            'reasons': self.reasons
        }


class ViralPostDetector:
    """Детектор 'залетевших' постов."""

    def __init__(self, baseline_analyzer: ChannelBaselineAnalyzer):
        """
        Инициализирует детектор 'залетевших' постов.

        Args:
            baseline_analyzer: Анализатор базовых метрик каналов
        """
        self.baseline_analyzer = baseline_analyzer
        self.settings = self._load_thresholds()
        logger.info("Инициализирован ViralPostDetector")

    def _load_thresholds(self) -> Dict[str, Any]:
        """Загружает пороги для определения 'залетевших' постов."""
        try:
            # Получаем настройки из БД
            viral_thresholds_raw = self.baseline_analyzer.supabase.get_system_setting('viral_thresholds')

            if viral_thresholds_raw:
                if isinstance(viral_thresholds_raw, str):
                    try:
                        import json
                        viral_thresholds = json.loads(viral_thresholds_raw)
                    except Exception as e:
                        logger.warning(f"Failed to parse viral_thresholds: {e}, using defaults")
                        viral_thresholds = {
                            "min_viral_score": 1.5,
                            "min_zscore": 1.5,
                            "min_median_multiplier": 2.0,
                            "min_views_percentile": 0.001
                        }
                else:
                    viral_thresholds = viral_thresholds_raw
            else:
                viral_thresholds = {
                    "min_viral_score": 1.5,
                    "min_zscore": 1.5,
                    "min_median_multiplier": 2.0,
                    "min_views_percentile": 0.001
                }

            return viral_thresholds

        except Exception as e:
            logger.warning(f"Не удалось загрузить пороги из БД: {e}. Используем значения по умолчанию.")
            return {
                "min_viral_score": 1.5,
                "min_zscore": 1.5,
                "min_median_multiplier": 2.0,
                "min_views_percentile": 0.001
            }

    def analyze_post_virality(self, post: Dict[str, Any], channel_baseline: ChannelBaseline) -> ViralPostResult:
        """
        Анализирует пост на 'залетевшесть'.

        Args:
            post: Данные поста
            channel_baseline: Базовые метрики канала

        Returns:
            Результат анализа поста
        """
        try:
            post_id = post.get('id') or f"{post.get('message_id', 'unknown')}_{post.get('channel_username', 'unknown')}"

            # Рассчитываем engagement rate поста
            engagement_rate = self._calculate_post_engagement_rate(post)
            if engagement_rate is None:
                return ViralPostResult(
                    post_id=post_id,
                    is_viral=False,
                    viral_score=0,
                    engagement_rate=0,
                    zscore=0,
                    median_multiplier=0,
                    reasons=["Не удалось рассчитать engagement rate"]
                )

            # Рассчитываем метрики "залетевшести"
            zscore = self._calculate_zscore(engagement_rate, channel_baseline)
            median_multiplier = self._calculate_median_multiplier(engagement_rate, channel_baseline)
            viral_score = self._calculate_viral_score(zscore, median_multiplier, post)

            # Определяем, является ли пост "залетевшим"
            is_viral = self._is_post_viral(viral_score, zscore, median_multiplier, post, channel_baseline)

            # Собираем причины
            reasons = self._get_virality_reasons(is_viral, viral_score, zscore, median_multiplier)

            result = ViralPostResult(
                post_id=post_id,
                is_viral=is_viral,
                viral_score=viral_score,
                engagement_rate=engagement_rate,
                zscore=zscore,
                median_multiplier=median_multiplier,
                reasons=reasons
            )

            logger.debug(f"Анализ поста {post_id}: viral_score={viral_score:.2f}, is_viral={is_viral}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при анализе поста {post.get('id', 'unknown')}: {e}")
            return ViralPostResult(
                post_id=post.get('id', 'unknown'),
                is_viral=False,
                viral_score=0,
                engagement_rate=0,
                zscore=0,
                median_multiplier=0,
                reasons=[f"Ошибка анализа: {str(e)}"]
            )

    def _calculate_post_engagement_rate(self, post: Dict[str, Any]) -> Optional[float]:
        """Рассчитывает engagement rate для поста."""
        try:
            views = post.get('views', 0)
            if views <= 0:
                return None

            forwards = post.get('forwards', 0)
            reactions = post.get('reactions', 0)
            replies = post.get('replies', 0)

            # Используем веса из baseline_analyzer
            weights = self.baseline_analyzer.settings.get('viral_weights', {})

            # Если weights - строка JSON, распарсим её
            if isinstance(weights, str):
                try:
                    import json
                    weights = json.loads(weights)
                    logger.debug(f"Parsed viral_weights in detector: {weights}")
                except Exception as e:
                    logger.warning(f"Ошибка парсинга viral_weights: {e}, используем дефолтные")
                    weights = {"forward_rate": 0.5, "reaction_rate": 0.3, "reply_rate": 0.2}
            elif not weights or not isinstance(weights, dict):
                logger.warning("Viral weights not found or invalid in detector, using defaults")
                weights = {"forward_rate": 0.5, "reaction_rate": 0.3, "reply_rate": 0.2}

            # Взвешенная сумма engagement
            weighted_engagement = (
                forwards * weights['forward_rate'] +
                reactions * weights['reaction_rate'] +
                replies * weights['reply_rate']
            )

            engagement_rate = weighted_engagement / views

            logger.debug(f"Post {post.get('id', 'unknown')}: views={views}, forwards={forwards}, reactions={reactions}, replies={replies}")
            logger.debug(f"Weights: {weights}")
            logger.debug(f"Weighted engagement: {weighted_engagement}, engagement_rate: {engagement_rate}")

            return min(engagement_rate, 1.0)  # Ограничиваем максимумом 100%

        except Exception as e:
            logger.warning(f"Ошибка при расчете engagement rate: {e}")
            return None

    def _calculate_zscore(self, engagement_rate: float, baseline: ChannelBaseline) -> float:
        """Рассчитывает Z-score для engagement rate."""
        if baseline.std_engagement_rate <= 0:
            return 0

        return (engagement_rate - baseline.avg_engagement_rate) / baseline.std_engagement_rate

    def _calculate_median_multiplier(self, engagement_rate: float, baseline: ChannelBaseline) -> float:
        """Рассчитывает во сколько раз engagement выше медианы канала."""
        if baseline.median_engagement_rate <= 0:
            return 1.0

        return engagement_rate / baseline.median_engagement_rate

    def _calculate_viral_score(self, zscore: float, median_multiplier: float, post: Dict[str, Any]) -> float:
        """
        Рассчитывает итоговую оценку "залетевшести" поста.

        Формула: 0.4 * Z-score + 0.4 * (median_multiplier - 1) + 0.2 * scale_factor
        """
        # Z-score компонент (макс 5.0)
        zscore_component = min(abs(zscore) / 3.0, 5.0)

        # Median multiplier компонент (макс 4.0)
        median_component = min(max(median_multiplier - 1.0, 0), 4.0)

        # Scale компонент - учитывает размер поста (макс 1.0)
        views = post.get('views', 0)
        scale_component = min(views / 10000, 1.0)  # Нормализуем на 10k просмотров

        viral_score = (
            0.4 * zscore_component +
            0.4 * median_component +
            0.2 * scale_component
        )

        return round(viral_score, 2)

    def _is_post_viral(self, viral_score: float, zscore: float, median_multiplier: float,
                      post: Dict[str, Any], baseline: ChannelBaseline) -> bool:
        """Определяет, является ли пост 'залетевшим'."""
        # Проверяем минимальный viral_score
        if viral_score < self.settings.get('min_viral_score', 1.0):
            return False

        # Проверяем Z-score
        if zscore < self.settings.get('min_zscore', 1.0):
            return False

        # Проверяем превышение медианы
        if median_multiplier < self.settings.get('min_median_multiplier', 1.5):
            return False

        # Проверяем минимальные просмотры
        views = post.get('views', 0)
        subscribers_count = getattr(baseline, 'subscribers_count', 0) or 0
        if isinstance(subscribers_count, str):
            try:
                subscribers_count = int(subscribers_count)
            except:
                subscribers_count = 0

        min_views = max(100, int(subscribers_count * self.settings.get('min_views_percentile', 0.001)))
        if views < min_views:
            return False

        return True

    def _get_virality_reasons(self, is_viral: bool, viral_score: float, zscore: float, median_multiplier: float) -> List[str]:
        """Формирует список причин 'залетевшести' или отсутствия."""
        reasons = []

        min_viral_score = self.settings.get('min_viral_score', 1.0)
        min_zscore = self.settings.get('min_zscore', 1.0)
        min_median_multiplier = self.settings.get('min_median_multiplier', 1.5)

        if is_viral:
            if viral_score >= min_viral_score:
                reasons.append(f"Высокий viral_score: {viral_score:.2f}")
            if zscore >= min_zscore:
                reasons.append(f"Высокий Z-score: {zscore:.2f}")
            if median_multiplier >= min_median_multiplier:
                reasons.append(f"Превышение медианы: {median_multiplier:.1f}x")
        else:
            if viral_score < min_viral_score:
                reasons.append(f"Низкий viral_score: {viral_score:.2f} < {min_viral_score}")
            if zscore < min_zscore:
                reasons.append(f"Низкий Z-score: {zscore:.2f} < {min_zscore}")
            if median_multiplier < min_median_multiplier:
                reasons.append(f"Низкое превышение медианы: {median_multiplier:.1f}x < {min_median_multiplier}")

        return reasons

    def detect_viral_posts(self, posts: List[Dict[str, Any]], channel_username: str) -> List[ViralPostResult]:
        """
        Анализирует список постов на 'залетевшесть'.

        Args:
            posts: Список постов для анализа
            channel_username: Username канала

        Returns:
            Список результатов анализа
        """
        # Получаем базовые метрики канала
        baseline = self.baseline_analyzer.get_channel_baseline(channel_username)

        if not baseline:
            logger.warning(f"Нет базовых метрик для канала {channel_username}")
            # Возвращаем результаты без анализа
            return [
                ViralPostResult(
                    post_id=post.get('id', f"{post.get('message_id', 'unknown')}_{channel_username}"),
                    is_viral=False,
                    viral_score=0,
                    engagement_rate=0,
                    zscore=0,
                    median_multiplier=0,
                    reasons=["Нет базовых метрик канала"]
                )
                for post in posts
            ]

        results = []
        for post in posts:
            # Проверяем, что post является словарем
            if not isinstance(post, dict):
                logger.error(f"Post is not a dict, it's {type(post)}: {post}")
                continue

            result = self.analyze_post_virality(post, baseline)
            results.append(result)

        viral_count = sum(1 for r in results if r.is_viral)
        logger.info(f"Найдено {viral_count} 'залетевших' постов из {len(results)}")

        return results

    def update_post_viral_metrics(self, post_id: str, result: ViralPostResult) -> bool:
        """
        Обновляет метрики 'залетевшести' поста в БД.

        Args:
            post_id: ID поста
            result: Результат анализа

        Returns:
            True если обновление успешно
        """
        try:
            update_data = {
                'viral_score': result.viral_score,
                'engagement_rate': result.engagement_rate,
                'zscore': result.zscore,
                'median_multiplier': result.median_multiplier,
                'last_viral_calculation': datetime.now().isoformat()
            }

            self.baseline_analyzer.supabase.client.table('posts').update(
                update_data
            ).eq('id', post_id).execute()

            logger.debug(f"Обновлены метрики поста {post_id}: viral_score={result.viral_score}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при обновлении метрик поста {post_id}: {e}")
            return False
