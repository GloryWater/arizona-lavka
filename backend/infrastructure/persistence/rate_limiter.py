"""
Rate Limiter с поддержкой Redis и in-memory fallback.

Перемещён из корня в infrastructure/persistence.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from config import Settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None


@dataclass
class RateLimitResult:
    """Результат проверки rate limit."""
    allowed: bool
    remaining: int
    reset_after: float
    retry_after: Optional[float] = None


class RateLimiterBase(ABC):
    """Базовый класс для rate limiter."""

    @abstractmethod
    async def check_rate_limit(self, identifier: str) -> RateLimitResult:
        pass

    @abstractmethod
    async def reset(self, identifier: str) -> bool:
        pass


class InMemoryRateLimiter(RateLimiterBase):
    """In-memory rate limiter с sliding window."""

    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._store: Dict[str, list] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 60

    async def check_rate_limit(self, identifier: str) -> RateLimitResult:
        current_time = time.time()

        async with self._lock:
            # Периодическая очистка
            if current_time - self._last_cleanup > self._cleanup_interval:
                await self._cleanup()

            if identifier not in self._store:
                self._store[identifier] = []

            # Удаляем старые записи за пределами окна
            window_start = current_time - self.window_seconds
            self._store[identifier] = [
                ts for ts in self._store[identifier]
                if ts > window_start
            ]

            request_count = len(self._store[identifier])

            if request_count >= self.limit:
                oldest_timestamp = min(self._store[identifier]) if self._store[identifier] else current_time
                reset_after = (oldest_timestamp + self.window_seconds) - current_time
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_after=max(0, reset_after),
                    retry_after=max(0, reset_after),
                )

            # Добавляем текущий запрос
            self._store[identifier].append(current_time)
            remaining = self.limit - len(self._store[identifier])

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_after=self.window_seconds,
            )

    async def reset(self, identifier: str) -> bool:
        async with self._lock:
            if identifier in self._store:
                del self._store[identifier]
            return True

    async def _cleanup(self) -> None:
        current_time = time.time()
        window_start = current_time - self.window_seconds

        to_delete = []
        for identifier, timestamps in self._store.items():
            self._store[identifier] = [ts for ts in timestamps if ts > window_start]
            if not self._store[identifier]:
                to_delete.append(identifier)

        for identifier in to_delete:
            del self._store[identifier]

        self._last_cleanup = current_time


class RedisRateLimiter(RateLimiterBase):
    """Redis-based rate limiter с sliding window log."""

    def __init__(
        self,
        redis_client: "aioredis.Redis",
        limit: int,
        window_seconds: int = 60,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis_client
        self.limit = limit
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    async def check_rate_limit(self, identifier: str) -> RateLimitResult:
        current_time = time.time()
        key = f"{self.key_prefix}:{identifier}"
        window_start = current_time - self.window_seconds

        async with self.redis.pipeline(transaction=True) as pipe:
            while True:
                try:
                    await pipe.zremrangebyscore(key, 0, window_start)
                    await pipe.zcard(key)
                    results = await pipe.execute()
                    break
                except Exception:
                    await pipe.reset()
                    raise

            current_count = results[1]

            if current_count >= self.limit:
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    reset_after = (oldest_timestamp + self.window_seconds) - current_time
                else:
                    reset_after = self.window_seconds

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_after=max(0, reset_after),
                    retry_after=max(0, reset_after),
                )

            async with self.redis.pipeline(transaction=True) as pipe2:
                while True:
                    try:
                        request_id = f"{current_time}:{id(self)}:{hash(current_time)}"
                        await pipe2.zadd(key, {request_id: current_time})
                        await pipe2.expire(key, self.window_seconds * 2)
                        await pipe2.execute()
                        break
                    except Exception:
                        await pipe2.reset()
                        raise

            remaining = self.limit - current_count - 1

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_after=self.window_seconds,
            )

    async def reset(self, identifier: str) -> bool:
        key = f"{self.key_prefix}:{identifier}"
        await self.redis.delete(key)
        return True


# Global instance
_rate_limiter_instance: Optional[RateLimiterBase] = None
_rate_limiter_lock = asyncio.Lock()


async def get_rate_limiter() -> RateLimiterBase:
    """Получает или создаёт rate limiter (singleton)."""
    global _rate_limiter_instance

    if _rate_limiter_instance is not None:
        return _rate_limiter_instance

    async with _rate_limiter_lock:
        if _rate_limiter_instance is not None:
            return _rate_limiter_instance

        settings = get_settings()
        redis_url = getattr(settings, 'REDIS_URL', None)

        # Пробуем создать Redis limiter если доступен
        if redis_url and REDIS_AVAILABLE:
            try:
                redis_client = await aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await redis_client.ping()
                _rate_limiter_instance = RedisRateLimiter(
                    redis_client=redis_client,
                    limit=settings.RATE_LIMIT_PER_MINUTE,
                    window_seconds=60,
                    key_prefix="arizonalavka:ratelimit",
                )
                return _rate_limiter_instance
            except Exception:
                pass

        # In-memory fallback
        _rate_limiter_instance = InMemoryRateLimiter(
            limit=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        )
        return _rate_limiter_instance


async def reset_rate_limiter() -> None:
    """Сбрасывает экземпляр (для тестов)."""
    global _rate_limiter_instance
    async with _rate_limiter_lock:
        if _rate_limiter_instance is not None:
            if isinstance(_rate_limiter_instance, RedisRateLimiter):
                await _rate_limiter_instance.redis.close()
            _rate_limiter_instance = None


# Импортируем здесь чтобы избежать circular imports
from config import get_settings
