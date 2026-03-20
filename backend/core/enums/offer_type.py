"""
OfferType enum.
"""

from enum import Enum


class OfferType(str, Enum):
    """Тип предложения: продажа или покупка."""

    SELL = "sell"
    BUY = "buy"
