"""
Unit of Work implementation.

Реализует паттерн Unit of Work для управления транзакциями.
"""

from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.interfaces.repositories import (
    IAdminLogRepository,
    IAuditLogRepository,
    IConfigHistoryRepository,
    IFavoriteItemRepository,
    IGlobalSettingRepository,
    IPriceAlertRepository,
    IUserRepository,
)
from application.interfaces.uow import IUnitOfWork
from infrastructure.database.repositories import (
    AdminLogRepository,
    AuditLogRepository,
    ConfigHistoryRepository,
    FavoriteItemRepository,
    GlobalSettingRepository,
    PriceAlertRepository,
    UserRepository,
)


class UnitOfWork(IUnitOfWork):
    """
    Реализация Unit of Work.

    Управляет транзакциями и предоставляет доступ к репозиториям в рамках одной транзакции.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        Инициализация Unit of Work.

        Args:
            session_factory: Фабрика сессий SQLAlchemy
        """
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None

        # Инициализируем репозитории как None - они будут созданы в __aenter__
        self.users: Optional[IUserRepository] = None
        self.config_history: Optional[IConfigHistoryRepository] = None
        self.favorites: Optional[IFavoriteItemRepository] = None
        self.price_alerts: Optional[IPriceAlertRepository] = None
        self.audit_logs: Optional[IAuditLogRepository] = None
        self.admin_logs: Optional[IAdminLogRepository] = None
        self.global_settings: Optional[IGlobalSettingRepository] = None

    async def __aenter__(self):
        """
        Начинает транзакцию.

        Создает сессию и репозитории для работы в рамках одной транзакции.
        """
        self.session = self.session_factory()

        # Создаем репозитории с одной и той же сессией
        self.users = UserRepository(self.session)
        self.config_history = ConfigHistoryRepository(self.session)
        self.favorites = FavoriteItemRepository(self.session)
        self.price_alerts = PriceAlertRepository(self.session)
        self.audit_logs = AuditLogRepository(self.session)
        self.admin_logs = AdminLogRepository(self.session)
        self.global_settings = GlobalSettingRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Завершает транзакцию.

        Выполняет commit при успешном завершении или rollback при исключении.
        """
        if exc_type is not None:
            # Произошло исключение - откатываем транзакцию
            await self.rollback()
        else:
            # Нет исключения - фиксируем транзакцию
            await self.commit()

        # Закрываем сессию
        if self.session:
            await self.session.close()

    async def commit(self):
        """Фиксирует изменения в транзакции."""
        if self.session:
            await self.session.commit()

    async def rollback(self):
        """Откатывает изменения в транзакции."""
        if self.session:
            await self.session.rollback()
