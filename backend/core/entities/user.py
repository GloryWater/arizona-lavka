"""
User domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    """
    Domain сущность пользователя.

    Атрибуты:
        id: Первичный ключ
        username: Уникальное имя пользователя
        email: Уникальный email
        hashed_password: Хешированный пароль
        first_name: Имя (опционально)
        last_name: Фамилия (опционально)
        is_premium: Premium статус
        role: Роль пользователя (user/admin)
        telegram_id: Telegram ID (опционально)
        telegram_username: Telegram username
        is_telegram_user: Флаг Telegram пользователя
        last_active_at: Последняя активность
        login_attempts: Количество неудачных попыток входа
        locked_until: Время разблокировки
        refresh_token: Текущий refresh токен
        created_at: Дата создания
        updated_at: Дата обновления
    """
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    hashed_password: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: bool = False
    role: str = "user"
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    is_telegram_user: bool = False
    last_active_at: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    refresh_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_admin(self) -> bool:
        """Проверяет является ли пользователь администратором."""
        return self.role == "admin"

    def is_locked(self) -> bool:
        """Проверяет заблокирован ли пользователь."""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(timezone.utc)

    def full_name(self) -> str:
        """Возвращает полное имя пользователя."""
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p) or self.username


# Импортируем timezone здесь чтобы избежать circular imports
from datetime import timezone
