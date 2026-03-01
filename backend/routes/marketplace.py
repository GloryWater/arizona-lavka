"""
Роуты marketplace - публичные endpoints.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, HTTPException, status

from config import SERVER_NAMES, get_server_name
from dependencies import get_marketplace_service, get_lavka_service
from models import OfferType, OffersResponse, Offer, ServerInfo
from services.marketplace_service import MarketplaceService
from services.lavka_service import LavkaService

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_offers(
    users_data: list,
    search_term: str = "",
    server_id: Optional[int] = None,
    sort_order: str = "none",
) -> list[Offer]:
    """
    Парсит данные пользователей в список предложений.

    Оптимизация: один проход по данным, предварительная фильтрация серверов.
    """
    offers = []
    search_lower = search_term.lower() if search_term else None

    for user_data in users_data:
        user_server = user_data.get("serverId")
        if server_id is not None and user_server != server_id:
            continue

        # Корректная обработка LavkaUid - пропускаем пользователей без лавки
        lavka_uid_raw = user_data.get("LavkaUid")
        if lavka_uid_raw is None or lavka_uid_raw == 0:
            continue
        lavka_uid = str(lavka_uid_raw)

        username = user_data.get("username") or "Unknown"
        user_status = bool(user_data.get("userStatus", 0))

        # Предметы на продажу (SELL)
        items_sell = user_data.get("items_sell") or []
        prices_sell = user_data.get("price_sell") or []
        counts_sell = user_data.get("count_sell") or []

        if items_sell and prices_sell and counts_sell:
            min_len = min(len(items_sell), len(prices_sell), len(counts_sell))
            for i in range(min_len):
                try:
                    item_value = items_sell[i]
                    parsed_id = LavkaService.parse_item_id(item_value)
                    if parsed_id is None:
                        continue

                    item_name = LavkaService.get_item_name(parsed_id)

                    if search_lower and search_lower not in item_name.lower():
                        continue

                    offers.append(Offer(
                        type=OfferType.SELL,
                        itemId=parsed_id,
                        itemName=item_name,
                        price=float(prices_sell[i]),
                        count=int(counts_sell[i]),
                        username=username,
                        lavkaUid=lavka_uid,
                        serverId=user_server,
                        userStatus=user_status,
                    ))
                except (ValueError, TypeError, IndexError):
                    continue

        # Предметы на покупку (BUY)
        items_buy = user_data.get("items_buy") or []
        prices_buy = user_data.get("price_buy") or []
        counts_buy = user_data.get("count_buy") or []

        if items_buy and prices_buy and counts_buy:
            min_len = min(len(items_buy), len(prices_buy), len(counts_buy))
            for i in range(min_len):
                try:
                    item_value = items_buy[i]
                    parsed_id = LavkaService.parse_item_id(item_value)
                    if parsed_id is None:
                        continue

                    item_name = LavkaService.get_item_name(parsed_id)

                    if search_lower and search_lower not in item_name.lower():
                        continue

                    offers.append(Offer(
                        type=OfferType.BUY,
                        itemId=parsed_id,
                        itemName=item_name,
                        price=float(prices_buy[i]),
                        count=int(counts_buy[i]),
                        username=username,
                        lavkaUid=lavka_uid,
                        serverId=user_server,
                        userStatus=user_status,
                    ))
                except (ValueError, TypeError, IndexError):
                    continue

    # Сортировка
    if sort_order == "asc":
        offers.sort(key=lambda x: x.price)
    elif sort_order == "desc":
        offers.sort(key=lambda x: x.price, reverse=True)

    return offers


def _parse_offers_split(
    users_data: list,
    search_term: str = "",
    server_id: Optional[int] = None,
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Парсит данные пользователей в разделённые предложения (скупка/продажа).

    Оптимизация: один проход по данным, предварительная фильтрация серверов,
    кэширование search_lower для производительности.

    Args:
        users_data: Данные пользователей из API
        search_term: Поисковый запрос
        server_id: ID сервера (None = все серверы)
        sort_order: Сортировка (asc, desc, none)
        limit: Лимит результатов
        offset: Смещение

    Returns:
        Dict с buy_offers, sell_offers и метаданными пагинации
    """
    buy_offers: List[Offer] = []
    sell_offers: List[Offer] = []
    search_lower = search_term.lower() if search_term else None

    # Предварительная фильтрация по серверу для производительности
    filtered_users = (
        users_data if server_id is None
        else [u for u in users_data if u.get("serverId") == server_id]
    )

    for user_data in filtered_users:
        # Корректная обработка LavkaUid - пропускаем пользователей без лавки
        lavka_uid_raw = user_data.get("LavkaUid")
        if lavka_uid_raw is None or lavka_uid_raw == 0:
            continue
        lavka_uid = str(lavka_uid_raw)

        username = user_data.get("username") or "Unknown"
        user_status = bool(user_data.get("userStatus", 0))
        user_server = user_data.get("serverId")

        # Логирование для отладки (только первый пользователь)
        if len(sell_offers) == 0 and len(buy_offers) == 0:
            logger.debug(f"User: {username}, LavkaUid: {lavka_uid}, Server: {user_server}")

        # Предметы на продажу (SELL - игрок продает)
        items_sell = user_data.get("items_sell") or []
        prices_sell = user_data.get("price_sell") or []
        counts_sell = user_data.get("count_sell") or []

        if items_sell and prices_sell and counts_sell:
            min_len = min(len(items_sell), len(prices_sell), len(counts_sell))
            for i in range(min_len):
                try:
                    item_value = items_sell[i]
                    parsed_id = LavkaService.parse_item_id(item_value)
                    if parsed_id is None:
                        continue

                    item_name = LavkaService.get_item_name(parsed_id)

                    if search_lower and search_lower not in item_name.lower():
                        continue

                    sell_offers.append(Offer(
                        type=OfferType.SELL,
                        itemId=parsed_id,
                        itemName=item_name,
                        price=float(prices_sell[i]),
                        count=int(counts_sell[i]),
                        username=username,
                        lavkaUid=lavka_uid,
                        serverId=user_server,
                        userStatus=user_status,
                    ))
                except (ValueError, TypeError, IndexError):
                    continue

        # Предметы на покупку (BUY - игрок покупает/скупает)
        items_buy = user_data.get("items_buy") or []
        prices_buy = user_data.get("price_buy") or []
        counts_buy = user_data.get("count_buy") or []

        if items_buy and prices_buy and counts_buy:
            min_len = min(len(items_buy), len(prices_buy), len(counts_buy))
            for i in range(min_len):
                try:
                    item_value = items_buy[i]
                    parsed_id = LavkaService.parse_item_id(item_value)
                    if parsed_id is None:
                        continue

                    item_name = LavkaService.get_item_name(parsed_id)

                    if search_lower and search_lower not in item_name.lower():
                        continue

                    buy_offers.append(Offer(
                        type=OfferType.BUY,
                        itemId=parsed_id,
                        itemName=item_name,
                        price=float(prices_buy[i]),
                        count=int(counts_buy[i]),
                        username=username,
                        lavkaUid=lavka_uid,
                        serverId=user_server,
                        userStatus=user_status,
                    ))
                except (ValueError, TypeError, IndexError):
                    continue

    # Сортировка по цене в зависимости от sort_order
    if sort_order == "asc":
        buy_offers.sort(key=lambda x: x.price)
        sell_offers.sort(key=lambda x: x.price)
    elif sort_order == "desc":
        buy_offers.sort(key=lambda x: x.price, reverse=True)
        sell_offers.sort(key=lambda x: x.price, reverse=True)
    # При "none" сортировка не применяется

    # Сохраняем общие количества до пагинации
    total_buy = len(buy_offers)
    total_sell = len(sell_offers)

    # Применяем пагинацию к каждому списку отдельно
    buy_offers = buy_offers[offset:offset + limit]
    sell_offers = sell_offers[offset:offset + limit]

    return {
        "buy_offers": buy_offers,
        "sell_offers": sell_offers,
        "total_buy": total_buy,
        "total_sell": total_sell,
        "limit": limit,
        "offset": offset,
    }


