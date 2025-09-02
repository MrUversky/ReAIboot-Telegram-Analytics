"""
Модуль для сбора данных из Telegram-каналов.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from tqdm import tqdm
import pytz

from .settings import settings
from .utils import setup_logger, normalize_channel_input
from .telegram_client import TelegramAnalyzer

# Настройка логирования
logger = setup_logger(__name__)

class MessageFetcher:
    """Класс для получения сообщений из каналов."""
    
    def __init__(self):
        """Инициализирует компонент для получения сообщений."""
        self.telegram = None
    
    async def __aenter__(self) -> "MessageFetcher":
        """Контекстный менеджер: вход."""
        self.telegram = TelegramAnalyzer()
        await self.telegram.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        if self.telegram:
            await self.telegram.disconnect()
    
    async def fetch_channels_data(
        self,
        channels: List[str],
        days: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получает данные из всех указанных каналов.
        
        Args:
            channels: Список каналов (имена или URL).
            days: Количество дней для анализа.
            limit: Максимальное количество сообщений для загрузки из канала.
            
        Returns:
            Список сообщений со всех каналов.
        """
        
        all_messages = []
        
        # Проверяем, что список каналов не пуст
        if not channels:
            logger.error("Список каналов пуст")
            return all_messages
        
        # Инициализируем клиент Telegram, если еще не сделано
        if not self.telegram:
            self.telegram = TelegramAnalyzer()
            await self.telegram.connect()
        
        # Обрабатываем каждый канал
        for channel in tqdm(channels, desc="Обработка каналов"):
            try:
                # Нормализуем входные данные канала
                normalized_channel = normalize_channel_input(channel)
                
                logger.info(f"Получение данных из канала: {normalized_channel}")
                
                # Получаем сообщения из канала
                channel_messages, channel_info = await self.telegram.get_messages(
                    normalized_channel,
                    days=days,
                    limit=limit
                )
                
                # Если возникла ошибка, переходим к следующему каналу
                if "error" in channel_info and not channel_messages:
                    logger.error(f"Ошибка при получении данных из канала {normalized_channel}: {channel_info['error']}")
                    continue
                
                # Добавляем сообщения из канала в общий список
                all_messages.extend(channel_messages)
                
                logger.info(f"Получено {len(channel_messages)} сообщений из канала {normalized_channel}")
                
            except Exception as e:
                logger.error(f"Ошибка при получении данных из канала {channel}: {e}")
        
        # Конвертируем даты из UTC в локальный часовой пояс
        timezone = settings.tz
        
        for message in all_messages:
            try:
                # Преобразуем строку ISO даты в объект datetime
                dt = datetime.fromisoformat(message["date"])
                
                # Если дата уже содержит информацию о часовом поясе, переводим в целевой пояс
                if dt.tzinfo:
                    local_dt = dt.astimezone(timezone)
                # Иначе предполагаем, что дата в UTC
                else:
                    utc_dt = dt.replace(tzinfo=pytz.UTC)
                    local_dt = utc_dt.astimezone(timezone)
                
                # Обновляем дату в сообщении
                message["date"] = local_dt.isoformat()
                message["date_local"] = local_dt.strftime("%Y-%m-%d %H:%M:%S")
                
            except Exception as e:
                logger.error(f"Ошибка при конвертации даты для сообщения {message.get('message_id')}: {e}")
        
        logger.info(f"Всего получено {len(all_messages)} сообщений из {len(channels)} каналов")
        
        # Сортируем сообщения по дате (сначала новые)
        all_messages.sort(key=lambda x: x["date"], reverse=True)
        
        return all_messages
