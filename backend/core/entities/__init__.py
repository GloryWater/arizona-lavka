"""
Domain entities - бизнес-сущности предметной области.
"""

from .user import UserEntity
from .config import ConfigHistoryEntity
from .favorite import FavoriteItemEntity
from .price_alert import PriceAlertEntity

__all__ = [
    "UserEntity",
    "ConfigHistoryEntity",
    "FavoriteItemEntity",
    "PriceAlertEntity",
]
