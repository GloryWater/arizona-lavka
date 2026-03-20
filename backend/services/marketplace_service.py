"""
Сервис для работы с данными marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from cachetools import TTLCache

from config import Settings
from metrics.prometheus import (
    external_api_circuit_breaker,
    external_api_request_duration_seconds,
    external_api_requests_total,
    marketplace_cache_age_seconds,
    marketplace_circuit_breaker_state,
    marketplace_offers_count,
    marketplace_offers_fetched_total,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Возвращает текущее UTC время (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class CacheEntry:
    """Запись кэша с данными и временем."""

    data: List[dict]
    timestamp: datetime


def _sanitize_item_name(name: str) -> str:
    """
    Санитизирует название предмета для защиты от XSS.

    Args:
        name: Название предмета из внешнего API

    Returns:
        str: Санитизированное название с экранированными HTML-сущностями
    """
    if not name:
        return name
    # Экранируем основные HTML-сущности
    return (
        name.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


@dataclass
class CircuitBreakerState:
    """Состояние circuit breaker для внешнего API."""

    failure_count: int = 0
    success_count: int = 0  # Явный счётчик успехов для half-open состояния
    last_failure_time: Optional[float] = None
    state: str = "closed"  # closed, open, half-open
    last_state_change: float = 0.0
    total_requests: int = 0  # Общее количество запросов для метрик
    total_failures: int = 0  # Общее количество неудач для метрик
    total_successes: int = 0  # Общее количество успехов для метрик

    FAILURE_THRESHOLD: int = 5  # Количество неудач до открытия
    SUCCESS_THRESHOLD: int = 2  # Количество успехов для закрытия
    TIMEOUT_SECONDS: float = 60.0  # Время ожидания перед полуоткрытием

    def get_metrics(self) -> dict:
        """
        Получает метрики circuit breaker.

        Returns:
            dict: Метрики для мониторинга
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(self.total_requests, 1),
            "last_state_change": (
                datetime.fromtimestamp(self.last_state_change).isoformat()
                if self.last_state_change
                else None
            ),
        }


