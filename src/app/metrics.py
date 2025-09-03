"""
Модуль для расчета метрик вовлеченности контента.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from dataclasses import dataclass

from .settings import settings
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)

@dataclass
class EngagementMetrics:
    """Класс для хранения метрик вовлеченности."""
    
    view_rate: float = 0.0
    reaction_rate: float = 0.0
    reply_rate: float = 0.0
    forward_rate: float = 0.0
    score: float = 0.0


class MetricsCalculator:
    """Класс для расчета метрик вовлеченности."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Инициализирует калькулятор метрик.
        
        Args:
            weights: Веса для расчета общего показателя вовлеченности.
        """
        # Загружаем веса из конфигурации или используем переданные
        if weights is None:
            self.weights = settings.load_score_weights()
        else:
            self.weights = weights
        
        logger.info(f"Используемые веса для расчета метрик: {self.weights}")
    
    def compute_metrics(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Рассчитывает метрики вовлеченности для списка сообщений.
        
        Args:
            messages: Список сообщений.
            
        Returns:
            Обновленный список сообщений с добавленными метриками.
        """
        
        for message in messages:
            metrics = self.compute_message_metrics(message)
            
            # Добавляем метрики в сообщение
            message["view_rate"] = metrics.view_rate
            message["reaction_rate"] = metrics.reaction_rate
            message["reply_rate"] = metrics.reply_rate
            message["forward_rate"] = metrics.forward_rate
            message["score"] = metrics.score
        
        # Сортируем сообщения по score в порядке убывания
        messages.sort(key=lambda x: x["score"], reverse=True)
        
        return messages
    
    def compute_message_metrics(self, message: Dict[str, Any]) -> EngagementMetrics:
        """
        Рассчитывает метрики вовлеченности для конкретного сообщения.
        
        Args:
            message: Сообщение для анализа.
            
        Returns:
            Объект с метриками вовлеченности.
        """
        
        # Извлекаем необходимые данные
        views = message.get("views", 0) or 0
        reactions = message.get("reactions", 0) or 0
        replies = message.get("replies", 0) or 0
        forwards = message.get("forwards", 0) or 0
        participants_count = message.get("participants_count", 0) or 0
        
        # Рассчитываем метрики
        metrics = EngagementMetrics()
        
        # Рассчитываем view_rate
        if participants_count > 0:
            metrics.view_rate = views / participants_count
        
        # Рассчитываем остальные метрики
        if views > 0:
            metrics.reaction_rate = reactions / views
            metrics.reply_rate = replies / views
            metrics.forward_rate = forwards / views
        
        # Рассчитываем общий score на основе весов
        metrics.score = self.compute_score(metrics)
        
        return metrics
    
    def compute_score(self, metrics: EngagementMetrics) -> float:
        """
        Рассчитывает общий показатель вовлеченности на основе отдельных метрик.
        
        Args:
            metrics: Метрики вовлеченности.
            
        Returns:
            Общий показатель вовлеченности (score).
        """
        
        score = (
            self.weights.get("view_rate", 0.1) * metrics.view_rate +
            self.weights.get("reaction_rate", 0.4) * metrics.reaction_rate +
            self.weights.get("reply_rate", 0.3) * metrics.reply_rate +
            self.weights.get("forward_rate", 0.2) * metrics.forward_rate
        )
        
        return score
    
    def get_top_overall(self, messages: List[Dict[str, Any]], top_n: int = 30) -> List[Dict[str, Any]]:
        """
        Возвращает топ N сообщений по общему рейтингу.
        
        Args:
            messages: Список сообщений с рассчитанными метриками.
            top_n: Количество лучших сообщений для выбора.
            
        Returns:
            Список лучших сообщений.
        """
        
        # Сортируем сообщения по score в порядке убывания
        sorted_messages = sorted(messages, key=lambda x: x["score"], reverse=True)
        
        # Выбираем топ N
        return sorted_messages[:top_n]
    
    def get_top_by_channel(self, messages: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Возвращает топ N сообщений для каждого канала.
        
        Args:
            messages: Список сообщений с рассчитанными метриками.
            top_n: Количество лучших сообщений для выбора из каждого канала.
            
        Returns:
            Список лучших сообщений из каждого канала.
        """
        
        # Создаем DataFrame для удобства группировки
        df = pd.DataFrame(messages)
        
        # Группируем по каналу и сортируем по score
        top_by_channel = []
        for channel_id, group in df.groupby("channel_username"):
            # Сортируем группу по score и выбираем top_n
            top_channel_messages = group.sort_values(by="score", ascending=False).head(top_n)
            top_by_channel.extend(top_channel_messages.to_dict("records"))
        
        # Сортируем итоговый список по score
        top_by_channel = sorted(top_by_channel, key=lambda x: x["score"], reverse=True)
        
        return top_by_channel
