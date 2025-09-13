# 🚀 Руководство по развертыванию ReAIboot

## 🎯 Быстрый запуск проекта

### 1. Запуск API сервера
```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск API сервера
python scripts/run_api.py

# Проверка работы
curl http://localhost:8001/health
```

### 2. Запуск UI демо
```bash
# Открыть в браузере
open demo_ui.html

# Или запустить локальный сервер
python -m http.server 3000
# Открыть: http://localhost:3000/demo_ui.html
```

---

## 🌐 Развертывание в веб

### Вариант 1: БЕСПЛАТНЫЙ (Vercel + Railway)

#### 1.1 Backend на Railway
```bash
# Установка Railway CLI
npm install -g @railway/cli

# Авторизация
railway login

# Создание проекта
railway init reai-boot-api

# Настройка переменных окружения
railway variables set OPENAI_API_KEY=your_key
railway variables set CLAUDE_API_KEY=your_key

# Деплой
railway up
```

**Стоимость:** $5/месяц (после free tier)
**URL:** `https://reai-boot-api.up.railway.app`

#### 1.2 Frontend на Vercel
```bash
# Установка Vercel CLI
npm install -g vercel

# Создание Next.js проекта
npx create-next-app@latest frontend --typescript --tailwind --app

# Деплой
cd frontend
vercel --prod

# Настройка API URL
# В .env.local: NEXT_PUBLIC_API_URL=https://your-railway-url
```

**Стоимость:** БЕСПЛАТНО (до 100GB traffic)
**URL:** `https://reai-boot.vercel.app`

### Вариант 2: БЮДЖЕТНЫЙ ($10-20/месяц)

#### DigitalOcean App Platform
```bash
# Создание приложения
doctl apps create --spec app-spec.yaml

# Файл app-spec.yaml
name: reai-boot
services:
- name: api
  source_dir: /
  github:
    repo: MrUversky/ReAIboot-Telegram-Analytics
    branch: main
  run_command: python scripts/run_api.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: ${OPENAI_API_KEY}
  - key: CLAUDE_API_KEY
    value: ${CLAUDE_API_KEY}
```

**Стоимость:** $12/месяц
**Особенности:** Автоматический scaling, backups

### Вариант 3: ПРОФЕССИОНАЛЬНЫЙ ($25-50/месяц)

#### AWS (EC2 + RDS)
```bash
# Создание EC2 инстанса
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t3.micro \
  --key-name your-key-pair

# Настройка RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier reai-boot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password your-password \
  --allocated-storage 20
```

**Стоимость:** $25-40/месяц
**Особенности:** Максимальная производительность, масштабируемость

---

## 📊 Мониторинг работоспособности

### 1. Health Checks
```python
# В main.py добавить endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "openai": check_openai_status(),
            "claude": check_claude_status(),
            "database": check_db_status()
        }
    }
```

### 2. Sentry для ошибок
```bash
# Установка
pip install sentry-sdk

# Настройка в main.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### 3. Метрики с Prometheus
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 4. UptimeRobot для мониторинга
- **URL для мониторинга:** `https://your-domain/health`
- **Интервал проверок:** 5 минут
- **Уведомления:** Email + SMS
- **Стоимость:** $5.50/месяц

---

## 🧪 Тесты функциональности

### 1. Unit тесты
```bash
# Запуск тестов
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ --cov=src --cov-report=html
```

### 2. API тесты с Postman/Newman
```json
{
  "info": {
    "name": "ReAIboot API Tests"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test(\"Status code is 200\", function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "",
              "pm.test(\"Response has status healthy\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData.status).to.eql(\"healthy\");",
              "});"
            ]
          }
        }
      ]
    }
  ]
}
```

### 3. E2E тесты с Playwright
```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('Dashboard loads correctly', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Проверяем заголовок
  await expect(page.locator('h1')).toContainText('ReAIboot Dashboard');

  // Проверяем метрики
  await expect(page.locator('#total-posts')).toBeVisible();

  // Проверяем вкладки
  await page.click('#tab-posts');
  await expect(page.locator('#posts-container')).toBeVisible();
});
```

### 4. Load testing с Artillery
```yaml
# artillery.yml
config:
  target: 'http://localhost:8001'
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 120
      arrivalRate: 10
      name: "Load testing"

scenarios:
  - name: "Health check"
    requests:
      - get:
          url: "/health"

  - name: "API load test"
    requests:
      - post:
          url: "/api/llm/process"
          json:
            posts: [
              {
                "message_id": "test_1",
                "channel_title": "Test Channel",
                "text": "Test post content",
                "views": 100,
                "reactions": 10,
                "replies": 5,
                "forwards": 2,
                "score": 7.5
              }
            ]
```

---

## 🔧 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Railway
      run: |
        curl -X POST \
          -H "Authorization: Bearer ${{ secrets.RAILWAY_TOKEN }}" \
          -H "Content-Type: application/json" \
          https://backboard.railway.app/project/your-project-id/trigger
```

---

## 📈 Оптимизация стоимости

### 1. Мониторинг расходов
```python
# Отслеживание стоимости API вызовов
COST_TRACKER = {
    'openai': {'calls': 0, 'cost': 0},
    'claude': {'calls': 0, 'cost': 0}
}

def track_cost(provider: str, tokens: int, model: str):
    if provider == 'openai':
        if 'gpt-4' in model:
            cost = tokens * 0.03 / 1000  # $0.03 per 1K tokens
        else:
            cost = tokens * 0.0015 / 1000  # $0.0015 per 1K tokens
    elif provider == 'claude':
        cost = tokens * 0.003 / 1000  # $0.003 per 1K tokens

    COST_TRACKER[provider]['calls'] += 1
    COST_TRACKER[provider]['cost'] += cost
```

### 2. Кеширование ответов
```python
from cachetools import TTLCache
import hashlib

cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL

def get_cache_key(text: str, prompt: str) -> str:
    content = f"{text}:{prompt}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_response(text: str, prompt: str):
    key = get_cache_key(text, prompt)
    return cache.get(key)

def set_cached_response(text: str, prompt: str, response: str):
    key = get_cache_key(text, prompt)
    cache[key] = response
```

### 3. Оптимизация промптов
```python
# Сокращение промптов для снижения токенов
def optimize_prompt(prompt: str) -> str:
    # Удаление лишних пробелов
    prompt = ' '.join(prompt.split())

    # Замена повторяющихся инструкций
    prompt = prompt.replace('Please', '').replace('please', '')

    # Ограничение длины
    if len(prompt) > 2000:
        prompt = prompt[:2000] + "..."

    return prompt
```

---

## 🚨 План действий

### Этап 1: Базовое развертывание (1 неделя)
- [ ] Настроить Railway для backend
- [ ] Создать Vercel проект для frontend
- [ ] Подключить домен
- [ ] Настроить переменные окружения

### Этап 2: Мониторинг (3 дня)
- [ ] Добавить Sentry
- [ ] Настроить health checks
- [ ] Создать дашборд мониторинга

### Этап 3: Тестирование (1 неделя)
- [ ] Написать unit тесты
- [ ] Создать API тесты
- [ ] Настроить E2E тесты
- [ ] Load testing

### Этап 4: Оптимизация (1 неделя)
- [ ] Кеширование ответов
- [ ] Оптимизация промптов
- [ ] Мониторинг стоимости
- [ ] Auto-scaling

**Рекомендация:** Начать с **Railway + Vercel** (бесплатно для начала, $10-15/месяц при росте)
