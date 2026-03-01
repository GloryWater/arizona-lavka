"""
Marketplace API implementation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import httpx
from cachetools import TTLCache

from application.interfaces.external import IMarketplaceAPI
from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись кэша с данными и временем."""
    data: List[dict]
    timestamp: datetime


def _sanitize_item_name(name: str) -> str:
    """Санитизирует название предмета для защиты от XSS."""
    if not name:
        return name
    return (name
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


class MarketplaceAPI(IMarketplaceAPI):
    """
    Реализация IMarketplaceAPI для получения данных из внешнего API.

    Особенности:
    - TTL кэширование
    - Circuit breaker для защиты от cascade failure
    - Graceful error handling
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._cache: TTLCache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL_SECONDS
        )
        self._cache_key = "marketplace_data"
        self._http_client: httpx.AsyncClient | None = None
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._circuit_state = "closed"  # closed, open, half-open
        self._last_state_change: float = 0.0

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

    def _check_circuit_breaker(self) -> bool:
        """Проверяет состояние circuit breaker."""
        import time
        current_time = time.time()

        if self._circuit_state == "closed":
            return True

        if self._circuit_state == "open":
            if current_time - self._last_state_change >= 60.0:
                self._circuit_state = "half-open"
                self._last_state_change = current_time
                logger.info("Circuit breaker перешёл в half-open состояние")
                return True
            return False

        return True

    def _record_success(self) -> None:
        """Записывает успешный запрос."""
        if self._circuit_state == "half-open":
            self._failure_count = 0
            self._circuit_state = "closed"
            logger.info("Circuit breaker закрыт после успешного запроса")
        elif self._circuit_state == "closed":
            self._failure_count = 0

    def _record_failure(self) -> None:
        """Записывает неудачный запрос."""
        import time
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._circuit_state == "half-open":
            self._circuit_state = "open"
            self._last_state_change = time.time()
            logger.warning("Circuit breaker открыт после неудачи в half-open")
        elif self._circuit_state == "closed" and self._failure_count >= 5:
            self._circuit_state = "open"
            self._last_state_change = time.time()
            logger.warning(f"Circuit breaker открыт после {self._failure_count} неудач")

    async def fetch_marketplace_data(self) -> List[dict]:
        """
        Получает данные из внешнего API с кэшированием.

        Returns:
            Список данных пользователей из API
        """
        import time

        # Проверка кэша
        if self._cache_key in self._cache:
            entry = self._cache[self._cache_key]
            age = (datetime.now(timezone.utc) - entry.timestamp).total_seconds()
            logger.info(f"Кэш hit (возраст: {age:.1f}с)")
            return entry.data

        # Проверка circuit breaker
        if not self._check_circuit_breaker():
            logger.warning("Circuit breaker открыт - запрос к API заблокирован")
            if self._cache_key in self._cache:
                entry = self._cache[self._cache_key]
                logger.warning(f"Возвращаем устаревший кэш (возраст: {(datetime.now(timezone.utc) - entry.timestamp).total_seconds():.1f}с)")
                return entry.data
            raise RuntimeError(
                "Marketplace API временно недоступен. Circuit breaker открыт. "
                "Попробуйте через 1 минуту."
            )

        # Получение данных из API
        try:
            client = await self._get_client()
            response = await client.get(self.settings.EXTERNAL_API_URL)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                logger.error(f"Ожидался список, получено: {type(data)}")
                self._record_failure()
                return []

            # Сохранение в кэш
            self._cache[self._cache_key] = CacheEntry(
                data=data,
                timestamp=datetime.now(timezone.utc)
            )

            self._record_success()
            logger.info(f"Данные получены из API: {len(data)} пользователей")
            return data

        except httpx.TimeoutException:
            logger.error("Timeout при запросе к внешнему API")
            self._record_failure()
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от внешней API: {e.response.status_code}")
            self._record_failure()
            return []
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к внешнему API: {e}")
            self._record_failure()
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            self._record_failure()
            return []

    def clear_cache(self) -> bool:
        """Очищает кэш."""
        self._cache.clear()
        logger.info("Кэш очищен")
        return True

    def is_cache_available(self) -> bool:
        """Проверяет наличие данных в кэше."""
        return self._cache_key in self._cache
