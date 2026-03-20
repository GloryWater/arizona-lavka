"""
Arizona Lavka Marketplace - Metrics Package.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

from .prometheus import (  # Auth metrics; Marketplace metrics; Config metrics; Database metrics; External API metrics; Security metrics; App metrics
    RequestTimer,
    active_user_sessions,
    app_info,
    app_uptime_seconds,
    app_workers,
    auth_email_verifications_total,
    auth_logins_total,
    auth_registrations_total,
    auth_token_refreshes_total,
    config_downloads_total,
    config_generation_duration_seconds,
    config_generations_total,
    config_history_saves_total,
    config_items_generated_total,
    db_connections_active,
    db_connections_total,
    db_queries_total,
    db_query_duration_seconds,
    end_request_timer,
    external_api_circuit_breaker,
    external_api_request_duration_seconds,
    external_api_requests_total,
    get_metrics,
    get_metrics_content_type,
    marketplace_cache_age_seconds,
    marketplace_circuit_breaker_state,
    marketplace_lavka_requests_total,
    marketplace_offers_count,
    marketplace_offers_fetched_total,
    marketplace_search_requests_total,
    record_http_request,
    record_request_duration,
    registry,
    security_blocked_ips,
    security_suspicious_activities_total,
    security_turnstile_verifications_total,
    set_app_info,
    start_request_timer,
)

__all__ = [
    "registry",
    "get_metrics",
    "get_metrics_content_type",
    "record_http_request",
    "record_request_duration",
    "start_request_timer",
    "end_request_timer",
    "set_app_info",
    "RequestTimer",
    # Auth
    "auth_logins_total",
    "auth_registrations_total",
    "auth_token_refreshes_total",
    "auth_email_verifications_total",
    "active_user_sessions",
    # Marketplace
    "marketplace_offers_fetched_total",
    "marketplace_offers_count",
    "marketplace_cache_age_seconds",
    "marketplace_circuit_breaker_state",
    "marketplace_search_requests_total",
    "marketplace_lavka_requests_total",
    # Config
    "config_generations_total",
    "config_items_generated_total",
    "config_history_saves_total",
    "config_downloads_total",
    "config_generation_duration_seconds",
    # Database
    "db_queries_total",
    "db_query_duration_seconds",
    "db_connections_active",
    "db_connections_total",
    # External API
    "external_api_requests_total",
    "external_api_request_duration_seconds",
    "external_api_circuit_breaker",
    # Security
    "security_blocked_ips",
    "security_suspicious_activities_total",
    "security_turnstile_verifications_total",
    # App
    "app_uptime_seconds",
    "app_info",
    "app_workers",
]
