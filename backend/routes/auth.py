"""
Роуты для аутентификации с усиленной безопасностью.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    get_current_user_required,
    get_db_session,
    get_db_session_no_commit,
)
from exceptions import TurnstileVerificationError
from infrastructure.database.models import User
from models import (
    EmailVerificationRequest,
    EmailVerificationTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserRegisterResponse,
    UserResponse,
)
from services.audit_log_service import AuditLogService
from services.auth_service import AuthService
from services.security_service import (
    AntiSpamService,
    DeviceFingerprintService,
    EmailVerificationService,
    SecurityAuditLog,
)
from services.turnstile_service import TurnstileService
from utils.email_validator import is_valid_email

logger = logging.getLogger(__name__)

router = APIRouter()


def get_auth_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> AuthService:
    """Создаёт экземпляр AuthService."""
    from config import get_settings

    return AuthService(session, get_settings())


def get_audit_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> AuditLogService:
    """Создаёт экземпляр AuditLogService."""
    return AuditLogService(session)


def get_email_verification_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> EmailVerificationService:
    """Создаёт экземпляр EmailVerificationService."""
    from config import get_settings

    return EmailVerificationService(session, get_settings())


def get_anti_spam_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> AntiSpamService:
    """Создаёт экземпляр AntiSpamService."""
    from config import get_settings

    return AntiSpamService(session, get_settings())


def get_fingerprint_service(
    session: AsyncSession = Depends(get_db_session_no_commit),
) -> DeviceFingerprintService:
    """Создаёт экземпляр DeviceFingerprintService."""
    from config import get_settings

    return DeviceFingerprintService(session, get_settings())


def _get_client_info(request: Request) -> tuple:
    """Получает информацию о клиенте."""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    fingerprint = request.headers.get("x-device-fingerprint")
    return ip_address, user_agent, fingerprint


async def _perform_turnstile_verification(data: UserRegister, ip_address: str):
    """Выполняет проверку Cloudflare Turnstile.

    Args:
        data: Данные регистрации пользователя
        ip_address: IP-адрес клиента

    Raises:
        HTTPException: Если проверка не пройдена
    """
    turnstile_service = TurnstileService()
    try:
        await turnstile_service.verify_token(
            token=data.turnstile_token,
            remote_ip=ip_address,
        )
    except TurnstileVerificationError as e:
        logger.warning(
            f"Turnstile верификация не пройдена: IP={ip_address}, "
            f"errors={e.extra.get('turnstile_error_codes', [])}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Bot protection failed: {e.detail}",
        )


async def _validate_registration_data(
    data: UserRegister,
    auth_service: AuthService,
    ip_address: str,
    fingerprint: str,
    user_agent: str,
    anti_spam_service: AntiSpamService,
):
    """Выполняет проверки безопасности и валидации данных регистрации.

    Args:
        data: Данные регистрации пользователя
        auth_service: Сервис аутентификации
        ip_address: IP-адрес клиента
        fingerprint: Отпечаток устройства
        user_agent: User agent клиента
        anti_spam_service: Сервис антиспама

    Raises:
        HTTPException: Если проверки не пройдены
    """
    # Проверка блокировки IP
    is_blocked, block_reason = await anti_spam_service.is_ip_blocked(ip_address)
    if is_blocked:
        logger.warning(f"Попытка регистрации с заблокированного IP: {ip_address}")
        raise HTTPException(status_code=403, detail=block_reason)

    # Проверка лимитов регистрации
    allowed, reason = await anti_spam_service.check_registration_limit(
        ip_address, fingerprint
    )
    if not allowed:
        logger.warning(
            f"Превышен лимит регистрации: IP={ip_address}, fingerprint={fingerprint[:16]}..."
        )
        raise HTTPException(status_code=429, detail=reason)

    # Проверка disposable email
    allowed, reason = await anti_spam_service.check_email_domain(data.email)
    if not allowed:
        logger.warning(f"Попытка регистрации с disposable email: {data.email}")
        raise HTTPException(status_code=400, detail=reason)

    # Валидация DNS (MX записи) - опционально
    if not await is_valid_email(data.email):
        logger.warning(f"Email не прошёл DNS проверку: {data.email}")
        raise HTTPException(status_code=400, detail="Невалидный email домен")

    # Проверка уникальности username
    result = await auth_service.session.execute(
        select(User).where(User.username == data.username)
    )
    if result.scalar_one_or_none():
        # Логгируем попытку
        await anti_spam_service.log_registration_attempt(
            ip_address=ip_address,
            username=data.username,
            email=data.email,
            fingerprint=fingerprint,
            user_agent=user_agent,
            success=False,
        )
        raise HTTPException(
            status_code=400, detail="Пользователь с таким именем уже существует"
        )

    # Проверка уникальности email
    result = await auth_service.session.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        await anti_spam_service.log_registration_attempt(
            ip_address=ip_address,
            email=data.email,
            fingerprint=fingerprint,
            user_agent=user_agent,
            success=False,
        )
        raise HTTPException(
            status_code=400, detail="Пользователь с таким email уже существует"
        )

    # Валидация email
    if len(data.email) > 255:
        raise HTTPException(
            status_code=400, detail="Email должен быть не более 255 символов"
        )


async def _track_user_device(
    fingerprint_service: DeviceFingerprintService,
    user: User,
    ip_address: str,
    user_agent: str,
    data: UserRegister,
    fingerprint: str,
):
    """Отслеживает устройство пользователя.

    Args:
        fingerprint_service: Сервис отпечатков устройств
        user: Объект пользователя
        ip_address: IP-адрес клиента
        user_agent: User agent клиента
        data: Данные регистрации пользователя
        fingerprint: Отпечаток устройства
    """
    device_info = {
        "screen_resolution": data.screen_resolution,
        "timezone": data.timezone,
        "language": data.language,
    }
    await fingerprint_service.track_device(
        fingerprint=fingerprint,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
        is_trusted=False,  # Новые устройства не доверяем
    )

    # Обновляем last_login_fingerprint у пользователя
    user.last_login_fingerprint = fingerprint
    user.last_login_ip = ip_address
    user.last_login_user_agent = user_agent


async def _log_registration_success(
    audit_service: AuditLogService,
    anti_spam_service: AntiSpamService,
    auth_service: AuthService,
    user: User,
    ip_address: str,
    user_agent: str,
    fingerprint: str,
):
    """Логирует успешную регистрацию пользователя.

    Args:
        audit_service: Сервис аудита
        anti_spam_service: Сервис антиспама
        auth_service: Сервис аутентификации
        user: Объект пользователя
        ip_address: IP-адрес клиента
        user_agent: User agent клиента
        fingerprint: Отпечаток устройства
    """
    # Логируем попытку регистрации
    await anti_spam_service.log_registration_attempt(
        ip_address=ip_address,
        username=user.username,
        email=user.email,
        fingerprint=fingerprint,
        user_agent=user_agent,
        success=True,
    )

    # Логируем регистрацию пользователя
    await audit_service.log_user_registered(
        user_id=user.id,
        username=user.username,
        email=user.email,
        ip_address=ip_address,
    )

    # Логируем событие безопасности
    security_log = SecurityAuditLog(
        event_type="user_registered",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        fingerprint=fingerprint,
        event_data={"email": user.email, "username": user.username},
        risk_score=0,
    )
    auth_service.session.add(security_log)


@router.post("/register", response_model=UserRegisterResponse)
async def register(
    data: UserRegister,
    request: Request,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditLogService = Depends(get_audit_service),
    email_service: EmailVerificationService = Depends(get_email_verification_service),
    anti_spam_service: AntiSpamService = Depends(get_anti_spam_service),
    fingerprint_service: DeviceFingerprintService = Depends(get_fingerprint_service),
):
    """
    Регистрация нового пользователя с проверками безопасности.

    - **Cloudflare Turnstile** верификация (защита от ботов)
    - Проверка на спам (лимиты по IP и fingerprint)
    - Проверка disposable email
    - Валидация DNS (MX записи)
    - Создание токена верификации email
    - Tracking устройства
    """
    # Получаем информацию о клиенте
    ip_address, user_agent, req_fingerprint = _get_client_info(request)

    # === ПРОВЕРКА TURNSTILE (Cloudflare Bot Protection) ===
    # Это первая проверка - блокирует ботов до любых операций с БД
    await _perform_turnstile_verification(data, ip_address)

    # Генерируем fingerprint если не передан
    fingerprint = req_fingerprint or fingerprint_service.generate_fingerprint(
        user_agent=user_agent,
        ip_address=ip_address,
        screen_resolution=data.screen_resolution,
        timezone=data.timezone,
        language=data.language,
    )

    # === ПРОВЕРКА БЕЗОПАСНОСТИ ===
    await _validate_registration_data(
        data, auth_service, ip_address, fingerprint, user_agent, anti_spam_service
    )

    # === СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ===
    user = await auth_service.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    # === TRACKING УСТРОЙСТВА ===
    await _track_user_device(
        fingerprint_service, user, ip_address, user_agent, data, fingerprint
    )

    # === СОЗДАНИЕ ТОКЕНА ВЕРИФИКАЦИИ ===
    token, code = await email_service.create_verification_token(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # === ОТПРАВКА EMAIL (Background) ===
    # В production здесь будет отправка email
    # background_tasks.add_task(send_verification_email, user.email, code, token)
    logger.info(f"Код верификации для {user.email}: {code} (токен: {token[:16]}...)")

    # === ЛОГИРОВАНИЕ ===
    await _log_registration_success(
        audit_service,
        anti_spam_service,
        auth_service,
        user,
        ip_address,
        user_agent,
        fingerprint,
    )

    logger.info(f"Зарегистрирован новый пользователь: {user.username} (ID: {user.id})")

    # Коммит транзакции
    await auth_service.session.commit()

    # Генерация токенов
    tokens = await auth_service.generate_token_pair(user)

    return UserRegisterResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user),
        requires_email_verification=True,
        message="Пользователь зарегистрирован. Пожалуйста, подтвердите email.",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditLogService = Depends(get_audit_service),
    anti_spam_service: AntiSpamService = Depends(get_anti_spam_service),
    fingerprint_service: DeviceFingerprintService = Depends(get_fingerprint_service),
):
    """
    Вход пользователя с проверками безопасности.

    - Проверка блокировки IP
    - Проверка лимитов входа
    - Детекция подозрительных устройств
    - Audit logging
    """
    try:
        ip_address, user_agent, req_fingerprint = _get_client_info(request)

        # Проверка блокировки IP
        is_blocked, block_reason = await anti_spam_service.is_ip_blocked(ip_address)
        if is_blocked:
            logger.warning(f"Попытка входа с заблокированного IP: {ip_address}")
            raise HTTPException(status_code=403, detail=block_reason)

        # Проверка лимитов попыток входа
        # (реализуется в AuthService через login_attempts у пользователя)

        user = await auth_service.authenticate_user(
            data.username_or_email, data.password
        )

        if not user:
            # Логируем неудачную попытку
            await auth_service.session.commit()  # Коммит для инкремента login_attempts
            logger.info(
                f"Failed login attempt for {data.username_or_email} from {ip_address}"
            )
            raise HTTPException(
                status_code=401,
                detail="Неверное имя пользователя или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # === DETECT SUSPICIOUS ACTIVITY ===
        fingerprint = req_fingerprint or fingerprint_service.generate_fingerprint(
            user_agent=user_agent,
            ip_address=ip_address,
        )

        try:
            is_suspicious, reason = await fingerprint_service.detect_suspicious_device(
                fingerprint=fingerprint,
                user_id=user.id,
                ip_address=ip_address,
            )

            if is_suspicious:
                logger.warning(
                    f"Подозрительный вход для пользователя {user.username}: {reason}"
                )
                # Логируем событие безопасности
                security_log = SecurityAuditLog(
                    event_type="suspicious_login",
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    fingerprint=fingerprint,
                    event_data={"reason": reason},
                    risk_score=75,
                    is_suspicious=True,
                )
                auth_service.session.add(security_log)
                # Не блокируем вход, но логируем
        except Exception as e:
            logger.error(
                f"Error detecting suspicious activity for user {user.id}: {str(e)}",
                exc_info=True,
            )

        # === TRACKING УСТРОЙСТВА ===
        try:
            await fingerprint_service.track_device(
                fingerprint=fingerprint,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_trusted=False,
            )
        except Exception as e:
            logger.error(
                f"Error tracking device for user {user.id}: {str(e)}", exc_info=True
            )

        # Обновляем информацию о последнем входе
        user.last_login_fingerprint = fingerprint
        user.last_login_ip = ip_address
        user.last_login_user_agent = user_agent
        # Для PostgreSQL используем naive datetime (без timezone)
        user.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # === ЛОГИРОВАНИЕ ===
        try:
            await audit_service.log_user_logged_in(
                user_id=user.id,
                username=user.username,
                ip_address=ip_address,
            )
        except Exception as e:
            logger.error(
                f"Error logging user login for {user.id}: {str(e)}", exc_info=True
            )

        # Логируем событие безопасности
        try:
            security_log = SecurityAuditLog(
                event_type="user_login",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                fingerprint=fingerprint,
                event_data={
                    "username": user.username,
                    "email_verified": user.is_email_verified,
                },
                risk_score=0 if user.is_email_verified else 25,
            )
            auth_service.session.add(security_log)
        except Exception as e:
            logger.error(
                f"Error creating security log for user {user.id}: {str(e)}",
                exc_info=True,
            )

        await auth_service.session.commit()

        # Генерация токенов
        tokens = await auth_service.generate_token_pair(user)

        logger.info(f"Successful login for user {user.username} from {ip_address}")
        return tokens
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during login",
        )


@router.post("/verify-email", response_model=dict)
async def verify_email(
    data: EmailVerificationRequest,
    current_user: User = Depends(get_current_user_required),
    email_service: EmailVerificationService = Depends(get_email_verification_service),
):
    """
    Подтверждение email кодом.

    Код отправляется на email при регистрации.
    """
    if current_user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email уже подтверждён")

    success = await email_service.verify_by_code(
        user_id=current_user.id,
        code=data.code,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Неверный или истёкший код верификации",
        )

    await email_service.session.commit()

    return {
        "message": "Email успешно подтверждён",
        "is_verified": True,
    }


@router.get("/verify-email/{token}")
async def verify_email_by_token(
    token: str,
    email_service: EmailVerificationService = Depends(get_email_verification_service),
):
    """
    Подтверждение email токеном из ссылки.

    Ссылка приходит на email.
    """
    user = await email_service.verify_by_token(token)

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Неверный или истёкший токен верификации",
        )

    await email_service.session.commit()

    return {
        "message": "Email успешно подтверждён",
        "user_id": user.id,
        "username": user.username,
    }


@router.post("/verify-email-token", response_model=dict)
async def verify_email_by_token_post(
    data: EmailVerificationTokenRequest,
    email_service: EmailVerificationService = Depends(get_email_verification_service),
):
    """
    Подтверждение email токеном из ссылки (POST версия для frontend).

    Ссылка приходит на email.
    """
    user = await email_service.verify_by_token(data.token)

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Неверный или истёкший токен верификации",
        )

    await email_service.session.commit()

    return {
        "message": "Email успешно подтверждён",
        "is_email_verified": True,
    }


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_user_required),
    email_service: EmailVerificationService = Depends(get_email_verification_service),
):
    """Повторная отправка кода верификации."""
    if current_user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email уже подтверждён")

    ip_address, user_agent, _ = _get_client_info(email_service.session)

    try:
        token, code = await email_service.resend_verification(
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # В production здесь будет отправка email
        logger.info(f"Новый код верификации для {current_user.email}: {code}")

        return {
            "message": "Код верификации отправлен повторно",
            "email": current_user.email,
        }

    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))


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

    tokens = await auth_service.generate_token_pair(user)

    return tokens


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user_required),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Выход пользователя."""
    await auth_service.revoke_refresh_token(current_user)

    # Логируем событие безопасности
    security_log = SecurityAuditLog(
        event_type="user_logout",
        user_id=current_user.id,
        ip_address=current_user.last_login_ip,
        event_data={"username": current_user.username},
    )
    auth_service.session.add(security_log)
    await auth_service.session.commit()

    return {"message": "Успешный выход"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user_required),
):
    """Получение информации о текущем пользователе."""
    return current_user
