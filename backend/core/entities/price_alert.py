"""
PriceAlert domain entity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceAlertEntity:
    """
    Domain сущность уведомления о цене.
    """
    id: Optional[int] = None
    user_id: int = 0
    item_id: int = 0
    item_name: str = ""
    server_id: int = 0
    target_price: float = 0.0
    condition: str = ""
    is_active: bool = True
    triggered: bool = False
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[float] = None
    created_at: Optional[datetime] = None
