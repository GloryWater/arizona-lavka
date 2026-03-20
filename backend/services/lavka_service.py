"""
Сервис для работы с лавками и предметами.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from config import Settings
from models import LavkaDetail, LavkaItem, LavkaSummary, OfferType
from services.marketplace_service import MarketplaceService, _sanitize_item_name

logger = logging.getLogger(__name__)

# Путь к файлу mapping предметов
# items.json находится в папке backend/ (рядом с main.py)
# При запуске в Docker: /app/items.json
ITEMS_FILE = Path(__file__).parent.parent / "items.json"


class LavkaService:
    """
    Сервис для работы с лавками и предметами.

    Особенности:
    - Ленивая загрузка mapping предметов
    - Кэширование mapping в памяти
    - Статические методы для производительности
    """

    # Класс-уровень кэш для mapping предметов
    _items_mapping: Dict[str, str] = {}
    _items_loaded: bool = False

    def __init__(self, marketplace_service: MarketplaceService, settings: Settings):
        """
        Инициализация сервиса.

        Args:
            marketplace_service: Сервис marketplace для получения данных
            settings: Настройки приложения
        """
        self.marketplace_service = marketplace_service
        self.settings = settings

    @classmethod
    def load_items_mapping(cls) -> Dict[str, str]:
        """
        Загружает статический JSON с mapping предметов в память.

        Returns:
            Словарь mapping предметов ID -> название

        Raises:
            RuntimeError: Если файл items.json не найден после нескольких попыток
        """
        if cls._items_loaded:
            logger.debug(f"Mapping уже загружен: {len(cls._items_mapping)} предметов")
            return cls._items_mapping

        logger.info(f"Загрузка mapping предметов из {ITEMS_FILE}")
        logger.info(
            f"ITEMS_FILE exists: {ITEMS_FILE.exists()}, absolute: {ITEMS_FILE.absolute()}"
        )

        # Проверка существования файла перед загрузкой
        if not ITEMS_FILE.exists():
            logger.error(
                f"Критическая ошибка: файл items.json не найден по пути {ITEMS_FILE}"
            )
            logger.error("Убедитесь, что файл items.json находится в папке backend/")
            # Возвращаем пустой mapping с флагом загрузки чтобы не пытаться снова
            cls._items_loaded = True
            return {}

        try:
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                cls._items_mapping = json.load(f)
            cls._items_loaded = True
            logger.info(f"Загружено {len(cls._items_mapping)} предметов в mapping")
            return cls._items_mapping
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            cls._items_mapping = {}
            cls._items_loaded = True  # Помечаем как загружено чтобы не пытаться снова
            return {}

    @classmethod
    def get_item_name(cls, item_id: int) -> str:
        """
        Получает название предмета по ID.

        Args:
            item_id: ID предмета

        Returns:
            Название предмета или fallback строку (санитизированные)
        """
        if not cls._items_loaded:
            cls.load_items_mapping()
        name = cls._items_mapping.get(str(item_id), f"Unknown Item (ID: {item_id})")
        # Санитизация для защиты от XSS
        return _sanitize_item_name(name)

    @staticmethod
    def parse_item_id(item_value) -> Optional[int]:
        """
        Парсит item_id из значения, которое может быть в формате:
        - 6132 (число или строка)
        - "6132(+12)" (строка с суффиксом)

        Args:
            item_value: Значение для парсинга

        Returns:
            int или None если не удалось распарсить
        """
        if item_value is None:
            return None

        if isinstance(item_value, int):
            return item_value

        if isinstance(item_value, str):
            # Пробуем распарсить как чистое число
            try:
                return int(item_value)
            except ValueError:
                pass

            # Пробуем извлечь число из формата "6132(+12)"
            if "(" in item_value:
                clean_id = item_value.split("(")[0].strip()
                try:
                    return int(clean_id)
                except ValueError:
                    return None

            # Пробуем распарсить как float и округлить
            try:
                return int(float(item_value))
            except ValueError:
                return None

        return None

    async def get_lavkas_for_server(self, server_id: int) -> List[LavkaSummary]:
        """
        Получает список лавок для указанного сервера.

        Args:
            server_id: ID сервера (0-32)

        Returns:
            Список лавок, отсортированный по количеству предметов (убывание)
        """
        users_data = await self.marketplace_service.fetch_data()
        logger.info(f"Получено {len(users_data)} пользователей для списка лавок")

        lavkas_dict: Dict[str, dict] = {}

        for user_data in users_data:
            user_server = user_data.get("serverId")
            if user_server != server_id:
                continue

            # Корректная обработка LavkaUid
            lavka_uid_raw = user_data.get("LavkaUid")
            if lavka_uid_raw is None or lavka_uid_raw == 0:
                continue

            lavka_uid = str(lavka_uid_raw)
            username = user_data.get("username") or "Unknown"

            items_sell = user_data.get("items_sell") or []
            count_sell = user_data.get("count_sell") or []
            items_buy = user_data.get("items_buy") or []
            count_buy = user_data.get("count_buy") or []

            sell_count = (
                min(len(items_sell), len(count_sell))
                if items_sell and count_sell
                else 0
            )
            buy_count = (
                min(len(items_buy), len(count_buy)) if items_buy and count_buy else 0
            )

            if lavka_uid not in lavkas_dict:
                lavkas_dict[lavka_uid] = {
                    "lavkaUid": lavka_uid,
                    "username": username,
                    "serverId": server_id,
                    "sellCount": 0,
                    "buyCount": 0,
                }

            lavkas_dict[lavka_uid]["sellCount"] += sell_count
            lavkas_dict[lavka_uid]["buyCount"] += buy_count

        lavkas_list = [
            LavkaSummary(
                lavkaUid=lavka["lavkaUid"],
                username=lavka["username"],
                serverId=lavka["serverId"],
                sellCount=lavka["sellCount"],
                buyCount=lavka["buyCount"],
                totalItems=lavka["sellCount"] + lavka["buyCount"],
            )
            for lavka in lavkas_dict.values()
            if (lavka["sellCount"] + lavka["buyCount"]) > 0
        ]

        # Сортировка по количеству предметов (убывание)
        lavkas_list.sort(key=lambda x: x.totalItems, reverse=True)

        return lavkas_list

    async def get_lavka_detail(
        self, lavka_uid: str, server_id: Optional[int] = None
    ) -> Optional[LavkaDetail]:
        """
        Получает детальную информацию о лавке.

        Args:
            lavka_uid: Уникальный идентификатор лавки
            server_id: ID сервера для точного поиска (опционально)

        Returns:
            Детальная информация о лавке или None если не найдена
        """
        users_data = await self.marketplace_service.fetch_data()
        logger.info(
            f"Поиск лавки по UID: {lavka_uid}"
            + (f" на сервере: {server_id}" if server_id else "")
        )

        # Собираем все найденные лавки с таким UID
        found_users = []
        for user_data in users_data:
            # Корректная обработка LavkaUid
            user_lavka_uid_raw = user_data.get("LavkaUid")
            if user_lavka_uid_raw is None or user_lavka_uid_raw == 0:
                continue

            user_lavka_uid = str(user_lavka_uid_raw)

            if user_lavka_uid == lavka_uid:
                found_users.append(
                    {
                        "username": user_data.get("username"),
                        "serverId": user_data.get("serverId"),
                        "lavkaUid": user_lavka_uid,
                    }
                )

        # Логирование если найдено несколько лавок с одинаковым UID
        if len(found_users) > 1:
            logger.warning(
                f"Найдено {len(found_users)} лавок с одинаковым UID {lavka_uid}:"
            )
            for u in found_users:
                logger.warning(
                    f"  - Username: {u['username']}, Server: {u['serverId']}"
                )
            if server_id is not None:
                logger.info(f"Будет использована лавка на сервере {server_id}")
        elif len(found_users) == 0:
            logger.warning(f"Лавка с UID {lavka_uid} не найдена")
            return None

        # Ищем лавку на указанном сервере (если server_id передан)
        target_user_data = None
        for user_data in users_data:
            user_lavka_uid_raw = user_data.get("LavkaUid")
            if user_lavka_uid_raw is None or user_lavka_uid_raw == 0:
                continue

            user_lavka_uid = str(user_lavka_uid_raw)
            if user_lavka_uid != lavka_uid:
                continue

            user_server = user_data.get("serverId")

            # Если server_id указан - ищем точное совпадение
            if server_id is not None and user_server != server_id:
                continue

            # Нашли подходящую лавку
            target_user_data = user_data
            break

        # Если не нашли с server_id, берём первую найденную (fallback)
        if target_user_data is None and found_users:
            for user_data in users_data:
                user_lavka_uid_raw = user_data.get("LavkaUid")
                if user_lavka_uid_raw is None or user_lavka_uid_raw == 0:
                    continue
                user_lavka_uid = str(user_lavka_uid_raw)
                if user_lavka_uid == lavka_uid:
                    target_user_data = user_data
                    break

        if target_user_data is None:
            return None

        username = target_user_data.get("username") or "Unknown"
        server_id_result = target_user_data.get("serverId") or 0
        user_status = bool(target_user_data.get("userStatus", 0))

        sell_items: List[LavkaItem] = []
        buy_items: List[LavkaItem] = []

        # Извлекаем предметы на продажу
        items_sell = target_user_data.get("items_sell") or []
        prices_sell = target_user_data.get("price_sell") or []
        counts_sell = target_user_data.get("count_sell") or []

        if items_sell and prices_sell and counts_sell:
            min_len = min(len(items_sell), len(prices_sell), len(counts_sell))
            for i in range(min_len):
                parsed_id = self.parse_item_id(items_sell[i])
                if parsed_id is None:
                    continue
                try:
                    sell_items.append(
                        LavkaItem(
                            itemId=parsed_id,
                            itemName=self.get_item_name(parsed_id),
                            price=float(prices_sell[i]),
                            count=int(counts_sell[i]),
                            type=OfferType.SELL,
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Пропущен предмет продажи: {e}")

        # Извлекаем предметы на покупку
        items_buy = target_user_data.get("items_buy") or []
        prices_buy = target_user_data.get("price_buy") or []
        counts_buy = target_user_data.get("count_buy") or []

        if items_buy and prices_buy and counts_buy:
            min_len = min(len(items_buy), len(prices_buy), len(counts_buy))
            for i in range(min_len):
                parsed_id = self.parse_item_id(items_buy[i])
                if parsed_id is None:
                    continue
                try:
                    buy_items.append(
                        LavkaItem(
                            itemId=parsed_id,
                            itemName=self.get_item_name(parsed_id),
                            price=float(prices_buy[i]),
                            count=int(counts_buy[i]),
                            type=OfferType.BUY,
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Пропущен предмет покупки: {e}")

        return LavkaDetail(
            lavkaUid=lavka_uid,
            username=username,
            serverId=server_id_result,
            userStatus=user_status,
            sellItems=sell_items,
            buyItems=buy_items,
            totalSell=len(sell_items),
            totalBuy=len(buy_items),
        )
