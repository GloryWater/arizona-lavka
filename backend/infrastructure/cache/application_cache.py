"""
Enhanced application-level caching service with multiple strategies and decorators.

This module provides a comprehensive caching solution for the Arizona Lavka Marketplace
with support for Redis, in-memory cache, and various caching strategies.
"""

import asyncio
import json
import logging
import pickle
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

import redis.asyncio as aioredis
from cachetools import TTLCache

from config import get_settings
from infrastructure.cache.redis_connection import get_redis_manager

logger = logging.getLogger(__name__)

# Generic type for decorator
T = TypeVar('T')


class CacheStrategy:
    """Enumeration of available caching strategies."""
    TTL = "ttl"
    INFINITE = "infinite"
    SLIDING = "sliding"
    WRITE_THROUGH = "write_through"
    READ_THROUGH = "read_through"


class ApplicationCache:
    """Enhanced application-level cache with multiple backends and strategies."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_manager = get_redis_manager()
        
        # In-memory cache as fallback
        self.memory_cache = TTLCache(
            maxsize=self.settings.CACHE_MAX_SIZE,
            ttl=self.settings.CACHE_TTL_SECONDS
        )
        
        # Track cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        # Cache prefixes for different entities
        self.prefixes = {
            'user': 'user:',
            'config': 'config:',
            'marketplace': 'marketplace:',
            'session': 'session:',
            'rate_limit': 'rate_limit:',
            'general': 'general:'
        }

    async def initialize(self):
        """Initialize the cache instance and perform warmup if enabled."""
        try:
            # Initialize Redis connection
            await self.redis_manager.initialize()
            logger.info("Application cache initialized with Redis backend")
            
            # Warm up cache if enabled
            if self.settings.CACHE_WARMUP_ON_STARTUP:
                await self._warmup_cache()
        except Exception as e:
            logger.error(f"Error initializing application cache: {e}")
            if self.settings.CACHE_FALLBACK_TO_MEMORY:
                logger.warning("Falling back to memory cache only")
            else:
                raise

    async def _warmup_cache(self):
        """Warm up the cache with commonly accessed data."""
        logger.info("Warming up application cache...")
        
        # Example: Preload common configuration data
        try:
            # This would preload commonly accessed data into cache
            # Implementation would depend on specific application needs
            logger.info("Cache warmup completed")
        except Exception as e:
            logger.error(f"Error during cache warmup: {e}")

    async def get(self, key: str, use_redis: bool = True) -> Optional[Any]:
        """Get value from cache with fallback to memory cache."""
        # Try Redis first
        if use_redis:
            try:
                value = await self.redis_manager.get(key)
                if value is not None:
                    self.stats['hits'] += 1
                    return self._deserialize(value)
            except Exception as e:
                logger.warning(f"Redis get error for key {key}: {e}")
                # Fallback to memory cache
                pass
        
        # Try memory cache
        try:
            if key in self.memory_cache:
                self.stats['hits'] += 1
                return self.memory_cache[key]
        except KeyError:
            pass
        
        self.stats['misses'] += 1
        return None

    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        use_redis: bool = True
    ) -> bool:
        """Set value in cache with optional TTL."""
        serialized_value = self._serialize(value)
        
        success = True
        if use_redis:
            try:
                ttl = ttl or self.settings.REDIS_CACHE_TTL_SECONDS
                await self.redis_manager.set(key, serialized_value, ex=ttl)
            except Exception as e:
                logger.warning(f"Redis set error for key {key}: {e}")
                success = False
        
        # Always set in memory cache as backup
        try:
            self.memory_cache[key] = value
        except Exception as e:
            logger.error(f"Memory cache set error for key {key}: {e}")
            success = False
        
        if success:
            self.stats['sets'] += 1
        
        return success

    async def delete(self, key: str, use_redis: bool = True) -> bool:
        """Delete value from cache."""
        success = True
        
        if use_redis:
            try:
                await self.redis_manager.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error for key {key}: {e}")
                success = False
        
        # Remove from memory cache
        try:
            if key in self.memory_cache:
                del self.memory_cache[key]
        except KeyError:
            pass
        
        if success:
            self.stats['deletes'] += 1
        
        return success

    async def clear_pattern(self, pattern: str, use_redis: bool = True) -> int:
        """Clear all keys matching a pattern."""
        deleted_count = 0
        
        if use_redis:
            try:
                redis_client = self.redis_manager.get_client()
                if redis_client:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        deleted_count = await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear pattern error for {pattern}: {e}")
        
        # Clear from memory cache
        keys_to_remove = [key for key in self.memory_cache if pattern.replace('*', '') in key]
        for key in keys_to_remove:
            try:
                del self.memory_cache[key]
                deleted_count += 1
            except KeyError:
                pass
        
        return deleted_count

    async def exists(self, key: str, use_redis: bool = True) -> bool:
        """Check if key exists in cache."""
        if use_redis:
            try:
                exists = await self.redis_manager.exists(key)
                if exists:
                    return True
            except Exception as e:
                logger.warning(f"Redis exists error for key {key}: {e}")
        
        return key in self.memory_cache

    def _serialize(self, obj: Any) -> str:
        """Serialize object for storage."""
        try:
            # Try JSON serialization first (for simple objects)
            return json.dumps(obj, default=str)
        except TypeError:
            # Fall back to pickle for complex objects
            return pickle.dumps(obj).hex()

    def _deserialize(self, data: str) -> Any:
        """Deserialize object from storage."""
        try:
            # Try JSON deserialization first
            return json.loads(data)
        except json.JSONDecodeError:
            try:
                # Fall back to pickle deserialization
                return pickle.loads(bytes.fromhex(data))
            except Exception:
                # Return as string if all else fails
                return data

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.stats.copy()

    def get_cache_key(self, entity_type: str, identifier: str) -> str:
        """Generate standardized cache key."""
        prefix = self.prefixes.get(entity_type, self.prefixes['general'])
        return f"{prefix}{identifier}"


# Global cache instance
_cache_instance: Optional[ApplicationCache] = None


def get_application_cache() -> ApplicationCache:
    """Get the global application cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ApplicationCache()
    return _cache_instance


