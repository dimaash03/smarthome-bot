from pathlib import Path
from dotenv import dotenv_values
from pydantic_settings import BaseSettings

# Шлях до .env відносно цього файлу (app/config.py → корінь проекту)
_BASE_DIR = Path(__file__).parent.parent
_env_file = _BASE_DIR / ".env"

# Читаємо .env напряму з файлу — системні env vars повністю ігноруються
_env_values = dotenv_values(_env_file)


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ANTHROPIC_API_KEY: str
    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"

    class Config:
        env_file_encoding = "utf-8"


# init-значення мають найвищий пріоритет у pydantic-settings
settings = Settings(**_env_values)
