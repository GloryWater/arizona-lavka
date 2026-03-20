"""
Arizona Lavka Marketplace - Prometheus Metrics.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Модуль для сбора и экспорта метрик Prometheus.
"""

import time
from typing import Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    multiprocess,
)

# =============================================================================
# Registry
# =============================================================================

# Основной реестр для всех метрик приложения
registry = CollectorRegistry()

# Для многопроцессного режима (если используется с gunicorn/uvicorn workers)
MULTIPROC_DIR: Optional[str] = None


def setup_multiproc_mode(multiproc_dir: str) -> None:
    """
    Настраивает многопроцессный режим для Prometheus.

    Args:
        multiproc_dir: Директория для хранения метрик между процессами
    """
    global MULTIPROC_DIR
    MULTIPROC_DIR = multiproc_dir
    import os

    os.environ["PROMETHEUS_MULTIPROC_DIR"] = multiproc_dir


# =============================================================================
# HTTP Metrics
# =============================================================================

# Счётчик HTTP запросов
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

# Гистограмма длительности HTTP запросов
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

# Сводка (Summary) для перцентилей
http_request_duration_summary = Summary(
    "http_request_duration_summary_seconds",
    "HTTP request duration summary (percentiles)",
    ["method", "endpoint"],
    registry=registry,
)

# Счётчик запросов по статусам
http_responses_total = Counter(
    "http_responses_total",
    "Total HTTP responses by status code",
    ["status_code", "status_category"],
    registry=registry,
)

# Гейз для активных запросов
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method"],
    registry=registry,
)


# =============================================================================
# Business Metrics - Authentication
# =============================================================================

auth_logins_total = Counter(
    "auth_logins_total",
    "Total login attempts",
    ["status", "method"],  # status: success/failure, method: password/telegram
    registry=registry,
)

auth_registrations_total = Counter(
    "auth_registrations_total",
    "Total registration attempts",
    ["status"],  # status: success/failure
    registry=registry,
)

auth_token_refreshes_total = Counter(
    "auth_token_refreshes_total",
    "Total token refresh operations",
    ["status"],
    registry=registry,
)

auth_email_verifications_total = Counter(
    "auth_email_verifications_total",
    "Total email verification attempts",
    ["status"],
    registry=registry,
)

# Активные сессии
active_user_sessions = Gauge(
    "active_user_sessions",
    "Number of active user sessions",
    registry=registry,
)


# =============================================================================
# Business Metrics - Marketplace
# =============================================================================

marketplace_offers_fetched_total = Counter(
    "marketplace_offers_fetched_total",
    "Total marketplace data fetch operations",
    ["status"],  # status: success/failure/cache_hit
    registry=registry,
)

marketplace_offers_count = Gauge(
    "marketplace_offers_count",
    "Current number of offers in cache",
    ["type"],  # type: buy/sell/total
    registry=registry,
)

marketplace_cache_age_seconds = Gauge(
    "marketplace_cache_age_seconds",
    "Age of marketplace cache in seconds",
    registry=registry,
)

marketplace_circuit_breaker_state = Gauge(
    "marketplace_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    registry=registry,
)

marketplace_search_requests_total = Counter(
    "marketplace_search_requests_total",
    "Total marketplace search requests",
    ["server_id"],
    registry=registry,
)

marketplace_lavka_requests_total = Counter(
    "marketplace_lavka_requests_total",
    "Total lavka detail requests",
    registry=registry,
)


# =============================================================================
# Business Metrics - Config Generator
# =============================================================================

config_generations_total = Counter(
    "config_generations_total",
    "Total config generation requests",
    ["status", "mode"],  # status: success/failure, mode: SELL/BUY
    registry=registry,
)

config_items_generated_total = Counter(
    "config_items_generated_total",
    "Total items generated in configs",
    ["mode"],
    registry=registry,
)

config_history_saves_total = Counter(
    "config_history_saves_total",
    "Total configs saved to history",
    registry=registry,
)

config_downloads_total = Counter(
    "config_downloads_total",
    "Total config downloads",
    registry=registry,
)

config_generation_duration_seconds = Histogram(
    "config_generation_duration_seconds",
    "Config generation duration in seconds",
    ["mode"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=registry,
)


# =============================================================================
# Business Metrics - User
# =============================================================================

user_favorites_total = Gauge(
    "user_favorites_total",
    "Total favorite items across all users",
    registry=registry,
)

user_price_alerts_total = Gauge(
    "user_price_alerts_total",
    "Total price alerts across all users",
    registry=registry,
)

user_price_alerts_triggered_total = Counter(
    "user_price_alerts_triggered_total",
    "Total triggered price alerts",
    registry=registry,
)


# =============================================================================
# Database Metrics
# =============================================================================

db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["status"],  # status: success/error
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry,
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=registry,
)

