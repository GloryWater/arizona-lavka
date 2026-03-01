"""
ConfigHistory repository implementation.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.config import ConfigHistoryEntity
from application.interfaces.repositories import IConfigHistoryRepository
from infrastructure.database.models import ConfigHistory


class ConfigHistoryRepository(IConfigHistoryRepository):
    """Repository для истории конфигов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, config: ConfigHistory) -> ConfigHistoryEntity:
        return ConfigHistoryEntity(
            id=config.id,
            user_id=config.user_id,
            server_id=config.server_id,
            server_name=config.server_name,
            mode=config.mode,
            percentage=config.percentage,
            items_count=config.items_count,
            config_data=config.config_data,
            used_historical_data=config.used_historical_data,
            confidence_score=config.confidence_score,
            download_count=config.download_count,
            created_at=config.created_at,
        )

    def _from_entity(self, entity: ConfigHistoryEntity) -> ConfigHistory:
        return ConfigHistory(
            id=entity.id,
            user_id=entity.user_id,
            server_id=entity.server_id,
            server_name=entity.server_name,
            mode=entity.mode,
            percentage=entity.percentage,
            items_count=entity.items_count,
            config_data=entity.config_data,
            used_historical_data=entity.used_historical_data,
            confidence_score=entity.confidence_score,
            download_count=entity.download_count,
            created_at=entity.created_at,
        )

    async def get_by_id(self, config_id: int) -> Optional[ConfigHistoryEntity]:
        config = await self.session.get(ConfigHistory, config_id)
        return self._to_entity(config) if config else None

    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ConfigHistoryEntity]:
        query = (
            select(ConfigHistory)
            .where(ConfigHistory.user_id == user_id)
            .order_by(desc(ConfigHistory.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        configs = result.scalars().all()
        return [self._to_entity(c) for c in configs]

    async def create(self, config: ConfigHistoryEntity) -> ConfigHistoryEntity:
        db_config = self._from_entity(config)
        self.session.add(db_config)
        await self.session.flush()
        await self.session.refresh(db_config)
        return self._to_entity(db_config)

    async def increment_download_count(self, config_id: int) -> int:
        config = await self.session.get(ConfigHistory, config_id)
        if not config:
            return 0
        config.download_count += 1
        await self.session.flush()
        return config.download_count

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(ConfigHistory.id)))
        return result.scalar_one() or 0

    async def count_by_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(ConfigHistory.id)).where(ConfigHistory.user_id == user_id)
        )
        return result.scalar_one() or 0

    async def count_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(ConfigHistory.id)).where(
                ConfigHistory.created_at >= since
            )
        )
        return result.scalar_one() or 0

    async def get_daily_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        from sqlalchemy import text
        try:
            query = text("""
                SELECT DATE(date_trunc('day', created_at)) as date, COUNT(id) as count
                FROM config_history
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY DATE(date_trunc('day', created_at))
                ORDER BY date
            """)
            result = await self.session.execute(
                query,
                {"start_date": start_date, "end_date": end_date}
            )
            return {row.date: row.count for row in result}
        except Exception:
            # Fallback для SQLite
            query = select(
                func.strftime('%Y-%m-%d', ConfigHistory.created_at).label('date'),
                func.count(ConfigHistory.id).label('count')
            ).where(
                and_(ConfigHistory.created_at >= start_date, ConfigHistory.created_at <= end_date)
            ).group_by(func.strftime('%Y-%m-%d', ConfigHistory.created_at))
            result = await self.session.execute(query)
            return {row.date: row.count for row in result}