@router.get("/servers")
async def get_servers():
    """Получить список всех серверов."""
    servers = [{"id": sid, "name": name} for sid, name in SERVER_NAMES.items()]
    return {"servers": servers, "total": len(servers)}


@router.get("/items")
async def get_items():
    """Получить mapping всех предметов."""
    import json
    from pathlib import Path

    items_file = Path(__file__).parent.parent / "items.json"
    try:
        with open(items_file, "r", encoding="utf-8") as f:
            items = json.load(f)
        return items
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Items mapping not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid items JSON format")


@router.get("/offers", response_model=OffersResponse)
async def get_offers(
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    search_term: str = Query(default="", max_length=100, description="Поисковый запрос"),
    server_id: Optional[int] = Query(default=None, ge=-1, le=32, description="ID сервера"),
    sort_order: str = Query(default="none", pattern="^(asc|desc|none)$", description="Сортировка"),
):
    """Получить предложения marketplace с фильтрацией."""
    users_data = await marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    # Парсинг предложений
    offers = _parse_offers(
        users_data=users_data,
        search_term=search_term,
        server_id=server_id if server_id is not None and server_id >= 0 else None,
        sort_order=sort_order,
    )

    # Подсчёт уникальных серверов
    unique_servers = len(set(o.serverId for o in offers)) if offers else 0

    return OffersResponse(offers=offers, total=len(offers), servers=unique_servers)


