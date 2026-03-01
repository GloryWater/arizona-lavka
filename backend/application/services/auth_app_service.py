"""
Auth application service.

Содержит бизнес-логику аутентификации и авторизации.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from application.interfaces.repositories import IUserRepository
from application.dtos import UserRegisterDTO, UserLoginDTO, TokenDTO, TelegramUserDTO
from core.entities.user import UserEntity
from core.exceptions import UnauthorizedError, BusinessRuleViolationError, ValidationError

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Возвращает текущее UTC время."""
    return datetime.now(timezone.utc)


class PasswordHandler:
    """Обработчик паролей с использованием bcrypt."""

    @staticmethod
    def hash(password: str) -> str:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False


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
        from jose import jwt

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
        from jose import jwt

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
        from jose import JWTError, jwt
        try:
            return jwt.decode(token, secret_key, algorithms=[algorithm])
        except JWTError:
            return None


class AuthAppService:
    """
    Application сервис для аутентификации и авторизации.

    Содержит бизнес-логику:
    - Регистрация пользователя
    - Аутентификация по паролю
    - Генерация JWT токенов
    - Telegram аутентификация
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        max_login_attempts: int = 5,
        lockout_duration_minutes: int = 15,
    ):
        self.user_repository = user_repository
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.max_login_attempts = max_login_attempts
        self.lockout_duration_minutes = lockout_duration_minutes

    async def register(self, dto: UserRegisterDTO) -> UserEntity:
        """
        Регистрирует нового пользователя.

        Args:
            dto: DTO регистрации

        Returns:
            UserEntity: Созданный пользователь

        Raises:
            BusinessRuleViolationError: Если пользователь уже существует
        """
        # Проверка существования пользователя
        existing = await self.user_repository.get_by_username(dto.username)
        if existing:
            raise BusinessRuleViolationError(
                message="Пользователь с таким именем уже существует",
                resource="username",
            )

        existing = await self.user_repository.get_by_email(dto.email)
        if existing:
            raise BusinessRuleViolationError(
                message="Пользователь с таким email уже существует",
                resource="email",
            )

        # Валидация email
        if len(dto.email) > 255:
            raise ValidationError(
                message="Email должен быть не более 255 символов",
                field="email",
            )

        # Создание пользователя
        user = UserEntity(
            username=dto.username,
            email=dto.email,
            hashed_password=PasswordHandler.hash(dto.password),
            first_name=dto.first_name,
            last_name=dto.last_name,
        )

        created = await self.user_repository.create(user)
        logger.info(f"Зарегистрирован новый пользователь: {created.username} (ID: {created.id})")
        return created

    async def authenticate(self, dto: UserLoginDTO) -> UserEntity:
        """
        Аутентифицирует пользователя.

        Args:
            dto: DTO входа

        Returns:
            UserEntity: Аутентифицированный пользователь

        Raises:
            UnauthorizedError: Если credentials неверны
        """
        # Поиск пользователя
        user = await self.user_repository.get_by_username_or_email(dto.username_or_email)
        if not user:
            raise UnauthorizedError(message="Неверное имя пользователя или пароль")

        # Проверка блокировки
        if user.is_locked():
            raise UnauthorizedError(
                message="Аккаунт заблокирован после множественных неудачных попыток входа",
            )

        # Проверка пароля
        if not PasswordHandler.verify(dto.password, user.hashed_password):
            await self._handle_failed_login(user)
            raise UnauthorizedError(message="Неверное имя пользователя или пароль")

        # Успешный вход
        await self._handle_successful_login(user)
        return user

    async def generate_tokens(self, user: UserEntity) -> TokenDTO:
        """
        Генерирует пару токенов для пользователя.

        Args:
            user: Domain сущность пользователя

        Returns:
            TokenDTO: Access и refresh токены
        """
        user_data = {"sub": str(user.id), "username": user.username}

        access_token = TokenManager.create_access_token(
            data=user_data,
            expires_delta=timedelta(minutes=self.access_token_expire_minutes),
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            user_role=user.role,
        )

        refresh_token = TokenManager.create_refresh_token(
            data=user_data,
            expires_delta=timedelta(days=self.refresh_token_expire_days),
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
        )

        # Сохраняем refresh токен
        user.refresh_token = refresh_token
        user.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.user_repository.update(user)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def validate_refresh_token(self, refresh_token: str) -> UserEntity:
        """
        Валидирует refresh токен.

        Args:
            refresh_token: Refresh токен

        Returns:
            UserEntity: Пользователь

        Raises:
            UnauthorizedError: Если токен невалиден
        """
        payload = TokenManager.decode_token(
            refresh_token,
            self.jwt_secret_key,
            self.jwt_algorithm,
        )

        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError(message="Неверный refresh токен")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(message="Неверный refresh токен")

        user = await self.user_repository.get_by_id(int(user_id))
        if not user or user.refresh_token != refresh_token:
            raise UnauthorizedError(message="Неверный refresh токен")

        return user

    async def revoke_refresh_token(self, user: UserEntity) -> None:
        """
        Отозвать refresh токен (выход).

        Args:
            user: Domain сущность пользователя
        """
        user.refresh_token = None
        await self.user_repository.update(user)

    async def login_or_create_telegram_user(self, telegram_user: TelegramUserDTO) -> UserEntity:
        """
        Вход или создание пользователя через Telegram.

        Args:
            telegram_user: DTO Telegram пользователя

        Returns:
            UserEntity: Пользователь
        """
        telegram_id = str(telegram_user.id)

        # Поиск по telegram_id
        user = await self.user_repository.get_by_telegram_id(telegram_id)

        if user:
            # Существующий пользователь
            await self._handle_successful_login(user)
            return user

        # Создание нового пользователя
        username = telegram_user.username or f"tg_user_{telegram_id}"

        # Проверяем уникальность username
        existing = await self.user_repository.get_by_username(username)
        if existing:
            username = f"tg_{telegram_id}_{int(_utcnow().timestamp())}"

        # Генерируем случайный пароль (никогда не используется)
        random_password = secrets.token_urlsafe(32)

        user = UserEntity(
            username=username,
            email=f"{telegram_id}@telegram.local",
            hashed_password=PasswordHandler.hash(random_password),
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            telegram_id=telegram_id,
            telegram_username=telegram_user.username,
            is_telegram_user=True,
        )

        created = await self.user_repository.create(user)
        logger.info(f"Создан новый Telegram пользователь: {created.username} (ID: {telegram_id})")
        return created

    async def _handle_failed_login(self, user: UserEntity) -> None:
        """Обрабатывает неудачную попытку входа."""
        user.login_attempts += 1

        if user.login_attempts >= self.max_login_attempts:
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                minutes=self.lockout_duration_minutes
            )

        await self.user_repository.update(user)

    async def _handle_successful_login(self, user: UserEntity) -> None:
        """Обрабатывает успешный вход."""
        user.login_attempts = 0
        user.locked_until = None
        user.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.user_repository.update(user)
