"""
PriceAlert repository implementation.
"""

from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.repositories import IPriceAlertRepository
from core.entities.price_alert import PriceAlertEntity
from infrastructure.database.models import PriceAlert


class PriceAlertRepository(IPriceAlertRepository):
    """Repository для уведомлений о ценах."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, alert: PriceAlert) -> PriceAlertEntity:
        return PriceAlertEntity(
            id=alert.id,
            user_id=alert.user_id,
            item_id=alert.item_id,
            item_name=alert.item_name,
            server_id=alert.server_id,
            target_price=alert.target_price,
            condition=alert.condition,
            is_active=alert.is_active,
            triggered=alert.triggered,
            triggered_at=alert.triggered_at,
            triggered_price=alert.triggered_price,
            created_at=alert.created_at,
        )

    def _from_entity(self, entity: PriceAlertEntity) -> PriceAlert:
        return PriceAlert(
            id=entity.id,
            user_id=entity.user_id,
            item_id=entity.item_id,
            item_name=entity.item_name,
            server_id=entity.server_id,
            target_price=entity.target_price,
            condition=entity.condition,
            is_active=entity.is_active,
            triggered=entity.triggered,
            triggered_at=entity.triggered_at,
            triggered_price=entity.triggered_price,
            created_at=entity.created_at,
        )

    async def get_by_id(self, alert_id: int) -> Optional[PriceAlertEntity]:
        alert = await self.session.get(PriceAlert, alert_id)
        return self._to_entity(alert) if alert else None

    async def get_by_user_id(
        self,
        user_id: int,
        is_active: bool = True,
    ) -> List[PriceAlertEntity]:
        query = (
            select(PriceAlert)
            .where(PriceAlert.user_id == user_id)
            .where(PriceAlert.is_active == is_active)
            .order_by(desc(PriceAlert.created_at))
        )
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        return [self._to_entity(a) for a in alerts]

    async def create(self, alert: PriceAlertEntity) -> PriceAlertEntity:
        db_alert = self._from_entity(alert)
        self.session.add(db_alert)
        await self.session.flush()
        await self.session.refresh(db_alert)
        return self._to_entity(db_alert)

    async def delete(self, alert_id: int) -> bool:
        alert = await self.session.get(PriceAlert, alert_id)
        if not alert:
            return False
        await self.session.delete(alert)
        await self.session.commit()
        return True

    async def update(self, alert: PriceAlertEntity) -> PriceAlertEntity:
        """Обновляет уведомление о цене."""
        db_alert = await self.session.get(PriceAlert, alert.id)
        if not db_alert:
            raise ValueError(f"Price alert with id {alert.id} not found")

        # Обновляем поля
        for field, value in vars(alert).items():
            if hasattr(db_alert, field) and field not in [
                "id",
                "created_at",
            ]:  # Не обновляем id и created_at
                setattr(db_alert, field, value)

        await self.session.flush()
        await self.session.refresh(db_alert)
        return self._to_entity(db_alert)
