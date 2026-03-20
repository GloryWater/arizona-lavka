"""
Unit of Work interface.

Определяет контракт для управления транзакциями и репозиториями.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from application.interfaces.repositories import (
    IAdminLogRepository,
    IAuditLogRepository,
    IConfigHistoryRepository,
    IFavoriteItemRepository,
    IGlobalSettingRepository,
    IPriceAlertRepository,
    IUserRepository,
)


class IUnitOfWork(ABC):
    """
    Интерфейс Unit of Work.

    Управляет транзакциями и предоставляет доступ к репозиториям.
    """

    # Репозитории
    users: IUserRepository
    config_history: IConfigHistoryRepository
    favorites: IFavoriteItemRepository
    price_alerts: IPriceAlertRepository
    audit_logs: IAuditLogRepository
    admin_logs: IAdminLogRepository
    global_settings: IGlobalSettingRepository

    @abstractmethod
    async def __aenter__(self):
        """Начинает транзакцию."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершает транзакцию (commit или rollback)."""
        pass

    @abstractmethod
    async def commit(self):
        """Фиксирует изменения в транзакции."""
        pass

    @abstractmethod
    async def rollback(self):
        """Откатывает изменения в транзакции."""
        pass
