"""
Maintenance mode middleware - упрощённая версия.
"""

import logging
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)


def create_maintenance_middleware(app: FastAPI) -> None:
    """
    Регистрирует middleware для режима обслуживания.
    """

    @app.middleware("http")
    async def maintenance_mode_middleware(
        request: Request, call_next: Callable
    ) -> Response:
        # Пропускаем health check и auth endpoints всегда
        if request.url.path in [
            "/",
            "/health",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/telegram/login",
        ]:
            return await call_next(request)

        # Временно пропускаем все запросы (maintenance mode выключен)
        # В будущем здесь будет проверка из БД
        return await call_next(request)
