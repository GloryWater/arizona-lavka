"""
FavoriteItem domain entity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FavoriteItemEntity:
    """
    Domain сущность избранного предмета.
    """
    id: Optional[int] = None
    user_id: int = 0
    item_id: int = 0
    item_name: str = ""
    target_price: Optional[float] = None
    target_percentage: float = -5.0
    mode: str = ""
    server_id: int = 0
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
