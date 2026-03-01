"""
ConfigHistory domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class ConfigHistoryEntity:
    """
    Domain сущность истории конфигов.

    Атрибуты:
        id: Первичный ключ
        user_id: ID пользователя
        server_id: ID сервера
        server_name: Название сервера
        mode: Режим (SELL/BUY)
        percentage: Процент корректировки
        items_count: Количество предметов
        config_data: Данные конфига (JSON)
        used_historical_data: Использовались ли исторические данные
        confidence_score: Оценка уверенности
        download_count: Количество скачиваний
        created_at: Дата создания
    """
    id: Optional[int] = None
    user_id: int = 0
    server_id: int = 0
    server_name: str = ""
    mode: str = ""
    percentage: float = 0.0
    items_count: int = 0
    config_data: dict = field(default_factory=dict)
    used_historical_data: bool = False
    confidence_score: Optional[float] = None
    download_count: int = 0
    created_at: Optional[datetime] = None
