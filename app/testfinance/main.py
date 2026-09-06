"""FastAPI-приложение (см. [[Архитектура сервиса]])."""

from fastapi import FastAPI

from testfinance.api.routes import health
from testfinance.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(health.router)
