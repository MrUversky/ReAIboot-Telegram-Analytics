"""
Supabase клиент для интеграции с базой данных.
Обеспечивает хранение и извлечение данных постов, анализов и сценариев.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from supabase import create_client, Client
from postgrest.exceptions import APIError

from .settings import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клиент для работы с Supabase."""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()

    def _initialize_client(self):
        """Инициализация Supabase клиента."""
        try:
            if not settings.supabase_url or not settings.supabase_anon_key:
                logger.warning("Supabase credentials not found, running without database")
                return

            self.client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_anon_key
            )
            logger.info("Supabase client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Проверка подключения к Supabase."""
        if not self.client:
            return False

        try:
            # Простая проверка подключения
            result = self.client.table('channels').select('count').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection check failed: {e}")
            return False

    # ===== КАНАЛЫ =====

    def get_channels(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Получить список каналов."""
        if not self.client:
            return []

        try:
            query = self.client.table('channels').select('*')
            if active_only:
                query = query.eq('is_active', True)

            result = query.order('username').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching channels: {e}")
            return []

    def upsert_channel(self, username: str, title: str = None, description: str = None) -> bool:
        """Добавить или обновить канал."""
        if not self.client:
            return False

        try:
            data = {
                'username': username,
                'title': title,
                'description': description,
                'updated_at': datetime.utcnow().isoformat()
            }

            result = self.client.table('channels').upsert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error upserting channel {username}: {e}")
            return False

    def update_channel_last_parsed(self, username: str) -> bool:
        """Обновить время последнего парсинга канала."""
        if not self.client:
            return False

        try:
            result = self.client.table('channels').update({
                'last_parsed': datetime.utcnow().isoformat()
            }).eq('username', username).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating channel last_parsed for {username}: {e}")
            return False

    # ===== ПОСТЫ =====

    def is_post_processed(self, message_id: int, channel_username: str,
                         analysis_type: str = None) -> bool:
        """Проверить, был ли пост уже обработан."""
        if not self.client:
            return False

        try:
            post_id = f"{message_id}_{channel_username}"
            query = self.client.table('post_analysis').select('id').eq('post_id', post_id)

            if analysis_type:
                query = query.eq('analysis_type', analysis_type)

            result = query.eq('status', 'completed').execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if post is processed: {e}")
            return False

    def save_posts_batch(self, posts: List[Dict[str, Any]]) -> int:
        """Сохранить batch постов в базу данных."""
        if not self.client:
            return 0

        try:
            # Подготовим данные для вставки
            posts_data = []
            for post in posts:
                post_data = {
                    'id': f"{post['message_id']}_{post['channel_username']}",
                    'message_id': post['message_id'],
                    'channel_username': post['channel_username'],
                    'channel_title': post.get('channel_title'),
                    'date': post['date'],
                    'text_preview': post.get('text_preview', '')[:500],  # Ограничим длину
                    'full_text': post.get('text', ''),
                    'views': post.get('views', 0),
                    'forwards': post.get('forwards', 0),
                    'replies': post.get('replies', 0),
                    'reactions': post.get('reactions', 0),
                    'participants_count': post.get('participants_count', 0),
                    'has_media': post.get('has_media', False),
                    'permalink': post.get('permalink'),
                    'raw_data': json.dumps(post)
                }
                posts_data.append(post_data)

            if posts_data:
                # Используем upsert для обновления существующих записей
                result = self.client.table('posts').upsert(posts_data).execute()
                saved_count = len(result.data)
                logger.info(f"Saved {saved_count} posts to database")
                return saved_count
            else:
                return 0

        except Exception as e:
            logger.error(f"Error saving posts batch: {e}")
            return 0

    def get_recent_posts(self, days: int = 7, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получить недавние посты."""
        if not self.client:
            return []

        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            result = (self.client.table('posts')
                     .select('*')
                     .gte('date', since_date.isoformat())
                     .order('date', desc=True)
                     .limit(limit)
                     .execute())
            return result.data
        except Exception as e:
            logger.error(f"Error fetching recent posts: {e}")
            return []

    # ===== МЕТРИКИ =====

    def save_post_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Сохранить метрики постов."""
        if not self.client:
            return 0

        try:
            result = self.client.table('post_metrics').insert(metrics).execute()
            return len(result.data)
        except Exception as e:
            logger.error(f"Error saving post metrics: {e}")
            return 0

    def get_post_metrics(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Получить метрики поста."""
        if not self.client:
            return None

        try:
            result = (self.client.table('post_metrics')
                     .select('*')
                     .eq('post_id', post_id)
                     .order('calculated_at', desc=True)
                     .limit(1)
                     .execute())

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching post metrics for {post_id}: {e}")
            return None

    # ===== АНАЛИЗ ПОСТОВ =====

    def save_post_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Сохранить результаты анализа поста."""
        if not self.client:
            return False

        try:
            # Добавим дополнительные поля
            analysis_data['updated_at'] = datetime.utcnow().isoformat()

            result = self.client.table('post_analysis').upsert(analysis_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error saving post analysis: {e}")
            return False

    def get_post_analysis(self, post_id: str, analysis_type: str = None) -> Optional[Dict[str, Any]]:
        """Получить анализ поста."""
        if not self.client:
            return None

        try:
            query = self.client.table('post_analysis').select('*').eq('post_id', post_id)

            if analysis_type:
                query = query.eq('analysis_type', analysis_type)

            result = query.order('created_at', desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching post analysis for {post_id}: {e}")
            return None

    def update_analysis_status(self, analysis_id: int, status: str,
                              tokens_used: int = None, cost_usd: float = None,
                              processing_time: float = None) -> bool:
        """Обновить статус анализа."""
        if not self.client:
            return False

        try:
            update_data = {'status': status}
            if tokens_used is not None:
                update_data['tokens_used'] = tokens_used
            if cost_usd is not None:
                update_data['cost_usd'] = cost_usd
            if processing_time is not None:
                update_data['processing_time_seconds'] = processing_time

            result = (self.client.table('post_analysis')
                     .update(update_data)
                     .eq('id', analysis_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating analysis status: {e}")
            return False

    # ===== СЦЕНАРИИ =====

    def save_scenarios(self, scenarios: List[Dict[str, Any]]) -> int:
        """Сохранить сгенерированные сценарии."""
        if not self.client:
            return 0

        try:
            result = self.client.table('scenarios').insert(scenarios).execute()
            saved_count = len(result.data)
            logger.info(f"Saved {saved_count} scenarios to database")
            return saved_count
        except Exception as e:
            logger.error(f"Error saving scenarios: {e}")
            return 0

    def get_scenarios_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        """Получить сценарии для поста."""
        if not self.client:
            return []

        try:
            result = (self.client.table('scenarios')
                     .select('*')
                     .eq('post_id', post_id)
                     .order('created_at', desc=True)
                     .execute())
            return result.data
        except Exception as e:
            logger.error(f"Error fetching scenarios for post {post_id}: {e}")
            return []

    def update_scenario_status(self, scenario_id: int, status: str) -> bool:
        """Обновить статус сценария."""
        if not self.client:
            return False

        try:
            result = (self.client.table('scenarios')
                     .update({'status': status})
                     .eq('id', scenario_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating scenario status: {e}")
            return False

    # ===== ТОКЕНЫ И СТАТИСТИКА =====

    def save_token_usage(self, usage_data: Dict[str, Any]) -> bool:
        """Сохранить использование токенов."""
        if not self.client:
            return False

        try:
            result = self.client.table('token_usage').insert(usage_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error saving token usage: {e}")
            return False

    def get_token_usage_stats(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Получить статистику использования токенов."""
        if not self.client:
            return {}

        try:
            # Вызываем PostgreSQL функцию
            params = {}
            if user_id:
                params['p_user_id'] = user_id
            if days:
                params['p_days'] = days

            result = self.client.rpc('get_token_usage_summary', params).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error fetching token usage stats: {e}")
            return {}

    # ===== СИСТЕМНЫЙ МОНИТОРИНГ =====

    def save_system_log(self, level: str, component: str, message: str,
                       details: Dict[str, Any] = None, user_id: str = None) -> bool:
        """Сохранить системный лог."""
        if not self.client:
            return False

        try:
            log_data = {
                'level': level,
                'component': component,
                'message': message,
                'details': json.dumps(details) if details else None,
                'user_id': user_id
            }

            result = self.client.table('system_logs').insert(log_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error saving system log: {e}")
            return False

    def get_system_health(self) -> Dict[str, Any]:
        """Получить показатели здоровья системы."""
        if not self.client:
            return {}

        try:
            result = self.client.rpc('get_system_health').execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error fetching system health: {e}")
            return {}

    def start_parsing_session(self, channels_count: int, user_id: str = None) -> Optional[int]:
        """Начать сессию парсинга."""
        if not self.client:
            return None

        try:
            session_data = {
                'channels_parsed': channels_count,
                'initiated_by': user_id,
                'configuration': json.dumps({
                    'channels_count': channels_count,
                    'started_at': datetime.utcnow().isoformat()
                })
            }

            result = self.client.table('parsing_sessions').insert(session_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error starting parsing session: {e}")
            return None

    def complete_parsing_session(self, session_id: int, posts_found: int) -> bool:
        """Завершить сессию парсинга."""
        if not self.client:
            return False

        try:
            result = (self.client.table('parsing_sessions')
                     .update({
                         'completed_at': datetime.utcnow().isoformat(),
                         'posts_found': posts_found,
                         'status': 'completed'
                     })
                     .eq('id', session_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error completing parsing session: {e}")
            return False

    # ===== РУБРИКИ И ФОРМАТЫ =====

    def get_rubrics(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Получить список рубрик."""
        if not self.client:
            return []

        try:
            query = self.client.table('rubrics').select('*')
            if active_only:
                query = query.eq('is_active', True)

            result = query.order('name').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching rubrics: {e}")
            return []

    def get_reel_formats(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Получить список форматов reels."""
        if not self.client:
            return []

        try:
            query = self.client.table('reel_formats').select('*')
            if active_only:
                query = query.eq('is_active', True)

            result = query.order('name').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching reel formats: {e}")
            return []

    def get_rubric_formats(self, rubric_id: str = None) -> List[Dict[str, Any]]:
        """Получить связи рубрик и форматов."""
        if not self.client:
            return []

        try:
            query = self.client.table('rubric_formats').select('*, rubrics(*), reel_formats(*)')

            if rubric_id:
                query = query.eq('rubric_id', rubric_id)

            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching rubric formats: {e}")
            return []


# Глобальный экземпляр клиента
supabase_client = SupabaseClient()
