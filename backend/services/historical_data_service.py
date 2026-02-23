"""
Сервис для анализа исторических данных marketplace.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Settings

logger = logging.getLogger(__name__)

# Путь к папке с историческими данными
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
                with open(buy_file, "r", encoding="cp1251") as f:
                    self.buy_data = json.load(f)
                logger.info(f"Загружено покупок для сервера {self.server_id}: {len(self.buy_data)} предметов")
            else:
                logger.warning(f"Файл покупок не найден: {buy_file}")
            
            # Загрузка данных о продажах
            sell_file = HISTORICAL_DATA_PATH / f"info_users_sell_{self.server_name}.json"
            if sell_file.exists():
                with open(sell_file, "r", encoding="cp1251") as f:
                    self.sell_data = json.load(f)
                logger.info(f"Загружено продаж для сервера {self.server_id}: {len(self.sell_data)} предметов")
            else:
                logger.warning(f"Файл продаж не найден: {sell_file}")
            
            self._data_loaded = True
            return True
            
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
            logger.error(f"Ошибка загрузки исторических данных для сервера {self.server_id}: {e}")
            return False
    
    def _parse_history_entry(self, entry: List[Any]) -> Dict:
        """
        Парсит запись истории в формат dict.
        
        Структура JSON: [дата, количество, общая_сумма, количество?, цена, цена?]
        """
        return {
            "date": entry[0],
            "quantity": entry[1],
            "total_amount": entry[2],
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
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
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
        Рассчитывает ликвидность предмета (0-100).
        
        Returns:
            Score ликвидности от 0 до 100
        """
        history = self.get_item_history(item_name, mode)
        
        if not history:
            return 0.0
        
        # Фильтрация по дням - используем UTC для консистентности
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_history = [h for h in history if h["date"] >= cutoff_date]
        
        if not recent_history:
            return 0.0
        
        # Количество дней с торгами
        unique_dates = set(h["date"] for h in recent_history)
        days_with_trades = len(unique_dates)
        
        # Общий объём
        total_volume = sum(h["quantity"] for h in recent_history)
        
        # Расчёт scores
        days_score = (days_with_trades / days) * 100
        volume_score = min((total_volume / 1000) * 100, 100)
        
        # Итоговый score
        liquidity_score = days_score * 0.4 + volume_score * 0.6
        
        return min(liquidity_score, 100)
