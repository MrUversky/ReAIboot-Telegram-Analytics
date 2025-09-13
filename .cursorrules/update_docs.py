#!/usr/bin/env python3
"""
Documentation Auto-Update Script

Automatically updates documentation based on code changes.
This script analyzes code changes and generates/updates corresponding documentation.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@dataclass
class CodeChange:
    """Represents a code change"""

    file_path: str
    change_type: str  # 'added', 'modified', 'deleted'
    content: str
    line_number: Optional[int] = None


@dataclass
class DocumentationUpdate:
    """Represents a documentation update"""

    file_path: str
    content: str
    change_type: str  # 'create', 'update', 'delete'


class DocumentationAgent:
    """Main class for documentation updates"""

    def __init__(self, project_root: str, force_ai: bool = False):
        self.project_root = Path(project_root)
        self.docs_root = self.project_root / "docs"
        self.api_docs_root = self.docs_root / "technical" / "api" / "endpoints"
        self.force_ai = force_ai

        # Performance metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "files_analyzed": 0,
            "changes_found": 0,
            "updates_applied": 0,
            "errors": [],
        }

    def analyze_changes(self, changed_files: List[str]) -> List[CodeChange]:
        """Analyze changed files and extract relevant changes"""
        changes = []
        self.metrics["start_time"] = time.time()
        self.metrics["files_analyzed"] = len(changed_files)

        for i, file_path in enumerate(changed_files):
            full_path = self.project_root / file_path

            if not full_path.exists():
                continue

            # Analyze file based on type
            if file_path.endswith(".py"):
                file_changes = self._analyze_python_file(file_path, full_path)
                changes.extend(file_changes)
            elif file_path.endswith((".js", ".ts", ".tsx")):
                file_changes = self._analyze_javascript_file(file_path, full_path)
                changes.extend(file_changes)
            elif file_path.endswith(".sql"):
                file_changes = self._analyze_sql_file(file_path, full_path)
                changes.extend(file_changes)
            elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                file_changes = self._analyze_config_file(file_path, full_path)
                changes.extend(file_changes)

            # Analyze Python files for business logic (additional to API analysis)
            if file_path.endswith(".py") and not "test" in file_path.lower():
                business_changes = self._analyze_business_logic_file(
                    file_path, full_path
                )
                changes.extend(business_changes)

        # Update metrics
        self.metrics["changes_found"] = len(changes)
        self.metrics["end_time"] = time.time()

        return changes

    def _analyze_python_file(self, file_path: str, full_path: Path) -> List[CodeChange]:
        """Analyze Python file for API endpoints and functions"""
        changes = []

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find FastAPI endpoints
        endpoint_pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*r?[\'"]([^\'"]+)[\'"]\s*.*?\)\s*async def\s+(\w+)'
        matches = re.finditer(endpoint_pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            method, path, func_name = match.groups()
            line_number = content[: match.start()].count("\n") + 1

            # Extract function signature and docstring
            func_start = match.end()
            func_end_pattern = r"(?=@app\.|\nclass|\ndef|\n@|$)"
            func_end_match = re.search(
                func_end_pattern, content[func_start:], re.MULTILINE
            )

            if func_end_match:
                func_content = content[func_start : func_start + func_end_match.start()]
            else:
                func_content = content[func_start:]

            changes.append(
                CodeChange(
                    file_path=file_path,
                    change_type="api_endpoint",
                    content=f"Method: {method.upper()}\nPath: {path}\nFunction: {func_name}\nContent: {func_content[:500]}...",
                    line_number=line_number,
                )
            )

        return changes

    def _analyze_sql_file(self, file_path: str, full_path: Path) -> List[CodeChange]:
        """Analyze SQL file for schema changes"""
        changes = []

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find table creation/alteration
        table_pattern = r"(CREATE TABLE|ALTER TABLE|DROP TABLE)\s+(\w+)"
        matches = re.finditer(table_pattern, content, re.IGNORECASE)

        for match in matches:
            operation, table_name = match.groups()
            line_number = content[: match.start()].count("\n") + 1

            changes.append(
                CodeChange(
                    file_path=file_path,
                    change_type="database_schema",
                    content=f"Operation: {operation}\nTable: {table_name}",
                    line_number=line_number,
                )
            )

        return changes

    def _analyze_config_file(self, file_path: str, full_path: Path) -> List[CodeChange]:
        """Analyze configuration files for changes"""
        changes = []

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # For now, just mark config files as changed
        # In future, could parse specific config formats
        changes.append(
            CodeChange(
                file_path=file_path,
                change_type="configuration",
                content=f"Configuration file: {file_path}",
                line_number=1,
            )
        )

        return changes

    def _analyze_javascript_file(
        self, file_path: str, full_path: Path
    ) -> List[CodeChange]:
        """Analyze JavaScript/TypeScript file for components and functions"""
        changes = []

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find React components (function/class components)
        component_patterns = [
            r"^function\s+(\w+)\s*\(",  # Function components
            r"^const\s+(\w+)\s*=\s*\(",  # Arrow function components
            r"^export\s+(?:default\s+)?function\s+(\w+)",  # Exported functions
            r"^export\s+(?:const|function)\s+(\w+)",  # Export declarations
        ]

        for i, line in enumerate(lines):
            for pattern in component_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    component_name = match.group(1)
                    if not component_name.startswith("_"):  # Skip private components
                        component_info = self._extract_js_component_info(content, i)
                        changes.append(
                            CodeChange(
                                file_path=file_path,
                                change_type="frontend_component",
                                content=f"Component: {component_name}\nInfo: {component_info}",
                                line_number=i + 1,
                            )
                        )
                        break  # Only add once per component

        # Find API calls and external integrations
        api_patterns = [
            r"fetch\s*\(",
            r"axios\.",
            r"api\.",
            r"\.post\s*\(",
            r"\.get\s*\(",
        ]

        for pattern in api_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[: match.start()].count("\n") + 1
                context = self._get_context_lines(lines, line_number - 1, 2)
                changes.append(
                    CodeChange(
                        file_path=file_path,
                        change_type="frontend_component",
                        content=f"API call: {match.group()}\nContext: {context}",
                        line_number=line_number,
                    )
                )

        return changes

    def _extract_js_component_info(
        self, content: str, component_line_index: int
    ) -> str:
        """Extract basic information about a JS/TS component"""
        lines = content.split("\n")
        info = []

        # Look for props interface or type
        for i in range(
            component_line_index - 5, min(component_line_index + 10, len(lines))
        ):
            if i >= 0:
                line = lines[i].strip()
                if "interface" in line and "Props" in line:
                    info.append("Has Props interface")
                    break
                elif "type" in line and "=" in line:
                    info.append("Has type definition")
                    break

        # Check for hooks usage
        component_end = min(component_line_index + 50, len(lines))
        component_content = "\n".join(lines[component_line_index:component_end])

        hooks = []
        if "useState" in component_content:
            hooks.append("useState")
        if "useEffect" in component_content:
            hooks.append("useEffect")
        if "useContext" in component_content:
            hooks.append("useContext")

        if hooks:
            info.append(f"Uses hooks: {', '.join(hooks)}")

        return "; ".join(info) if info else "Frontend component"

    def _analyze_business_logic_file(
        self, file_path: str, full_path: Path
    ) -> List[CodeChange]:
        """Analyze Python file for business logic changes (classes, methods, LLM interactions)"""
        changes = []

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find classes
        class_pattern = r"^class\s+(\w+)"
        for i, line in enumerate(lines):
            class_match = re.match(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                # Extract class docstring and basic info
                class_info = self._extract_class_info(content, i)
                changes.append(
                    CodeChange(
                        file_path=file_path,
                        change_type="business_logic",
                        content=f"Class: {class_name}\nInfo: {class_info}",
                        line_number=i + 1,
                    )
                )

        # Find important functions (not API endpoints)
        func_pattern = r"^def\s+(\w+)\s*\("
        for i, line in enumerate(lines):
            func_match = re.match(func_pattern, line)
            if func_match:
                func_name = func_match.group(1)
                # Skip if it's an API endpoint (already analyzed)
                if not any(
                    keyword in func_name.lower()
                    for keyword in ["get", "post", "put", "delete", "patch"]
                ):
                    func_info = self._extract_function_info(content, i)
                    changes.append(
                        CodeChange(
                            file_path=file_path,
                            change_type="business_logic",
                            content=f"Function: {func_name}\nInfo: {func_info}",
                            line_number=i + 1,
                        )
                    )

        # Find LLM-related patterns
        llm_patterns = [
            r"openai\.|claude\.|anthropic\.|gpt-",
            r"client\.chat\.completions\.create",
            r"prompt_manager\.|PromptManager",
            r"LLM.*process|process.*LLM",
        ]

        for pattern in llm_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_number = content[: match.start()].count("\n") + 1
                context = self._get_context_lines(lines, line_number - 1, 3)
                changes.append(
                    CodeChange(
                        file_path=file_path,
                        change_type="business_logic",
                        content=f"LLM interaction: {match.group()}\nContext: {context}",
                        line_number=line_number,
                    )
                )

        return changes

    def _extract_class_info(self, content: str, class_line_index: int) -> str:
        """Extract basic information about a class"""
        lines = content.split("\n")
        info = []

        # Look for docstring
        for i in range(class_line_index + 1, min(class_line_index + 10, len(lines))):
            line = lines[i].strip()
            if '"""' in line or "'''" in line:
                # Found docstring start
                docstring_lines = []
                in_docstring = True
                j = i
                while j < len(lines) and in_docstring:
                    docstring_lines.append(lines[j])
                    if ('"""' in lines[j] or "'''" in lines[j]) and j > i:
                        in_docstring = False
                    j += 1
                if docstring_lines:
                    info.append("Docstring: " + " ".join(docstring_lines)[:200] + "...")
                break

        # Look for __init__ method
        for i in range(class_line_index + 1, min(class_line_index + 20, len(lines))):
            if "def __init__" in lines[i]:
                info.append("Has __init__ method")
                break

        return "; ".join(info) if info else "No additional info"

    def _extract_function_info(self, content: str, func_line_index: int) -> str:
        """Extract basic information about a function"""
        lines = content.split("\n")
        info = []

        # Look for docstring
        for i in range(func_line_index + 1, min(func_line_index + 10, len(lines))):
            line = lines[i].strip()
            if '"""' in line or "'''" in line:
                docstring_lines = []
                in_docstring = True
                j = i
                while j < len(lines) and in_docstring:
                    docstring_lines.append(lines[j])
                    if ('"""' in lines[j] or "'''" in lines[j]) and j > i:
                        in_docstring = False
                    j += 1
                if docstring_lines:
                    info.append("Docstring: " + " ".join(docstring_lines)[:200] + "...")
                break

        # Check function parameters
        func_line = lines[func_line_index]
        if "(" in func_line and ")" in func_line:
            params_start = func_line.find("(")
            params_end = func_line.find(")")
            params = func_line[params_start : params_end + 1]
            if len(params) > 2:  # More than just ()
                info.append(f"Parameters: {params}")

        return "; ".join(info) if info else "No additional info"

    def _get_context_lines(
        self, lines: List[str], start_index: int, num_lines: int
    ) -> str:
        """Get context lines around a specific line"""
        start = max(0, start_index - num_lines)
        end = min(len(lines), start_index + num_lines + 1)
        return "\n".join(lines[start:end])

    def _create_api_section_template(self, section: str) -> str:
        """Create template for API section documentation"""

        section_descriptions = {
            "llm": {
                "title": "LLM API - Искусственный интеллект",
                "description": "Эндпоинты для работы с моделями искусственного интеллекта, генерации контента и анализа постов.",
                "purpose": "Обработка запросов к LLM, генерация сценариев контента, анализ текстовых данных.",
            },
            "posts": {
                "title": "Posts API - Посты и контент",
                "description": "Управление постами Telegram, расчет вирусности, статистика и аналитика.",
                "purpose": "CRUD операции с постами, расчет метрик вовлеченности, получение статистики.",
            },
            "sandbox": {
                "title": "Sandbox API - Песочница для тестирования",
                "description": "Отладочная среда для тестирования LLM пайплайна и отладки генерации контента.",
                "purpose": "Тестирование полного цикла обработки постов, отладка и мониторинг.",
            },
            "admin": {
                "title": "Admin API - Администрирование",
                "description": "Административные функции, управление промптами, системные настройки.",
                "purpose": "Управление системой, обновление конфигураций, мониторинг состояния.",
            },
            "general": {
                "title": "General API - Общие эндпоинты",
                "description": "Общие API эндпоинты для статистики, здоровья системы и вспомогательных функций.",
                "purpose": "Мониторинг системы, получение общей статистики, вспомогательные функции.",
            },
        }

        desc = section_descriptions.get(
            section,
            {
                "title": f"API {section.title()}",
                "description": f"Эндпоинты для работы с {section}.",
                "purpose": f"Управление функциональностью {section}.",
            },
        )

        return f"""# {desc['title']}

## Обзор

{desc['description']}

### Назначение
{desc['purpose']}

### Аутентификация
Все эндпоинты требуют валидной аутентификации через API ключи или Bearer токены.

### Формат данных
- **Request/Response**: JSON
- **Encoding**: UTF-8
- **Errors**: Стандартный формат ошибок API

---

## Эндпоинты
"""

    def generate_documentation_updates(
        self, changes: List[CodeChange]
    ) -> List[DocumentationUpdate]:
        """Generate documentation updates based on code changes"""
        updates = []

        for change in changes:
            if change.change_type == "api_endpoint":
                update = self._generate_api_docs(change)
                if update:
                    updates.append(update)
            elif change.change_type == "database_schema":
                update = self._generate_db_docs(change)
                if update:
                    updates.append(update)
            elif change.change_type == "business_logic":
                update = self._generate_architecture_docs(change)
                if update:
                    updates.append(update)
            elif change.change_type == "frontend_component":
                update = self._generate_frontend_docs(change)
                if update:
                    updates.append(update)
            elif change.change_type == "configuration":
                # TODO: Добавить генерацию документации для конфигураций
                logger.info(f"Configuration change detected: {change.file_path}")

        return updates

    def _generate_api_docs(self, change: CodeChange) -> Optional[DocumentationUpdate]:
        """Generate API documentation for endpoint"""
        lines = change.content.split("\n")
        method = None
        path = None
        func_name = None

        for line in lines:
            if line.startswith("Method: "):
                method = line.replace("Method: ", "")
            elif line.startswith("Path: "):
                path = line.replace("Path: ", "")
            elif line.startswith("Function: "):
                func_name = line.replace("Function: ", "")

        if not all([method, path, func_name]):
            return None

        # Determine which API section this belongs to
        if "/posts" in path:
            section = "posts"
        elif "/llm" in path:
            section = "llm"
        elif "/sandbox" in path:
            section = "sandbox"
        elif "/admin" in path or "admin" in path:
            section = "admin"
        else:
            section = "general"

        docs_path = self.api_docs_root / f"{section}.md"

        # Check if docs file exists
        if docs_path.exists():
            # Update existing file
            with open(docs_path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Check if endpoint already documented
            if f"**Эндпоинт:** `{method} {path}`" in current_content:
                logger.info(f"Endpoint {method} {path} already documented")
                return None

            # Add new endpoint documentation
            new_content = self._generate_endpoint_section(
                method, path, func_name, change.content
            )
            updated_content = current_content + "\n\n" + new_content

            return DocumentationUpdate(
                file_path=str(docs_path), content=updated_content, change_type="update"
            )
        else:
            # Create new file with proper template
            template = self._create_api_section_template(section)
            content = (
                template
                + "\n\n"
                + self._generate_endpoint_section(
                    method, path, func_name, change.content
                )
            )

            return DocumentationUpdate(
                file_path=str(docs_path), content=content, change_type="create"
            )

    def _generate_endpoint_section(
        self, method: str, path: str, func_name: str, details: str
    ) -> str:
        """Generate documentation section for an endpoint"""
        section = f"""## {func_name.replace('_', ' ').title()}

**Эндпоинт:** `{method} {path}`

**Аутентификация:** API Key

### Описание
Автоматически сгенерированная документация для эндпоинта {func_name}.

### Детали реализации
```
Function: {func_name}
Location: {details.split('Location: ')[1] if 'Location: ' in details else 'Unknown'}
```

---

*Сгенерировано автоматически: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return section

    def _generate_db_docs(self, change: CodeChange) -> Optional[DocumentationUpdate]:
        """Generate database documentation"""
        # This would be more complex in a real implementation
        logger.info(f"Database change detected: {change.content}")
        return None

    def _generate_architecture_docs(
        self, change: CodeChange
    ) -> Optional[DocumentationUpdate]:
        """Generate architecture documentation for business logic"""
        lines = change.content.split("\n")
        component_type = None
        component_name = None
        component_info = None

        for line in lines:
            if line.startswith("Class: "):
                component_type = "class"
                component_name = line.replace("Class: ", "")
            elif line.startswith("Function: "):
                component_type = "function"
                component_name = line.replace("Function: ", "")
            elif line.startswith("LLM interaction: "):
                component_type = "llm_interaction"
                component_name = line.replace("LLM interaction: ", "")
            elif line.startswith("Info: ") or line.startswith("Context: "):
                component_info = line.replace("Info: ", "").replace("Context: ", "")

        if not component_type or not component_name:
            return None

        # Determine which architecture document to update
        if component_type == "class":
            docs_path = self.docs_root / "technical" / "architecture" / "components.md"
            section = "Классы и компоненты"
        elif component_type == "function":
            docs_path = self.docs_root / "technical" / "architecture" / "components.md"
            section = "Функции"
        elif component_type == "llm_interaction":
            docs_path = (
                self.docs_root / "technical" / "architecture" / "llm-integration.md"
            )
            section = "Интеграция с LLM"
        else:
            return None

        # Create architecture docs directory if needed
        docs_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if docs file exists
        if docs_path.exists():
            with open(docs_path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Check if component already documented
            if f"### {component_name}" in current_content and not self.force_ai:
                logger.info(f"Component {component_name} already documented")
                return None

            change_type = "update"
        else:
            # Create new architecture file
            current_content = self._create_architecture_template(component_type)
            change_type = "create"

        # Generate component documentation
        component_docs = self._generate_component_docs(
            component_type, component_name, component_info, change.file_path
        )

        # Add to appropriate section
        if f"## {section}" in current_content:
            # Insert after section header
            section_pattern = f"## {section}\n"
            insert_position = current_content.find(section_pattern) + len(
                section_pattern
            )
            updated_content = (
                current_content[:insert_position]
                + "\n"
                + component_docs
                + "\n"
                + current_content[insert_position:]
            )
        else:
            # Add new section
            updated_content = current_content + f"\n## {section}\n\n{component_docs}\n"

        return DocumentationUpdate(
            file_path=str(docs_path), change_type=change_type, content=updated_content
        )

    def _create_architecture_template(self, component_type: str) -> str:
        """Create template for architecture documentation"""

        if component_type in ["class", "function"]:
            return """# Архитектура системы

## Обзор

Этот документ описывает основные компоненты и архитектуру системы ReAIboot.

## Классы и компоненты

Здесь описаны основные классы системы и их назначение.

## Функции

Здесь описаны ключевые функции и их роль в системе.

## Взаимодействие компонентов

Диаграмма взаимодействия основных компонентов:

```
Frontend (Next.js) <-> API (FastAPI) <-> LLM Services <-> Database (Supabase)
```

## Поток данных

1. Пользователь отправляет запрос через UI
2. API получает запрос и валидирует данные
3. Данные передаются в LLM процессоры
4. Результат сохраняется в базу данных
5. Ответ возвращается пользователю
"""
        elif component_type == "llm_interaction":
            return """# Интеграция с LLM

## Обзор

Этот документ описывает интеграцию системы с моделями искусственного интеллекта.

## Используемые модели

- **Claude 3.5 Sonnet** - основной движок для генерации контента
- **GPT-4o** - резервная модель для сложных задач

## Архитектура взаимодействия

### Основной поток:
1. Получение запроса от API
2. Подготовка промпта через PromptManager
3. Отправка запроса к LLM
4. Обработка и парсинг ответа
5. Сохранение результатов

## Компоненты интеграции

### LLMOrchestrator
Основной координатор всех LLM операций.

### Специализированные процессоры:
- FilterProcessor - фильтрация контента
- AnalysisProcessor - анализ постов
- RubricSelectorProcessor - выбор рубрики и формата
- GeneratorProcessor - генерация сценариев

## Промпты и шаблоны

Все промпты хранятся в базе данных Supabase в таблице `prompt_templates`.

## Обработка ошибок

- Таймауты запросов
- Парсинг невалидного JSON
- Fallback на резервные модели
"""

        return "# Архитектура системы\n\nДокументация в разработке.\n"

    def _generate_component_docs(
        self,
        component_type: str,
        component_name: str,
        component_info: str,
        file_path: str,
    ) -> str:
        """Generate documentation for a specific component"""

        if component_type == "class":
            return f"""### {component_name}

**Файл:** `{file_path}`

**Описание:** {component_info}

**Назначение:** [Требуется описание]

**Методы:** [Требуется описание]

**Зависимости:** [Требуется анализ]
"""

        elif component_type == "function":
            return f"""### {component_name}

**Файл:** `{file_path}`

**Сигнатура:** {component_info}

**Назначение:** [Требуется описание]

**Параметры:**
- [Требуется анализ параметров]

**Возвращаемое значение:** [Требуется анализ]
"""

        elif component_type == "llm_interaction":
            return f"""### Интеграция: {component_name}

**Файл:** `{file_path}`

**Контекст:** {component_info}

**Тип взаимодействия:** [API вызов / Обработка ответа / Управление промптами]

**Модель:** [Claude / GPT / другая]

**Назначение:** [Требуется описание]
"""

        # Try to generate AI description if OpenAI is available
        ai_description = self._generate_ai_component_description(
            component_type, component_name, component_info, file_path
        )
        if ai_description:
            return ai_description

        return f"### {component_name}\n\nДокументация в разработке.\n"

    def _generate_ai_component_description(
        self,
        component_type: str,
        component_name: str,
        component_info: str,
        file_path: str,
    ) -> Optional[str]:
        """Generate AI-powered description for component"""
        try:
            import os

            import openai

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None

            client = openai.Client(api_key=api_key)

            # Extract relevant context for AI analysis
            try:
                file_content = self._extract_component_context(file_path, component_name, component_type)
            except Exception as e:
                logger.warning(f"Failed to extract context for {component_name}: {e}")
                file_content = f"File: {file_path}\nComponent: {component_name}\nType: {component_type}\nContext extraction failed."

            prompt = f"""
            Проанализируй этот компонент системы ReAIboot и создай краткое описание на русском языке.

            Тип компонента: {component_type}
            Название: {component_name}
            Информация: {component_info}
            Файл: {file_path}

            Контекст файла (первые 2000 символов):
            {file_content}

            Создай описание включающее:
            1. Назначение компонента
            2. Основные методы/функции
            3. Зависимости и связи с другими компонентами
            4. Особенности реализации

            Формат ответа - Markdown с заголовками.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,  # Reduced from 500
                temperature=0.3,
            )

            description = response.choices[0].message.content.strip()

            return f"""### {component_name}

**Файл:** `{file_path}`

**Описание:** {component_info}

{description}
"""

        except Exception as e:
            logger.warning(f"Failed to generate AI description: {e}")
            return None

    def _extract_component_context(self, file_path: str, component_name: str, component_type: str) -> str:
        """Extract relevant context for AI analysis without sending entire file"""
        try:
            with open(self.project_root / file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            return f"Could not read file: {file_path}"

        lines = content.split('\n')
        context_parts = []

        # Add file header info
        context_parts.append(f"File: {file_path}")
        context_parts.append(f"Component: {component_name} ({component_type})")

        # Extract imports (first 10 lines typically)
        imports = []
        for line in lines[:20]:  # Check first 20 lines for imports
            line = line.strip()
            if line.startswith(('import ', 'from ')) and not line.startswith('from typing'):
                imports.append(line)
            if len(imports) >= 5:  # Limit imports
                break
        if imports:
            context_parts.append("\nKey imports:")
            context_parts.extend(imports[:5])

        # Find component definition and extract docstring + method signatures
        in_component = False
        component_start = -1
        brace_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Find component start
            if not in_component:
                if component_type == "class" and stripped.startswith(f"class {component_name}"):
                    in_component = True
                    component_start = i
                    # Extract class docstring
                    docstring = self._extract_docstring(lines, i)
                    if docstring:
                        context_parts.append(f"\nClass docstring:\n{docstring}")
                elif component_type == "function" and (stripped.startswith(f"def {component_name}") or stripped.startswith(f"async def {component_name}")):
                    in_component = True
                    component_start = i
                    # Extract function docstring
                    docstring = self._extract_docstring(lines, i)
                    if docstring:
                        context_parts.append(f"\nFunction docstring:\n{docstring}")
                    # For functions, also add the signature
                    context_parts.append(f"\nFunction signature:\n{line}")
                    break  # Functions are simpler, just signature + docstring

            # For classes, extract method signatures
            elif component_type == "class" and in_component:
                if stripped.startswith(('def ', 'async def ')) and not stripped.startswith('    ') and brace_count == 0:
                    # This is a method definition
                    method_name = stripped.split('(')[0].replace('def ', '').replace('async def ', '')
                    context_parts.append(f"\nMethod: {method_name}")
                    # Extract method docstring
                    method_docstring = self._extract_docstring(lines, i)
                    if method_docstring:
                        context_parts.append(f"  Docstring: {method_docstring[:100]}...")

                # Track braces for nested structures
                brace_count += stripped.count('{') - stripped.count('}')
                if brace_count < 0:  # End of class
                    break

        # Limit total context length
        full_context = '\n'.join(context_parts)
        if len(full_context) > 1500:  # Reasonable limit
            full_context = full_context[:1500] + "\n\n[Context truncated for length]"

        return full_context

    def _extract_docstring(self, lines: List[str], start_idx: int) -> str:
        """Extract docstring starting from given line index"""
        if start_idx + 1 >= len(lines):
            return ""

        # Look for triple quotes
        line = lines[start_idx + 1].strip()
        if line.startswith('"""') or line.startswith("'''"):
            quote_type = '"""' if line.startswith('"""') else "'''"
            docstring_lines = []

            # First line
            first_line = line.replace(quote_type, '').strip()
            if first_line:
                docstring_lines.append(first_line)

            # Continue until closing quotes
            for i in range(start_idx + 2, len(lines)):
                line = lines[i]
                if quote_type in line:
                    # Last line
                    last_part = line.split(quote_type)[0].strip()
                    if last_part:
                        docstring_lines.append(last_part)
                    break
                else:
                    docstring_lines.append(line.strip())

            return '\n'.join(docstring_lines)
        return ""

    def _generate_frontend_docs(
        self, change: CodeChange
    ) -> Optional[DocumentationUpdate]:
        """Generate frontend documentation for components"""
        lines = change.content.split("\n")
        component_type = None
        component_name = None
        component_info = None

        for line in lines:
            if line.startswith("Component: "):
                component_type = "component"
                component_name = line.replace("Component: ", "")
            elif line.startswith("API call: "):
                component_type = "api_call"
                component_name = line.replace("API call: ", "")
            elif line.startswith("Info: ") or line.startswith("Context: "):
                component_info = line.replace("Info: ", "").replace("Context: ", "")

        if not component_type or not component_name:
            return None

        # Create frontend docs directory
        docs_path = self.docs_root / "technical" / "frontend" / "components.md"
        docs_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if docs file exists
        if docs_path.exists():
            with open(docs_path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Check if component already documented
            if f"### {component_name}" in current_content:
                logger.info(f"Frontend component {component_name} already documented")
                return None

            change_type = "update"
        else:
            # Create new frontend file
            current_content = self._create_frontend_template()
            change_type = "create"

        # Generate component documentation
        component_docs = self._generate_frontend_component_docs(
            component_type, component_name, component_info, change.file_path
        )

        # Add to appropriate section
        section = (
            "React Компоненты" if component_type == "component" else "API Интеграции"
        )
        if f"## {section}" in current_content:
            section_pattern = f"## {section}\n"
            insert_position = current_content.find(section_pattern) + len(
                section_pattern
            )
            updated_content = (
                current_content[:insert_position]
                + "\n"
                + component_docs
                + "\n"
                + current_content[insert_position:]
            )
        else:
            updated_content = current_content + f"\n## {section}\n\n{component_docs}\n"

        return DocumentationUpdate(
            file_path=str(docs_path), change_type=change_type, content=updated_content
        )

    def _create_frontend_template(self) -> str:
        """Create template for frontend documentation"""
        return """# Frontend Компоненты

## Обзор

Этот документ описывает компоненты и интеграции frontend части системы ReAIboot.

## React Компоненты

Здесь описаны основные React компоненты системы.

## API Интеграции

Здесь описаны интеграции с backend API и внешними сервисами.

## Архитектура Frontend

```
React Components <-> API Layer <-> Backend Services
```

## Технологии

- **React** - UI фреймворк
- **TypeScript** - типизация
- **Next.js** - React фреймворк
- **Tailwind CSS** - стилизация
"""

    def _generate_frontend_component_docs(
        self,
        component_type: str,
        component_name: str,
        component_info: str,
        file_path: str,
    ) -> str:
        """Generate documentation for frontend component"""

        if component_type == "component":
            return f"""### {component_name}

**Файл:** `{file_path}`

**Описание:** {component_info}

**Тип:** React компонент

**Назначение:** [Требуется описание]

**Props:** [Требуется анализ]

**Состояние:** [Требуется анализ]
"""

        elif component_type == "api_call":
            return f"""### API вызов: {component_name}

**Файл:** `{file_path}`

**Контекст:** {component_info}

**Тип вызова:** [GET/POST/PUT/DELETE]

**Эндпоинт:** [Требуется анализ]

**Назначение:** [Требуется описание]
"""

        return f"### {component_name}\n\nДокументация в разработке.\n"

    def apply_updates(self, updates: List[DocumentationUpdate]) -> None:
        """Apply documentation updates to files"""
        self.metrics["updates_applied"] = len(updates)

        for update in updates:
            docs_path = Path(update.file_path)

            # Create directory if it doesn't exist
            docs_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(docs_path, "w", encoding="utf-8") as f:
                f.write(update.content)

            logger.info(
                f"{'Created' if update.change_type == 'create' else 'Updated'} {update.file_path}"
            )

        # Generate metrics report
        self._generate_metrics_report()

        # Create documentation dashboard
        self._create_documentation_dashboard()

    def _generate_metrics_report(self) -> None:
        """Generate performance metrics report"""
        if not self.metrics["start_time"] or not self.metrics["end_time"]:
            return

        processing_time = self.metrics["end_time"] - self.metrics["start_time"]
        docs_path = self.docs_root / "metrics" / "performance.md"
        docs_path.parent.mkdir(parents=True, exist_ok=True)

        report = f"""# Метрики производительности документации

## Обзор

Автоматически сгенерированный отчет о работе системы обновления документации.

## Статистика выполнения

- **Время обработки:** {processing_time:.2f} секунд
- **Файлов проанализировано:** {self.metrics["files_analyzed"]}
- **Изменений найдено:** {self.metrics["changes_found"]}
- **Документов обновлено:** {self.metrics["updates_applied"]}
- **Ошибок:** {len(self.metrics["errors"])}

## Детали анализа

### По типам файлов:
- **Python файлы:** API эндпоинты, классы, функции, LLM взаимодействия
- **JavaScript/TypeScript:** React компоненты, API вызовы
- **SQL файлы:** Схемы базы данных
- **YAML файлы:** Конфигурации

### По типам изменений:
- **API endpoints:** Новые и измененные эндпоинты
- **Business logic:** Классы, методы, LLM интеграции
- **Frontend components:** React компоненты и API интеграции
- **Configuration:** Изменения настроек

## Ошибки и предупреждения

{chr(10).join(f"- {error}" for error in self.metrics["errors"]) if self.metrics["errors"] else "Ошибок не обнаружено"}

## Системная информация

- **Дата генерации:** {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Версия Python:** {sys.version.split()[0]}
- **Платформа:** {sys.platform}

---
*Этот отчет генерируется автоматически при каждом обновлении документации.*
"""

        with open(docs_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Performance metrics report generated: {docs_path}")

    def _create_documentation_dashboard(self) -> None:
        """Create a simple documentation dashboard"""
        dashboard_path = self.docs_root / "DASHBOARD.md"

        # Collect information about all documentation files
        docs_structure = self._analyze_docs_structure()

        dashboard = f"""# 📚 Documentation Dashboard - ReAIboot

## Обзор системы документации

Добро пожаловать в централизованный dashboard документации проекта ReAIboot!

## 📊 Метрики проекта

{self._get_project_metrics()}

## 📁 Структура документации

### Business Documentation
{docs_structure.get('business', 'В разработке')}

### Technical Documentation
{docs_structure.get('technical', 'В разработке')}

### User Guides
{docs_structure.get('user_guides', 'В разработке')}

### Templates
{docs_structure.get('templates', 'В разработке')}

## 🔍 Быстрый поиск

### По категориям:
- [API Documentation](./technical/api/overview.md) - Все API эндпоинты
- [Architecture](./technical/architecture/components.md) - Архитектура системы
- [Frontend](./technical/frontend/components.md) - React компоненты
- [LLM Guide](./LLM_README.md) - Руководство для ИИ

### По типам:
- 🔧 **Техническая документация** - API, архитектура, база данных
- 💼 **Бизнес документация** - требования, аудитория, конкуренты
- 👥 **Пользовательские гайды** - инструкции, примеры использования
- 🤖 **LLM документация** - специальное руководство для ИИ

## 🚀 Быстрые действия

### Для разработчиков:
1. **Обновить документацию:** `python .cursorrules/update_docs.py --all`
2. **Проверить изменения:** `python .cursorrules/update_docs.py --dry-run --files src/`
3. **Посмотреть метрики:** [Performance Metrics](./metrics/performance.md)

### Для LLM:
1. **Прочитать LLM_README.md** - полное понимание проекта
2. **Изучить API** - все доступные эндпоинты
3. **Посмотреть архитектуру** - компоненты и взаимодействия

## 📈 Статус документации

### ✅ Автоматически обновляемые разделы:
- API эндпоинты (FastAPI)
- Архитектурные компоненты
- LLM интеграции
- Frontend компоненты

### 🔄 Требующие ручного обновления:
- Бизнес-требования
- Пользовательские гайды
- Дизайн-документы

## 🔗 Полезные ссылки

- [GitHub Repository](https://github.com/MrUversky/ReAIboot-Telegram-Analytics)
- [API Swagger](http://localhost:8000/api/docs) (при запущенном сервере)
- [Performance Metrics](./metrics/performance.md)

---

## 💡 Советы по использованию

### Для быстрого старта:
1. Начните с [LLM_README.md](./LLM_README.md) если вы ИИ
2. Посмотрите [Architecture Overview](./technical/architecture/components.md)
3. Ознакомьтесь с [API Endpoints](./technical/api/overview.md)

### Для глубокого понимания:
1. Изучите [Business Documentation](./business/overview.md)
2. Прочитайте [User Guides](./user-guides/getting-started.md)
3. Посмотрите [Performance Metrics](./metrics/performance.md)

---

*Dashboard обновляется автоматически при изменениях в документации*
*Последнее обновление: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(dashboard)

        logger.info(f"Documentation dashboard created: {dashboard_path}")

    def _analyze_docs_structure(self) -> Dict[str, str]:
        """Analyze the structure of documentation"""
        structure = {}

        # Business docs
        business_files = list((self.docs_root / "business").glob("*.md"))
        if business_files:
            structure["business"] = "\n".join(
                f"- [{f.stem.title()}](./business/{f.name})" for f in business_files
            )

        # Technical docs
        technical_dirs = ["api", "architecture", "database", "deployment", "frontend"]
        technical_content = []
        for dir_name in technical_dirs:
            dir_path = self.docs_root / "technical" / dir_name
            if dir_path.exists():
                files = list(dir_path.glob("*.md"))
                if files:
                    technical_content.append(f"**{dir_name.title()}:**")
                    technical_content.extend(
                        f"  - [{f.stem.replace('_', ' ').title()}](./technical/{dir_name}/{f.name})"
                        for f in files
                    )

        if technical_content:
            structure["technical"] = "\n".join(technical_content)

        # User guides
        user_guide_files = list((self.docs_root / "user-guides").glob("*.md"))
        if user_guide_files:
            structure["user_guides"] = "\n".join(
                f"- [{f.stem.replace('-', ' ').title()}](./user-guides/{f.name})"
                for f in user_guide_files
            )

        # Templates
        template_files = list((self.docs_root / "templates").glob("*.md"))
        if template_files:
            structure["templates"] = "\n".join(
                f"- [{f.stem.replace('-', ' ').title()}](./templates/{f.name})"
                for f in template_files
            )

        return structure

    def _get_project_metrics(self) -> str:
        """Get basic project metrics"""
        total_docs = len(list(self.docs_root.glob("**/*.md")))
        api_endpoints = len(
            list((self.docs_root / "technical" / "api" / "endpoints").glob("*.md"))
        )
        components = len(
            list((self.docs_root / "technical" / "architecture").glob("*.md"))
        )

        return f"""
- **Всего документов:** {total_docs}
- **API эндпоинтов:** {api_endpoints}
- **Архитектурных компонентов:** {components}
- **Время последнего анализа:** {time.strftime('%H:%M:%S')}
- **Статус системы:** ✅ Активна
"""


def main():
    parser = argparse.ArgumentParser(
        description="Auto-update documentation based on code changes"
    )
    parser.add_argument("--files", nargs="*", help="Files to analyze")
    parser.add_argument("--all", action="store_true", help="Update all documentation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without applying",
    )
    parser.add_argument(
        "--force-ai",
        action="store_true",
        help="Force AI regeneration for all components (expensive)",
    )

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent.parent
    project_root = script_dir

    agent = DocumentationAgent(str(project_root), force_ai=args.force_ai)

    if args.all:
        # Analyze all Python files
        python_files = list(project_root.glob("src/**/*.py"))
        changed_files = [str(f.relative_to(project_root)) for f in python_files]
    elif args.files:
        changed_files = args.files
    else:
        # Try to get changed files from git
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                cwd=project_root,
            )
            changed_files = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
        except:
            logger.error("Could not get changed files from git")
            changed_files = []

    if not changed_files:
        logger.info("No files to analyze")
        return

    logger.info(f"Analyzing {len(changed_files)} files...")

    # Analyze changes
    changes = agent.analyze_changes(changed_files)
    logger.info(f"Found {len(changes)} relevant changes")

    # Generate updates
    updates = agent.generate_documentation_updates(changes)
    logger.info(f"Generated {len(updates)} documentation updates")

    if args.dry_run:
        for update in updates:
            print(f"Would {update.change_type}: {update.file_path}")
        return

    # Apply updates
    agent.apply_updates(updates)

    logger.info("Documentation update completed!")


if __name__ == "__main__":
    main()
