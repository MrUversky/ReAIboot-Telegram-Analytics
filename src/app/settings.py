"""
Модуль для загрузки и управления настройками приложения.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import pytz

# Загрузка .env файла
load_dotenv()

class Settings:
    """Класс для управления всеми настройками приложения."""
    
    def __init__(self):
        # Telegram настройки
        self.telegram_api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.telegram_api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.telegram_session = os.getenv("TELEGRAM_SESSION", "telegram_session")
        
        # OpenAI настройки
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

        # Claude настройки
        self.anthropic_api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        # Supabase настройки
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        # Настройки приложения
        self.timezone = os.getenv("TZ", "Asia/Tbilisi")
        
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.out_dir = self.base_dir / "out"
        
        # Создаем директорию для выходных файлов, если она не существует
        os.makedirs(self.out_dir, exist_ok=True)
    
    @property
    def tz(self):
        """Возвращает объект timezone."""
        return pytz.timezone(self.timezone)
    
    def load_channels(self, file_path: Optional[str] = None) -> List[str]:
        """Загружает список каналов из файла."""
        
        if not file_path:
            file_path = self.base_dir / "channels.txt"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл со списком каналов не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            channels = [line.strip() for line in f if line.strip()]
        
        return channels
    
    def load_content_plan(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает план контента из YAML файла."""
        
        if not file_path:
            file_path = self.base_dir / "content_plan.yaml"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл с планом контента не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content_plan = yaml.safe_load(f)
        
        return content_plan
    
    def load_score_weights(self, file_path: Optional[str] = None) -> Dict[str, float]:
        """Загружает веса для расчета метрик из YAML файла."""
        
        if not file_path:
            file_path = self.base_dir / "score.yaml"
        else:
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл с весами метрик не найден: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            score_config = yaml.safe_load(f)
        
        return score_config.get("weights", {})


# Создаем глобальный экземпляр настроек
settings = Settings()
