"""
Система управления промптами для LLM.
Содержит все промпты, контекст проекта и переменные для подстановки.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import os

from .settings import settings


@dataclass
class PromptTemplate:
    """Шаблон промпта с переменными."""
    name: str
    description: str
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Any]
    model_settings: Dict[str, Any]


class PromptManager:
    """Менеджер промптов для управления контекстом и шаблонами."""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.project_context = self._load_project_context()
        self._load_default_templates()

    def _load_project_context(self) -> Dict[str, Any]:
        """Загружает контекст проекта ПерепрошИИвка."""
        return {
            "project_name": "ПерепрошИИвка",
            "project_description": """
            ПерепрошИИвка - образовательный проект о технологиях, бизнесе и саморазвитии.
            Создаем короткие видео-ролики (Reels) с практическими советами и инсайтами.

            Целевая аудитория:
            - Специалисты IT сферы
            - Предприниматели и бизнесмены
            - Люди, интересующиеся технологиями и саморазвитием

            Формат контента:
            - Короткие видео 15-60 секунд
            - Практическая ценность
            - Доступный язык
            - Визуально привлекательный контент
            """,
            "content_principles": [
                "Фокус на практической пользе",
                "Простой и понятный язык",
                "Визуально привлекательные материалы",
                "Эмоциональная вовлеченность зрителя",
                "Конкретные actionable советы"
            ],
            "brand_voice": """
            - Профессиональный, но дружелюбный
            - Доступный, без сложного жаргона
            - Вдохновляющий и мотивирующий
            - Фокус на результатах и пользе
            """
        }

    def _load_default_templates(self):
        """Загружает стандартные шаблоны промптов."""

        # Шаблон для фильтрации
        self.templates["filter_posts"] = PromptTemplate(
            name="filter_posts",
            description="Фильтрация постов на пригодность для ПерепрошИИвка",
            system_prompt=f"""Ты - эксперт по анализу контента для социальных сетей.
Проект: {self.project_context['project_name']}
{self.project_context['project_description']}

Твоя задача: оценить, подходит ли пост из Telegram для создания образовательного контента.""",
            user_prompt="""Оцени этот пост по шкале 1-10:

ПОСТ:
{{post_text}}

МЕТРИКИ:
- Просмотры: {{views}}
- Реакции: {{reactions}}
- Комментарии: {{replies}}
- Репосты: {{forwards}}

Оцени по шкале 1-10 и определи, подходит ли для создания образовательного контента.

Верни только JSON: {{"score": число, "reason": "краткое объяснение", "suitable": true/false}}""",
            variables={
                "post_text": "",
                "views": 0,
                "reactions": 0,
                "replies": 0,
                "forwards": 0
            },
            model_settings={
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 300
            }
        )

        # Шаблон для анализа
        self.templates["analyze_success"] = PromptTemplate(
            name="analyze_success",
            description="Анализ причин успеха поста",
            system_prompt=f"""Ты - опытный аналитик контента для социальных сетей.
Проект: {self.project_context['project_name']}
{self.project_context['project_description']}

Твоя задача: глубоко проанализировать почему пост стал популярным.""",
            user_prompt="""Проанализируй этот успешный пост:

ПОСТ:
{{post_text}}

МЕТРИКИ ВОВЛЕЧЕННОСТИ:
- Просмотры: {{views}}
- Реакции: {{reactions}}
- Комментарии: {{replies}}
- Репосты: {{forwards}}

ПРОАНАЛИЗИРУЙ:
1. Почему этот пост стал популярным?
2. Какие ключевые факторы успеха?
3. Что можно взять для создания собственного контента?

