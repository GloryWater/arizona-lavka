"""
External service interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Any


class IMarketplaceAPI(ABC):
    """
    Интерфейс для внешнего marketplace API.

    Абстрагирует получение данных из внешнего API.
    """

    @abstractmethod
    async def fetch_marketplace_data(self) -> List[dict]:
        """
        Получает данные marketplace.

        Returns:
            Список данных пользователей из API
        """
        pass
