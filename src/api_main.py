"""
Основной FastAPI сервер для ReAIboot.
Предоставляет REST API для всех функций системы.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import logging

# Импорты из нашего проекта
from .app.llm.orchestrator import LLMOrchestrator
from .app.prompts import prompt_manager
from .app.settings import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="ReAIboot API",
    description="API для анализа Telegram постов и генерации сценариев",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшн указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный оркестратор
orchestrator = LLMOrchestrator()

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

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_status: Dict[str, bool]

# Эндпоинты

@app.get("/", tags=["health"])
async def root():
    """Корневой эндпоинт."""
    return {"message": "ReAIboot API", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Проверка здоровья системы."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_status=orchestrator.get_processor_status()
    )

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

# Статистика и метрики

@app.get("/api/stats/llm", tags=["stats"])
async def get_llm_stats():
    """Получить статистику использования LLM."""
    return {
        "processor_status": orchestrator.get_processor_status(),
        "available_templates": list(prompt_manager.get_all_templates().keys()),
        "project_context_keys": list(prompt_manager.project_context.keys())
    }

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
