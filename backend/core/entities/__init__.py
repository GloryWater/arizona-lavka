"""
Domain entities - бизнес-сущности предметной области.
"""

from .config import ConfigHistoryEntity
from .favorite import FavoriteItemEntity
from .price_alert import PriceAlertEntity
from .user import UserEntity

__all__ = [
    "UserEntity",
    "ConfigHistoryEntity",
    "FavoriteItemEntity",
    "PriceAlertEntity",
]
