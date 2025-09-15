"""
Модуль для работы с Telegram API через Telethon.
Telethon - надежная и проверенная библиотека для Telegram API.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pytz

# Импортируем Telethon
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.chatlists import (
    CheckChatlistInviteRequest,
    GetChatlistUpdatesRequest,
    JoinChatlistInviteRequest,
)
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import Channel, Chat
from telethon.tl.types import Message as TelethonMessage
from telethon.tl.types import MessageReactions, PeerChannel, User

from .settings import settings
from .utils import normalize_channel_input, safe_get, setup_logger, truncate_text

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
            raise ValueError(
                "TELEGRAM_API_ID и TELEGRAM_API_HASH должны быть установлены в настройках"
            )

        if not session_name:
            # Telethon автоматически добавляет .session, поэтому убираем его из имени
            base_session = settings.telegram_session or "telegram_session"
            session_name = (
                base_session.replace(".session", "")
                if base_session.endswith(".session")
                else base_session
            )

        # Создаем клиента с правильными параметрами
        self.client = TelegramClient(
            session_name,
            api_id,
            api_hash,
            device_model="ReAIboot Parser",
            system_version="1.0.0",
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
            if (
                os.path.getsize(session_file) < 1000
            ):  # Минимальный размер валидной сессии
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
                self.api_hash,
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
                        return {"phone_code_hash": "already_authorized", "timeout": 60}
                except Exception as e:
                    logger.warning(f"Ошибка при проверке авторизации: {e}")

                # Отправляем код
                logger.info("Отправляем код подтверждения...")
                sent_code = await temp_client.send_code_request(phone)
                logger.info(
                    f"Код успешно отправлен, phone_code_hash: {sent_code.phone_code_hash}"
                )

                return {
                    "phone_code_hash": sent_code.phone_code_hash,
                    "timeout": sent_code.timeout,
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
                self.api_hash,
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
            logger.error(
                "Требуется двухфакторная аутентификация. Пожалуйста, настройте сессию вручную."
            )
            raise ValueError(
                "2FA требуется, но не поддерживается в автоматическом режиме"
            )

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
            logger.warning(
                f"Flood wait {e.seconds} секунд при получении канала '{channel_input}'"
            )
            await asyncio.sleep(e.seconds)
            # Повторная попытка
            try:
                channel = await self.client.get_entity(normalized_channel)
                return channel
            except Exception as e2:
                logger.error(
                    f"Ошибка после flood wait при получении канала '{channel_input}': {e2}"
                )
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
            full_channel = await self.client(
                GetFullChannelRequest(channel=channel_entity)
            )

            channel_info = {
                "id": channel_entity.id,
                "title": getattr(channel_entity, "title", None),
                "username": getattr(channel_entity, "username", None),
                "participants_count": getattr(
                    full_channel.full_chat, "participants_count", 0
                ),
                "date": getattr(channel_entity, "date", None),
                "about": getattr(full_channel.full_chat, "about", None),
            }

            return channel_info
        except FloodWaitError as e:
            logger.warning(
                f"Flood wait {e.seconds} секунд при получении информации о канале '{channel_input}'"
            )
            await asyncio.sleep(e.seconds)
            # Повторная попытка
            try:
                full_channel = await self.client(
                    GetFullChannelRequest(channel=channel_entity)
                )
                channel_info = {
                    "id": channel_entity.id,
                    "title": getattr(channel_entity, "title", None),
                    "username": getattr(channel_entity, "username", None),
                    "participants_count": getattr(
                        full_channel.full_chat, "participants_count", 0
                    ),
                    "date": getattr(channel_entity, "date", None),
                    "about": getattr(full_channel.full_chat, "about", None),
                }
                return channel_info
            except Exception as e2:
                logger.error(
                    f"Ошибка после flood wait при получении информации о канале '{channel_input}': {e2}"
                )
                return {"error": str(e2)}
        except Exception as e:
            logger.error(
                f"Ошибка при получении информации о канале '{channel_input}': {e}"
            )
            return {"error": str(e)}

    async def get_channels_from_user_folders(self) -> Dict[str, Any]:
        """
        Получает список всех папок пользователя и каналов в них.

        Returns:
            Словарь с информацией о папках и их каналах
        """
        logger.info("=== НАЧАЛО get_channels_from_user_folders ===")

        if not self.is_connected:
            await self.connect()

        try:
            # Получаем все диалоги (включая папки)
            logger.info("Получаем все диалоги пользователя...")
            from telethon.tl.functions.messages import GetDialogsRequest
            from telethon.tl.types import InputPeerEmpty

            dialogs_result = await self.client(
                GetDialogsRequest(
                    offset_date=None,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=500,  # Большой лимит для получения всех диалогов
                    hash=0,
                    exclude_pinned=False,
                    folder_id=None,  # Все папки
                )
            )

            logger.info(f"Получено {len(dialogs_result.dialogs)} диалогов всего")

            folders = {}
            folder_ids_found = set()

            for dialog in dialogs_result.dialogs:
                # GetDialogsRequest возвращает dialogs в поле dialogs
                folder_id = getattr(dialog, "folder_id", None)
                folder_ids_found.add(folder_id)

                # Обрабатываем как обычные папки (folder_id > 0), так и "основную ленту" (folder_id = null)
                effective_folder_id = (
                    folder_id if folder_id is not None else 0
                )  # 0 = основная лента

                if effective_folder_id not in folders:
                    if folder_id is None:
                        folders[effective_folder_id] = {
                            "id": effective_folder_id,
                            "name": "Основная лента",  # Название для каналов без папки
                            "channels": [],
                        }
                    else:
                        folders[effective_folder_id] = {
                            "id": effective_folder_id,
                            "name": f"Папка {folder_id}",  # Telegram не дает имена папок через API
                            "channels": [],
                        }

                # Получаем информацию о диалоге (канал или чат)
                try:
                    # Получаем полную информацию о диалоге
                    entity = await self.client.get_entity(dialog)

                    # Проверяем тип диалога
                    dialog_info = {
                        "id": entity.id,
                        "username": getattr(entity, "username", None),
                        "title": getattr(entity, "title", ""),
                        "type": type(entity).__name__.lower(),
                    }

                    # Добавляем специфичную информацию в зависимости от типа
                    if hasattr(entity, "participants_count"):
                        dialog_info["participants_count"] = getattr(
                            entity, "participants_count", 0
                        )

                    # Создаем отдельные списки для каналов и чатов
                    if "channels" not in folders[effective_folder_id]:
                        folders[effective_folder_id]["channels"] = []
                    if "chats" not in folders[effective_folder_id]:
                        folders[effective_folder_id]["chats"] = []

                    if isinstance(entity, Channel):
                        folders[effective_folder_id]["channels"].append(dialog_info)
                    else:
                        folders[effective_folder_id]["chats"].append(dialog_info)

                except Exception as e:
                    logger.warning(f"Не удалось получить информацию о диалоге: {e}")

            logger.info(
                f"Найдено {len(folders)} папок с {sum(len(f['channels']) for f in folders.values())} каналами"
            )

            result = {
                "total_folders": len(folders),
                "folders": list(folders.values()),
                "total_channels": sum(len(f["channels"]) for f in folders.values()),
            }

            logger.info(
                f"Найдено {len(folders)} папок с {result['total_channels']} каналами"
            )
            return result

        except Exception as e:
            logger.error(f"Ошибка при получении папок пользователя: {e}")
            return {"error": f"Не удалось получить папки пользователя: {str(e)}"}

    async def get_user_channels(self) -> Dict[str, Any]:
        """
        Получает список всех каналов пользователя (из всех папок и основных диалогов).

        Returns:
            Словарь с информацией о каналах пользователя
        """
        if not self.is_connected:
            await self.connect()

        try:
            # Получаем все диалоги пользователя
            logger.info("Получаем все каналы пользователя...")
            from telethon.tl.functions.messages import GetDialogsRequest
            from telethon.tl.types import InputPeerEmpty

            dialogs_result = await self.client(
                GetDialogsRequest(
                    offset_date=None,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=500,  # Большой лимит для получения всех диалогов
                    hash=0,
                    exclude_pinned=False,
                    folder_id=None,  # Все папки
                )
            )

            channels = []
            logger.info(f"Получено {len(dialogs_result.dialogs)} диалогов всего")

            for dialog in dialogs_result.dialogs:
                try:
                    # Получаем полную информацию о канале
                    channel_entity = await self.client.get_entity(dialog)

                    # Проверяем, что это канал (не чат, не бот)
                    if isinstance(channel_entity, Channel) and not getattr(
                        channel_entity, "megagroup", False
                    ):
                        channel_info = {
                            "id": channel_entity.id,
                            "username": getattr(channel_entity, "username", None),
                            "title": getattr(channel_entity, "title", ""),
                            "participants_count": getattr(
                                channel_entity, "participants_count", 0
                            ),
                            "type": "channel",
                        }

                        # Добавляем только если есть username (публичный канал)
                        if channel_info["username"]:
                            channels.append(channel_info)

                except Exception as e:
                    logger.warning(f"Не удалось получить информацию о диалоге: {e}")

            result = {"total_channels": len(channels), "channels": channels}

            logger.info(f"Найдено {len(channels)} публичных каналов")
            return result

        except Exception as e:
            logger.error(f"Ошибка при получении каналов пользователя: {e}")
            return {"error": f"Не удалось получить каналы пользователя: {str(e)}"}

    async def get_channels_from_folder(self, folder_link: str) -> Dict[str, Any]:
        """
        Получает список каналов из папки по ссылке на приглашение.

        Args:
            folder_link: Ссылка на папку в формате https://t.me/addlist/slug

        Returns:
            Словарь с информацией о папке и списком каналов
        """

        if not self.is_connected:
            await self.connect()

        # Извлекаем slug из ссылки
        slug = self._extract_slug_from_link(folder_link)
        if not slug:
            return {"error": f"Неверный формат ссылки: {folder_link}"}

        try:
            # Сначала пробуем CheckChatlistInviteRequest
            logger.info(f"Пытаемся получить папку с slug: {slug}")
            invite = await self.client(CheckChatlistInviteRequest(slug=slug))
            logger.info(f"Получен ответ от Telegram API: {type(invite).__name__}")

            # Если уже присоединились, пробуем альтернативный подход
            from telethon.tl.types.chatlists import ChatlistInviteAlready

            if isinstance(invite, ChatlistInviteAlready):
                logger.info(
                    "Пользователь уже присоединился к папке, пробуем получить информацию другим способом"
                )

                # Пробуем JoinChatlistInviteRequest с пустым списком (только для получения информации)
                try:
                    logger.info(
                        "Пробуем JoinChatlistInviteRequest для получения информации..."
                    )
                    join_result = await self.client(
                        JoinChatlistInviteRequest(slug=slug, peers=[])
                    )
                    logger.info(
                        f"JoinChatlistInviteRequest вернул: {type(join_result).__name__}"
                    )

                    # Если JoinChatlistInviteRequest сработал, но не вернул invite, попробуем GetChatlistUpdatesRequest
                    logger.info("Пробуем получить обновления папки...")
                    updates = await self.client(GetChatlistUpdatesRequest())
                    logger.info(
                        f"Получены обновления: {len(updates.chats) if hasattr(updates, 'chats') else 0} чатов"
                    )

                    return {
                        "error": "Не удалось получить содержимое папки.\n\n"
                        + "Попробуйте:\n"
                        + "• Открыть папку в Telegram Desktop/Mobile\n"
                        + "• Скопировать ссылку оттуда\n"
                        + "• Или добавить каналы вручную"
                    }

                except Exception as join_error:
                    logger.warning(f"JoinChatlistInviteRequest failed: {join_error}")
                    return {
                        "error": "Не удалось получить содержимое папки.\n\n"
                        + "Попробуйте:\n"
                        + "• Открыть папку в Telegram Desktop/Mobile\n"
                        + "• Скопировать ссылку оттуда\n"
                        + "• Или добавить каналы вручную"
                    }

            # Проверяем тип ответа
            if hasattr(invite, "title") and invite.title:
                logger.info(f"Папка найдена: '{invite.title}'")
            else:
                logger.warning(
                    f"Папка недоступна или не найдена. Тип объекта: {type(invite).__name__}"
                )
                logger.warning(
                    f"Атрибуты объекта: {[attr for attr in dir(invite) if not attr.startswith('_')]}"
                )

                return {
                    "error": "Папка не найдена или недоступна. Возможные причины:\n"
                    + "• Ссылка на папку недействительна\n"
                    + "• Папка приватная и требует специального приглашения\n"
                    + "• Ограничения Telegram API для доступа к папкам"
                }

            # Извлекаем каналы из приглашения
            channels = []
            for chat in invite.chats:
                if isinstance(chat, Channel):
                    channel_info = {
                        "id": chat.id,
                        "username": getattr(chat, "username", None),
                        "title": getattr(chat, "title", ""),
                        "participants_count": getattr(chat, "participants_count", 0),
                        "type": "channel",
                    }
                    if channel_info["username"]:  # Добавляем только если есть username
                        channels.append(channel_info)

            result = {
                "folder_title": invite.title,
                "total_channels": len(channels),
                "channels": channels,
                "slug": slug,
            }

            logger.info(f"Из папки '{invite.title}' получено {len(channels)} каналов")
            return result

        except FloodWaitError as e:
            logger.warning(
                f"Flood wait {e.seconds} секунд при получении папки '{folder_link}'"
            )
            await asyncio.sleep(e.seconds)
            # Повторная попытка
            try:
                invite = await self.client(CheckChatlistInviteRequest(slug=slug))
                # Аналогичная обработка...
                channels = []
                for chat in invite.chats:
                    if isinstance(chat, Channel):
                        channel_info = {
                            "id": chat.id,
                            "username": getattr(chat, "username", None),
                            "title": getattr(chat, "title", ""),
                            "participants_count": getattr(
                                chat, "participants_count", 0
                            ),
                            "type": "channel",
                        }
                        if channel_info["username"]:
                            channels.append(channel_info)

                return {
                    "folder_title": invite.title,
                    "total_channels": len(channels),
                    "channels": channels,
                    "slug": slug,
                }
            except Exception as e2:
                logger.error(
                    f"Ошибка после flood wait при получении папки '{folder_link}': {e2}"
                )
                return {"error": str(e2)}
        except Exception as e:
            logger.error(f"Ошибка при получении папки '{folder_link}': {e}")
            return {"error": str(e)}

    def _extract_slug_from_link(self, link: str) -> Optional[str]:
        """
        Извлекает slug из ссылки на папку.

        Args:
            link: Ссылка в формате https://t.me/addlist/slug или addlist/slug

        Returns:
            Slug приглашения или None если формат неверный
        """
        import re

        # Регулярное выражение для поиска slug в ссылке
        patterns = [
            r"https?://t\.me/addlist/([a-zA-Z0-9_-]+)",  # Полная ссылка
            r"t\.me/addlist/([a-zA-Z0-9_-]+)",  # Короткая ссылка
            r"addlist/([a-zA-Z0-9_-]+)",  # Только addlist/slug
            r"([a-zA-Z0-9_-]+)" if link.startswith("addlist/") else None,  # Только slug
        ]

        for pattern in patterns:
            if pattern:
                match = re.search(pattern, link)
                if match:
                    return match.group(1)

        return None

    async def get_messages(
        self, channel_input: str, days: int = 7, limit: int = 100
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
            async for message in self.client.iter_messages(channel_entity, limit=limit):
                # Проверяем, входит ли сообщение в указанный период
                # Убеждаемся, что обе даты имеют информацию о часовом поясе
                message_date = message.date
                if not message_date.tzinfo:
                    message_date = message_date.replace(tzinfo=pytz.UTC)

                # Поскольку iter_messages возвращает сообщения от новых к старым,
                # мы останавливаемся, когда находим сообщение старше нужного периода
                if message_date < since_date:
                    logger.info(
                        f"Останавливаемся на сообщении от {message_date} (старше {since_date})"
                    )
                    break

                # Пропускаем сообщения без текста
                if not message.text:
                    continue

                # Форматируем сообщение
                message_data = await self._format_message(message, channel_info)
                messages.append(message_data)

            logger.info(
                f"Загружено {len(messages)} сообщений из канала '{channel_entity.title}'"
            )
            return messages, channel_info

        except FloodWaitError as e:
            logger.warning(
                f"Flood wait {e.seconds} секунд при получении сообщений из канала '{channel_input}'"
            )
            await asyncio.sleep(e.seconds)
            # Повторная попытка с меньшим лимитом
            try:
                messages = []
                async for message in self.client.iter_messages(
                    channel_entity, limit=min(limit, 50)  # Уменьшаем лимит
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

                logger.info(
                    f"Загружено {len(messages)} сообщений после flood wait из канала '{channel_entity.title}'"
                )
                return messages, channel_info
            except Exception as e2:
                logger.error(
                    f"Ошибка после flood wait при получении сообщений из канала '{channel_input}': {e2}"
                )
                return [], {"error": str(e2)}
        except Exception as e:
            logger.error(
                f"Ошибка при получении сообщений из канала '{channel_input}': {e}"
            )
            return [], {"error": str(e)}

    async def _format_message(
        self, message: TelethonMessage, channel_info: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        # Формируем ID поста (такой же как в save_posts_batch)
        channel_username = channel_info.get("username", "")
        if channel_username and not channel_username.startswith("@"):
            channel_username = f"@{channel_username}"
        post_id = f"{message.id}_{channel_username}"

        # Форматируем сообщение
        message_data = {
            "id": post_id,  # Добавляем ID для обновления метрик
            "channel_title": channel_info.get("title"),
            "channel_username": channel_username,  # Уже с @
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
            "permalink": permalink,
        }

        return message_data

    async def get_channel_posts(
        self, channel_username: str, days_back: int = 7, max_posts: int = 100
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
            channel_username, days=days_back, limit=max_posts
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
