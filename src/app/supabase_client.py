"""
Supabase клиент для интеграции с базой данных.
Обеспечивает хранение и извлечение данных постов, анализов и сценариев.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
try:
    from supabase import create_client, Client
    from postgrest.exceptions import APIError
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None
    APIError = Exception

from .settings import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клиент для работы с Supabase."""

    def __init__(self):
        self.client: Optional[Any] = None
        self._initialize_client()

    def _initialize_client(self):
        """Инициализация Supabase клиента."""
        try:
            if not SUPABASE_AVAILABLE:
                logger.warning("Supabase library not available, running without database")
                return

            if not settings.supabase_url:
                logger.warning("Supabase URL not found, running without database")
                return

            # Используем сервисный ключ, если он доступен (обходит RLS)
            api_key = settings.supabase_service_role_key or settings.supabase_anon_key

            if not api_key:
                logger.warning("No Supabase API key found, running without database")
                return

            self.client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=api_key
            )

            key_type = "service role" if settings.supabase_service_role_key else "anonymous"
            logger.info(f"Supabase client initialized successfully (using {key_type} key)")

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
            # Нормализуем username - ВСЕГДА добавляем @ для консистентности
            canonical_username = username if username.startswith('@') else f'@{username}'

            # Сначала проверим, существует ли уже канал с таким username
            existing_channel = None

            # Ищем канал с каноническим username (с @)
            existing_canonical = self.client.table('channels').select('*').eq('username', canonical_username).execute()
            if existing_canonical.data:
                existing_channel = existing_canonical.data[0]

            # Если не нашли с @, ищем без @ (старый формат)
            if not existing_channel:
                existing_legacy = self.client.table('channels').select('*').eq('username', username.lstrip('@')).execute()
                if existing_legacy.data:
                    existing_channel = existing_legacy.data[0]
                    # Если нашли старый формат, обновим его до канонического
                    logger.info(f"Found legacy channel {existing_channel['username']}, updating to canonical format")

            if existing_channel:
                # Обновляем существующий канал
                update_data = {
                    'username': canonical_username,  # Всегда используем канонический формат
                    'title': title,
                    'description': description,
                    'updated_at': datetime.utcnow().isoformat()
                }
                result = (self.client.table('channels')
                         .update(update_data)
                         .eq('id', existing_channel['id'])
                         .execute())
                logger.info(f"Updated existing channel {existing_channel['username']} with title '{title}'")
                return len(result.data) > 0
            else:
                # Создаем новый канал с каноническим username
                data = {
                    'username': canonical_username,
                    'title': title,
                    'description': description,
                    'updated_at': datetime.utcnow().isoformat()
                }
                result = self.client.table('channels').insert(data).execute()
                logger.info(f"Created new channel {canonical_username} with title '{title}'")
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

    def ensure_channel_exists(self, channel_username: str, channel_info: Dict[str, Any] = None) -> bool:
        """Убедиться, что канал существует в базе данных."""
        # Используем единый метод upsert_channel для консистентности
        channel_title = channel_info.get('title') if channel_info else None
        channel_description = channel_info.get('about') if channel_info else None
        return self.upsert_channel(channel_username, channel_title, channel_description)

    def save_posts_batch(self, posts: List[Dict[str, Any]], channel_username: str = None, channel_info: Dict[str, Any] = None) -> int:
        """Сохранить batch постов в базу данных."""
        if not self.client:
            return 0

        try:
            # Сначала убедимся, что канал существует
            if channel_username and posts:
                channel_title = channel_info.get('title') if channel_info else None
                channel_description = channel_info.get('about') if channel_info else None
                self.upsert_channel(channel_username, channel_title, channel_description)

            # Подготовим данные для вставки
            posts_data = []
            for post in posts:
                post_data = {
                    'id': f"{post['message_id']}_{post['channel_username'] if post['channel_username'].startswith('@') else '@' + post['channel_username']}",
                    'message_id': post['message_id'],
                    'channel_username': post['channel_username'] if post['channel_username'].startswith('@') else f"@{post['channel_username']}",
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
                # Используем upsert для избежания дубликатов и обновления статистики существующих постов
                result = (self.client.table('posts')
                         .upsert(
                             posts_data,
                             on_conflict='id',
                             ignore_duplicates=False  # Обновляем существующие записи
                         )
                         .execute())
                saved_count = len(result.data)
                logger.info(f"Saved/updated {saved_count} posts to database")
                return saved_count
            else:
                return 0

        except Exception as e:
            logger.error(f"Error saving posts batch: {e}")
            # Добавим отладочную информацию
            if posts_data:
                logger.error(f"First post data: {posts_data[0]}")
                logger.error(f"Channel username in post: {posts_data[0].get('channel_username')}")
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

    def save_parsing_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Сохранить сессию парсинга и вернуть результат."""
        if not self.client:
            raise Exception("Supabase client not initialized")

        try:
            # Добавляем timestamp если не указан
            if 'started_at' not in session_data:
                session_data['started_at'] = datetime.utcnow().isoformat()

            result = self.client.table('parsing_sessions').insert(session_data).execute()

            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created parsing session with ID: {session_id}")
                return {'id': session_id}
            else:
                raise Exception("Failed to create parsing session")
        except Exception as e:
            logger.error(f"Error saving parsing session: {e}")
            raise e

    def get_parsing_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные сессии парсинга по ID."""
        if not self.client:
            return None

        try:
            result = (self.client.table('parsing_sessions')
                     .select('*')
                     .eq('id', session_id)
                     .execute())

            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting parsing session {session_id}: {e}")
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

    def update_parsing_session(self, session_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновить данные сессии парсинга."""
        if not self.client:
            return False

        try:
            result = (self.client.table('parsing_sessions')
                     .update(update_data)
                     .eq('id', session_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating parsing session {session_id}: {e}")
            return False

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Получить канал по ID."""
        if not self.client:
            return None

        try:
            result = (self.client.table('channels')
                     .select('*')
                     .eq('id', channel_id)
                     .execute())
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching channel {channel_id}: {e}")
            return None

    def update_channel(self, channel_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновить данные канала."""
        if not self.client:
            return False

        try:
            # Добавляем timestamp обновления
            update_data['updated_at'] = datetime.utcnow().isoformat()

            result = (self.client.table('channels')
                     .update(update_data)
                     .eq('id', channel_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating channel {channel_id}: {e}")
            return False

    def delete_channel(self, channel_id: str) -> bool:
        """Удалить канал."""
        if not self.client:
            return False

        try:
            result = (self.client.table('channels')
                     .delete()
                     .eq('id', channel_id)
                     .execute())
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting channel {channel_id}: {e}")
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

    # === МЕТОДЫ ДЛЯ РАБОТЫ С СИСТЕМНЫМИ НАСТРОЙКАМИ ===

    def get_system_setting(self, key: str) -> Optional[Any]:
        """Получить системную настройку по ключу."""
        if not self.client:
            return None

        try:
            result = self.client.table('system_settings').select('value').eq('key', key).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]['value']
            return None
        except Exception as e:
            logger.error(f"Error getting system setting {key}: {e}")
            return None

    def update_system_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Обновить системную настройку."""
        if not self.client:
            return False

        try:
            update_data = {
                'value': value,
                'updated_at': datetime.now().isoformat()
            }
            if description:
                update_data['description'] = description

            self.client.table('system_settings').update(update_data).eq('key', key).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating system setting {key}: {e}")
            return False

    def get_all_system_settings(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить все системные настройки."""
        if not self.client:
            return []

        try:
            query = self.client.table('system_settings').select('*')
            if category:
                query = query.eq('category', category)

            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching system settings: {e}")
            return []

    # === МЕТОДЫ ДЛЯ РАБОТЫ С БАЗОВЫМИ МЕТРИКАМИ КАНАЛОВ ===

    def get_channel_baseline(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Получить базовые метрики канала."""
        if not self.client:
            return None

        try:
            result = self.client.table('channel_baselines').select('*').eq(
                'channel_username', channel_username
            ).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting channel baseline for {channel_username}: {e}")
            return None

    def save_channel_baseline(self, baseline_data: Dict[str, Any]) -> bool:
        """Сохранить базовые метрики канала."""
        if not self.client:
            return False

        try:
            baseline_data['updated_at'] = datetime.now().isoformat()
            self.client.table('channel_baselines').upsert(
                baseline_data,
                on_conflict='channel_username'
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving channel baseline: {e}")
            return False

    def get_channels_needing_baseline_update(self, max_age_hours: int = 24) -> List[str]:
        """Получить каналы, которым нужно обновить базовые метрики."""
        if not self.client:
            return []

        try:
            cutoff_time = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

            result = self.client.table('channel_baselines').select('channel_username').or_(
                f'last_calculated.lt.{cutoff_time},last_calculated.is.null'
            ).execute()

            return [row['channel_username'] for row in result.data]
        except Exception as e:
            logger.error(f"Error getting channels needing baseline update: {e}")
            return []

    # === МЕТОДЫ ДЛЯ РАБОТЫ С VIRAL МЕТРИКАМИ ПОСТОВ ===

    def update_post_viral_metrics(self, post_id: str, viral_data: Dict[str, Any]) -> bool:
        """Обновить viral метрики поста."""
        if not self.client:
            return False

        try:
            viral_data['last_viral_calculation'] = datetime.now().isoformat()
            viral_data['updated_at'] = datetime.now().isoformat()

            self.client.table('posts').update(viral_data).eq('id', post_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating viral metrics for post {post_id}: {e}")
            return False

    def get_viral_posts(self, channel_username: Optional[str] = None,
                       min_viral_score: float = 1.5, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить 'залетевшие' посты."""
        if not self.client:
            return []

        try:
            query = self.client.table('posts').select('*').gte('viral_score', min_viral_score)

            if channel_username:
                query = query.eq('channel_username', channel_username)

            result = query.order('viral_score', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting viral posts: {e}")
            return []


# Глобальный экземпляр клиента
supabase_client = SupabaseClient()

# Алиас для совместимости с API
SupabaseManager = SupabaseClient