"""
Сервис для работы с Telegram Bot API.
Отправляет уведомления и отчеты в Telegram бота.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from telegram import Bot
from telegram.error import TelegramError, NetworkError, RetryAfter

from .utils import setup_logger

logger = setup_logger(__name__)

class TelegramBotService:
    """Сервис для работы с Telegram Bot API."""

    def __init__(self, token: str):
        """
        Инициализация Telegram Bot сервиса.

        Args:
            token: Токен Telegram бота
        """
        self.bot = Bot(token=token)
        self.token = token

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = 'HTML',
        disable_preview: bool = True
    ) -> Dict[str, Any]:
        """
        Отправить сообщение в Telegram.

        Args:
            chat_id: ID чата получателя
            text: Текст сообщения
            parse_mode: Режим форматирования ('HTML', 'Markdown', etc.)
            disable_preview: Отключить превью ссылок

        Returns:
            Dict с результатом отправки
        """
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_preview
            )

            logger.info(f"Message sent successfully to chat {chat_id}")
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat.id
            }

        except RetryAfter as e:
            logger.warning(f"Rate limit exceeded, retry after {e.retry_after} seconds")
            return {
                "success": False,
                "error": "rate_limit",
                "retry_after": e.retry_after,
                "message": f"Превышен лимит отправки сообщений. Повторите через {e.retry_after} секунд."
            }

        except NetworkError as e:
            logger.error(f"Network error: {e}")
            return {
                "success": False,
                "error": "network",
                "message": "Ошибка сети при отправке сообщения"
            }

        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return {
                "success": False,
                "error": "telegram_api",
                "message": f"Ошибка Telegram API: {str(e)}"
            }

        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return {
                "success": False,
                "error": "unexpected",
                "message": f"Неожиданная ошибка: {str(e)}"
            }

    async def test_connection(self, chat_id: str) -> Dict[str, Any]:
        """
        Тестовое сообщение для проверки работоспособности бота.

        Args:
            chat_id: ID чата для теста

        Returns:
            Dict с результатом тестового сообщения
        """
        test_message = """
🤖 <b>ReAIboot Bot</b>

✅ <b>Тестовое подключение успешно!</b>

