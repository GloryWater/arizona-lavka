"""
Arizona Lavka Marketplace - Rate Limiter.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Note:
    Этот файл существует для обратной совместимости.
    Новый код должен использовать:
        from infrastructure.persistence.rate_limiter import ...
"""

# Импортируем всё из нового расположения
from infrastructure.persistence.rate_limiter import (
    RateLimiterBase,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimiterFactory,
    RateLimitResult,
    get_rate_limiter,
    reset_rate_limiter,
)

__all__ = [
    "RateLimiterBase",
    "InMemoryRateLimiter",
    "RedisRateLimiter",
    "RateLimiterFactory",
    "RateLimitResult",
    "get_rate_limiter",
    "reset_rate_limiter",
]
