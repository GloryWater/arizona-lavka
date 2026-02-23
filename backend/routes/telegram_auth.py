"""
Роуты Telegram аутентификации.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import User
from dependencies import get_db_session, get_current_user_required
from models import TokenResponse, UserResponse, TelegramLoginRequest
from services.auth_service import AuthService
from services.telegram_auth_service import validate_telegram_init_data, parse_telegram_user

logger = logging.getLogger(__name__)

router = APIRouter()


def get_auth_service(
    session: AsyncSession = Depends(get_db_session)
) -> AuthService:
    """Создаёт экземпляр AuthService."""
    return AuthService(session, get_settings())


@router.post("/telegram/login", response_model=TokenResponse)
async def telegram_login(
    request: Request,
    data: TelegramLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Вход через Telegram initData.

    Принимает initData от Telegram WebApp, проверяет подпись,
    находит или создаёт пользователя, возвращает JWT токены.
    """
    settings = get_settings()

    # Проверяем наличие токена бота
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram интеграция не настроена"
        )

    # Валидация initData
    telegram_user = validate_telegram_init_data(
        data.init_data,
        settings.TELEGRAM_BOT_TOKEN
    )

    if not telegram_user:
        logger.warning("Невалидный initData от Telegram")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидные данные Telegram"
        )

    try:
        # Вход или создание пользователя
        user = await auth_service.login_or_create_telegram_user(telegram_user)

        # Генерация пары токенов
        tokens = await auth_service.generate_token_pair(user)

        logger.info(f"Telegram пользователь авторизован: {user.telegram_id}")

        return TokenResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка Telegram авторизации: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка авторизации"
        )


@router.get("/telegram/me", response_model=UserResponse)
async def get_telegram_user(
    current_user: User = Depends(get_current_user_required),
):
    """
    Получение информации о текущем пользователе Telegram.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_premium=current_user.is_premium,
        is_telegram_user=current_user.is_telegram_user,
        created_at=current_user.created_at,
    )
