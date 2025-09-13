#!/usr/bin/env python3
"""
Documentation Auto-Update Script

Automatically updates documentation based on code changes.
This script analyzes code changes and generates/updates corresponding documentation.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_root = self.project_root / "docs"
        self.api_docs_root = self.docs_root / "technical" / "api" / "endpoints"

    def analyze_changes(self, changed_files: List[str]) -> List[CodeChange]:
        """Analyze changed files and extract relevant changes"""
        changes = []

        for file_path in changed_files:
            full_path = self.project_root / file_path

            if not full_path.exists():
                continue

            # Analyze file based on type
            if file_path.endswith('.py'):
                file_changes = self._analyze_python_file(file_path, full_path)
                changes.extend(file_changes)
            elif file_path.endswith('.sql'):
                file_changes = self._analyze_sql_file(file_path, full_path)
                changes.extend(file_changes)

        return changes

    def _analyze_python_file(self, file_path: str, full_path: Path) -> List[CodeChange]:
        """Analyze Python file for API endpoints and functions"""
        changes = []

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find FastAPI endpoints
        endpoint_pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*r?[\'"]([^\'"]+)[\'"]\s*.*?\)\s*async def\s+(\w+)'
        matches = re.finditer(endpoint_pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            method, path, func_name = match.groups()
            line_number = content[:match.start()].count('\n') + 1

            # Extract function signature and docstring
            func_start = match.end()
            func_end_pattern = r'(?=@app\.|\nclass|\ndef|\n@|$)'
            func_end_match = re.search(func_end_pattern, content[func_start:], re.MULTILINE)

            if func_end_match:
                func_content = content[func_start:func_start + func_end_match.start()]
            else:
                func_content = content[func_start:]

            changes.append(CodeChange(
                file_path=file_path,
                change_type='api_endpoint',
                content=f"Method: {method.upper()}\nPath: {path}\nFunction: {func_name}\nContent: {func_content[:500]}...",
                line_number=line_number
            ))

        return changes

    def _analyze_sql_file(self, file_path: str, full_path: Path) -> List[CodeChange]:
        """Analyze SQL file for schema changes"""
        changes = []

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find table creation/alteration
        table_pattern = r'(CREATE TABLE|ALTER TABLE|DROP TABLE)\s+(\w+)'
        matches = re.finditer(table_pattern, content, re.IGNORECASE)

        for match in matches:
            operation, table_name = match.groups()
            line_number = content[:match.start()].count('\n') + 1

            changes.append(CodeChange(
                file_path=file_path,
                change_type='database_schema',
                content=f"Operation: {operation}\nTable: {table_name}",
                line_number=line_number
            ))

        return changes

    def generate_documentation_updates(self, changes: List[CodeChange]) -> List[DocumentationUpdate]:
        """Generate documentation updates based on code changes"""
        updates = []

        for change in changes:
            if change.change_type == 'api_endpoint':
                update = self._generate_api_docs(change)
                if update:
                    updates.append(update)
            elif change.change_type == 'database_schema':
                update = self._generate_db_docs(change)
                if update:
                    updates.append(update)

        return updates

    def _generate_api_docs(self, change: CodeChange) -> Optional[DocumentationUpdate]:
        """Generate API documentation for endpoint"""
        lines = change.content.split('\n')
        method = None
        path = None
        func_name = None

        for line in lines:
            if line.startswith('Method: '):
                method = line.replace('Method: ', '')
            elif line.startswith('Path: '):
                path = line.replace('Path: ', '')
            elif line.startswith('Function: '):
                func_name = line.replace('Function: ', '')

        if not all([method, path, func_name]):
            return None

        # Determine which API section this belongs to
        if '/posts' in path:
            section = 'posts'
        elif '/llm' in path:
            section = 'llm'
        elif '/sandbox' in path:
            section = 'sandbox'
        elif '/admin' in path or 'admin' in path:
            section = 'admin'
        else:
            section = 'general'

        docs_path = self.api_docs_root / f"{section}.md"

        # Check if docs file exists
        if docs_path.exists():
            # Update existing file
            with open(docs_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Check if endpoint already documented
            if f"**Эндпоинт:** `{method} {path}`" in current_content:
                logger.info(f"Endpoint {method} {path} already documented")
                return None

            # Add new endpoint documentation
            new_content = self._generate_endpoint_section(method, path, func_name, change.content)
            updated_content = current_content + "\n\n" + new_content

            return DocumentationUpdate(
                file_path=str(docs_path),
                content=updated_content,
                change_type='update'
            )
        else:
            # Create new file
            content = f"# API {section.title()}\n\n## Обзор\n\nЭндпоинты для работы с {section}.\n\n---\n\n"
            content += self._generate_endpoint_section(method, path, func_name, change.content)

            return DocumentationUpdate(
                file_path=str(docs_path),
                content=content,
                change_type='create'
            )

    def _generate_endpoint_section(self, method: str, path: str, func_name: str, details: str) -> str:
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

    def apply_updates(self, updates: List[DocumentationUpdate]) -> None:
        """Apply documentation updates to files"""
        for update in updates:
            docs_path = Path(update.file_path)

            # Create directory if it doesn't exist
            docs_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(docs_path, 'w', encoding='utf-8') as f:
                f.write(update.content)

            logger.info(f"{'Created' if update.change_type == 'create' else 'Updated'} {update.file_path}")

def main():
    parser = argparse.ArgumentParser(description='Auto-update documentation based on code changes')
    parser.add_argument('--files', nargs='*', help='Files to analyze')
    parser.add_argument('--all', action='store_true', help='Update all documentation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without applying')

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent.parent
    project_root = script_dir

    agent = DocumentationAgent(str(project_root))

    if args.all:
        # Analyze all Python files
        python_files = list(project_root.glob('src/**/*.py'))
        changed_files = [str(f.relative_to(project_root)) for f in python_files]
    elif args.files:
        changed_files = args.files
    else:
        # Try to get changed files from git
        import subprocess
        try:
            result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'],
                                  capture_output=True, text=True, cwd=project_root)
            changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
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

if __name__ == '__main__':
    main()
