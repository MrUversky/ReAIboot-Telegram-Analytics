"""
Основной FastAPI сервер для ReAIboot.
Предоставляет REST API для всех функций системы.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

# Импорты из нашего проекта
from .app.llm.orchestrator import LLMOrchestrator
from .app.prompts import prompt_manager
from .app.settings import settings
# Импорт TelegramAnalyzer будет сделан ниже с обработкой ошибок
from .app.supabase_client import SupabaseManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="ReAIboot API",
    description="API для анализа Telegram постов и генерации сценариев",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Настройка CORS для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшн указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные объекты
orchestrator = LLMOrchestrator()

# Telegram инициализация (асинхронная)
telegram_analyzer = None
telegram_available = False
telegram_authorization_needed = False

async def init_telegram():
    """Асинхронная инициализация Telegram клиента."""
    global telegram_analyzer, telegram_available, telegram_authorization_needed

    try:
        from .app.telegram_client import TelegramAnalyzer
        telegram_analyzer = TelegramAnalyzer()

        # Проверяем, нужна ли авторизация
        if await telegram_analyzer.needs_authorization():
            logger.warning("Telegram сессия требует авторизации")
            telegram_authorization_needed = True
            telegram_available = False
            return

        await telegram_analyzer.connect()
        telegram_available = True
        telegram_authorization_needed = False
        logger.info("TelegramAnalyzer успешно инициализирован и подключен")
    except ValueError as e:
        logger.warning(f"Не настроены API ключи Telegram: {e}")
        telegram_analyzer = None
        telegram_available = False
    except Exception as e:
        logger.error(f"Ошибка при инициализации TelegramAnalyzer: {e}")
        telegram_analyzer = None
        telegram_available = False

# Инициализация будет выполнена в startup event
supabase_manager = SupabaseManager()

# Startup event для инициализации Telegram
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера."""
    logger.info("🚀 Инициализация ReAIboot API...")

    # Инициализируем Telegram асинхронно
    await init_telegram()

    logger.info("✅ API сервер готов к работе")

# Pydantic модели для запросов/ответов
class PostData(BaseModel):
    message_id: str
    channel_title: str
    text: str
    views: int = 0
    reactions: int = 0
    replies: int = 0
    forwards: int = 0
    score: float = 0.0

class ProcessRequest(BaseModel):
    posts: List[PostData]
    rubric: Optional[Dict[str, Any]] = None
    reel_format: Optional[Dict[str, Any]] = None

class PromptUpdate(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    model_settings: Optional[Dict[str, Any]] = None

class ParsingRequest(BaseModel):
    channel_username: str
    days_back: int = 7
    max_posts: int = 100
    save_to_db: bool = True

class BulkParsingRequest(BaseModel):
    channels: List[str]
    days_back: int = 7
    max_posts: int = 100
    save_to_db: bool = True

class ParsingResponse(BaseModel):
    session_id: int
    channel_username: str
    status: str
    posts_found: int
    posts_processed: int
    started_at: str
    message: str

class ChannelManagementRequest(BaseModel):
    username: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    parse_frequency_hours: int = 24
    max_posts_per_parse: int = 100
    days_back: int = 7

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_status: Dict[str, bool]
    telegram_status: str = "unknown"
    telegram_authorization_needed: bool = False

# Эндпоинты

# Простой health check для мониторинга
@app.get("/health", tags=["health"])
async def simple_health():
    """Простая проверка здоровья системы."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/", tags=["health"])
async def root():
    """Корневой эндпоинт."""
    return {"message": "ReAIboot API", "version": "1.0.0"}

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Проверка здоровья системы."""
    # Проверяем статус Telegram
    telegram_status = "unknown"
    try:
        if telegram_available and telegram_analyzer:
            # Проверяем, есть ли сессия
            import os
            from src.app.settings import settings
            # Telethon автоматически добавляет .session к имени файла
            session_file = f"{settings.telegram_session}.session"
            if os.path.exists(session_file):
                telegram_status = "healthy"
            else:
                telegram_status = "no_session"
        else:
            telegram_status = "unavailable"
    except Exception as e:
        logger.error(f"Error checking Telegram status: {e}")
        telegram_status = "error"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_status=orchestrator.get_processor_status(),
        telegram_status=telegram_status,
        telegram_authorization_needed=telegram_authorization_needed
    )