class MarketplaceService:
    """
    Сервис для получения и кэширования данных marketplace.

    Особенности:
    - TTL кэширование (30 секунд)
    - Thread-safe операции с асинхронным lock
    - Graceful error handling
    - Circuit breaker для защиты от cascade failure
    """

    def __init__(self, settings: Settings):
        """
        Инициализация сервиса.

        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self._cache: TTLCache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL_SECONDS
        )
        self._cache_key = "marketplace_data"
        self._lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreakerState(
            state="closed", last_state_change=time.time()
        )

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
        """
        Проверяет состояние circuit breaker.

        Returns:
            bool: True если запрос разрешён, False если circuit open
        """
        import time

        cb = self._circuit_breaker
        current_time = time.time()

        if cb.state == "closed":
            return True

        if cb.state == "open":
            # Проверяем таймаут
            if current_time - cb.last_state_change >= cb.TIMEOUT_SECONDS:
                cb.state = "half-open"
                cb.last_state_change = current_time
                logger.info("Circuit breaker перешёл в half-open состояние")
                return True
            return False

        # half-open - разрешаем запрос
        return True

    def _record_success(self) -> None:
        """Записывает успешный запрос в circuit breaker."""
        cb = self._circuit_breaker
        cb.total_requests += 1
        cb.total_successes += 1

        if cb.state == "half-open":
            cb.failure_count = 0
            cb.success_count += 1
            if cb.success_count >= cb.SUCCESS_THRESHOLD:
                # Circuit breaker закрыт после успешных запросов
                cb.state = "closed"
                cb.last_state_change = time.time()
                cb.success_count = 0  # Сбрасываем после закрытия
                cb.total_failures = cb.total_failures  # Сохраняем для метрик
                logger.info("Circuit breaker закрыт после успешных запросов")
        elif cb.state == "closed":
            # Сбрасываем счётчик неудач при успешном запросе
            # Но не сбрасываем success_count чтобы избежать частых переходов
            cb.failure_count = 0

    def _record_failure(self) -> None:
        """Записывает неудачный запрос в circuit breaker."""
        import time

        cb = self._circuit_breaker
        cb.total_requests += 1
        cb.total_failures += 1
        cb.failure_count += 1
        cb.last_failure_time = time.time()

        if cb.state == "half-open":
            # Сразу возвращаем в open при неудаче
            cb.state = "open"
            cb.last_state_change = time.time()
            logger.warning("Circuit breaker открыт после неудачи в half-open")
        elif cb.state == "closed" and cb.failure_count >= cb.FAILURE_THRESHOLD:
            cb.state = "open"
            cb.last_state_change = time.time()
            logger.warning(f"Circuit breaker открыт после {cb.failure_count} неудач")

    async def fetch_data(self) -> List[dict]:
        """
        Получает данные из внешнего API с кэшированием и circuit breaker.

        Returns:
            Список данных пользователей из API

        Raises:
            RuntimeError: Если circuit breaker открыт и кэш недоступен
        """
        import time

        # Проверка кэша
        async with self._lock:
            if self._cache_key in self._cache:
                entry: CacheEntry = self._cache[self._cache_key]
                age = (_utcnow() - entry.timestamp).total_seconds()
                logger.info(f"Кэш hit (возраст: {age:.1f}с)")
                marketplace_offers_fetched_total.labels(status="cache_hit").inc()
                marketplace_cache_age_seconds.set(age)
                return entry.data

        # Проверка circuit breaker перед запросом
        if not self._check_circuit_breaker():
            logger.warning("Circuit breaker открыт - запрос к API заблокирован")
            marketplace_offers_fetched_total.labels(status="failure").inc()
            # Возвращаем устаревший кэш если есть
            if self._cache_key in self._cache:
                entry: CacheEntry = self._cache[self._cache_key]
                logger.warning(
                    f"Возвращаем устаревший кэш (возраст: {(_utcnow() - entry.timestamp).total_seconds():.1f}с)"
                )
                return entry.data
            # Критическая ошибка - нет кэша и API недоступен
            raise RuntimeError(
                "Marketplace API временно недоступен. Circuit breaker открыт. "
                "Попробуйте через 1 минуту."
            )

        # Получение данных из API
        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get(self.settings.EXTERNAL_API_URL)
            response.raise_for_status()
            data = response.json()

            # Запись метрик успешного запроса
            external_api_requests_total.labels(
                api="marketplace", status="success"
            ).inc()
            external_api_request_duration_seconds.labels(api="marketplace").observe(
                time.time() - start_time
            )

            if not isinstance(data, list):
                logger.error(f"Ожидался список, получено: {type(data)}")
                self._record_failure()
                marketplace_offers_fetched_total.labels(status="failure").inc()
                external_api_requests_total.labels(
                    api="marketplace", status="failure"
                ).inc()
                return []

            # Сохранение в кэш
            async with self._lock:
                self._cache[self._cache_key] = CacheEntry(
                    data=data, timestamp=_utcnow()
                )

            self._record_success()
            marketplace_offers_fetched_total.labels(status="success").inc()
            marketplace_offers_count.labels(type="total").set(len(data))
            logger.info(f"Данные получены из API: {len(data)} пользователей")
            return data

        except httpx.TimeoutException:
            logger.error("Timeout при запросе к внешнему API")
            self._record_failure()
            marketplace_offers_fetched_total.labels(status="failure").inc()
            external_api_requests_total.labels(
                api="marketplace", status="failure"
            ).inc()
            external_api_request_duration_seconds.labels(api="marketplace").observe(
                time.time() - start_time
            )
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от внешней API: {e.response.status_code}")
            self._record_failure()
            marketplace_offers_fetched_total.labels(status="failure").inc()
            external_api_requests_total.labels(
                api="marketplace", status="failure"
            ).inc()
            external_api_request_duration_seconds.labels(api="marketplace").observe(
                time.time() - start_time
            )
            return []
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к внешнему API: {e}")
            self._record_failure()
            marketplace_offers_fetched_total.labels(status="failure").inc()
            external_api_requests_total.labels(
                api="marketplace", status="failure"
            ).inc()
            external_api_request_duration_seconds.labels(api="marketplace").observe(
                time.time() - start_time
            )
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            self._record_failure()
            marketplace_offers_fetched_total.labels(status="failure").inc()
            external_api_requests_total.labels(
                api="marketplace", status="failure"
            ).inc()
            external_api_request_duration_seconds.labels(api="marketplace").observe(
                time.time() - start_time
            )
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
        return (_utcnow() - entry.timestamp).total_seconds()

    def get_metrics(self) -> dict:
        """
        Получает метрики сервиса marketplace.

        Returns:
            dict: Метрики для мониторинга
        """
        cache_age = self.get_cache_age()

        # Обновляем Prometheus метрики
        if cache_age is not None:
            marketplace_cache_age_seconds.set(cache_age)

        # Circuit breaker state: 0=closed, 1=open, 2=half-open
        cb_state_map = {"closed": 0, "open": 1, "half-open": 2}
        cb_state = cb_state_map.get(self._circuit_breaker.state, 0)
        marketplace_circuit_breaker_state.set(cb_state)
        external_api_circuit_breaker.labels(api="marketplace").set(cb_state)

        return {
            "circuit_breaker": self._circuit_breaker.get_metrics(),
            "cache": {
                "available": self.is_cache_available(),
                "age_seconds": cache_age,
                "ttl_seconds": self.settings.CACHE_TTL_SECONDS,
            },
        }
