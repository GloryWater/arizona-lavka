"""
Cache service for Redis-based caching operations.
"""

import json
import logging
from typing import Any, Optional, Union

from infrastructure.cache.redis_connection import get_redis_manager
from infrastructure.cache.application_cache import get_application_cache

logger = logging.getLogger(__name__)


class CacheService:
    """Service for handling caching operations with Redis and in-memory fallback."""

    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.app_cache = get_application_cache()

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        try:
            # Use the application cache which handles both Redis and memory
            return await self.app_cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with optional TTL."""
        try:
            # Use the application cache which handles both Redis and memory
            return await self.app_cache.set(key, value, ttl=ttl)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached value by key."""
        try:
            # Use the application cache which handles both Redis and memory
            return await self.app_cache.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if cached value exists."""
        try:
            # Use the application cache which handles both Redis and memory
            return await self.app_cache.exists(key)
        except Exception as e:
            logger.error(f"Error checking existence of cache for key {key}: {e}")
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple cached values."""
        results = {}
        for key in keys:
            value = await self.get(key)
            results[key] = value
        return results

    async def set_many(self, data: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple cached values."""
        try:
            for key, value in data.items():
                await self.set(key, value, ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting multiple cache values: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all cached values matching a pattern."""
        try:
            # Use the application cache which handles both Redis and memory
            return await self.app_cache.clear_pattern(pattern)
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a cached integer value."""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return 0

            return await redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing cache value for key {key}: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a cached integer value."""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return 0

            return await redis_client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing cache value for key {key}: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a cached value."""
        try:
            return await self.redis_manager.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            return self.app_cache.get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# Global instance
_cache_service_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get cache service instance."""
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    return _cache_service_instance
