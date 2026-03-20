"""
Domain exceptions.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from typing import Any, Optional


class DomainException(Exception):
    """
    Базовое исключение domain слоя.

    Все domain исключения наследуются от этого класса.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# Domain Business Rule Violations
# =============================================================================


class EntityNotFoundError(DomainException):
    """
    Сущность не найдена (404).

    Используется когда запрошенный объект не существует в domain.
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: Any,
        message: Optional[str] = None,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        msg = message or f"{entity_type} с ID {entity_id} не найден"
        super().__init__(message=msg, code="ENTITY_NOT_FOUND")


class BusinessRuleViolationError(DomainException):
    """
    Нарушение бизнес-правила (400).

    Используется когда операция нарушает бизнес-правила предметной области.
    """

    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details={**(details or {}), "rule": rule} if rule else details,
        )


class ValidationError(DomainException):
    """
    Ошибка валидации domain сущности (400).

    Используется когда данные сущности не проходят валидацию.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="DOMAIN_VALIDATION_ERROR",
            details={**(details or {}), "field": field} if field else details,
        )


class ConflictError(DomainException):
    """
    Конфликт состояния (409).

    Используется когда ресурс уже существует или есть конфликт состояния.
    """

    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="DOMAIN_CONFLICT",
            details={**(details or {}), "resource": resource} if resource else details,
        )


class UnauthorizedError(DomainException):
    """
    Пользователь не авторизован (401).
    """

    def __init__(
        self,
        message: str = "Требуется авторизация",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenError(DomainException):
    """
    Доступ запрещён (403).
    """

    def __init__(
        self,
        message: str = "Доступ запрещён",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            details=details,
        )
