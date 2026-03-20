"""
Infrastructure database package.
"""

from .connection import Base, DatabaseManager, get_db_manager
from .models import (
    AdminLog,
    AdminLogEventEnum,
    AuditLog,
    ConfigHistory,
    FavoriteItem,
    GlobalSetting,
    PriceAlert,
    User,
    UserRoleEnum,
    _utc_now,
)
from .repositories import (
    AdminLogRepository,
    AuditLogRepository,
    ConfigHistoryRepository,
    FavoriteItemRepository,
    GlobalSettingRepository,
    PriceAlertRepository,
    UserRepository,
)

__all__ = [
    "DatabaseManager",
    "get_db_manager",
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
    "UserRepository",
    "ConfigHistoryRepository",
    "FavoriteItemRepository",
    "PriceAlertRepository",
    "AuditLogRepository",
    "AdminLogRepository",
    "GlobalSettingRepository",
]