@router.get("/search")
async def search_items(
    marketplace_service: MarketplaceService = Depends(get_marketplace_service),
    search_term: str = Query(default="", max_length=100, description="Поисковый запрос"),
    server_id: Optional[int] = Query(default=None, ge=-1, le=32, description="ID сервера (-1 = все серверы)"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc|none)$", description="Сортировка по цене"),
    limit: int = Query(default=50, ge=10, le=200, description="Лимит результатов"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
):
    """
    Поиск предметов с раздельными результатами (скупка/продажа) и пагинацией.

    - **buy_offers**: Предметы, которые игроки покупают (скупка)
    - **sell_offers**: Предметы, которые игроки продают (продажа)
    - **sort_order**: asc (по возрастанию), desc (по убыванию), none (без сортировки)
    """
    users_data = await marketplace_service.fetch_data()

    if not users_data:
        raise HTTPException(status_code=503, detail="Marketplace service unavailable")

    # Если server_id = -1, то ищем по всем серверам
    effective_server_id = None if server_id == -1 else server_id

    result = _parse_offers_split(
        users_data=users_data,
        search_term=search_term,
        server_id=effective_server_id,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    return {
        **result,
        "server_id": server_id,
        "search_term": search_term,
        "sort_order": sort_order,
    }


@router.get("/lavkas")
async def get_lavkas(
    server_id: int = Query(..., ge=0, le=32, description="ID сервера"),
    lavka_service: LavkaService = Depends(get_lavka_service),
):
    """Получить список лавок на сервере."""
    try:
        lavkas = await lavka_service.get_lavkas_for_server(server_id)
        return {
            "lavkas": lavkas,
            "total": len(lavkas),
            "serverName": get_server_name(server_id),
        }
    except Exception as e:
        logger.error(f"Error getting lavkas: {e}")
        raise HTTPException(status_code=500, detail="Error fetching lavkas")


@router.get("/lavkas/{lavka_uid}")
async def get_lavka_detail(
    lavka_uid: str,
    server_id: Optional[int] = Query(default=None, ge=0, le=32, description="ID сервера для точного поиска"),
    lavka_service: LavkaService = Depends(get_lavka_service),
):
    """Получить детальную информацию о лавке."""
    try:
        # Передаём server_id в сервис для точного поиска
        lavka = await lavka_service.get_lavka_detail(lavka_uid, server_id)

        if lavka is None:
            raise HTTPException(status_code=404, detail="Лавка не найдена")

        return lavka.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lavka detail: {e}")
        raise HTTPException(status_code=500, detail="Error fetching lavka details")
