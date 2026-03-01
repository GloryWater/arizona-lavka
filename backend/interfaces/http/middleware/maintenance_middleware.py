"""
Maintenance mode middleware.
"""

import logging
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response

from config import get_settings

logger = logging.getLogger(__name__)


def create_maintenance_middleware(app: FastAPI) -> None:
    """
    Регистрирует middleware для режима обслуживания.

    Когда режим включён:
    - Блокирует все запросы кроме health check, auth и админ-панели
    - Администраторы могут продолжать работу
    - Возвращает 503 Service Unavailable для остальных
    """

    @app.middleware("http")
    async def maintenance_mode_middleware(
        request: Request,
        call_next: Callable
    ) -> Response:
        # Пропускаем health check и auth endpoints всегда
        if request.url.path in [
            "/", "/health", "/api/health", "/docs", "/redoc", "/openapi.json",
            "/api/auth/login", "/api/auth/register", "/api/auth/refresh",
            "/telegram/login",
        ]:
            return await call_next(request)

        # Проверяем режим обслуживания
        try:
            from services.maintenance_service import MaintenanceService
            is_maintenance = await MaintenanceService.is_maintenance_mode()

            if is_maintenance:
                # Проверяем является ли пользователь администратором
                auth_header = request.headers.get("Authorization")
                is_admin = False

                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    from services.auth_service import TokenManager

                    settings = get_settings()
                    payload = TokenManager.decode_token(
                        token,
                        settings.JWT_SECRET_KEY,
                        settings.JWT_ALGORITHM,
                    )

                    if payload and payload.get("role") == "admin":
                        is_admin = True

                # Администраторы могут работать в режиме обслуживания
                if is_admin:
                    return await call_next(request)

                # Для всех остальных - 503
                message = "Технические работы. Попробуйте позже."
                retry_after = 300  # 5 минут

                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "status": "error",
                        "code": "MAINTENANCE_MODE",
                        "detail": message,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception as e:
            # В случае ошибки проверки - пропускаем запрос (fail-open)
            logger.warning(f"Ошибка проверки maintenance mode: {e}")

        return await call_next(request)
