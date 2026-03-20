"""
Arizona Lavka Marketplace - Custom Exceptions.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

from typing import Any, Optional


class AppException(Exception):
    """
    Базовое исключение приложения.

    Все кастомные исключения наследуются от этого класса.
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.extra = extra or {}
        super().__init__(self.detail)


# =============================================================================
# Client Errors (4xx)
# =============================================================================


class ValidationError(AppException):
    """
    Ошибка валидации данных (400).

    Используется когда клиент отправил некорректные данные.
    """

    def __init__(
        self,
        detail: str = "Некорректные данные",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=400,
            error_code=error_code or "VALIDATION_ERROR",
            extra=extra,
        )


class UnauthorizedError(AppException):
    """
    Пользователь не авторизован (401).

    Используется когда токен отсутствует или истёк.
    """

    def __init__(
        self,
        detail: str = "Требуется авторизация",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code=error_code or "UNAUTHORIZED",
            extra=extra,
        )


class ForbiddenError(AppException):
    """
    Доступ запрещён (403).

    Используется когда у пользователя нет прав для действия.
    """

    def __init__(
        self,
        detail: str = "Доступ запрещён",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code=error_code or "FORBIDDEN",
            extra=extra,
        )


class NotFoundError(AppException):
    """
    Ресурс не найден (404).

    Используется когда запрошенный объект не существует.
    """

    def __init__(
        self,
        detail: str = "Ресурс не найден",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=404,
            error_code=error_code or "NOT_FOUND",
            extra=extra,
        )


class ConflictError(AppException):
    """
    Конфликт данных (409).

    Используется когда ресурс уже существует или есть конфликт состояния.
    """

    def __init__(
        self,
        detail: str = "Конфликт данных",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=409,
            error_code=error_code or "CONFLICT",
            extra=extra,
        )


class TooManyRequestsError(AppException):
    """
    Слишком много запросов (429).

    Используется для rate limiting.
    """

    def __init__(
        self,
        detail: str = "Слишком много запросов",
        error_code: Optional[str] = None,
        retry_after: int = 60,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=429,
            error_code=error_code or "TOO_MANY_REQUESTS",
            extra={**(extra or {}), "retry_after": retry_after},
        )


# =============================================================================
# Server Errors (5xx)
# =============================================================================


class InternalServerError(AppException):
    """
    Внутренняя ошибка сервера (500).

    Используется для непредвиденных ошибок. Клиенту показывается
    безопасное сообщение без технических деталей.
    """

    def __init__(
        self,
        detail: str = "Внутренняя ошибка сервера",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code=error_code or "INTERNAL_ERROR",
            extra=extra,
        )


class ServiceUnavailableError(AppException):
    """
    Сервис недоступен (503).

    Используется когда зависимый сервис (БД, внешний API) недоступен.
    """

    def __init__(
        self,
        detail: str = "Сервис временно недоступен",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=503,
            error_code=error_code or "SERVICE_UNAVAILABLE",
            extra=extra,
        )


class DatabaseError(AppException):
    """
    Ошибка базы данных (503).

    Используется при ошибках подключения или выполнения запросов к БД.
    """

    def __init__(
        self,
        detail: str = "Ошибка базы данных",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=503,
            error_code=error_code or "DATABASE_ERROR",
            extra=extra,
        )


class ExternalAPIError(AppException):
    """
    Ошибка внешнего API (502).

    Используется когда внешний сервис вернул ошибку.
    """

    def __init__(
        self,
        detail: str = "Ошибка внешнего сервиса",
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=502,
            error_code=error_code or "EXTERNAL_API_ERROR",
            extra=extra,
        )


class TurnstileVerificationError(AppException):
    """
    Ошибка верификации Cloudflare Turnstile (403).

    Используется когда токен Turnstile не прошёл проверку.
    """

    def __init__(
        self,
        detail: str = "Не удалось пройти проверку на бота",
        error_code: Optional[str] = None,
        error_codes: Optional[list[str]] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code=error_code or "TURNSTILE_VERIFICATION_FAILED",
            extra={**(extra or {}), "turnstile_error_codes": error_codes or []},
        )