# Telegram авторизация эндпоинты
@app.post("/api/telegram/start-auth", tags=["telegram"])
async def start_telegram_auth():
    """Запускает процесс авторизации Telegram."""
    global telegram_analyzer, telegram_authorization_needed, telegram_available

    try:
        from .app.telegram_client import TelegramAnalyzer

        # Создаем новый analyzer только если его нет или он не инициализирован
        if telegram_analyzer is None:
            telegram_analyzer = TelegramAnalyzer()

        # Проверяем, нужна ли авторизация
        needs_auth = await telegram_analyzer.needs_authorization()

        if needs_auth:
            logger.info("Запуск процесса авторизации Telegram")
            telegram_authorization_needed = True
            telegram_available = False
            return {
                "status": "auth_needed",
                "message": "Требуется авторизация. Используйте /api/telegram/send-code для отправки кода",
                "can_retry": True
            }
        else:
            # Пытаемся подключиться
            await telegram_analyzer.connect()
            telegram_available = True
            telegram_authorization_needed = False
            return {
                "status": "connected",
                "message": "Успешно подключено к Telegram"
            }

    except Exception as e:
        logger.error(f"Ошибка при запуске авторизации Telegram: {e}")
        telegram_available = False
        telegram_authorization_needed = True
        return {
            "status": "error",
            "message": f"Ошибка: {str(e)}",
            "can_retry": True
        }

@app.post("/api/telegram/send-code", tags=["telegram"])
async def send_telegram_code(phone_data: Dict[str, str]):
    """Отправляет код подтверждения на номер телефона."""
    global auth_client, auth_phone_hash

    try:
        phone = phone_data.get("phone")
        if not phone:
            raise ValueError("Не указан номер телефона")

        # Очищаем предыдущего клиента если он существует
        if auth_client:
            try:
                await auth_client.disconnect()
            except:
                pass
            auth_client = None

        # Используем async клиент правильно
        from telethon import TelegramClient
        import os

        logger.info("Создаем async клиент для авторизации")

        # Создаем async клиент
        api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")

        # Используем основную сессию для авторизации
        session_file = "session_per"
        auth_client = TelegramClient(session_file, api_id, api_hash)

        try:
            # Подключаемся асинхронно
            logger.info("Подключаемся к Telegram...")
            await auth_client.connect()

            # Отправляем код (правильный метод из документации)
            logger.info(f"Отправляем код на номер {phone}")
            sent_code = await auth_client.send_code_request(phone)

            # Сохраняем phone_code_hash для последующей проверки
            auth_phone_hash = sent_code.phone_code_hash

            return {
                "status": "code_sent",
                "message": f"Код отправлен на {phone}",
                "phone_code_hash": sent_code.phone_code_hash
            }

        except Exception as e:
            # Очищаем клиента при ошибке
            if auth_client:
                await auth_client.disconnect()
                auth_client = None
            raise

    except Exception as e:
        logger.error(f"Ошибка при отправке кода: {e}")
        return {
            "status": "error",
            "message": f"Ошибка отправки кода: {str(e)}",
            "can_retry": True
        }

# Глобальная переменная для хранения клиента авторизации
auth_client = None
auth_phone_hash = None

@app.post("/api/telegram/verify-code", tags=["telegram"])
async def verify_telegram_code(code_data: Dict[str, str]):
    """Проверяет код подтверждения."""
    global telegram_available, telegram_authorization_needed, auth_client, auth_phone_hash

    try:
        code = code_data.get("code")
        phone_code_hash = code_data.get("phone_code_hash")

        if not code:
            raise ValueError("Не указан код подтверждения")

        if not auth_client:
            return {
                "status": "error",
                "message": "Сначала нужно отправить код авторизации",
                "can_retry": True
            }

        if phone_code_hash != auth_phone_hash:
            return {
                "status": "error",
                "message": "Неверный phone_code_hash",
                "can_retry": True
            }

        logger.info("Проверяем код с существующим клиентом")

        try:
            # Проверяем код с тем же клиентом
            logger.info(f"Проверяем код: {code}")
            await auth_client.sign_in(phone_code_hash, code)

            # Проверяем авторизацию
            if await auth_client.is_user_authorized():
                logger.info("Успешная авторизация!")
                telegram_available = True
                telegram_authorization_needed = False

                # Сохраняем авторизованного клиента для будущих запросов
                global telegram_analyzer
                if telegram_analyzer:
                    await telegram_analyzer.disconnect()
                telegram_analyzer = auth_client
                auth_client = None  # Очищаем временную переменную

                return {
                    "status": "verified",
                    "message": "Успешно авторизован в Telegram!"
                }
            else:
                raise ValueError("Авторизация не удалась")

        except Exception as e:
            logger.error(f"Ошибка при проверке кода: {e}")
            # Очищаем клиента при ошибке
            if auth_client:
                await auth_client.disconnect()
                auth_client = None
            raise

    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {e}")
        return {
            "status": "error",
            "message": f"Ошибка проверки кода: {str(e)}",
            "can_retry": True
        }

