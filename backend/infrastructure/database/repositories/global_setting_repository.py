"""
GlobalSetting repository implementation.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.repositories import IGlobalSettingRepository
from infrastructure.database.models import GlobalSetting


class GlobalSettingRepository(IGlobalSettingRepository):
    """Repository для глобальных настроек."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(self, key: str) -> Optional[dict]:
        result = await self.session.execute(
            select(GlobalSetting).where(GlobalSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        return (
            {
                "key": setting.key,
                "value": setting.value,
                "updated_at": setting.updated_at,
            }
            if setting
            else None
        )

    async def get_all(self) -> List[Any]:
        result = await self.session.execute(
            select(GlobalSetting).order_by(GlobalSetting.key)
        )
        return result.scalars().all()

    async def upsert(self, key: str, value: dict) -> GlobalSetting:
        result = await self.session.execute(
            select(GlobalSetting).where(GlobalSetting.key == key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            setting = GlobalSetting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
            setting.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await self.session.flush()
        await self.session.refresh(setting)
        return setting

    async def get_maintenance_status(self) -> dict:
        result = await self.get_by_key("maintenance_mode")
        if not result:
            return {"enabled": False, "message": "", "estimated_end": None}
        return result.get(
            "value", {"enabled": False, "message": "", "estimated_end": None}
        )

    async def set_maintenance_status(
        self,
        enabled: bool,
        message: str,
        estimated_end: Optional[str],
    ) -> None:
        await self.upsert(
            "maintenance_mode",
            {
                "enabled": enabled,
                "message": message,
                "estimated_end": estimated_end,
            },
        )
