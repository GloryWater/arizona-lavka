"""
Arizona Lavka Marketplace - Prometheus Metrics Middleware.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Middleware для автоматического сбора HTTP метрик.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from metrics.prometheus import (
    http_request_duration_seconds,
    http_request_duration_summary,
    http_requests_in_progress,
    http_requests_total,
    http_responses_total,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Prometheus Metrics Middleware
# =============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware для сбора метрик Prometheus для всех HTTP запросов.

    Собирает:
    - Количество запросов (по методам, endpoint'ам, статусам)
    - Длительность запросов (гистограмма, summary)
    - Количество активных запросов
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обрабатывает запрос и собирает метрики.

        Args:
            request: HTTP запрос
            call_next: Следующий middleware/handler

        Returns:
            Response: HTTP ответ
        """
        method = request.method
        endpoint = self._get_endpoint_path(request.url.path)

        # Начало замера
        start_time = time.time()
        http_requests_in_progress.labels(method=method).inc()

        try:
            response = await call_next(request)

            # Завершение замера
            duration = time.time() - start_time
            status_code = response.status_code

            # Запись метрик
            self._record_metrics(method, endpoint, status_code, duration)

            return response

        except Exception as e:
            # Обработка ошибок
            duration = time.time() - start_time
            status_code = 500

            logger.error(f"Request error: {e} | {method} {endpoint}")

            # Запись метрик для ошибки
            self._record_metrics(method, endpoint, status_code, duration)

            raise

        finally:
            http_requests_in_progress.labels(method=method).dec()

    def _get_endpoint_path(self, path: str) -> str:
        """
        Нормализует путь endpoint'а для метрик.

        Убирает динамические параметры (ID) для группировки метрик.

        Args:
            path: Оригинальный путь

        Returns:
            str: Нормализованный путь
        """
        # Заменяем числовые ID на {id}
        import re

        normalized = re.sub(r"/\d+", "/{id}", path)

        # Убираем query параметры
        normalized = normalized.split("?")[0]

        # Ограничиваем длину
        if len(normalized) > 100:
            normalized = normalized[:100]

        return normalized

    def _record_metrics(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
    ) -> None:
        """
        Записывает метрики запроса.

        Args:
            method: HTTP метод
            endpoint: Endpoint path
            status_code: HTTP статус код
            duration: Длительность в секундах
        """
        # Счётчик запросов
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code,
        ).inc()

        # Счётчик ответов по категориям
        category = self._get_status_category(status_code)
        http_responses_total.labels(
            status_code=status_code,
            status_category=category,
        ).inc()

        # Гистограмма длительности
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        # Summary для перцентилей
        http_request_duration_summary.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

    def _get_status_category(self, status_code: int) -> str:
        """
        Получает категорию статуса.

        Args:
            status_code: HTTP статус код

        Returns:
            str: Категория (2xx, 3xx, 4xx, 5xx)
        """
        if 200 <= status_code < 300:
            return "2xx"
        elif 300 <= status_code < 400:
            return "3xx"
        elif 400 <= status_code < 500:
            return "4xx"
        else:
            return "5xx"


# =============================================================================
# Factory Function
# =============================================================================


def create_prometheus_middleware(app: FastAPI) -> None:
    """
    Добавляет Prometheus middleware в приложение.

    Args:
        app: FastAPI приложение
    """
    app.add_middleware(PrometheusMiddleware)
    logger.info("Prometheus middleware registered")
