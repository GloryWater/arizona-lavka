"""
Сервис для работы с данными marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from cachetools import TTLCache

from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись кэша с данными и временем."""
    data: List[dict]
    timestamp: datetime


class MarketplaceService:
    """
    Сервис для получения и кэширования данных marketplace.

    Особенности:
    - TTL кэширование (30 секунд)
    - Thread-safe операции с асинхронным lock
    - Graceful error handling
    """

    def __init__(self, settings: Settings):
        """
        Инициализация сервиса.

        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self._cache: TTLCache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL_SECONDS
        )
        self._cache_key = "marketplace_data"
        self._lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Получает или создаёт HTTP клиент."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.settings.API_TIMEOUT_SECONDS,
                headers={"User-Agent": "ArizonaLavka/3.0"},
                follow_redirects=True,
            )
        return self._http_client

    async def close(self) -> None:
        """Закрывает HTTP клиент."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def fetch_data(self) -> List[dict]:
        """
        Получает данные из внешнего API с кэшированием.

        Returns:
            Список данных пользователей из API
        """
        # Проверка кэша
        async with self._lock:
            if self._cache_key in self._cache:
                entry: CacheEntry = self._cache[self._cache_key]
                age = (datetime.utcnow() - entry.timestamp).total_seconds()
                logger.info(f"Кэш hit (возраст: {age:.1f}с)")
                return entry.data

        # Получение данных из API
        try:
            client = await self._get_client()
            response = await client.get(self.settings.EXTERNAL_API_URL)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                logger.error(f"Ожидался список, получено: {type(data)}")
                return []

            # Сохранение в кэш
            async with self._lock:
                self._cache[self._cache_key] = CacheEntry(
                    data=data,
                    timestamp=datetime.utcnow()
                )

            logger.info(f"Данные получены из API: {len(data)} пользователей")
            return data

        except httpx.TimeoutException:
            logger.error("Timeout при запросе к внешнему API")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от внешней API: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к внешнему API: {e}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return []

    def clear_cache(self) -> bool:
        """Очищает кэш API."""
        self._cache.clear()
        logger.info("Кэш очищен")
        return True

    def is_cache_available(self) -> bool:
        """Проверяет наличие данных в кэше."""
        return self._cache_key in self._cache

    def get_cache_age(self) -> Optional[float]:
        """Получает возраст кэша в секундах."""
        if self._cache_key not in self._cache:
            return None

        entry: CacheEntry = self._cache[self._cache_key]
        return (datetime.utcnow() - entry.timestamp).total_seconds()
