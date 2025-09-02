"""
Модуль для работы с моделями машинного обучения (OpenAI API).
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
import asyncio

try:
    import openai
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .settings import settings
from .utils import setup_logger, is_valid_json_response

# Настройка логирования
logger = setup_logger(__name__)


class LLMProcessor:
    """Класс для работы с LLM через OpenAI API."""
    
    def __init__(self):
        """Инициализирует процессор LLM."""
        
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model_name = settings.openai_model_name
        
        # Проверяем доступность API ключа
        self.is_available = OPENAI_AVAILABLE and bool(self.api_key)
        
        if not OPENAI_AVAILABLE:
            logger.warning("Библиотека openai не установлена. LLM функции недоступны.")
        elif not self.api_key:
            logger.warning("OPENAI_API_KEY не задан в настройках. LLM функции недоступны.")
        else:
            # Инициализируем клиенты OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(f"LLM процессор инициализирован. Используемая модель: {self.model_name}")
    
    def is_llm_available(self) -> bool:
        """
        Проверяет доступность LLM.
        
        Returns:
            True, если LLM доступен, иначе False.
        """
        return self.is_available
    
    async def classify_message(self, message: Dict[str, Any], rubrics: List[Dict[str, Any]]) -> List[str]:
        """
        Классифицирует сообщение по рубрикам с использованием LLM.
        
        Args:
            message: Сообщение для классификации.
            rubrics: Список рубрик для классификации.
            
        Returns:
            Список идентификаторов подходящих рубрик.
        """
        
        if not self.is_available:
            logger.warning("LLM недоступен. Классификация не выполняется.")
            return []
        
        try:
            # Формируем информацию о рубриках
            rubrics_info = ""
            for idx, rubric in enumerate(rubrics, 1):
                rubrics_info += f"{idx}. {rubric.get('id')}: {rubric.get('name')} - {', '.join(rubric.get('examples', []))}\n"
            
            # Текст сообщения для анализа
            text = message.get("text", "")
            if not text:
                return []
            
            # Формируем запрос к LLM
            system_prompt = """Вы - алгоритм классификации контента. Вы анализируете текст поста и определяете, к каким рубрикам из заданного списка он относится.
Выберите до 3 наиболее релевантных рубрик. Оцените содержание, тему, стиль и формат поста.
Ответ должен быть только в JSON-формате: {"rubrics": ["rubric_id1", "rubric_id2"]}."""
            
            user_prompt = f"""Проанализируйте следующий пост и определите подходящие рубрики:

ПОСТ:
{text}

ДОСТУПНЫЕ РУБРИКИ:
{rubrics_info}

Выберите до 3 наиболее релевантных рубрик и верните ответ в формате JSON: {{"rubrics": ["rubric_id1", "rubric_id2", ...]}}"""
            
            # Отправляем запрос к API
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Извлекаем ответ
            result_text = response.choices[0].message.content
            
            # Пробуем распарсить JSON
            try:
                result_json = json.loads(result_text)
                if isinstance(result_json, dict) and "rubrics" in result_json:
                    return result_json["rubrics"]
            except json.JSONDecodeError:
                # Если ответ не в формате JSON, пытаемся извлечь идентификаторы рубрик из текста
                logger.warning(f"Не удалось распарсить JSON из ответа LLM: {result_text}")
                
                # Возвращаем пустой список в случае ошибки
                return []
            
            return []
        
        except Exception as e:
            logger.error(f"Ошибка при классификации сообщения через LLM: {e}")
            return []
    
    async def generate_scenarios(
        self, 
        message: Dict[str, Any], 
        rubric_id: str
    ) -> Dict[str, Any]:
        """
        Генерирует сценарии для Reels на основе сообщения.
        
        Args:
            message: Исходное сообщение.
            rubric_id: Идентификатор рубрики.
            
        Returns:
            Словарь со сценариями или пустой словарь в случае ошибки.
        """
        
        if not self.is_available:
            logger.warning("LLM недоступен. Генерация сценариев не выполняется.")
            return {}
        
        try:
            # Получаем текст сообщения
            text = message.get("text", "")
            if not text:
                return {}
            
            # Формируем запрос к LLM
            system_prompt = """Вы - креативный директор для социальных сетей. Ваша задача - создать сценарии для коротких видео Reels на основе предложенного текста.
Создайте три сценария разной длительности: 15, 30 и 45 секунд. 
Для каждого сценария напишите:
1. hook - цепляющее начало (1-2 предложения)
2. insight - ключевой инсайт (1-2 предложения)
3. beats[] - список точек для съемки/монтажа (3-6 пунктов)
4. cta - призыв к действию (1 предложение)
5. captions - 3 варианта подписи к видео (до 300 символов каждая)
6. hashtags - 5-8 релевантных хэштегов на русском языке

Ответ должен быть только в JSON-формате со следующей структурой:
{
  "scenarios": [
    {
      "duration": 15,
      "hook": "текст",
      "insight": "текст",
      "beats": ["шаг 1", "шаг 2", ...],
      "cta": "текст",
      "captions": ["вариант 1", "вариант 2", "вариант 3"],
      "hashtags": ["#тег1", "#тег2", ...]
    },
    // аналогично для 30 и 45 секунд
  ]
}"""
            
            user_prompt = f"""Создайте сценарии для Reels на основе этого поста в рубрике "{rubric_id}":

{text[:2000]}  # Ограничиваем текст до 2000 символов

Требования:
- Сценарии должны быть адаптированы к формату коротких видео
- Сохраняйте ключевые идеи и инсайты из исходного текста
- Добавляйте оригинальные элементы для привлечения внимания
- Используйте яркие, запоминающиеся хуки
- Делайте акцент на практическую пользу/инсайт
- Подписи должны быть короткими и емкими

Верните сценарии длительностью 15, 30 и 45 секунд в формате JSON."""
            
            # Отправляем запрос к API
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            # Извлекаем ответ
            result_text = response.choices[0].message.content
            
            # Пробуем распарсить JSON
            try:
                result_json = json.loads(result_text)
                if is_valid_json_response(result_json):
                    return result_json
                else:
                    # Если структура JSON не соответствует ожидаемой, оборачиваем в {"raw": ...}
                    return {"raw": result_text}
            except json.JSONDecodeError:
                # Если ответ не в формате JSON, оборачиваем в {"raw": ...}
                logger.warning(f"Не удалось распарсить JSON из ответа LLM: {result_text[:100]}...")
                return {"raw": result_text}
        
        except Exception as e:
            logger.error(f"Ошибка при генерации сценариев через LLM: {e}")
            return {"error": str(e)}
