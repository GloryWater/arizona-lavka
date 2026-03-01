"""
Сервис для анализа исторических данных marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import json
import logging
import math
import os
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import Settings

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Возвращает текущее UTC время (timezone-aware)."""
    return datetime.now(timezone.utc)

# Путь к папке с историческими данными
# Приоритеты (по порядку):
# 1. Переменная окружения HISTORICAL_DATA_PATH
# 2. /data (Docker mount)
# 3. ../../data относительно этого файла (локальная разработка)
_env_data_path = os.environ.get("HISTORICAL_DATA_PATH")
if _env_data_path:
    HISTORICAL_DATA_PATH = Path(_env_data_path)
elif Path("/data").exists():
    HISTORICAL_DATA_PATH = Path("/data")
else:
    HISTORICAL_DATA_PATH = Path(__file__).parent.parent.parent / "data"

# Маппинг ID серверов на имена файлов
SERVER_FILE_MAPPING = {
    0: "vc", 1: "phoenix", 2: "tucson", 3: "scottdale", 4: "chandler",
    5: "brainburg", 6: "saintrose", 7: "mesa", 8: "red-rock", 9: "yuma",
    10: "surprise", 11: "prescott", 12: "glendale", 13: "kingman", 14: "winslow",
    15: "payson", 16: "gilbert", 17: "show-low", 18: "casa-grande", 19: "page",
    20: "sun-city", 21: "queen-creek", 22: "sedona", 23: "holiday", 24: "wednesday",
    25: "yava", 26: "faraway", 27: "bumble-bee", 28: "christmas", 29: "mirage",
    30: "love", 31: "drake", 32: "space",
}


class HistoricalDataService:
    """
    Сервис для анализа исторических данных marketplace.
    
    Использует датированную статистику покупок/продаж для:
    - Анализа трендов цен
    - Расчёта ликвидности предметов
    - Прогнозирования справедливой цены
    """
    
    def __init__(self, settings: Settings):
        """
        Инициализация сервиса.
        
        Args:
            settings: Настройки приложения
        """
        self.settings = settings
        self._analyzers: Dict[int, HistoricalDataAnalyzer] = {}
    
    def get_analyzer(self, server_id: int = 0) -> "HistoricalDataAnalyzer":
        """
        Получает или создаёт анализатор для указанного сервера.
        
        Args:
            server_id: ID сервера (0-32)
        
        Returns:
            HistoricalDataAnalyzer: Анализатор для сервера
        """
        if server_id not in self._analyzers:
            self._analyzers[server_id] = HistoricalDataAnalyzer(server_id)
        return self._analyzers[server_id]


