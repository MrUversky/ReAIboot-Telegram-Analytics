"""
Тесты для модуля расчета метрик.
"""

import unittest
import json
import os
from pathlib import Path
import sys

# Добавляем родительскую директорию в sys.path для импорта модулей приложения
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.metrics import MetricsCalculator, EngagementMetrics


class TestMetricsCalculator(unittest.TestCase):
    """Тесты для класса MetricsCalculator."""
    
    def setUp(self):
        """Подготовка к тестированию."""
        
        # Загружаем тестовые данные
        fixtures_path = Path(__file__).parent / "fixtures_sample.json"
        
        with open(fixtures_path, "r", encoding="utf-8") as f:
            self.test_messages = json.load(f)
        
        # Создаем экземпляр калькулятора с тестовыми весами
        self.test_weights = {
            "view_rate": 0.1,
            "reaction_rate": 0.4,
            "reply_rate": 0.3,
            "forward_rate": 0.2
        }
        
        self.calculator = MetricsCalculator(weights=self.test_weights)
    
    def test_compute_message_metrics(self):
        """Тестирование расчета метрик для отдельного сообщения."""
        
        # Тестируем первое сообщение из набора данных
        message = self.test_messages[0]
        
        # Рассчитываем метрики
        metrics = self.calculator.compute_message_metrics(message)
        
        # Проверяем тип результата
        self.assertIsInstance(metrics, EngagementMetrics)
        
        # Проверяем значения метрик
        # view_rate = views / participants_count = 5000 / 10000 = 0.5
        self.assertAlmostEqual(metrics.view_rate, 0.5)
        
        # reaction_rate = reactions / views = 200 / 5000 = 0.04
        self.assertAlmostEqual(metrics.reaction_rate, 0.04)
        
        # reply_rate = replies / views = 50 / 5000 = 0.01
        self.assertAlmostEqual(metrics.reply_rate, 0.01)
        
        # forward_rate = forwards / views = 100 / 5000 = 0.02
        self.assertAlmostEqual(metrics.forward_rate, 0.02)
        
        # score = 0.1*0.5 + 0.4*0.04 + 0.3*0.01 + 0.2*0.02 = 0.05 + 0.016 + 0.003 + 0.004 = 0.073
        expected_score = (
            self.test_weights["view_rate"] * metrics.view_rate +
            self.test_weights["reaction_rate"] * metrics.reaction_rate +
            self.test_weights["reply_rate"] * metrics.reply_rate +
            self.test_weights["forward_rate"] * metrics.forward_rate
        )
        self.assertAlmostEqual(metrics.score, expected_score)
    
    def test_compute_score(self):
        """Тестирование расчета общего score на основе метрик."""
        
        # Создаем тестовый объект метрик
        metrics = EngagementMetrics(
            view_rate=0.5,
            reaction_rate=0.04,
            reply_rate=0.01,
            forward_rate=0.02
        )
        
        # Рассчитываем score
        score = self.calculator.compute_score(metrics)
        
        # Проверяем результат
        expected_score = (
            self.test_weights["view_rate"] * metrics.view_rate +
            self.test_weights["reaction_rate"] * metrics.reaction_rate +
            self.test_weights["reply_rate"] * metrics.reply_rate +
            self.test_weights["forward_rate"] * metrics.forward_rate
        )
        self.assertAlmostEqual(score, expected_score)
    
    def test_compute_metrics(self):
        """Тестирование расчета метрик для списка сообщений."""
        
        # Рассчитываем метрики для всех тестовых сообщений
        messages_with_metrics = self.calculator.compute_metrics(self.test_messages)
        
        # Проверяем, что все сообщения имеют необходимые метрики
        self.assertEqual(len(messages_with_metrics), len(self.test_messages))
        
        for message in messages_with_metrics:
            self.assertIn("view_rate", message)
            self.assertIn("reaction_rate", message)
            self.assertIn("reply_rate", message)
            self.assertIn("forward_rate", message)
            self.assertIn("score", message)
    
    def test_get_top_overall(self):
        """Тестирование выбора лучших сообщений по общему рейтингу."""
        
        # Рассчитываем метрики для всех тестовых сообщений
        messages_with_metrics = self.calculator.compute_metrics(self.test_messages)
        
        # Выбираем топ-3 сообщения
        top_3 = self.calculator.get_top_overall(messages_with_metrics, top_n=3)
        
        # Проверяем, что выбрано правильное количество сообщений
        self.assertEqual(len(top_3), 3)
        
        # Проверяем, что сообщения отсортированы по убыванию score
        for i in range(len(top_3) - 1):
            self.assertGreaterEqual(top_3[i]["score"], top_3[i+1]["score"])
    
    def test_get_top_by_channel(self):
        """Тестирование выбора лучших сообщений для каждого канала."""
        
        # Рассчитываем метрики для всех тестовых сообщений
        messages_with_metrics = self.calculator.compute_metrics(self.test_messages)
        
        # Выбираем топ-1 сообщение для каждого канала
        top_by_channel = self.calculator.get_top_by_channel(messages_with_metrics, top_n=1)
        
        # Проверяем, что выбрано правильное количество сообщений
        # В тестовых данных у нас 3 различных канала, поэтому должно быть 3 сообщения
        self.assertEqual(len(top_by_channel), 3)
        
        # Проверяем, что сообщения от разных каналов
        channel_ids = set(message["channel_id"] for message in top_by_channel)
        self.assertEqual(len(channel_ids), 3)


if __name__ == "__main__":
    unittest.main()
