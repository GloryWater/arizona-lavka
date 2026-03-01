"""
Роуты для аутентификации.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import User
from dependencies import get_db_session, get_db_session_no_commit, get_current_user_required
from models import UserRegister, UserLogin, TokenResponse, UserResponse
from services.auth_service import AuthService
from services.audit_log_service import AuditLogService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_auth_service(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AuthService:
    """Создаёт экземпляр AuthService."""
    from config import get_settings
    return AuthService(session, get_settings())


def get_audit_service(
    session: AsyncSession = Depends(get_db_session_no_commit)
) -> AuditLogService:
    """Создаёт экземпляр AuditLogService."""
    return AuditLogService(session)


@router.post("/register", response_model=TokenResponse)
async def register(
    data: UserRegister,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """Регистрация нового пользователя."""
    from sqlalchemy import select

    # Проверка уникальности username
    result = await auth_service.session.execute(
        select(User).where(User.username == data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    # Проверка уникальности email
    result = await auth_service.session.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    # Валидация email
    if len(data.email) > 255:
        raise HTTPException(status_code=400, detail="Email должен быть не более 255 символов")

    # Создание пользователя
    user = await auth_service.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    # Логирование события регистрации
    ip_address = request.client.host if request.client else None
    await audit_service.log_user_registered(
        user_id=user.id,
        username=user.username,
        email=user.email,
        ip_address=ip_address,
    )

    logger.info(f"Зарегистрирован новый пользователь: {user.username} (ID: {user.id})")

    # Коммит транзакции
    await auth_service.session.commit()

    # Генерация токенов
    tokens = await auth_service.generate_token_pair(user)

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """Вход пользователя."""
    user = await auth_service.authenticate_user(data.username_or_email, data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Логирование события входа
    ip_address = request.client.host if request.client else None
    await audit_service.log_user_logged_in(
        user_id=user.id,
        username=user.username,
        ip_address=ip_address,
    )

    # Генерация токенов (асинхронная версия с атомарным сохранением refresh_token)
    tokens = await auth_service.generate_token_pair(user)

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: dict,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Обновление access токена."""
    refresh_token_str = data.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="Refresh token required")

    user = await auth_service.validate_refresh_token(refresh_token_str)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный refresh токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерация новой пары токенов (асинхронная версия с атомарным сохранением)
    tokens = await auth_service.generate_token_pair(user)

    return tokens


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user_required),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Выход пользователя."""
    await auth_service.revoke_refresh_token(current_user)
    return {"message": "Успешный выход"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user_required),
):
    """Получение информации о текущем пользователе."""
    return current_user
