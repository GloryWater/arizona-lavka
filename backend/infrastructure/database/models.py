"""
Database models - ORM модели.

Импортируем из connection.py где теперь определены ORM модели.
"""

from infrastructure.database.connection import (  # Security models; Metrics models
    AdminLog,
    AdminLogEventEnum,
    AuditLog,
    Base,
    ConfigHistory,
    Conversion,
    DailyMetrics,
    DeviceFingerprint,
    EmailVerificationToken,
    FavoriteItem,
    GlobalSetting,
    PageView,
    PriceAlert,
    User,
    UserEvent,
    UserRoleEnum,
    UserSession,
    _utc_now,
)

__all__ = [
    "Base",
    "User",
    "ConfigHistory",
    "FavoriteItem",
    "PriceAlert",
    "AuditLog",
    "AdminLog",
    "GlobalSetting",
    "UserRoleEnum",
    "AdminLogEventEnum",
    "_utc_now",
    # Security
    "EmailVerificationToken",
    "DeviceFingerprint",
    # Metrics
    "UserSession",
    "PageView",
    "UserEvent",
    "Conversion",
    "DailyMetrics",
]
