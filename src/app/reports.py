"""
Генератор отчетов по виральным постам.
Создает аналитические отчеты и отправляет их через Telegram бота.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .supabase_client import SupabaseManager
from .telegram_bot import TelegramBotService
from .llm.orchestrator import LLMOrchestrator
from .utils import setup_logger

logger = setup_logger(__name__)

class ReportGenerator:
    """Генератор отчетов по виральным постам."""

    def __init__(self, supabase_manager: SupabaseManager):
        """
        Инициализация генератора отчетов.

        Args:
            supabase_manager: Менеджер Supabase для работы с БД
        """
        self.supabase = supabase_manager
        self.orchestrator = LLMOrchestrator()

    async def generate_viral_report(
        self,
        days: int = 7,
        min_viral_score: float = 1.0,
        channel_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Генерировать отчет по виральным постам.

        Args:
            days: Период анализа в днях
            min_viral_score: Минимальный порог виральности
            channel_username: Фильтр по конкретному каналу

        Returns:
            Dict с результатом генерации отчета
        """
        try:
            logger.info(f"Generating viral report: days={days}, min_score={min_viral_score}, channel={channel_username}")

            # Получаем виральные посты
            viral_posts = await self._get_viral_posts(days, min_viral_score, channel_username)

            if not viral_posts:
                logger.warning(f"No viral posts found for criteria: days={days}, min_score={min_viral_score}")
                return {
                    "success": False,
                    "message": f"Не найдено виральных постов за {days} дней с минимальным score {min_viral_score}"
                }

            logger.info(f"Found {len(viral_posts)} viral posts")

            # Анализируем тренды через LLM
            trends_analysis = await self._analyze_trends(viral_posts)

            # Формируем отчет
            report = self._format_report(viral_posts, trends_analysis, days)

            return {
                "success": True,
                "report": report,
                "posts_count": len(viral_posts),
                "analysis": trends_analysis,
                "posts": viral_posts,
                "period_days": days,
                "min_viral_score": min_viral_score
            }

        except Exception as e:
            logger.error(f"Error generating viral report: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка при генерации отчета: {str(e)}"
            }

    async def send_report_via_bot(
        self,
        report_data: Dict[str, Any],
        bot_token: str,
        chat_id: str
    ) -> Dict[str, Any]:
        """
        Отправить отчет через Telegram бота.

        Args:
            report_data: Данные отчета
            bot_token: Токен бота
            chat_id: ID чата

        Returns:
            Dict с результатом отправки
        """
        try:
            logger.info(f"Sending report via bot to chat {chat_id}")

            bot_service = TelegramBotService(bot_token)
            result = await bot_service.send_viral_report(chat_id, report_data)

            if result["success"]:
                logger.info(f"Report sent successfully to chat {chat_id}")
            else:
                logger.error(f"Failed to send report to chat {chat_id}: {result.get('message', 'Unknown error')}")

            return result

        except Exception as e:
            logger.error(f"Error sending report via bot: {e}", exc_info=True)
            return {
                "success": False,
                "error": "unexpected",
                "message": f"Неожиданная ошибка при отправке: {str(e)}"
            }

    async def _get_viral_posts(
        self,
        days: int,
        min_score: float,
        channel: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Получить виральные посты из базы данных.

        Args:
            days: Период в днях
            min_score: Минимальный viral score
            channel: Фильтр по каналу

        Returns:
            Список виральных постов
        """
        try:
            # Вычисляем дату начала периода
            start_date = datetime.now() - timedelta(days=days)

            # Формируем запрос к Supabase
            query = self.supabase.client.table('posts').select(
                'id, message_id, channel_username, channel_title, text_preview, '
                'viral_score, engagement_rate, views, forwards, reactions, '
                'permalink, date'
            ).gte('date', start_date.isoformat())

            # Добавляем фильтры
            if min_score > 0:
                query = query.gte('viral_score', min_score)

            if channel:
                query = query.eq('channel_username', channel)

            # Сортируем по viral_score
            query = query.order('viral_score', desc=True).limit(20)

            response = query.execute()

            if response.data:
                logger.info(f"Retrieved {len(response.data)} viral posts from database")
                return response.data
            else:
                logger.info("No viral posts found in database")
                return []

        except Exception as e:
            logger.error(f"Error retrieving viral posts: {e}", exc_info=True)
            return []

    async def _analyze_trends(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анализировать тренды через LLM.

        Args:
            posts: Список виральных постов

        Returns:
            Dict с анализом трендов
        """
        try:
            if not posts:
                return {"summary": "Недостаточно данных для анализа", "recommendations": []}

            # Включаем debug режим для детального логирования
            session_id = f"trends_analysis_{int(asyncio.get_event_loop().time())}"
            self.orchestrator.enable_debug_mode(session_id)

            # Подготавливаем данные для анализа
            posts_text = self._prepare_posts_for_analysis(posts)

            # Создаем задачу для LLM
            analysis_task = {
                "type": "viral_trends_analysis",
                "posts": posts_text,
                "count": len(posts)
            }

            # Запускаем анализ через оркестратор
            result = await self.orchestrator.process_trends_analysis(analysis_task)

            if result.overall_success:
                logger.info("Successfully analyzed trends with LLM")
                return result.final_data
            else:
                logger.warning(f"LLM analysis failed: {result.error}")
                # Возвращаем debug логи если есть
                debug_info = getattr(self.orchestrator, 'debug_log', [])
                if debug_info:
                    logger.info(f"Debug logs: {debug_info[-5:]}")  # Показываем последние 5 записей
                return {
                    "summary": "Не удалось выполнить анализ трендов через ИИ",
                    "recommendations": [],
                    "debug_info": debug_info[-10:] if debug_info else None  # Последние 10 записей
                }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}", exc_info=True)
            return {
                "summary": f"Ошибка при анализе трендов: {str(e)}",
                "recommendations": []
            }

    def _prepare_posts_for_analysis(self, posts: List[Dict[str, Any]]) -> str:
        """
        Подготовить посты для анализа LLM.

        Args:
            posts: Список постов

        Returns:
            Форматированный текст для анализа
        """
        posts_text = []

        for i, post in enumerate(posts[:20], 1):  # Анализируем топ 20 постов
            title = post.get('channel_title', 'Unknown')
            text = post.get('text_preview', '')[:500]  # Ограничиваем длину
            viral_score = post.get('viral_score', 0)
            views = post.get('views', 0)

            post_summary = f"""
Пост {i}:
Канал: {title}
Viral Score: {viral_score:.1f}
Просмотры: {views:,}
Текст: {text}
---
"""
            posts_text.append(post_summary)

        return "\n".join(posts_text)

    def _format_report(
        self,
        posts: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        days: int
    ) -> str:
        """
        Форматировать отчет для Telegram.

        Args:
            posts: Список постов
            analysis: Результат анализа
            days: Период анализа

        Returns:
            Отформатированный отчет
        """
        # Используем статический метод из TelegramBotService
        return TelegramBotService._format_viral_report({
            "posts": posts,
            "analysis": analysis,
            "period_days": days
        })

