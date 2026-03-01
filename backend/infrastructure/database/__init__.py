"""
Infrastructure database package.
"""

from .connection import DatabaseManager, get_db_manager, Base
from .models import (
    User,
    ConfigHistory,
    FavoriteItem,
    PriceAlert,
    AuditLog,
    AdminLog,
    GlobalSetting,
    UserRoleEnum,
    AdminLogEventEnum,
    _utc_now,
)
from .repositories import (
    UserRepository,
    ConfigHistoryRepository,
    FavoriteItemRepository,
    PriceAlertRepository,
    AuditLogRepository,
    AdminLogRepository,
    GlobalSettingRepository,
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
