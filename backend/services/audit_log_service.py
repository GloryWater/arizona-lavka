"""
Сервис аудита и логирования событий пользователей.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuditLogService:
    """
    Сервис для логирования событий пользователей.

    События:
    - USER_REGISTERED: Регистрация нового пользователя
    - USER_LOGGED_IN: Вход пользователя
    - CONFIG_GENERATED: Генерация конфига
    - USER_DELETED: Удаление пользователя (admin)
    - SETTINGS_UPDATED: Изменение глобальных настроек (admin)
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    async def log_event(
        self,
        user_id: Optional[int],
        username: Optional[str],
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Логирует событие пользователя.

        Args:
            user_id: ID пользователя (если доступно)
            username: Имя пользователя (если доступно)
            event_type: Тип события (USER_REGISTERED, USER_LOGGED_IN, CONFIG_GENERATED)
            details: Детали события
            ip_address: IP адрес клиента
        """
        from database import AuditLog

        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=event_type,
                resource="user" if event_type in ["USER_REGISTERED", "USER_LOGGED_IN", "USER_DELETED"] else "config",
                resource_id=user_id,
                ip_address=ip_address,
                details=str(details) if details else None,
                status="success",
            )

            self.session.add(log_entry)
            await self.session.commit()

            logger.info(f"Audit: {event_type} - user_id={user_id}, username={username}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to log audit event {event_type}: {e}")
            # Не пробрасываем ошибку, чтобы не ломать основной поток

    async def log_user_registered(
        self,
        user_id: int,
        username: str,
        email: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Логирует регистрацию пользователя."""
        await self.log_event(
            user_id=user_id,
            username=username,
            event_type="USER_REGISTERED",
            details={"email": email},
            ip_address=ip_address,
        )

    async def log_user_logged_in(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Логирует вход пользователя."""
        await self.log_event(
            user_id=user_id,
            username=username,
            event_type="USER_LOGGED_IN",
            details={"login_method": "password"},
            ip_address=ip_address,
        )

    async def log_config_generated(
        self,
        user_id: int,
        username: str,
        server_id: int,
        mode: str,
        items_count: int,
        ip_address: Optional[str] = None,
    ) -> None:
        """Логирует генерацию конфига."""
        await self.log_event(
            user_id=user_id,
            username=username,
            event_type="CONFIG_GENERATED",
            details={
                "server_id": server_id,
                "mode": mode,
                "items_count": items_count,
            },
            ip_address=ip_address,
        )

    async def log_user_deleted(
        self,
        admin_user_id: int,
        admin_username: str,
        deleted_user_id: int,
        deleted_username: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Логирует удаление пользователя администратором.

        Args:
            admin_user_id: ID администратора
            admin_username: Имя администратора
            deleted_user_id: ID удалённого пользователя
            deleted_username: Имя удалённого пользователя
            ip_address: IP адрес
        """
        await self.log_event(
            user_id=admin_user_id,
            username=admin_username,
            event_type="USER_DELETED",
            details={
                "deleted_user_id": deleted_user_id,
                "deleted_username": deleted_username,
            },
            ip_address=ip_address,
        )

    async def log_settings_updated(
        self,
        admin_user_id: int,
        admin_username: str,
        setting_key: str,
        setting_value: Any,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Логирует изменение глобальных настроек администратором.

        Args:
            admin_user_id: ID администратора
            admin_username: Имя администратора
            setting_key: Ключ настройки
            setting_value: Новое значение настройки
            ip_address: IP адрес
        """
        await self.log_event(
            user_id=admin_user_id,
            username=admin_username,
            event_type="SETTINGS_UPDATED",
            details={
                "setting_key": setting_key,
                "setting_value": setting_value,
            },
            ip_address=ip_address,
        )
