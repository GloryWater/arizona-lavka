"""
Logging middleware для логирования запросов.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)


def create_logging_middleware(app: FastAPI) -> None:
    """
    Регистрирует middleware для логирования запросов.

    Логирует:
    - Метод и путь запроса
    - Статус код ответа
    - Время обработки
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        logger.info(f"{request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} ({process_time:.3f}s)"
        )

        return response
