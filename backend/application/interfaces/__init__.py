"""
Application interfaces - абстракции для инфраструктуры.
"""

from .external import IMarketplaceAPI
from .repositories import (
    IAdminLogRepository,
    IAuditLogRepository,
    IConfigHistoryRepository,
    IFavoriteItemRepository,
    IGlobalSettingRepository,
    IPriceAlertRepository,
    IUserRepository,
)

__all__ = [
    "IUserRepository",
    "IConfigHistoryRepository",
    "IFavoriteItemRepository",
    "IPriceAlertRepository",
    "IAuditLogRepository",
    "IAdminLogRepository",
    "IGlobalSettingRepository",
    "IMarketplaceAPI",
]
