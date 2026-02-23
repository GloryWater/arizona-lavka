"""
Роуты для аутентификации.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import User
from models import UserRegister, UserLogin, TokenResponse, UserResponse
from dependencies import get_db_session, get_current_user_required
from services.auth_service import AuthService

router = APIRouter()


def get_auth_service(
    session: AsyncSession = Depends(get_db_session)
) -> AuthService:
    """Создаёт экземпляр AuthService."""
    from config import get_settings
    return AuthService(session, get_settings())


@router.post("/register", response_model=TokenResponse)
async def register(
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Регистрация нового пользователя."""
    # Проверка уникальности username
    from sqlalchemy import select
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
    
    # Создание пользователя
    user = await auth_service.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    
    # Генерация токенов
    tokens = auth_service.create_token_pair(user)
    
    # Сохранение refresh токена
    await auth_service.update_refresh_token(user, tokens["refresh_token"])
    
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Вход пользователя."""
    user = await auth_service.authenticate_user(data.username_or_email, data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерация токенов
    tokens = auth_service.create_token_pair(user)
    
    # Сохранение refresh токена
    await auth_service.update_refresh_token(user, tokens["refresh_token"])
    
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: dict,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Обновление access токена."""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    user = await auth_service.validate_refresh_token(refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный refresh токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерация новой пары токенов
    tokens = auth_service.create_token_pair(user)
    
    # Обновление refresh токена
    await auth_service.update_refresh_token(user, tokens["refresh_token"])
    
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
