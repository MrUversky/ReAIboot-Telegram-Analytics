# 🤖 Documentation Agent - Правила автоматического обновления документации

## Обзор

Documentation Agent - это система на базе Cursor Rules, которая автоматически отслеживает изменения в коде и обновляет соответствующую документацию.

## Принципы работы

### 1. Автоматическое обнаружение изменений
- Мониторинг изменений в исходном коде
- Анализ типа изменений (новые эндпоинты, изменения API, бизнес-логика)
- Определение затронутых разделов документации

### 2. Генерация обновлений
- Создание или обновление API документации
- Обновление описаний функций и классов
- Генерация примеров использования

### 3. Валидация и проверка
- Проверка корректности обновлений
- Валидация синтаксиса
- Проверка на конфликты

## Структура правил

### Основные правила

#### 1. **API Endpoints Detection**
```
Триггер: Изменения в api_main.py или других файлах API
Действие: Обновить technical/api/endpoints/
```

#### 2. **Business Logic Changes**
```
Триггер: Изменения в основных модулях (llm/, supabase_client.py)
Действие: Обновить technical/architecture/ и user-guides/
```

#### 3. **Configuration Updates**
```
Триггер: Изменения в settings.py, requirements.txt
Действие: Обновить development/setup.md и technical/deployment/
```

#### 4. **Database Schema Changes**
```
Триггер: Изменения в SQL файлах, миграциях
Действие: Обновить technical/database/
```

## Промпты для генерации документации

### API Documentation Prompt

```
Ты - технический писатель, специализирующийся на API документации.

ЗАДАЧА: Создать или обновить документацию для API эндпоинта на основе анализа кода.

КОД ДЛЯ АНАЛИЗА:
{code_snippet}

ТЕКУЩАЯ ДОКУМЕНТАЦИЯ:
{current_docs}

ИНСТРУКЦИИ:
1. Проанализируй сигнатуру функции и параметры
2. Определи HTTP метод и путь
3. Опиши request/response форматы
4. Создай примеры использования
5. Добавь информацию об аутентификации и ошибках

ВЫВОД: Обновленная документация в формате Markdown
```

### Business Logic Documentation Prompt

```
Ты - технический писатель, объясняющий сложные концепции простым языком.

ЗАДАЧА: Описать функциональность модуля для технической документации.

МОДУЛЬ: {module_name}
ОПИСАНИЕ: {module_description}
ОСНОВНЫЕ ФУНКЦИИ: {functions_list}

ИНСТРУКЦИИ:
1. Объясни назначение модуля
2. Опиши основные функции и их взаимодействие
3. Приведи примеры использования
4. Укажи зависимости и требования

ВЫВОД: Раздел документации в формате Markdown
```

## Автоматические действия

### При изменении API

```python
# .cursorrules/api_changes.py
def on_api_change(file_path, changes):
    """Обработка изменений в API"""

    # Определить тип изменения
    change_type = detect_change_type(changes)

    if change_type == "new_endpoint":
        # Создать новую документацию эндпоинта
        docs = generate_endpoint_docs(changes)
        save_docs_to_file(docs, f"technical/api/endpoints/{endpoint_name}.md")

    elif change_type == "endpoint_modified":
        # Обновить существующую документацию
        current_docs = load_current_docs(endpoint_name)
        updated_docs = update_endpoint_docs(current_docs, changes)
        save_docs_to_file(updated_docs, f"technical/api/endpoints/{endpoint_name}.md")

    # Проверить на конфликты
    validate_documentation(updated_docs)
```

### При изменении бизнес-логики

```python
# .cursorrules/business_logic_changes.py
def on_business_logic_change(file_path, changes):
    """Обработка изменений в бизнес-логике"""

    # Анализ изменений
    affected_modules = analyze_dependencies(changes)

    for module in affected_modules:
        # Обновить документацию модуля
        docs = generate_module_docs(module, changes)
        update_architecture_docs(docs)

        # Обновить пользовательские гайды если нужно
        if requires_user_guide_update(module):
            update_user_guides(docs)
```

## Интеграция с Git

### Pre-commit hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: documentation-check
        name: Check documentation updates
        entry: python .cursorrules/check_docs.py
        language: system
        files: ^(src/|docs/)
        pass_filenames: false
```

### GitHub Actions

```yaml
# .github/workflows/docs-update.yml
name: Update Documentation

on:
  push:
    paths:
      - 'src/**'
      - '!docs/**'

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Update documentation
        run: python .cursorrules/update_docs.py
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/
          git commit -m "docs: automatic documentation update" || echo "No changes to commit"
```

## Качество и валидация

### Проверки документации

```python
# .cursorrules/validation.py
def validate_documentation(docs_content):
    """Валидация сгенерированной документации"""

    checks = [
        validate_markdown_syntax,
        validate_api_examples,
        validate_cross_references,
        validate_code_snippets
    ]

    for check in checks:
        result = check(docs_content)
        if not result['valid']:
            raise ValidationError(f"Documentation validation failed: {result['error']}")
```

### Метрики качества

- **Completeness**: Все ли API эндпоинты документированы
- **Accuracy**: Корректность примеров и описаний
- **Consistency**: Единообразие форматирования
- **Freshness**: Актуальность документации

## Мониторинг и аналитика

### Отслеживание изменений

```python
# .cursorrules/analytics.py
def track_documentation_changes():
    """Отслеживание изменений в документации"""

    metrics = {
        'files_updated': count_updated_files(),
        'api_endpoints_documented': count_api_endpoints(),
        'documentation_coverage': calculate_coverage(),
        'update_frequency': measure_update_frequency()
    }

    save_metrics(metrics)
    generate_report(metrics)
```

### Отчеты

```markdown
# Documentation Update Report

## Period: 2024-12-01 to 2024-12-31

### Summary
- **Files Updated**: 15
- **API Endpoints**: 8 new, 3 updated
- **Coverage**: 95%

### Details
- New endpoints documented: `/api/posts/bulk`, `/api/llm/batch`
- Updated: `/api/sandbox/test-pipeline` - added new parameters
- Issues found: 2 broken links fixed

### Recommendations
- Add more code examples for complex endpoints
- Update user guides for new features
```

## Ручное управление

### Принудительное обновление

```bash
# Обновить всю документацию
python .cursorrules/update_docs.py --all

# Обновить конкретный раздел
python .cursorrules/update_docs.py --section api/endpoints

# Обновить конкретный файл
python .cursorrules/update_docs.py --file technical/api/endpoints/posts.md
```

### Отключение автоматического обновления

```bash
# Для конкретного коммита
git commit -m "fix: bug fix" --no-verify

# Отключить для файла
echo "docs/technical/api/endpoints/debug.md" >> .docsignore
```

## Безопасность и контроль качества

### Валидация изменений

1. **Синтаксическая проверка** Markdown файлов
2. **Проверка ссылок** на корректность
3. **Валидация примеров** кода (syntax highlighting)
4. **Проверка согласованности** терминов и определений

### Рецензирование

- Автоматические обновления требуют approval
- Критические изменения проверяются вручную
- Сообщество может предлагать улучшения

---

*Обновлено: Декабрь 2024 | Версия: 1.0*
