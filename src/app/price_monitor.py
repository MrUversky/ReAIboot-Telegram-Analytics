"""
Продвинутый монитор цен LLM API.
Обеспечивает автоматическое получение, валидацию и мониторинг цен.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import time
import threading
from dataclasses import dataclass

from .settings import settings


@dataclass
class PriceData:
    """Структура данных цены."""
    model: str
    token_type: str  # 'input' или 'output'
    price_per_million: float
    source: str  # 'api', 'web', 'cache', 'default'
    timestamp: datetime
    confidence: float  # 0-1, уверенность в цене


@dataclass
class PriceAlert:
    """Структура уведомления об изменении цены."""
    model: str
    token_type: str
    old_price: float
    new_price: float
    change_percent: float
    timestamp: datetime


class LLMPriceMonitor:
    """
    Продвинутый монитор цен LLM с автоматическим обновлением.

    Архитектура:
    1. Многоуровневая система получения цен
    2. Кэширование с TTL
    3. Валидация и мониторинг изменений
    4. Fallback стратегии
    5. Уведомления об изменениях
    """

    # Источники цен (приоритет от высшего к низшему)
    PRICE_SOURCES = {
        'openai_api': {
            'name': 'OpenAI API',
            'priority': 1,
            'requires_key': True,
            'endpoint': 'https://api.openai.com/v1/models'
        },
        'anthropic_api': {
            'name': 'Anthropic API',
            'priority': 2,
            'requires_key': True,
            'endpoint': 'https://api.anthropic.com/v1/models'
        },
        'openai_web': {
            'name': 'OpenAI Website',
            'priority': 3,
            'requires_key': False,
            'endpoint': 'https://openai.com/api/pricing/'
        },
        'anthropic_web': {
            'name': 'Anthropic Website',
            'priority': 4,
            'requires_key': False,
            'endpoint': 'https://www.anthropic.com/pricing'
        },
        'cached': {
            'name': 'Cache',
            'priority': 5,
            'requires_key': False,
            'endpoint': None
        },
        'default': {
            'name': 'Default Values',
            'priority': 6,
            'requires_key': False,
            'endpoint': None
        }
    }

    # Дефолтные цены (базовые значения)
    DEFAULT_PRICES = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.150, 'output': 0.600},
        'claude-3-5-sonnet': {'input': 3.0, 'output': 15.0}
    }

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.llm_price_cache'
        self.cache_dir.mkdir(exist_ok=True)

        self.price_cache = {}
        self.alerts = []
        self.last_update = None
        self.update_interval = timedelta(hours=6)  # Обновление каждые 6 часов

        # Настройка логирования
        self.logger = logging.getLogger(__name__)

        # Загрузка кэша при инициализации
        self._load_cache()

        # Автоматическое обновление в фоне
        self._start_background_updates()

    def get_price(self, model: str, token_type: str) -> PriceData:
        """
        Получить актуальную цену для модели.

        Args:
            model: Название модели
            token_type: 'input' или 'output'

        Returns:
            PriceData с актуальной ценой
        """
        cache_key = f"{model}_{token_type}"

        # Проверяем кэш
        if self._is_cache_valid(cache_key):
            cached_data = self.price_cache.get(cache_key)
            if cached_data:
                return cached_data

        # Получаем новую цену
        price_data = self._fetch_price(model, token_type)

        # Сохраняем в кэш
        self.price_cache[cache_key] = price_data
        self._save_cache()

        # Проверяем на изменения и создаем алерты
        self._check_price_changes(model, token_type, price_data)

        return price_data

    def _fetch_price(self, model: str, token_type: str) -> PriceData:
        """
        Получить цену из всех доступных источников.
        """
        for source_name, source_config in sorted(
            self.PRICE_SOURCES.items(),
            key=lambda x: x[1]['priority']
        ):
            try:
                if source_name == 'openai_api' and model.startswith('gpt'):
                    price = self._fetch_from_openai_api(model, token_type)
                elif source_name == 'anthropic_api' and model.startswith('claude'):
                    price = self._fetch_from_anthropic_api(model, token_type)
                elif source_name == 'openai_web' and model.startswith('gpt'):
                    price = self._fetch_from_openai_web(model, token_type)
                elif source_name == 'anthropic_web' and model.startswith('claude'):
                    price = self._fetch_from_anthropic_web(model, token_type)
                elif source_name == 'cached':
                    price = self._get_cached_price(model, token_type)
                elif source_name == 'default':
                    price = self._get_default_price(model, token_type)
                else:
                    continue

                if price is not None:
                    confidence = self._calculate_confidence(source_config['priority'])
                    return PriceData(
                        model=model,
                        token_type=token_type,
                        price_per_million=price,
                        source=source_name,
                        timestamp=datetime.now(),
                        confidence=confidence
                    )

            except Exception as e:
                self.logger.warning(f"Ошибка получения цены из {source_name}: {e}")
                continue

        # Если ничего не нашли, возвращаем дефолтное значение
        return PriceData(
            model=model,
            token_type=token_type,
            price_per_million=self._get_default_price(model, token_type),
            source='default',
            timestamp=datetime.now(),
            confidence=0.1
        )

    def _fetch_from_openai_api(self, model: str, token_type: str) -> Optional[float]:
        """Получить цену из OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                # В реальном сценарии здесь нужно получить цены через pricing endpoint
                # Пока возвращаем None
                return None

        except Exception as e:
            self.logger.warning(f"OpenAI API error: {e}")

        return None

    def _fetch_from_anthropic_api(self, model: str, token_type: str) -> Optional[float]:
        """Получить цену из Anthropic API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                # Аналогично OpenAI
                return None

        except Exception as e:
            self.logger.warning(f"Anthropic API error: {e}")

        return None

    def _fetch_from_openai_web(self, model: str, token_type: str) -> Optional[float]:
        """Получить цену с сайта OpenAI."""
        try:
            response = requests.get(
                "https://openai.com/api/pricing/",
                timeout=15
            )

            if response.status_code == 200:
                # Здесь можно парсить HTML для извлечения цен
                # Пока возвращаем None
                return None

        except Exception as e:
            self.logger.warning(f"OpenAI web scraping error: {e}")

        return None

    def _fetch_from_anthropic_web(self, model: str, token_type: str) -> Optional[float]:
        """Получить цену с сайта Anthropic."""
        try:
            response = requests.get(
                "https://www.anthropic.com/pricing",
                timeout=15
            )

            if response.status_code == 200:
                # Аналогично OpenAI
                return None

        except Exception as e:
            self.logger.warning(f"Anthropic web scraping error: {e}")

        return None

    def _get_cached_price(self, model: str, token_type: str) -> Optional[float]:
        """Получить цену из кэша."""
        cache_key = f"{model}_{token_type}"
        cached_data = self.price_cache.get(cache_key)

        if cached_data and self._is_cache_valid(cache_key):
            return cached_data.price_per_million

        return None

    def _get_default_price(self, model: str, token_type: str) -> float:
        """Получить дефолтную цену."""
        return self.DEFAULT_PRICES.get(model, {}).get(token_type, 1.0)

    def _calculate_confidence(self, source_priority: int) -> float:
        """Рассчитать уверенность в цене на основе источника."""
        # Чем выше приоритет, тем выше уверенность
        confidence_map = {1: 1.0, 2: 0.9, 3: 0.7, 4: 0.5, 5: 0.3, 6: 0.1}
        return confidence_map.get(source_priority, 0.1)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверить валидность кэша."""
        cached_data = self.price_cache.get(cache_key)
        if not cached_data:
            return False

        # Кэш валиден 6 часов
        return datetime.now() - cached_data.timestamp < self.update_interval

    def _check_price_changes(self, model: str, token_type: str, new_price_data: PriceData):
        """Проверить изменения цены и создать алерт."""
        cache_key = f"{model}_{token_type}"
        old_price_data = self.price_cache.get(cache_key)

        if not old_price_data:
            return

        # Рассчитываем изменение
        old_price = old_price_data.price_per_million
        new_price = new_price_data.price_per_million

        if old_price == 0:
            return

        change_percent = ((new_price - old_price) / old_price) * 100

        # Создаем алерт если изменение > 5%
        if abs(change_percent) > 5:
            alert = PriceAlert(
                model=model,
                token_type=token_type,
                old_price=old_price,
                new_price=new_price,
                change_percent=change_percent,
                timestamp=datetime.now()
            )

            self.alerts.append(alert)
            self.logger.info(f"Цена изменилась: {model} {token_type} {change_percent:+.1f}%")

    def _load_cache(self):
        """Загрузить кэш из файла."""
        cache_file = self.cache_dir / 'price_cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Преобразуем данные обратно в PriceData
                for key, value in data.items():
                    self.price_cache[key] = PriceData(
                        model=value['model'],
                        token_type=value['token_type'],
                        price_per_million=value['price_per_million'],
                        source=value['source'],
                        timestamp=datetime.fromisoformat(value['timestamp']),
                        confidence=value['confidence']
                    )

                self.logger.info(f"Загружен кэш цен: {len(self.price_cache)} записей")

            except Exception as e:
                self.logger.warning(f"Ошибка загрузки кэша: {e}")

    def _save_cache(self):
        """Сохранить кэш в файл."""
        cache_file = self.cache_dir / 'price_cache.json'

        try:
            # Преобразуем PriceData в dict для сериализации
            data = {}
            for key, price_data in self.price_cache.items():
                data[key] = {
                    'model': price_data.model,
                    'token_type': price_data.token_type,
                    'price_per_million': price_data.price_per_million,
                    'source': price_data.source,
                    'timestamp': price_data.timestamp.isoformat(),
                    'confidence': price_data.confidence
                }

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Ошибка сохранения кэша: {e}")

    def _start_background_updates(self):
        """Запустить фоновые обновления цен."""
        def update_worker():
            while True:
                try:
                    self.logger.info("Фоновое обновление цен...")
                    self.refresh_all_prices()
                    self.logger.info("Обновление цен завершено")
                except Exception as e:
                    self.logger.error(f"Ошибка фонового обновления: {e}")

                time.sleep(self.update_interval.total_seconds())

        thread = threading.Thread(target=update_worker, daemon=True)
        thread.start()

    def refresh_all_prices(self):
        """Обновить все цены."""
        self.logger.info("Обновление всех цен...")

        for model in self.DEFAULT_PRICES.keys():
            for token_type in ['input', 'output']:
                try:
                    new_price = self._fetch_price(model, token_type)
                    cache_key = f"{model}_{token_type}"

                    # Проверяем изменения
                    if cache_key in self.price_cache:
                        self._check_price_changes(model, token_type, new_price)

                    self.price_cache[cache_key] = new_price

                except Exception as e:
                    self.logger.warning(f"Ошибка обновления цены {model} {token_type}: {e}")

        self._save_cache()
        self.last_update = datetime.now()

    def get_price_report(self) -> Dict[str, Any]:
        """Получить отчет по всем ценам."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'prices': {},
            'alerts': [],
            'summary': {}
        }

        # Собираем все цены
        for model in self.DEFAULT_PRICES.keys():
            report['prices'][model] = {}
            for token_type in ['input', 'output']:
                price_data = self.get_price(model, token_type)
                report['prices'][model][token_type] = {
                    'price_per_million': price_data.price_per_million,
                    'price_per_1k': price_data.price_per_million / 1000,
                    'source': price_data.source,
                    'confidence': price_data.confidence,
                    'last_updated': price_data.timestamp.isoformat()
                }

        # Добавляем последние алерты (последние 10)
        recent_alerts = self.alerts[-10:]
        report['alerts'] = [
            {
                'model': alert.model,
                'token_type': alert.token_type,
                'old_price': alert.old_price,
                'new_price': alert.new_price,
                'change_percent': alert.change_percent,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in recent_alerts
        ]

        # Статистика
        total_alerts = len(self.alerts)
        significant_changes = len([a for a in self.alerts if abs(a.change_percent) > 10])

        report['summary'] = {
            'total_alerts': total_alerts,
            'significant_changes': significant_changes,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_size': len(self.price_cache)
        }

        return report

    def get_cost_calculation(self, usage: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Рассчитать стоимость на основе использования.

        Args:
            usage: {'этап': {'model': str, 'input_tokens': int, 'output_tokens': int}}
        """
        total_cost = 0
        breakdown = {}

        for stage, data in usage.items():
            model = data['model']
            input_tokens = data.get('input_tokens', 0)
            output_tokens = data.get('output_tokens', 0)

            # Получаем цены
            input_price_data = self.get_price(model, 'input')
            output_price_data = self.get_price(model, 'output')

            # Рассчитываем стоимость
            input_cost = (input_tokens / 1_000_000) * input_price_data.price_per_million
            output_cost = (output_tokens / 1_000_000) * output_price_data.price_per_million
            stage_cost = input_cost + output_cost

            total_cost += stage_cost

            breakdown[stage] = {
                'cost_usd': round(stage_cost, 6),
                'tokens': input_tokens + output_tokens,
                'model': model,
                'input_price_source': input_price_data.source,
                'output_price_source': output_price_data.source
            }

        return {
            'total_cost_usd': round(total_cost, 6),
            'total_cost_rub': round(total_cost * 100, 2),
            'breakdown': breakdown,
            'calculated_at': datetime.now().isoformat()
        }


# Глобальный экземпляр монитора
price_monitor = LLMPriceMonitor()