db_connections_total = Counter(
    "db_connections_total",
    "Total database connections created",
    registry=registry,
)


# =============================================================================
# External API Metrics
# =============================================================================

external_api_requests_total = Counter(
    "external_api_requests_total",
    "Total external API requests",
    ["api", "status"],  # api: marketplace/telegram/etc
    registry=registry,
)

external_api_request_duration_seconds = Histogram(
    "external_api_request_duration_seconds",
    "External API request duration in seconds",
    ["api"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=registry,
)

external_api_circuit_breaker = Gauge(
    "external_api_circuit_breaker",
    "External API circuit breaker state",
    ["api"],
    registry=registry,
)


# =============================================================================
# Security Metrics
# =============================================================================

security_blocked_ips = Gauge(
    "security_blocked_ips",
    "Number of currently blocked IP addresses",
    registry=registry,
)

security_suspicious_activities_total = Counter(
    "security_suspicious_activities_total",
    "Total suspicious activities detected",
    ["type"],  # type: suspicious_login/brute_force/spam
    registry=registry,
)

security_turnstile_verifications_total = Counter(
    "security_turnstile_verifications_total",
    "Total Cloudflare Turnstile verification attempts",
    ["status"],  # status: success/failure
    registry=registry,
)


# =============================================================================
# Application Metrics
# =============================================================================

app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
    registry=registry,
)

app_info = Gauge(
    "app_info",
    "Application information",
    ["version", "environment"],
    registry=registry,
)

app_workers = Gauge(
    "app_workers",
    "Number of application workers",
    registry=registry,
)


# =============================================================================
# Helper Functions
# =============================================================================


def get_metrics() -> bytes:
    """
    Получает все метрики в формате Prometheus.

    Returns:
        bytes: Метрики в текстовом формате
    """
    if MULTIPROC_DIR:
        from prometheus_client import multiprocess

        multiprocess.MultiProcessCollector(MULTIPROC_DIR, registry)

    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Получает Content-Type для метрик."""
    return CONTENT_TYPE_LATEST


def record_request_duration(
    method: str,
    endpoint: str,
    duration: float,
) -> None:
    """
    Записывает длительность запроса.

    Args:
        method: HTTP метод
        endpoint: Endpoint path
        duration: Длительность в секундах
    """
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)

    http_request_duration_summary.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)


def record_http_request(
    method: str,
    endpoint: str,
    status: int,
) -> None:
    """
    Записывает HTTP запрос.

    Args:
        method: HTTP метод
        endpoint: Endpoint path
        status: HTTP статус код
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status,
    ).inc()

    # Категоризация по статусам
    if 200 <= status < 300:
        category = "2xx"
    elif 300 <= status < 400:
        category = "3xx"
    elif 400 <= status < 500:
        category = "4xx"
    else:
        category = "5xx"

    http_responses_total.labels(
        status_code=status,
        status_category=category,
    ).inc()


def start_request_timer(method: str) -> float:
    """
    Начинает таймер для запроса.

    Args:
        method: HTTP метод

    Returns:
        float: Время начала
    """
    http_requests_in_progress.labels(method=method).inc()
    return time.time()


def end_request_timer(method: str) -> None:
    """
    Завершает таймер запроса.

    Args:
        method: HTTP метод
    """
    http_requests_in_progress.labels(method=method).dec()


def set_app_info(version: str, environment: str) -> None:
    """
    Устанавливает информацию о приложении.

    Args:
        version: Версия приложения
        environment: Окружение (production/development)
    """
    app_info.labels(version=version, environment=environment).set(1)
    app_uptime_seconds.set_function(lambda: time.time() - app_start_time)


# Время запуска приложения
app_start_time: float = time.time()


# =============================================================================
# Context Manager для тайминга запросов
# =============================================================================


class RequestTimer:
    """
    Контекстный менеджер для замера длительности запросов.

    Usage:
        with RequestTimer(method, endpoint) as timer:
            # обработка запроса
        timer.record()  # запись метрик
    """

    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.start_time: float = 0.0
        self.duration: float = 0.0

    def __enter__(self) -> "RequestTimer":
        self.start_time = time.time()
        http_requests_in_progress.labels(method=self.method).inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.duration = time.time() - self.start_time
        http_requests_in_progress.labels(method=self.method).dec()

    def record(self, status: int) -> None:
        """Записывает метрики запроса."""
        record_http_request(self.method, self.endpoint, status)
        record_request_duration(self.method, self.endpoint, self.duration)
