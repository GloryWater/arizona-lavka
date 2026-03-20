"""
Infrastructure layer - Infrastructure Services.

Реализации интерфейсов для работы с БД, внешними API, кэшем.
Зависит от core и application layers.
"""

from .cache import (
    ApplicationCache,
    get_application_cache,
    cache_result,
    invalidate_cache,
    UserCache,
    ConfigCache,
    MarketplaceCache,
    CacheStrategy,
    CacheService,
    get_cache_service,
    RedisManager,
    get_redis_manager,
    SessionManager,
    get_session_manager
)

__all__ = [
    "ApplicationCache",
    "get_application_cache",
    "cache_result",
    "invalidate_cache",
    "UserCache",
    "ConfigCache",
    "MarketplaceCache",
    "CacheStrategy",
    "CacheService",
    "get_cache_service",
    "RedisManager",
    "get_redis_manager",
    "SessionManager",
    "get_session_manager",
]
