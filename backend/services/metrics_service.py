"""
Metrics Service - сервис для работы с метриками пользователей.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.repositories import MetricsRepository
from models import (
    ConversionRequest,
    EventCategory,
    PageViewRequest,
    SessionEndRequest,
    SessionStartRequest,
    UserEventRequest,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Сервис для управления метриками пользователей.

    Предоставляет методы для:
    - Управления сессиями
    - Отслеживания просмотров страниц
    - Отслеживания действий пользователей
    - Отслеживания конверсий
    - Получения аналитики
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.session = session
        self.repository = MetricsRepository(session)

    # =========================================================================
    # Session Management
    # =========================================================================

    async def start_session(
        self,
        data: SessionStartRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Начинает новую сессию пользователя.

        Args:
            data: Данные запроса
            ip_address: IP адрес клиента
            user_agent: User-Agent строка

        Returns:
            Dict с session_id и статусом
        """
        try:
            # Проверяем, существует ли уже сессия
            existing = await self.repository.get_session_by_id_field(data.session_id)
            if existing:
                # Обновляем last_active_at
                await self.repository.update_session(
                    existing,
                    last_active_at=datetime.utcnow(),
                )
                return {"session_id": data.session_id, "status": "continued"}

            # Создаём новую сессию
            session = await self.repository.create_session(
                session_id=data.session_id,
                ip_address=self._anonymize_ip(ip_address) if ip_address else None,
                user_agent=user_agent,
                device_info=data.device_info,
                utm_source=data.utm_source,
                utm_medium=data.utm_medium,
                utm_campaign=data.utm_campaign,
            )

            logger.info(f"Started new session: {data.session_id}")
            return {"session_id": data.session_id, "status": "started"}

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return {"session_id": data.session_id, "status": "error_logged"}

    async def end_session(self, data: SessionEndRequest) -> Dict[str, Any]:
        """
        Завершает сессию пользователя.

        Args:
            data: Данные запроса

        Returns:
            Dict с session_id и статусом
        """
        try:
            session = await self.repository.get_session_by_id_field(data.session_id)
            if not session:
                logger.warning(f"Session not found: {data.session_id}")
                return {"session_id": data.session_id, "status": "not_found"}

            await self.repository.end_session(session)
            logger.info(f"Ended session: {data.session_id}")
            return {"session_id": data.session_id, "status": "ended"}

        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {"session_id": data.session_id, "status": "error_logged"}

    async def link_session_to_user(
        self,
        session_id: str,
        user_id: int,
    ) -> bool:
        """
        Привязывает сессию к пользователю после аутентификации.

        Args:
            session_id: ID сессии
            user_id: ID пользователя

        Returns:
            True если успешно
        """
        try:
            session = await self.repository.get_session_by_id_field(session_id)
            if not session:
                return False

            if session.user_id is None:
                await self.repository.link_session_to_user(session, user_id)
                logger.info(f"Linked session {session_id} to user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Error linking session to user: {e}")
            return False

    # =========================================================================
    # Page View Tracking
    # =========================================================================

    async def track_page_view(
        self,
        data: PageViewRequest,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отслеживает просмотр страницы.

        Args:
            data: Данные запроса
            user_id: ID пользователя (если аутентифицирован)

        Returns:
            Dict со статусом
        """
        try:
            # Sanitize page_path (prevent XSS)
            sanitized_path = self._sanitize_path(data.page_path)

            await self.repository.create_page_view(
                session_id=data.session_id,
                page_path=sanitized_path,
                user_id=user_id,
                page_title=data.page_title,
                referrer=data.referrer,
                time_on_page=data.time_on_page,
            )

            # Обновляем last_active_at сессии
            await self._update_session_activity(data.session_id)

            return {"status": "recorded"}

        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
            return {"status": "error_logged"}

    # =========================================================================
    # User Event Tracking
    # =========================================================================

    async def track_event(
        self,
        data: UserEventRequest,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отслеживает действие пользователя.

        Args:
            data: Данные запроса
            user_id: ID пользователя (если аутентифицирован)

        Returns:
            Dict со статусом
        """
        try:
            await self.repository.create_event(
                session_id=data.session_id,
                event_type=data.event_type,
                event_category=data.event_category.value,
                user_id=user_id,
                event_data=data.event_data,
                error_message=data.error_message,
            )

            # Обновляем last_active_at сессии
            await self._update_session_activity(data.session_id)

            return {"status": "recorded"}

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return {"status": "error_logged"}

    # =========================================================================
    # Conversion Tracking
    # =========================================================================

    async def track_conversion(
        self,
        data: ConversionRequest,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отслеживает конверсию.

        Args:
            data: Данные запроса
            user_id: ID пользователя (если аутентифицирован)

        Returns:
            Dict со статусом
        """
        try:
            conversion_value = (
                Decimal(str(data.conversion_value)) if data.conversion_value else None
            )

            await self.repository.create_conversion(
                session_id=data.session_id,
                conversion_type=data.conversion_type,
                user_id=user_id,
                conversion_value=conversion_value,
                currency=data.currency,
                attribution_source=data.attribution_source,
            )

            logger.info(
                f"Tracked conversion: {data.conversion_type}, "
                f"value: {conversion_value} {data.currency}"
            )

            return {"status": "recorded"}

        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            return {"status": "error_logged"}

    # =========================================================================
    # Analytics Methods
    # =========================================================================

    async def get_overview_metrics(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Получает обзор метрик для дашборда.

        Args:
            hours: Период в часах (по умолчанию 24)

        Returns:
            Dict с метриками
        """
        now = datetime.utcnow()
        start_date = now - timedelta(hours=hours)

        dau = await self.repository.get_dau(now)
        mau = await self.repository.get_mau(now)
        avg_duration = await self.repository.get_avg_session_duration(start_date, now)
        total_sessions = await self.repository.get_total_sessions(start_date, now)
        total_events = await self.repository.get_total_events(start_date, now)
        total_page_views = await self.repository.get_total_page_views(start_date, now)
        total_conversions = await self.repository.get_total_conversions(start_date, now)
        total_revenue = await self.repository.get_total_revenue(start_date, now)

        return {
            "dau": dau,
            "mau": mau,
            "avg_session_duration": avg_duration,
            "total_sessions_24h": total_sessions,
            "total_events_24h": total_events,
            "total_page_views_24h": total_page_views,
            "total_conversions_24h": total_conversions,
            "total_revenue_24h": float(total_revenue),
        }

    async def get_engagement_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Получает метрики вовлеченности.

        Returns:
            Dict с метриками вовлеченности
        """
        top_pages = await self.repository.get_top_pages(
            limit=10, start_date=start_date, end_date=end_date
        )
        top_actions = await self.repository.get_top_events(
            limit=10, start_date=start_date, end_date=end_date
        )
        avg_pages = await self.repository.get_avg_pages_per_session(
            start_date=start_date, end_date=end_date
        )

        # Расчёт retention rate (упрощённо)
        retention_rate = await self._calculate_retention_rate(start_date, end_date)

        return {
            "top_pages": top_pages,
            "top_actions": top_actions,
            "retention_rate": retention_rate,
            "avg_pages_per_session": avg_pages,
        }

    async def get_conversion_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Получает метрики конверсий.

        Returns:
            Dict с метриками конверсий
        """
        funnel = await self.repository.get_conversion_funnel(
            start_date=start_date, end_date=end_date
        )
        total_conversions = sum(item["count"] for item in funnel)

        total_revenue = sum(item["total_value"] for item in funnel)
        avg_revenue = total_revenue / total_conversions if total_conversions > 0 else 0

        revenue_by_type = {item["type"]: item["total_value"] for item in funnel}

        return {
            "total_conversions": total_conversions,
            "conversion_funnel": funnel,
            "revenue_metrics": {
                "total": total_revenue,
                "avg": avg_revenue,
                "by_type": revenue_by_type,
            },
        }

    async def get_user_segments(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Получает сегменты пользователей.

        Returns:
            Dict с сегментами
        """
        power_users = await self.repository.get_power_users(
            limit=10, start_date=start_date, end_date=end_date
        )

        # Подсчёт общего количества пользователей
        total_users_result = await self.session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar_one() or 0

        # Активные пользователи (за последний месяц)
        active_users = await self.repository.get_mau()

        # Сегменты (упрощённо)
        segments = {
            "new_users": 0,  # Можно доработать
            "regular_users": active_users - len(power_users),
            "power_users": len(power_users),
        }

        return {
            "total_users": total_users,
            "active_users": active_users,
            "power_users": power_users,
            "user_segments": segments,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _update_session_activity(self, session_id: str) -> None:
        """Обновляет last_active_at для сессии."""
        try:
            session = await self.repository.get_session_by_id_field(session_id)
            if session:
                await self.repository.update_session(
                    session,
                    last_active_at=datetime.utcnow(),
                )
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")

    def _anonymize_ip(self, ip_address: str) -> str:
        """
        Анонимизирует IP адрес (сохраняет /24 подсеть).

        Для IPv4: 192.168.1.123 -> 192.168.1.0
        """
        try:
            if ":" in ip_address:  # IPv6
                parts = ip_address.split(":")
                return ":".join(parts[:3]) + "::/48"
            else:  # IPv4
                parts = ip_address.split(".")
                return ".".join(parts[:3]) + ".0/24"
        except Exception:
            return ip_address

    def _sanitize_path(self, path: str) -> str:
        """
        Санизирует page_path для предотвращения XSS.

        Удаляет опасные символы и нормализует путь.
        """
        # Удаляем потенциально опасные символы
        sanitized = (
            path.replace("<", "").replace(">", "").replace('"', "").replace("'", "")
        )
        # Нормализуем путь
        if not sanitized.startswith("/"):
            sanitized = "/" + sanitized
        # Ограничиваем длину
        return sanitized[:500]

    async def _calculate_retention_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """
        Рассчитывает retention rate (упрощённо).

        Retention = (пользователи, активные в текущем периоде и предыдущем) /
                    (пользователи, активные в предыдущем периоде)
        """
        if end_date is None:
            end_date = datetime.utcnow()

        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # Предыдущий период такой же длительности
        period_duration = end_date - start_date
        prev_start = start_date - period_duration
        prev_end = start_date

        # Пользователи в предыдущем периоде
        prev_result = await self.session.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                and_(
                    UserSession.user_id.isnot(None),
                    UserSession.started_at >= prev_start,
                    UserSession.started_at < prev_end,
                )
            )
        )
        prev_users = (await prev_result).scalar_one() or 0

        # Пользователи в обоих периодах (упрощённо - просто текущие активные)
        current_users = await self.repository.get_mau(end_date)

        if prev_users == 0:
            return 0.0

        # Упрощённый расчёт
        retention = (current_users / prev_users) * 100 if prev_users > 0 else 0
        return min(retention, 100.0)  # Ограничиваем 100%


# Импорты для методов
from sqlalchemy import and_, func, select

from infrastructure.database.models import User, UserSession