def cache_result(
    ttl: int = 300,  # 5 minutes default
    key_prefix: str = "",
    cache_strategy: str = CacheStrategy.TTL,
    entity_type: str = "general"
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        cache_strategy: Strategy to use for caching
        entity_type: Type of entity being cached
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key from function name and arguments
            cache_key = _generate_cache_key(func.__name__, args, kwargs, key_prefix, entity_type)
            
            cache = get_application_cache()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result
            
            logger.debug(f"Cache MISS for key: {cache_key}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Set in cache
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func_name: str, 
    args: Tuple, 
    kwargs: Dict, 
    key_prefix: str, 
    entity_type: str
) -> str:
    """Generate a unique cache key based on function and parameters."""
    import hashlib
    
    # Create a string representation of args and kwargs
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))
    
    # Create a hash of the parameters to keep key length manageable
    params_hash = hashlib.md5((args_str + kwargs_str).encode()).hexdigest()[:16]
    
    # Construct the key
    full_key = f"{key_prefix}:{func_name}:{params_hash}"
    
    # Use the cache instance to get the proper prefixed key
    cache = get_application_cache()
    return cache.get_cache_key(entity_type, full_key)


def invalidate_cache(
    key_prefix: str = "",
    entity_type: str = "general"
):
    """
    Decorator to invalidate cache entries after function execution.
    
    Args:
        key_prefix: Prefix of keys to invalidate
        entity_type: Type of entity whose cache should be invalidated
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = get_application_cache()
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Invalidate related cache entries
            if key_prefix:
                pattern = f"{cache.get_cache_key(entity_type, key_prefix)}*"
                await cache.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# Predefined cache instances for common use cases
class UserCache:
    """Specialized cache for user-related data."""
    
    def __init__(self):
        self.cache = get_application_cache()
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile from cache."""
        key = self.cache.get_cache_key('user', f'profile:{user_id}')
        return await self.cache.get(key)
    
    async def set_user_profile(self, user_id: int, profile: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set user profile in cache."""
        key = self.cache.get_cache_key('user', f'profile:{user_id}')
        return await self.cache.set(key, profile, ttl=ttl)
    
    async def invalidate_user_profile(self, user_id: int) -> bool:
        """Invalidate user profile cache."""
        key = self.cache.get_cache_key('user', f'profile:{user_id}')
        return await self.cache.delete(key)


class ConfigCache:
    """Specialized cache for configuration data."""
    
    def __init__(self):
        self.cache = get_application_cache()
    
    async def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration from cache."""
        key = self.cache.get_cache_key('config', f'data:{config_id}')
        return await self.cache.get(key)
    
    async def set_config(self, config_id: str, config: Dict[str, Any], ttl: int = 1800) -> bool:
        """Set configuration in cache."""
        key = self.cache.get_cache_key('config', f'data:{config_id}')
        return await self.cache.set(key, config, ttl=ttl)
    
    async def invalidate_config(self, config_id: str) -> bool:
        """Invalidate configuration cache."""
        key = self.cache.get_cache_key('config', f'data:{config_id}')
        return await self.cache.delete(key)


class MarketplaceCache:
    """Specialized cache for marketplace data."""
    
    def __init__(self):
        self.cache = get_application_cache()
    
    async def get_marketplace_data(self, server_id: int, mode: str) -> Optional[Dict[str, Any]]:
        """Get marketplace data from cache."""
        key = self.cache.get_cache_key('marketplace', f'data:{server_id}:{mode}')
        return await self.cache.get(key)
    
    async def set_marketplace_data(
        self, 
        server_id: int, 
        mode: str, 
        data: Dict[str, Any], 
        ttl: int = 300
    ) -> bool:
        """Set marketplace data in cache."""
        key = self.cache.get_cache_key('marketplace', f'data:{server_id}:{mode}')
        return await self.cache.set(key, data, ttl=ttl)
    
    async def invalidate_marketplace_data(self, server_id: int, mode: str) -> bool:
        """Invalidate marketplace data cache."""
        key = self.cache.get_cache_key('marketplace', f'data:{server_id}:{mode}')
        return await self.cache.delete(key)