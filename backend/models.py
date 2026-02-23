"""
Pydantic модели для валидации данных API.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

from config import SERVER_NAMES


class OfferType(str, Enum):
    """Тип предложения: продажа или покупка."""
    SELL = "sell"
    BUY = "buy"


class ConfigMode(str, Enum):
    """Режим генерации конфига."""
    SELL = "SELL"
    BUY = "BUY"


# =============================================================================
# Marketplace Models
# =============================================================================

class ServerInfo(BaseModel):
    """Информация о сервере."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def get_all_servers(cls) -> List["ServerInfo"]:
        """Получает список всех серверов."""
        return [
            cls(id=server_id, name=name)
            for server_id, name in SERVER_NAMES.items()
        ]


class Offer(BaseModel):
    """Нормализованное предложение."""
    type: OfferType
    itemId: int
    itemName: str
    price: float
    count: int
    username: str
    lavkaUid: str
    serverId: int
    serverName: str = ""
    userStatus: bool

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context) -> None:
        """Автоматически заполняет serverName после инициализации."""
        if not self.serverName:
            from config import get_server_name
            self.serverName = get_server_name(self.serverId)


class OffersResponse(BaseModel):
    """Ответ API с предложениями."""
    offers: List[Offer]
    total: int
    servers: int


class SearchParams(BaseModel):
    """Параметры поиска."""
    search_term: Optional[str] = Field(default="", max_length=100)
    server_id: Optional[int] = Field(default=None, ge=-1, le=32)
    sort_order: Optional[Literal["asc", "desc", "none"]] = Field(default="none")


# =============================================================================
# Lavka Models
# =============================================================================

class LavkaSummary(BaseModel):
    """Краткая информация о лавке."""
    lavkaUid: str
    username: str
    serverId: int
    sellCount: int
    buyCount: int
    totalItems: int

    model_config = ConfigDict(from_attributes=True)


class LavkaItem(BaseModel):
    """Предмет в лавке."""
    itemId: int
    itemName: str
    price: float
    count: int
    type: OfferType

    model_config = ConfigDict(from_attributes=True)


class LavkaDetail(BaseModel):
    """Детальная информация о лавке."""
    lavkaUid: str
    username: str
    serverId: int
    userStatus: bool
    sellItems: List[LavkaItem]
    buyItems: List[LavkaItem]
    totalSell: int
    totalBuy: int

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Config Generator Models
# =============================================================================

class ConfigGenerateRequest(BaseModel):
    """Запрос на генерацию конфига."""
    server_id: int = Field(ge=0, le=32, description="ID сервера (0-32)")
    mode: ConfigMode = Field(description="Режим: SELL или BUY")
    percentage: float = Field(ge=-50, le=50, description="Процент корректировки цены (-50% до +50%)")
    min_liquidity: float = Field(default=0.0, ge=0, le=100, description="Минимальная ликвидность предмета (0-100)")
    save_to_history: bool = Field(default=True, description="Сохранить в историю")


class ConfigItemResponse(BaseModel):
    """Элемент конфига для ответа API (формат бота)."""
    price: str
    maximum: bool = True
    enabled: bool = True
    name: str
    price_vc: int = 9
    count: int = 1
    slot_count: List[str] = ["0"]
    slot_id: List[str] = ["0"]
    position_tab: int = 1
    all_count: int = 0
    continue_: str = "1"
    count_maximum: int = 0

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: x.rstrip('_') if x.endswith('_') else x
    )


class ConfigStatsResponse(BaseModel):
    """Статистика генерации конфига (очищенная)."""
    total_items: int
    items_with_history: int
    avg_confidence: float
    price_range: dict


class ConfigGenerateResponse(BaseModel):
    """Ответ с сгенерированным конфигом."""
    config: List[ConfigItemResponse]
    total_items: int
    server_name: str
    mode: str
    stats: ConfigStatsResponse


class ConfigHistoryResponse(BaseModel):
    """Элемент истории конфигов."""
    id: int
    server_name: str
    server_id: int
    mode: str
    percentage: float
    items_count: int
    created_at: datetime
    download_count: int


class ConfigDetailResponse(BaseModel):
    """Детали конфига для скачивания."""
    config: List[dict]
    server_name: str
    mode: str
    created_at: datetime


# =============================================================================
# Auth Models
# =============================================================================

class UserRegister(BaseModel):
    """Регистрация пользователя."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    """Вход пользователя."""
    username_or_email: str
    password: str


class TelegramLoginRequest(BaseModel):
    """Запрос на вход через Telegram."""
    init_data: str


class TokenResponse(BaseModel):
    """Ответ с токенами."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Информация о пользователе."""
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: bool = False
    is_telegram_user: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserResponse):
    """Расширенная информация о пользователе."""
    configs_count: int = 0


class FavoriteItemCreate(BaseModel):
    """Создание избранного предмета."""
    item_id: int
    item_name: str
    target_price: Optional[float] = None
    target_percentage: float = -5.0
    mode: str
    server_id: int
    notes: Optional[str] = None


class FavoriteItemResponse(BaseModel):
    """Избранный предмет."""
    id: int
    item_id: int
    item_name: str
    target_price: Optional[float]
    target_percentage: float
    mode: str
    server_id: int
    notes: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceAlertCreate(BaseModel):
    """Создание уведомления."""
    item_id: int
    item_name: str
    server_id: int
    target_price: float
    condition: str


class PriceAlertResponse(BaseModel):
    """Уведомление."""
    id: int
    item_id: int
    item_name: str
    server_id: int
    target_price: float
    condition: str
    is_active: bool
    triggered: bool
    triggered_at: Optional[datetime]
    triggered_price: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
