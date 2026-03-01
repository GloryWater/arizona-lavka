"""
Сервис режима обслуживания (Maintenance Mode).

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Возвращает текущее UTC время (timezone-aware)."""
    return datetime.now(timezone.utc)

# Кэш для режима обслуживания
_maintenance_cache: Optional[bool] = None
_maintenance_cache_timestamp: float = 0
_CACHE_TTL_SECONDS = 30  # Кэшируем на 30 секунд


class MaintenanceService:
    """
    Сервис для управления режимом обслуживания.
    
    Режим обслуживания контролируется через глобальную настройку
    'maintenance_mode' в таблице global_settings.
    
    Формат настройки:
    {
        "enabled": true/false,
        "message": "Сообщение для пользователей",
        "started_at": "2026-02-26T10:00:00Z",
        "estimated_end": "2026-02-26T12:00:00Z"
    }
    """
    
    @classmethod
    async def is_maintenance_mode(cls) -> bool:
        """
        Проверяет, включён ли режим обслуживания.
        
        Returns:
            bool: True если режим обслуживания активен
        """
        global _maintenance_cache, _maintenance_cache_timestamp
        
        current_time = time.time()
        
        # Проверка кэша
        if (_maintenance_cache is not None and 
            (current_time - _maintenance_cache_timestamp) < _CACHE_TTL_SECONDS):
            return _maintenance_cache
        
        # Получаем настройку из БД
        try:
            from database import GlobalSetting
            from dependencies import get_db_manager
            from fastapi import Request
            
            # Для использования вне запросов нужен отдельный подход
            # Используем lazy import чтобы избежать circular dependency
            setting = await cls._get_maintenance_setting()
            
            if setting and isinstance(setting.value, dict):
                is_maintenance = setting.value.get("enabled", False)
                _maintenance_cache = is_maintenance
                _maintenance_cache_timestamp = current_time
                return is_maintenance
        except Exception as e:
            logger.warning(f"Ошибка проверки maintenance mode: {e}")
        
        # По умолчанию режим выключен
        _maintenance_cache = False
        _maintenance_cache_timestamp = current_time
        return False
    
    @classmethod
    async def _get_maintenance_setting(cls) -> Optional["GlobalSetting"]:
        """
        Получает настройку maintenance_mode из БД.

        Returns:
            GlobalSetting или None
        """
        from database import GlobalSetting, DatabaseManager
        from config import get_settings

        settings = get_settings()

        # Создаём временную сессию для получения настройки из БД
        db_manager = DatabaseManager(settings.database_url, echo=False)

        try:
            await db_manager.initialize()
            async with db_manager.get_session_no_commit() as session:
                result = await session.execute(
                    select(GlobalSetting).where(GlobalSetting.key == "maintenance_mode")
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Ошибка получения maintenance настройки: {e}")
            return None
        finally:
            # Гарантированное закрытие соединения даже при ошибке инициализации
            await db_manager.close()
    
    @classmethod
    async def enable_maintenance(
        cls,
        session: AsyncSession,
        message: str = "Технические работы",
        estimated_end: Optional[str] = None
    ) -> bool:
        """
        Включает режим обслуживания.

        Args:
            session: Сессия БД
            message: Сообщение для пользователей
            estimated_end: Предполагаемое время окончания (ISO 8601)

        Returns:
            bool: True если успешно
        """
        from database import GlobalSetting

        global _maintenance_cache, _maintenance_cache_timestamp

        try:
            # Ищем существующую настройку
            result = await session.execute(
                select(GlobalSetting).where(GlobalSetting.key == "maintenance_mode")
            )
            setting = result.scalar_one_or_none()

            maintenance_data = {
                "enabled": True,
                "message": message,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "estimated_end": estimated_end,
            }

            if setting:
                setting.value = maintenance_data
                setting.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                setting = GlobalSetting(
                    key="maintenance_mode",
                    value=maintenance_data,
                )
                session.add(setting)

            await session.commit()

            # Инвалидация кэша
            _maintenance_cache = True
            _maintenance_cache_timestamp = time.time()

            logger.info("Режим обслуживания ВКЛЮЧЁН")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка включения maintenance mode: {e}")
            return False
    
    @classmethod
    async def disable_maintenance(cls, session: AsyncSession) -> bool:
        """
        Выключает режим обслуживания.

        Args:
            session: Сессия БД

        Returns:
            bool: True если успешно
        """
        from database import GlobalSetting

        global _maintenance_cache, _maintenance_cache_timestamp

        try:
            result = await session.execute(
                select(GlobalSetting).where(GlobalSetting.key == "maintenance_mode")
            )
            setting = result.scalar_one_or_none()

            if setting:
                # Сохраняем историю последнего обслуживания
                old_value = setting.value
                setting.value = {
                    "enabled": False,
                    "last_maintenance": {
                        "started_at": old_value.get("started_at"),
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "message": old_value.get("message"),
                    }
                }
                setting.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await session.commit()
            else:
                # Создаём настройку с выключенным режимом
                setting = GlobalSetting(
                    key="maintenance_mode",
                    value={
                        "enabled": False,
                    },
                )
                session.add(setting)
                await session.commit()

            # Инвалидация кэша
            _maintenance_cache = False
            _maintenance_cache_timestamp = time.time()

            logger.info("Режим обслуживания ВЫКЛЮЧЕН")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка выключения maintenance mode: {e}")
            return False
    
    @classmethod
    async def get_maintenance_info(cls, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о режиме обслуживания.
        
        Args:
            session: Сессия БД
            
        Returns:
            Dict с информацией о maintenance или None
        """
        from database import GlobalSetting
        
        try:
            result = await session.execute(
                select(GlobalSetting).where(GlobalSetting.key == "maintenance_mode")
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                return setting.value
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения maintenance info: {e}")
            return None
    
    @classmethod
    def invalidate_cache(cls) -> None:
        """
        Инвалидирует кэш режима обслуживания.
        
        Используйте после ручного изменения настройки в БД.
        """
        global _maintenance_cache, _maintenance_cache_timestamp
        _maintenance_cache = None
        _maintenance_cache_timestamp = 0
