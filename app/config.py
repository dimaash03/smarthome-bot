import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# override=True: значення з .env завжди перебивають системні env vars
load_dotenv(override=True)


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ANTHROPIC_API_KEY: str
    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
