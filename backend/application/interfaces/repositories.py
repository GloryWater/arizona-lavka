"""
Repository interfaces - абстракции для доступа к данным.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List, Optional

from core.entities.config import ConfigHistoryEntity
from core.entities.favorite import FavoriteItemEntity
from core.entities.price_alert import PriceAlertEntity
from core.entities.user import UserEntity


class IUserRepository(ABC):
    """
    Интерфейс репозитория пользователей.

    Абстрагирует доступ к данным пользователей от бизнес-логики.
    """

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Получает пользователя по ID."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Получает пользователя по username."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Получает пользователя по email."""
        pass

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: str) -> Optional[UserEntity]:
        """Получает пользователя по Telegram ID."""
        pass

    @abstractmethod
    async def get_by_username_or_email(
        self, username_or_email: str
    ) -> Optional[UserEntity]:
        """Получает пользователя по username или email."""
        pass

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        """Создаёт нового пользователя."""
        pass

    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """Обновляет пользователя."""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Удаляет пользователя."""
        pass

    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: str = "created_at",
    ) -> List[UserEntity]:
        """Получает всех пользователей с пагинацией."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Возвращает общее количество пользователей."""
        pass

    @abstractmethod
    async def count_active_since(self, since: datetime) -> int:
        """Возвращает количество активных пользователей с указанной даты."""
        pass


class IConfigHistoryRepository(ABC):
    """Интерфейс репозитория истории конфигов."""

    @abstractmethod
    async def get_by_id(self, config_id: int) -> Optional[ConfigHistoryEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ConfigHistoryEntity]:
        pass

    @abstractmethod
    async def create(self, config: ConfigHistoryEntity) -> ConfigHistoryEntity:
        pass

    @abstractmethod
    async def increment_download_count(self, config_id: int) -> int:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass

    @abstractmethod
    async def count_by_user(self, user_id: int) -> int:
        pass

    @abstractmethod
    async def count_since(self, since: datetime) -> int:
        pass

    @abstractmethod
    async def get_daily_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        pass


class IFavoriteItemRepository(ABC):
    """Интерфейс репозитория избранных предметов."""

    @abstractmethod
    async def get_by_id(self, favorite_id: int) -> Optional[FavoriteItemEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        is_active: bool = True,
    ) -> List[FavoriteItemEntity]:
        pass

    @abstractmethod
    async def create(self, favorite: FavoriteItemEntity) -> FavoriteItemEntity:
        pass

    @abstractmethod
    async def update(self, favorite: FavoriteItemEntity) -> FavoriteItemEntity:
        pass

    @abstractmethod
    async def delete(self, favorite_id: int) -> bool:
        pass


class IPriceAlertRepository(ABC):
    """Интерфейс репозитория уведомлений о ценах."""

    @abstractmethod
    async def get_by_id(self, alert_id: int) -> Optional[PriceAlertEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        is_active: bool = True,
    ) -> List[PriceAlertEntity]:
        pass

    @abstractmethod
    async def create(self, alert: PriceAlertEntity) -> PriceAlertEntity:
        pass

    @abstractmethod
    async def update(self, alert: PriceAlertEntity) -> PriceAlertEntity:
        pass

    @abstractmethod
    async def delete(self, alert_id: int) -> bool:
        pass


class IAuditLogRepository(ABC):
    """Интерфейс репозитория аудита."""

    @abstractmethod
    async def create(
        self,
        user_id: Optional[int],
        action: str,
        resource: Optional[str],
        resource_id: Optional[int],
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Optional[str],
        status: str,
        error_message: Optional[str],
    ) -> Any:
        pass

    @abstractmethod
    async def get_all(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        action: Optional[str],
        search_query: Optional[str],
        status_filter: Optional[str],
        page: int,
        limit: int,
    ) -> List[Any]:
        pass


class IAdminLogRepository(ABC):
    """Интерфейс репозитория логов админ-панели."""

    @abstractmethod
    async def create(
        self,
        user_id: Optional[int],
        event_type: str,
        details: Optional[dict],
        ip_address: Optional[str],
    ) -> Any:
        pass

    @abstractmethod
    async def get_all(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_type: Optional[str],
        search_query: Optional[str],
        page: int,
        limit: int,
    ) -> List[Any]:
        pass


class IGlobalSettingRepository(ABC):
    """Интерфейс репозитория глобальных настроек."""

    @abstractmethod
    async def get_by_key(self, key: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    async def upsert(self, key: str, value: dict) -> Any:
        pass

    @abstractmethod
    async def get_maintenance_status(self) -> dict:
        pass

    @abstractmethod
    async def set_maintenance_status(
        self,
        enabled: bool,
        message: str,
        estimated_end: Optional[str],
    ) -> None:
        pass
