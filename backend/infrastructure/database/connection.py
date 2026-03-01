"""
Database connection and session management.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import AsyncGenerator, Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON,
    UniqueConstraint, Index, func, Enum
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


# =============================================================================
# Base Model
# =============================================================================

class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех ORM моделей."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


# =============================================================================
# Enums
# =============================================================================

from enum import Enum as PyEnum

class UserRoleEnum(PyEnum):
    """Роли пользователей."""
    USER = "user"
    ADMIN = "admin"


class AdminLogEventEnum(PyEnum):
    """Типы событий админ-логов."""
    LOGIN = "login"
    LOGOUT = "logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    CONFIG_GENERATED = "config_generated"
    SETTINGS_UPDATED = "settings_updated"
    EXPORT_DATA = "export_data"
    VIEW_LOGS = "view_logs"
    VIEW_STATS = "view_stats"


# =============================================================================
# Helper Functions
# =============================================================================

from datetime import datetime, timezone

def _utc_now() -> datetime:
    """Возвращает текущее UTC время для default значений."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =============================================================================
# Database Models
# =============================================================================

class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)

    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False, index=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    telegram_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telegram_first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telegram_last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_telegram_user: Mapped[bool] = mapped_column(Boolean, default=False)

    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)

    configs: Mapped[List["ConfigHistory"]] = relationship(
        "ConfigHistory", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    favorites: Mapped[List["FavoriteItem"]] = relationship(
        "FavoriteItem", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    price_alerts: Mapped[List["PriceAlert"]] = relationship(
        "PriceAlert", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    admin_logs: Mapped[List["AdminLog"]] = relationship(
        "AdminLog", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_users_username_email", "username", "email"),
    )


class ConfigHistory(Base):
    """История сгенерированных конфигов."""
    __tablename__ = "config_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    server_id: Mapped[int] = mapped_column(Integer, nullable=False)
    server_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)

    items_count: Mapped[int] = mapped_column(Integer, default=0)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    used_historical_data: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    download_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="configs")

    __table_args__ = (
        Index("ix_config_history_user_created", "user_id", "created_at"),
    )


class FavoriteItem(Base):
    """Избранные предметы."""
    __tablename__ = "favorite_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)

    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_percentage: Mapped[float] = mapped_column(Float, default=-5.0)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="favorites")

    __table_args__ = (
        Index("ix_favorite_items_user_item", "user_id", "item_id", "mode"),
    )


class PriceAlert(Base):
    """Уведомления об изменении цен."""
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)

    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    triggered_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="price_alerts")

    __table_args__ = (
        Index("ix_price_alerts_user_active", "user_id", "is_active"),
    )


class AuditLog(Base):
    """Журнал аудита действий."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )


class AdminLog(Base):
    """Журнал логов админ-панели."""
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="admin_logs")

    __table_args__ = (
        Index("ix_admin_logs_event_created", "event_type", "created_at"),
    )


class GlobalSetting(Base):
    """Глобальные настройки проекта."""
    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)


# =============================================================================
# Database Session Management
# =============================================================================

class DatabaseManager:
    """Менеджер базы данных."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, database_url: str = None, echo: bool = False):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_maker = None
        self._initialized = True

    async def initialize(self) -> None:
        """Инициализация движка и создание таблиц."""
        from config import get_settings

        if self.database_url is None:
            settings = get_settings()
            self.database_url = settings.database_url

        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
        )

        self._session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Закрытие соединения с БД."""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для получения сессии с авто-коммитом."""
        if not self._session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def get_session_no_commit(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для получения сессии без авто-коммита."""
        if not self._session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_maker()
        try:
            yield session
        finally:
            await session.close()


# Global instance
_db_manager_instance: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Получает или создаёт DatabaseManager (singleton)."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance
