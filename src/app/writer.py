"""
Модуль для записи результатов анализа в различные форматы (CSV, Markdown).
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from .settings import settings
from .utils import setup_logger

# Настройка логирования
logger = setup_logger(__name__)


class DataWriter:
    """Класс для записи данных в различные форматы."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Инициализирует объект для записи данных.
        
        Args:
            output_dir: Директория для сохранения файлов.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = settings.out_dir
        
        # Создаем директорию, если она не существует
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Инициализирован writer с директорией вывода: {self.output_dir}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, columns: Optional[List[str]] = None) -> str:
        """
        Сохраняет данные в CSV файл.
        
        Args:
            data: Список словарей с данными.
            filename: Имя файла без расширения.
            columns: Список колонок для включения в CSV.
            
        Returns:
            Путь к сохраненному файлу.
        """
        
        # Добавляем расширение .csv, если его нет
        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"
        
        filepath = self.output_dir / filename
        
        try:
            # Создаем DataFrame из данных
            df = pd.DataFrame(data)
            
            # Фильтруем колонки, если указаны
            if columns:
                # Проверяем, какие колонки существуют в данных
                existing_columns = [col for col in columns if col in df.columns]
                df = df[existing_columns]
            
            # Сохраняем в CSV
            df.to_csv(filepath, index=False, encoding="utf-8")
            
            logger.info(f"Данные сохранены в CSV: {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении CSV файла {filename}: {e}")
            return ""
    
    def save_scenarios_to_markdown(
        self,
        messages: List[Dict[str, Any]],
        scenarios: Dict[str, Any],
        filename: str = "scenarios.md"
    ) -> str:
        """
        Сохраняет сценарии в Markdown файл.
        
        Args:
            messages: Список сообщений с метриками.
            scenarios: Словарь со сценариями для сообщений.
            filename: Имя файла без расширения.
            
        Returns:
            Путь к сохраненному файлу.
        """
        
        # Добавляем расширение .md, если его нет
        if not filename.endswith(".md"):
            filename = f"{filename}.md"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Заголовок документа
                f.write("# Сценарии для контента\n\n")
                f.write("Сгенерированные идеи для контента на основе популярных постов из Telegram-каналов.\n\n")
                f.write("---\n\n")
                
                # Перебираем сообщения
                for i, message in enumerate(messages, 1):
                    message_id = message.get("message_id")
                    channel_title = message.get("channel_title", "Неизвестный канал")
                    score = message.get("score", 0)
                    text_preview = message.get("text_preview", "")
                    permalink = message.get("permalink", "#")
                    rubric_names = message.get("rubric_names", [])
                    
                    # Заголовок сообщения
                    f.write(f"## {i}. {channel_title}\n\n")
                    
                    # Метаданные
                    f.write(f"- **Источник**: [{channel_title}]({permalink})\n")
                    f.write(f"- **Score**: {score:.4f}\n")
                    if rubric_names:
                        f.write(f"- **Рубрики**: {', '.join(rubric_names)}\n")
                    f.write("\n")
                    
                    # Превью текста
                    f.write("### Исходный пост\n\n")
                    f.write(f"{text_preview}\n\n")
                    
                    # Сценарии
                    f.write("### Сценарии\n\n")
                    
                    # Получаем сценарии для текущего сообщения
                    message_scenarios = scenarios.get(str(message_id), {})
                    
                    if not message_scenarios:
                        f.write("*Сценарии не сгенерированы для этого сообщения.*\n\n")
                        continue
                    
                    # Проверяем формат сценариев
                    if "raw" in message_scenarios:
                        # Если ответ не в формате JSON, выводим как есть
                        f.write("```\n")
                        f.write(message_scenarios["raw"])
                        f.write("\n```\n\n")
                    elif "error" in message_scenarios:
                        # Если произошла ошибка
                        f.write(f"*Ошибка при генерации сценариев: {message_scenarios['error']}*\n\n")
                    elif "scenarios" in message_scenarios:
                        # Если есть правильно сформированные сценарии
                        for scenario in message_scenarios["scenarios"]:
                            duration = scenario.get("duration", "")
                            hook = scenario.get("hook", "")
                            insight = scenario.get("insight", "")
                            cta = scenario.get("cta", "")
                            beats = scenario.get("beats", [])
                            captions = scenario.get("captions", [])
                            hashtags = scenario.get("hashtags", [])
                            
                            f.write(f"#### Сценарий {duration} сек\n\n")
                            f.write(f"**Hook:** {hook}\n\n")
                            f.write(f"**Insight:** {insight}\n\n")
                            
                            f.write("**Beats:**\n\n")
                            for j, beat in enumerate(beats, 1):
                                f.write(f"{j}. {beat}\n")
                            f.write("\n")
                            
                            f.write(f"**CTA:** {cta}\n\n")
                            
                            f.write("**Варианты подписей:**\n\n")
                            for j, caption in enumerate(captions, 1):
                                f.write(f"Вариант {j}:\n")
                                f.write(f"> {caption}\n\n")
                            
                            if hashtags:
                                f.write("**Хэштеги:** ")
                                f.write(" ".join(hashtags))
                                f.write("\n\n")
                    else:
                        # Если формат не соответствует ожиданиям
                        f.write("*Некорректный формат сценариев.*\n\n")
                        f.write("```json\n")
                        f.write(json.dumps(message_scenarios, ensure_ascii=False, indent=2))
                        f.write("\n```\n\n")
                    
                    # Разделитель между сообщениями
                    f.write("---\n\n")
            
            logger.info(f"Сценарии сохранены в Markdown: {filepath}")
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении Markdown файла {filename}: {e}")
            return ""
    
    def save_all_data(
        self,
        all_messages: List[Dict[str, Any]],
        top_overall: List[Dict[str, Any]],
        top_by_channel: List[Dict[str, Any]],
        scenarios: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Сохраняет все данные в соответствующие файлы.
        
        Args:
            all_messages: Все сообщения с метриками.
            top_overall: Лучшие сообщения по общему рейтингу.
            top_by_channel: Лучшие сообщения для каждого канала.
            scenarios: Словарь со сценариями для сообщений.
            
        Returns:
            Словарь с путями к сохраненным файлам.
        """
        
        result = {}
        
        # Основные колонки для CSV
        csv_columns = [
            "channel_title", "channel_username", "message_id", "date", "date_local",
            "text_preview", "views", "forwards", "replies", "reactions",
            "participants_count", "has_media", "permalink",
            "view_rate", "reaction_rate", "reply_rate", "forward_rate", "score",
            "rubrics", "rubric_names"
        ]
        
        # Сохраняем все сообщения
        all_messages_path = self.save_to_csv(
            all_messages,
            "all_messages.csv",
            columns=csv_columns
        )
        result["all_messages"] = all_messages_path
        
        # Сохраняем лучшие сообщения по общему рейтингу
        top_overall_path = self.save_to_csv(
            top_overall,
            "top_overall.csv",
            columns=csv_columns
        )
        result["top_overall"] = top_overall_path
        
        # Сохраняем лучшие сообщения по каналам
        top_by_channel_path = self.save_to_csv(
            top_by_channel,
            "top_by_channel.csv",
            columns=csv_columns
        )
        result["top_by_channel"] = top_by_channel_path
        
        # Сохраняем сценарии, если они есть
        if scenarios:
            scenarios_path = self.save_scenarios_to_markdown(
                top_overall,
                scenarios,
                "scenarios.md"
            )
            result["scenarios"] = scenarios_path
        
        return result
