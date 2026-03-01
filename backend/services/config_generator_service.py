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
import math
import statistics
from datetime import datetime, timedelta
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

    Веса для расчёта цены (настраиваются через settings):
    - Текущие цены: 40%
    - Исторические данные: 35%
    - Тренды: 25%

    Note:
        Веса по умолчанию могут быть переопределены через класс-атрибуты.
    """

    # Веса для расчёта взвешенной цены (класс-атрибуты для переопределения)
    WEIGHT_CURRENT: float = 0.40
    WEIGHT_HISTORICAL: float = 0.35
    WEIGHT_TREND: float = 0.25

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

        # Веса для расчёта (используем класс-атрибуты)
        self.weight_current = self.WEIGHT_CURRENT
        self.weight_historical = self.WEIGHT_HISTORICAL
        self.weight_trend = self.WEIGHT_TREND
        
        # Кэш для анализа предметов (TTL: 5 минут)
        self._analysis_cache: Dict[str, Tuple[PriceAnalysis, datetime]] = {}
        self._cache_ttl = 300  # секунд
        
        # Флаг для отслеживания манипуляций (для логирования)
        self._manipulation_warnings: Dict[str, int] = {}

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

        logger.info(f"Группировка предметов: server_id={server_id}, mode={mode.value}, пользователей={len(users_data)}")

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

        logger.info(f"Сгруппировано {len(items_data)} уникальных предметов")
        return items_data

    def invalidate_cache(self):
        """
        Очищает кэш анализа предметов.
        
        Вызывается перед новой генерацией для обеспечения актуальности данных.
        """
        self._analysis_cache.clear()
        logger.debug("Кэш анализа предметов очищен")

    def _check_manipulation(
        self,
        item_name: str,
        prices: List[float],
        users_data: List[dict],
        server_id: int,
        mode: ConfigMode
    ) -> Tuple[bool, str]:
        """
        Выявляет подозрительные паттерны (консервативно, без ложных срабатываний).
        
        Критерии обнаружения манипуляций (все должны выполняться):
        1. Один пользователь имеет >70% всех предложений (очень высокий порог)
        2. При этом у него >10 предложений (минимум для статистики)
        3. Цены одинаковые или отличаются <5% (признак сговора)
        
        Args:
            item_name: Название предмета
            prices: Список цен
            users_data: Данные пользователей
            server_id: ID сервера
            mode: Режим торговли
        
        Returns:
            (is_manipulated, reason) - если манипуляция не обнаружена, (False, "")
        """
        # Требуем минимум 10 цен для анализа (защита от ложных срабатываний)
        if len(prices) < 10:
            return False, ""
        
        # Считаем предложения по пользователям
        user_prices: Dict[str, List[float]] = {}
        mode_key = "items_sell" if mode == ConfigMode.SELL else "items_buy"
        price_key = "price_sell" if mode == ConfigMode.SELL else "price_buy"
        
        for user_data in users_data:
            if user_data.get("serverId") != server_id:
                continue
            
            username = user_data.get("username", "unknown")
            items = user_data.get(mode_key) or []
            user_prices_list = user_data.get(price_key) or []
            
            for item, price in zip(items, user_prices_list):
                parsed_id = LavkaService.parse_item_id(item)
                if parsed_id is None:
                    continue
                
                # Проверяем, тот ли это предмет
                try:
                    item_name_check = LavkaService.get_item_name(parsed_id)
                    if item_name_check != item_name:
                        continue
                except (ValueError, TypeError):
                    continue
                
                if username not in user_prices:
                    user_prices[username] = []
                try:
                    user_prices[username].append(float(price))
                except (ValueError, TypeError):
                    continue
        
        # Проверка: один пользователь имеет >70% предложений
        total_prices = sum(len(p) for p in user_prices.values())
        if total_prices < 10:  # Ещё одна проверка
            return False, ""
        
        max_user_prices = max(len(p) for p in user_prices.values()) if user_prices else 0
        dominance_ratio = max_user_prices / total_prices if total_prices > 0 else 0
        
        # Порог 70% для обнаружения доминирования
        if dominance_ratio <= 0.70:
            return False, ""
        
        # Проверка на одинаковость цен у доминирующего пользователя
        dominant_user = max(user_prices.keys(), key=lambda u: len(user_prices[u]))
        dominant_prices = user_prices[dominant_user]
        
        if len(dominant_prices) < 10:
            return False, ""
        
        # Проверяем, насколько одинаковы цены (вариация <5%)
        avg_price = statistics.mean(dominant_prices)
        if avg_price == 0:
            return False, ""
        
        variance = statistics.stdev(dominant_prices) / avg_price if len(dominant_prices) > 1 else 0
        
        # Манипуляция: доминирование >70% + вариация цен <5%
        if variance < 0.05:
            # Логирование с ограничением частоты (не чаще 1 раза на предмет)
            if item_name not in self._manipulation_warnings:
                logger.warning(
                    f"Возможная манипуляция: item={item_name}, "
                    f"user={dominant_user}, dominance={dominance_ratio:.1%}, "
                    f"variance={variance:.2%}"
                )
                self._manipulation_warnings[item_name] = 1
            
            return True, f"User {dominant_user} dominates with {dominance_ratio:.1%}"
        
        return False, ""

    def _calculate_dynamic_weights(
        self,
        liquidity_score: float,
        data_points: int,
        price_variance: float,
        mode: str = "sell"
    ) -> Tuple[float, float, float]:
        """
        Адаптивная настройка весов (консервативно, без резких изменений).

        Args:
            liquidity_score: Ликвидность предмета (0-100)
            data_points: Количество текущих данных
            price_variance: Вариация цен (0-1)
            mode: Режим торговли ("sell" или "buy")

        Returns:
            (weight_current, weight_historical, weight_trend)
        """
        # Для SELL режима больше доверяем текущим ценам (чтобы быть конкурентными)
        # Для BUY режима больше доверяем истории (чтобы не переплачивать)
        is_sell = mode.lower() == "sell"

        # Очень мало данных → больше доверия истории
        if data_points < 3 or liquidity_score < 20:
            return (0.30, 0.50, 0.20) if not is_sell else (0.50, 0.30, 0.20)

        # Мало данных → смещение к истории
        if data_points < 5 or liquidity_score < 40:
            return (0.35, 0.45, 0.20) if not is_sell else (0.55, 0.25, 0.20)

        # Высокая волатильность → меньше доверия трендам
        if price_variance > 0.6:
            return (0.50, 0.35, 0.15) if not is_sell else (0.60, 0.25, 0.15)

        # Очень высокая ликвидность → больше доверия текущим ценам
        if liquidity_score > 85 and data_points >= 15:
            return (0.45, 0.35, 0.20) if not is_sell else (0.65, 0.20, 0.15)

        # Стандартные веса (по умолчанию)
        return (0.40, 0.35, 0.25) if not is_sell else (0.60, 0.25, 0.15)

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
        Рассчитывает статистику для конфига (расширенная).

        Args:
            config_items: Список элементов конфига
            items_with_history: Количество предметов с историческими данными
            confidence_scores: Список очков уверенности
            extra_stats: Дополнительные поля для статистики

        Returns:
            Dict со статистикой
        """
        price_values = [int(item.price) for item in config_items]

        # Базовая статистика
        stats = {
            "total_items": len(config_items),
            "items_with_history": items_with_history,
            "avg_confidence": statistics.mean(confidence_scores) if confidence_scores else 0,
            "price_range": {
                "min": min(price_values) if price_values else 0,
                "max": max(price_values) if price_values else 0,
                "avg": statistics.mean(price_values) if price_values else 0,
                "median": statistics.median(price_values) if price_values else 0,
            }
        }

        # Расширенная статистика (только если есть данные)
        if price_values:
            sorted_prices = sorted(price_values)
            n = len(sorted_prices)
            
            # Процентили
            stats["percentiles"] = {
                "p25": sorted_prices[n // 4] if n >= 4 else sorted_prices[0],
                "p50": sorted_prices[n // 2],
                "p75": sorted_prices[3 * n // 4] if n >= 4 else sorted_prices[-1],
            }
            
            # Распределение по ценовым категориям
            stats["price_distribution"] = {
                "cheap": sum(1 for p in price_values if p < 50),
                "medium": sum(1 for p in price_values if 50 <= p < 200),
                "expensive": sum(1 for p in price_values if p >= 200),
            }
        
        # Распределение уверенности
        if confidence_scores:
            stats["confidence_distribution"] = {
                "high": sum(1 for c in confidence_scores if c >= 0.75),
                "medium": sum(1 for c in confidence_scores if 0.50 <= c < 0.75),
                "low": sum(1 for c in confidence_scores if c < 0.50),
            }

        if extra_stats:
            stats.update(extra_stats)

        return stats
    
    @staticmethod
    def _calculate_iqr_median(prices: List[float], use_percentile: float = 50) -> float:
        """
        Рассчитывает медиану/перцентиль с IQR фильтрацией выбросов.

        Args:
            prices: Список цен для анализа
            use_percentile: Перцентиль для расчёта (50 = медиана, 75 = верхняя четверть, 90 = топ-10%)

        Returns:
            float: Значение после фильтрации выбросов

        Note:
            Guard clauses:
            - Пустой список → 0.0
            - 1-2 элемента → медиана без фильтрации
            - Если отфильтровано >50% → медиана оригинальных данных
        """
        if not prices:
            logger.warning("Пустой список цен для IQR-медианы")
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

        # Если отфильтровано больше 50% данных, используем перцентиль всех цен
        if len(filtered) < len(prices) * 0.5:
            logger.debug(f"Отфильтровано {len(prices) - len(filtered)} из {len(prices)} цен (>50%), используем исходный перцентиль")
            # Расчёт перцентиля
            k = (len(sorted_prices) - 1) * (use_percentile / 100)
            f = int(k)
            c = f + 1 if f + 1 < len(sorted_prices) else f
            return sorted_prices[f] + (k - f) * (sorted_prices[c] - sorted_prices[f])

        # Расчёт перцентиля на отфильтрованных данных
        k = (len(filtered) - 1) * (use_percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(filtered) else f
        return filtered[f] + (k - f) * (filtered[c] - filtered[f])
    
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
    def _round_price(price: float, confidence: ConfidenceLevel, mode: str = "sell") -> int:
        """
        Округляет цену в зависимости от уверенности и режима.

        Для SELL режима округляем ВВЕРХ (чтобы не занизить цену).
        Для BUY режима округляем ВНИЗ (чтобы не переплачивать).
        """
        is_sell = mode.lower() == "sell"

        if confidence in (ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH):
            rounded = int(round(price))
            return math.ceil(rounded * 1.02) if is_sell else math.floor(rounded * 0.98)
        elif confidence == ConfidenceLevel.MEDIUM:
            # Округление до 5, но для SELL - вверх, для BUY - вниз
            if is_sell:
                return int(math.ceil(price / 5) * 5)
            else:
                return int(math.floor(price / 5) * 5)
        else:
            # Низкая уверенность - округление до 10
            if is_sell:
                return int(math.ceil(price / 10) * 10)
            else:
                return int(math.floor(price / 10) * 10)
    
    def analyze_item(
        self,
        item_id: int,
        item_name: str,
        current_prices: List[float],
        mode: str = "sell",
        server_id: int = 0,
        users_data: Optional[List[dict]] = None,
        config_mode: Optional[ConfigMode] = None,
    ) -> PriceAnalysis:
        """
        Анализирует предмет и рассчитывает справедливую цену.
        
        Улучшения:
        1. Кэширование результатов (TTL: 5 минут)
        2. Исправленное применение тренда (аддитивное, не мультипликативное)
        3. Адаптивные веса в зависимости от качества данных
        4. Детекция манипуляций (консервативная)
        
        Args:
            item_id: ID предмета
            item_name: Название предмета
            current_prices: Список текущих цен
            mode: Режим торговли ("sell" или "buy")
            server_id: ID сервера
            users_data: Данные пользователей (для детекции манипуляций)
            config_mode: Режим конфига (для детекции манипуляций)
        
        Returns:
            PriceAnalysis с результатами анализа
        """
        # Проверка кэша
        cache_key = f"{item_id}:{mode}:{server_id}"
        now = datetime.utcnow()
        
        if cache_key in self._analysis_cache:
            cached_analysis, cached_time = self._analysis_cache[cache_key]
            if (now - cached_time).total_seconds() < self._cache_ttl:
                return cached_analysis
        
        # Базовая инициализация
        analysis = PriceAnalysis(
            item_id=item_id,
            item_name=item_name,
            current_prices=current_prices.copy(),
            data_points_current=len(current_prices)
        )

        current_median = 0.0
        current_variance = 0.5

        if current_prices:
            # Для SELL режима используем 75-й перцентиль (верхняя четверть), для BUY - медиану
            # Это даёт более высокие цены для продажи и более низкие для покупки
            percentile = 75 if (isinstance(mode, str) and mode.lower() == "sell") or (hasattr(mode, 'value') and mode.value == "SELL") else 50
            current_median = self._calculate_iqr_median(current_prices, use_percentile=percentile)
            current_avg = statistics.mean(current_prices)
            current_std = statistics.stdev(current_prices) if len(current_prices) > 1 else 0
            current_variance = (current_std / current_avg) if current_avg > 0 else 0

        # Получаем исторические данные
        analyzer = self.historical_data_service.get_analyzer(server_id)

        # Конвертируем режим в нижний регистр для исторических данных ("SELL" -> "sell", "BUY" -> "buy")
        mode_lower = mode.lower() if isinstance(mode, str) else mode.value.lower()

        # ИНВЕРСИЯ: для SELL конфига используем buy историю (цены, по которым покупали)
        # для BUY конфига используем sell историю (цены, по которым продавали)
        historical_mode = "buy" if mode_lower == "sell" else "sell"

        historical_trend = analyzer.calculate_price_trend(item_name, historical_mode, days=7)

        analysis.historical_avg = historical_trend.get("avg_price", 0)
        analysis.historical_trend = historical_trend.get("trend", "stable")
        analysis.historical_trend_percent = historical_trend.get("price_change_percent", 0)
        analysis.liquidity_score = analyzer.calculate_liquidity_score(item_name, historical_mode, days=30)
        analysis.data_points_historical = historical_trend.get("data_points", 0)
        analysis.used_historical = analysis.data_points_historical > 0

        # Детекция манипуляций (если предоставлены данные)
        is_manipulated = False
        if users_data and config_mode and len(current_prices) >= 10:
            is_manipulated, _ = self._check_manipulation(
                item_name, current_prices, users_data, server_id, config_mode
            )
            # При манипуляции снижаем ликвидность на 50%
            if is_manipulated:
                analysis.liquidity_score *= 0.5
                logger.debug(f"Предмет {item_name}: ликвидность снижена из-за возможной манипуляции")

        # Адаптивные веса (с учётом режима)
        w_current, w_historical, w_trend = self._calculate_dynamic_weights(
            analysis.liquidity_score,
            len(current_prices),
            current_variance,
            mode_lower
        )

        # Расчёт взвешенной цены (ИСПРАВЛЕНО: тренд применяется аддитивно)
        weighted_price = 0.0
        weights_used = 0.0

        # 1. Базовая цена (текущие + история)
        if current_median > 0:
            weighted_price += current_median * w_current
            weights_used += w_current

        if analysis.historical_avg > 0 and analysis.used_historical:
            weighted_price += analysis.historical_avg * w_historical
            weights_used += w_historical

        # 2. Корректировка трендом (только историческую часть, аддитивно!)
        if analysis.historical_trend != "stable" and analysis.used_historical:
            trend_adjustment = 0.0
            if analysis.historical_trend == "up":
                # Рост тренда → добавляем к цене
                trend_adjustment = analysis.historical_avg * (abs(analysis.historical_trend_percent) / 100 * 0.5)
            elif analysis.historical_trend == "down":
                # Падение тренда → вычитаем из цены
                trend_adjustment = -analysis.historical_avg * (abs(analysis.historical_trend_percent) / 100 * 0.5)
            
            weighted_price += trend_adjustment * w_trend
            weights_used += w_trend

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

        # Округление (с учётом режима)
        analysis.final_price = self._round_price(analysis.weighted_price, analysis.confidence, mode_lower)
        analysis.final_price = max(analysis.final_price, 1)

        # Сохранение в кэш
        self._analysis_cache[cache_key] = (analysis, now)

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
            percentage: Процент корректировки (-50 до +50)
            users_data: Данные пользователей из API
            min_liquidity: Минимальный порог ликвидности (0-100) для фильтрации предметов

        Returns:
            (config_items, stats)

        Note:
            Guard clauses:
            - percentage должен быть в диапазоне [-50, 50]
            - server_id должен быть в диапазоне [0, 32]
            - users_data не должен быть пустым
        """
        # Валидация входных данных (guard clauses)
        if percentage < -50 or percentage > 50:
            logger.warning(f"Percentage {percentage} out of range, clamping to [-50, 50]")
            percentage = max(-50, min(50, percentage))

        if server_id < 0 or server_id > 32:
            logger.error(f"Invalid server_id: {server_id}")
            raise ValueError(f"server_id must be between 0 and 32, got {server_id}")

        # Guard clause: проверка на пустые данные
        if not users_data:
            logger.error("Empty users_data provided to generate_config")
            raise ValueError("users_data cannot be empty - marketplace API returned no data")

        # Guard clause: проверка users_data на корректность структуры
        if not all(isinstance(u, dict) for u in users_data):
            logger.error("Invalid users_data structure: expected list of dicts")
            raise ValueError("users_data must be a list of dictionaries")

        logger.info(f"Начало генерации конфига: server_id={server_id}, mode={mode.value}, percentage={percentage}")

        # Очистка кэша перед новой генерацией
        self.invalidate_cache()

        # Группировка предметов по item_id (используем базовый метод)
        items_data = self._group_items_from_users(users_data, server_id, mode)

        logger.info(f"Получено {len(items_data)} предметов для генерации конфига")

        # Анализ каждого предмета
        config_items: List[ConfigItemResponse] = []
        items_with_history = 0
        confidence_scores = []
        filtered_by_liquidity = 0

        for item_id, (item_name, prices) in items_data.items():
            analysis = self.analyze_item(
                item_id, item_name, prices, mode.value, server_id,
                users_data=users_data, config_mode=mode
            )

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

        logger.info(f"Сгенерировано {len(config_items)} предметов в конфиге (отфильтровано по ликвидности: {filtered_by_liquidity})")

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
        top_count: int = 20,
    ) -> Tuple[List[ConfigItemResponse], Dict]:
        """
        Генерирует конфиг топ-N предметов по ликвидности.

        Args:
            server_id: ID сервера
            mode: Режим (SELL/BUY)
            percentage: Процент корректировки
            users_data: Данные пользователей из API
            top_count: Количество топ предметов (20, 50, 100)

        Returns:
            (config_items, stats)
        """
        # Guard clause: валидация server_id
        if server_id < 0 or server_id > 32:
            logger.error(f"Invalid server_id: {server_id}")
            raise ValueError(f"server_id must be between 0 and 32, got {server_id}")

        # Guard clause: проверка на пустые данные
        if not users_data:
            logger.error("Empty users_data provided to generate_config_by_liquidity")
            raise ValueError("users_data cannot be empty - marketplace API returned no data")

        # Guard clause: проверка структуры данных
        if not all(isinstance(u, dict) for u in users_data):
            logger.error("Invalid users_data structure: expected list of dicts")
            raise ValueError("users_data must be a list of dictionaries")

        # Guard clause: валидация top_count
        if top_count < 1 or top_count > 100:
            logger.warning(f"top_count {top_count} out of range, clamping to [1, 100]")
            top_count = max(1, min(100, top_count))

        # Очистка кэша перед новой генерацией
        self.invalidate_cache()

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
            analysis = self.analyze_item(
                item_id, item_name, prices, mode.value, server_id,
                users_data=users_data, config_mode=mode
            )
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
        # Guard clause: валидация server_id
        if server_id < 0 or server_id > 32:
            logger.error(f"Invalid server_id: {server_id}")
            raise ValueError(f"server_id must be between 0 and 32, got {server_id}")

        # Guard clause: проверка на пустые данные
        if not users_data:
            logger.error("Empty users_data provided to generate_config_by_category")
            raise ValueError("users_data cannot be empty - marketplace API returned no data")

        # Guard clause: проверка структуры данных
        if not all(isinstance(u, dict) for u in users_data):
            logger.error("Invalid users_data structure: expected list of dicts")
            raise ValueError("users_data must be a list of dictionaries")

        # Guard clause: валидация category
        from services.item_categories import get_all_categories
        valid_categories = [str(i) for i in range(len(get_all_categories()))]
        if category not in valid_categories and category != "all":
            logger.warning(f"Invalid category '{category}', using 'all' instead")
            category = "all"

        # Очистка кэша перед новой генерацией
        self.invalidate_cache()

        # Группировка предметов (используем базовый метод)
        items_data = self._group_items_from_users(users_data, server_id, mode)

        # Фильтрация по категории
        filtered_items = get_items_by_category(items_data, category)

        # Генерация конфига
        config_items: List[ConfigItemResponse] = []
        items_with_history = 0
        confidence_scores = []

        for item_id, (item_name, prices) in filtered_items.items():
            analysis = self.analyze_item(
                item_id, item_name, prices, mode.value, server_id,
                users_data=users_data, config_mode=mode
            )

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

    async def generate_config_batch(
        self,
        server_id: int,
        mode: ConfigMode,
        percentage: float,
        users_data: List[dict],
        categories: Optional[List[str]] = None,
        min_liquidity: float = 0.0,
    ) -> Dict[str, Tuple[List[ConfigItemResponse], Dict]]:
        """
        Генерирует конфиги для нескольких категорий за один проход.
        
        Оптимизация: предметы анализируются один раз, затем распределяются по категориям.
        Ускорение: в 5-10 раз при генерации для нескольких категорий.
        
        Args:
            server_id: ID сервера
            mode: Режим (SELL/BUY)
            percentage: Процент корректировки (-50 до +50)
            users_data: Данные пользователей из API
            categories: Список категорий или None для всех доступных
            min_liquidity: Минимальный порог ликвидности (0-100)
        
        Returns:
            Dict {category: (config_items, stats)}
        """
        # Guard clauses
        if server_id < 0 or server_id > 32:
            raise ValueError(f"server_id must be between 0 and 32, got {server_id}")
        
        if not users_data:
            raise ValueError("users_data cannot be empty")
        
        if not all(isinstance(u, dict) for u in users_data):
            raise ValueError("users_data must be a list of dictionaries")
        
        # Очистка кэша
        self.invalidate_cache()
        
        # Группировка предметов
        items_data = self._group_items_from_users(users_data, server_id, mode)
        
        logger.info(f"Пакетная генерация: {len(items_data)} предметов, категории={categories}")
        
        # Анализ ВСЕХ предметов один раз
        all_analyses: Dict[int, PriceAnalysis] = {}
        for item_id, (item_name, prices) in items_data.items():
            all_analyses[item_id] = self.analyze_item(
                item_id, item_name, prices, mode.value, server_id,
                users_data=users_data, config_mode=mode
            )
        
        # Определение категорий для генерации
        if categories is None:
            all_cats = get_all_categories()
            categories = ["all"] + [str(i) for i in range(len(all_cats))]
        
        # Генерация по категориям
        results: Dict[str, Tuple[List[ConfigItemResponse], Dict]] = {}
        
        for category in categories:
            # Фильтрация предметов по категории
            if category == "all":
                filtered_items = items_data
            else:
                filtered_items = get_items_by_category(items_data, category)
            
            # Создание конфига из готовых анализов
            config_items: List[ConfigItemResponse] = []
            items_with_history = 0
            confidence_scores = []
            filtered_by_liquidity = 0
            
            for item_id in filtered_items.keys():
                analysis = all_analyses[item_id]
                
                # Фильтрация по ликвидности
                if analysis.liquidity_score < min_liquidity:
                    filtered_by_liquidity += 1
                    continue
                
                if analysis.used_historical:
                    items_with_history += 1
                
                confidence_scores.append(analysis.confidence_score)
                
                # Процентная корректировка
                adjusted_price = int(analysis.final_price * (1 + percentage / 100))
                adjusted_price = max(adjusted_price, 1)
                
                config_item = self._create_config_item(analysis.item_name, adjusted_price)
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
            
            # Статистика
            extra_stats = {
                "filtered_by_liquidity": filtered_by_liquidity,
                "category": category,
            }
            
            if category != "all":
                all_cats = get_all_categories()
                if category.isdigit() and int(category) < len(all_cats):
                    extra_stats["category_name"] = all_cats[int(category)]["name"]
            
            stats = self._calculate_stats(
                config_items=final_items,
                items_with_history=items_with_history,
                confidence_scores=confidence_scores,
                extra_stats=extra_stats,
            )
            
            results[category] = (final_items, stats)
        
        logger.info(f"Пакетная генерация завершена: {len(results)} категорий")
        return results
