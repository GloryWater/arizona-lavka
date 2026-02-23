"""
Dependency Injection для Arizona Lavka Marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from functools import lru_cache
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database import DatabaseManager
from services.marketplace_service import MarketplaceService
from services.historical_data_service import HistoricalDataService
from services.config_generator_service import ConfigGeneratorService
from services.lavka_service import LavkaService


# =============================================================================
# Settings Dependency
# =============================================================================

@lru_cache
def get_settings() -> Settings:
    """
    Получает кэшированный экземпляр настроек.
    
    Returns:
        Settings: Экземпляр настроек
    """
    from config import get_settings
    return get_settings()


# =============================================================================
# Database Dependency
# =============================================================================

def get_db_manager(request: Request) -> DatabaseManager:
    """
    Получает менеджер базы данных из состояния приложения.

    Args:
        request: HTTP запрос

    Returns:
        DatabaseManager: Менеджер базы данных

    Raises:
        HTTPException: Если БД не инициализирована
    """
    db_manager: DatabaseManager = request.app.state.db_manager
    if not db_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )
    return db_manager


async def get_db_session(
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии базы данных.

    Args:
        db_manager: Менеджер базы данных

    Yields:
        AsyncSession: Сессия базы данных
    """
    async with db_manager.get_session() as session:
        yield session


# =============================================================================
# Service Dependencies (с кэшированием для производительности)
# =============================================================================

# Кэш для сервисов на время запроса
_service_cache: dict = {}


async def get_marketplace_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[MarketplaceService, None]:
    """
    Создаёт экземпляр MarketplaceService.
    
    Note:
        Сервис создаётся один раз на время жизни запроса благодаря кэшированию.
        Это предотвращает множественные создания объектов при цепочке зависимостей.

    Args:
        settings: Настройки приложения

    Yields:
        MarketplaceService: Сервис marketplace
    """
    # Проверяем кэш
    if 'marketplace' in _service_cache:
        yield _service_cache['marketplace']
        return
    
    service = MarketplaceService(settings)
    _service_cache['marketplace'] = service
    
    try:
        yield service
    finally:
        await service.close()
        _service_cache.pop('marketplace', None)


async def get_historical_data_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[HistoricalDataService, None]:
    """
    Создаёт экземпляр HistoricalDataService.
    
    Note:
        Сервис не требует закрытия ресурсов, используется singleton на запрос.

    Args:
        settings: Настройки приложения

    Yields:
        HistoricalDataService: Сервис исторических данных
    """
    if 'historical' in _service_cache:
        yield _service_cache['historical']
        return
    
    service = HistoricalDataService(settings)
    _service_cache['historical'] = service
    yield service


async def get_lavka_service(
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[LavkaService, None]:
    """
    Создаёт экземпляр LavkaService.
    
    Note:
        Использует кэшированный marketplace_service из текущего запроса.

    Args:
        marketplace_service: Сервис marketplace
        settings: Настройки приложения

    Yields:
        LavkaService: Сервис лавок
    """
    if 'lavka' in _service_cache:
        yield _service_cache['lavka']
        return
    
    service = LavkaService(marketplace_service, settings)
    _service_cache['lavka'] = service
    yield service


async def get_config_generator_service(
    session: AsyncSession = Depends(get_db_session),
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    historical_data_service: HistoricalDataService = Depends(get_historical_data_service),
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[ConfigGeneratorService, None]:
    """
    Создаёт экземпляр ConfigGeneratorService.
    
    Note:
        Использует кэшированные зависимости из текущего запроса.
        Это критично для производительности при генерации конфигов.

    Args:
        session: Сессия базы данных
        marketplace_service: Сервис marketplace
        historical_data_service: Сервис исторических данных
        settings: Настройки приложения

    Yields:
        ConfigGeneratorService: Сервис генерации конфигов
    """
    if 'config_generator' in _service_cache:
        yield _service_cache['config_generator']
        return
    
    service = ConfigGeneratorService(
        session, marketplace_service, historical_data_service, settings
    )
    _service_cache['config_generator'] = service
    yield service


# =============================================================================
# User Dependencies
# =============================================================================

async def get_current_user_optional(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> Optional["User"]:
    """
    Получает текущего пользователя (опционально).

    Args:
        request: HTTP запрос
        session: Сессия базы данных

    Returns:
        User | None: Объект пользователя или None
    """
    from database import User
    from services.auth_service import get_current_user_from_request

    return await get_current_user_from_request(request, session)


async def get_current_user_required(
    user: Optional["User"] = Depends(get_current_user_optional)
) -> "User":
    """
    Требует обязательной авторизации.

    Args:
        user: Объект пользователя (опционально)

    Returns:
        User: Объект пользователя

    Raises:
        HTTPException: Если пользователь не авторизован
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
