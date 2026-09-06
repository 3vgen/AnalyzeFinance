"""FastAPI-приложение (см. [[Архитектура сервиса]])."""

from fastapi import FastAPI

from testfinance.api.routes import accounts, auth, health
from testfinance.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(accounts.router)
