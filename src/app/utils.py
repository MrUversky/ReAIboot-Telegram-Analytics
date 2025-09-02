"""
Вспомогательные функции для работы приложения.
"""

import re
import logging
import datetime
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Создает и настраивает логгер с заданным именем и уровнем."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

def extract_username_from_url(url: str) -> Optional[str]:
    """Извлекает имя пользователя/канала из URL Telegram."""
    
    # Для ссылок вида https://t.me/username
    if url.startswith('http'):
        parsed = urlparse(url)
        if parsed.netloc == 't.me' or parsed.netloc.endswith('.t.me'):
            path = parsed.path.strip('/')
            return path if path else None
    
    # Для ссылок вида @username
    elif url.startswith('@'):
        return url[1:]
    
    return None

def normalize_channel_input(channel_input: str) -> str:
    """Нормализует ввод канала для использования в API."""
    
    username = extract_username_from_url(channel_input)
    
    if username:
        return username
    
    # Если это не URL и не @username, возвращаем как есть
    return channel_input.strip()

def truncate_text(text: str, max_length: int = 500) -> str:
    """Обрезает текст до указанной длины."""
    
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def format_datetime(dt: datetime.datetime, timezone=None) -> str:
    """Форматирует дату и время в строку с учетом часового пояса."""
    
    if timezone:
        dt = dt.astimezone(timezone)
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def safe_get(obj: Any, *keys, default=None) -> Any:
    """Безопасно получает вложенное значение из объекта."""
    
    for key in keys:
        try:
            obj = obj[key] if isinstance(obj, dict) else getattr(obj, key)
        except (KeyError, AttributeError, TypeError):
            return default
    
    return obj

def clean_html(text: str) -> str:
    """Удаляет HTML-теги из текста."""
    
    if not text:
        return ""
    
    # Простая очистка от HTML-тегов
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()

def is_valid_json_response(response: Union[Dict, Any]) -> bool:
    """Проверяет, что ответ от LLM является допустимым JSON."""
    
    return isinstance(response, dict) and not isinstance(response, str)
