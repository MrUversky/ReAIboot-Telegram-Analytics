.PHONY: all run test lint format clean

# Виртуальное окружение
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Параметры запуска
DAYS := 7
TOP_OVERALL := 30
TOP_PER_CHANNEL := 5
LIMIT := 100

all: $(VENV) run

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Запуск приложения
run: $(VENV)
	$(PYTHON) -m src.main --days $(DAYS) --top-overall $(TOP_OVERALL) --top-per-channel $(TOP_PER_CHANNEL) --limit $(LIMIT)

# Запуск без LLM
run-no-llm: $(VENV)
	$(PYTHON) -m src.main --days $(DAYS) --top-overall $(TOP_OVERALL) --top-per-channel $(TOP_PER_CHANNEL) --limit $(LIMIT) --no-llm

# Запуск тестов
test: $(VENV)
	$(PYTHON) -m unittest discover -s tests

# Проверка синтаксиса
lint: $(VENV)
	$(VENV)/bin/pylint src tests || true
	$(VENV)/bin/flake8 src tests || true

# Форматирование кода
format: $(VENV)
	$(VENV)/bin/black src tests
	$(VENV)/bin/isort src tests

# Установка инструментов для разработки
dev-setup: $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pylint flake8 black isort

# Очистка
clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/app/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete

# Полная очистка (включая виртуальное окружение)
distclean: clean
	rm -rf $(VENV)

# Справка
help:
	@echo "Доступные команды:"
	@echo "  make run             - Запустить приложение с параметрами по умолчанию"
	@echo "  make run-no-llm      - Запустить приложение без использования LLM"
	@echo "  make test            - Запустить тесты"
	@echo "  make lint            - Проверить синтаксис"
	@echo "  make format          - Отформатировать код"
	@echo "  make clean           - Удалить временные файлы"
	@echo "  make distclean       - Удалить виртуальное окружение и временные файлы"
	@echo ""
	@echo "Параметры запуска (можно изменить):"
	@echo "  DAYS=$(DAYS)"
	@echo "  TOP_OVERALL=$(TOP_OVERALL)"
	@echo "  TOP_PER_CHANNEL=$(TOP_PER_CHANNEL)"
	@echo "  LIMIT=$(LIMIT)"
