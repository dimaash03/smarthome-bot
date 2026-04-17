from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ANTHROPIC_API_KEY: str
    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_ignore_empty = True  # ігнорує порожні системні env vars, бере з .env


settings = Settings()
