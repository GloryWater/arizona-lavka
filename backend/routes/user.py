"""
Роуты для пользователя.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user_required, get_db_session
from infrastructure.database.models import ConfigHistory, FavoriteItem, PriceAlert, User
from models import (
    FavoriteItemCreate,
    FavoriteItemResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    UserProfileResponse,
)

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Получение профиля пользователя."""
    # Подсчёт конфигов
    configs_count_result = await session.execute(
        select(func.count(ConfigHistory.id)).where(
            ConfigHistory.user_id == current_user.id
        )
    )
    configs_count = configs_count_result.scalar_one() or 0

    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_premium=current_user.is_premium,
        created_at=current_user.created_at,
        configs_count=configs_count,
    )


@router.get("/favorites")
async def get_favorites(
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Получение списка избранных предметов."""
    result = await session.execute(
        select(FavoriteItem)
        .where(FavoriteItem.user_id == current_user.id)
        .where(FavoriteItem.is_active == True)
        .order_by(FavoriteItem.created_at.desc())
    )
    favorites = result.scalars().all()

    return favorites


@router.post("/favorites", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    data: FavoriteItemCreate,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Добавление предмета в избранное."""
    favorite = FavoriteItem(
        user_id=current_user.id,
        item_id=data.item_id,
        item_name=data.item_name,
        target_price=data.target_price,
        target_percentage=data.target_percentage,
        mode=data.mode,
        server_id=data.server_id,
        notes=data.notes,
    )

    session.add(favorite)
    await session.commit()
    await session.refresh(favorite)

    return favorite


@router.delete("/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Удаление предмета из избранного."""
    favorite = await session.get(FavoriteItem, favorite_id)

    if not favorite:
        raise HTTPException(status_code=404, detail="Избранный предмет не найден")

    if favorite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    await session.delete(favorite)
    await session.commit()

    return {"message": "Предмет удалён из избранного"}


@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Получение списка уведомлений."""
    result = await session.execute(
        select(PriceAlert)
        .where(PriceAlert.user_id == current_user.id)
        .where(PriceAlert.is_active == True)
        .order_by(PriceAlert.created_at.desc())
    )
    alerts = result.scalars().all()

    return alerts


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: PriceAlertCreate,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Создание уведомления об изменении цены."""
    alert = PriceAlert(
        user_id=current_user.id,
        item_id=data.item_id,
        item_name=data.item_name,
        server_id=data.server_id,
        target_price=data.target_price,
        condition=data.condition,
    )

    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return alert


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Удаление уведомления."""
    alert = await session.get(PriceAlert, alert_id)

    if not alert:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    await session.delete(alert)
    await session.commit()

    return {"message": "Уведомление удалено"}
