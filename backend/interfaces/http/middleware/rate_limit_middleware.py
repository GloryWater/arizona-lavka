"""
Rate limiting middleware - упрощённая версия.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response

from config import get_settings

logger = logging.getLogger(__name__)


def create_rate_limit_middleware(app: FastAPI) -> None:
    """
    Регистрирует middleware для rate limiting.
    """

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
        from infrastructure.persistence.rate_limiter import (
            InMemoryRateLimiter,
            get_rate_limiter,
        )

        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"

        # Пропускаем rate limit для health check, docs endpoints
        if request.url.path in [
            "/",
            "/health",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]:
            return await call_next(request)

        # Whitelist для нагрузочного тестирования
        load_testing_ips = getattr(settings, "LOAD_TESTING_IPS", "")
        if load_testing_ips:
            testing_ips_list = [ip.strip() for ip in load_testing_ips.split(",")]
            if client_ip in testing_ips_list:
                return await call_next(request)

        # Проверка rate limiter
        rate_limiter = await get_rate_limiter()
        if rate_limiter is None:
            logger.warning("Rate limiter не инициализирован, пропускаем проверку")
            return await call_next(request)

        try:
            # Специальная обработка для /api/auth/refresh
            if request.url.path == "/api/auth/refresh":
                refresh_limiter = InMemoryRateLimiter(limit=30, window_seconds=60)
                result = await refresh_limiter.check_rate_limit(f"refresh:{client_ip}")

                if not result.allowed:
                    headers = {
                        "Retry-After": str(int(result.retry_after or 60)),
                        "X-RateLimit-Limit": "30",
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + result.reset_after)),
                    }
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Слишком много запросов на обновление токена. Попробуйте через {int(result.retry_after or 60)} секунд.",
                        headers=headers,
                    )
            else:
                # Стандартный rate limit
                result = await rate_limiter.check_rate_limit(client_ip)

                if not result.allowed:
                    headers = {
                        "Retry-After": str(int(result.retry_after or 60)),
                        "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + result.reset_after)),
                    }
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Слишком много запросов. Попробуйте через {int(result.retry_after or 60)} секунд.",
                        headers=headers,
                    )

            # Добавляем заголовки с информацией о rate limit
            response = await call_next(request)
            if request.url.path == "/api/auth/refresh":
                response.headers["X-RateLimit-Limit"] = "30"
            else:
                response.headers["X-RateLimit-Limit"] = str(
                    settings.RATE_LIMIT_PER_MINUTE
                )
            response.headers["X-RateLimit-Remaining"] = str(result.remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time() + result.reset_after)
            )
            return response

        except HTTPException as http_exc:
            # Пробрасываем HTTP исключения
            raise http_exc
        except Exception as e:
            logger.error(f"Ошибка rate limiting: {e}")
            # В случае ошибки пропускаем запрос (fail-open)
            return await call_next(request)
