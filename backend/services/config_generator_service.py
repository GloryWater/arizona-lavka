"""
Сервис для генерации торговых конфигов.

Использует комбинированный подход:
1. Текущие цены с marketplace
2. Исторические данные (тренды, статистика)
3. IQR фильтрация выбросов

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from models import ConfigMode, ConfigItemResponse
from services.marketplace_service import MarketplaceService
from services.historical_data_service import HistoricalDataService
from services.lavka_service import LavkaService
from services.item_categories import categorize_item, get_items_by_category, get_all_categories

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Уровни уверенности в расчётах."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class PriceAnalysis:
    """Результат анализа цены для предмета."""
    item_id: int
    item_name: str
    current_prices: List[float] = field(default_factory=list)
    historical_avg: float = 0.0
    historical_trend: str = "stable"
    historical_trend_percent: float = 0.0
    liquidity_score: float = 0.0
    weighted_price: float = 0.0
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_score: float = 0.0
    final_price: int = 0
    data_points_current: int = 0
    data_points_historical: int = 0
    used_historical: bool = False


class ConfigGeneratorService:
    """
    Сервис генерации торговых конфигов.
    
    Веса для расчёта цены:
    - Текущие цены: 40%
    - Исторические данные: 35%
    - Тренды: 25%
    """
    
    def __init__(
        self,
        session: AsyncSession,
        marketplace_service: MarketplaceService,
        historical_data_service: HistoricalDataService,
        settings: Settings,
    ):
        """
        Инициализация сервиса.
        
        Args:
            session: Сессия базы данных
            marketplace_service: Сервис marketplace
            historical_data_service: Сервис исторических данных
            settings: Настройки приложения
        """
        self.session = session
        self.marketplace_service = marketplace_service
        self.historical_data_service = historical_data_service
        self.settings = settings
        
        # Веса для расчёта
        self.weight_current = 0.40
        self.weight_historical = 0.35
        self.weight_trend = 0.25

    def _group_items_from_users(
        self,
        users_data: List[dict],
        server_id: int,
        mode: ConfigMode,
    ) -> Dict[int, Tuple[str, List[float]]]:
        """
        Группирует предметы из данных пользователей по item_id.
        
        Это базовый метод для устранения дублирования кода между
        generate_config, generate_config_by_liquidity и generate_config_by_category.
        
        Args:
            users_data: Данные пользователей из API
            server_id: ID сервера для фильтрации
            mode: Режим (SELL/BUY)
            
        Returns:
            Dict {item_id: (item_name, [prices])}
        """
        items_data: Dict[int, Tuple[str, List[float]]] = {}
        mode_key = "items_sell" if mode == ConfigMode.SELL else "items_buy"
        price_key = "price_sell" if mode == ConfigMode.SELL else "price_buy"

        for user_data in users_data:
            if user_data.get("serverId") != server_id:
                continue

            items = user_data.get(mode_key) or []
            prices = user_data.get(price_key) or []

            min_len = min(len(items), len(prices))
            for i in range(min_len):
                parsed_id = LavkaService.parse_item_id(items[i])
                if parsed_id is None:
                    continue

                try:
                    price = float(prices[i])
                    if parsed_id not in items_data:
                        item_name = LavkaService.get_item_name(parsed_id)
                        items_data[parsed_id] = (item_name, [])
                    items_data[parsed_id][1].append(price)
                except (ValueError, TypeError):
                    continue

        return items_data

    def _create_config_item(self, item_name: str, price: int) -> ConfigItemResponse:
        """
        Создаёт ConfigItemResponse с стандартными параметрами.
        
        Args:
            item_name: Название предмета
            price: Цена предмета
            
        Returns:
            ConfigItemResponse с заполненными полями
        """
        return ConfigItemResponse(
            price=str(price),
            maximum=True,
            enabled=True,
            name=item_name,
            price_vc=9,
            count=1,
            slot_count=["0"],
            slot_id=["0"],
            position_tab=0,
            all_count=0,
            continue_="1",
            count_maximum=0,
        )

    def _calculate_stats(
        self,
        config_items: List[ConfigItemResponse],
        items_with_history: int = 0,
        confidence_scores: Optional[List[float]] = None,
        extra_stats: Optional[Dict] = None,
    ) -> Dict:
        """
        Рассчитывает статистику для конфига.
        
        Args:
            config_items: Список элементов конфига
            items_with_history: Количество предметов с историческими данными
            confidence_scores: Список очков уверенности
            extra_stats: Дополнительные поля для статистики
            
        Returns:
            Dict со статистикой
        """
        price_values = [int(item.price) for item in config_items]
        
        stats = {
            "total_items": len(config_items),
            "items_with_history": items_with_history,
            "avg_confidence": statistics.mean(confidence_scores) if confidence_scores else 0,
            "price_range": {
                "min": min(price_values) if price_values else 0,
                "max": max(price_values) if price_values else 0,
                "avg": statistics.mean(price_values) if price_values else 0,
            }
        }
        
        if extra_stats:
            stats.update(extra_stats)
        
        return stats
    
    @staticmethod
    def _calculate_iqr_median(prices: List[float]) -> float:
        """Рассчитывает медиану с IQR фильтрацией выбросов."""
        if not prices:
            return 0.0
        
        if len(prices) < 3:
            return statistics.median(prices)
        
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        q1_pos = (n - 1) * 0.25
        q3_pos = (n - 1) * 0.75
        
        q1_lower = int(q1_pos)
        q1_upper = min(q1_lower + 1, n - 1)
        q1 = sorted_prices[q1_lower] + (q1_pos - q1_lower) * (sorted_prices[q1_upper] - sorted_prices[q1_lower])
        
        q3_lower = int(q3_pos)
        q3_upper = min(q3_lower + 1, n - 1)
        q3 = sorted_prices[q3_lower] + (q3_pos - q3_lower) * (sorted_prices[q3_upper] - sorted_prices[q3_lower])
        
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        filtered = [p for p in sorted_prices if lower_bound <= p <= upper_bound]
        
        if len(filtered) < len(prices) * 0.5:
            return statistics.median(prices)
        
        return statistics.median(filtered) if filtered else statistics.median(prices)
    
    @staticmethod
    def _calculate_confidence(
        current_count: int,
        historical_days: int,
        liquidity: float,
        price_variance: float
    ) -> Tuple[ConfidenceLevel, float]:
        """Рассчитывает уровень уверенности (0-1)."""
        score = 0.0
        
        if current_count >= 10:
            score += 0.3
        elif current_count >= 5:
            score += 0.2
        elif current_count >= 2:
            score += 0.1
        
        if historical_days >= 14:
            score += 0.3
        elif historical_days >= 7:
            score += 0.2
        elif historical_days >= 3:
            score += 0.1
        
        score += (liquidity / 100) * 0.25
        score += (1 - min(price_variance, 1)) * 0.15
        
        thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.90,
            ConfidenceLevel.HIGH: 0.75,
            ConfidenceLevel.MEDIUM: 0.50,
            ConfidenceLevel.LOW: 0.25,
        }
        
        for level, threshold in thresholds.items():
            if score >= threshold:
                return level, score
        
        return ConfidenceLevel.VERY_LOW, score
    
    @staticmethod
    def _round_price(price: float, confidence: ConfidenceLevel) -> int:
        """Округляет цену в зависимости от уверенности."""
        if confidence in (ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH):
            return int(round(price))
        elif confidence == ConfidenceLevel.MEDIUM:
            return int(round(price / 5) * 5)
        else:
            return int(round(price / 10) * 10)
    
    def analyze_item(
        self,
        item_id: int,
        item_name: str,
        current_prices: List[float],
        mode: str = "sell",
        server_id: int = 0
    ) -> PriceAnalysis:
        """Анализирует предмет и рассчитывает справедливую цену."""
        analysis = PriceAnalysis(
            item_id=item_id,
            item_name=item_name,
            current_prices=current_prices.copy(),
            data_points_current=len(current_prices)
        )
        
        current_median = 0.0
        current_variance = 0.5
        
        if current_prices:
            current_median = self._calculate_iqr_median(current_prices)
            current_avg = statistics.mean(current_prices)
            current_std = statistics.stdev(current_prices) if len(current_prices) > 1 else 0
            current_variance = (current_std / current_avg) if current_avg > 0 else 0
        
        # Получаем исторические данные
        analyzer = self.historical_data_service.get_analyzer(server_id)
        
        historical_trend = analyzer.calculate_price_trend(item_name, mode, days=7)
        
        analysis.historical_avg = historical_trend.get("avg_price", 0)
        analysis.historical_trend = historical_trend.get("trend", "stable")
        analysis.historical_trend_percent = historical_trend.get("price_change_percent", 0)
        analysis.liquidity_score = analyzer.calculate_liquidity_score(item_name, mode, days=30)
        analysis.data_points_historical = historical_trend.get("data_points", 0)
        analysis.used_historical = analysis.data_points_historical > 0
        
        # Расчёт взвешенной цены
        weighted_price = 0.0
        weights_used = 0.0
        
        if current_median > 0:
            weighted_price += current_median * self.weight_current
            weights_used += self.weight_current
        
        if analysis.historical_avg > 0 and analysis.used_historical:
            weighted_price += analysis.historical_avg * self.weight_historical
            weights_used += self.weight_historical
        
        # Применяем тренд
        if analysis.historical_trend != "stable" and analysis.used_historical:
            trend_factor = 1.0
            if analysis.historical_trend == "up":
                trend_factor = 1.0 + (abs(analysis.historical_trend_percent) / 100 * 0.5)
            elif analysis.historical_trend == "down":
                trend_factor = 1.0 - (abs(analysis.historical_trend_percent) / 100 * 0.5)
            
            weighted_price *= trend_factor
            weights_used += self.weight_trend
        
        if weights_used > 0:
            analysis.weighted_price = weighted_price / weights_used
        elif current_median > 0:
            analysis.weighted_price = current_median
        elif analysis.historical_avg > 0:
            analysis.weighted_price = analysis.historical_avg
        
        # Расчёт уверенности
        analysis.confidence, analysis.confidence_score = self._calculate_confidence(
            current_count=len(current_prices),
            historical_days=analysis.data_points_historical,
            liquidity=analysis.liquidity_score,
            price_variance=current_variance,
        )
        
        # Округление
        analysis.final_price = self._round_price(analysis.weighted_price, analysis.confidence)
        analysis.final_price = max(analysis.final_price, 1)
        
        return analysis
    
    async def generate_config(
        self,
        server_id: int,
        mode: ConfigMode,
        percentage: float,
        users_data: List[dict],
        min_liquidity: float = 0.0,
    ) -> Tuple[List[ConfigItemResponse], Dict]:
        """
        Генерирует торговый конфиг.

        Args:
            server_id: ID сервера
            mode: Режим (SELL/BUY)
            percentage: Процент корректировки
            users_data: Данные пользователей из API
            min_liquidity: Минимальный порог ликвидности (0-100) для фильтрации предметов

        Returns:
            (config_items, stats)
        """
        # Группировка предметов по item_id (используем базовый метод)
        items_data = self._group_items_from_users(users_data, server_id, mode)

        # Анализ каждого предмета
        config_items: List[ConfigItemResponse] = []
        items_with_history = 0
        confidence_scores = []
        filtered_by_liquidity = 0

        for item_id, (item_name, prices) in items_data.items():
            analysis = self.analyze_item(item_id, item_name, prices, mode.value, server_id)

            # Фильтрация по ликвидности
            if analysis.liquidity_score < min_liquidity:
                filtered_by_liquidity += 1
                continue

            if analysis.used_historical:
                items_with_history += 1

            confidence_scores.append(analysis.confidence_score)

            # Применяем процентную корректировку
            adjusted_price = int(analysis.final_price * (1 + percentage / 100))
            adjusted_price = max(adjusted_price, 1)

            config_item = self._create_config_item(item_name, adjusted_price)
            config_items.append(config_item)

        # Сортировка по item_id и присвоение position_tab
        config_items_sorted = sorted(
            zip(list(items_data.keys()), config_items),
            key=lambda x: x[0]
        )

        final_items = []
        for idx, (item_id, item) in enumerate(config_items_sorted, start=1):
            item.position_tab = idx
            final_items.append(item)

        # Статистика (используем базовый метод)
        stats = self._calculate_stats(
            config_items=final_items,
            items_with_history=items_with_history,
            confidence_scores=confidence_scores,
            extra_stats={
                "filtered_by_liquidity": filtered_by_liquidity,
            },
        )

        return final_items, stats

    async def generate_config_by_liquidity(
        self,
        server_id: int,
        mode: ConfigMode,
        percentage: float,
        users_data: List[dict],
        top_count: int = 10,
    ) -> Tuple[List[ConfigItemResponse], Dict]:
        """
        Генерирует конфиг топ-N предметов по ликвидности.

        Args:
            server_id: ID сервера
            mode: Режим (SELL/BUY)
            percentage: Процент корректировки
            users_data: Данные пользователей из API
            top_count: Количество топ предметов (10, 50, 100)

        Returns:
            (config_items, stats)
        """
        # Группировка предметов (используем базовый метод)
        items_data = self._group_items_from_users(users_data, server_id, mode)

        # Расчёт ликвидности для каждого предмета
        liquidity_scores: List[Tuple[int, str, List[float], float]] = []
        analyzer = self.historical_data_service.get_analyzer(server_id)

        for item_id, (item_name, prices) in items_data.items():
            liquidity = analyzer.calculate_liquidity_score(
                item_name,
                mode.value,
                days=30
            )
            liquidity_scores.append((item_id, item_name, prices, liquidity))

        # Сортировка по ликвидности (убывание) и выбор топ-N
        liquidity_scores.sort(key=lambda x: x[3], reverse=True)
        top_items = liquidity_scores[:top_count]

        # Генерация конфига
        config_items: List[ConfigItemResponse] = []
        confidence_scores = []

        for item_id, item_name, prices, liquidity in top_items:
            analysis = self.analyze_item(item_id, item_name, prices, mode.value, server_id)
            confidence_scores.append(analysis.confidence_score)

            # Применяем процентную корректировку
            adjusted_price = int(analysis.final_price * (1 + percentage / 100))
            adjusted_price = max(adjusted_price, 1)

            config_item = self._create_config_item(item_name, adjusted_price)
            config_items.append(config_item)

        # Сортировка по ликвидности и присвоение position_tab
        for idx, item in enumerate(config_items, start=1):
            item.position_tab = idx

        # Статистика (используем базовый метод)
        stats = self._calculate_stats(
            config_items=config_items,
            confidence_scores=confidence_scores,
            extra_stats={
                "top_count": top_count,
                "avg_liquidity": statistics.mean([x[3] for x in top_items]) if top_items else 0,
            }
        )

        return config_items, stats

    async def generate_config_by_category(
        self,
        server_id: int,
        mode: ConfigMode,
        percentage: float,
        users_data: List[dict],
        category: str,
    ) -> Tuple[List[ConfigItemResponse], Dict]:
        """
        Генерирует конфиг предметов определённой категории.

        Args:
            server_id: ID сервера
            mode: Режим (SELL/BUY)
            percentage: Процент корректировки
            users_data: Данные пользователей из API
            category: Ключ категории ("all", "mine_resources", "farm_resources", etc.)

        Returns:
            (config_items, stats)
        """
        # Группировка предметов (используем базовый метод)
        items_data = self._group_items_from_users(users_data, server_id, mode)

        # Фильтрация по категории
        filtered_items = get_items_by_category(items_data, category)

        # Генерация конфига
        config_items: List[ConfigItemResponse] = []
        items_with_history = 0
        confidence_scores = []

        for item_id, (item_name, prices) in filtered_items.items():
            analysis = self.analyze_item(item_id, item_name, prices, mode.value, server_id)

            if analysis.used_historical:
                items_with_history += 1

            confidence_scores.append(analysis.confidence_score)

            # Применяем процентную корректировку
            adjusted_price = int(analysis.final_price * (1 + percentage / 100))
            adjusted_price = max(adjusted_price, 1)

            config_item = self._create_config_item(item_name, adjusted_price)
            config_items.append(config_item)

        # Сортировка по item_id и присвоение position_tab
        config_items_sorted = sorted(
            zip(list(filtered_items.keys()), config_items),
            key=lambda x: x[0]
        )

        final_items = []
        for idx, (item_id, item) in enumerate(config_items_sorted, start=1):
            item.position_tab = idx
            final_items.append(item)

        # Статистика (используем базовый метод)
        all_categories = get_all_categories()
        stats = self._calculate_stats(
            config_items=final_items,
            items_with_history=items_with_history,
            confidence_scores=confidence_scores,
            extra_stats={
                "category": category,
                "category_name": all_categories[int(category)]["name"] if category.isdigit() and int(category) < len(all_categories) else category,
            }
        )

        return final_items, stats
