"""
Admin metrics routes - endpoints для админ-дашборда метрик.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    get_current_user_required,
    get_db_session,
    get_db_session_no_commit,
)
from models import (
    AdminMetricsQueryParams,
    ConversionMetricsResponse,
    EngagementMetricsResponse,
    MetricsExportResponse,
    MetricsOverviewResponse,
    UserSegmentsResponse,
)
from services.auth_service import AuthService
from services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Admin Metrics"])


async def get_admin_user(
    current_user=Depends(get_current_user_required),
) -> dict:
    """
    Проверяет что пользователь является администратором.

    Returns:
        dict: Информация о пользователе

    Raises:
        HTTPException: Если пользователь не администратор
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора",
        )
    return current_user


def get_metrics_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> MetricsService:
    """Создаёт экземпляр MetricsService."""
    return MetricsService(session)


def get_date_range(
    range_param: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Вычисляет диапазон дат на основе параметров.

    Args:
        range_param: '7d', '30d', '90d', или 'custom'
        start_date: Дата начала в формате YYYY-MM-DD
        end_date: Дата окончания в формате YYYY-MM-DD

    Returns:
        Tuple[start_date, end_date] или [None, None] для диапазона по умолчанию
    """
    now = datetime.utcnow()

    if range_param == "7d":
        return now - timedelta(days=7), now
    elif range_param == "30d":
        return now - timedelta(days=30), now
    elif range_param == "90d":
        return now - timedelta(days=90), now
    elif range_param == "custom" and start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start, end
        except ValueError:
            pass

    # По умолчанию 30 дней
    return now - timedelta(days=30), now


@router.get("/overview", response_model=MetricsOverviewResponse)
async def get_overview_metrics(
    range: Optional[str] = "24h",
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Получает обзор метрик для дашборда.

    Возвращает:
    - DAU (Daily Active Users)
    - MAU (Monthly Active Users)
    - Средняя длительность сессии
    - Количество сессий за 24h
    - Количество событий за 24h
    - Количество просмотров за 24h
    - Количество конверсий за 24h
    - Общая выручка за 24h
    """
    hours = 24
    if range == "7d":
        hours = 7 * 24
    elif range == "30d":
        hours = 30 * 24

    metrics = await service.get_overview_metrics(hours=hours)
    return MetricsOverviewResponse(**metrics)


@router.get("/engagement", response_model=EngagementMetricsResponse)
async def get_engagement_metrics(
    range: Optional[str] = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Получает метрики вовлеченности.

    Возвращает:
    - Топ страниц по просмотрам
    - Топ действий пользователей
    - Retention rate
    - Среднее количество страниц за сессию
    """
    date_start, date_end = get_date_range(range, start_date, end_date)

    metrics = await service.get_engagement_metrics(
        start_date=date_start, end_date=date_end
    )
    return EngagementMetricsResponse(**metrics)


@router.get("/conversions", response_model=ConversionMetricsResponse)
async def get_conversion_metrics(
    range: Optional[str] = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Получает метрики конверсий.

    Возвращает:
    - Общее количество конверсий
    - Воронка конверсий по типам
    - Метрики выручки (total, avg, by_type)
    """
    date_start, date_end = get_date_range(range, start_date, end_date)

    metrics = await service.get_conversion_metrics(
        start_date=date_start, end_date=date_end
    )
    return ConversionMetricsResponse(**metrics)


@router.get("/users", response_model=UserSegmentsResponse)
async def get_user_segments(
    range: Optional[str] = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Получает сегменты пользователей.

    Возвращает:
    - Общее количество пользователей
    - Активные пользователи
    - Power users (топ 10% по активности)
    - Сегменты пользователей
    """
    date_start, date_end = get_date_range(range, start_date, end_date)

    metrics = await service.get_user_segments(start_date=date_start, end_date=date_end)
    return UserSegmentsResponse(**metrics)


@router.get("/export")
async def export_metrics(
    range: Optional[str] = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Экспортирует метрики в CSV формате.

    Возвращает CSV файл с данными о:
    - Сессиях
    - Просмотрах страниц
    - Событиях пользователей
    - Конверсиях
    """
    date_start, date_end = get_date_range(range, start_date, end_date)

    # Создаём CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовок
    writer.writerow(
        [
            "Type",
            "ID",
            "Session ID",
            "User ID",
            "Type/Path",
            "Created At",
            "Value",
        ]
    )

    # Получаем данные из репозитория
    repo = service.repository

    # Сессии
    sessions_query = await service.session.execute(
        select(UserSession)
        .where(UserSession.started_at >= date_start)
        .where(UserSession.started_at <= date_end)
        .limit(1000)
    )
    for session in sessions_query.scalars().all():
        writer.writerow(
            [
                "session",
                session.id,
                session.session_id,
                session.user_id,
                "",
                session.started_at.isoformat() if session.started_at else "",
                "",
            ]
        )

    # Page views
    pageviews_query = await service.session.execute(
        select(PageView)
        .where(PageView.viewed_at >= date_start)
        .where(PageView.viewed_at <= date_end)
        .limit(1000)
    )
    for pv in pageviews_query.scalars().all():
        writer.writerow(
            [
                "pageview",
                pv.id,
                pv.session_id,
                pv.user_id,
                pv.page_path,
                pv.viewed_at.isoformat() if pv.viewed_at else "",
                "",
            ]
        )

    # Events
    events_query = await service.session.execute(
        select(UserEvent)
        .where(UserEvent.created_at >= date_start)
        .where(UserEvent.created_at <= date_end)
        .limit(1000)
    )
    for event in events_query.scalars().all():
        writer.writerow(
            [
                "event",
                event.id,
                event.session_id,
                event.user_id,
                event.event_type,
                event.created_at.isoformat() if event.created_at else "",
                "",
            ]
        )

    # Conversions
    conversions_query = await service.session.execute(
        select(Conversion)
        .where(Conversion.converted_at >= date_start)
        .where(Conversion.converted_at <= date_end)
        .limit(1000)
    )
    for conv in conversions_query.scalars().all():
        writer.writerow(
            [
                "conversion",
                conv.id,
                conv.session_id,
                conv.user_id,
                conv.conversion_type,
                conv.converted_at.isoformat() if conv.converted_at else "",
                str(conv.conversion_value) if conv.conversion_value else "",
            ]
        )

    # Формируем ответ
    csv_content = output.getvalue()
    output.close()

    filename = f"metrics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/json")
async def export_metrics_json(
    range: Optional[str] = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user=Depends(get_admin_user),
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Экспортирует метрики в JSON формате.

    Возвращает сводные данные в JSON.
    """
    import json

    date_start, date_end = get_date_range(range, start_date, end_date)

    # Получаем все метрики
    overview = await service.get_overview_metrics(hours=720)  # 30 дней
    engagement = await service.get_engagement_metrics(
        start_date=date_start, end_date=date_end
    )
    conversions = await service.get_conversion_metrics(
        start_date=date_start, end_date=date_end
    )
    segments = await service.get_user_segments(start_date=date_start, end_date=date_end)

    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "date_range": {
            "start": date_start.isoformat() if date_start else None,
            "end": date_end.isoformat() if date_end else None,
        },
        "overview": overview,
        "engagement": engagement,
        "conversions": conversions,
        "user_segments": segments,
    }

    json_content = json.dumps(export_data, indent=2, default=str)

    filename = f"metrics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        io.BytesIO(json_content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Импорты для методов
from sqlalchemy import select

from infrastructure.database.models import Conversion, PageView, UserEvent, UserSession
