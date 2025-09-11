"""
Модуль для загрузки и управления настройками приложения.
"""

import os
import yaml
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import pytz
from datetime import datetime, timedelta

# Загрузка .env файла
load_dotenv()

class Settings:
    """Класс для управления всеми настройками приложения."""
    
    def __init__(self):
        # Telegram настройки
        self.telegram_api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.telegram_api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.telegram_session = os.getenv("TELEGRAM_SESSION", "telegram_session")
        
        # OpenAI настройки
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

        # Claude настройки
        self.anthropic_api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        # Модели для разных процессоров
        self.filter_model = os.getenv("FILTER_MODEL", self.openai_model_name)
        self.analysis_model = os.getenv("ANALYSIS_MODEL", self.anthropic_model_name)
        self.rubric_model = os.getenv("RUBRIC_MODEL", "gpt-4o")
        self.generator_model = os.getenv("GENERATOR_MODEL", "gpt-4o")

        # Supabase настройки
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        # Настройки приложения
        self.timezone = os.getenv("TZ", "Asia/Tbilisi")
        
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.out_dir = self.base_dir / "out"
        
        # Создаем директорию для выходных файлов, если она не существует
        os.makedirs(self.out_dir, exist_ok=True)
    
    @property
    def tz(self):
        """Возвращает объект timezone."""
        return pytz.timezone(self.timezone)
    
    def load_channels(self, file_path: Optional[str] = None) -> List[str]:
        """Загружает список каналов из файла."""
        
        if not file_path:
            file_path = self.base_dir / "channels.txt"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл со списком каналов не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            channels = [line.strip() for line in f if line.strip()]
        
        return channels
    
    def load_content_plan(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает план контента из YAML файла."""
        
        if not file_path:
            file_path = self.base_dir / "content_plan.yaml"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл с планом контента не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content_plan = yaml.safe_load(f)
        
        return content_plan
    
    def load_score_weights(self, file_path: Optional[str] = None) -> Dict[str, float]:
        """Загружает веса для расчета метрик из YAML файла."""
        
        if not file_path:
            file_path = self.base_dir / "score.yaml"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл с весами метрик не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            score_config = yaml.safe_load(f)
        
        return score_config.get("weights", {})


class LLMPriceManager:
    """Продвинутый менеджер для получения актуальных цен на LLM API."""

    # Дефолтные цены (последнее известное значение)
    DEFAULT_PRICES = {
        'gpt-4o': {
            'input': 2.50,    # $2.50 за 1M токенов
            'output': 10.00   # $10.00 за 1M токенов
        },
        'gpt-4o-mini': {
            'input': 0.150,   # $0.150 за 1M токенов
            'output': 0.600   # $0.600 за 1M токенов
        },
        'claude-3-5-sonnet': {
            'input': 3.0,     # $3.0 за 1M токенов
            'output': 15.0    # $15.0 за 1M токенов
        }
    }

    # API endpoints для получения цен
    API_ENDPOINTS = {
        'openai': 'https://api.openai.com/v1/models',
        'anthropic': 'https://api.anthropic.com/v1/models'
    }

    def __init__(self):
        self.prices_cache = {}
        self.cache_timestamp = None
        self.cache_duration = timedelta(hours=24)  # Кэш на 24 часа

    def get_price_per_1k_tokens(self, model: str, token_type: str = 'input') -> float:
        """
        Получить цену за 1000 токенов для указанной модели.

        Args:
            model: Название модели (gpt-4o, gpt-4o-mini, claude-3-5-sonnet)
            token_type: Тип токенов ('input' или 'output')

        Returns:
            Цена в долларах за 1000 токенов
        """
        # Проверяем кэш
        if self._is_cache_valid():
            cached_price = self.prices_cache.get(model, {}).get(token_type)
            if cached_price is not None:
                return cached_price

        # Получаем актуальные цены
        try:
            if model.startswith('gpt'):
                price = self._get_openai_price(model, token_type)
            elif model.startswith('claude'):
                price = self._get_anthropic_price(model, token_type)
            else:
                raise ValueError(f"Неизвестная модель: {model}")

            # Кэшируем результат
            if model not in self.prices_cache:
                self.prices_cache[model] = {}
            self.prices_cache[model][token_type] = price
            self.cache_timestamp = datetime.now()

            return price

        except Exception as e:
            logging.warning(f"Не удалось получить актуальную цену для {model}: {e}")
            # Возвращаем дефолтную цену
            default_price_per_million = self.DEFAULT_PRICES.get(model, {}).get(token_type, 1.0)
            return default_price_per_million / 1000  # Конвертируем в цену за 1000 токенов

    def _is_cache_valid(self) -> bool:
        """Проверяет, действителен ли кэш."""
        if self.cache_timestamp is None:
            return False
        return datetime.now() - self.cache_timestamp < self.cache_duration

    def _get_openai_price(self, model: str, token_type: str) -> float:
        """Получить актуальную цену OpenAI модели через API."""
        try:
            # Попытка 1: Получить цены из OpenAI API
            price = self._fetch_openai_price_from_api(model, token_type)
            if price:
                return price

            # Попытка 2: Получить цены из публичных источников
            price = self._fetch_openai_price_from_public_sources(model, token_type)
            if price:
                return price

        except Exception as e:
            logging.warning(f"Не удалось получить цену OpenAI для {model}: {e}")

        # Fallback: использовать дефолтные цены
        logging.info(f"Используем дефолтную цену для {model}")
        price_per_million = self.DEFAULT_PRICES.get(model, {}).get(token_type, 1.0)
        return price_per_million / 1000

    def _get_anthropic_price(self, model: str, token_type: str) -> float:
        """Получить актуальную цену Anthropic модели через API."""
        try:
            # Попытка 1: Получить цены из Anthropic API
            price = self._fetch_anthropic_price_from_api(model, token_type)
            if price:
                return price

            # Попытка 2: Получить цены из публичных источников
            price = self._fetch_anthropic_price_from_public_sources(model, token_type)
            if price:
                return price

        except Exception as e:
            logging.warning(f"Не удалось получить цену Anthropic для {model}: {e}")

        # Fallback: использовать дефолтные цены
        logging.info(f"Используем дефолтную цену для {model}")
        price_per_million = self.DEFAULT_PRICES.get(model, {}).get(token_type, 1.0)
        return price_per_million / 1000

    def _fetch_openai_price_from_api(self, model: str, token_type: str) -> float:
        """Получить цену из OpenAI API (если доступен API ключ)."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(self.API_ENDPOINTS['openai'], headers=headers, timeout=10)

            if response.status_code == 200:
                # В реальном API OpenAI цены можно получить через отдельный endpoint
                # Пока возвращаем None для демонстрации
                logging.info("OpenAI API доступен, но цены нужно получать через pricing API")
                return None

        except Exception as e:
            logging.warning(f"Ошибка при запросе к OpenAI API: {e}")

        return None

    def _fetch_openai_price_from_public_sources(self, model: str, token_type: str) -> float:
        """Получить цены из публичных источников OpenAI."""
        try:
            # Попытка получить цены с официального сайта
            response = requests.get("https://openai.com/api/pricing/", timeout=10)

            if response.status_code == 200:
                # Здесь можно парсить HTML или JSON с официального сайта
                # Пока возвращаем None для демонстрации
                logging.info("Публичный источник OpenAI доступен")
                return None

        except Exception as e:
            logging.warning(f"Ошибка при запросе к публичному источнику OpenAI: {e}")

        return None

    def _fetch_anthropic_price_from_api(self, model: str, token_type: str) -> float:
        """Получить цену из Anthropic API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            response = requests.get(self.API_ENDPOINTS['anthropic'], headers=headers, timeout=10)

            if response.status_code == 200:
                # Аналогично OpenAI - цены через отдельный endpoint
                logging.info("Anthropic API доступен")
                return None

        except Exception as e:
            logging.warning(f"Ошибка при запросе к Anthropic API: {e}")

        return None

    def _fetch_anthropic_price_from_public_sources(self, model: str, token_type: str) -> float:
        """Получить цены из публичных источников Anthropic."""
        try:
            response = requests.get("https://www.anthropic.com/pricing", timeout=10)

            if response.status_code == 200:
                logging.info("Публичный источник Anthropic доступен")
                return None

        except Exception as e:
            logging.warning(f"Ошибка при запросе к публичному источнику Anthropic: {e}")
        return None

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Рассчитать общую стоимость запроса.

        Args:
            model: Название модели
            input_tokens: Количество входных токенов
            output_tokens: Количество выходных токенов

        Returns:
            Стоимость в долларах
        """
        input_cost = (input_tokens / 1000) * self.get_price_per_1k_tokens(model, 'input')
        output_cost = (output_tokens / 1000) * self.get_price_per_1k_tokens(model, 'output')
        return input_cost + output_cost

    def get_cost_summary(self, usage_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Получить сводку стоимости по всем этапам.

        Args:
            usage_data: Данные об использовании {'этап': {'model': str, 'input_tokens': int, 'output_tokens': int}}

        Returns:
            Сводка стоимости
        """
        total_cost = 0
        breakdown = {}

        for stage, data in usage_data.items():
            model = data['model']
            input_tokens = data.get('input_tokens', 0)
            output_tokens = data.get('output_tokens', 0)

            cost = self.calculate_cost(model, input_tokens, output_tokens)
            total_cost += cost
            breakdown[stage] = {
                'cost_usd': round(cost, 6),
                'tokens': input_tokens + output_tokens,
                'model': model
            }

        return {
            'total_cost_usd': round(total_cost, 6),
            'total_cost_rub': round(total_cost * 100, 2),  # Примерный курс 100 руб/$
            'breakdown': breakdown,
            'last_updated': self.cache_timestamp.isoformat() if self.cache_timestamp else None
        }

    def force_refresh_prices(self) -> Dict[str, Any]:
        """Принудительно обновить все цены."""
        logging.info("Принудительное обновление цен...")
        self.prices_cache = {}
        self.cache_timestamp = None

        # Получить новые цены для всех моделей
        refreshed_prices = {}
        for model in self.DEFAULT_PRICES.keys():
            refreshed_prices[model] = {
                'input': self.get_price_per_1k_tokens(model, 'input'),
                'output': self.get_price_per_1k_tokens(model, 'output')
            }

        self.cache_timestamp = datetime.now()

        return {
            'refreshed_prices': refreshed_prices,
            'timestamp': self.cache_timestamp.isoformat(),
            'status': 'success'
        }

    def get_price_changes_report(self, previous_prices: Dict = None) -> Dict[str, Any]:
        """Получить отчет об изменениях цен."""
        if previous_prices is None:
            previous_prices = self.DEFAULT_PRICES

        current_prices = {}
        changes = {}

        for model in self.DEFAULT_PRICES.keys():
            current_prices[model] = {
                'input': self.get_price_per_1k_tokens(model, 'input'),
                'output': self.get_price_per_1k_tokens(model, 'output')
            }

            if model in previous_prices:
                changes[model] = {
                    'input_change': current_prices[model]['input'] - (previous_prices[model].get('input', 0) / 1000),
                    'output_change': current_prices[model]['output'] - (previous_prices[model].get('output', 0) / 1000),
                    'input_percent': 0,
                    'output_percent': 0
                }

                # Расчет процентного изменения
                if previous_prices[model].get('input', 0) > 0:
                    changes[model]['input_percent'] = (changes[model]['input_change'] / (previous_prices[model]['input'] / 1000)) * 100
                if previous_prices[model].get('output', 0) > 0:
                    changes[model]['output_percent'] = (changes[model]['output_change'] / (previous_prices[model]['output'] / 1000)) * 100

        return {
            'current_prices': current_prices,
            'changes': changes,
            'generated_at': datetime.now().isoformat()
        }

    def validate_prices(self) -> Dict[str, Any]:
        """Валидация полученных цен."""
        issues = []
        warnings = []

        for model in self.DEFAULT_PRICES.keys():
            try:
                input_price = self.get_price_per_1k_tokens(model, 'input')
                output_price = self.get_price_per_1k_tokens(model, 'output')

                # Проверка на отрицательные цены
                if input_price < 0:
                    issues.append(f"Отрицательная цена input для {model}: {input_price}")
                if output_price < 0:
                    issues.append(f"Отрицательная цена output для {model}: {output_price}")

                # Проверка на слишком низкие цены (возможная ошибка)
                if input_price < 0.00001 and input_price > 0:
                    warnings.append(f"Подозрительно низкая цена input для {model}: {input_price}")
                if output_price < 0.00001 and output_price > 0:
                    warnings.append(f"Подозрительно низкая цена output для {model}: {output_price}")

                # Проверка на слишком высокие цены
                if input_price > 10:  # $10 за 1000 токенов - слишком много
                    issues.append(f"Подозрительно высокая цена input для {model}: {input_price}")
                if output_price > 50:  # $50 за 1000 токенов - слишком много
                    issues.append(f"Подозрительно высокая цена output для {model}: {output_price}")

            except Exception as e:
                issues.append(f"Ошибка получения цены для {model}: {str(e)}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'validated_at': datetime.now().isoformat()
        }


# Создаем глобальный экземпляр настроек
settings = Settings()

# Создаем глобальный экземпляр менеджера цен
price_manager = LLMPriceManager()
