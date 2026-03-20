"""
Redis connection and session management.
"""

import asyncio
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from config import get_settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis manager singleton for caching and session management."""

    _instance = None
    _redis_client: Optional[aioredis.Redis] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        settings = get_settings()

        try:
            self._redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=30,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                max_connections=20,
                retry_on_error=[ConnectionError, TimeoutError],
            )

            # Test connection
            await self._redis_client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()

    def get_client(self) -> Optional[aioredis.Redis]:
        """Get Redis client instance."""
        return self._redis_client

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self._redis_client:
            return None
        return await self._redis_client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        if not self._redis_client:
            return False

        ttl = ex or get_settings().REDIS_CACHE_TTL_SECONDS
        try:
            await self._redis_client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._redis_client:
            return False
        return bool(await self._redis_client.delete(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._redis_client:
            return False
        return bool(await self._redis_client.exists(key))

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key."""
        if not self._redis_client:
            return False
        return bool(await self._redis_client.expire(key, ttl))

    async def hset(
        self, name: str, key: str, value: str, ex: Optional[int] = None
    ) -> bool:
        """Set hash value in Redis."""
        if not self._redis_client:
            return False

        try:
            await self._redis_client.hset(name, key, value)
            if ex:
                await self._redis_client.expire(name, ex)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {name}:{key} in Redis: {e}")
            return False

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash value from Redis."""
        if not self._redis_client:
            return None
        return await self._redis_client.hget(name, key)

    async def hgetall(self, name: str) -> dict:
        """Get all hash values from Redis."""
        if not self._redis_client:
            return {}
        return await self._redis_client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields from Redis."""
        if not self._redis_client:
            return 0
        return await self._redis_client.hdel(name, *keys)


# Global instance
_redis_manager_instance: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """Get Redis manager instance."""
    global _redis_manager_instance
    if _redis_manager_instance is None:
        _redis_manager_instance = RedisManager()
    return _redis_manager_instance


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Get Redis client instance."""
    manager = get_redis_manager()
    return manager.get_client()
