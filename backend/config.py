"""
Конфигурация приложения Arizona Lavka Marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import os
import secrets
import warnings
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.secrets_manager import get_secret


def _get_secret_or_env(
    secret_name: str, env_name: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Получает секрет из безопасного хранилища, Docker secret файла или переменной окружения.

    Приоритет:
    1. Secure secrets manager
    2. Docker secret файл (если указан *_FILE)
    3. Переменная окружения
    4. Значение по умолчанию
    """
    # First, try to get from secure secrets manager
    secret_value = get_secret(secret_name.lower(), None)
    if secret_value:
        return secret_value

    # Then check Docker secret file
    file_env = f"{env_name}_FILE"
    secret_file = os.environ.get(file_env)
    if secret_file:
        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except (IOError, OSError):
            pass

    # Then check environment variable
    env_value = os.environ.get(env_name)
    if env_value:
        return env_value

    return default


class Settings(BaseSettings):
    """
    Настройки приложения из переменных окружения.

    Attributes:
        APP_NAME: Название приложения
        APP_VERSION: Версия приложения
        DEBUG: Режим отладки
        HOST: Хост для запуска сервера
        PORT: Порт для запуска сервера

        POSTGRES_USER: Пользователь PostgreSQL
        POSTGRES_PASSWORD: Пароль PostgreSQL
        POSTGRES_DB: Имя базы данных PostgreSQL
        POSTGRES_HOST: Хост PostgreSQL
        POSTGRES_PORT: Порт PostgreSQL

        JWT_SECRET_KEY: Секретный ключ для JWT
        JWT_ALGORITHM: Алгоритм JWT
        ACCESS_TOKEN_EXPIRE_MINUTES: Время жизни access токена
        REFRESH_TOKEN_EXPIRE_DAYS: Время жизни refresh токена

        CORS_ORIGINS: Разрешённые CORS origin
        CORS_ALLOW_CREDENTIALS: Разрешить credentials в CORS

        EXTERNAL_API_URL: URL внешнего API marketplace
        API_TIMEOUT_SECONDS: Таймаут запросов к внешнему API

        CACHE_TTL_SECONDS: TTL кэша
        CACHE_MAX_SIZE: Максимальный размер кэша

        RATE_LIMIT_PER_MINUTE: Лимит запросов в минуту

        MIN_PASSWORD_LENGTH: Минимальная длина пароля
        MAX_LOGIN_ATTEMPTS: Максимум попыток входа
        LOCKOUT_DURATION_MINUTES: Длительность блокировки
    """

    # Application
    APP_NAME: str = "Arizona Lavka Marketplace"
    APP_VERSION: str = "3.1.0"
    DEBUG: bool = False
    PRODUCTION: bool = False
    API_PREFIX: str = "/api"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database - PostgreSQL
    # Используем функцию для получения секретов из файлов или env
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "arizonalavka"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    def __init__(self, **kwargs):
        """
        Инициализация настроек с поддержкой безопасного управления секретами.

        Приоритет получения значений:
        1. Secure secrets manager
        2. Docker secret файлы (*_FILE)
        3. Переменные окружения
        4. Значения по умолчанию
        """
        # Получаем секреты из безопасного хранилища, Docker файлов или env
        postgres_user = _get_secret_or_env(
            "POSTGRES_USER", "POSTGRES_USER", "arizonalavka"
        )
        postgres_password = _get_secret_or_env(
            "POSTGRES_PASSWORD", "POSTGRES_PASSWORD", ""
        )
        jwt_secret = _get_secret_or_env("JWT_SECRET_KEY", "JWT_SECRET_KEY", None)
        gmail_username = _get_secret_or_env("GMAIL_USERNAME", "GMAIL_USERNAME", None)
        gmail_app_password = _get_secret_or_env(
            "GMAIL_APP_PASSWORD", "GMAIL_APP_PASSWORD", None
        )
        telegram_bot_token = _get_secret_or_env(
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", None
        )
        cloudflare_turnstile_secret = _get_secret_or_env(
            "CLOUDFLARE_TURNSTILE_SECRET_KEY", "CLOUDFLARE_TURNSTILE_SECRET_KEY", None
        )

        # Обновляем kwargs переданными значениями
        kwargs.setdefault("POSTGRES_USER", postgres_user)
        kwargs.setdefault("POSTGRES_PASSWORD", postgres_password)
        kwargs.setdefault("JWT_SECRET_KEY", jwt_secret)
        kwargs.setdefault("GMAIL_USERNAME", gmail_username)
        kwargs.setdefault("GMAIL_APP_PASSWORD", gmail_app_password)
        kwargs.setdefault("TELEGRAM_BOT_TOKEN", telegram_bot_token)
        kwargs.setdefault(
            "CLOUDFLARE_TURNSTILE_SECRET_KEY", cloudflare_turnstile_secret
        )

        super().__init__(**kwargs)

    @property
    def database_url(self) -> str:
        """URL подключения к базе данных."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # JWT Settings
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: Optional[str]) -> str:
        """
        Валидация и генерация JWT секрета.

        В production обязательно установите JWT_SECRET_KEY в .env файле!
        Генерация временного ключа только для разработки.

        Args:
            v: Значение секрета из переменных окружения

        Returns:
            str: Валидный JWT секрет

        Raises:
            ValueError: Если секрет короче 32 символов
        """
        if v is None or v == "":
            # В production генерация временного ключа недопустима
            if os.environ.get("PRODUCTION", "false").lower() == "true":
                raise ValueError(
                    "JWT_SECRET_KEY ОБЯЗАТЕЛЕН для production! "
                    "Используйте Docker secrets или установите переменную окружения. "
                    "Минимальная длина: 64 символа."
                )

            # Генерируем временный ключ только для разработки
            temp_key = secrets.token_urlsafe(32)
            warnings.warn(
                "JWT_SECRET_KEY не задан! Сгенерирован временный ключ. "
                "В production обязательно установите JWT_SECRET_KEY! "
                "Все токены будут инвалидированы при перезапуске сервера.",
                UserWarning,
                stacklevel=2,
            )
            return temp_key

        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY должен быть не менее 32 символов. "
                f"Текущая длина: {len(v)}. "
                f"Используйте: openssl rand -base64 64 для генерации"
            )

        return v

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:5173,http://localhost:8000,https://lavka.glorysyntax.live"
    )
    CORS_ALLOW_CREDENTIALS: bool = True

    @property
    def cors_origins_parsed(self) -> List[str]:
        """Парсит CORS_ORIGINS из строки в список."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # External API
    EXTERNAL_API_URL: str = "https://api.arz.market/api/getSelectedMarketplace/-1"
    API_TIMEOUT_SECONDS: int = 30

    # Telegram Bot Token (для Telegram WebApp аутентификации)
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Cache
    CACHE_TTL_SECONDS: int = 30
    CACHE_MAX_SIZE: int = 100

    # Rate Limiting
    # Увеличено до 120 для обработки сценариев с refresh токенами
    RATE_LIMIT_PER_MINUTE: int = 120

    # Load Testing - IP адреса для whitelist (без лимитов)
    # Формат: "127.0.0.1,192.168.1.100" или пусто для отключения
    LOAD_TESTING_IPS: str = "172.18.0.1,127.0.0.1,localhost"

    # Security
    MIN_PASSWORD_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Cloudflare Turnstile (Bot Protection)
    CLOUDFLARE_TURNSTILE_SITE_KEY: Optional[str] = None  # Public key for frontend
    CLOUDFLARE_TURNSTILE_SECRET_KEY: Optional[str] = (
        None  # Secret key for backend verification
    )

    # Email Verification
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 24
    EMAIL_VERIFICATION_CODE_LENGTH: int = 6
    EMAIL_VERIFICATION_MAX_ATTEMPTS: int = 3
    EMAIL_VERIFICATION_COOLDOWN_MINUTES: int = 5

    # Gmail SMTP Configuration (for sending verification emails)
    GMAIL_USERNAME: Optional[str] = None  # Full Gmail address
    GMAIL_APP_PASSWORD: Optional[str] = (
        None  # 16-character App Password (not regular password)
    )

    # Frontend URL (for email verification links)
    FRONTEND_URL: str = "http://localhost:5173"  # Default Vite dev server

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None

    # Anti-Spam
    REGISTRATION_LIMIT_PER_IP_HOUR: int = 5
    REGISTRATION_LIMIT_PER_FINGERPRINT_HOUR: int = 3
    LOGIN_ATTEMPTS_PER_IP_MINUTE: int = 10
    IP_BLOCK_DURATION_HOURS: int = 24

    # Disposable Email Domains (дополнительные)
    DISPOSABLE_EMAIL_DOMAINS: str = (
        "tempmail.com,throwaway.email,guerrillamail.com,mailinator.com,temp-mail.org,fakeinbox.com,10minutemail.com,trashmail.com,getnada.com,maildrop.cc,sharklasers.com,grr.la,dispostable.com,tempinbox.com,emailondeck.com"
    )

    @property
    def disposable_email_domains_parsed(self) -> set:
        """Парсит список disposable email доменов."""
        return {
            d.strip().lower()
            for d in self.DISPOSABLE_EMAIL_DOMAINS.split(",")
            if d.strip()
        }

    # Device Fingerprinting
    FINGERPRINT_TRUST_DURATION_DAYS: int = 30
    SUSPICIOUS_LOGIN_RISK_THRESHOLD: int = 50

    # Historical Data
    HISTORICAL_DATA_PATH: str = "data"

    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379/0"  # Используем имя сервиса в Docker
    REDIS_CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    
    # Session Configuration
    SESSION_EXPIRE_SECONDS: int = 86400  # 24 hours default
    SESSION_COOKIE_NAME: str = "session_id"
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    CACHE_MAX_SIZE: int = 1000  # Maximum number of items in memory cache
    CACHE_BACKEND: str = "redis"  # Options: "redis", "memory", "hybrid"
    CACHE_PREFIX: str = "arizona:"
    CACHE_COMPRESSION_ENABLED: bool = True  # Enable compression for large values
    CACHE_SERIALIZATION_METHOD: str = "pickle"  # Options: "json", "pickle", "msgpack"
    
    # Advanced Cache Settings
    CACHE_ENABLE_CLUSTER: bool = False  # Enable Redis cluster mode
    CACHE_FALLBACK_TO_MEMORY: bool = True  # Fallback to memory cache if Redis unavailable
    CACHE_METRICS_ENABLED: bool = True  # Enable cache metrics collection
    CACHE_WARMUP_ON_STARTUP: bool = True  # Warm up cache on application startup
    CACHE_INVALIDATE_ON_WRITE: bool = True  # Invalidate related cache entries on write
    CACHE_NAMESPACES: List[str] = ["user", "config", "marketplace", "session", "rate_limit", "general"]

    # Security Headers
    SECURE_HEADERS_ENABLED: bool = True
    CONTENT_SECURITY_POLICY: str = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';"
    )
    X_FRAME_OPTIONS: str = "DENY"
    X_CONTENT_TYPE_OPTIONS: str = "nosniff"
    REFERRER_POLICY: str = "strict-origin-when-cross-origin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Получает кэшированный экземпляр настроек.

    Returns:
        Settings: Экземпляр настроек
    """
    return Settings()


# =============================================================================
# Server Constants
# =============================================================================

SERVER_NAMES: dict[int, str] = {
    0: "Vice City",
    1: "Phoenix",
    2: "Tucson",
    3: "Scottsdale",
    4: "Chandler",
    5: "Brainburg",
    6: "Saint Rose",
    7: "Mesa",
    8: "Red Rock",
    9: "Yuma",
    10: "Surprise",
    11: "Prescott",
    12: "Glendale",
    13: "Kingman",
    14: "Winslow",
    15: "Payson",
    16: "Gilbert",
    17: "Show Low",
    18: "Casa Grande",
    19: "Page",
    20: "Sun City",
    21: "Queen Creek",
    22: "Sedona",
    23: "Holiday",
    24: "Wednesday",
    25: "Yava",
    26: "Faraway",
    27: "Bumble Bee",
    28: "Christmas",
    29: "Mirage",
    30: "Love",
    31: "Drake",
    32: "Space",
}


def get_server_name(server_id: int) -> str:
    """Получает название сервера по ID."""
    return SERVER_NAMES.get(server_id, f"Unknown Server ({server_id})")
