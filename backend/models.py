"""
Arizona Lavka Marketplace - Compatibility Layer.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Note:
    Этот файл существует для обратной совместимости.
    Импортирует модели из infrastructure, core и schemas для совместимости.
"""

# Domain entities из core
from core.entities import (
    ConfigHistoryEntity,
    FavoriteItemEntity,
    PriceAlertEntity,
    UserEntity,
)

# Domain enums из core
from core.enums import ConfigMode, OfferType

# ORM модели из infrastructure
from infrastructure.database.models import (
    AdminLog,
    AdminLogEventEnum,
    AuditLog,
    Base,
    ConfigHistory,
    FavoriteItem,
    GlobalSetting,
    PriceAlert,
    User,
    UserRoleEnum,
    _utc_now,
)

# Pydantic schemas из schemas
from schemas import (  # Marketplace; Config Generator; Auth; Admin; Metrics
    AdminLogResponse,
    AdminMetricsQueryParams,
    AdminStatsChartData,
    AdminStatsSummary,
    AdminUserResponse,
    AuditLogResponse,
    ConfigDetailResponse,
    ConfigGenerateRequest,
    ConfigGenerateResponse,
    ConfigHistoryResponse,
    ConfigItemResponse,
    ConfigStatsResponse,
    ConversionMetricsResponse,
    ConversionRequest,
    ConversionResponse,
    EmailVerificationRequest,
    EmailVerificationTokenRequest,
    EngagementMetricsResponse,
    EventCategory,
    FavoriteItemCreate,
    FavoriteItemResponse,
    GlobalSettingResponse,
    GlobalSettingUpdate,
    LavkaDetail,
    LavkaItem,
    LavkaSummary,
    MetricsExportResponse,
    MetricsOverviewResponse,
    Offer,
    OffersResponse,
    PageViewRequest,
    PageViewResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    SearchParams,
    ServerInfo,
    SessionEndRequest,
    SessionEndResponse,
    SessionStartRequest,
    SessionStartResponse,
    TelegramLoginRequest,
    TokenResponse,
    UserEventRequest,
    UserEventResponse,
    UserLogin,
    UserProfileResponse,
    UserRegister,
    UserRegisterResponse,
    UserResponse,
    UserSegmentsResponse,
)

__all__ = [
    # ORM
    "Base",
    "User",
    "ConfigHistory",
    "FavoriteItem",
    "PriceAlert",
    "AuditLog",
    "AdminLog",
    "GlobalSetting",
    "UserRoleEnum",
    "AdminLogEventEnum",
    "_utc_now",
    # Enums
    "OfferType",
    "ConfigMode",
    # Entities
    "UserEntity",
    "ConfigHistoryEntity",
    "FavoriteItemEntity",
    "PriceAlertEntity",
    # Schemas
    "ServerInfo",
    "Offer",
    "OffersResponse",
    "SearchParams",
    "LavkaSummary",
    "LavkaItem",
    "LavkaDetail",
    "ConfigGenerateRequest",
    "ConfigItemResponse",
    "ConfigStatsResponse",
    "ConfigGenerateResponse",
    "ConfigHistoryResponse",
    "ConfigDetailResponse",
    "UserRegister",
    "UserLogin",
    "TelegramLoginRequest",
    "TokenResponse",
    "UserResponse",
    "UserRegisterResponse",
    "EmailVerificationRequest",
    "EmailVerificationTokenRequest",
    "UserProfileResponse",
    "FavoriteItemCreate",
    "FavoriteItemResponse",
    "PriceAlertCreate",
    "PriceAlertResponse",
    "AdminUserResponse",
    "AdminLogResponse",
    "AuditLogResponse",
    "AdminStatsSummary",
    "AdminStatsChartData",
    "GlobalSettingResponse",
    "GlobalSettingUpdate",
    # Metrics
    "EventCategory",
    "SessionStartRequest",
    "SessionStartResponse",
    "SessionEndRequest",
    "SessionEndResponse",
    "PageViewRequest",
    "PageViewResponse",
    "UserEventRequest",
    "UserEventResponse",
    "ConversionRequest",
    "ConversionResponse",
    "MetricsOverviewResponse",
    "EngagementMetricsResponse",
    "ConversionMetricsResponse",
    "UserSegmentsResponse",
    "MetricsExportResponse",
    "AdminMetricsQueryParams",
]
