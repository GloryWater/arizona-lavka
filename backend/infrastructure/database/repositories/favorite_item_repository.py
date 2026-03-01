"""
FavoriteItem repository implementation.
"""

from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.favorite import FavoriteItemEntity
from application.interfaces.repositories import IFavoriteItemRepository
from infrastructure.database.models import FavoriteItem


class FavoriteItemRepository(IFavoriteItemRepository):
    """Repository для избранных предметов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, fav: FavoriteItem) -> FavoriteItemEntity:
        return FavoriteItemEntity(
            id=fav.id,
            user_id=fav.user_id,
            item_id=fav.item_id,
            item_name=fav.item_name,
            target_price=fav.target_price,
            target_percentage=fav.target_percentage,
            mode=fav.mode,
            server_id=fav.server_id,
            notes=fav.notes,
            is_active=fav.is_active,
            created_at=fav.created_at,
            updated_at=fav.updated_at,
        )

    def _from_entity(self, entity: FavoriteItemEntity) -> FavoriteItem:
        return FavoriteItem(
            id=entity.id,
            user_id=entity.user_id,
            item_id=entity.item_id,
            item_name=entity.item_name,
            target_price=entity.target_price,
            target_percentage=entity.target_percentage,
            mode=entity.mode,
            server_id=entity.server_id,
            notes=entity.notes,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_id(self, favorite_id: int) -> Optional[FavoriteItemEntity]:
        fav = await self.session.get(FavoriteItem, favorite_id)
        return self._to_entity(fav) if fav else None

    async def get_by_user_id(
        self,
        user_id: int,
        is_active: bool = True,
    ) -> List[FavoriteItemEntity]:
        query = (
            select(FavoriteItem)
            .where(FavoriteItem.user_id == user_id)
            .where(FavoriteItem.is_active == is_active)
            .order_by(desc(FavoriteItem.created_at))
        )
        result = await self.session.execute(query)
        favorites = result.scalars().all()
        return [self._to_entity(f) for f in favorites]

    async def create(self, favorite: FavoriteItemEntity) -> FavoriteItemEntity:
        db_fav = self._from_entity(favorite)
        self.session.add(db_fav)
        await self.session.flush()
        await self.session.refresh(db_fav)
        return self._to_entity(db_fav)

    async def delete(self, favorite_id: int) -> bool:
        fav = await self.session.get(FavoriteItem, favorite_id)
        if not fav:
            return False
        await self.session.delete(fav)
        await self.session.commit()
        return True