@app.post("/api/telegram/reset-auth", tags=["telegram"])
async def reset_telegram_auth():
    """Сбрасывает авторизацию Telegram для повторного входа."""
    global telegram_analyzer, telegram_available, telegram_authorization_needed

    try:
        # Отключаем существующий клиент
        if telegram_analyzer:
            try:
                await telegram_analyzer.disconnect()
            except Exception as e:
                logger.warning(f"Ошибка при отключении клиента: {e}")

        # Удаляем файлы сессии
        import os
        from .app.settings import settings

        session_files = [
            f"{settings.telegram_session}.session",
            f"{settings.telegram_session}.session-journal",
            f"{settings.telegram_session}.session.backup"
        ]

        for session_file in session_files:
            try:
                if os.path.exists(session_file):
                    os.remove(session_file)
                    logger.info(f"Удален файл сессии: {session_file}")
            except Exception as e:
                logger.warning(f"Не удалось удалить {session_file}: {e}")

        # Сбрасываем состояние
        telegram_analyzer = None
        telegram_available = False
        telegram_authorization_needed = True

        logger.info("Авторизация Telegram сброшена")
        return {
            "status": "reset",
            "message": "Авторизация сброшена. Можно начать заново."
        }

    except Exception as e:
        logger.error(f"Ошибка при сбросе авторизации: {e}")
        return {
            "status": "error",
            "message": f"Ошибка сброса: {str(e)}"
        }

# LLM эндпоинты

