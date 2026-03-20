"""
User application service.
"""

import logging
from typing import List, Optional

from application.dtos import UserProfileDTO
from application.interfaces.repositories import (
    IConfigHistoryRepository,
    IFavoriteItemRepository,
    IPriceAlertRepository,
    IUserRepository,
)
from core.entities.favorite import FavoriteItemEntity
from core.entities.price_alert import PriceAlertEntity
from core.entities.user import UserEntity

logger = logging.getLogger(__name__)


class UserAppService:
    """
    Application сервис для управления пользователем.

    Содержит бизнес-логику:
    - Получение профиля пользователя
    - Управление избранными предметами
    - Управление уведомлениями
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        config_history_repository: IConfigHistoryRepository,
        favorite_item_repository: IFavoriteItemRepository,
        price_alert_repository: IPriceAlertRepository,
    ):
        self.user_repository = user_repository
        self.config_history_repository = config_history_repository
        self.favorite_item_repository = favorite_item_repository
        self.price_alert_repository = price_alert_repository

    async def get_profile(self, user_id: int) -> Optional[UserProfileDTO]:
        """
        Получает профиль пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            UserProfileDTO или None
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        configs_count = await self.config_history_repository.count_by_user(user_id)

        return UserProfileDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_premium=user.is_premium,
            role=user.role,
            is_telegram_user=user.is_telegram_user,
            last_active_at=user.last_active_at,
            created_at=user.created_at,
            configs_count=configs_count,
        )

    async def get_favorites(self, user_id: int) -> List[FavoriteItemEntity]:
        """
        Получает избранные предметы пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Список FavoriteItemEntity
        """
        return await self.favorite_item_repository.get_by_user_id(
            user_id, is_active=True
        )

    async def add_favorite(
        self,
        user_id: int,
        item_id: int,
        item_name: str,
        target_price: Optional[float],
        target_percentage: float,
        mode: str,
        server_id: int,
        notes: Optional[str],
    ) -> FavoriteItemEntity:
        """
        Добавляет предмет в избранное.

        Args:
            user_id: ID пользователя
            item_id: ID предмета
            item_name: Название предмета
            target_price: Целевая цена
            target_percentage: Целевой процент
            mode: Режим (SELL/BUY)
            server_id: ID сервера
            notes: Заметки

        Returns:
            FavoriteItemEntity: Созданный избранный предмет
        """
        favorite = FavoriteItemEntity(
            user_id=user_id,
            item_id=item_id,
            item_name=item_name,
            target_price=target_price,
            target_percentage=target_percentage,
            mode=mode,
            server_id=server_id,
            notes=notes,
        )
        return await self.favorite_item_repository.create(favorite)

    async def delete_favorite(self, user_id: int, favorite_id: int) -> bool:
        """
        Удаляет предмет из избранного.

        Args:
            user_id: ID пользователя
            favorite_id: ID избранного предмета

        Returns:
            bool: True если успешно
        """
        favorite = await self.favorite_item_repository.get_by_id(favorite_id)
        if not favorite or favorite.user_id != user_id:
            return False
        return await self.favorite_item_repository.delete(favorite_id)

    async def get_alerts(self, user_id: int) -> List[PriceAlertEntity]:
        """
        Получает уведомления пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Список PriceAlertEntity
        """
        return await self.price_alert_repository.get_by_user_id(user_id, is_active=True)

    async def create_alert(
        self,
        user_id: int,
        item_id: int,
        item_name: str,
        server_id: int,
        target_price: float,
        condition: str,
    ) -> PriceAlertEntity:
        """
        Создаёт уведомление об изменении цены.

        Args:
            user_id: ID пользователя
            item_id: ID предмета
            item_name: Название предмета
            server_id: ID сервера
            target_price: Целевая цена
            condition: Условие (above/below)

        Returns:
            PriceAlertEntity: Созданное уведомление
        """
        alert = PriceAlertEntity(
            user_id=user_id,
            item_id=item_id,
            item_name=item_name,
            server_id=server_id,
            target_price=target_price,
            condition=condition,
        )
        return await self.price_alert_repository.create(alert)

    async def delete_alert(self, user_id: int, alert_id: int) -> bool:
        """
        Удаляет уведомление.

        Args:
            user_id: ID пользователя
            alert_id: ID уведомления

        Returns:
            bool: True если успешно
        """
        alert = await self.price_alert_repository.get_by_id(alert_id)
        if not alert or alert.user_id != user_id:
            return False
        return await self.price_alert_repository.delete(alert_id)
