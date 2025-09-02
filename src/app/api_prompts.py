"""
API endpoints для управления промптами.
Позволяет редактировать промпты через UI.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .prompts import prompt_manager, PromptTemplate


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptUpdate(BaseModel):
    """Модель для обновления промпта."""
    name: str
    description: str = None
    system_prompt: str = None
    user_prompt: str = None
    variables: Dict[str, Any] = None
    model_settings: Dict[str, Any] = None


class PromptResponse(BaseModel):
    """Модель ответа с промптом."""
    name: str
    description: str
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Any]
    model_settings: Dict[str, Any]


@router.get("/", response_model=Dict[str, PromptResponse])
async def get_all_prompts():
    """Получить все доступные промпты."""
    templates = prompt_manager.get_all_templates()
    result = {}

    for name, template in templates.items():
        result[name] = PromptResponse(
            name=template.name,
            description=template.description,
            system_prompt=template.system_prompt,
            user_prompt=template.user_prompt,
            variables=template.variables,
            model_settings=template.model_settings
        )

    return result


@router.get("/{template_name}", response_model=PromptResponse)
async def get_prompt(template_name: str):
    """Получить конкретный промпт по имени."""
    template = prompt_manager.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Промпт {template_name} не найден")

    return PromptResponse(
        name=template.name,
        description=template.description,
        system_prompt=template.system_prompt,
        user_prompt=template.user_prompt,
        variables=template.variables,
        model_settings=template.model_settings
    )


@router.put("/{template_name}")
async def update_prompt(template_name: str, updates: PromptUpdate):
    """Обновить промпт."""
    if template_name not in prompt_manager.templates:
        raise HTTPException(status_code=404, detail=f"Промпт {template_name} не найден")

    # Преобразуем Pydantic модель в словарь, исключая None значения
    update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)

    # Удаляем поле name из обновлений (его нельзя менять)
    update_dict.pop("name", None)

    prompt_manager.update_template(template_name, update_dict)

    # Сохраняем изменения в файл
    prompt_manager.save_templates_to_file()

    return {"message": f"Промпт {template_name} обновлен"}


@router.post("/{template_name}/test")
async def test_prompt(template_name: str, variables: Dict[str, Any]):
    """Протестировать промпт с переменными."""
    try:
        rendered = prompt_manager.render_prompt(template_name, variables)
        return {
            "template_name": template_name,
            "rendered": rendered,
            "variables_used": variables
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/context/project")
async def get_project_context():
    """Получить контекст проекта."""
    return prompt_manager.project_context


@router.put("/context/project")
async def update_project_context(context: Dict[str, Any]):
    """Обновить контекст проекта."""
    prompt_manager.project_context.update(context)
    prompt_manager.save_templates_to_file()
    return {"message": "Контекст проекта обновлен"}


@router.post("/save")
async def save_prompts():
    """Сохранить все промпты в файл."""
    prompt_manager.save_templates_to_file()
    return {"message": "Промпты сохранены в файл"}


@router.post("/load")
async def load_prompts():
    """Загрузить промпты из файла."""
    prompt_manager.load_templates_from_file()
    return {"message": "Промпты загружены из файла"}
