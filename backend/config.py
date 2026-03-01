"""
Конфигурация приложения Arizona Lavka Marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import secrets
import warnings
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database - PostgreSQL
    POSTGRES_USER: str = "arizonalavka"
    POSTGRES_PASSWORD: str = "arizonalavka_password"
    POSTGRES_DB: str = "arizonalavka"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

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
            # Генерируем временный ключ только для разработки
            # В production это приведёт к инвалидации токенов при рестарте
            # Для безопасности генерируем ключ и логируем предупреждение
            temp_key = secrets.token_urlsafe(32)
            warnings.warn(
                "JWT_SECRET_KEY не задан! Сгенерирован временный ключ. "
                "В production обязательно установите JWT_SECRET_KEY в .env файле! "
                "Все токены будут инвалидированы при перезапуске сервера.",
                UserWarning,
                stacklevel=2
            )
            return temp_key

        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY должен быть не менее 32 символов. "
                f"Текущая длина: {len(v)}. "
                f"Используйте: secrets.token_urlsafe(32) для генерации"
            )

        return v

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000,https://lavka.glorysyntax.live"
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

    # Historical Data
    HISTORICAL_DATA_PATH: str = "data"

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
    0: "Vice City", 1: "Phoenix", 2: "Tucson", 3: "Scottsdale", 4: "Chandler",
    5: "Brainburg", 6: "Saint Rose", 7: "Mesa", 8: "Red Rock", 9: "Yuma",
    10: "Surprise", 11: "Prescott", 12: "Glendale", 13: "Kingman", 14: "Winslow",
    15: "Payson", 16: "Gilbert", 17: "Show Low", 18: "Casa Grande", 19: "Page",
    20: "Sun City", 21: "Queen Creek", 22: "Sedona", 23: "Holiday", 24: "Wednesday",
    25: "Yava", 26: "Faraway", 27: "Bumble Bee", 28: "Christmas", 29: "Mirage",
    30: "Love", 31: "Drake", 32: "Space",
}


def get_server_name(server_id: int) -> str:
    """Получает название сервера по ID."""
    return SERVER_NAMES.get(server_id, f"Unknown Server ({server_id})")
