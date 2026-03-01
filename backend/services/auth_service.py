"""
Сервис аутентификации и авторизации.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database import User


def _utcnow() -> datetime:
    """Возвращает текущее UTC время (timezone-aware)."""
    return datetime.now(timezone.utc)

logger = logging.getLogger(__name__)


# =============================================================================
# Password Hashing
# =============================================================================

class PasswordHandler:
    """Обработчик паролей с использованием bcrypt."""

    @classmethod
    def hash(cls, password: str) -> str:
        """
        Хеширует пароль используя bcrypt.

        Args:
            password: Пароль в открытом виде

        Returns:
            str: Хешированный пароль
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @classmethod
    def verify(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет пароль используя bcrypt с защитой от timing attack.

        Args:
            plain_password: Пароль в открытом виде
            hashed_password: Хешированный пароль

        Returns:
            bool: True если пароль верный

        Note:
            Используется bcrypt.checkpw который имеет постоянное время сравнения
            для защиты от атак по времени (timing attack).
        """
        try:
            # bcrypt.checkpw internally использует constant-time comparison
            # что защищает от timing attack при подборе пароля
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            # Возвращаем False при любых ошибках валидации
            # чтобы не раскрывать информацию о формате хеша
            return False


# =============================================================================
# JWT Token Management
# =============================================================================

class TokenManager:
    """Менеджер JWT токенов."""

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        secret_key: str = None,
        algorithm: str = "HS256",
        user_role: str = "user"
    ) -> str:
        """
        Создаёт access токен.

        Args:
            data: Данные для токена
            expires_delta: Время жизни токена
            secret_key: Секретный ключ
            algorithm: Алгоритм шифрования
            user_role: Роль пользователя (для включения в токен)

        Returns:
            str: JWT токен

        Note:
            Использует timezone-aware datetime для совместимости с PostgreSQL.
            Для PostgreSQL TIMESTAMP WITHOUT TIME ZONE используется naive datetime
            через явное приведение .replace(tzinfo=None).
        """
        to_encode = data.copy()

        if expires_delta:
            expire = _utcnow() + expires_delta
        else:
            expire = _utcnow() + timedelta(minutes=30)

        to_encode.update({
            "exp": expire,
            "iat": _utcnow(),
            "type": "access",
            "role": user_role
        })

        return jwt.encode(to_encode, secret_key, algorithm=algorithm)

    @staticmethod
    def create_refresh_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        secret_key: str = None,
        algorithm: str = "HS256"
    ) -> str:
        """
        Создаёт refresh токен.

        Args:
            data: Данные для токена
            expires_delta: Время жизни токена
            secret_key: Секретный ключ
            algorithm: Алгоритм шифрования

        Returns:
            str: JWT токен
        """
        to_encode = data.copy()

        if expires_delta:
            expire = _utcnow() + expires_delta
        else:
            expire = _utcnow() + timedelta(days=7)

        to_encode.update({
            "exp": expire,
            "iat": _utcnow(),
            "type": "refresh"
        })

        return jwt.encode(to_encode, secret_key, algorithm=algorithm)

    @staticmethod
    def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> Optional[dict]:
        """
        Декодирует JWT токен.

        Args:
            token: JWT токен
            secret_key: Секретный ключ
            algorithm: Алгоритм шифрования

        Returns:
            dict | None: Декодированные данные или None
        """
        try:
            return jwt.decode(token, secret_key, algorithms=[algorithm])
        except JWTError:
            return None


# =============================================================================
# AuthService
# =============================================================================

class AuthService:
    """
    Сервис аутентификации и авторизации.

    Методы:
        authenticate_user: Аутентификация пользователя
        create_user: Создание нового пользователя
        create_token_pair: Создание пары токенов
        validate_refresh_token: Валидация refresh токена
    """

    def __init__(self, session: AsyncSession, settings: Settings):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
            settings: Настройки приложения
        """
        self.session = session
        self.settings = settings

    async def authenticate_user(
        self,
        username_or_email: str,
        password: str
    ) -> Optional["User"]:
        """
        Аутентификация пользователя.

        Args:
            username_or_email: Имя пользователя или email
            password: Пароль

        Returns:
            User | None: Объект пользователя или None
        """
        from database import User

        # Поиск пользователя
        user = await self._get_user_by_username_or_email(username_or_email)
        if not user:
            return None

        # Проверка блокировки
        # Для PostgreSQL используем naive datetime (без timezone)
        if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > _utcnow():
            return None

        # Проверка пароля
        if not PasswordHandler.verify(password, user.hashed_password):
            await self._handle_failed_login(user)
            return None

        # Успешный вход
        await self._handle_successful_login(user)
        return user

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> "User":
        """
        Создание нового пользователя.

        Args:
            username: Имя пользователя
            email: Email
            password: Пароль
            first_name: Имя (опционально)
            last_name: Фамилия (опционально)

        Returns:
            User: Созданный пользователь
        """
        from database import User

        user = User(
            username=username,
            email=email,
            hashed_password=PasswordHandler.hash(password),
            first_name=first_name,
            last_name=last_name,
        )

        self.session.add(user)
        await self.session.flush()  # Get the user ID without committing
        await self.session.refresh(user)

        return user

    async def login_or_create_telegram_user(
        self,
        telegram_user: Dict[str, Any]
    ) -> "User":
        """
        Вход или создание пользователя через Telegram.

        Args:
            telegram_user: Данные пользователя от Telegram

        Returns:
            User: Объект пользователя

        Note:
            Для Telegram-пользователей не используется парольная аутентификация.
            Поле hashed_password заполняется случайным значением для соответствия схеме БД.
            Аутентификация происходит только через Telegram init_data валидацию.
        """
        from database import User
        from sqlalchemy import select
        import secrets

        telegram_id = str(telegram_user.get("id"))

        # Поиск по telegram_id
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Существующий пользователь
            await self._handle_successful_login(user)
            return user

        # Создание нового пользователя
        telegram_username = telegram_user.get("username")
        telegram_first_name = telegram_user.get("first_name", "")
        telegram_last_name = telegram_user.get("last_name", "")

        # Генерируем username из telegram_id если нет username
        username = telegram_username or f"tg_user_{telegram_id}"

        # Проверяем уникальность username
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            username = f"tg_{telegram_id}_{int(_utcnow().timestamp())}"

        # Генерируем случайный пароль вместо детерминированного
        # Он никогда не используется для входа, только для соответствия схеме БД
        random_password = secrets.token_urlsafe(32)

        user = User(
            username=username,
            email=f"{telegram_id}@telegram.local",
            hashed_password=PasswordHandler.hash(random_password),
            first_name=telegram_first_name,
            last_name=telegram_last_name,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            telegram_first_name=telegram_first_name,
            telegram_last_name=telegram_last_name,
            is_telegram_user=True,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"Создан новый Telegram пользователь: {user.username} (ID: {telegram_id})")
        return user

    async def generate_token_pair(self, user: "User") -> dict:
        """
        Создаёт пару токенов (access + refresh).

        Args:
            user: Объект пользователя

        Returns:
            dict: Словарь с токенами
        """
        user_data = {"sub": str(user.id), "username": user.username}

        access_token = TokenManager.create_access_token(
            data=user_data,
            expires_delta=timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            secret_key=self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
            user_role=user.role,
        )

        refresh_token = TokenManager.create_refresh_token(
            data=user_data,
            expires_delta=timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS),
            secret_key=self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

        # Сохраняем refresh токен в БД атомарно
        user.refresh_token = refresh_token

        # Обновляем last_active_at (наивный datetime для PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        user.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Один commit() для обеих операций
        await self.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def create_token_pair(self, user: "User") -> dict:
        """
        Создаёт пару токенов (access + refresh).

        Note:
            Синхронная версия для использования в синхронных контекстах.
            Для асинхронных операций используйте generate_token_pair().

        Args:
            user: Объект пользователя

        Returns:
            dict: Словарь с токенами
        """
        user_data = {"sub": str(user.id), "username": user.username}

        access_token = TokenManager.create_access_token(
            data=user_data,
            expires_delta=timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            secret_key=self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
            user_role=user.role,
        )

        refresh_token = TokenManager.create_refresh_token(
            data=user_data,
            expires_delta=timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS),
            secret_key=self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def validate_refresh_token(self, refresh_token: str) -> Optional["User"]:
        """
        Валидация refresh токена.

        Args:
            refresh_token: Refresh токен

        Returns:
            User | None: Объект пользователя или None
        """
        from database import User

        # Декодирование токена
        payload = TokenManager.decode_token(
            refresh_token,
            self.settings.JWT_SECRET_KEY,
            self.settings.JWT_ALGORITHM,
        )

        if not payload or payload.get("type") != "refresh":
            return None

        # Получение пользователя
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await self.session.get(User, int(user_id))
        if not user or user.refresh_token != refresh_token:
            return None

        return user

    async def update_refresh_token(self, user: "User", refresh_token: str) -> None:
        """
        Обновляет refresh токен пользователя.

        Args:
            user: Объект пользователя
            refresh_token: Новый refresh токен
        """
        user.refresh_token = refresh_token
        await self.session.commit()

    async def revoke_refresh_token(self, user: "User") -> None:
        """
        Отозвать refresh токен (выход).

        Args:
            user: Объект пользователя
        """
        user.refresh_token = None
        await self.session.commit()

    # =============================================================================
    # Private Helper Methods
    # =============================================================================

    async def _get_user_by_username_or_email(
        self,
        username_or_email: str
    ) -> Optional["User"]:
        """Получает пользователя по username или email."""
        from database import User

        # По username
        result = await self.session.execute(
            select(User).where(User.username == username_or_email)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # По email
        result = await self.session.execute(
            select(User).where(User.email == username_or_email)
        )
        return result.scalar_one_or_none()

    async def _handle_failed_login(self, user: "User") -> None:
        """Обрабатывает неудачную попытку входа."""
        user.login_attempts += 1

        if user.login_attempts >= self.settings.MAX_LOGIN_ATTEMPTS:
            # Для PostgreSQL используем naive datetime (без timezone)
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                minutes=self.settings.LOCKOUT_DURATION_MINUTES
            )

        await self.session.commit()

    async def _handle_successful_login(self, user: "User") -> None:
        """Обрабатывает успешный вход."""
        user.login_attempts = 0
        user.locked_until = None
        await self.session.commit()


# Импортируем здесь чтобы избежать circular imports
from fastapi import Request


async def get_current_user_from_request(
    request: Request,
    session: AsyncSession
) -> Optional["User"]:
    """
    Получает текущего пользователя из JWT токена в запросе.

    Args:
        request: HTTP запрос
        session: Сессия базы данных

    Returns:
        User | None: Объект пользователя или None
    """
    from config import get_settings

    settings = get_settings()

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    payload = TokenManager.decode_token(
        token,
        settings.JWT_SECRET_KEY,
        settings.JWT_ALGORITHM,
    )

    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await session.get(User, int(user_id))

    # Обновляем last_active_at без коммита всей сессии
    # Используем flush() чтобы обновить только это изменение
    if user:
        user.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.flush()

    return user
