"""
Модуль для работы с Telegram API через Telethon.
Telethon - надежная и проверенная библиотека для Telegram API.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pytz

# Импортируем Telethon
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import (
    Channel,
    Message as TelethonMessage,
    MessageReactions,
    PeerChannel
)
from telethon.errors import SessionPasswordNeededError, FloodWaitError

from .settings import settings
from .utils import setup_logger, normalize_channel_input, safe_get, truncate_text

# Настройка логирования
logger = setup_logger(__name__)

class TelegramAnalyzer:
    """Класс для анализа Telegram-каналов с использованием Telethon."""

    def __init__(self, session_name: Optional[str] = None):
        """
        Инициализирует клиент Telegram.

        Args:
            session_name: Имя файла сессии.
        """
        api_id = settings.telegram_api_id
        api_hash = settings.telegram_api_hash

        if not api_id or not api_hash:
            raise ValueError("TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены в настройках")

        if not session_name:
            # Telethon автоматически добавляет .session, поэтому убираем его из имени
            base_session = settings.telegram_session or "telegram_session"
            session_name = base_session.replace('.session', '') if base_session.endswith('.session') else base_session

        # Создаем клиента с правильными параметрами
        self.client = TelegramClient(
            session_name,
            api_id,
            api_hash,
            device_model="ReAIboot Parser",
            system_version="1.0.0"
        )
        self.is_connected = False
        self.api_id = api_id
        self.api_hash = api_hash

    async def needs_authorization(self) -> bool:
        """Проверяет, нужна ли авторизация для сессии."""
        try:
            # Проверяем, существует ли файл сессии
            session_file = f"{self.client.session.filename}"
            if not os.path.exists(session_file):
                logger.info("Файл сессии не найден")
                return True

            # Проверяем размер файла сессии (пустая сессия ~ 0 байт)
            if os.path.getsize(session_file) < 1000:  # Минимальный размер валидной сессии
                logger.warning("Файл сессии слишком мал, вероятно поврежден")
                return True

            # Пытаемся проверить сессию без полного подключения
            # Если сессия валидна, это не вызовет исключения
            try:
                # Попытка быстрой проверки сессии
                await self.client.connect()
                authorized = await self.client.is_user_authorized()
                await self.client.disconnect()

                if not authorized:
                    logger.warning("Сессия существует, но пользователь не авторизован")
                    return True

                return False

            except Exception as e:
                logger.warning(f"Ошибка при проверке сессии: {e}")
                return True

        except Exception as e:
            logger.error(f"Ошибка при проверке необходимости авторизации: {e}")
            return True

    async def connect(self) -> None:
        """Подключается к Telegram API с обработкой авторизации."""

        if self.is_connected:
            return

        try:
            logger.info("Подключение к Telegram...")

            # Проверяем, есть ли уже сохраненная сессия
            # Telethon автоматически формирует полное имя файла с .session
            if os.path.exists(f"{self.client.session.filename}"):
                logger.info("Найдена сохраненная сессия, пытаемся подключиться...")
                await self.client.start()
            else:
                logger.info("Сессия не найдена, требуется авторизация...")
                await self._authorize_client()

            self.is_connected = True
            logger.info("Успешно подключено к Telegram")

            # Проверяем, что клиент действительно авторизован
            me = await self.client.get_me()
            logger.info(f"Авторизован как: {me.first_name} (@{me.username})")

        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            self.is_connected = False
            raise

    async def send_code(self, phone: str) -> Dict[str, Any]:
        """Отправляет код подтверждения на номер телефона."""
        try:
            logger.info(f"=== НАЧАЛО ОТПРАВКИ КОДА НА НОМЕР: {phone} ===")

            # Создаем новый клиент для этого запроса согласно документации
            from telethon import TelegramClient
            temp_client = TelegramClient(
                f"{self.client.session.filename}_auth",  # Уникальное имя сессии для авторизации
                self.api_id,
                self.api_hash
            )

            # Используем контекстный менеджер согласно документации
            async with temp_client:
                logger.info("Временный клиент подключен")

                # Проверяем авторизацию
                try:
                    is_authorized = await temp_client.is_user_authorized()
                    logger.info(f"Статус авторизации: {is_authorized}")

                    if is_authorized:
                        logger.info("Клиент уже авторизован")
                        return {
                            "phone_code_hash": "already_authorized",
                            "timeout": 60
                        }
                except Exception as e:
                    logger.warning(f"Ошибка при проверке авторизации: {e}")

                # Отправляем код
                logger.info("Отправляем код подтверждения...")
                sent_code = await temp_client.send_code_request(phone)
                logger.info(f"Код успешно отправлен, phone_code_hash: {sent_code.phone_code_hash}")

                return {
                    "phone_code_hash": sent_code.phone_code_hash,
                    "timeout": sent_code.timeout
                }

        except Exception as e:
            logger.error(f"Ошибка при отправке кода: {e}")
            logger.error(f"Тип ошибки: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def verify_code(self, code: str, phone_code_hash: str) -> None:
        """Проверяет код подтверждения."""
        try:
            logger.info("Проверка кода подтверждения")

            # Создаем новый клиент для этого запроса согласно документации
            from telethon import TelegramClient
            temp_client = TelegramClient(
                f"{self.client.session.filename}_auth",  # То же уникальное имя сессии
                self.api_id,
                self.api_hash
            )

            # Используем контекстный менеджер согласно документации
            async with temp_client:
                logger.info("Временный клиент подключен для проверки кода")

                # Проверяем код
                await temp_client.sign_in(phone_code_hash=phone_code_hash, code=code)

                # Проверяем авторизацию
                if await temp_client.is_user_authorized():
                    logger.info("Успешная авторизация!")
                    self.is_connected = True
                else:
                    raise ValueError("Авторизация не удалась")

        except Exception as e:
            logger.error(f"Ошибка при проверке кода: {e}")
            raise

    async def _authorize_client(self) -> None:
        """Выполняет авторизацию клиента."""

        logger.info("Начинаем процесс авторизации...")

        try:
            await self.client.start()

            # Проверяем, требуется ли пароль (2FA)
            if await self.client.is_user_authorized():
                logger.info("Пользователь уже авторизован")
                return

            logger.info("Требуется авторизация пользователя")

        except SessionPasswordNeededError:
            logger.error("Требуется двухфакторная аутентификация. Пожалуйста, настройте сессию вручную.")
            raise ValueError("2FA требуется, но не поддерживается в автоматическом режиме")

        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
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

    async def manual_auth(self, phone: str) -> str:
        """
        Выполняет ручную авторизацию для создания сессии.

        Args:
            phone: Номер телефона в международном формате (+7XXXXXXXXXX)

        Returns:
            Инструкции для пользователя
        """
        logger.info(f"Начинаем ручную авторизацию для номера: {phone}")

        try:
            await self.client.start(phone=phone)

            # Проверяем, авторизован ли уже пользователь
            if await self.client.is_user_authorized():
                logger.info("Пользователь уже авторизован")
                return "✅ Уже авторизован"

            # Отправляем код подтверждения
            logger.info("Отправлен код подтверждения")
            return "📱 Код подтверждения отправлен. Используйте метод send_code(code) для завершения авторизации"

        except Exception as e:
            logger.error(f"Ошибка при отправке кода: {e}")
            raise

    async def send_code(self, code: str) -> str:
        """
        Завершает авторизацию с кодом подтверждения.

        Args:
            code: Код подтверждения из Telegram

        Returns:
            Результат авторизации
        """
        try:
            await self.client.sign_in(code=code)

            if await self.client.is_user_authorized():
                logger.info("✅ Авторизация успешна")
                return "✅ Авторизация успешна! Сессия сохранена."
            else:
                logger.error("❌ Авторизация не удалась")
                return "❌ Авторизация не удалась"

        except SessionPasswordNeededError:
            logger.warning("Требуется пароль 2FA")
            return "🔐 Требуется пароль двухфакторной аутентификации. Используйте метод sign_in_2fa(password)"
        except Exception as e:
            logger.error(f"Ошибка при вводе кода: {e}")
            raise

    async def sign_in_2fa(self, password: str) -> str:
        """
        Завершает авторизацию с паролем 2FA.

        Args:
            password: Пароль двухфакторной аутентификации

        Returns:
            Результат авторизации
        """
        try:
            await self.client.sign_in(password=password)

            if await self.client.is_user_authorized():
                logger.info("✅ Авторизация с 2FA успешна")
                return "✅ Авторизация успешна! Сессия сохранена."
            else:
                logger.error("❌ Авторизация с 2FA не удалась")
                return "❌ Авторизация не удалась"

        except Exception as e:
            logger.error(f"Ошибка при вводе пароля 2FA: {e}")
            raise

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
        except FloodWaitError as e:
            logger.warning(f"Flood wait {e.seconds} секунд при получении канала '{channel_input}'")
            await asyncio.sleep(e.seconds)
            # Повторная попытка
            try:
                channel = await self.client.get_entity(normalized_channel)
                return channel
            except Exception as e2:
                logger.error(f"Ошибка после flood wait при получении канала '{channel_input}': {e2}")
                return None
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

            channel_info = {
                "id": channel_entity.id,
                "title": getattr(channel_entity, 'title', None),
                "username": getattr(channel_entity, 'username', None),
                "participants_count": getattr(full_channel.full_chat, 'participants_count', 0),
                "date": getattr(channel_entity, 'date', None),
                "about": getattr(full_channel.full_chat, 'about', None),
            }

            return channel_info
        except FloodWaitError as e:
            logger.warning(f"Flood wait {e.seconds} секунд при получении информации о канале '{channel_input}'")
            await asyncio.sleep(e.seconds)
            # Повторная попытка
            try:
                full_channel = await self.client(GetFullChannelRequest(channel=channel_entity))
                channel_info = {
                    "id": channel_entity.id,
                    "title": getattr(channel_entity, 'title', None),
                    "username": getattr(channel_entity, 'username', None),
                    "participants_count": getattr(full_channel.full_chat, 'participants_count', 0),
                    "date": getattr(channel_entity, 'date', None),
                    "about": getattr(full_channel.full_chat, 'about', None),
                }
                return channel_info
            except Exception as e2:
                logger.error(f"Ошибка после flood wait при получении информации о канале '{channel_input}': {e2}")
                return {"error": str(e2)}
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
                limit=limit
            ):
                # Проверяем, входит ли сообщение в указанный период
                # Убеждаемся, что обе даты имеют информацию о часовом поясе
                message_date = message.date
                if not message_date.tzinfo:
                    message_date = message_date.replace(tzinfo=pytz.UTC)

                # Поскольку iter_messages возвращает сообщения от новых к старым,
                # мы останавливаемся, когда находим сообщение старше нужного периода
                if message_date < since_date:
                    logger.info(f"Останавливаемся на сообщении от {message_date} (старше {since_date})")
                    break

                # Пропускаем сообщения без текста
                if not message.text:
                    continue

                # Форматируем сообщение
                message_data = await self._format_message(message, channel_info)
                messages.append(message_data)

            logger.info(f"Загружено {len(messages)} сообщений из канала '{channel_entity.title}'")
            return messages, channel_info

        except FloodWaitError as e:
            logger.warning(f"Flood wait {e.seconds} секунд при получении сообщений из канала '{channel_input}'")
            await asyncio.sleep(e.seconds)
            # Повторная попытка с меньшим лимитом
            try:
                messages = []
                async for message in self.client.iter_messages(
                    channel_entity,
                    limit=min(limit, 50)  # Уменьшаем лимит
                ):
                    message_date = message.date
                    if not message_date.tzinfo:
                        message_date = message_date.replace(tzinfo=pytz.UTC)

                    if message_date < since_date:
                        break

                    if not message.text:
                        continue

                    message_data = await self._format_message(message, channel_info)
                    messages.append(message_data)

                logger.info(f"Загружено {len(messages)} сообщений после flood wait из канала '{channel_entity.title}'")
                return messages, channel_info
            except Exception as e2:
                logger.error(f"Ошибка после flood wait при получении сообщений из канала '{channel_input}': {e2}")
                return [], {"error": str(e2)}
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений из канала '{channel_input}': {e}")
            return [], {"error": str(e)}
    
    async def _format_message(self, message: TelethonMessage, channel_info: Dict[str, Any]) -> Dict[str, Any]:
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

    async def get_channel_posts(
        self,
        channel_username: str,
        days_back: int = 7,
        max_posts: int = 100
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Получает посты из канала (wrapper для совместимости с API).

        Args:
            channel_username: Username канала
            days_back: Количество дней назад
            max_posts: Максимальное количество постов

        Returns:
            Tuple (список постов, информация о канале)
        """
        messages, channel_info = await self.get_messages(
            channel_username,
            days=days_back,
            limit=max_posts
        )

        if "error" in channel_info:
            logger.error(f"Ошибка при получении постов: {channel_info['error']}")
            return [], channel_info

        return messages, channel_info

    def is_processor_available(self) -> bool:
        """
        Проверяет доступность процессора (для совместимости).

        Returns:
            True если доступен
        """
        return True