<i>Бот готов к отправке отчетов и уведомлений.</i>
        """.strip()

        result = await self.send_message(chat_id, test_message)

        if result["success"]:
            logger.info(f"Bot test successful for chat {chat_id}")
        else:
            logger.error(f"Bot test failed for chat {chat_id}: {result.get('message', 'Unknown error')}")

        return result

    async def send_viral_report(
        self,
        chat_id: str,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Отправить отчет по виральным постам.

        Args:
            chat_id: ID чата получателя
            report_data: Данные отчета

        Returns:
            Dict с результатом отправки
        """
        try:
            # Форматируем отчет для Telegram
            report_text = self._format_viral_report(report_data)

            # Telegram ограничивает сообщения 4096 символами
            if len(report_text) > 4000:
                report_text = report_text[:4000] + "\n\n... (сообщение обрезано)"

            # Отправляем отчет
            result = await self.send_message(chat_id, report_text)

            if result["success"]:
                logger.info(f"Viral report sent successfully to chat {chat_id}")
            else:
                logger.error(f"Failed to send viral report to chat {chat_id}")

            return result

        except Exception as e:
            logger.error(f"Error sending viral report: {e}")
            return {
                "success": False,
                "error": "formatting",
                "message": f"Ошибка при формировании отчета: {str(e)}"
            }

    @staticmethod
    def _format_viral_report(data: Dict[str, Any]) -> str:
        """
        Форматировать отчет по виральным постам для Telegram.

        Args:
            data: Данные отчета

        Returns:
            Отформатированный текст отчета
        """
        posts = data.get("posts", [])
        analysis = data.get("analysis", {})
        period_days = data.get("period_days", 7)

        # Заголовок
        report = f"""
🎯 <b>Анализ виральных постов</b>
📅 <b>Период:</b> {period_days} дней
📊 <b>Найдено постов:</b> {len(posts)}

"""

        # Топ посты
        if posts:
            report += f"🔥 <b>Топ виральных постов:</b>\n\n"

            for i, post in enumerate(posts[:10], 1):  # Показываем топ 10
                title = post.get("channel_title", "Unknown")
                viral_score = post.get("viral_score", 0)
                views = post.get("views", 0)
                url = post.get("permalink", "#")

                report += f"{i}. <b>{title}</b>\n"
                report += f"   ⭐ Viral Score: {viral_score:.1f}\n"
                report += f"   👁 Просмотры: {views:,}\n"
                if url and url != "#":
                    report += f"   🔗 <a href='{url}'>Ссылка на пост</a>\n"
                report += "\n"

        # Анализ трендов
        if analysis:
            report += f"🧠 <b>Анализ трендов от ИИ:</b>\n\n"
            # Конвертируем markdown в HTML
            summary = analysis.get('summary', 'Анализ недоступен')
            import re
            # Заменяем **текст** на <b>текст</b>
            summary = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', summary)
            # Заменяем маркеры списков * и - на •
            summary = re.sub(r'^[\*\-\+] ', '• ', summary, flags=re.MULTILINE)
            # Удаляем оставшиеся ** если они есть
            summary = summary.replace('**', '')
            report += f"{summary}\n\n"

        # Подвал
        report += f"""
📈 <b>ReAIboot Analytics</b>
🤖 <i>Автоматический анализ социальных медиа</i>
"""

        return report.strip()

    async def send_parsing_complete_notification(
        self,
        chat_id: str,
        parsing_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Отправить уведомление о завершении парсинга.

        Args:
            chat_id: ID чата получателя
            parsing_stats: Статистика парсинга

        Returns:
            Dict с результатом отправки
        """
        channels_count = parsing_stats.get("channels_processed", 0)
        posts_count = parsing_stats.get("posts_collected", 0)
        duration = parsing_stats.get("duration_seconds", 0)

        message = f"""
✅ <b>Парсинг завершен успешно!</b>

📊 <b>Статистика:</b>
• Каналов обработано: {channels_count}
• Постов собрано: {posts_count}
• Время выполнения: {duration:.1f} сек

📈 <b>Система готова к анализу!</b>
"""

        return await self.send_message(chat_id, message.strip())

    async def get_last_chat_id(self) -> Dict[str, Any]:
        """
        Получить chat_id из последнего обновления бота.

        Этот метод проверяет последние обновления от бота и находит
        chat_id последнего сообщения от пользователя.

        Returns:
            Dict с chat_id или сообщением об ошибке
        """
        try:
            # Получить обновления от бота (последние 10 обновлений)
            updates = await self.bot.get_updates(limit=10, timeout=10)

            if not updates:
                return {
                    "success": False,
                    "message": "Нет новых обновлений. Напишите боту @iivka_bot любое сообщение и попробуйте снова."
                }

            # Найти последнее сообщение от пользователя (не от бота)
            latest_user_message = None
            for update in reversed(updates):  # Перебираем с конца (новые сообщения)
                if (update.message and
                    update.message.chat and
                    hasattr(update.message, 'from_user') and
                    update.message.from_user and
                    not update.message.from_user.is_bot):
                    latest_user_message = update.message
                    break

            if not latest_user_message:
                return {
                    "success": False,
                    "message": "Не найдено сообщений от пользователей. Напишите боту @iivka_bot любое сообщение и повторите попытку."
                }

            chat_id = str(latest_user_message.chat.id)
            chat_type = latest_user_message.chat.type
            username = getattr(latest_user_message.chat, 'username', None)
            first_name = getattr(latest_user_message.chat, 'first_name', None)
            last_name = getattr(latest_user_message.chat, 'last_name', None)

            # Формируем имя чата
            chat_name = username or f"{first_name or ''} {last_name or ''}".strip()
            if not chat_name:
                chat_name = f"Chat {chat_id}"

            return {
                "success": True,
                "chat_id": chat_id,
                "chat_type": chat_type,
                "chat_name": chat_name,
                "username": username,
                "message": f"✅ Найден Chat ID: <code>{chat_id}</code>\n📝 Тип чата: {chat_type}\n👤 Имя: {chat_name}"
            }

        except Exception as e:
            logger.error(f"Error getting chat ID: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка получения chat_id: {str(e)}"
            }
