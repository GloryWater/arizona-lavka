"""
AdminLog repository implementation.
"""

from typing import Optional, List, Any
from datetime import datetime

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.repositories import IAdminLogRepository
from infrastructure.database.models import AdminLog


class AdminLogRepository(IAdminLogRepository):
    """Repository для логов админ-панели."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: Optional[int],
        event_type: str,
        details: Optional[dict],
        ip_address: Optional[str],
    ) -> AdminLog:
        log = AdminLog(
            user_id=user_id,
            event_type=event_type,
            details=details,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_all(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_type: Optional[str],
        search_query: Optional[str],
        page: int,
        limit: int,
    ) -> List[AdminLog]:
        from infrastructure.database.models import User

        query = select(AdminLog)
        conditions = []

        if start_date:
            conditions.append(AdminLog.created_at >= start_date)
        if end_date:
            conditions.append(AdminLog.created_at <= end_date)
        if event_type:
            conditions.append(AdminLog.event_type == event_type)
        if search_query:
            if search_query.isdigit():
                conditions.append(AdminLog.user_id == int(search_query))
            else:
                user_subquery = select(User.id).where(User.username.ilike(f"%{search_query}%"))
                conditions.append(AdminLog.user_id.in_(user_subquery.scalar_subquery()))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AdminLog.created_at))
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()
