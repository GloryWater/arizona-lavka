"""
Email verification service for user registration.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from infrastructure.database.models import EmailVerificationToken, User


class EmailVerificationService:
    """
    Service for handling email verification workflow.

    Features:
    - Generate secure verification tokens
    - Send verification emails via Gmail SMTP
    - Validate and expire tokens
    - Rate limiting support
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=self.settings.GMAIL_USERNAME,
            MAIL_PASSWORD=self.settings.GMAIL_APP_PASSWORD,
            MAIL_FROM=self.settings.GMAIL_USERNAME,
            MAIL_PORT=465,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

    async def create_verification_token(self, user_id: int) -> str:
        """
        Generate and store verification token for user.

        Args:
            user_id: ID of the user

        Returns:
            str: Plain text token (to be sent via email)
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(
            hours=self.settings.EMAIL_VERIFICATION_EXPIRY_HOURS
        )

        # Delete any existing tokens for this user (only one active token at a time)
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )

        # Create new token
        db_token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.commit()

        return token

    async def send_verification_email(
        self,
        email: str,
        token: str,
        username: str,
    ) -> None:
        """
        Send verification email via Gmail SMTP.

        Args:
            email: Recipient email address
            token: Verification token (plain text)
            username: User's display name
        """
        verification_link = f"{self.settings.FRONTEND_URL}/verify?token={token}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🏪 Arizona Lavka</h1>
            </div>
            
            <div style="padding: 30px;">
                <h2 style="color: #2563eb; margin-top: 0;">Welcome, {username}!</h2>
                <p style="font-size: 16px; color: #555;">
                    Thank you for registering on Arizona Lavka Marketplace. 
                    Please verify your email to unlock all platform features.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" 
                       style="background-color: #2563eb; color: white; padding: 14px 32px; 
                              text-decoration: none; border-radius: 8px; display: inline-block; 
                              font-weight: bold; font-size: 16px;">
                        ✓ Verify Email Address
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; background: #f3f4f6; padding: 15px; border-radius: 6px;">
                    <strong>Link expires in {self.settings.EMAIL_VERIFICATION_EXPIRY_HOURS} hours</strong>
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    If you didn't create this account, please ignore this email. 
                    The verification link will expire and the account will be automatically deleted.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    © 2026 Arizona Lavka Marketplace. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

        message = MessageSchema(
            subject="🏪 Verify Your Email - Arizona Lavka Marketplace",
            recipients=[email],
            html=html_body,
            subtype="html",
        )

        fm = FastMail(self.mail_config)
        await fm.send_message(message)

    async def verify_token(self, token: str) -> Optional[EmailVerificationToken]:
        """
        Validate verification token and return if valid.

        Args:
            token: Plain text verification token

        Returns:
            EmailVerificationToken if valid, None otherwise
        """
        token_hash = self._hash_token(token)

        result = await self.db.execute(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token_hash == token_hash)
            .where(EmailVerificationToken.expires_at > datetime.utcnow())
            .options(EmailVerificationToken.user.joinedload())
        )

        return result.scalar_one_or_none()

    async def delete_token(self, token: EmailVerificationToken) -> None:
        """
        Delete used verification token.

        Args:
            token: Token to delete
        """
        await self.db.delete(token)
        await self.db.commit()

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash token for secure storage.

        Args:
            token: Plain text token

        Returns:
            str: SHA-256 hash of token
        """
        return hashlib.sha256(token.encode()).hexdigest()
