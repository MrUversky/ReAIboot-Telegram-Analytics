#!/usr/bin/env python3
"""
Generate Table of Contents for documentation

Automatically generates and updates table of contents in docs/README.md
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TocGenerator:
    """Generates table of contents for documentation"""

    def __init__(self, docs_root: str):
        self.docs_root = Path(docs_root)

    def generate_toc(self) -> str:
        """Generate complete table of contents"""
        toc_lines = []

        # Define the structure
        structure = {
            "business": {
                "title": "📊 Бизнес-информация",
                "description": "аудитория, конкуренты, стратегия",
            },
            "technical": {
                "title": "🏗️ Техническая документация",
                "description": "архитектура, API, деплой",
                "subsections": {
                    "architecture": "Архитектура системы",
                    "api": "API документация",
                    "database": "База данных",
                    "deployment": "Инфраструктура",
                },
            },
            "user-guides": {
                "title": "👥 Руководства пользователей",
                "description": "гайды по использованию",
            },
            "development": {
                "title": "💻 Для разработчиков",
                "description": "настройка, разработка, тестирование",
            },
        }

        for section, config in structure.items():
            toc_lines.append(
                f"- **[{config['title']}]({section}/)** - {config['description']}"
            )

            section_path = self.docs_root / section
            if section_path.exists():
                files = self._get_section_files(
                    section_path, config.get("subsections", {})
                )
                for file_link, file_title in files:
                    toc_lines.append(f"  - {file_link}")

        return "\n".join(toc_lines)

    def _get_section_files(
        self, section_path: Path, subsections: Dict[str, str] = None
    ) -> List[Tuple[str, str]]:
        """Get files in a section, organizing by subsections if provided"""
        files = []

        if subsections:
            for sub_dir, sub_title in subsections.items():
                sub_path = section_path / sub_dir
                if sub_path.exists():
                    sub_files = list(sub_path.glob("*.md"))
                    for file_path in sorted(sub_files):
                        if file_path.name == "README.md":
                            continue
                        title = self._extract_title(file_path)
                        rel_path = file_path.relative_to(self.docs_root)
                        files.append((f"[{title}]({rel_path})", title))
        else:
            # Simple listing for sections without subsections
            md_files = list(section_path.glob("*.md"))
            for file_path in sorted(md_files):
                if file_path.name == "README.md":
                    continue
                title = self._extract_title(file_path)
                rel_path = file_path.relative_to(self.docs_root)
                files.append((f"[{title}]({rel_path})", title))

        return files

    def _extract_title(self, file_path: Path) -> str:
        """Extract title from markdown file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for the first heading
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

            # Fallback to filename
            return file_path.stem.replace("-", " ").replace("_", " ").title()

        except Exception:
            return file_path.stem

    def update_docs_readme(self):
        """Update the docs/README.md with generated TOC"""
        docs_readme = self.docs_root / "README.md"

        if not docs_readme.exists():
            print(f"docs/README.md not found at {docs_readme}")
            return

        with open(docs_readme, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the TOC section
        toc_pattern = r"(## 🗂️ Структура документации\n\n)(.*?)(\n\n## 🔍 Быстрый поиск)"
        toc_match = re.search(toc_pattern, content, re.DOTALL)

        if toc_match:
            new_toc = self.generate_toc()
            updated_content = content.replace(toc_match.group(2), new_toc)

            with open(docs_readme, "w", encoding="utf-8") as f:
                f.write(updated_content)

            print("✅ Updated docs/README.md with new TOC")
        else:
            print("⚠️  TOC section not found in docs/README.md")


def main():
    # Determine docs root
    script_dir = Path(__file__).parent.parent / "docs"
    docs_root = script_dir

    generator = TocGenerator(str(docs_root))
    generator.update_docs_readme()


if __name__ == "__main__":
    main()
