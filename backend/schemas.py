"""
Arizona Lavka Marketplace - Pydantic Schemas for API.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Pydantic модели для валидации запросов и ответов API.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import SERVER_NAMES

# =============================================================================
# Enums
# =============================================================================


class OfferType(str, Enum):
    """Тип предложения: продажа или покупка."""

    SELL = "sell"
    BUY = "buy"


class ConfigMode(str, Enum):
    """Режим генерации конфига."""

    SELL = "SELL"
    BUY = "BUY"


# =============================================================================
# Marketplace Schemas
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
            cls(id=server_id, name=name) for server_id, name in SERVER_NAMES.items()
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
# Lavka Schemas
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
# Config Generator Schemas
# =============================================================================


class ConfigGenerateRequest(BaseModel):
    """Запрос на генерацию конфига."""

    server_id: int = Field(ge=0, le=32, description="ID сервера (0-32)")
    mode: ConfigMode = Field(description="Режим: SELL или BUY")
    percentage: float = Field(
        ge=-50, le=50, description="Процент корректировки цены (-50% до +50%)"
    )
    min_liquidity: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Минимальная ликвидность предмета (0-100%)",
    )
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
        alias_generator=lambda x: x.rstrip("_") if x.endswith("_") else x,
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
# Auth Schemas
# =============================================================================


class UserRegister(BaseModel):
    """Регистрация пользователя."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    fingerprint: Optional[str] = Field(None, max_length=64)
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    # Cloudflare Turnstile token for bot protection
    turnstile_token: str = Field(
        ..., description="Cloudflare Turnstile verification token"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Валидация email по RFC 5322 (упрощённая)."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Некорректный формат email адреса")
        return v


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
    role: str = "user"
    last_active_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegisterResponse(BaseModel):
    """Ответ после регистрации."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    requires_email_verification: bool = True
    message: str = "Пользователь зарегистрирован. Пожалуйста, подтвердите email."


class EmailVerificationRequest(BaseModel):
    """Подтверждение email кодом."""

    code: str = Field(..., min_length=6, max_length=6)


class EmailVerificationTokenRequest(BaseModel):
    """Подтверждение email токеном из ссылки."""

    token: str


class EmailResendRequest(BaseModel):
    """Запрос на повторную отправку письма верификации."""

    email: str


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


# =============================================================================
# Admin Schemas
# =============================================================================


class AdminUserResponse(BaseModel):
    """Информация о пользователе для админки."""

    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: bool = False
    role: str = "user"
    last_active_at: Optional[datetime] = None
    created_at: datetime
    configs_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminLogResponse(BaseModel):
    """Лог админ-панели."""

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    event_type: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Лог аудита действий пользователей."""

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminStatsSummary(BaseModel):
    """Сводная статистика."""

    total_users: int
    total_configs: int
    dau: int
    mau: int
    avg_configs_per_user_per_day: float


class AdminStatsChartData(BaseModel):
    """Данные для графика."""

    date: str
    registrations: int
    configs_generated: int


class GlobalSettingResponse(BaseModel):
    """Настройка."""

    key: str
    value: dict
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlobalSettingUpdate(BaseModel):
    """Обновление настройки."""

    value: dict


# =============================================================================
# Metrics Schemas
# =============================================================================


class EventCategory(str):
    """Категории событий."""

    ACTION = "action"
    NAVIGATION = "navigation"
    CONVERSION = "conversion"
    ERROR = "error"


class SessionStartRequest(BaseModel):
    """Запрос начала сессии."""

    session_id: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[dict] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class SessionStartResponse(BaseModel):
    """Ответ начала сессии."""

    session_id: str
    user_id: Optional[int] = None
    started_at: datetime
    status: str = "ok"


class SessionEndRequest(BaseModel):
    """Запрос завершения сессии."""

    session_id: str
    duration_seconds: Optional[int] = None
    pages_viewed: Optional[int] = None
    events_count: Optional[int] = None


class SessionEndResponse(BaseModel):
    """Ответ завершения сессии."""

    session_id: str
    ended_at: datetime
    status: str = "ok"


class PageViewRequest(BaseModel):
    """Запрос просмотра страницы."""

    session_id: str
    user_id: Optional[int] = None
    page_path: str
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    time_on_page: Optional[int] = None


class PageViewResponse(BaseModel):
    """Ответ просмотра страницы."""

    session_id: str
    page_path: str
    viewed_at: datetime
    status: str = "ok"


class UserEventRequest(BaseModel):
    """Запрос события пользователя."""

    session_id: str
    user_id: Optional[int] = None
    event_type: str
    event_category: str
    event_data: Optional[dict] = None
    error_message: Optional[str] = None


class UserEventResponse(BaseModel):
    """Ответ события пользователя."""

    event_id: int
    event_type: str
    recorded_at: datetime
    status: str = "ok"


class ConversionRequest(BaseModel):
    """Запрос конверсии."""

    session_id: str
    user_id: Optional[int] = None
    conversion_type: str
    conversion_value: Optional[float] = None
    currency: Optional[str] = None
    metadata: Optional[dict] = None


class ConversionResponse(BaseModel):
    """Ответ конверсии."""

    conversion_id: int
    conversion_type: str
    converted_at: datetime
    status: str = "ok"


# Admin Metrics Responses
class MetricsOverviewResponse(BaseModel):
    """Обзор метрик."""

    dau: int
    mau: int
    total_sessions: int
    avg_session_duration: float
    total_page_views: int
    total_events: int
    total_conversions: int
    total_revenue: Optional[float] = None


class EngagementMetricsResponse(BaseModel):
    """Метрики вовлеченности."""

    avg_pages_per_session: float
    avg_events_per_session: float
    bounce_rate: float
    retention_rate_day_1: float
    retention_rate_day_7: float
    retention_rate_day_30: float


class ConversionMetricsResponse(BaseModel):
    """Метрики конверсии."""

    total_conversions: int
    conversion_rate: float
    total_revenue: Optional[float] = None
    avg_order_value: Optional[float] = None
    top_conversion_types: list


class UserSegmentsResponse(BaseModel):
    """Сегменты пользователей."""

    new_users: int
    returning_users: int
    power_users: int
    at_risk_users: int


class MetricsExportResponse(BaseModel):
    """Экспорт метрик."""

    format: str
    data: dict
    generated_at: datetime


class AdminMetricsQueryParams(BaseModel):
    """Параметры запроса метрик."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    server_id: Optional[int] = None
    user_id: Optional[int] = None
