"""
Роуты для генерации конфигов.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, ConfigHistory
from dependencies import get_db_session, get_current_user_required, get_config_generator_service
from models import ConfigGenerateRequest, ConfigItemResponse, ConfigHistoryResponse, ConfigMode
from services.config_generator_service import ConfigGeneratorService
from services.marketplace_service import MarketplaceService
from services.item_categories import get_all_categories
from config import get_server_name

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate")
async def generate_config(
    request: ConfigGenerateRequest,
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
    marketplace_service: MarketplaceService = Depends(lambda: None),  # Получим из config_generator
):
    """Сгенерировать торговый конфиг."""
    # Получаем данные из API
    users_data = await config_generator.marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    # Генерируем конфиг
    try:
        config_items, stats = await config_generator.generate_config(
            server_id=request.server_id,
            mode=request.mode,
            percentage=request.percentage,
            users_data=users_data,
            min_liquidity=request.min_liquidity,
        )
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")
    
    # Конвертируем в dict для JSON
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]
    
    # Сохраняем в историю если запрошено
    if request.save_to_history:
        config_history = ConfigHistory(
            user_id=current_user.id,
            server_id=request.server_id,
            server_name=get_server_name(request.server_id),
            mode=request.mode.value,
            percentage=request.percentage,
            items_count=len(config_items),
            config_data=config_data,
            used_historical_data=stats["items_with_history"] > 0,
            confidence_score=stats["avg_confidence"],
        )
        config_generator.session.add(config_history)
        await config_generator.session.commit()
    
    return {
        "config": config_data,
        "total_items": stats["total_items"],
        "server_name": get_server_name(request.server_id),
        "mode": request.mode.value,
        "stats": stats,
    }


@router.post("/generate/download")
async def generate_and_download_config(
    request: ConfigGenerateRequest,
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
):
    """Сгенерировать и скачать конфиг."""
    users_data = await config_generator.marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    try:
        config_items, stats = await config_generator.generate_config(
            server_id=request.server_id,
            mode=request.mode,
            percentage=request.percentage,
            users_data=users_data,
            min_liquidity=request.min_liquidity,
        )
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")
    
    # Конвертируем в dict
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]
    
    # Сохраняем в историю
    if request.save_to_history:
        config_history = ConfigHistory(
            user_id=current_user.id,
            server_id=request.server_id,
            server_name=get_server_name(request.server_id),
            mode=request.mode.value,
            percentage=request.percentage,
            items_count=len(config_items),
            config_data=config_data,
            used_historical_data=stats["items_with_history"] > 0,
            confidence_score=stats["avg_confidence"],
        )
        config_generator.session.add(config_history)
        await config_generator.session.commit()

    # Генерируем JSON в формате для бота (cp1251)
    # Убираем лишние поля, оставляем только нужные для бота
    bot_config = []
    for item in config_items:
        item_dict = {
            "price": item.price,
            "maximum": item.maximum,
            "enabled": item.enabled,
            "name": item.name,
            "price_vc": item.price_vc,
            "count": item.count,
            "slot_count": item.slot_count,
            "slot_id": item.slot_id,
            "position_tab": item.position_tab,
            "all_count": item.all_count,
        }
        # Добавляем continue и count_maximum только если они есть
        if hasattr(item, 'continue_') and item.continue_:
            item_dict["continue"] = item.continue_
        if hasattr(item, 'count_maximum'):
            item_dict["count_maximum"] = item.count_maximum
        bot_config.append(item_dict)
    
    json_str = json.dumps(bot_config, ensure_ascii=False, indent=4)

    logger.info(f"Генерация JSON конфига: {len(config_items)} предметов, размер JSON: {len(json_str)} байт")

    return Response(
        content=json_str.encode("cp1251"),
        media_type="application/json; charset=cp1251",
        headers={
            "Content-Disposition": f'attachment; filename="config_{request.mode.value.lower()}_{request.server_id}.json"',
        },
    )


@router.get("/history")
async def get_config_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Получить историю конфигов пользователя."""
    query = (
        select(ConfigHistory)
        .where(ConfigHistory.user_id == current_user.id)
        .order_by(desc(ConfigHistory.created_at))
        .limit(limit)
    )

    result = await session.execute(query)
    configs = result.scalars().all()

    return [
        ConfigHistoryResponse(
            id=config.id,
            server_name=config.server_name,
            server_id=config.server_id,
            mode=config.mode,
            percentage=config.percentage,
            items_count=config.items_count,
            created_at=config.created_at,
            download_count=config.download_count,
        )
        for config in configs
    ]


@router.get("/history/{config_id}")
async def get_config_detail(
    config_id: int,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session),
):
    """Получить детали конфига и скачать."""
    config = await session.get(ConfigHistory, config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Конфиг не найден")
    
    # Проверка принадлежности
    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    # Увеличиваем счётчик скачиваний
    config.download_count += 1
    await session.commit()
    
    # Генерируем JSON
    json_str = json.dumps(config.config_data, ensure_ascii=False, indent=4)
    
    return Response(
        content=json_str.encode("cp1251"),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="config_{config.mode}_{config.server_id}.json"',
        },
    )


@router.post("/generate/liquidity")
async def generate_config_by_liquidity(
    server_id: int = Query(..., ge=0, le=32),
    mode: ConfigMode = Query(...),
    percentage: float = Query(default=0, ge=-50, le=50),
    top_count: int = Query(default=10, ge=5, le=100),
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
):
    """Сгенерировать конфиг топ-N предметов по ликвидности."""
    users_data = await config_generator.marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    try:
        config_items, stats = await config_generator.generate_config_by_liquidity(
            server_id=server_id,
            mode=mode,
            percentage=percentage,
            users_data=users_data,
            top_count=top_count,
        )
    except Exception as e:
        logger.error(f"Error generating config by liquidity: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    return {
        "config": config_data,
        "stats": stats,
        "server_name": get_server_name(server_id),
        "mode": mode.value,
    }


@router.post("/generate/category")
async def generate_config_by_category(
    server_id: int = Query(..., ge=0, le=32),
    mode: ConfigMode = Query(...),
    percentage: float = Query(default=0, ge=-50, le=50),
    category: str = Query(default="all", description="Ключ категории"),
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
):
    """Сгенерировать конфиг предметов определённой категории."""
    users_data = await config_generator.marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    try:
        config_items, stats = await config_generator.generate_config_by_category(
            server_id=server_id,
            mode=mode,
            percentage=percentage,
            users_data=users_data,
            category=category,
        )
    except Exception as e:
        logger.error(f"Error generating config by category: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    return {
        "config": config_data,
        "stats": stats,
        "server_name": get_server_name(server_id),
        "mode": mode.value,
    }


@router.get("/categories")
async def get_categories():
    """Получить список всех категорий предметов."""
    return {"categories": get_all_categories()}