class HistoricalDataAnalyzer:
    """Анализатор исторических данных для конкретного сервера."""

    def __init__(self, server_id: int = 0):
        """
        Инициализация анализатора.

        Args:
            server_id: ID сервера (по умолчанию 0 = Vice City)
        """
        self.server_id = server_id
        self.server_name = SERVER_FILE_MAPPING.get(server_id, "vc")
        self.buy_data: Dict[str, List[Dict]] = {}
        self.sell_data: Dict[str, List[Dict]] = {}
        self._data_loaded = False
        
        # Кэш для расчёта ликвидности (TTL: 5 минут)
        self._liquidity_cache: Dict[str, Tuple[float, datetime]] = {}
        self._liquidity_cache_ttl = 300  # секунд
    
    def load_historical_data(self) -> bool:
        """
        Загружает исторические данные из JSON файлов для текущего сервера.

        Returns:
            True если данные успешно загружены
        """
        if self._data_loaded:
            return True

        try:
            # Загрузка данных о покупках (файлы в кодировке cp1251)
            buy_file = HISTORICAL_DATA_PATH / f"info_users_buy_{self.server_name}.json"
            if buy_file.exists():
                # Пробуем несколько кодировок для максимальной совместимости
                self.buy_data = self._load_json_with_fallback(buy_file)
                if self.buy_data:
                    logger.info(f"Загружено покупок для сервера {self.server_id}: {len(self.buy_data)} предметов")
                else:
                    logger.warning(f"Не удалось загрузить файл покупок: {buy_file}")
            else:
                logger.warning(f"Файл покупок не найден: {buy_file} - исторические данные для покупок будут недоступны")

            # Загрузка данных о продажах
            sell_file = HISTORICAL_DATA_PATH / f"info_users_sell_{self.server_name}.json"
            if sell_file.exists():
                # Пробуем несколько кодировок для максимальной совместимости
                self.sell_data = self._load_json_with_fallback(sell_file)
                if self.sell_data:
                    logger.info(f"Загружено продаж для сервера {self.server_id}: {len(self.sell_data)} предметов")
                else:
                    logger.warning(f"Не удалось загрузить файл продаж: {sell_file}")
            else:
                logger.warning(f"Файл продаж не найден: {sell_file} - исторические данные для продаж будут недоступны")

            # Логирование если оба файла отсутствуют
            if not buy_file.exists() and not sell_file.exists():
                logger.error(
                    f"Критическая ошибка: исторические данные отсутствуют для сервера {self.server_id} "
                    f"(ожидаемые файлы: {buy_file.name}, {sell_file.name}). "
                    f"Проверьте путь к данным: {HISTORICAL_DATA_PATH}"
                )

            self._data_loaded = True
            
            # Инвалидация кэша ликвидности при загрузке новых данных
            self._liquidity_cache.clear()
            
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON исторических данных для сервера {self.server_id}: {e}")
            return False
        except FileNotFoundError as e:
            logger.error(f"Файл исторических данных не найден для сервера {self.server_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке исторических данных для сервера {self.server_id}: {e}")
            return False
    
    def _load_json_with_fallback(self, file_path: Path) -> Optional[Dict]:
        """
        Загружает JSON файл с fallback на несколько кодировок.
        
        Приоритет кодировок:
        1. utf-8 (современный стандарт)
        2. cp1251 (Windows Cyrillic, используется в старых файлах)
        3. latin-1 (суперсет, всегда декодирует без ошибок)
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Распарсенные данные или None если загрузка не удалась
        """
        encodings = ["utf-8", "cp1251", "latin-1"]
        
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    data = json.load(f)
                    if encoding != "utf-8":
                        logger.warning(f"Файл {file_path} загружен с fallback кодировкой {encoding}")
                    return data
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в файле {file_path}: {e}")
                return None
        
        logger.error(f"Не удалось прочитать файл {file_path} ни в одной из кодировок: {encodings}")
        return None
    
    def _parse_history_entry(self, entry: List[Any]) -> Dict:
        """
        Парсит запись истории в формат dict.

        Структура JSON: [дата, количество, общая_сумма, количество?, цена, цена?]
        """
        return {
            "date": entry[0] if len(entry) > 0 else "",
            "quantity": entry[1] if len(entry) > 1 else 0,
            "total_amount": entry[2] if len(entry) > 2 else 0,
            "price": entry[4] if len(entry) > 4 else 0,
        }
    
    def get_item_history(self, item_name: str, mode: str = "buy") -> List[Dict]:
        """
        Получает историю торгов для предмета.
        
        Args:
            item_name: Название предмета
            mode: "buy" или "sell"
        
        Returns:
            Список записей истории, отсортированных по дате
        """
        if not self._data_loaded:
            self.load_historical_data()
        
        data = self.buy_data if mode == "buy" else self.sell_data
        
        # Поиск предмета (ключи в кодировке cp1251)
        if item_name in data:
            history_list = data[item_name].get("list", [])
            return [self._parse_history_entry(entry) for entry in history_list]
        
        # Пробуем сконвертировать имя из UTF-8 в cp1251
        try:
            item_name_cp1251 = item_name.encode('utf-8').decode('cp1251')
            if item_name_cp1251 in data:
                history_list = data[item_name_cp1251].get("list", [])
                return [self._parse_history_entry(entry) for entry in history_list]
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        
        # Ищем по частичному совпадению
        for key, value in data.items():
            try:
                key_utf8 = key.encode('cp1251').decode('utf-8')
                if item_name.lower() in key_utf8.lower():
                    history_list = value.get("list", [])
                    return [self._parse_history_entry(entry) for entry in history_list]
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        
        return []
    
    def calculate_price_trend(
        self,
        item_name: str,
        mode: str = "buy",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Рассчитывает тренд цены за указанное количество дней.
        
        Returns:
            Словарь с метриками тренда
        """
        history = self.get_item_history(item_name, mode)
        
        if not history:
            return {
                "trend": "stable", "current_price": 0, "old_price": 0,
                "avg_price": 0, "min_price": 0, "max_price": 0,
                "price_change": 0, "price_change_percent": 0,
                "volume": 0, "data_points": 0,
            }
        
        # Сортировка по дате
        history.sort(key=lambda x: x["date"], reverse=True)

        # Фильтрация по дням - используем UTC для консистентности
        cutoff_date = (_utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_history = [h for h in history if h["date"] >= cutoff_date]
        
        if not recent_history:
            recent_history = history[:days] if len(history) >= days else history
        
        if not recent_history:
            return {
                "trend": "stable", "current_price": 0, "old_price": 0,
                "avg_price": 0, "min_price": 0, "max_price": 0,
                "price_change": 0, "price_change_percent": 0,
                "volume": 0, "data_points": 0,
            }
        
        prices = [h["price"] for h in recent_history if h["price"] > 0]
        
        if not prices:
            return {
                "trend": "stable", "current_price": 0, "old_price": 0,
                "avg_price": 0, "min_price": 0, "max_price": 0,
                "price_change": 0, "price_change_percent": 0,
                "volume": 0, "data_points": 0,
            }
        
        current_price = prices[0]
        old_price = prices[-1] if len(prices) > 1 else prices[0]
        price_change = current_price - old_price
        price_change_percent = (price_change / old_price * 100) if old_price > 0 else 0
        
        # Определение тренда
        if price_change_percent > 5:
            trend = "up"
        elif price_change_percent < -5:
            trend = "down"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "current_price": current_price,
            "old_price": old_price,
            "avg_price": statistics.mean(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "volume": sum(h["quantity"] for h in recent_history),
            "data_points": len(prices),
        }
    
    def calculate_liquidity_score(
        self,
        item_name: str,
        mode: str = "buy",
        days: int = 30
    ) -> float:
        """
        Рассчитывает ликвидность предмета (0-100) по улучшенной формуле.

        Учитывает 5 факторов:
        1. Частота сделок (35%) - логарифмическая шкала
        2. Объём торгов (25%) - логарифмическая шкала
        3. Свежесть данных (20%) - time decay с периодом полураспада 14 дней
        4. Консистентность (10%) - равномерность распределения по дням
        5. Спред (10%) - разница между buy/sell ценами

        Args:
            item_name: Название предмета
            mode: "buy" или "sell"
            days: Период анализа в днях (по умолчанию 30)

        Returns:
            Score ликвидности от 0 до 100

        Note:
            Результаты кэшируются на 5 минут для производительности.
        """
        # Проверка кэша
        cache_key = f"{item_name}:{mode}:{days}"
        now = _utcnow()

        if cache_key in self._liquidity_cache:
            cached_value, cached_time = self._liquidity_cache[cache_key]
            if (now - cached_time).total_seconds() < self._liquidity_cache_ttl:
                return cached_value

        history = self.get_item_history(item_name, mode)

        if not history:
            self._liquidity_cache[cache_key] = (0.0, now)
            return 0.0

        # Фильтрация по дням - используем UTC для консистентности
        cutoff_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_history = [h for h in history if h["date"] >= cutoff_date]

        if not recent_history:
            self._liquidity_cache[cache_key] = (0.0, now)
            return 0.0

        # 1. Частота сделок (35%)
        # Логарифмическая шкала: 1 сделка = 17.5%, 10 = 52.5%, 100 = 100%
        trade_count = len(recent_history)
        frequency_score = min(math.log10(trade_count + 1) / 2, 1) * 100

        # 2. Объём торгов (25%)
        # Логарифмическая шкала: 1 ед = 11%, 10 = 33%, 100 = 56%, 1000 = 83%
        total_volume = sum(h["quantity"] for h in recent_history)
        volume_score = min(math.log10(total_volume + 1) / 3, 1) * 100

        # 3. Свежесть данных (20%)
        # Time decay: чем свежее сделка, тем больше вес
        weighted_sum = 0.0
        total_weight = 0.0

        for h in recent_history:
            try:
                trade_date = datetime.strptime(h["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_ago = (now - trade_date).days
                # Экспоненциальное затухание с периодом полураспада 14 дней
                weight = math.exp(-days_ago * math.log(2) / 14)
                weighted_sum += h["quantity"] * weight
                total_weight += weight
            except (ValueError, TypeError):
                continue

        # Нормализация freshness_score
        if total_weight > 0 and total_volume > 0:
            freshness_score = min((weighted_sum / total_volume) * 100, 100)
        else:
            freshness_score = 0.0

        # 4. Консистентность (10%)
        # Насколько равномерно распределены торги по дням
        unique_dates = set(h["date"] for h in recent_history)
        days_with_trades = len(unique_dates)
        max_possible_days = min(days, trade_count)
        consistency_score = (days_with_trades / max_possible_days) * 100 if max_possible_days > 0 else 0.0

        # 5. Спред (10%) - рассчитываем на основе разницы buy/sell
        spread_data = self.calculate_spread(item_name, days=min(days, 7))
        if spread_data["has_both_sides"]:
            spread_percent = spread_data["spread_percent"]
            # Конвертируем спред в score: 0% = 100%, 10% = 70%, 30% = 30%, >50% = 0%
            spread_score = max(100 - (spread_percent * 2), 0)
        else:
            # Нет данных по спреду — нейтральный score
            spread_score = 50.0

        # Итоговый score
        liquidity_score = (
            frequency_score * 0.35 +
            volume_score * 0.25 +
            freshness_score * 0.20 +
            consistency_score * 0.10 +
            spread_score * 0.10
        )

        result = min(liquidity_score, 100)

        # Сохранение в кэш
        self._liquidity_cache[cache_key] = (result, now)

        return result

    def calculate_spread(
        self,
        item_name: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Рассчитывает спред (разницу) между ценами покупки и продажи.

        Спред показывает разницу между средней ценой покупки (buy) и продажи (sell).
        Низкий спред (<10%) = высокая ликвидность (рынок эффективен)
        Высокий спред (>30%) = низкая ликвидность (рынок неэффективен)

        Args:
            item_name: Название предмета
            days: Период анализа в днях

        Returns:
            Dict с метриками спреда:
            - spread_absolute: абсолютная разница цен
            - spread_percent: процентный спред
            - buy_avg_price: средняя цена покупки
            - sell_avg_price: средняя цена продажи
            - liquidity_rating: оценка ликвидности по спреду
        """
        # Получаем истории для buy и sell
        buy_history = self.get_item_history(item_name, "buy")
        sell_history = self.get_item_history(item_name, "sell")

        # Фильтрация по дням
        now = _utcnow()
        cutoff_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")

        buy_recent = [h for h in buy_history if h["date"] >= cutoff_date and h["price"] > 0]
        sell_recent = [h for h in sell_history if h["date"] >= cutoff_date and h["price"] > 0]

        # Если нет данных для одной из сторон
        if not buy_recent or not sell_recent:
            return {
                "spread_absolute": 0,
                "spread_percent": 0,
                "buy_avg_price": 0,
                "sell_avg_price": 0,
                "liquidity_rating": "unknown",
                "has_both_sides": bool(buy_recent and sell_recent),
            }

        # Расчёт средних цен
        buy_avg_price = statistics.mean([h["price"] for h in buy_recent])
        sell_avg_price = statistics.mean([h["price"] for h in sell_recent])

        # Спред
        spread_absolute = sell_avg_price - buy_avg_price
        spread_percent = (spread_absolute / buy_avg_price * 100) if buy_avg_price > 0 else 0

        # Оценка ликвидности по спреду
        if spread_percent < 5:
            liquidity_rating = "very_high"  # Очень высокая (рынок эффективен)
        elif spread_percent < 10:
            liquidity_rating = "high"
        elif spread_percent < 20:
            liquidity_rating = "medium"
        elif spread_percent < 30:
            liquidity_rating = "low"
        else:
            liquidity_rating = "very_low"  # Очень низкая (возможны манипуляции)

        return {
            "spread_absolute": spread_absolute,
            "spread_percent": spread_percent,
            "buy_avg_price": buy_avg_price,
            "sell_avg_price": sell_avg_price,
            "liquidity_rating": liquidity_rating,
            "has_both_sides": True,
        }

    def get_24h_activity(
        self,
        item_name: str,
        mode: str = "buy"
    ) -> Dict[str, Any]:
        """
        Получает метрики активности предмета за последние 24 часа.

        Args:
            item_name: Название предмета
            mode: "buy" или "sell"

        Returns:
            Dict с метриками:
            - trade_count: количество сделок
            - volume: общий объём торгов
            - last_trade_date: дата последней сделки
            - avg_price: средняя цена за 24 часа
        """
        history = self.get_item_history(item_name, mode)

        if not history:
            return {
                "trade_count": 0,
                "volume": 0,
                "last_trade_date": None,
                "avg_price": 0,
            }

        # Фильтрация по последним 24 часам
        now = _utcnow()
        cutoff_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        recent_history = [h for h in history if h["date"] >= cutoff_date]

        if not recent_history:
            return {
                "trade_count": 0,
                "volume": 0,
                "last_trade_date": None,
                "avg_price": 0,
            }

        # Сортировка по дате (свежие первые)
        recent_history.sort(key=lambda x: x["date"], reverse=True)

        # Подсчёт метрик
        trade_count = len(recent_history)
        total_volume = sum(h["quantity"] for h in recent_history)
        last_trade_date = recent_history[0]["date"] if recent_history else None
        
        prices = [h["price"] for h in recent_history if h["price"] > 0]
        avg_price = statistics.mean(prices) if prices else 0

        return {
            "trade_count": trade_count,
            "volume": total_volume,
            "last_trade_date": last_trade_date,
            "avg_price": avg_price,
        }
