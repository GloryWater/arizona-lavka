"""
AuditLog repository implementation.
"""

from typing import Optional, List, Any
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.repositories import IAuditLogRepository
from infrastructure.database.models import AuditLog


class AuditLogRepository(IAuditLogRepository):
    """Repository для логов аудита."""

    def __init__(self, session: AsyncSession):
        self.session = session

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
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status=status,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_all(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        action: Optional[str],
        search_query: Optional[str],
        status_filter: Optional[str],
        page: int,
        limit: int,
    ) -> List[AuditLog]:
        from sqlalchemy import desc
        from infrastructure.database.models import User

        query = select(AuditLog)
        conditions = []

        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)
        if action:
            conditions.append(AuditLog.action == action)
        if status_filter:
            conditions.append(AuditLog.status == status_filter)
        if search_query:
            if search_query.isdigit():
                conditions.append(AuditLog.user_id == int(search_query))
            else:
                user_subquery = select(User.id).where(User.username.ilike(f"%{search_query}%"))
                conditions.append(AuditLog.user_id.in_(user_subquery.scalar_subquery()))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.created_at))
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()
