from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trilingua"

    # Auth
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # AI Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    ai_provider: str = "auto"

    # Sentry
    sentry_dsn: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Environment
    environment: str = "development"

    model_config = {"env_file": str(Path(__file__).resolve().parent.parent / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
