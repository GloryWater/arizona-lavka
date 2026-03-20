"""
Cloudflare Turnstile verification service.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import httpx

from config import get_settings
from exceptions import TurnstileVerificationError


class TurnstileService:
    """
    Service for verifying Cloudflare Turnstile tokens.

    Cloudflare Turnstile is a privacy-friendly CAPTCHA alternative
    that verifies users in the background without interaction in 99% of cases.
    """

    TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    def __init__(self):
        self.settings = get_settings()

    async def verify_token(self, token: str, remote_ip: str) -> bool:
        """
        Verify Cloudflare Turnstile token.

        Args:
            token: Turnstile token from frontend
            remote_ip: Real user IP address

        Returns:
            bool: True if verification successful

        Raises:
            TurnstileVerificationError: If verification fails
        """
        if not self.settings.CLOUDFLARE_TURNSTILE_SECRET_KEY:
            # Skip verification in development if key not configured
            return True

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Cloudflare требует form-urlencoded
                response = await client.post(
                    self.TURNSTILE_VERIFY_URL,
                    data={
                        "secret": self.settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
                        "response": token,
                        "remoteip": remote_ip,
                    },
                )
                # Логируем для отладки
                import logging

                logger = logging.getLogger(__name__)
                logger.info(f"Turnstile API status: {response.status_code}")
                logger.info(f"{token}")
                logger.info(f"{self.settings.CLOUDFLARE_TURNSTILE_SECRET_KEY}")
                logger.info(f"{remote_ip}")
                logger.info(f"Turnstile API response: {response.text}")
                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    error_codes = result.get("error-codes", ["unknown_error"])
                    raise TurnstileVerificationError(
                        detail="Turnstile verification failed",
                        error_codes=error_codes,
                    )

                return True

            except httpx.TimeoutException:
                raise TurnstileVerificationError(
                    detail="Captcha service temporarily unavailable",
                    error_codes=["timeout"],
                )
            except httpx.HTTPError as e:
                raise TurnstileVerificationError(
                    detail="Captcha service error",
                    error_codes=[str(e)],
                )
