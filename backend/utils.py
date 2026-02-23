"""Утилиты для обработки данных marketplace."""

import logging
from typing import Any, List

from config import get_server_name
from models import Offer, OfferType
from services.lavka_service import get_item_name, parse_item_id

logger = logging.getLogger(__name__)


def parse_parallel_offers(
    items: List[Any],
    prices: List[Any],
    counts: List[Any],
    offer_type: OfferType,
    username: str,
    lavka_uid: str,
    server_id: int,
    user_status: bool,
) -> List[Offer]:
    """
    Парсит параллельные массивы предметов, цен и количеств в список Offer.

    Args:
        items: Список ID предметов (могут быть в формате "6132(+12)")
        prices: Список цен
        counts: Список количеств
        offer_type: Тип предложения (SELL/BUY)
        username: Имя пользователя
        lavka_uid: UID лавки
        server_id: ID сервера
        user_status: Статус пользователя

    Returns:
        Список нормализованных предложений Offer
    """
    offers = []
    min_len = min(len(items), len(prices), len(counts))

    for i in range(min_len):
        item_id = parse_item_id(items[i])
        if item_id is None:
            continue

        try:
            offers.append(
                Offer(
                    type=offer_type,
                    itemId=item_id,
                    itemName=get_item_name(item_id),
                    price=float(prices[i]),
                    count=int(counts[i]),
                    username=username,
                    lavkaUid=lavka_uid,
                    serverId=server_id,
                    userStatus=user_status,
                )
            )
        except (ValueError, TypeError):
            logger.warning(
                f"Пропущен предмет: type={offer_type}, item_id={item_id}, "
                f"price={prices[i]}, count={counts[i]}"
            )

    return offers
