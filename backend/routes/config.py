"""
Роуты для генерации конфигов.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import json
import logging
import random
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, ConfigHistory
from dependencies import get_db_session, get_db_session_no_commit, get_current_user_required, get_config_generator_service
from models import ConfigGenerateRequest, ConfigItemResponse, ConfigHistoryResponse, ConfigMode
from services.config_generator_service import ConfigGeneratorService
from services.marketplace_service import MarketplaceService
from services.item_categories import get_all_categories
from services.audit_log_service import AuditLogService
from config import get_server_name

router = APIRouter()
logger = logging.getLogger(__name__)


def get_audit_service(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AuditLogService:
    """Создаёт экземпляр AuditLogService."""
    return AuditLogService(session)


@router.post("/generate")
async def generate_config(
    request: ConfigGenerateRequest,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session_no_commit),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
    marketplace_service: MarketplaceService = Depends(lambda: None),  # Получим из config_generator
):
    """Сгенерировать торговый конфиг."""
    # Валидация server_id перед генерацией
    from config import SERVER_NAMES
    if request.server_id not in SERVER_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный server_id: {request.server_id}. Допустимые значения: 0-32"
        )

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
    except ValueError as e:
        # Обработка ошибок валидации данных
        logger.error(f"Validation error generating config: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    # Конвертируем в dict для JSON
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    # Сохраняем в историю если запрошено (в транзакции)
    if request.save_to_history:
        try:
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
            session.add(config_history)
            # Явный commit для атомарности операции
            await session.commit()
            logger.info(f"Конфиг сохранён в историю: user_id={current_user.id}, server_id={request.server_id}")
        except Exception as e:
            # Откат транзакции при ошибке сохранения
            await session.rollback()
            logger.error(f"Error saving config to history: {e}")
            # Не прерываем операцию, конфиг всё равно возвращается пользователю

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
    request_ctx: Request,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_db_session_no_commit),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
    audit_service: AuditLogService = Depends(get_audit_service),
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
    except ValueError as e:
        # Обработка ошибок валидации данных
        logger.error(f"Validation error generating config: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    # Конвертируем в dict
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    # Сохраняем в историю
    if request.save_to_history:
        try:
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
            session.add(config_history)
            # Явный commit для атомарности операции
            await session.commit()
            logger.info(f"Конфиг сохранён в историю (download): user_id={current_user.id}, server_id={request.server_id}")
        except Exception as e:
            # Откат транзакции при ошибке сохранения
            await session.rollback()
            logger.error(f"Error saving config to history (download): {e}")
            # Не прерываем операцию, конфиг всё равно возвращается пользователю

    # Логирование события генерации конфига
    ip_address = request_ctx.client.host if request_ctx.client else None
    try:
        await audit_service.log_config_generated(
            user_id=current_user.id,
            username=current_user.username,
            server_id=request.server_id,
            mode=request.mode.value,
            items_count=len(config_items),
            ip_address=ip_address,
        )
    except Exception as e:
        # Логирование ошибки аудита, но не прерываем операцию
        logger.error(f"Failed to log config generation: {e}")

    # Генерируем JSON в формате для бота (UTF-8 с BOM для совместимости с Windows/cp1251)
    # Формат как в ArzMarket_Drake_sell4138.json
    bot_config = []
    for item in config_items:
        item_dict = {
            "price": str(item.price),
            "maximum": item.maximum,
            "continue": "1",
            "all_count": item.all_count,
            "price_vc": str(item.price_vc),
            "position_tab": item.position_tab,
            "enabled": item.enabled,
            "count": str(item.count),
            "name": item.name,
            "count_maximum": 0,
        }
        bot_config.append(item_dict)

    json_str = json.dumps(bot_config, ensure_ascii=False, indent=2)

    logger.info(f"Генерация JSON конфига: {len(config_items)} предметов, размер JSON: {len(json_str)} байт")

    # Формат имени: action_server_numbers.json
    server_name_file = get_server_name(request.server_id).lower().replace(" ", "_")
    action_file = "sell" if request.mode.value == "SELL" else "buy"
    random_num = random.randint(1000, 9999999)

    # Используем кодировку cp1251 (Windows-1251) для совместимости с Windows
    json_bytes = json_str.encode("cp1251")

    return Response(
        content=json_bytes,
        media_type="application/json; charset=cp1251",
        headers={
            "Content-Disposition": f'attachment; filename="{action_file}_{server_name_file}_{random_num}.json"',
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
        media_type="application/json; charset=cp1251",
        headers={
            "Content-Disposition": f'attachment; filename="config_{config.mode}_{config.server_id}.json"',
        },
    )


@router.post("/generate/liquidity")
async def generate_config_by_liquidity(
    request_ctx: Request,
    server_id: int = Query(..., ge=0, le=32),
    mode: ConfigMode = Query(...),
    percentage: float = Query(default=0, ge=-50, le=50),
    top_count: int = Query(default=20, ge=5, le=100),
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
    audit_service: AuditLogService = Depends(get_audit_service),
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
    except ValueError as e:
        # Обработка ошибок валидации данных
        logger.error(f"Validation error generating config by liquidity: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating config by liquidity: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    # Логирование события генерации конфига
    ip_address = request_ctx.client.host if request_ctx.client else None
    await audit_service.log_config_generated(
        user_id=current_user.id,
        username=current_user.username,
        server_id=server_id,
        mode=mode.value,
        items_count=len(config_items),
        ip_address=ip_address,
    )

    # Конвертируем в dict для JSON
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    return {
        "config": config_data,
        "total_items": stats["total_items"],
        "server_name": get_server_name(server_id),
        "mode": mode.value,
        "stats": stats,
    }


@router.post("/generate/category")
async def generate_config_by_category(
    request_ctx: Request,
    server_id: int = Query(..., ge=0, le=32),
    mode: ConfigMode = Query(...),
    percentage: float = Query(default=0, ge=-50, le=50),
    category: str = Query(default="all", description="Ключ категории"),
    current_user: User = Depends(get_current_user_required),
    config_generator: ConfigGeneratorService = Depends(get_config_generator_service),
    audit_service: AuditLogService = Depends(get_audit_service),
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
    except ValueError as e:
        # Обработка ошибок валидации данных
        logger.error(f"Validation error generating config by category: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating config by category: {e}")
        raise HTTPException(status_code=500, detail="Error generating config")

    # Логирование события генерации конфига
    ip_address = request_ctx.client.host if request_ctx.client else None
    await audit_service.log_config_generated(
        user_id=current_user.id,
        username=current_user.username,
        server_id=server_id,
        mode=mode.value,
        items_count=len(config_items),
        ip_address=ip_address,
    )

    # Конвертируем в dict для JSON
    config_data = [item.model_dump(mode="json", by_alias=True) for item in config_items]

    return {
        "config": config_data,
        "total_items": stats["total_items"],
        "server_name": get_server_name(server_id),
        "mode": mode.value,
        "stats": stats,
    }


@router.get("/categories")
async def get_categories():
    """Получить список всех категорий предметов."""
    return {"categories": get_all_categories()}


@router.get("/settings")
async def get_config_settings(
    session: AsyncSession = Depends(get_db_session),
):
    """Получить настройки генерации конфигов."""
    from database import GlobalSetting
    from sqlalchemy import select

    result = await session.execute(
        select(GlobalSetting).where(GlobalSetting.key == "config_generation_methods")
    )
    setting = result.scalar_one_or_none()

    if setting:
        return [setting]
    
    # Возвращаем настройки по умолчанию
    return [{
        "key": "config_generation_methods",
        "value": {
            "allow_all": True,
            "allow_liquidity": True,
            "allow_category": True,
        },
    }]
