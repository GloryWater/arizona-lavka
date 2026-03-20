"""
Metrics repository - репозиторий для работы с метриками пользователей.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    Conversion,
    DailyMetrics,
    PageView,
    User,
    UserEvent,
    UserSession,
)


class MetricsRepository:
    """
    Repository для работы с метриками пользователей.

    Реализует методы для создания, чтения, обновления и удаления метрик.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    # =========================================================================
    # Session Methods
    # =========================================================================

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[dict] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
    ) -> UserSession:
        """Создаёт новую сессию пользователя."""
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Получает сессию по session_id."""
        return await self.session.get(UserSession, session_id, populate_existing=True)

    async def get_session_by_id_field(self, session_id: str) -> Optional[UserSession]:
        """Получает сессию по полю session_id."""
        result = await self.session.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_session(
        self,
        session: UserSession,
        **kwargs: Any,
    ) -> UserSession:
        """Обновляет поля сессии."""
        for field, value in kwargs.items():
            if hasattr(session, field):
                setattr(session, field, value)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def end_session(self, session: UserSession) -> UserSession:
        """Завершает сессию."""
        session.ended_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def link_session_to_user(
        self,
        session: UserSession,
        user_id: int,
    ) -> UserSession:
        """Привязывает сессию к пользователю (после аутентификации)."""
        session.user_id = user_id
        await self.session.flush()
        await self.session.refresh(session)
        return session

    # =========================================================================
    # Page View Methods
    # =========================================================================

    async def create_page_view(
        self,
        session_id: str,
        page_path: str,
        user_id: Optional[int] = None,
        page_title: Optional[str] = None,
        referrer: Optional[str] = None,
        time_on_page: Optional[int] = None,
    ) -> PageView:
        """Создаёт запись о просмотре страницы."""
        page_view = PageView(
            session_id=session_id,
            user_id=user_id,
            page_path=page_path,
            page_title=page_title,
            referrer=referrer,
            time_on_page=time_on_page,
        )
        self.session.add(page_view)
        await self.session.flush()
        await self.session.refresh(page_view)
        return page_view

    async def get_page_views_by_session(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[PageView]:
        """Получает просмотры страниц по сессии."""
        result = await self.session.execute(
            select(PageView)
            .where(PageView.session_id == session_id)
            .order_by(desc(PageView.viewed_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # User Event Methods
    # =========================================================================

    async def create_event(
        self,
        session_id: str,
        event_type: str,
        event_category: str,
        user_id: Optional[int] = None,
        event_data: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> UserEvent:
        """Создаёт событие пользователя."""
        event = UserEvent(
            session_id=session_id,
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            event_data=event_data,
            error_message=error_message,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def get_events_by_session(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[UserEvent]:
        """Получает события по сессии."""
        result = await self.session.execute(
            select(UserEvent)
            .where(UserEvent.session_id == session_id)
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Conversion Methods
    # =========================================================================

    async def create_conversion(
        self,
        session_id: str,
        conversion_type: str,
        user_id: Optional[int] = None,
        conversion_value: Optional[Decimal] = None,
        currency: str = "RUB",
        attribution_source: Optional[str] = None,
    ) -> Conversion:
        """Создаёт запись о конверсии."""
        conversion = Conversion(
            session_id=session_id,
            user_id=user_id,
            conversion_type=conversion_type,
            conversion_value=conversion_value,
            currency=currency,
            attribution_source=attribution_source,
        )
        self.session.add(conversion)
        await self.session.flush()
        await self.session.refresh(conversion)
        return conversion

    async def get_conversions_by_user(
        self,
        user_id: int,
        limit: int = 100,
    ) -> List[Conversion]:
        """Получает конверсии пользователя."""
        result = await self.session.execute(
            select(Conversion)
            .where(Conversion.user_id == user_id)
            .order_by(desc(Conversion.converted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Analytics Methods
    # =========================================================================

    async def get_dau(self, date: Optional[datetime] = None) -> int:
        """Получает DAU (Daily Active Users) для указанной даты."""
        if date is None:
            date = datetime.utcnow().date()

        result = await self.session.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                and_(
                    UserSession.user_id.isnot(None),
                    extract("date", UserSession.started_at) == date,
                )
            )
        )
        return result.scalar_one() or 0

    async def get_mau(self, reference_date: Optional[datetime] = None) -> int:
        """Получает MAU (Monthly Active Users) за последние 30 дней."""
        if reference_date is None:
            reference_date = datetime.utcnow()

        thirty_days_ago = reference_date - timedelta(days=30)

        result = await self.session.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                and_(
                    UserSession.user_id.isnot(None),
                    UserSession.started_at >= thirty_days_ago,
                )
            )
        )
        return result.scalar_one() or 0

    async def get_avg_session_duration(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Получает среднюю длительность сессии."""
        query = select(
            func.avg(
                func.extract("epoch", UserSession.last_active_at)
                - func.extract("epoch", UserSession.started_at)
            )
        ).where(UserSession.ended_at.isnot(None))

        if start_date:
            query = query.where(UserSession.started_at >= start_date)
        if end_date:
            query = query.where(UserSession.started_at <= end_date)

        result = await self.session.execute(query)
        avg_duration = result.scalar_one()
        return float(avg_duration) if avg_duration else 0.0

    async def get_total_sessions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Получает общее количество сессий."""
        query = select(func.count(UserSession.id))

        if start_date:
            query = query.where(UserSession.started_at >= start_date)
        if end_date:
            query = query.where(UserSession.started_at <= end_date)

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_total_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Получает общее количество событий."""
        query = select(func.count(UserEvent.id))

        if start_date:
            query = query.where(UserEvent.created_at >= start_date)
        if end_date:
            query = query.where(UserEvent.created_at <= end_date)

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_total_page_views(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Получает общее количество просмотров страниц."""
        query = select(func.count(PageView.id))

        if start_date:
            query = query.where(PageView.viewed_at >= start_date)
        if end_date:
            query = query.where(PageView.viewed_at <= end_date)

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_total_conversions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Получает общее количество конверсий."""
        query = select(func.count(Conversion.id))

        if start_date:
            query = query.where(Conversion.converted_at >= start_date)
        if end_date:
            query = query.where(Conversion.converted_at <= end_date)

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_total_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Decimal:
        """Получает общую выручку от конверсий."""
        query = select(func.sum(Conversion.conversion_value))

        if start_date:
            query = query.where(Conversion.converted_at >= start_date)
        if end_date:
            query = query.where(Conversion.converted_at <= end_date)

        result = await self.session.execute(query)
        total = result.scalar_one()
        return total if total else Decimal("0.00")

    async def get_top_pages(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Получает топ страниц по количеству просмотров."""
        query = select(
            PageView.page_path,
            func.count(PageView.id).label("count"),
        ).group_by(PageView.page_path)

        if start_date:
            query = query.where(PageView.viewed_at >= start_date)
        if end_date:
            query = query.where(PageView.viewed_at <= end_date)

        query = query.order_by(desc("count")).limit(limit)

        result = await self.session.execute(query)
        return [
            {"page_path": row.page_path, "count": row.count} for row in result.all()
        ]

    async def get_top_events(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Получает топ событий по количеству."""
        query = select(
            UserEvent.event_type,
            func.count(UserEvent.id).label("count"),
        ).group_by(UserEvent.event_type)

        if start_date:
            query = query.where(UserEvent.created_at >= start_date)
        if end_date:
            query = query.where(UserEvent.created_at <= end_date)

        query = query.order_by(desc("count")).limit(limit)

        result = await self.session.execute(query)
        return [
            {"event_type": row.event_type, "count": row.count} for row in result.all()
        ]

    async def get_power_users(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Получает топ активных пользователей (power users)."""
        query = select(
            User.id,
            User.username,
            func.count(UserEvent.id).label("events_count"),
        ).join(UserEvent, User.id == UserEvent.user_id)

        if start_date:
            query = query.where(UserEvent.created_at >= start_date)
        if end_date:
            query = query.where(UserEvent.created_at <= end_date)

        query = query.group_by(User.id, User.username)
        query = query.order_by(desc("events_count")).limit(limit)

        result = await self.session.execute(query)
        return [
            {
                "user_id": row.id,
                "username": row.username,
                "events_count": row.events_count,
            }
            for row in result.all()
        ]

    async def get_conversion_funnel(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Получает воронку конверсий по типам."""
        query = select(
            Conversion.conversion_type,
            func.count(Conversion.id).label("count"),
            func.sum(Conversion.conversion_value).label("total_value"),
        ).group_by(Conversion.conversion_type)

        if start_date:
            query = query.where(Conversion.converted_at >= start_date)
        if end_date:
            query = query.where(Conversion.converted_at <= end_date)

        query = query.order_by(desc("count"))

        result = await self.session.execute(query)
        return [
            {
                "type": row.conversion_type,
                "count": row.count,
                "total_value": float(row.total_value) if row.total_value else 0.0,
            }
            for row in result.all()
        ]

    async def get_avg_pages_per_session(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Получает среднее количество страниц за сессию."""
        query = select(
            func.count(PageView.id)
            / func.nullif(func.count(func.distinct(PageView.session_id)), 0)
        )

        if start_date:
            query = query.where(PageView.viewed_at >= start_date)
        if end_date:
            query = query.where(PageView.viewed_at <= end_date)

        result = await self.session.execute(query)
        avg = result.scalar_one()
        return float(avg) if avg else 0.0