@app.post("/api/llm/process", tags=["llm"])
async def process_posts(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Обработать посты через LLM пайплайн.

    - **posts**: Список постов для обработки
    - **rubric**: Рубрика для всех постов (опционально)
    - **reel_format**: Формат для всех постов (опционально)
    """
    try:
        # Преобразуем Pydantic модели в словари
        posts_data = [post.model_dump() for post in request.posts]

        # Запускаем обработку в фоне
        background_tasks.add_task(process_posts_background, posts_data, request.rubric, request.reel_format)

        return {"message": "Обработка запущена в фоне", "posts_count": len(posts_data)}

    except Exception as e:
        logger.error(f"Ошибка при запуске обработки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

async def process_posts_background(posts_data: List[Dict], rubric: Optional[Dict], reel_format: Optional[Dict]):
    """Фоновая обработка постов."""
    try:
        logger.info(f"Начинаем обработку {len(posts_data)} постов")

        results = await orchestrator.process_posts_batch(
            posts=posts_data,
            rubric=rubric,
            reel_format=reel_format,
            concurrency=3  # Обрабатываем по 3 поста одновременно
        )

        logger.info(f"Обработка завершена: {len(results)} результатов")

        # TODO: Сохранить результаты в базу данных
        # await save_results_to_db(results)

    except Exception as e:
        logger.error(f"Ошибка в фоновой обработке: {e}")

@app.post("/api/llm/test/{template_name}", tags=["llm"])
async def test_prompt_template(template_name: str, variables: Dict[str, Any]):
    """Протестировать шаблон промпта."""
    try:
        rendered = prompt_manager.render_prompt(template_name, variables)
        return {
            "template_name": template_name,
            "rendered": rendered,
            "variables_used": variables
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Шаблон не найден: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестирования: {str(e)}")

# Управление промптами

@app.get("/api/prompts", tags=["prompts"])
async def get_all_prompts():
    """Получить все шаблоны промптов."""
    try:
        templates = prompt_manager.get_all_templates()
        result = {}

        for name, template in templates.items():
            result[name] = {
                "name": template.name,
                "description": template.description,
                "system_prompt": template.system_prompt,
                "user_prompt": template.user_prompt,
                "variables": template.variables,
                "model_settings": template.model_settings
            }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения промптов: {str(e)}")

@app.get("/api/prompts/{template_name}", tags=["prompts"])
async def get_prompt(template_name: str):
    """Получить конкретный шаблон промпта."""
    try:
        template = prompt_manager.get_template(template_name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Шаблон {template_name} не найден")

        return {
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt,
            "variables": template.variables,
            "model_settings": template.model_settings
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения промпта: {str(e)}")

@app.put("/api/prompts/{template_name}", tags=["prompts"])
async def update_prompt(template_name: str, updates: PromptUpdate):
    """Обновить шаблон промпта."""
    try:
        if template_name not in prompt_manager.templates:
            raise HTTPException(status_code=404, detail=f"Шаблон {template_name} не найден")

        # Преобразуем в словарь, исключая None значения
        update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)

        prompt_manager.update_template(template_name, update_dict)
        prompt_manager.save_templates_to_file()

        return {"message": f"Промпт {template_name} обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления промпта: {str(e)}")

# Контекст проекта

@app.get("/api/context/project", tags=["context"])
async def get_project_context():
    """Получить контекст проекта."""
    return prompt_manager.project_context

@app.put("/api/context/project", tags=["context"])
async def update_project_context(context: Dict[str, Any]):
    """Обновить контекст проекта."""
    try:
        prompt_manager.project_context.update(context)
        prompt_manager.save_templates_to_file()
        return {"message": "Контекст проекта обновлен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления контекста: {str(e)}")

# === НОВЫЕ API ЭНДПОИНТЫ ДЛЯ VIRAL DETECTION ===

# Системные настройки

@app.get("/api/settings", tags=["settings"])
async def get_system_settings(category: Optional[str] = None):
    """Получить системные настройки."""
    try:
        settings = supabase_manager.get_all_system_settings(category)
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@app.get("/api/settings/{key}", tags=["settings"])
async def get_system_setting(key: str):
    """Получить конкретную системную настройку."""
    try:
        setting = supabase_manager.get_system_setting(key)
        if setting is None:
            raise HTTPException(status_code=404, detail=f"Настройка {key} не найдена")
        return {"key": key, "value": setting}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настройки: {str(e)}")

@app.put("/api/settings/{key}", tags=["settings"])
async def update_system_setting(key: str, value: Any, description: Optional[str] = None):
    """Обновить системную настройку."""
    try:
        success = supabase_manager.update_system_setting(key, value, description)
        if not success:
            raise HTTPException(status_code=500, detail=f"Не удалось обновить настройку {key}")
        return {"message": f"Настройка {key} обновлена"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настройки: {str(e)}")

# Базовые метрики каналов

@app.get("/api/channels/baselines", tags=["channels"])
async def get_channel_baselines():
    """Получить базовые метрики всех каналов."""
    try:
        # Получаем все каналы с базовыми метриками
        channels = supabase_manager.client.table('channels').select('*').execute()
        baselines = []

        for channel in channels.data:
            baseline = supabase_manager.get_channel_baseline(channel['username'])
            if baseline:
                baselines.append({
                    'channel': channel,
                    'baseline': baseline
                })

        return {"baselines": baselines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения базовых метрик: {str(e)}")

@app.get("/api/channels/{channel_username}/baseline", tags=["channels"])
async def get_channel_baseline(channel_username: str):
    """Получить базовые метрики конкретного канала."""
    try:
        baseline = supabase_manager.get_channel_baseline(channel_username)
        if not baseline:
            raise HTTPException(status_code=404, detail=f"Базовые метрики для канала {channel_username} не найдены")

        return {"baseline": baseline}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения базовых метрик: {str(e)}")

@app.post("/api/channels/{channel_username}/baseline/calculate", tags=["channels"])
async def calculate_channel_baseline(channel_username: str):
    """Пересчитать базовые метрики канала."""
    try:
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

        analyzer = ChannelBaselineAnalyzer(supabase_manager)
        baseline = analyzer.calculate_channel_baseline(channel_username)

        if not baseline:
            raise HTTPException(status_code=400, detail=f"Недостаточно данных для расчета базовых метрик канала {channel_username}")

        # Сохраняем рассчитанные метрики
        success = analyzer.save_channel_baseline(baseline)
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось сохранить базовые метрики")

        return {"message": f"Базовые метрики канала {channel_username} пересчитаны", "baseline": baseline.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета базовых метрик: {str(e)}")

@app.post("/api/channels/baselines/update", tags=["channels"])
async def update_all_channel_baselines():
    """Обновить базовые метрики для всех каналов."""
    try:
        from .app.smart_top_posts_filter import SmartTopPostsFilter

        filter = SmartTopPostsFilter(supabase_manager)
        channels = supabase_manager.get_channels_needing_baseline_update()

        if not channels:
            return {"message": "Нет каналов, требующих обновления базовых метрик"}

        stats = filter.update_channel_baselines(channels)
        return {"message": f"Обновлено базовых метрик для {stats['updated']} каналов", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления базовых метрик: {str(e)}")

# Viral посты

@app.get("/api/posts/viral", tags=["posts"])
async def get_viral_posts(channel_username: Optional[str] = None,
                         min_viral_score: float = 1.5, limit: int = 100):
    """Получить 'залетевшие' посты."""
    try:
        posts = supabase_manager.get_viral_posts(channel_username, min_viral_score, limit)
        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения viral постов: {str(e)}")

@app.post("/api/posts/{post_id}/viral/update", tags=["posts"])
async def update_post_viral_metrics(post_id: str):
    """Пересчитать viral метрики для поста."""
    try:
        from .app.viral_post_detector import ViralPostDetector
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

        # Получаем данные поста
        post_result = supabase_manager.client.table('posts').select('*').eq('id', post_id).execute()
        if not post_result.data:
            raise HTTPException(status_code=404, detail=f"Пост {post_id} не найден")

        post = post_result.data[0]
        channel_username = post['channel_username']

        # Получаем базовые метрики канала
        baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
        baseline = baseline_analyzer.get_channel_baseline(channel_username)

        if not baseline:
            raise HTTPException(status_code=400, detail=f"Нет базовых метрик для канала {channel_username}")

        # Анализируем пост
        detector = ViralPostDetector(baseline_analyzer)
        result = detector.analyze_post_virality(post, baseline)

        # Обновляем метрики
        success = detector.update_post_viral_metrics(post_id, result)
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось обновить viral метрики")

        return {"message": f"Viral метрики поста {post_id} обновлены", "result": result.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления viral метрик: {str(e)}")

# Статистика и метрики

@app.get("/api/stats/llm", tags=["stats"])
async def get_llm_stats():
    """Получить статистику использования LLM."""
    return {
        "processor_status": orchestrator.get_processor_status(),
        "available_templates": list(prompt_manager.get_all_templates().keys()),
        "project_context_keys": list(prompt_manager.project_context.keys())
    }

@app.get("/api/stats/health", tags=["stats"])
async def get_system_health():
    """Получить статистику здоровья системы."""
    try:
        # Получаем реальную статистику из базы данных
        try:
            # Общее количество постов
            posts_result = supabase_manager.client.table('posts').select('*', count='exact').execute()
            total_posts = posts_result.count

            # Посты за сегодня
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            posts_today_result = (supabase_manager.client.table('posts')
                                .select('*', count='exact')
                                .gte('date', today.isoformat())
                                .execute())
            posts_today = posts_today_result.count

            # Активные каналы
            channels_result = supabase_manager.client.table('channels').select('*', count='exact').execute()
            active_channels = channels_result.count

            # Недавний анализ (LLM запросы за последние 7 дней)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_analysis = 0  # Пока заглушка, можно добавить позже

            # Среднее время обработки
            avg_processing_time = 0.0  # Пока заглушка

            # Процент ошибок
            error_rate = 0.0  # Пока заглушка

            return {
                "total_posts": total_posts,
                "posts_today": posts_today,
                "active_channels": active_channels,
                "recent_analysis": recent_analysis,
                "avg_processing_time": avg_processing_time,
                "error_rate": error_rate
            }
        except Exception as e:
            logger.error(f"Error getting stats from database: {e}")
            # Возвращаем заглушку в случае ошибки
            return {
                "total_posts": 0,
                "posts_today": 0,
                "active_channels": 0,
                "recent_analysis": 0,
                "avg_processing_time": 0.0,
                "error_rate": 0.0
            }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@app.get("/api/stats/tokens", tags=["stats"])
async def get_token_usage_stats(user_id: Optional[str] = None, days: int = 30):
    """Получить статистику использования токенов."""
    try:
        # Пока возвращаем заглушку
        return {
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_cost_per_token": 0.0,
            "models_used": [],
            "operations_count": 0
        }
    except Exception as e:
        logger.error(f"Error getting token usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get token usage stats")

# Эндпоинты для парсинга каналов

@app.post("/api/parsing/channel", response_model=ParsingResponse, tags=["parsing"])
async def parse_single_channel(request: ParsingRequest, background_tasks: BackgroundTasks):
    """
    Запустить парсинг одного канала.

    - **channel_username**: Username канала (например: @dnevteh)
    - **days_back**: Количество дней назад для парсинга (по умолчанию 7)
    - **max_posts**: Максимальное количество постов (по умолчанию 100)
    - **save_to_db**: Сохранять ли результаты в базу данных
    """
    try:
        logger.info(f"Запуск парсинга канала {request.channel_username}")

        # Создаем сессию парсинга в базе данных
        session_data = {
            'started_at': datetime.now().isoformat(),
            'status': 'running',
            'channels_parsed': 1,
            'posts_found': 0,
            'initiated_by': None  # TODO: получить реального пользователя
        }

        # Сохраняем сессию
        session_result = supabase_manager.save_parsing_session(session_data)
        session_id = session_result['id']

        # Запускаем парсинг в фоне
        background_tasks.add_task(
            parse_channel_background,
            request.channel_username,
            request.days_back,
            request.max_posts,
            request.save_to_db,
            session_id
        )

        return ParsingResponse(
            session_id=session_id,
            channel_username=request.channel_username,
            status="running",
            posts_found=0,
            posts_processed=0,
            started_at=session_data['started_at'],
            message=f"Парсинг канала {request.channel_username} запущен"
        )

    except Exception as e:
        logger.error(f"Ошибка при запуске парсинга канала: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска парсинга: {str(e)}")

@app.post("/api/parsing/bulk", tags=["parsing"])
async def parse_multiple_channels(request: BulkParsingRequest, background_tasks: BackgroundTasks):
    """
    Запустить парсинг нескольких каналов.

    - **channels**: Список username каналов
    - **days_back**: Количество дней назад для парсинга (по умолчанию 7)
    - **max_posts**: Максимальное количество постов на канал (по умолчанию 100)
    - **save_to_db**: Сохранять ли результаты в базу данных
    """
    try:
        logger.info(f"Запуск массового парсинга {len(request.channels)} каналов")

        # Создаем сессию парсинга
        session_data = {
            'started_at': datetime.now().isoformat(),
            'status': 'running',
            'channels_parsed': len(request.channels),
            'posts_found': 0,
            'initiated_by': None
        }

        session_result = supabase_manager.save_parsing_session(session_data)
        session_id = session_result['id']

        # Запускаем парсинг всех каналов в фоне
        background_tasks.add_task(
            parse_channels_bulk_background,
            request.channels,
            request.days_back,
            request.max_posts,
            request.save_to_db,
            session_id
        )

        return {
            "session_id": session_id,
            "channels_count": len(request.channels),
            "status": "running",
            "message": f"Массовый парсинг {len(request.channels)} каналов запущен"
        }

    except Exception as e:
        logger.error(f"Ошибка при запуске массового парсинга: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска парсинга: {str(e)}")

@app.get("/api/parsing/session/{session_id}", tags=["parsing"])
async def get_parsing_session_status(session_id: int):
    """
    Получить статус сессии парсинга.

    - **session_id**: ID сессии парсинга
    """
    try:
        session_data = supabase_manager.get_parsing_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Сессия парсинга {session_id} не найдена")

        return {
            "session_id": session_id,
            "status": session_data.get("status"),
            "started_at": session_data.get("started_at"),
            "completed_at": session_data.get("completed_at"),
            "channels_parsed": session_data.get("channels_parsed", 0),
            "posts_found": session_data.get("posts_found", 0),
            "error_message": session_data.get("error_message")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статуса сессии {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса сессии: {str(e)}")

@app.put("/api/channels/{channel_id}", tags=["channels"])
async def update_channel_settings(channel_id: int, request: ChannelManagementRequest):
    """
    Обновить настройки канала.

    - **channel_id**: ID канала в базе данных
    - **username**: Username канала
    - **title**: Название канала
    - **description**: Описание канала
    - **category**: Категория канала
    - **is_active**: Активен ли канал
    - **parse_frequency_hours**: Частота парсинга в часах
    - **max_posts_per_parse**: Максимум постов за раз
    - **days_back**: Дни назад для парсинга
    """
    try:
        update_data = request.model_dump()
        result = supabase_manager.update_channel(channel_id, update_data)

        return {
            "message": "Настройки канала обновлены",
            "channel": result
        }

    except Exception as e:
        logger.error(f"Ошибка обновления канала: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {str(e)}")

@app.delete("/api/channels/{channel_id}", tags=["channels"])
async def delete_channel(channel_id: int):
    """Удалить канал."""
    try:
        supabase_manager.delete_channel(channel_id)
        return {"message": "Канал удален"}

    except Exception as e:
        logger.error(f"Ошибка удаления канала: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")

# Фоновые функции для парсинга

async def parse_channel_background(channel_username: str, days_back: int, max_posts: int,
                                  save_to_db: bool, session_id: int):
    """Фоновая функция для парсинга одного канала."""
    try:
        logger.info(f"Начинаем парсинг канала {channel_username}")

        # Подключаемся к Telegram
        if telegram_available and telegram_analyzer:
            try:
                await telegram_analyzer.connect()

                # Получаем посты и информацию о канале
                posts, channel_info = await telegram_analyzer.get_channel_posts(
                    channel_username=channel_username,
                    days_back=days_back,
                    max_posts=max_posts
                )
            except Exception as e:
                logger.warning(f"Ошибка при парсинге Telegram: {e}. Используем заглушку.")
                posts = []
                channel_info = {}
        else:
            # Telegram недоступен, используем заглушку
            posts = []
            channel_info = {}

        logger.info(f"Найдено {len(posts)} постов в канале {channel_username}")

        # Сохраняем посты в базу данных
        if save_to_db and posts:
            supabase_manager.save_posts_batch(posts, channel_username, channel_info)

        # Обновляем сессию парсинга
        supabase_manager.update_parsing_session(session_id, {
            'status': 'completed',
            'posts_found': len(posts),
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Парсинг канала {channel_username} завершен")

    except Exception as e:
        logger.error(f"Ошибка парсинга канала {channel_username}: {e}")

        # Обновляем статус сессии как failed
        supabase_manager.update_parsing_session(session_id, {
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now().isoformat()
        })

async def parse_channels_bulk_background(channels: List[str], days_back: int, max_posts: int,
                                        save_to_db: bool, session_id: int):
    """Фоновая функция для массового парсинга каналов."""
    try:
        logger.info(f"Начинаем массовый парсинг {len(channels)} каналов")

        total_posts = 0

        for channel_username in channels:
            try:
                logger.info(f"Парсинг канала {channel_username}")

                posts = []
                channel_info = {}

                if telegram_available and telegram_analyzer:
                    try:
                        await telegram_analyzer.connect()

                        posts, channel_info = await telegram_analyzer.get_channel_posts(
                            channel_username=channel_username,
                            days_back=days_back,
                            max_posts=max_posts
                        )
                    except Exception as e:
                        logger.warning(f"Ошибка при парсинге {channel_username}: {e}. Используем заглушку.")
                        posts = []
                        channel_info = {}
                else:
                    # Telegram недоступен, используем заглушку
                    posts = []
                    channel_info = {}

                if save_to_db and posts:
                    supabase_manager.save_posts_batch(posts, channel_username, channel_info)

                total_posts += len(posts)
                logger.info(f"Канал {channel_username}: найдено {len(posts)} постов")

            except Exception as e:
                logger.error(f"Ошибка парсинга канала {channel_username}: {e}")

        # Обновляем сессию
        supabase_manager.update_parsing_session(session_id, {
            'status': 'completed',
            'posts_found': total_posts,
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Массовый парсинг завершен: {total_posts} постов из {len(channels)} каналов")

    except Exception as e:
        logger.error(f"Ошибка массового парсинга: {e}")

        supabase_manager.update_parsing_session(session_id, {
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now().isoformat()
        })

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений."""
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск ReAIboot API...")
    print("📱 Документация: http://localhost:8000/docs")
    print("🔄 ReDoc: http://localhost:8000/redoc")

    uvicorn.run(
        "src.api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
