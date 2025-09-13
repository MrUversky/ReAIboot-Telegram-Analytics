# 🤝 Вклад в разработку ReAIboot

## Для разработчиков

Этот документ описывает процесс внесения вклада в проект ReAIboot с учетом автоматической системы документации.

## 📋 Перед началом работы

### 1. Ознакомьтесь с системой
- **LLM_README.md** - полное руководство по проекту для ИИ
- **DASHBOARD.md** - навигация по документации
- **metrics/performance.md** - метрики производительности

### 2. Настройте окружение
```bash
# Клонируйте репозиторий
git clone https://github.com/MrUversky/ReAIboot-Telegram-Analytics.git
cd ReAIboot-Telegram-Analytics

# Установите зависимости
pip install -r requirements.txt
npm install

# Настройте переменные окружения
cp docker_env_example.txt .env
# Отредактируйте .env файл
```

## 🚀 Процесс разработки

### Добавление нового компонента

#### 1. Напишите код с документацией
```python
class NewProcessor:
    """Краткое описание компонента"""

    def __init__(self):
        """Инициализация компонента"""
        pass

    def process(self, data: Dict) -> Dict:
        """Обработка данных

        Args:
            data: Входные данные

        Returns:
            Обработанные данные
        """
        return data
```

#### 2. Автоматическое документирование
```bash
# Система автоматически обнаружит новый компонент
# и сгенерирует AI-описание при коммите
git add .
git commit -m "Add NewProcessor component"
```

#### 3. Проверка результатов
```bash
# Проверьте обновленную документацию
cat docs/technical/architecture/components.md | grep -A 10 "NewProcessor"
```

### Изменение существующего компонента

#### 1. Внесите изменения
```python
def existing_method(self, data: Dict) -> Dict:
    """Обновленное описание метода"""
    # Измененная логика
    return processed_data
```

#### 2. Документация обновится автоматически
- Pre-commit hook запустит анализ
- Документация обновится если найдены изменения

## 🤖 Работа с AI документацией

### Когда AI генерирует описания

#### ✅ **Автоматически:**
- При обнаружении новых классов/функций
- При добавлении новых API эндпоинтов
- При первом коммите нового компонента

#### ❌ **Не генерирует:**
- Для уже документированных компонентов
- При изменениях в существующих методах (без новых компонентов)
- При чисто cosmetic изменениях

### Принудительная генерация

```bash
# Перегенерировать AI описания для всех компонентов (дорого!)
python3 .cursorrules/update_docs.py --force-ai --all

# Только для конкретных файлов
python3 .cursorrules/update_docs.py --force-ai --files src/app/new_component.py
```

### Оптимизация расходов

| Действие | Стоимость | Когда использовать |
|----------|-----------|-------------------|
| `--all` | Низкая | Ежедневно, для новых компонентов |
| `--force-ai --all` | Высокая | Раз в месяц, при глобальных изменениях |
| `--files` | Средняя | При работе над конкретным компонентом |

## 📝 Ручное обновление документации

### Для бизнес-документации
```bash
# Обновите файлы в docs/business/
vim docs/business/overview.md
vim docs/business/audience.md
```

### Для пользовательских гайдов
```bash
# Обновите файлы в docs/user-guides/
vim docs/user-guides/admin-guide.md
```

### Для технической документации
- Техническая документация обновляется автоматически
- Ручное вмешательство только при необходимости

## 🔍 Отладка системы документации

### Просмотр изменений
```bash
# Посмотреть что будет обновлено без применения
python3 .cursorrules/update_docs.py --dry-run --files src/app/component.py

# Посмотреть логи генерации AI
python3 .cursorrules/update_docs.py --files src/app/component.py 2>&1
```

### Проверка метрик
```bash
# Посмотреть метрики производительности
cat docs/metrics/performance.md

# Проверить статус системы
cat docs/monitoring/system-health.md
```

### Ручной запуск отдельных компонентов
```bash
# Только анализ (без генерации документации)
python3 -c "
from .cursorrules.update_docs import DocumentationAgent
agent = DocumentationAgent('.')
changes = agent.analyze_changes(['src/app/orchestrator.py'])
print(f'Found {len(changes)} changes')
"

# Только генерация (с уже известными изменениями)
python3 .cursorrules/update_docs.py --dry-run --all
```

## 🐛 Устранение неполадок

### AI генерация не работает
```bash
# Проверьте API ключ
echo $OPENAI_API_KEY

# Проверьте подключение
python3 -c "import openai; print('OpenAI доступен')"
```

### Документация не обновляется
```bash
# Проверьте pre-commit hooks
cat .pre-commit-config.yaml

# Ручной запуск
python3 .cursorrules/update_docs.py --all
```

### Неправильные описания компонентов
```bash
# Перегенерируйте конкретный компонент
python3 .cursorrules/update_docs.py --force-ai --files src/app/component.py

# Проверьте качество извлечения контекста
python3 -c "
from .cursorrules.update_docs import DocumentationAgent
agent = DocumentationAgent('.')
context = agent._extract_component_context('src/app/component.py', 'ComponentName', 'class')
print('Extracted context:')
print(context)
"
```

## 📊 Мониторинг вклада

### Метрики проекта
- **Документация:** автоматический охват компонентов
- **Качество кода:** линтинг, тесты, покрытие
- **Производительность:** время выполнения, использование ресурсов

### Статус документации
```bash
# Посмотреть dashboard
cat docs/DASHBOARD.md

# Проверить покрытие
grep -r "Требуется описание" docs/ | wc -l
```

## 🎯 Лучшие практики

### ✅ Делайте:
- Пишите docstring'и для всех публичных методов
- Используйте типизацию в сигнатурах функций
- Тестируйте изменения перед коммитом
- Читайте автоматически сгенерированную документацию

### ❌ Не делайте:
- Не запускайте `--force-ai` без необходимости
- Не редактируйте автоматически генерируемые разделы вручную
- Не игнорируйте предупреждения pre-commit hooks

## 📞 Поддержка

- **Документация:** `docs/README.md`
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

*Этот документ является частью автоматической системы документации ReAIboot*
