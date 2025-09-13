#!/usr/bin/env python3
"""
Documentation Pre-commit Check Script

Validates documentation before commits and suggests updates.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DocumentationValidator:
    """Validates documentation quality and consistency"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_root = self.project_root / "docs"
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting documentation validation...")

        self._validate_file_structure()
        self._validate_api_documentation()
        self._validate_cross_references()
        self._validate_markdown_syntax()
        self._validate_code_examples()

        # Report results
        if self.errors:
            logger.error(f"Found {len(self.errors)} errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False

        if self.warnings:
            logger.warning(f"Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        logger.info("Documentation validation passed!")
        return True

    def _validate_file_structure(self):
        """Validate documentation file structure"""
        required_files = [
            "README.md",
            "technical/api/overview.md",
            "technical/api/endpoints/posts.md",
            "technical/api/endpoints/llm.md",
            "technical/api/endpoints/sandbox.md",
            "business/overview.md",
            "business/audience.md",
            "user-guides/getting-started.md",
        ]

        for file_path in required_files:
            full_path = self.docs_root / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required documentation file: {file_path}")

    def _validate_api_documentation(self):
        """Validate API documentation completeness"""
        api_files = list(
            (self.docs_root / "technical" / "api" / "endpoints").glob("*.md")
        )

        for api_file in api_files:
            self._validate_single_api_file(api_file)

    def _validate_single_api_file(self, file_path: Path):
        """Validate single API documentation file"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for required sections
        required_patterns = [
            r"## .+\n\n\*\*Эндпоинт:\*\*",
            r"\*\*Аутентификация:\*\*",
            r"### Описание",
            r"### Пример запроса",
            r"### Пример ответа",
        ]

        for pattern in required_patterns:
            if not re.search(pattern, content, re.MULTILINE):
                self.warnings.append(
                    f"Missing required section in {file_path.name}: {pattern}"
                )

    def _validate_cross_references(self):
        """Validate cross-references between documents"""
        # This would check for broken links between docs
        pass

    def _validate_markdown_syntax(self):
        """Validate Markdown syntax"""
        md_files = list(self.docs_root.glob("**/*.md"))

        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for common Markdown issues
            issues = []

            # Unclosed code blocks
            code_blocks = re.findall(r"```", content)
            if len(code_blocks) % 2 != 0:
                issues.append("Unclosed code block")

            # Broken links
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
            for link_text, link_url in links:
                if not link_url.startswith(("http", "/", "#")):
                    # Check if relative link exists
                    link_path = (md_file.parent / link_url).resolve()
                    if not link_path.exists():
                        issues.append(f"Broken relative link: {link_url}")

            if issues:
                self.warnings.append(f"{md_file.name}: {', '.join(issues)}")

    def _validate_code_examples(self):
        """Validate code examples in documentation"""
        md_files = list(self.docs_root.glob("**/*.md"))

        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find code blocks
            code_blocks = re.findall(r"```(\w+)?\n(.*?)\n```", content, re.DOTALL)

            for lang, code in code_blocks:
                if lang == "json":
                    self._validate_json_code(code, md_file.name)
                elif lang == "python":
                    self._validate_python_code(code, md_file.name)
                elif lang == "bash":
                    self._validate_bash_code(code, md_file.name)

    def _validate_json_code(self, code: str, file_name: str):
        """Validate JSON code blocks"""
        try:
            json.loads(code.strip())
        except json.JSONDecodeError as e:
            self.warnings.append(f"{file_name}: Invalid JSON in code block: {e}")

    def _validate_python_code(self, code: str, file_name: str):
        """Validate Python code blocks"""
        # Basic syntax check
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            self.warnings.append(f"{file_name}: Invalid Python syntax: {e}")

    def _validate_bash_code(self, code: str, file_name: str):
        """Validate Bash code blocks"""
        # Check for common bash issues
        lines = code.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("curl") and " -d " in line:
                # Check if data is properly quoted
                if not re.search(r'-d\s+[\'"\{]', line):
                    self.warnings.append(
                        f"{file_name}: Unquoted curl data in: {line[:50]}..."
                    )


def main():
    # Determine project root
    script_dir = Path(__file__).parent.parent
    project_root = script_dir

    validator = DocumentationValidator(str(project_root))

    if validator.validate_all():
        logger.info("✅ Documentation validation passed!")
        sys.exit(0)
    else:
        logger.error("❌ Documentation validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
