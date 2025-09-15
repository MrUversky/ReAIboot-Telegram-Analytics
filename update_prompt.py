#!/usr/bin/env python3

import os
from src.app.supabase_client import SupabaseClient

os.environ['SUPABASE_URL'] = 'https://oxsvtjtgtdaqoslcxdna.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGFxb3NsY3hkbmEiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzI2NDU4OTcyLCJleHAiOjIwNDIwMjQ5NzJ9.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGFxb3NsY3hkbmEiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzI2NDU4OTcyLCJleHAiOjIwNDIwMjQ5NzJ9'

client = SupabaseClient()

# Новый улучшенный промпт
new_user_prompt = '''Проанализируй следующие {{posts_count}} виральных постов и дай КОНКРЕТНЫЕ РЕКОМЕНДАЦИИ для создания контента, который будет вирусным в Telegram.

🎯 КЛЮЧЕВЫЕ ЗАДАЧИ АНАЛИЗА:

1. **ТОП ТЕМ И ТРЕНДОВ** - Какие темы встречаются чаще всего и почему они работают
2. **ВИРАЛЬНЫЕ ХУКИ** - Какие заголовки и первые предложения цепляют внимание
3. **ФОРМАТЫ КОНТЕНТА** - Какие форматы постов работают лучше всего
4. **ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ** - Какие эмоции вызывают вовлеченность
5. **ГОРЯЧИЕ ТЕМЫ** - Топ-5 тем, которые повторяются в нескольких постах

📊 СТРУКТУРА АНАЛИЗА:

**🔥 ГОРЯЧИЕ ТЕМЫ (ТОП-5):**
• Тема 1: сколько постов, почему популярна
• Тема 2: сколько постов, почему популярна
• ...

**🎯 РАБОТАЮЩИЕ ХУКИ (КОНКРЕТНЫЕ ПРИМЕРЫ):**
• "Хук 1" - почему работает + пример использования
• "Хук 2" - почему работает + пример использования
• ...

**📝 ФОРМАТЫ ПОСТОВ:**
• Формат 1: описание + пример структуры
• Формат 2: описание + пример структуры
• ...

**💡 КОНКРЕТНЫЕ ИДЕИ ДЛЯ КОНТЕНТА:**
• Идея 1: полное описание поста + заголовок + структура
• Идея 2: полное описание поста + заголовок + структура
• ...

**🎨 РЕКОМЕНДАЦИИ ПО ОФОРМЛЕНИЮ:**
• Как использовать эмодзи
• Как структурировать текст
• Как добавлять призывы к действию

ПОСТЫ ДЛЯ АНАЛИЗА:
{{posts_text}}

⚠️ ВАЖНО: Дай МАКСИМАЛЬНО КОНКРЕТНЫЕ рекомендации. После прочтения анализа я должен суметь сразу создать 3-5 постов для своего канала.'''

result = client.client.table('llm_prompts').update({'user_prompt': new_user_prompt}).eq('name', 'viral_trends_analysis').execute()
print('Prompt updated successfully')
print(f"New prompt length: {len(new_user_prompt)}")