Верни анализ в JSON формате:
{{
  "success_factors": ["фактор1", "фактор2", ...],
  "content_strengths": ["сильная сторона1", "сильная сторона2", ...],
  "audience_insights": ["инсайт1", "инсайт2", ...],
  "content_ideas": ["идея1", "идея2", ...],
  "lessons_learned": "выводы для нашего контента",
  "recommended_topics": ["тема1", "тема2", ...]
}}""",
            variables={
                "post_text": "",
                "views": 0,
                "reactions": 0,
                "replies": 0,
                "forwards": 0
            },
            model_settings={
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.4,
                "max_tokens": 2000
            }
        )

        # Шаблон для генерации
        self.templates["generate_scenario"] = PromptTemplate(
            name="generate_scenario",
            description="Генерация сценария для Reels",
            system_prompt=f"""Ты - креативный директор по контенту для TikTok/Reels.
Проект: {self.project_context['project_name']}
{self.project_context['project_description']}

{self.project_context['brand_voice']}

Создай сценарий с хуком, основной идеей и раскадровкой.""",
            user_prompt="""Создай сценарий Reels на основе этого поста:

ПОСТ:
{{post_text}}

АНАЛИЗ УСПЕХА:
{{analysis}}

РУБРИКА: {{rubric_name}}
ФОРМАТ: {{format_name}}
ДЛИТЕЛЬНОСТЬ: {{duration}} секунд

СОЗДАЙ СЦЕНАРИЙ:
1. Hook (3-5 секунд)
2. Основная идея (5-10 секунд)
3. Шаги/расказдровка (10-15 секунд)
4. Призыв к действию (3-5 секунд)

ВЕРНИ В ФОРМАТЕ JSON:
{{
  "title": "Название видео",
  "duration": {{duration}},
  "hook": {{
    "text": "Текст хука",
    "visual": "Описание визуала",
    "voiceover": "Текст для озвучки"
  }},
  "insight": {{
    "text": "Ключевой инсайт",
    "visual": "Визуальное оформление",
    "voiceover": "Текст для озвучки"
  }},
  "steps": [
    {{
      "step": 1,
      "title": "Название шага",
      "description": "Описание",
      "visual": "Визуальные элементы",
      "voiceover": "Текст для озвучки",
      "duration": 5
    }}
  ],
  "cta": {{
    "text": "Призыв к действию",
    "visual": "Визуальное оформление",
    "voiceover": "Текст для озвучки"
  }},
  "hashtags": ["#тег1", "#тег2"],
  "music_suggestion": "Рекомендация музыки"
}}""",
            variables={
                "post_text": "",
                "analysis": "",
                "rubric_name": "",
                "format_name": "",
                "duration": 30
            },
            model_settings={
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 3000
            }
        )

    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Получает шаблон промпта по имени."""
        return self.templates.get(template_name)

    def update_template(self, template_name: str, updates: Dict[str, Any]):
        """Обновляет шаблон промпта."""
        if template_name in self.templates:
            template = self.templates[template_name]
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)

    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """Возвращает все доступные шаблоны."""
        return self.templates.copy()

    def render_prompt(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Рендерит промпт с подстановкой переменных."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Шаблон {template_name} не найден")

        # Подставляем переменные в промпты
        system_prompt = template.system_prompt
        user_prompt = template.user_prompt

        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }

    def save_templates_to_file(self, file_path: Optional[str] = None):
        """Сохраняет шаблоны в YAML файл."""
        if not file_path:
            file_path = settings.base_dir / "prompts_config.yaml"

        data = {
            "project_context": self.project_context,
            "templates": {}
        }

        for name, template in self.templates.items():
            data["templates"][name] = {
                "name": template.name,
                "description": template.description,
                "system_prompt": template.system_prompt,
                "user_prompt": template.user_prompt,
                "variables": template.variables,
                "model_settings": template.model_settings
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def load_templates_from_file(self, file_path: Optional[str] = None):
        """Загружает шаблоны из YAML файла."""
        if not file_path:
            file_path = settings.base_dir / "prompts_config.yaml"

        if not Path(file_path).exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if "project_context" in data:
            self.project_context.update(data["project_context"])

        if "templates" in data:
            for name, template_data in data["templates"].items():
                self.templates[name] = PromptTemplate(**template_data)


# Глобальный экземпляр менеджера промптов
prompt_manager = PromptManager()
