"""
База данных и ORM модели Arizona Lavka Marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from datetime import datetime
from typing import Optional, List, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON,
    UniqueConstraint, Index, func
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


# =============================================================================
# Base Model
# =============================================================================

class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей."""
    
    # Представление строки
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


# =============================================================================
# Database Models
# =============================================================================

class User(Base):
    """
    Модель пользователя.
    
    Атрибуты:
        id: Первичный ключ
        username: Уникальное имя пользователя (3-50 символов)
        email: Уникальный email
        hashed_password: Хешированный пароль
        first_name: Имя (опционально)
        last_name: Фамилия (опционально)
        is_premium: Premium статус
        login_attempts: Количество неудачных попыток входа
        locked_until: Время разблокировки после блокировки
        refresh_token: Текущий refresh токен
        created_at: Дата создания
        updated_at: Дата обновления
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Профиль
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)

    # Telegram
    telegram_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telegram_first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telegram_last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_telegram_user: Mapped[bool] = mapped_column(Boolean, default=False)

    # Безопасность
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Токены
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Связи
    configs: Mapped[List["ConfigHistory"]] = relationship(
        "ConfigHistory", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    favorites: Mapped[List["FavoriteItem"]] = relationship(
        "FavoriteItem", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    price_alerts: Mapped[List["PriceAlert"]] = relationship(
        "PriceAlert", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_users_username_email", "username", "email"),
    )


class ConfigHistory(Base):
    """
    История сгенерированных конфигов.
    """
    __tablename__ = "config_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Параметры генерации
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)
    server_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)  # SELL или BUY
    percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Результаты
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    used_historical_data: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Статистика
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="configs")

    __table_args__ = (
        Index("ix_config_history_user_created", "user_id", "created_at"),
    )


class FavoriteItem(Base):
    """
    Избранные предметы.
    """
    __tablename__ = "favorite_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Предмет
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Параметры
    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_percentage: Mapped[float] = mapped_column(Float, default=-5.0)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="favorites")

    __table_args__ = (
        Index("ix_favorite_items_user_item", "user_id", "item_id", "mode"),
    )


class PriceAlert(Base):
    """
    Уведомления об изменении цен.
    """
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Предмет
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Параметры
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)  # "above" или "below"

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    triggered_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="price_alerts")

    __table_args__ = (
        Index("ix_price_alerts_user_active", "user_id", "is_active"),
    )


class AuditLog(Base):
    """
    Журнал аудита действий.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Пользователь
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Действие
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Контекст
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failure, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )


# =============================================================================
# Database Session Management
# =============================================================================

class DatabaseManager:
    """
    Менеджер базы данных для управления подключением и сессиями.
    
    Использование:
        db_manager = DatabaseManager(database_url)
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # работа с сессией
    """
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Инициализация менеджера БД.
        
        Args:
            database_url: URL подключения к базе данных
            echo: Логировать ли SQL запросы
        """
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_maker = None
    
    async def initialize(self) -> None:
        """Инициализация движка и создание таблиц."""
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
        
        # Создание таблиц
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Закрытие соединения с БД."""
        if self._engine:
            await self._engine.dispose()
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Контекстный менеджер для получения сессии.
        
        Yield:
            AsyncSession: Сессия базы данных
        """
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
        """
        Контекстный менеджер для получения сессии без авто-коммита.
        
        Yield:
            AsyncSession: Сессия базы данных
        """
        if not self._session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self._session_maker()
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# Helper Functions
# =============================================================================

async def get_db_session(db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД.
    
    Args:
        db_manager: Менеджер базы данных
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with db_manager.get_session() as session:
        yield session
