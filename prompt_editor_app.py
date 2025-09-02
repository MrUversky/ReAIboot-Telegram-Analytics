#!/usr/bin/env python3
"""
Простое веб-приложение для редактирования промптов.
Запускает FastAPI сервер с интерфейсом для управления промптами.
"""

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import json
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.prompts import prompt_manager
from src.app.api_prompts import router as prompts_router

# Создаем FastAPI приложение
app = FastAPI(
    title="ReAIboot Prompt Editor",
    description="Интерфейс для редактирования промптов LLM",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(prompts_router)

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

# Создаем папку для шаблонов если её нет
Path("templates").mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница с редактором промптов."""
    templates_list = list(prompt_manager.get_all_templates().keys())
    return templates.TemplateResponse("index.html", {
        "request": request,
        "templates": templates_list,
        "project_context": prompt_manager.project_context
    })


@app.get("/template/{template_name}", response_class=HTMLResponse)
async def edit_template(request: Request, template_name: str):
    """Страница редактирования конкретного промпта."""
    template = prompt_manager.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Шаблон {template_name} не найден")

    return templates.TemplateResponse("edit_template.html", {
        "request": request,
        "template": template,
        "template_name": template_name
    })


@app.post("/template/{template_name}/update")
async def update_template_post(
    template_name: str,
    system_prompt: str = Form(...),
    user_prompt: str = Form(...),
    description: str = Form(...)
):
    """Обновление промпта через POST запрос."""
    updates = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "description": description
    }

    prompt_manager.update_template(template_name, updates)
    prompt_manager.save_templates_to_file()

    return {"message": f"Промпт {template_name} обновлен"}


@app.get("/test/{template_name}", response_class=HTMLResponse)
async def test_template(request: Request, template_name: str):
    """Страница тестирования промпта."""
    template = prompt_manager.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Шаблон {template_name} не найден")

    return templates.TemplateResponse("test_template.html", {
        "request": request,
        "template": template,
        "template_name": template_name
    })


@app.post("/test/{template_name}/run")
async def run_test(
    template_name: str,
    post_text: str = Form(""),
    views: int = Form(1000),
    reactions: int = Form(50),
    replies: int = Form(10),
    forwards: int = Form(25),
    rubric_name: str = Form("Технологии"),
    format_name: str = Form("Объяснение"),
    duration: int = Form(30),
    analysis: str = Form("")
):
    """Запуск теста промпта."""
    variables = {
        "post_text": post_text,
        "views": views,
        "reactions": reactions,
        "replies": replies,
        "forwards": forwards,
        "rubric_name": rubric_name,
        "format_name": format_name,
        "duration": duration,
        "analysis": analysis
    }

    try:
        rendered = prompt_manager.render_prompt(template_name, variables)
        return {
            "success": True,
            "rendered": rendered,
            "variables": variables
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Создаем базовые HTML шаблоны
def create_templates():
    """Создает базовые HTML шаблоны."""

    # Главная страница
    index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>ReAIboot Prompt Editor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .template-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .template-card h3 { margin-top: 0; }
        .btn { background: #007cba; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #005a87; }
    </style>
</head>
<body>
    <h1>🎯 ReAIboot Prompt Editor</h1>
    <p>Интерфейс для редактирования промптов LLM</p>

    <h2>📋 Доступные шаблоны промптов:</h2>
    {% for template_name in templates %}
    <div class="template-card">
        <h3>{{ template_name }}</h3>
        <a href="/template/{{ template_name }}" class="btn">✏️ Редактировать</a>
        <a href="/test/{{ template_name }}" class="btn">🧪 Тестировать</a>
    </div>
    {% endfor %}

    <h2>📖 Контекст проекта:</h2>
    <pre>{{ project_context | tojson(indent=2) }}</pre>
</body>
</html>
"""

    # Страница редактирования
    edit_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Редактирование: {{ template_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        textarea { width: 100%; min-height: 200px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #005a87; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
    </style>
</head>
<body>
    <h1>✏️ Редактирование промпта: {{ template_name }}</h1>
    <a href="/" class="btn btn-secondary">← Назад</a>

    <form method="post" action="/template/{{ template_name }}/update">
        <div class="form-group">
            <label>Описание:</label>
            <input type="text" name="description" value="{{ template.description }}" required>
        </div>

        <div class="form-group">
            <label>System Prompt:</label>
            <textarea name="system_prompt" required>{{ template.system_prompt }}</textarea>
        </div>

        <div class="form-group">
            <label>User Prompt:</label>
            <textarea name="user_prompt" required>{{ template.user_prompt }}</textarea>
        </div>

        <button type="submit" class="btn">💾 Сохранить изменения</button>
    </form>

    <h3>🔧 Переменные шаблона:</h3>
    <pre>{{ template.variables | tojson(indent=2) }}</pre>

    <h3>⚙️ Настройки модели:</h3>
    <pre>{{ template.model_settings | tojson(indent=2) }}</pre>
</body>
</html>
"""

    # Страница тестирования
    test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Тестирование: {{ template_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        textarea { width: 100%; min-height: 100px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        input[type="text"], input[type="number"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #005a87; }
        .btn-secondary { background: #6c757d; }
        .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .error { background: #f8d7da; }
    </style>
    <script>
        async function runTest() {
            const form = document.getElementById('testForm');
            const formData = new FormData(form);

            const response = await fetch('/test/{{ template_name }}/run', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            const resultDiv = document.getElementById('result');

            if (result.success) {
                resultDiv.innerHTML = `
                    <h3>✅ Результат рендеринга:</h3>
                    <h4>System Prompt:</h4>
                    <pre>${result.rendered.system_prompt}</pre>
                    <h4>User Prompt:</h4>
                    <pre>${result.rendered.user_prompt}</pre>
                    <h4>Использованные переменные:</h4>
                    <pre>${JSON.stringify(result.variables, null, 2)}</pre>
                `;
            } else {
                resultDiv.innerHTML = `<h3 class="error">❌ Ошибка: ${result.error}</h3>`;
            }
            resultDiv.classList.remove('error');
        }
    </script>
</head>
<body>
    <h1>🧪 Тестирование промпта: {{ template_name }}</h1>
    <a href="/" class="btn btn-secondary">← Назад</a>
    <a href="/template/{{ template_name }}" class="btn btn-secondary">✏️ Редактировать</a>

    <form id="testForm">
        <h3>📝 Входные данные для теста:</h3>

        <div class="form-group">
            <label>Текст поста:</label>
            <textarea name="post_text" placeholder="Вставьте текст поста для тестирования">🤖 Нейросети в бизнесе: +300% эффективности за 30 дней

Представьте, что ваш менеджер по продажам отвечает на 50 заявок в час вместо 5!
ИИ может делать это 24/7 без перерывов и ошибок.

Результаты наших клиентов:
✅ Автоматизация рутины -70%
✅ Рост продаж +150%
✅ Экономия бюджета -40%

Кто уже внедрил ИИ в свой бизнес? #AI #бизнес #автоматизация</textarea>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div class="form-group">
                <label>Просмотры:</label>
                <input type="number" name="views" value="6500">
            </div>
            <div class="form-group">
                <label>Реакции:</label>
                <input type="number" name="reactions" value="98">
            </div>
            <div class="form-group">
                <label>Комментарии:</label>
                <input type="number" name="replies" value="15">
            </div>
            <div class="form-group">
                <label>Репосты:</label>
                <input type="number" name="forwards" value="42">
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div class="form-group">
                <label>Рубрика:</label>
                <input type="text" name="rubric_name" value="Инструменты / Ресурсы">
            </div>
            <div class="form-group">
                <label>Формат:</label>
                <input type="text" name="format_name" value="Пояснение концепции">
            </div>
            <div class="form-group">
                <label>Длительность (сек):</label>
                <input type="number" name="duration" value="30">
            </div>
        </div>

        <div class="form-group">
            <label>Анализ успеха (опционально):</label>
            <textarea name="analysis" placeholder="Результаты анализа причин успеха поста"></textarea>
        </div>

        <button type="button" onclick="runTest()" class="btn">🚀 Запустить тест</button>
    </form>

    <div id="result" class="result" style="display: none;"></div>

    <script>
        document.getElementById('result').style.display = 'block';
    </script>
</body>
</html>
"""

    # Сохраняем шаблоны
    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    with open("templates/edit_template.html", "w", encoding="utf-8") as f:
        f.write(edit_html)

    with open("templates/test_template.html", "w", encoding="utf-8") as f:
        f.write(test_html)


if __name__ == "__main__":
    # Создаем шаблоны
    create_templates()

    # Запускаем сервер
    print("🚀 Запуск Prompt Editor...")
    print("📱 Откройте браузер: http://localhost:8000")
    print("🎯 Доступные эндпоинты:")
    print("   / - Главная страница")
    print("   /template/{name} - Редактирование промпта")
    print("   /test/{name} - Тестирование промпта")
    print("   /docs - API документация")

    uvicorn.run(app, host="0.0.0.0", port=8000)
