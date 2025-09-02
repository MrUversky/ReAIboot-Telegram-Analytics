"""
Новая LLM архитектура для ReAIboot.
Поддерживает 3-этапную обработку: фильтрация → анализ → генерация.
"""

from .base_processor import BaseLLMProcessor
from .filter_processor import FilterProcessor
from .analysis_processor import AnalysisProcessor
from .generator_processor import GeneratorProcessor
from .orchestrator import LLMOrchestrator

__all__ = [
    'BaseLLMProcessor',
    'FilterProcessor',
    'AnalysisProcessor',
    'GeneratorProcessor',
    'LLMOrchestrator'
]
