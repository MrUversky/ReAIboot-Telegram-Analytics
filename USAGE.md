## Краткая инструкция по использованию

1. **Установка зависимостей:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Настройка:**
   - Скопируйте `.env.example` в `.env`
   - Заполните `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` (получите на https://my.telegram.org)
   - Опционально добавьте `OPENAI_API_KEY` для генерации сценариев

3. **Запуск:**
   ```bash
   # Без LLM (только анализ)
   python -m src.main --days 7 --no-llm
   
   # С LLM (анализ + сценарии)
   python -m src.main --days 7
   
   # Настройка параметров
   python -m src.main --days 3 --limit 100 --top-overall 20
   ```

4. **Результаты:**
   - `out/all_messages.csv` - все сообщения с метриками
   - `out/top_overall.csv` - лучшие сообщения по общему рейтингу
   - `out/top_by_channel.csv` - лучшие сообщения по каналам
   - `out/scenarios.md` - сценарии для контента (если включен LLM)

5. **Тестирование:**
   ```bash
   python -m unittest discover -s tests
   ```
