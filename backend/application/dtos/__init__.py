"""
Application DTOs (Data Transfer Objects).

DTO используются для передачи данных между слоями архитектуры.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any


# =============================================================================
# Auth DTOs
# =============================================================================

@dataclass
class UserRegisterDTO:
    """DTO для регистрации пользователя."""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@dataclass
class UserLoginDTO:
    """DTO для входа пользователя."""
    username_or_email: str
    password: str


@dataclass
class TokenDTO:
    """DTO для токенов."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class TelegramUserDTO:
    """DTO для Telegram пользователя."""
    id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    init_data: Optional[str] = None


# =============================================================================
# User DTOs
# =============================================================================

@dataclass
class UserProfileDTO:
    """DTO профиля пользователя."""
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: bool = False
    role: str = "user"
    is_telegram_user: bool = False
    last_active_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    configs_count: int = 0


# =============================================================================
# Marketplace DTOs
# =============================================================================

@dataclass
class OfferDTO:
    """DTO предложения marketplace."""
    type: str  # "sell" или "buy"
    item_id: int
    item_name: str
    price: float
    count: int
    username: str
    lavka_uid: str
    server_id: int
    server_name: str = ""
    user_status: bool = False


@dataclass
class LavkaSummaryDTO:
    """DTO краткой информации о лавке."""
    lavka_uid: str
    username: str
    server_id: int
    sell_count: int
    buy_count: int
    total_items: int


@dataclass
class LavkaItemDTO:
    """DTO предмета в лавке."""
    item_id: int
    item_name: str
    price: float
    count: int
    type: str  # "sell" или "buy"


@dataclass
class LavkaDetailDTO:
    """DTO детальной информации о лавке."""
    lavka_uid: str
    username: str
    server_id: int
    user_status: bool
    sell_items: List[LavkaItemDTO] = field(default_factory=list)
    buy_items: List[LavkaItemDTO] = field(default_factory=list)
    total_sell: int = 0
    total_buy: int = 0


# =============================================================================
# Config Generator DTOs
# =============================================================================

@dataclass
class ConfigGenerateRequestDTO:
    """DTO запроса генерации конфига."""
    server_id: int
    mode: str  # "SELL" или "BUY"
    percentage: float
    min_liquidity: float = 0.0
    save_to_history: bool = True


@dataclass
class ConfigItemDTO:
    """DTO элемента конфига."""
    price: str
    name: str
    maximum: bool = True
    enabled: bool = True
    price_vc: int = 9
    count: int = 1
    slot_count: List[str] = field(default_factory=lambda: ["0"])
    slot_id: List[str] = field(default_factory=lambda: ["0"])
    position_tab: int = 1
    all_count: int = 0
    continue_: str = "1"
    count_maximum: int = 0


@dataclass
class ConfigStatsDTO:
    """DTO статистики конфига."""
    total_items: int
    items_with_history: int
    avg_confidence: float
    price_range: dict


@dataclass
class ConfigGenerateResponseDTO:
    """DTO ответа генерации конфига."""
    config: List[ConfigItemDTO]
    total_items: int
    server_name: str
    mode: str
    stats: ConfigStatsDTO


@dataclass
class ConfigHistoryDTO:
    """DTO истории конфигов."""
    id: int
    server_name: str
    server_id: int
    mode: str
    percentage: float
    items_count: int
    created_at: datetime
    download_count: int


# =============================================================================
# Admin DTOs
# =============================================================================

@dataclass
class AdminStatsSummaryDTO:
    """DTO сводной статистики."""
    total_users: int
    total_configs: int
    dau: int
    mau: int
    avg_configs_per_user_per_day: float


@dataclass
class AdminStatsChartDataDTO:
    """DTO данных для графика."""
    date: str
    registrations: int
    configs_generated: int


@dataclass
class GlobalSettingDTO:
    """DTO глобальной настройки."""
    key: str
    value: dict
    updated_at: datetime
