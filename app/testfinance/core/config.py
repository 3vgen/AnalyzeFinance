"""Конфигурация приложения из переменных окружения / .env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_DATABASE_URL = "postgresql+asyncpg://testfinance@localhost:5432/testfinance"


class Settings(BaseSettings):
    """Настройки сервиса (см. [[Технологический стек]])."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "testfinance"
    debug: bool = False

    database_url: str = Field(default=_DEFAULT_DATABASE_URL)

    # JWT (ADR-007)
    jwt_secret: str = "dev-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
