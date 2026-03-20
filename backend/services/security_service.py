"""
Сервис безопасности - Email верификация, шифрование, защита от спама.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from infrastructure.database.connection import (
    BlockedIP,
    DeviceFingerprint,
    EmailVerificationToken,
    EncryptedUserDatum,
    LoginAttempt,
    PasswordResetToken,
    SecurityAuditLog,
    User,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Email Verification Service
# =============================================================================


class EmailVerificationService:
    """Сервис верификации email."""

    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_TOKEN_EXPIRY_HOURS = 24
    MAX_VERIFICATION_ATTEMPTS = 3
    CODE_COOLDOWN_MINUTES = 5

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    def _generate_verification_code(self) -> str:
        """Генерирует безопасный 6-значный код."""
        return "".join(
            [str(secrets.randbelow(10)) for _ in range(self.VERIFICATION_CODE_LENGTH)]
        )

    def _generate_verification_token(self) -> str:
        """Генерирует безопасный токен верификации."""
        return secrets.token_urlsafe(32)

    async def create_verification_token(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Создаёт токен и код верификации email.

        Returns:
            Tuple[str, str]: (token, code)
        """
        # Проверяем существующие токены
        await self.cleanup_expired_tokens(user_id)

        # Генерируем токен и код
        token = self._generate_verification_token()
        code = self._generate_verification_code()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            hours=self.VERIFICATION_TOKEN_EXPIRY_HOURS
        )

        # Создаём запись в БД
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            code=code,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.session.add(verification_token)
        await self.session.flush()

        logger.info(f"Создан токен верификации для пользователя {user_id}")
        return token, code

    async def verify_by_code(
        self,
        user_id: int,
        code: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Проверяет код верификации.

        Args:
            user_id: ID пользователя
            code: Код верификации
            ip_address: IP адрес для аудита

        Returns:
            bool: True если код верный
        """
        # Находим активный токен с этим кодом
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.code == code,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at
            > datetime.now(timezone.utc).replace(tzinfo=None),
        )

        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            logger.warning(f"Неверный код верификации для пользователя {user_id}")
            return False

        # Помечаем как использованный
        token.is_used = True
        await self.session.flush()

        # Обновляем статус пользователя
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user:
            user.is_email_verified = True
            user.email_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)

        logger.info(f"Email пользователя {user_id} успешно верифицирован")

        # Логируем событие безопасности
        await self._log_security_event(
            event_type="email_verified",
            user_id=user_id,
            ip_address=ip_address,
            event_data={"code_length": len(code)},
        )

        return True

    async def verify_by_token(self, token: str) -> Optional[User]:
        """
        Проверяет токен верификации.

        Args:
            token: Токен верификации

        Returns:
            User или None
        """
        # Находим активный токен
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at
            > datetime.now(timezone.utc).replace(tzinfo=None),
        )

        result = await self.session.execute(stmt)
        verification_token = result.scalar_one_or_none()

        if not verification_token:
            logger.warning("Неверный или истёкший токен верификации")
            return None

        # Получаем пользователя
        user_stmt = select(User).where(User.id == verification_token.user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        # Помечаем токен как использованный
        verification_token.is_used = True

        # Обновляем статус пользователя
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)

        logger.info(f"Email пользователя {user.id} успешно верифицирован по токену")

        # Логируем событие
        await self._log_security_event(
            event_type="email_verified_token",
            user_id=user.id,
            ip_address=verification_token.ip_address,
            event_data={"user_agent": verification_token.user_agent},
        )

        return user

    async def cleanup_expired_tokens(self, user_id: Optional[int] = None) -> int:
        """
        Удаляет истёкшие токены.

        Args:
            user_id: ID пользователя (опционально)

        Returns:
            int: Количество удалённых токенов
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = delete(EmailVerificationToken).where(
            EmailVerificationToken.expires_at < now
        )

        if user_id:
            stmt = stmt.where(EmailVerificationToken.user_id == user_id)

        result = await self.session.execute(stmt)
        await self.session.flush()

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Удалено {deleted_count} истёкших токенов верификации")

        return deleted_count

    async def resend_verification(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Повторная отправка кода верификации.

        Проверяет cooldown период.
        """
        # Проверяем последний отправленный код
        stmt = (
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.is_used == False,
                EmailVerificationToken.expires_at
                > datetime.now(timezone.utc).replace(tzinfo=None),
            )
            .order_by(EmailVerificationToken.created_at.desc())
        )

        result = await self.session.execute(stmt)
        last_token = result.scalar_one_or_none()

        if last_token:
            cooldown_until = last_token.created_at + timedelta(
                minutes=self.CODE_COOLDOWN_MINUTES
            )
            if datetime.now(timezone.utc).replace(tzinfo=None) < cooldown_until:
                logger.warning(
                    f"Попытка повторной отправки кода в cooldown период для {user_id}"
                )
                raise ValueError(
                    f"Повторная отправка доступна через "
                    f"{int((cooldown_until - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 60)} мин"
                )

        # Создаём новый токен
        return await self.create_verification_token(user_id, ip_address, user_agent)

    async def _log_security_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        risk_score: Optional[int] = None,
    ):
        """Логирует событие безопасности."""
        audit_log = SecurityAuditLog(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            event_data=event_data,
            risk_score=risk_score,
        )
        self.session.add(audit_log)


# =============================================================================
# Encryption Service
# =============================================================================


class EncryptionService:
    """
    Сервис шифрования чувствительных данных.

    Использует AES-256-GCM для шифрования.
    """

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self._encryption_key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        """
        Получает ключ шифрования.

        В production используйте переменную окружения ENCRYPTION_KEY.
        """
        key = os.environ.get("ENCRYPTION_KEY")

        if not key:
            # Для разработки используем ключ из JWT_SECRET_KEY
            jwt_secret = self.settings.JWT_SECRET_KEY.encode("utf-8")
            # Derive key using SHA-256
            key = hashlib.sha256(jwt_secret).digest()
            logger.warning(
                "Используется derived ключ шифрования. Установите ENCRYPTION_KEY для production!"
            )
        else:
            # Декодируем из base64 или используем как есть
            import base64

            try:
                key = base64.b64decode(key)
            except Exception:
                key = hashlib.sha256(key.encode("utf-8")).digest()

        if len(key) != 32:
            key = hashlib.sha256(key).digest()

        return key

    def encrypt(self, plaintext: str) -> Tuple[str, str]:
        """
        Шифрует строку используя AES-256-GCM.

        Returns:
            Tuple[str, str]: (ciphertext_b64, nonce_b64)
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        # Генерируем случайный nonce (12 bytes для GCM)
        nonce = os.urandom(12)

        # Создаём AESGCM cipher
        aesgcm = AESGCM(self._encryption_key)

        # Шифруем
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Кодируем в base64 для хранения
        import base64

        ciphertext_b64 = base64.b64encode(ciphertext).decode("utf-8")
        nonce_b64 = base64.b64encode(nonce).decode("utf-8")

        return ciphertext_b64, nonce_b64

    def decrypt(self, ciphertext_b64: str, nonce_b64: str) -> str:
        """
        Расшифровывает строку.

        Args:
            ciphertext_b64: Зашифрованные данные (base64)
            nonce_b64: Nonce (base64)

        Returns:
            str: Расшифрованная строка
        """
        import base64

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        # Декодируем из base64
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)

        # Расшифровываем
        aesgcm = AESGCM(self._encryption_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode("utf-8")

    async def store_encrypted_data(
        self,
        user_id: int,
        data_key: str,
        plaintext: str,
    ) -> EncryptedUserDatum:
        """
        Сохраняет зашифрованные данные пользователя.

        Args:
            user_id: ID пользователя
            data_key: Ключ данных (например, "phone", "api_key")
            plaintext: Данные для шифрования

        Returns:
            EncryptedUserDatum: Запись в БД
        """
        ciphertext, nonce = self.encrypt(plaintext)

        # Проверяем существующую запись
        stmt = select(EncryptedUserDatum).where(
            EncryptedUserDatum.user_id == user_id,
            EncryptedUserDatum.data_key == data_key,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.encrypted_value = ciphertext
            existing.nonce = nonce
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.session.flush()
            return existing

        # Создаём новую запись
        encrypted_data = EncryptedUserDatum(
            user_id=user_id,
            data_key=data_key,
            encrypted_value=ciphertext,
            nonce=nonce,
        )

        self.session.add(encrypted_data)
        await self.session.flush()

        logger.info(
            f"Сохранены зашифрованные данные для пользователя {user_id}, ключ: {data_key}"
        )
        return encrypted_data

    async def get_decrypted_data(
        self,
        user_id: int,
        data_key: str,
    ) -> Optional[str]:
        """
        Получает и расшифровывает данные.

        Args:
            user_id: ID пользователя
            data_key: Ключ данных

        Returns:
            str или None
        """
        stmt = select(EncryptedUserDatum).where(
            EncryptedUserDatum.user_id == user_id,
            EncryptedUserDatum.data_key == data_key,
        )

        result = await self.session.execute(stmt)
        encrypted_data = result.scalar_one_or_none()

        if not encrypted_data:
            return None

        try:
            return self.decrypt(encrypted_data.encrypted_value, encrypted_data.nonce)
        except Exception as e:
            logger.error(f"Ошибка расшифровки данных для {user_id}/{data_key}: {e}")
            return None


# =============================================================================
# Anti-Spam Service
# =============================================================================


class AntiSpamService:
    """
    Сервис защиты от спама и злоупотреблений.
    """

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

        # Лимиты
        self.REGISTRATION_LIMIT_PER_IP = 5  # Регистраций в час
        self.REGISTRATION_LIMIT_PER_FINGERPRINT = 3
        self.LOGIN_ATTEMPTS_PER_IP = 10  # Попыток входа в минуту
        self.BLOCK_DURATION_HOURS = 24

    async def check_registration_limit(
        self,
        ip_address: str,
        fingerprint: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет лимиты регистрации.

        Returns:
            Tuple[bool, Optional[str]]: (allowed, reason)
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        hour_ago = now - timedelta(hours=1)

        # Проверка по IP
        stmt = select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.username.is_(None),  # Только регистрации (без username)
            LoginAttempt.created_at > hour_ago,
        )
        result = await self.session.execute(stmt)
        ip_count = result.scalar() or 0

        if ip_count >= self.REGISTRATION_LIMIT_PER_IP:
            logger.warning(
                f"Превышен лимит регистраций для IP {ip_address}: {ip_count}"
            )
            await self._block_ip(ip_address, "Превышен лимит регистраций")
            return False, "Превышен лимит регистраций с этого IP"

        # Проверка по fingerprint
        if fingerprint:
            stmt = select(func.count(LoginAttempt.id)).where(
                LoginAttempt.fingerprint == fingerprint,
                LoginAttempt.username.is_(None),
                LoginAttempt.created_at > hour_ago,
            )
            result = await self.session.execute(stmt)
            fp_count = result.scalar() or 0

            if fp_count >= self.REGISTRATION_LIMIT_PER_FINGERPRINT:
                logger.warning(
                    f"Превышен лимит регистраций для fingerprint {fingerprint}"
                )
                return False, "Превышен лимит регистраций с этого устройства"

        return True, None

    async def log_registration_attempt(
        self,
        ip_address: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        fingerprint: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = False,
    ):
        """Логирует попытку регистрации."""
        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            email=email,
            fingerprint=fingerprint,
            user_agent=user_agent,
            success=success,
            failure_reason=None if success else "registration_attempt",
        )
        self.session.add(attempt)

    async def _block_ip(
        self,
        ip_address: str,
        reason: str,
        duration_hours: Optional[int] = None,
        is_permanent: bool = False,
    ):
        """Блокирует IP адрес."""
        blocked_until = None
        if duration_hours:
            blocked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                hours=duration_hours
            )

        # Проверяем существующую блокировку
        stmt = select(BlockedIP).where(BlockedIP.ip_address == ip_address)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.reason = reason
            existing.blocked_until = blocked_until
            existing.is_permanent = is_permanent
        else:
            blocked_ip = BlockedIP(
                ip_address=ip_address,
                reason=reason,
                blocked_until=blocked_until,
                is_permanent=is_permanent,
            )
            self.session.add(blocked_ip)

        await self.session.flush()
        logger.warning(f"Заблокирован IP {ip_address}: {reason}")

    async def is_ip_blocked(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет блокировку IP.

        Returns:
            Tuple[bool, Optional[str]]: (is_blocked, reason)
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = select(BlockedIP).where(
            BlockedIP.ip_address == ip_address,
            (BlockedIP.blocked_until.is_(None) | (BlockedIP.blocked_until > now)),
        )

        result = await self.session.execute(stmt)
        blocked_ip = result.scalar_one_or_none()

        if blocked_ip:
            if blocked_ip.is_permanent:
                return True, "IP заблокирован постоянно"
            elif blocked_ip.blocked_until:
                return True, f"IP заблокирован до {blocked_ip.blocked_until}"

        return False, None

    async def check_email_domain(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет email домен на Disposable Email.

        Returns:
            Tuple[bool, Optional[str]]: (allowed, reason)
        """
        domain = email.split("@")[-1].lower()

        # Список популярных disposable email доменов
        disposable_domains = {
            "tempmail.com",
            "throwaway.email",
            "guerrillamail.com",
            "mailinator.com",
            "temp-mail.org",
            "fakeinbox.com",
            "10minutemail.com",
            "trashmail.com",
            "getnada.com",
            "maildrop.cc",
            "sharklasers.com",
            "grr.la",
            "dispostable.com",
            "tempinbox.com",
            "emailondeck.com",
        }

        if domain in disposable_domains:
            logger.warning(f"Попытка регистрации с disposable email: {email}")
            return False, "Регистрация с временными email запрещена"

        # Проверка на популярные бесплатные домены (можно включить при необходимости)
        # free_domains = {'gmail.com', 'yahoo.com', 'outlook.com', ...}

        return True, None


# =============================================================================
# Device Fingerprinting Service
# =============================================================================


class DeviceFingerprintService:
    """Сервис fingerprinting устройств."""

    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    def generate_fingerprint(
        self,
        user_agent: str,
        ip_address: str,
        screen_resolution: Optional[str] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """
        Генерирует отпечаток устройства.

        Использует комбинацию параметров для создания уникального hash.
        """
        # Собираем данные для fingerprint
        fingerprint_data = f"{user_agent}|{ip_address}|{screen_resolution or ''}|{timezone or ''}|{language or ''}"

        # Создаём SHA-256 hash
        return hashlib.sha256(fingerprint_data.encode("utf-8")).hexdigest()[:64]

    async def track_device(
        self,
        fingerprint: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        is_trusted: bool = False,
    ) -> DeviceFingerprint:
        """
        Отслеживает устройство.

        Обновляет существующую запись или создаёт новую.
        """
        # Ищем существующую запись
        stmt = select(DeviceFingerprint).where(
            DeviceFingerprint.fingerprint == fingerprint,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующую
            existing.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if user_id:
                existing.user_id = user_id
            if ip_address:
                existing.ip_address = ip_address
            if user_agent:
                existing.user_agent = user_agent
            if device_info:
                existing.device_info = device_info
            if is_trusted:
                existing.is_trusted = is_trusted
            await self.session.flush()
            return existing

        # Создаём новую запись
        device_fp = DeviceFingerprint(
            fingerprint=fingerprint,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            is_trusted=is_trusted,
        )

        self.session.add(device_fp)
        await self.session.flush()

        return device_fp

    async def get_user_devices(
        self,
        user_id: int,
        trusted_only: bool = False,
    ) -> List[DeviceFingerprint]:
        """Получает устройства пользователя."""
        stmt = select(DeviceFingerprint).where(
            DeviceFingerprint.user_id == user_id,
        )

        if trusted_only:
            stmt = stmt.where(DeviceFingerprint.is_trusted == True)

        stmt = stmt.order_by(DeviceFingerprint.last_seen_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def trust_device(
        self,
        fingerprint: str,
        user_id: int,
    ) -> bool:
        """Помечает устройство как доверенное."""
        stmt = select(DeviceFingerprint).where(
            DeviceFingerprint.fingerprint == fingerprint,
            DeviceFingerprint.user_id == user_id,
        )

        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()

        if device:
            device.is_trusted = True
            await self.session.flush()
            return True

        return False

    async def detect_suspicious_device(
        self,
        fingerprint: str,
        user_id: int,
        ip_address: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Детектирует подозрительное устройство.

        Returns:
            Tuple[bool, Optional[str]]: (is_suspicious, reason)
        """
        # Проверяем историю устройства
        stmt = (
            select(DeviceFingerprint)
            .where(
                DeviceFingerprint.fingerprint == fingerprint,
            )
            .order_by(DeviceFingerprint.created_at.desc())
        )

        result = await self.session.execute(stmt)
        device = result.scalar_one_or_none()

        if not device:
            # Новое устройство - проверяем IP
            # Можно добавить дополнительную проверку
            return False, None

        # Проверяем смену IP
        if device.ip_address and device.ip_address != ip_address:
            # IP изменился - потенциально подозрительно
            logger.warning(
                f"Подозрительная активность: устройство {fingerprint[:16]}... "
                f"сменило IP с {device.ip_address} на {ip_address}"
            )
            return True, "IP адрес устройства изменился"

        return False, None
