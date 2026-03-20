"""
Arizona Lavka Marketplace - Error Handler.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Глобальный обработчик ошибок для FastAPI приложения.
Перехватывает все исключения и возвращает стандартизированные ответы.
Технические детали логируются, клиенту показываются безопасные сообщения.
"""

import logging
import traceback
from typing import Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from exceptions import (
    AppException,
    ConflictError,
    DatabaseError,
    ExternalAPIError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnauthorizedError,
)
from exceptions import ValidationError as AppValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# Стандартный формат ответа об ошибке
# =============================================================================


def create_error_response(
    status_code: int,
    detail: str,
    error_code: str,
    extra: dict | None = None,
) -> JSONResponse:
    """
    Создаёт стандартизированный JSON-ответ об ошибке.

    Args:
        status_code: HTTP статус код
        detail: Сообщение для клиента (безопасное, без технических деталей)
        error_code: Код ошибки для программной обработки
        extra: Дополнительные данные

    Returns:
        JSONResponse с форматом: { status: "error", detail, code, ...extra }
    """
    content = {
        "status": "error",
        "detail": detail,
        "code": error_code,
        "status_code": status_code,
    }

    if extra:
        content.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


# =============================================================================
# Обработчики исключений
# =============================================================================


def register_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует все обработчики исключений для приложения.

    Args:
        app: Экземпляр FastAPI приложения
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """
        Обработчик кастомных исключений приложения.

        Логгирует предупреждение для 4xx и ошибку для 5xx.
        """
        if exc.status_code >= 500:
            logger.error(
                f"AppException {exc.error_code}: {exc.detail}",
                extra={"request_path": str(request.url.path)},
            )
        else:
            logger.warning(
                f"AppException {exc.error_code}: {exc.detail}",
                extra={"request_path": str(request.url.path)},
            )

        return create_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            error_code=exc.error_code,
            extra=exc.extra if exc.extra else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """
        Обработчик ошибок валидации Pydantic/FastAPI.

        Форматирует ошибки валидации в понятный вид.
        """
        errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error.get("loc", []))
            message = error.get("msg", "Ошибка валидации")
            errors.append({"field": field, "message": message})

        logger.warning(
            f"Validation error: {errors}",
            extra={"request_path": str(request.url.path)},
        )

        # Формируем понятное сообщение
        if len(errors) == 1:
            detail = f"Ошибка в поле '{errors[0]['field']}': {errors[0]['message']}"
        else:
            detail = f"Обнаружено ошибок валидации: {len(errors)}. Проверьте данные"

        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            extra={"errors": errors},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        """
        Обработчик ошибок валидации Pydantic (для response моделей).
        """
        logger.error(
            f"Pydantic validation error: {exc}",
            extra={"request_path": str(request.url.path)},
        )

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обработки данных. Попробуйте позже",
            error_code="RESPONSE_VALIDATION_ERROR",
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Обработчик стандартных HTTPException FastAPI.

        Преобразует в кастомные исключения для единообразия.
        """
        # Маппинг стандартных HTTPException в кастомные
        exception_map = {
            401: UnauthorizedError,
            403: ForbiddenError,
            404: NotFoundError,
            409: ConflictError,
            429: TooManyRequestsError,
            503: ServiceUnavailableError,
        }

        if exc.status_code in exception_map:
            exc_class = exception_map[exc.status_code]
            app_exc = exc_class(
                detail=exc.detail or exc_class().__dict__["detail"],
            )
            return await app_exception_handler(request, app_exc)

        # Для остальных статусов (включая 500)
        logger.error(
            f"HTTPException {exc.status_code}: {exc.detail}",
            extra={"request_path": str(request.url.path)},
        )

        return create_error_response(
            status_code=exc.status_code,
            detail=exc.detail or "Произошла ошибка",
            error_code=f"HTTP_{exc.status_code}",
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Глобальный обработчик всех необработанных исключений.

        Логирует полный stack trace, клиенту показывает безопасное сообщение.
        """
        # Логируем полную информацию об ошибке
        error_traceback = traceback.format_exc()
        logger.error(
            f"Unhandled exception:\n{error_traceback}",
            extra={
                "request_path": str(request.url.path),
                "request_method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        # Клиенту показываем только безопасное сообщение
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера. Мы уже чиним!",
            error_code="INTERNAL_ERROR",
        )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        """
        Обработчик ошибок подключения (БД, внешние сервисы).
        """
        logger.error(
            f"Connection error: {exc}",
            extra={"request_path": str(request.url.path)},
        )

        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис временно недоступен. Попробуйте позже",
            error_code="CONNECTION_ERROR",
        )

    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError):
        """
        Обработчик ошибок таймаута.
        """
        logger.warning(
            f"Timeout error: {exc}",
            extra={"request_path": str(request.url.path)},
        )

        return create_error_response(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Превышено время ожидания ответа. Попробуйте позже",
            error_code="TIMEOUT_ERROR",
        )


# =============================================================================
# Утилиты для обработки ошибок
# =============================================================================


def handle_database_error(exc: Exception) -> DatabaseError:
    """
    Обёртка для ошибок базы данных.

    Args:
        exc: Оригинальное исключение

    Returns:
        DatabaseError для выброса
    """
    logger.error(f"Database error: {exc}", exc_info=True)
    return DatabaseError(detail="Ошибка базы данных. Попробуйте позже")


def handle_external_api_error(
    exc: Exception, service_name: str = "Внешний сервис"
) -> ExternalAPIError:
    """
    Обёртка для ошибок внешних API.

    Args:
        exc: Оригинальное исключение
        service_name: Название сервиса

    Returns:
        ExternalAPIError для выброса
    """
    logger.error(f"{service_name} error: {exc}", exc_info=True)
    return ExternalAPIError(detail=f"{service_name} временно недоступен")
