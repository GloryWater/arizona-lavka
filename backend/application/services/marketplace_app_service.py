"""
Marketplace application service.

Содержит бизнес-логику для работы с marketplace данными.
"""

import logging
from typing import List, Optional, Dict, Any

from application.interfaces.external import IMarketplaceAPI
from application.interfaces.repositories import IUserRepository
from application.dtos import OfferDTO, LavkaSummaryDTO, LavkaDetailDTO, LavkaItemDTO
from core.enums.offer_type import OfferType

logger = logging.getLogger(__name__)


class MarketplaceAppService:
    """
    Application сервис для marketplace.

    Содержит бизнес-логику:
    - Получение данных marketplace
    - Парсинг и фильтрация предложений
    - Поиск предметов
    - Получение информации о лавках
    """

    def __init__(
        self,
        marketplace_api: IMarketplaceAPI,
    ):
        self.marketplace_api = marketplace_api

    async def fetch_data(self) -> List[dict]:
        """
        Получает данные marketplace.

        Returns:
            Список данных пользователей из API
        """
        return await self.marketplace_api.fetch_marketplace_data()

    def parse_offers(
        self,
        users_data: List[dict],
        search_term: str = "",
        server_id: Optional[int] = None,
        sort_order: str = "none",
    ) -> List[OfferDTO]:
        """
        Парсит данные пользователей в список предложений.

        Оптимизация: один проход по данным, предварительная фильтрация серверов.
        """
        from services.lavka_service import LavkaService

        offers = []
        search_lower = search_term.lower() if search_term else None

        for user_data in users_data:
            user_server = user_data.get("serverId")
            if server_id is not None and user_server != server_id:
                continue

            # Корректная обработка LavkaUid
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

                        offers.append(OfferDTO(
                            type=OfferType.SELL.value,
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_sell[i]),
                            count=int(counts_sell[i]),
                            username=username,
                            lavka_uid=lavka_uid,
                            server_id=user_server,
                            user_status=user_status,
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

                        offers.append(OfferDTO(
                            type=OfferType.BUY.value,
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_buy[i]),
                            count=int(counts_buy[i]),
                            username=username,
                            lavka_uid=lavka_uid,
                            server_id=user_server,
                            user_status=user_status,
                        ))
                    except (ValueError, TypeError, IndexError):
                        continue

        # Сортировка
        if sort_order == "asc":
            offers.sort(key=lambda x: x.price)
        elif sort_order == "desc":
            offers.sort(key=lambda x: x.price, reverse=True)

        return offers

    def parse_offers_split(
        self,
        users_data: List[dict],
        search_term: str = "",
        server_id: Optional[int] = None,
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Парсит данные пользователей в разделённые предложения (скупка/продажа).
        """
        from services.lavka_service import LavkaService

        buy_offers: List[OfferDTO] = []
        sell_offers: List[OfferDTO] = []
        search_lower = search_term.lower() if search_term else None

        # Предварительная фильтрация по серверу
        filtered_users = (
            users_data if server_id is None
            else [u for u in users_data if u.get("serverId") == server_id]
        )

        for user_data in filtered_users:
            lavka_uid_raw = user_data.get("LavkaUid")
            if lavka_uid_raw is None or lavka_uid_raw == 0:
                continue
            lavka_uid = str(lavka_uid_raw)

            username = user_data.get("username") or "Unknown"
            user_status = bool(user_data.get("userStatus", 0))
            user_server = user_data.get("serverId")

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

                        sell_offers.append(OfferDTO(
                            type=OfferType.SELL.value,
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_sell[i]),
                            count=int(counts_sell[i]),
                            username=username,
                            lavka_uid=lavka_uid,
                            server_id=user_server,
                            user_status=user_status,
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

                        buy_offers.append(OfferDTO(
                            type=OfferType.BUY.value,
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_buy[i]),
                            count=int(counts_buy[i]),
                            username=username,
                            lavka_uid=lavka_uid,
                            server_id=user_server,
                            user_status=user_status,
                        ))
                    except (ValueError, TypeError, IndexError):
                        continue

        # Сортировка
        if sort_order == "asc":
            buy_offers.sort(key=lambda x: x.price)
            sell_offers.sort(key=lambda x: x.price)
        elif sort_order == "desc":
            buy_offers.sort(key=lambda x: x.price, reverse=True)
            sell_offers.sort(key=lambda x: x.price, reverse=True)

        # Сохраняем общие количества до пагинации
        total_buy = len(buy_offers)
        total_sell = len(sell_offers)

        # Применяем пагинацию
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

    async def get_lavkas_for_server(self, server_id: int) -> List[LavkaSummaryDTO]:
        """
        Получает список лавок на сервере.

        Args:
            server_id: ID сервера

        Returns:
            Список LavkaSummaryDTO
        """
        from services.lavka_service import LavkaService

        users_data = await self.fetch_data()
        lavka_service = LavkaService(self, None)  # Передаём self как marketplace_service

        # Фильтрация по серверу
        server_users = [u for u in users_data if u.get("serverId") == server_id]

        lavkas = []
        for user_data in server_users:
            lavka_uid_raw = user_data.get("LavkaUid")
            if lavka_uid_raw is None or lavka_uid_raw == 0:
                continue

            lavka_uid = str(lavka_uid_raw)
            username = user_data.get("username") or "Unknown"

            items_sell = user_data.get("items_sell") or []
            items_buy = user_data.get("items_buy") or []

            lavkas.append(LavkaSummaryDTO(
                lavka_uid=lavka_uid,
                username=username,
                server_id=server_id,
                sell_count=len(items_sell),
                buy_count=len(items_buy),
                total_items=len(items_sell) + len(items_buy),
            ))

        return lavkas

    async def get_lavka_detail(
        self,
        lavka_uid: str,
        server_id: Optional[int] = None,
    ) -> Optional[LavkaDetailDTO]:
        """
        Получает детальную информацию о лавке.

        Args:
            lavka_uid: UID лавки
            server_id: ID сервера для точного поиска

        Returns:
            LavkaDetailDTO или None
        """
        from services.lavka_service import LavkaService

        users_data = await self.fetch_data()
        lavka_service = LavkaService(self, None)

        # Поиск лавки
        for user_data in users_data:
            if server_id is not None and user_data.get("serverId") != server_id:
                continue

            user_lavka_uid_raw = user_data.get("LavkaUid")
            if user_lavka_uid_raw is None or user_lavka_uid_raw == 0:
                continue

            user_lavka_uid = str(user_lavka_uid_raw)
            if user_lavka_uid != lavka_uid:
                continue

            username = user_data.get("username") or "Unknown"
            user_status = bool(user_data.get("userStatus", 0))
            user_server = user_data.get("serverId")

            # Парсинг предметов на продажу
            sell_items = []
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
                        sell_items.append(LavkaItemDTO(
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_sell[i]),
                            count=int(counts_sell[i]),
                            type=OfferType.SELL.value,
                        ))
                    except (ValueError, TypeError, IndexError):
                        continue

            # Парсинг предметов на покупку
            buy_items = []
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
                        buy_items.append(LavkaItemDTO(
                            item_id=parsed_id,
                            item_name=item_name,
                            price=float(prices_buy[i]),
                            count=int(counts_buy[i]),
                            type=OfferType.BUY.value,
                        ))
                    except (ValueError, TypeError, IndexError):
                        continue

            return LavkaDetailDTO(
                lavka_uid=lavka_uid,
                username=username,
                server_id=user_server,
                user_status=user_status,
                sell_items=sell_items,
                buy_items=buy_items,
                total_sell=len(sell_items),
                total_buy=len(buy_items),
            )

        return None
