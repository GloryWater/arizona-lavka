"""
Metrics routes - endpoints для сбора метрик пользователей.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from models import (
    ConversionRequest,
    ConversionResponse,
    PageViewRequest,
    PageViewResponse,
    SessionEndRequest,
    SessionEndResponse,
    SessionStartRequest,
    SessionStartResponse,
    UserEventRequest,
    UserEventResponse,
)
from services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


def get_metrics_service(
    session: AsyncSession = Depends(get_db_session),
) -> MetricsService:
    """Создаёт экземпляр MetricsService."""
    return MetricsService(session)


def get_optional_user_id(
    request: Request,
) -> Optional[int]:
    """
    Получает ID пользователя из запроса (если аутентифицирован).

    Возвращает None если пользователь не аутентифицирован.
    """
    # Получаем пользователя из состояния запроса (устанавливается middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return user.id
    return None


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    data: SessionStartRequest,
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Начинает новую сессию пользователя.

    - **session_id**: UUID сессии (генерируется на клиенте)
    - **utm_source**: UTM метка источника
    - **utm_medium**: UTM метка типа трафика
    - **utm_campaign**: UTM метка кампании
    - **device_info**: Информация об устройстве (JSON)

    Для анонимных пользователей session_id хранится в localStorage.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    result = await service.start_session(data, ip_address, user_agent)

    status_code = 200 if result.get("status") != "error_logged" else 200
    return SessionStartResponse(
        session_id=result["session_id"],
        status=(
            "started"
            if result.get("status") in ["started", "continued"]
            else "error_logged"
        ),
        error_logged=result.get("status") == "error_logged",
    )


@router.post("/session/end", response_model=SessionEndResponse)
async def end_session(
    data: SessionEndRequest,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Завершает сессию пользователя.

    Вызывается при закрытии вкладки или уходе с сайта.
    """
    result = await service.end_session(data)

    return SessionEndResponse(
        session_id=data.session_id,
        status="ended" if result.get("status") == "ended" else "error_logged",
        error_logged=result.get("status") == "error_logged",
    )


@router.post("/pageview", response_model=PageViewResponse)
async def track_pageview(
    data: PageViewRequest,
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Отслеживает просмотр страницы.

    - **session_id**: UUID сессии
    - **page_path**: Путь страницы (например, /lavka/123)
    - **page_title**: Заголовок страницы
    - **referrer**: Referrer URL
    - **time_on_page**: Время на странице в секундах

    Автоматически вызывается при изменении маршрута.
    """
    user_id = get_optional_user_id(request)
    result = await service.track_page_view(data, user_id)

    return PageViewResponse(
        status="recorded" if result.get("status") == "recorded" else "error_logged",
        error_logged=result.get("status") == "error_logged",
    )


@router.post("/event", response_model=UserEventResponse)
async def track_event(
    data: UserEventRequest,
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Отслеживает действие пользователя.

    Типы событий:
    - **search_performed**: Пользователь выполнил поиск
    - **filter_applied**: Применён фильтр
    - **config_generated**: Сгенерирован конфиг
    - **config_exported**: Экспортирован конфиг
    - **lavka_viewed**: Просмотр лавки
    - **offer_clicked**: Клик по предложению
    - **login_completed**: Успешный вход

    Категории:
    - **navigation**: Навигационные события
    - **action**: Действия пользователя
    - **conversion**: Конверсии
    """
    user_id = get_optional_user_id(request)
    result = await service.track_event(data, user_id)

    return UserEventResponse(
        status="recorded" if result.get("status") == "recorded" else "error_logged",
        error_logged=result.get("status") == "error_logged",
    )


@router.post("/conversion", response_model=ConversionResponse)
async def track_conversion(
    data: ConversionRequest,
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Отслеживает конверсию.

    Типы конверсий:
    - **config_exported**: Экспорт конфига
    - **premium_purchased**: Покупка премиума
    - **daily_active**: Дневная активность (для DAU/MAU)

    - **conversion_value**: Денежное значение (если применимо)
    - **currency**: Валюта (по умолчанию RUB)
    - **attribution_source**: Источник атрибуции
    """
    user_id = get_optional_user_id(request)
    result = await service.track_conversion(data, user_id)

    return ConversionResponse(
        status="recorded" if result.get("status") == "recorded" else "error_logged",
        error_logged=result.get("status") == "error_logged",
    )
