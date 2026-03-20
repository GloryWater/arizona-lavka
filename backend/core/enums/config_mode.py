"""
ConfigMode enum.
"""

from enum import Enum


class ConfigMode(str, Enum):
    """Режим генерации конфига."""

    SELL = "SELL"
    BUY = "BUY"
