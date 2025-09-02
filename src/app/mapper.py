"""
Модуль для сопоставления сообщений с рубриками контент-плана.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import re

from .settings import settings
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)


class ContentMapper:
    """Класс для сопоставления контента с рубриками."""
    
    def __init__(self, content_plan: Optional[Dict[str, Any]] = None):
        """
        Инициализирует маппер контента.
        
        Args:
            content_plan: План контента с рубриками.
        """
        # Загружаем план контента из конфигурации или используем переданный
        if content_plan is None:
            self.content_plan = settings.load_content_plan()
        else:
            self.content_plan = content_plan
        
        # Извлекаем рубрики и ограничения
        self.rubrics = self.content_plan.get("rubrics", [])
        self.constraints = self.content_plan.get("constraints", {})
        
        logger.info(f"Загружено {len(self.rubrics)} рубрик из плана контента")
    
    def map_message_to_rubrics(self, message: Dict[str, Any]) -> List[str]:
        """
        Сопоставляет сообщение с рубриками на основе эвристик.
        
        Args:
            message: Сообщение для анализа.
            
        Returns:
            Список идентификаторов подходящих рубрик.
        """
        
        text = message.get("text", "").lower()
        if not text:
            return []
        
        matching_rubrics = set()
        
        # Проходим по всем рубрикам и проверяем ключевые слова
        for rubric in self.rubrics:
            rubric_id = rubric.get("id")
            examples = rubric.get("examples", [])
            
            # Проверяем наличие ключевых слов в тексте
            for example in examples:
                if example.lower() in text:
                    matching_rubrics.add(rubric_id)
                    break
        
        return list(matching_rubrics)
    
    def map_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Сопоставляет все сообщения с рубриками.
        
        Args:
            messages: Список сообщений для анализа.
            
        Returns:
            Обновленный список сообщений с добавленными рубриками.
        """
        
        for message in messages:
            # Сопоставляем сообщение с рубриками
            rubrics = self.map_message_to_rubrics(message)
            
            # Добавляем рубрики в сообщение
            message["rubrics"] = rubrics
            message["rubrics_count"] = len(rubrics)
            
            # Добавляем названия рубрик для удобства
            rubric_names = []
            for rubric_id in rubrics:
                for rubric in self.rubrics:
                    if rubric.get("id") == rubric_id:
                        rubric_names.append(rubric.get("name"))
                        break
            
            message["rubric_names"] = rubric_names
        
        return messages
    
    def get_rubric_details(self, rubric_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о рубрике по её идентификатору.
        
        Args:
            rubric_id: Идентификатор рубрики.
            
        Returns:
            Словарь с информацией о рубрике или None, если рубрика не найдена.
        """
        
        for rubric in self.rubrics:
            if rubric.get("id") == rubric_id:
                return rubric
        
        return None
    
    def get_all_rubrics(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех рубрик.
        
        Returns:
            Список рубрик.
        """
        
        return self.rubrics
