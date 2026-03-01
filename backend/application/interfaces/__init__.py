"""
Application interfaces - абстракции для инфраструктуры.
"""

from .repositories import (
    IUserRepository,
    IConfigHistoryRepository,
    IFavoriteItemRepository,
    IPriceAlertRepository,
    IAuditLogRepository,
    IAdminLogRepository,
    IGlobalSettingRepository,
)
from .external import (
    IMarketplaceAPI,
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
