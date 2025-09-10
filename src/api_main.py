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

# Настройка логирования
logger = logging.getLogger(__name__)

# Импорты из нашего проекта
from .app.llm.orchestrator import LLMOrchestrator
from .app.prompts import prompt_manager
from .app.settings import settings
from .app.telegram_client import TelegramAnalyzer
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
            await auth_client.sign_in(phone_code_hash=phone_code_hash, code=code)

            # Проверяем авторизацию
            if await auth_client.is_user_authorized():
                logger.info("Успешная авторизация!")
                telegram_available = True
                telegram_authorization_needed = False

                # Сохраняем авторизованного клиента для будущих запросов
                global telegram_analyzer
                if telegram_analyzer:
                    await telegram_analyzer.disconnect()

                # Отключаем auth_client и ждем завершения
                if auth_client:
                    await auth_client.disconnect()
                    await asyncio.sleep(2)  # Ждем освобождения сессионного файла

                # Создаем новый TelegramAnalyzer с авторизованной сессией
                telegram_analyzer = TelegramAnalyzer()
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

@app.post("/api/llm/analyze-quick", tags=["llm"])
async def quick_analyze_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Быстрый анализ одного поста (ТОЛЬКО фильтрация, оценка 1-10).
    Возвращает только результат фильтрации без анализа и выбора рубрик.

    - **post_data**: Данные поста для анализа
    """
    try:
        logger.info(f"Начинаем быстрый анализ поста {post_data.get('message_id', 'unknown')}")
        logger.info(f"Ключи входных данных: {list(post_data.keys())}")
        logger.info(f"Поле date: {post_data.get('date', 'MISSING')}")

        # Убеждаемся, что поле date присутствует
        if 'date' not in post_data and 'raw_data' in post_data:
            raw_data = post_data.get('raw_data', {})
            if isinstance(raw_data, str):
                import json
                try:
                    raw_data = json.loads(raw_data)
                except:
                    pass
            if 'date' in raw_data:
                post_data['date'] = raw_data['date']
                logger.info(f"Восстановили date из raw_data: {post_data['date']}")

        # Быстрый анализ: только фильтрация (оценка 1-10)
        result = await orchestrator.process_post_enhanced(
            post_data=post_data,
            skip_analysis=True,  # Пропускаем анализ
            skip_rubric_selection=True  # Пропускаем выбор рубрик
        )

        # Сохраняем результаты в базу данных
        if result.overall_success and supabase_manager:
            logger.info(f"Сохраняем результат анализа для поста {result.post_id}, успех: {result.overall_success}")
            await orchestrator._save_results_to_database([result], [post_data])
            logger.info(f"Результат анализа сохранен для поста {result.post_id}")

        return {
            "success": result.overall_success,
            "post_id": result.post_id,
            "stages": [
                {
                    "stage": stage.stage_name,
                    "success": stage.success,
                    "data": stage.data,
                    "error": stage.error,
                    "tokens_used": stage.tokens_used,
                    "processing_time": stage.processing_time
                }
                for stage in result.stages
            ],
            "total_tokens": result.total_tokens,
            "total_time": result.total_time,
            "error": result.error
        }

    except Exception as e:
        logger.error(f"Ошибка при быстром анализе: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.post("/api/llm/generate-scenarios", tags=["llm"])
async def generate_scenarios_from_analysis(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация сценариев на основе уже проведенного анализа.

    - **post_data**: Данные поста
    - **selected_combinations**: Выбранные комбинации рубрик/форматов
    """
    try:
        post_data = request.get("post_data", {})
        selected_combinations = request.get("selected_combinations", [])

        if not post_data:
            raise HTTPException(status_code=400, detail="Не переданы данные поста")

        if not selected_combinations:
            raise HTTPException(status_code=400, detail="Не выбраны комбинации рубрик/форматов")

        logger.info(f"Генерация сценариев для поста {post_data.get('message_id', 'unknown')}")

        scenarios = []

        # Генерируем сценарии для выбранных комбинаций
        for i, combination in enumerate(selected_combinations):
            logger.info(f"Генерация сценария {i+1}/{len(selected_combinations)}")

            generator_input = {
                **post_data,
                "rubric": combination.get("rubric", {}),
                "reel_format": combination.get("format", {}),
                "analysis": post_data.get("analysis", {})
            }

            scenario_result = await orchestrator.generator_processor.process(generator_input)

            if scenario_result.success:
                scenarios.append({
                    **scenario_result.data,
                    "rubric": combination.get("rubric", {}),
                    "format": combination.get("format", {}),
                    "combination_id": combination.get("id", f"combination_{i}"),
                    "selection_score": combination.get("score", 0)
                })

        # Сохраняем сценарии через оркестратор
        if scenarios and supabase_manager:
            logger.info(f"Сохраняем {len(scenarios)} сценариев для поста {post_data.get('message_id', 'unknown')}")

            # Создаем фиктивный результат для сохранения сценариев
            from app.llm.orchestrator import OrchestratorResult, ProcessingStage

            fake_result = OrchestratorResult(
                post_id=f"{post_data['message_id']}_{post_data['channel_username']}",
                overall_success=True,
                stages=[],
                final_data={"scenarios": scenarios}
            )

            await orchestrator._save_results_to_database([fake_result], [post_data])
            logger.info(f"Сценарии сохранены в БД для поста {post_data.get('message_id', 'unknown')}")

        return {
            "success": len(scenarios) > 0,
            "scenarios_generated": len(scenarios),
            "scenarios": scenarios
        }

    except Exception as e:
        logger.error(f"Ошибка при генерации сценариев: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.post("/api/llm/process-enhanced", tags=["llm"])
async def process_post_enhanced(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Полная 4-этапная обработка поста через новый enhanced флоу.

    - **posts**: Список постов для обработки
    - **skip_filter**: Пропустить фильтрацию (default: false)
    - **skip_analysis**: Пропустить анализ (default: false)
    - **skip_rubric_selection**: Пропустить выбор рубрик (default: false)
    """
    try:
        # Преобразуем Pydantic модели в словари
        posts_data = [post.model_dump() for post in request.posts]

        # Параметры для обработки
        skip_filter = request.model_dump().get("skip_filter", False)
        skip_analysis = request.model_dump().get("skip_analysis", False)
        skip_rubric_selection = request.model_dump().get("skip_rubric_selection", False)

        # Запускаем обработку в фоне
        background_tasks.add_task(
            process_posts_enhanced_background,
            posts_data,
            skip_filter,
            skip_analysis,
            skip_rubric_selection
        )

        return {
            "message": "4-этапная обработка запущена в фоне",
            "posts_count": len(posts_data),
            "stages": ["filter", "analysis", "rubric_selection", "generation"]
        }

    except Exception as e:
        logger.error(f"Ошибка при запуске enhanced обработки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


async def process_posts_enhanced_background(
    posts_data: List[Dict],
    skip_filter: bool = False,
    skip_analysis: bool = False,
    skip_rubric_selection: bool = False
):
    """Фоновая 4-этапная обработка постов."""
    try:
        logger.info(f"Начинаем enhanced обработку {len(posts_data)} постов")

        results = []
        for post_data in posts_data:
            result = await orchestrator.process_post_enhanced(
                post_data=post_data,
                skip_filter=skip_filter,
                skip_analysis=skip_analysis,
                skip_rubric_selection=skip_rubric_selection
            )
            results.append(result)

        logger.info(f"Enhanced обработка завершена: {len(results)} результатов")

        # Сохраняем результаты в базу данных
        if supabase_manager and results:
            await orchestrator._save_results_to_database(results, posts_data)

    except Exception as e:
        logger.error(f"Ошибка в enhanced фоновой обработке: {e}")


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

# === ЭНДПОИНТЫ БАЗЫ ДАННЫХ (должны быть ПЕРЕД файловыми) ===

@app.get("/api/prompts/db", tags=["prompts"])
async def get_all_prompts_db():
    """Получить все промпты из базы данных."""
    try:
        result = supabase_manager.client.table('llm_prompts').select('*').order('created_at', desc=True).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка получения промптов: {result.error}")

        return {"prompts": result.data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения промптов: {str(e)}")

@app.get("/api/prompts/db/{prompt_id}", tags=["prompts"])
async def get_prompt_db(prompt_id: int):
    """Получить конкретный промпт из базы данных."""
    try:
        result = supabase_manager.client.table('llm_prompts').select('*').eq('id', prompt_id).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка получения промпта: {result.error}")

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Промпт с ID {prompt_id} не найден")

        return {"prompt": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения промпта: {str(e)}")

@app.post("/api/prompts/test/{prompt_id}", tags=["prompts"])
async def test_prompt_db(prompt_id: int, variables: Dict[str, Any]):
    """Протестировать промпт с переменными."""
    try:
        from openai import AsyncOpenAI
        import time

        # Получаем промпт из базы данных
        result = supabase_manager.client.table('llm_prompts').select('*').eq('id', prompt_id).execute()

        if (hasattr(result, 'error') and result.error) or not result.data:
            raise HTTPException(status_code=404, detail=f"Промпт с ID {prompt_id} не найден")

        prompt = result.data[0]
        system_prompt = prompt.get('system_prompt', prompt.get('content', ''))
        user_prompt = prompt.get('user_prompt', '')

        # Подставляем переменные в промпты
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))

        # Проверяем доступность API ключей
        api_key = None
        if prompt['model'].startswith('gpt'):
            api_key = settings.openai_api_key
        elif prompt['model'].startswith('claude'):
            api_key = settings.anthropic_api_key

        if not api_key:
            # Возвращаем только обработанный промпт без вызова LLM
            return {
                "prompt_id": prompt_id,
                "processed_system_prompt": system_prompt,
                "processed_user_prompt": user_prompt,
                "variables_used": variables,
                "model": prompt['model'],
                "temperature": prompt['temperature'],
                "max_tokens": prompt['max_tokens'],
                "llm_response": None,
                "error": "API ключ не найден для данной модели"
            }

        start_time = time.time()

        try:
            # Вызываем соответствующий API
            if prompt['model'].startswith('gpt'):
                client = AsyncOpenAI(api_key=api_key)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                if user_prompt:
                    messages.append({"role": "user", "content": user_prompt})
                elif not system_prompt:
                    # Fallback если нет ни system ни user
                    messages.append({"role": "user", "content": "Пожалуйста, выполните задачу."})

                response = await client.chat.completions.create(
                    model=prompt['model'],
                    messages=messages,
                    temperature=prompt['temperature'],
                    max_tokens=prompt['max_tokens']
                )
                llm_response = response.choices[0].message.content

            elif prompt['model'].startswith('claude'):
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=api_key)
                messages = []
                if user_prompt:
                    messages.append({"role": "user", "content": user_prompt})
                elif system_prompt:
                    # Для Claude system prompt передается отдельно
                    pass
                else:
                    messages.append({"role": "user", "content": "Пожалуйста, выполните задачу."})

                response = await client.messages.create(
                    model=prompt['model'],
                    max_tokens=prompt['max_tokens'],
                    temperature=prompt['temperature'],
                    system=system_prompt if system_prompt else None,
                    messages=messages
                )
                llm_response = response.content[0].text

            processing_time = time.time() - start_time

            # Получаем количество токенов
            tokens_used = 0
            if prompt['model'].startswith('gpt') and hasattr(response, 'usage'):
                tokens_used = getattr(response.usage, 'total_tokens', 0)
            elif prompt['model'].startswith('claude') and hasattr(response, 'usage'):
                tokens_used = getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)

            return {
                "prompt_id": prompt_id,
                "processed_system_prompt": system_prompt,
                "processed_user_prompt": user_prompt,
                "variables_used": variables,
                "model": prompt['model'],
                "temperature": prompt['temperature'],
                "max_tokens": prompt['max_tokens'],
                "llm_response": llm_response,
                "processing_time": round(processing_time, 2),
                "tokens_used": tokens_used
            }

        except Exception as api_error:
            return {
                "prompt_id": prompt_id,
                "processed_system_prompt": system_prompt,
                "processed_user_prompt": user_prompt,
                "variables_used": variables,
                "model": prompt['model'],
                "temperature": prompt['temperature'],
                "max_tokens": prompt['max_tokens'],
                "llm_response": None,
                "error": f"Ошибка API: {str(api_error)}"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестирования промпта: {str(e)}")

@app.put("/api/prompts/db/{prompt_id}", tags=["prompts"])
async def update_prompt_db(prompt_id: int, prompt_data: Dict[str, Any]):
    """Обновить промпт в базе данных."""
    try:
        from datetime import datetime

        update_data = {
            'updated_at': datetime.now().isoformat()
        }

        # Добавляем только переданные поля
        for field in ['name', 'description', 'prompt_type', 'content', 'model', 'temperature', 'max_tokens', 'is_active']:
            if field in prompt_data:
                update_data[field] = prompt_data[field]

        result = supabase_manager.client.table('llm_prompts').update(update_data).eq('id', prompt_id).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка обновления промпта: {result.error}")

        return {"message": "Промпт обновлен успешно"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления промпта: {str(e)}")

@app.delete("/api/prompts/db/{prompt_id}", tags=["prompts"])
async def delete_prompt_db(prompt_id: int):
    """Удалить промпт из базы данных."""
    try:
        result = supabase_manager.client.table('llm_prompts').delete().eq('id', prompt_id).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка удаления промпта: {result.error}")

        return {"message": "Промпт удален успешно"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления промпта: {str(e)}")

# === ЭНДПОИНТЫ ФАЙЛОВОЙ СИСТЕМЫ ===

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

# === ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ ДЛЯ ПРОМПТОВ ===

@app.post("/api/prompts", tags=["prompts"])
async def create_prompt(prompt_data: Dict[str, Any]):
    """Создать новый промпт."""
    try:
        from src.app.settings import settings
        from datetime import datetime

        # Получаем текущего пользователя
        user = supabase.auth.get_user()
        user_id = user.user.id if user.user else None

        # Создаем промпт в базе данных с новой структурой
        prompt_record = {
            'name': prompt_data['name'],
            'description': prompt_data.get('description', ''),
            'prompt_type': prompt_data.get('prompt_type', 'custom'),
            'category': prompt_data.get('category', 'general'),
            'content': prompt_data['content'],
            'variables': prompt_data.get('variables', {}),
            'model': prompt_data.get('model', 'gpt-4o-mini'),  # Старые поля для совместимости
            'temperature': prompt_data.get('temperature', 0.7),
            'max_tokens': prompt_data.get('max_tokens', 2000),
            'model_settings': prompt_data.get('model_settings', {
                'model': prompt_data.get('model', 'gpt-4o-mini'),
                'temperature': prompt_data.get('temperature', 0.7),
                'max_tokens': prompt_data.get('max_tokens', 2000)
            }),
            'is_active': prompt_data.get('is_active', True),
            'is_system': prompt_data.get('is_system', False),
            'version': prompt_data.get('version', 1),
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        result = supabase_manager.client.table('llm_prompts').insert([prompt_record]).execute()

        if result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка создания промпта: {result.error}")

        return {"message": "Промпт создан успешно", "id": result.data[0]['id']}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания промпта: {str(e)}")

@app.put("/api/prompts/db/{prompt_id}", tags=["prompts"])
async def update_prompt_db(prompt_id: int, prompt_data: Dict[str, Any]):
    """Обновить промпт в базе данных."""
    try:
        from datetime import datetime

        update_data = {
            'updated_at': datetime.now().isoformat()
        }

        # Добавляем только переданные поля
        for field in ['name', 'description', 'prompt_type', 'category', 'content', 'variables', 'model_settings', 'is_active', 'version']:
            if field in prompt_data:
                update_data[field] = prompt_data[field]

        # Обновляем старые поля для совместимости
        if 'model' in prompt_data:
            update_data['model'] = prompt_data['model']
        if 'temperature' in prompt_data:
            update_data['temperature'] = prompt_data['temperature']
        if 'max_tokens' in prompt_data:
            update_data['max_tokens'] = prompt_data['max_tokens']

        # Синхронизируем model_settings со старыми полями
        if any(field in prompt_data for field in ['model', 'temperature', 'max_tokens']) and 'model_settings' not in prompt_data:
            # Получаем текущие model_settings
            current_result = supabase_manager.client.table('llm_prompts').select('model_settings').eq('id', prompt_id).execute()
            if current_result.data:
                current_settings = current_result.data[0]['model_settings'] or {}

                # Обновляем только переданные поля
                if 'model' in prompt_data:
                    current_settings['model'] = prompt_data['model']
                if 'temperature' in prompt_data:
                    current_settings['temperature'] = prompt_data['temperature']
                if 'max_tokens' in prompt_data:
                    current_settings['max_tokens'] = prompt_data['max_tokens']

                update_data['model_settings'] = current_settings

        result = supabase_manager.client.table('llm_prompts').update(update_data).eq('id', prompt_id).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка обновления промпта: {result.error}")

        return {"message": "Промпт обновлен успешно"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления промпта: {str(e)}")

@app.delete("/api/prompts/db/{prompt_id}", tags=["prompts"])
async def delete_prompt_db(prompt_id: int):
    """Удалить промпт из базы данных."""
    try:
        result = supabase_manager.client.table('llm_prompts').delete().eq('id', prompt_id).execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка удаления промпта: {result.error}")

        return {"message": "Промпт удален успешно"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления промпта: {str(e)}")

# Эндпоинты базы данных перемещены выше

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
        # Получаем все каналы
        channels = supabase_manager.client.table('channels').select('*').execute()
        baselines = []

        for channel in channels.data:
            baseline = supabase_manager.get_channel_baseline(channel['username'])
            if baseline:
                # Канал с рассчитанными метриками
                baselines.append({
                    'channel': channel,
                    'baseline': baseline
                })
            else:
                # Канал без метрик - подсчитываем реальное количество постов
                try:
                    from .app.supabase_client import supabase_client
                    posts_count = supabase_manager.client.table('posts').select('id', count='exact').eq('channel_username', channel['username']).execute()
                    actual_posts_count = posts_count.count if hasattr(posts_count, 'count') else 0
                except Exception as e:
                    logger.warning(f"Не удалось подсчитать посты для канала {channel['username']}: {e}")
                    actual_posts_count = 0

                baselines.append({
                    'channel': channel,
                    'baseline': {
                        'channel_username': channel['username'],
                        'baseline_status': 'not_calculated',
                        'posts_analyzed': actual_posts_count,  # Реальное количество постов
                        'median_engagement_rate': 0,
                        'std_engagement_rate': 0,
                        'avg_engagement_rate': 0,
                        'p75_engagement_rate': 0,
                        'p95_engagement_rate': 0,
                        'max_engagement_rate': 0,
                        'calculation_period_days': 30,
                        'min_posts_for_baseline': 10,
                        'last_calculated': None,
                        'next_calculation': None
                    }
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

@app.post("/api/channels/baselines/recalculate-all", tags=["channels"])
async def recalculate_all_baselines():
    """Принудительно пересчитать базовые метрики для ВСЕХ каналов."""
    try:
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        import json

        analyzer = ChannelBaselineAnalyzer(supabase_manager)

        # Получаем все уникальные каналы из постов
        channels_result = supabase_manager.client.table('posts').select('channel_username').execute()
        unique_channels = list(set(post['channel_username'] for post in channels_result.data))

        logger.info(f"🔄 Начинаем принудительный пересчет для {len(unique_channels)} каналов")

        recalculated_count = 0
        failed_count = 0
        results = []

        for channel_username in unique_channels:
            try:
                logger.info(f"📊 Пересчитываем базовые метрики для {channel_username}")

                # Принудительно пересчитываем
                baseline = analyzer.calculate_channel_baseline(channel_username)
                if baseline:
                    analyzer.save_channel_baseline(baseline)
                    recalculated_count += 1
                    results.append({
                        "channel": channel_username,
                        "status": "success",
                        "posts_analyzed": baseline.posts_analyzed,
                        "median_engagement": float(baseline.median_engagement_rate),
                        "std_engagement": float(baseline.std_engagement_rate)
                    })
                    logger.info(f"✅ Пересчитано для {channel_username}: {baseline.posts_analyzed} постов")
                else:
                    failed_count += 1
                    results.append({
                        "channel": channel_username,
                        "status": "failed",
                        "reason": "Недостаточно данных"
                    })
                    logger.warning(f"❌ Недостаточно данных для {channel_username}")

            except Exception as e:
                failed_count += 1
                results.append({
                    "channel": channel_username,
                    "status": "error",
                    "reason": str(e)
                })
                logger.error(f"❌ Ошибка для {channel_username}: {e}")

        logger.info(f"🎉 Пересчет завершен: {recalculated_count} успешно, {failed_count} неудачно")

        return {
            "success": True,
            "total_channels": len(unique_channels),
            "recalculated": recalculated_count,
            "failed": failed_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при массовом пересчете: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка пересчета: {str(e)}")

# Viral посты

@app.get("/api/posts/stats", tags=["posts"])
async def get_posts_stats(
    channel_username: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_views: Optional[int] = None,
    min_engagement: Optional[float] = None,
    search_term: Optional[str] = None
):
    """Получить общую статистику по постам без загрузки самих постов"""
    try:
        query = supabase_manager.client.table('posts').select('views, reactions, forwards', count='exact')

        if channel_username:
            query = query.eq('channel_username', channel_username)

        # Применяем дополнительные фильтры
        if date_from:
            query = query.gte('date', date_from)
        if date_to:
            query = query.lte('date', date_to)
        if min_views:
            query = query.gte('views', min_views)
        if min_engagement:
            query = query.gte('engagement_rate', min_engagement * 0.01)
        if search_term:
            query = query.or_(f"text.ilike.%{search_term}%,channel_title.ilike.%{search_term}%")

        result = query.execute()

        total_views = sum(post['views'] for post in result.data or [])
        total_reactions = sum(post['reactions'] for post in result.data or [])
        total_forwards = sum(post['forwards'] for post in result.data or [])
        total_posts = result.count or 0

        return {
            "total_posts": total_posts,
            "total_views": total_views,
            "total_reactions": total_reactions,
            "total_forwards": total_forwards
        }
    except Exception as e:
        logger.error(f"Error getting posts stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting posts stats: {str(e)}")


@app.get("/api/posts", tags=["posts"])
async def get_posts(
    limit: int = 50,
    offset: int = 0,
    channel_username: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_views: Optional[int] = None,
    min_engagement: Optional[float] = None,
    search_term: Optional[str] = None,
    only_viral: bool = False,
    min_viral_score: float = 1.0
):
    """Получить посты с метриками."""
    try:
        query = supabase_manager.client.table('posts').select('*')

        if channel_username:
            query = query.eq('channel_username', channel_username)

        # Применяем дополнительные фильтры
        if date_from:
            query = query.gte('date', date_from)
        if date_to:
            query = query.lte('date', date_to)
        if min_views:
            query = query.gte('views', min_views)
        if min_engagement:
            query = query.gte('engagement_rate', min_engagement * 0.01)  # Конвертируем проценты в десятичную дробь
        if search_term:
            # Поиск по тексту поста (full_text, text_preview) и названию канала
            query = query.or_(f"full_text.ilike.%{search_term}%,text_preview.ilike.%{search_term}%,channel_title.ilike.%{search_term}%,channel_username.ilike.%{search_term}%")

        # Фильтр виральных постов
        if only_viral:
            query = query.gte('viral_score', min_viral_score)

        # Получаем общее количество записей для определения has_more
        count_query = query
        count_result = count_query.execute()
        total_count = len(count_result.data) if count_result.data else 0

        posts_result = query.order('date', desc=True).range(offset, offset + limit - 1).execute()
        posts = posts_result.data or []

        # Определяем, есть ли еще записи
        has_more = (offset + len(posts)) < total_count

        # Получаем все post_id для batch запроса
        post_ids = [post['id'] for post in posts]

        # Batch запрос к post_analysis для всех постов
        analysis_dict = {}
        if post_ids:
            try:
                analysis_result = supabase_manager.client.table('post_analysis').select('post_id, suitability_score, is_suitable, filter_reason').in_('post_id', post_ids).execute()
                if analysis_result.data:
                    # Группируем по post_id и выбираем лучшую оценку
                    for analysis in analysis_result.data:
                        post_id = analysis['post_id']
                        score = analysis['suitability_score']

                        # Если это первая запись для поста или оценка лучше предыдущей
                        if post_id not in analysis_dict or (score is not None and (analysis_dict[post_id]['score'] is None or score > analysis_dict[post_id]['score'])):
                            analysis_dict[post_id] = {
                                'score': score,
                                'is_suitable': analysis['is_suitable'],
                                'analysis_reason': analysis['filter_reason']
                            }
            except Exception as e:
                logger.warning(f"Не удалось получить анализ постов: {e}")

        # Добавляем метрики виральности и оценки к постам
        for post in posts:
            # Метрики виральности
            if 'viral_score' not in post or post['viral_score'] is None:
                post['viral_score'] = 0
            if 'engagement_rate' not in post or post['engagement_rate'] is None:
                post['engagement_rate'] = 0
            if 'zscore' not in post or post['zscore'] is None:
                post['zscore'] = 0
            if 'median_multiplier' not in post or post['median_multiplier'] is None:
                post['median_multiplier'] = 0

            # Оценка из batch результата
            if post['id'] in analysis_dict:
                analysis = analysis_dict[post['id']]
                post['score'] = analysis['score']
                post['is_suitable'] = analysis['is_suitable']
                post['analysis_reason'] = analysis['analysis_reason']
            else:
                post['score'] = None
                post['is_suitable'] = None
                post['analysis_reason'] = None

        return {
            "posts": posts,
            "count": total_count,
            "has_more": has_more
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения постов: {str(e)}")

@app.get("/api/posts/{post_id}", tags=["posts"])
async def get_single_post(post_id: str):
    """Получить один пост с оценкой."""
    try:
        # Получаем пост
        post_result = supabase_manager.client.table('posts').select('*').eq('id', post_id).execute()

        if not post_result.data or len(post_result.data) == 0:
            raise HTTPException(status_code=404, detail="Пост не найден")

        post = post_result.data[0]

        # Добавляем метрики виральности
        if 'viral_score' not in post or post['viral_score'] is None:
            post['viral_score'] = 0
        if 'engagement_rate' not in post or post['engagement_rate'] is None:
            post['engagement_rate'] = 0
        if 'zscore' not in post or post['zscore'] is None:
            post['zscore'] = 0
        if 'median_multiplier' not in post or post['median_multiplier'] is None:
            post['median_multiplier'] = 0

        # Получаем оценку из post_analysis
        try:
            analysis_result = supabase_manager.client.table('post_analysis').select('suitability_score, is_suitable, filter_reason').eq('post_id', post_id).execute()
            if analysis_result.data and len(analysis_result.data) > 0:
                analysis = analysis_result.data[0]
                post['score'] = analysis['suitability_score']
                post['is_suitable'] = analysis['is_suitable']
                post['analysis_reason'] = analysis['filter_reason']
            else:
                post['score'] = None
                post['is_suitable'] = None
                post['analysis_reason'] = None
        except Exception:
            post['score'] = None
            post['is_suitable'] = None
            post['analysis_reason'] = None

        return post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения поста: {str(e)}")

@app.get("/api/posts/viral", tags=["posts"])
async def get_viral_posts(channel_username: Optional[str] = None,
                         min_viral_score: float = 1.5, limit: int = 100):
    """Получить 'залетевшие' посты."""
    try:
        posts = supabase_manager.get_viral_posts(channel_username, min_viral_score, limit)
        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения viral постов: {str(e)}")

@app.post("/api/debug/calculate-baseline", tags=["debug"])
async def debug_calculate_baseline(channel_username: str):
    """Отладка: рассчитать базовые метрики канала."""
    try:
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        import json

        logger.info(f"🔍 Начинаем отладку расчета базовых метрик для канала {channel_username}")

        analyzer = ChannelBaselineAnalyzer(supabase_manager)

        # Получаем посты канала
        posts_result = supabase_manager.client.table('posts').select('*').eq('channel_username', channel_username).execute()
        posts = posts_result.data or []

        logger.info(f"📊 Найдено {len(posts)} постов для канала {channel_username}")

        if not posts:
            return {"error": f"Нет постов для канала {channel_username}"}

        # Рассчитываем engagement rates
        engagement_rates = []
        posts_info = []

        for post in posts:
            rate = analyzer._calculate_post_engagement_rate(post)
            engagement_rates.append(rate)

            posts_info.append({
                "id": post.get('id'),
                "date": post.get('date'),
                "views": post.get('views', 0),
                "forwards": post.get('forwards', 0),
                "replies": post.get('replies', 0),
                "reactions": post.get('reactions', 0),
                "engagement_rate": rate
            })

        valid_rates = [r for r in engagement_rates if r is not None]
        logger.info(f"📈 Рассчитано {len(valid_rates)} engagement rates из {len(posts)} постов")

        # Проверяем минимальное количество (используем настройки с минимумом 3)
        min_from_settings = analyzer.settings['baseline_calculation'].get('min_posts_for_baseline', 5)
        min_posts = max(min_from_settings, 3)
        if len(valid_rates) < min_posts:
            return {
                "error": f"Недостаточно данных: {len(valid_rates)} < {min_posts}",
                "posts": posts_info,
                "valid_rates_count": len(valid_rates),
                "min_required": min_posts
            }

        # Удаляем выбросы
        clean_rates = analyzer._remove_outliers(valid_rates)
        logger.info(f"🧹 После удаления выбросов: {len(clean_rates)} из {len(valid_rates)}")

        if len(clean_rates) < min_posts:
            return {
                "error": f"После удаления выбросов недостаточно данных: {len(clean_rates)} < {min_posts}",
                "posts": posts_info,
                "valid_rates": valid_rates,
                "clean_rates": clean_rates,
                "min_required": min_posts
            }

        # Рассчитываем базовые метрики
        baseline = analyzer._calculate_baseline_stats(channel_username, clean_rates, len(posts))

        return {
            "success": True,
            "channel": channel_username,
            "posts_count": len(posts),
            "valid_rates_count": len(valid_rates),
            "clean_rates_count": len(clean_rates),
            "baseline": {
                "median": baseline.median_engagement_rate,
                "std": baseline.std_engagement_rate,
                "avg": baseline.avg_engagement_rate,
                "posts_analyzed": baseline.posts_analyzed
            },
            "posts_info": posts_info[:5]  # Первые 5 постов
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при отладке базовых метрик для {channel_username}: {e}")
        return {"error": str(e)}

@app.get("/api/debug/settings", tags=["debug"])
async def debug_get_settings():
    """Отладка: получить все настройки системы."""
    try:
        settings = {}
        keys = ['viral_weights', 'baseline_calculation', 'viral_thresholds']
        for key in keys:
            value = supabase_manager.get_system_setting(key)
            settings[key] = value

        return {"success": True, "settings": settings}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/debug/calculate-viral-single", tags=["debug"])
async def debug_calculate_single_post(post_id: str):
    """Отладка: рассчитать виральность одного поста."""
    try:
        from .app.viral_post_detector import ViralPostDetector
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        import json

        # Получаем данные поста
        post_result = supabase_manager.client.table('posts').select('*').eq('id', post_id).execute()
        if not post_result.data:
            raise HTTPException(status_code=404, detail=f"Пост {post_id} не найден")

        post = post_result.data[0]
        channel_username = post['channel_username']

        logger.info(f"📊 Пост найден: {post_id} из канала {channel_username}")
        logger.info(f"📈 Статистика поста: views={post.get('views', 0)}, forwards={post.get('forwards', 0)}, replies={post.get('replies', 0)}, reactions={post.get('reactions', 0)}")
        logger.info(f"📝 Post data: {post}")

        # Получаем базовые метрики канала
        baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
        baseline = baseline_analyzer.get_channel_baseline(channel_username)

        if not baseline:
            logger.warning(f"⚠️  Нет базовых метрик для канала {channel_username}")
            # Попробуем рассчитать
            baseline = baseline_analyzer.calculate_channel_baseline(channel_username)
            if baseline:
                baseline_analyzer.save_channel_baseline(baseline)
                logger.info(f"✅ Базовые метрики рассчитаны для канала {channel_username}")
            else:
                raise HTTPException(status_code=404, detail=f"Не удалось рассчитать базовые метрики для канала {channel_username}")

        logger.info(f"📊 Базовые метрики канала: median={baseline.median_engagement_rate}, std={baseline.std_engagement_rate}")

        # ДОБАВЛЯЕМ ОТЛАДКУ: проверяем supabase_manager
        logger.info(f"🔧 supabase_manager: {supabase_manager}")
        logger.info(f"🔧 supabase_manager.client: {supabase_manager.client}")

        # ДОБАВЛЯЕМ ОТЛАДКУ: проверяем настройки
        logger.info(f"🔧 Настройки baseline_analyzer: {baseline_analyzer.settings}")
        viral_weights = baseline_analyzer.settings.get('viral_weights')
        logger.info(f"🔧 Viral weights: {viral_weights} (тип: {type(viral_weights)})")

        # Проверяем парсинг
        if isinstance(viral_weights, str):
            try:
                import json
                parsed_weights = json.loads(viral_weights)
                logger.info(f"🔧 Parsed viral weights: {parsed_weights}")
                # Проверяем расчет
                test_calc = baseline_analyzer._calculate_post_engagement_rate(post)
                logger.info(f"🔧 Test calculation result: {test_calc}")
            except Exception as e:
                logger.error(f"🔧 Parse error: {e}")
        else:
            logger.info(f"🔧 Viral weights already parsed: {viral_weights}")
            # Проверяем расчет
            test_calc = baseline_analyzer._calculate_post_engagement_rate(post)
            logger.info(f"🔧 Test calculation result: {test_calc}")

        # Рассчитываем виральность
        detector = ViralPostDetector(baseline_analyzer)
        viral_results = detector.detect_viral_posts([post], channel_username)

        if viral_results:
            result = viral_results[0]
            logger.info(f"🎯 Результат расчета: viral_score={result.viral_score}, engagement_rate={result.engagement_rate}, zscore={result.zscore}, is_viral={result.is_viral}")

            # Сохраняем результат
            success = detector.update_post_viral_metrics(post_id, result)
            logger.info(f"💾 Сохранение метрик: {'✅' if success else '❌'}")

            return {
                "success": True,
                "post_id": post_id,
                "channel": channel_username,
                "baseline": {
                    "median": baseline.median_engagement_rate,
                    "std": baseline.std_engagement_rate,
                    "posts_analyzed": baseline.posts_analyzed
                },
                "metrics": {
                    "viral_score": result.viral_score,
                    "engagement_rate": result.engagement_rate,
                    "zscore": result.zscore,
                    "median_multiplier": result.median_multiplier,
                    "is_viral": result.is_viral
                },
                "post_stats": {
                    "views": post.get('views', 0),
                    "forwards": post.get('forwards', 0),
                    "replies": post.get('replies', 0),
                    "reactions": post.get('reactions', 0)
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Не удалось рассчитать виральность")

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете виральности поста {post_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@app.post("/api/posts/calculate-viral-batch", tags=["posts"])
async def calculate_viral_batch(channel_username: str = None, limit: int = 100):
    """Массовый расчет виральности постов."""
    try:
        from .app.viral_post_detector import ViralPostDetector
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        import json

        logger.info(f"🚀 Начинаем массовый расчет виральности. Канал: {channel_username}, Лимит: {limit}")

        # Получаем посты
        query = supabase_manager.client.table('posts').select('*').order('date', desc=True).limit(limit)
        if channel_username:
            query = query.eq('channel_username', channel_username)

        posts_result = query.execute()
        posts = posts_result.data or []

        if not posts:
            return {"success": False, "message": "Нет постов для обработки"}

        logger.info(f"📋 Найдено {len(posts)} постов для обработки")

        # Группируем по каналам
        channels_posts = {}
        for post in posts:
            channel = post['channel_username']
            if channel not in channels_posts:
                channels_posts[channel] = []
            channels_posts[channel].append(post)

        total_processed = 0
        channels_stats = []

        # Обрабатываем каждый канал
        for channel, channel_posts in channels_posts.items():
            logger.info(f"🔄 Обрабатываем канал {channel}: {len(channel_posts)} постов")

            # Проверяем базовые метрики канала
            baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
            baseline = baseline_analyzer.get_channel_baseline(channel)

            if not baseline:
                logger.info(f"📊 Рассчитываем базовые метрики для канала {channel}")
                baseline = baseline_analyzer.calculate_channel_baseline(channel)
                if baseline:
                    baseline_analyzer.save_channel_baseline(baseline)
                    logger.info(f"✅ Базовые метрики сохранены для канала {channel}")
                else:
                    logger.warning(f"⚠️  Не удалось рассчитать базовые метрики для канала {channel}")
                    continue

            # Рассчитываем виральность постов канала
            detector = ViralPostDetector(baseline_analyzer)
            viral_results = detector.detect_viral_posts(channel_posts, channel)

            # Сохраняем результаты
            processed_count = 0
            viral_count = 0

            for post, result in zip(channel_posts, viral_results):
                post_id = post.get('id')
                if post_id:
                    success = detector.update_post_viral_metrics(str(post_id), result)
                    if success:
                        processed_count += 1
                        if result.is_viral:
                            viral_count += 1

            logger.info(f"📊 Канал {channel}: обработано {processed_count}/{len(channel_posts)} постов, найдено {viral_count} виральных")

            channels_stats.append({
                "channel": channel,
                "total_posts": len(channel_posts),
                "processed_posts": processed_count,
                "viral_posts": viral_count,
                "baseline_status": "ready" if baseline else "failed"
            })

            total_processed += processed_count

        logger.info(f"🎉 Массовый расчет завершен: обработано {total_processed} постов из {len(posts)}")

        return {
            "success": True,
            "total_posts": len(posts),
            "processed_posts": total_processed,
            "channels": channels_stats
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при массовом расчете виральности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@app.post("/api/posts/calculate-viral-all", tags=["posts"])
async def calculate_viral_all_posts(channel_username: str = None):
    """Массовый расчет виральности для ВСЕХ постов."""
    try:
        from .app.viral_post_detector import ViralPostDetector
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer
        import json

        logger.info(f"🚀 Начинаем массовый расчет виральности для ВСЕХ постов. Канал: {channel_username}")

        # Получаем все посты (без лимита)
        query = supabase_manager.client.table('posts').select('*', count='exact').order('date', desc=True)
        if channel_username:
            query = query.eq('channel_username', channel_username)

        posts_result = query.execute()
        posts = posts_result.data or []
        total_posts = posts_result.count

        if not posts:
            return {"success": False, "message": "Нет постов для обработки"}

        logger.info(f"📋 Найдено {len(posts)} постов из {total_posts} для обработки")

        # Группируем по каналам
        channels_posts = {}
        for post in posts:
            channel = post['channel_username']
            if channel not in channels_posts:
                channels_posts[channel] = []
            channels_posts[channel].append(post)

        total_processed = 0
        channels_stats = []

        # Обрабатываем каждый канал
        for channel, channel_posts in channels_posts.items():
            logger.info(f"🔄 Обрабатываем канал {channel}: {len(channel_posts)} постов")

            # Проверяем базовые метрики канала
            baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
            baseline = baseline_analyzer.get_channel_baseline(channel)

            if not baseline:
                logger.info(f"📊 Рассчитываем базовые метрики для канала {channel}")
                baseline = baseline_analyzer.calculate_channel_baseline(channel)
                if baseline:
                    baseline_analyzer.save_channel_baseline(baseline)
                    logger.info(f"✅ Базовые метрики сохранены для канала {channel}")
                else:
                    logger.warning(f"⚠️  Не удалось рассчитать базовые метрики для канала {channel}")
                    continue

            # Рассчитываем виральность постов канала
            detector = ViralPostDetector(baseline_analyzer)
            viral_results = detector.detect_viral_posts(channel_posts, channel)

            # Сохраняем результаты
            processed_count = 0
            viral_count = 0

            for post, result in zip(channel_posts, viral_results):
                post_id = post.get('id')
                if post_id:
                    success = detector.update_post_viral_metrics(str(post_id), result)
                    if success:
                        processed_count += 1
                        if result.is_viral:
                            viral_count += 1

            logger.info(f"📊 Канал {channel}: обработано {processed_count}/{len(channel_posts)} постов, найдено {viral_count} виральных")

            channels_stats.append({
                "channel": channel,
                "total_posts": len(channel_posts),
                "processed_posts": processed_count,
                "viral_posts": viral_count,
                "baseline_status": "ready" if baseline else "failed"
            })

            total_processed += processed_count

        logger.info(f"🎉 Массовый расчет всех постов завершен: обработано {total_processed} постов из {len(posts)}")

        return {
            "success": True,
            "total_posts": len(posts),
            "processed_posts": total_processed,
            "channels": channels_stats,
            "message": f"Обработано {total_processed} постов из {len(posts)}"
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при массовом расчете всех постов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

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

# ===== ДОПОЛНИТЕЛЬНЫЕ API ЭНДПОИНТЫ ДЛЯ VIRAL DETECTION =====

@app.post("/api/posts/calculate-viral-batch", tags=["posts"])
async def calculate_viral_metrics_batch(channel_username: str = None, limit: int = 100):
    """Пересчитать viral метрики для группы постов."""
    try:
        from .app.viral_post_detector import ViralPostDetector
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

        # Получаем посты
        query = supabase_manager.client.table('posts').select('*')
        if channel_username:
            query = query.eq('channel_username', channel_username)
        query = query.is_('viral_score', None).limit(limit)  # Только посты без метрик

        posts_result = query.execute()
        posts = posts_result.data

        if not posts:
            return {"message": "Нет постов для расчета метрик", "processed": 0}

        # Группируем по каналам
        channels_processed = {}
        total_processed = 0

        for post in posts:
            channel_username = post['channel_username']
            if channel_username not in channels_processed:
                # Получаем базовые метрики канала
                baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
                baseline = baseline_analyzer.get_channel_baseline(channel_username)

                if not baseline:
                    # Пытаемся рассчитать базовые метрики
                    baseline = baseline_analyzer.calculate_channel_baseline(channel_username)
                    if baseline:
                        baseline_analyzer.save_channel_baseline(baseline)

                channels_processed[channel_username] = baseline

            baseline = channels_processed[channel_username]
            if not baseline:
                continue

            # Рассчитываем метрики виральности
            detector = ViralPostDetector(baseline_analyzer)
            result = detector.analyze_post_virality(post, baseline)

            # Обновляем метрики
            success = detector.update_post_viral_metrics(post['id'], result)
            if success:
                total_processed += 1

        return {
            "message": f"Обработано {total_processed} постов",
            "processed": total_processed,
            "channels": list(channels_processed.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета метрик: {str(e)}")

@app.post("/api/channels/{channel_username}/ensure-baseline", tags=["channels"])
async def ensure_channel_baseline(channel_username: str, force_recalculate: bool = False):
    """Убедиться, что базовые метрики канала существуют и актуальны."""
    try:
        from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

        analyzer = ChannelBaselineAnalyzer(supabase_manager)

        # Проверяем существующие метрики
        existing_baseline = analyzer.get_channel_baseline(channel_username)

        if existing_baseline and not force_recalculate:
            # Проверяем актуальность
            if existing_baseline.baseline_status == 'ready':
                return {
                    "message": "Базовые метрики актуальны",
                    "baseline": existing_baseline.to_dict(),
                    "status": "exists"
                }

        # Рассчитываем новые метрики
        baseline = analyzer.calculate_channel_baseline(channel_username)

        if not baseline:
            # Если недостаточно данных, получаем больше постов
            posts = analyzer._get_channel_posts_history(channel_username)
            if len(posts) < 5:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно данных для канала {channel_username}. Найдено всего {len(posts)} постов"
                )

            # Пытаемся с меньшим порогом
            baseline = analyzer.calculate_channel_baseline(channel_username)

        if baseline:
            success = analyzer.save_channel_baseline(baseline)
            if success:
                return {
                    "message": "Базовые метрики рассчитаны и сохранены",
                    "baseline": baseline.to_dict(),
                    "status": "created"
                }
            else:
                raise HTTPException(status_code=500, detail="Не удалось сохранить базовые метрики")
        else:
            raise HTTPException(status_code=400, detail="Не удалось рассчитать базовые метрики")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при работе с базовыми метриками: {str(e)}")

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

            # Автоматический расчет метрик виральности
            try:
                viral_calc_settings = supabase_manager.get_system_setting('viral_calculation') or {
                    'auto_calculate_viral': True,
                    'batch_size': 100
                }

                if viral_calc_settings.get('auto_calculate_viral', True):
                    logger.info(f"Автоматический расчет метрик виральности для {len(posts)} постов канала {channel_username}")

                    # Импортируем необходимые классы
                    from .app.viral_post_detector import ViralPostDetector
                    from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

                    # Проверяем/создаем базовые метрики канала
                    baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
                    baseline = baseline_analyzer.get_channel_baseline(channel_username)

                    if not baseline:
                        logger.info(f"Базовые метрики для канала {channel_username} не найдены, рассчитываем...")
                        baseline = baseline_analyzer.calculate_channel_baseline(channel_username)
                        if baseline:
                            baseline_analyzer.save_channel_baseline(baseline)
                            logger.info(f"Базовые метрики для канала {channel_username} рассчитаны")
                        else:
                            logger.warning(f"Не удалось рассчитать базовые метрики для канала {channel_username}")

                    if baseline:
                        # Рассчитываем метрики виральности
                        detector = ViralPostDetector(baseline_analyzer)
                        viral_results = detector.detect_viral_posts(posts, channel_username)

                        processed_count = 0
                        for post, result in zip(posts, viral_results):
                            # Проверяем наличие ID поста
                            post_id = post.get('id')
                            if post_id:
                                if detector.update_post_viral_metrics(str(post_id), result):
                                    processed_count += 1
                            else:
                                logger.warning(f"Пост без ID пропущен: {post.get('message_id', 'unknown')} в канале {channel_username}")

                        logger.info(f"Рассчитаны метрики виральности для {processed_count}/{len(posts)} постов канала {channel_username}")

                        viral_count = sum(1 for r in viral_results if r.is_viral)
                        if viral_count > 0:
                            logger.info(f"Найдено {viral_count} 'залетевших' постов в канале {channel_username}")

            except Exception as e:
                logger.error(f"Ошибка при автоматическом расчете метрик для канала {channel_username}: {e}")

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

        # Подключаемся к Telegram один раз в начале
        telegram_connected = False
        if telegram_available and telegram_analyzer:
            try:
                await telegram_analyzer.connect()
                telegram_connected = True
                logger.info("Успешно подключено к Telegram для массового парсинга")
            except Exception as e:
                logger.warning(f"Не удалось подключиться к Telegram: {e}")

        for channel_username in channels:
            try:
                logger.info(f"Парсинг канала {channel_username}")

                posts = []
                channel_info = {}

                if telegram_connected:
                    try:
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

                    # Обновляем время последнего парсинга канала
                    supabase_manager.update_channel_last_parsed(channel_username)
                    logger.info(f"Обновлено время последнего парсинга для канала {channel_username}")

                    # Автоматический расчет метрик виральности для канала
                    try:
                        viral_calc_settings = supabase_manager.get_system_setting('viral_calculation') or {
                            'auto_calculate_viral': True
                        }

                        if viral_calc_settings.get('auto_calculate_viral', True):
                            logger.info(f"Автоматический расчет метрик для канала {channel_username}")

                            from .app.viral_post_detector import ViralPostDetector
                            from .app.channel_baseline_analyzer import ChannelBaselineAnalyzer

                            baseline_analyzer = ChannelBaselineAnalyzer(supabase_manager)
                            baseline = baseline_analyzer.get_channel_baseline(channel_username)

                            if not baseline:
                                baseline = baseline_analyzer.calculate_channel_baseline(channel_username)
                                if baseline:
                                    baseline_analyzer.save_channel_baseline(baseline)

                            if baseline:
                                detector = ViralPostDetector(baseline_analyzer)
                                viral_results = detector.detect_viral_posts(posts, channel_username)

                                processed_count = 0
                                for post, result in zip(posts, viral_results):
                                    # Проверяем наличие ID поста
                                    post_id = post.get('id')
                                    if post_id:
                                        if detector.update_post_viral_metrics(str(post_id), result):
                                            processed_count += 1
                                    else:
                                        logger.warning(f"Пост без ID пропущен: {post.get('message_id', 'unknown')} в канале {channel_username}")

                                viral_count = sum(1 for r in viral_results if r.is_viral)
                                logger.info(f"Канал {channel_username}: {viral_count} viral постов из {len(posts)}")

                    except Exception as e:
                        logger.error(f"Ошибка расчета метрик для канала {channel_username}: {e}")

                total_posts += len(posts)
                logger.info(f"Канал {channel_username}: найдено {len(posts)} постов")

            except Exception as e:
                logger.error(f"Ошибка парсинга канала {channel_username}: {e}")

        # Отключаемся от Telegram после завершения
        if telegram_connected and telegram_analyzer:
            try:
                await telegram_analyzer.disconnect()
                logger.info("Отключено от Telegram после массового парсинга")
            except Exception as e:
                logger.warning(f"Ошибка при отключении от Telegram: {e}")

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

# Эндпоинты для рубрик и форматов
@app.get("/api/rubrics", tags=["rubrics"])
async def get_rubrics():
    """Получить все рубрики."""
    try:
        result = supabase_manager.client.table('rubrics').select('*').order('name').execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка получения рубрик: {result.error}")

        return result.data or []

    except Exception as e:
        logger.error(f"Ошибка получения рубрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения рубрик: {str(e)}")

@app.get("/api/formats", tags=["formats"])
async def get_formats():
    """Получить все форматы."""
    try:
        result = supabase_manager.client.table('reel_formats').select('*').order('name').execute()

        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Ошибка получения форматов: {result.error}")

        return result.data or []

    except Exception as e:
        logger.error(f"Ошибка получения форматов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения форматов: {str(e)}")

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
