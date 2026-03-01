"""
Arizona Lavka Marketplace - Database Compatibility Layer.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

# Импортируем из infrastructure (где теперь определены ORM модели)
from infrastructure.database.models import (
    Base,
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

# Импортируем из infrastructure
from infrastructure.database.connection import (
    DatabaseManager,
    get_db_manager,
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
]
