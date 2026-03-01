"""
Arizona Lavka Marketplace - Dependencies.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Note:
    Этот файл существует для обратной совместимости.
    Новый код должен использовать DI из application/services напрямую.
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
# New Architecture Dependencies (Clean Architecture)
# =============================================================================

from infrastructure.database.repositories import (
    UserRepository,
    ConfigHistoryRepository,
    FavoriteItemRepository,
    PriceAlertRepository,
    AuditLogRepository,
    AdminLogRepository,
    GlobalSettingRepository,
)
from infrastructure.external.marketplace_api import MarketplaceAPI
from application.services import (
    AuthAppService,
    MarketplaceAppService,
    UserAppService,
)
from services.config_generator_service import ConfigGeneratorService


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

    Note:
        Использует get_session() с автоматическим коммитом при успешном завершении.
        Для операций без коммита используйте get_db_session_no_commit().

    Args:
        db_manager: Менеджер базы данных

    Yields:
        AsyncSession: Сессия базы данных
    """
    async with db_manager.get_session() as session:
        yield session


async def get_db_session_no_commit(
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии базы данных без автоматического коммита.

    Note:
        Используйте для операций чтения или когда коммит управляется вручную.
        При использовании этой зависимости вы должны явно вызывать commit().

    Args:
        db_manager: Менеджер базы данных

    Yields:
        AsyncSession: Сессия базы данных
    """
    async with db_manager.get_session_no_commit() as session:
        yield session


# =============================================================================
# Service Dependencies (с кэшированием для производительности)
# =============================================================================

# Кэш для сервисов на время запроса (request-scoped)
# Использует request.state для хранения сервисов в рамках одного запроса
# Это предотвращает race condition при параллельных запросах


async def get_marketplace_service(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[MarketplaceService, None]:
    """
    Создаёт экземпляр MarketplaceService.

    Note:
        Сервис создаётся один раз на время жизни запроса благодаря кэшированию
        через request.state. Это предотвращает race condition при параллельных
        запросах и множественные создания объектов при цепочке зависимостей.

    Args:
        request: HTTP запрос (для request.state кэша)
        settings: Настройки приложения

    Yields:
        MarketplaceService: Сервис marketplace
    """
    # Проверяем кэш в request.state (request-scoped кэш)
    if not hasattr(request.state, 'services'):
        request.state.services = {}

    if 'marketplace' in request.state.services:
        yield request.state.services['marketplace']
        return

    service = MarketplaceService(settings)
    request.state.services['marketplace'] = service

    try:
        yield service
    finally:
        await service.close()
        request.state.services.pop('marketplace', None)


async def get_historical_data_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[HistoricalDataService, None]:
    """
    Создаёт экземпляр HistoricalDataService.

    Note:
        Сервис не требует закрытия ресурсов, используется singleton на запрос.
        Не требует request.state так как не имеет состояния.

    Args:
        settings: Настройки приложения

    Yields:
        HistoricalDataService: Сервис исторических данных
    """
    yield HistoricalDataService(settings)


async def get_lavka_service(
    request: Request,
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[LavkaService, None]:
    """
    Создаёт экземпляр LavkaService.

    Note:
        Использует кэшированный marketplace_service из request.state.
        Это критично для предотвращения race condition.

    Args:
        request: HTTP запрос
        marketplace_service: Сервис marketplace
        settings: Настройки приложения

    Yields:
        LavkaService: Сервис лавок
    """
    yield LavkaService(marketplace_service, settings)


async def get_config_generator_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    historical_data_service: HistoricalDataService = Depends(get_historical_data_service),
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[ConfigGeneratorService, None]:
    """
    Создаёт экземпляр ConfigGeneratorService.

    Note:
        Использует сессию без автоматического коммита (get_db_session_no_commit).
        Коммит управляется вручную в роутах при сохранении конфигов в историю.
        Использует кэшированные зависимости из request.state.

    Args:
        session: Сессия базы данных
        marketplace_service: Сервис marketplace
        historical_data_service: Сервис исторических данных
        settings: Настройки приложения

    Yields:
        ConfigGeneratorService: Сервис генерации конфигов
    """
    yield ConfigGeneratorService(
        session, marketplace_service, historical_data_service, settings
    )


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


async def get_current_admin(
    user: "User" = Depends(get_current_user_required)
) -> "User":
    """
    Требует чтобы пользователь был администратором.

    Args:
        user: Объект пользователя (обязательно авторизованный)

    Returns:
        User: Объект пользователя с ролью admin

    Raises:
        HTTPException: Если пользователь не администратор
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуются права администратора.",
        )
    return user


# =============================================================================
# New Architecture Dependencies (Clean Architecture)
# =============================================================================

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[UserRepository, None]:
    """Создаёт UserRepository."""
    yield UserRepository(session)


async def get_config_history_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[ConfigHistoryRepository, None]:
    """Создаёт ConfigHistoryRepository."""
    yield ConfigHistoryRepository(session)


async def get_favorite_item_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[FavoriteItemRepository, None]:
    """Создаёт FavoriteItemRepository."""
    yield FavoriteItemRepository(session)


async def get_price_alert_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[PriceAlertRepository, None]:
    """Создаёт PriceAlertRepository."""
    yield PriceAlertRepository(session)


async def get_audit_log_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[AuditLogRepository, None]:
    """Создаёт AuditLogRepository."""
    yield AuditLogRepository(session)


async def get_admin_log_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[AdminLogRepository, None]:
    """Создаёт AdminLogRepository."""
    yield AdminLogRepository(session)


async def get_global_setting_repository(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AsyncGenerator[GlobalSettingRepository, None]:
    """Создаёт GlobalSettingRepository."""
    yield GlobalSettingRepository(session)


async def get_marketplace_api(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[MarketplaceAPI, None]:
    """Создаёт MarketplaceAPI."""
    api = MarketplaceAPI(settings)
    try:
        yield api
    finally:
        await api.close()


async def get_auth_app_service(
    user_repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[AuthAppService, None]:
    """Создаёт AuthAppService."""
    yield AuthAppService(
        user_repository=user_repository,
        jwt_secret_key=settings.JWT_SECRET_KEY,
        jwt_algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        max_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
        lockout_duration_minutes=settings.LOCKOUT_DURATION_MINUTES,
    )


async def get_marketplace_app_service(
    marketplace_api: MarketplaceAPI = Depends(get_marketplace_api)
) -> AsyncGenerator[MarketplaceAppService, None]:
    """Создаёт MarketplaceAppService."""
    yield MarketplaceAppService(marketplace_api=marketplace_api)


async def get_user_app_service(
    user_repository: UserRepository = Depends(get_user_repository),
    config_history_repository: ConfigHistoryRepository = Depends(get_config_history_repository),
    favorite_item_repository: FavoriteItemRepository = Depends(get_favorite_item_repository),
    price_alert_repository: PriceAlertRepository = Depends(get_price_alert_repository),
) -> AsyncGenerator[UserAppService, None]:
    """Создаёт UserAppService."""
    yield UserAppService(
        user_repository=user_repository,
        config_history_repository=config_history_repository,
        favorite_item_repository=favorite_item_repository,
        price_alert_repository=price_alert_repository,
    )
