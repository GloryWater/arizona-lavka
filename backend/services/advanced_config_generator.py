"""Продвинутый генератор торговых конфигов с IQR фильтрацией."""

import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from services.historical_data_service import historical_data_service
from models import ConfigItem, ConfidenceInfo


class AdvancedConfigGenerator:
    """Генератор конфигов с использованием IQR метода и исторических данных."""

    # Веса для расчёта взвешенной цены
    WEIGHT_CURRENT = 0.40
    WEIGHT_HISTORICAL = 0.35
    WEIGHT_TREND = 0.25

    # Пороги уверенности
    CONFIDENCE_THRESHOLDS = {
        "VERY_HIGH": 0.90,
        "HIGH": 0.75,
        "MEDIUM": 0.50,
        "LOW": 0.25,
    }

    def __init__(self):
        self.historical_service = historical_data_service

    def _calculate_iqr_median(self, prices: List[int]) -> Tuple[float, int]:
        """
        Расчёт медианы с использованием IQR метода для фильтрации выбросов.
        
        Возвращает: (медиана, количество отфильтрованных выбросов)
        """
        if not prices:
            return 0.0, 0
        
        if len(prices) == 1:
            return float(prices[0]), 0
        
        # Сортировка
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        # Расчёт Q1 и Q3 с линейной интерполяцией
        q1_pos = (n - 1) * 0.25
        q3_pos = (n - 1) * 0.75
        
        q1_lower = int(q1_pos)
        q1_upper = min(q1_lower + 1, n - 1)
        q1_frac = q1_pos - q1_lower
        q1 = sorted_prices[q1_lower] * (1 - q1_frac) + sorted_prices[q1_upper] * q1_frac
        
        q3_lower = int(q3_pos)
        q3_upper = min(q3_lower + 1, n - 1)
        q3_frac = q3_pos - q3_lower
        q3 = sorted_prices[q3_lower] * (1 - q3_frac) + sorted_prices[q3_upper] * q3_frac
        
        # IQR
        iqr = q3 - q1
        
        # Границы
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Фильтрация выбросов
        filtered_prices = [p for p in sorted_prices if lower_bound <= p <= upper_bound]
        outliers_count = n - len(filtered_prices)
        
        # Если отфильтровано больше 50%, используем медиану всех
        if outliers_count > n * 0.5:
            filtered_prices = sorted_prices
        
        # Медиана
        median = statistics.median(filtered_prices)
        
        return median, outliers_count

    def _calculate_confidence(
        self,
        current_prices_count: int,
        historical_days: int,
        liquidity_score: float,
        price_variance: float,
    ) -> ConfidenceInfo:
        """
        Расчёт уверенности в рекомендации (0-1).
        
        Факторы:
        - Количество текущих предложений (0-0.3)
        - Дней исторических данных (0-0.3)
        - Ликвидность (0-0.25)
        - Стабильность цены (0-0.15)
        """
        # Фактор 1: Количество предложений
        if current_prices_count >= 10:
            factor1 = 0.3
        elif current_prices_count >= 5:
            factor1 = 0.2
        elif current_prices_count >= 2:
            factor1 = 0.1
        else:
            factor1 = 0.0
        
        # Фактор 2: Дней исторических данных
        if historical_days >= 14:
            factor2 = 0.3
        elif historical_days >= 7:
            factor2 = 0.2
        elif historical_days >= 3:
            factor2 = 0.1
        else:
            factor2 = 0.0
        
        # Фактор 3: Ликвидность
        factor3 = (liquidity_score / 100) * 0.25
        
        # Фактор 4: Стабильность цены
        factor4 = (1 - min(price_variance, 1)) * 0.15
        
        # Итоговый score
        score = factor1 + factor2 + factor3 + factor4
        
        # Определение уровня
        if score >= self.CONFIDENCE_THRESHOLDS["VERY_HIGH"]:
            level = "VERY_HIGH"
        elif score >= self.CONFIDENCE_THRESHOLDS["HIGH"]:
            level = "HIGH"
        elif score >= self.CONFIDENCE_THRESHOLDS["MEDIUM"]:
            level = "MEDIUM"
        elif score >= self.CONFIDENCE_THRESHOLDS["LOW"]:
            level = "LOW"
        else:
            level = "VERY_LOW"
        
        return ConfidenceInfo(score=score, level=level)

    def _round_price(self, price: float, confidence_level: str) -> int:
        """Округление цены в зависимости от уверенности."""
        if confidence_level in ("HIGH", "VERY_HIGH"):
            return int(round(price))
        elif confidence_level == "MEDIUM":
            return int(round(price / 5) * 5)
        else:
            return int(round(price / 10) * 10)

    def generate_config(
        self,
        items_data: Dict[int, Tuple[str, List[int]]],
        mode: str,
        server_id: int,
        percentage: float,
    ) -> Tuple[List[ConfigItem], Dict[int, ConfidenceInfo]]:
        """
        Генерация торгового конфига.
        
        Args:
            items_data: {item_id: (item_name, [prices])}
            mode: SELL или BUY
            server_id: ID сервера
            percentage: Процентная корректировка (-50..50)
        
        Returns:
            (config_items, confidence_scores)
        """
        config_items: List[ConfigItem] = []
        confidence_scores: Dict[int, ConfidenceInfo] = {}
        
        for item_id, (item_name, prices) in items_data.items():
            if not prices:
                continue
            
            # Этап 1: Расчёт текущей цены (IQR)
            median_price, outliers_count = self._calculate_iqr_median(prices)
            
            # Этап 2: Загрузка исторических данных
            trend = self.historical_service.get_trend(item_name, mode, server_id, 7)
            liquidity = self.historical_service.get_liquidity(item_name, mode, server_id, 30)
            
            historical_avg = 0.0
            trend_adjustment = 0.0
            historical_days = 0
            
            if trend:
                historical_avg = trend["avg_price"]
                historical_days = trend["data_points"]
                
                # Корректировка на тренд
                if trend["trend"] == "up":
                    trend_adjustment = trend["current_price"] * 1.05
                elif trend["trend"] == "down":
                    trend_adjustment = trend["current_price"] * 0.95
                else:
                    trend_adjustment = trend["current_price"]
            else:
                trend_adjustment = median_price
            
            # Этап 3: Расчёт взвешенной цены
            weighted_price = (
                median_price * self.WEIGHT_CURRENT +
                historical_avg * self.WEIGHT_HISTORICAL +
                trend_adjustment * self.WEIGHT_TREND
            )
            
            # Этап 4: Расчёт уверенности
            price_variance = 0.0
            if len(prices) > 1:
                price_variance = statistics.stdev(prices) / median_price if median_price > 0 else 1.0
            
            confidence = self._calculate_confidence(
                current_prices_count=len(prices),
                historical_days=historical_days,
                liquidity_score=liquidity if liquidity else 0,
                price_variance=min(price_variance, 1),
            )
            
            confidence_scores[item_id] = confidence
            
            # Этап 5: Применение процентной корректировки
            adjusted_price = weighted_price * (1 + percentage / 100)
            
            # Этап 6: Округление
            final_price = self._round_price(adjusted_price, confidence.level)
            final_price = max(final_price, 1)  # Минимум 1
            
            # Создание элемента конфига
            config_item = ConfigItem(
                price=str(final_price),  # Строка!
                maximum=True,
                enabled=True,
                name=item_name,
                price_vc=9,
                count=1,
                slot_count=["0"],
                slot_id=["0"],
                position_tab=0,  # Будет установлено позже
                all_count=0,
                continue_field="1",
                count_maximum=0,
            )
            config_items.append(config_item)
        
        # Сортировка по item_id и присвоение position_tab
        config_items_with_ids = sorted(
            zip(list(items_data.keys())[:len(config_items)], config_items),
            key=lambda x: x[0]
        )
        
        sorted_config_items = []
        for idx, (item_id, item) in enumerate(config_items_with_ids, start=1):
            item.position_tab = idx
            sorted_config_items.append(item)
        
        return sorted_config_items, confidence_scores


# Глобальный экземпляр
advanced_config_generator = AdvancedConfigGenerator()
