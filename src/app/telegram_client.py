"""
Модуль для работы с Telegram API через Telethon.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import (
    Channel, 
    Message, 
    MessageReactions, 
    PeerChannel
)

from .settings import settings
from .utils import setup_logger, normalize_channel_input, safe_get, truncate_text

# Настройка логирования
logger = setup_logger(__name__)

class TelegramAnalyzer:
    """Класс для анализа Telegram-каналов."""
    
    def __init__(self, session_name: Optional[str] = None):
        """
        Инициализирует клиент Telegram.
        
        Args:
            session_name: Имя файла сессии.
        """
        api_id = settings.telegram_api_id
        api_hash = settings.telegram_api_hash
        
        if not session_name:
            session_name = settings.telegram_session
        
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.is_connected = False
    
    async def connect(self) -> None:
        """Подключается к Telegram API."""
        
        if not self.is_connected:
            try:
                logger.info("Подключение к Telegram...")
                await self.client.start()
                self.is_connected = True
                logger.info("Успешно подключено к Telegram")
            except Exception as e:
                logger.error(f"Ошибка подключения к Telegram: {e}")
                raise
    
    async def disconnect(self) -> None:
        """Отключается от Telegram API."""
        
        if self.is_connected:
            try:
                await self.client.disconnect()
                self.is_connected = False
                logger.info("Отключено от Telegram")
            except Exception as e:
                logger.error(f"Ошибка при отключении от Telegram: {e}")
    
    async def __aenter__(self):
        """Контекстный менеджер: вход."""
        
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        
        await self.disconnect()
    
    async def get_channel_entity(self, channel_input: str) -> Optional[Channel]:
        """
        Получает сущность канала по имени/URL.
        
        Args:
            channel_input: Имя канала или URL.
            
        Returns:
            Сущность канала или None, если канал не найден.
        """
        
        if not self.is_connected:
            await self.connect()
        
        normalized_channel = normalize_channel_input(channel_input)
        
        try:
            channel = await self.client.get_entity(normalized_channel)
            return channel
        except Exception as e:
            logger.error(f"Ошибка при получении канала '{channel_input}': {e}")
            return None
    
    async def get_channel_info(self, channel_input: str) -> Dict[str, Any]:
        """
        Получает информацию о канале.
        
        Args:
            channel_input: Имя канала или URL.
            
        Returns:
            Словарь с информацией о канале.
        """
        
        if not self.is_connected:
            await self.connect()
        
        channel_entity = await self.get_channel_entity(channel_input)
        
        if not channel_entity:
            return {"error": f"Канал не найден: {channel_input}"}
        
        try:
            # Получаем полную информацию о канале
            full_channel = await self.client(GetFullChannelRequest(channel=channel_entity))
            
            # Получаем количество участников
            participants_count = full_channel.full_chat.participants_count
            
            channel_info = {
                "id": channel_entity.id,
                "title": channel_entity.title,
                "username": channel_entity.username,
                "participants_count": participants_count,
                "date": channel_entity.date.isoformat() if hasattr(channel_entity, "date") else None,
                "about": full_channel.full_chat.about if hasattr(full_channel.full_chat, "about") else None,
            }
            
            return channel_info
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале '{channel_input}': {e}")
            return {"error": str(e)}
    
    async def get_messages(
        self, 
        channel_input: str, 
        days: int = 7, 
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Получает сообщения из канала за указанный период.
        
        Args:
            channel_input: Имя канала или URL.
            days: Количество дней для анализа.
            limit: Максимальное количество сообщений для загрузки.
            
        Returns:
            Кортеж из списка сообщений и информации о канале.
        """
        
        if not self.is_connected:
            await self.connect()
        
        channel_entity = await self.get_channel_entity(channel_input)
        
        if not channel_entity:
            return [], {"error": f"Канал не найден: {channel_input}"}
        
        # Получаем информацию о канале
        channel_info = await self.get_channel_info(channel_input)
        
        # Определяем дату начала периода с учетом часового пояса
        now = datetime.now(pytz.UTC)
        since_date = now - timedelta(days=days)
        
        try:
            messages = []
            async for message in self.client.iter_messages(
                channel_entity, 
                limit=limit,
                offset_date=now
            ):
                # Проверяем, входит ли сообщение в указанный период
                # Убеждаемся, что обе даты имеют информацию о часовом поясе
                message_date = message.date
                if not message_date.tzinfo:
                    message_date = message_date.replace(tzinfo=pytz.UTC)
                
                if message_date < since_date:
                    break
                
                # Пропускаем сообщения без текста
                if not message.text:
                    continue
                
                # Форматируем сообщение
                message_data = await self._format_message(message, channel_info)
                messages.append(message_data)
            
            logger.info(f"Загружено {len(messages)} сообщений из канала '{channel_entity.title}'")
            return messages, channel_info
        
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений из канала '{channel_input}': {e}")
            return [], {"error": str(e)}
    
    async def _format_message(self, message: Message, channel_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует сообщение для вывода.
        
        Args:
            message: Объект сообщения.
            channel_info: Информация о канале.
            
        Returns:
            Словарь с данными о сообщении.
        """
        
        # Получаем количество просмотров
        views = getattr(message, "views", 0) or 0
        
        # Получаем количество пересылок
        forwards = getattr(message, "forwards", 0) or 0
        
        # Получаем реакции
        reactions = 0
        if message.reactions:
            for result in message.reactions.results:
                reactions += result.count
        
        # Получаем количество комментариев (replies)
        replies = 0
        if hasattr(message, "replies") and message.replies:
            replies = message.replies.replies
        
        # Формируем пермалинк, если возможно
        permalink = None
        if channel_info.get("username"):
            message_id = message.id
            permalink = f"https://t.me/{channel_info['username']}/{message_id}"
        
        # Проверяем наличие медиа
        has_media = bool(message.media)
        
        # Форматируем сообщение
        message_data = {
            "channel_id": channel_info.get("id"),
            "channel_title": channel_info.get("title"),
            "channel_username": channel_info.get("username"),
            "participants_count": channel_info.get("participants_count", 0),
            "message_id": message.id,
            "date": message.date.isoformat(),
            "text": truncate_text(message.text, 2000),
            "text_preview": truncate_text(message.text, 500),
            "views": views,
            "forwards": forwards,
            "replies": replies,
            "reactions": reactions,
            "has_media": has_media,
            "permalink": permalink
        }
        
        return message_data
