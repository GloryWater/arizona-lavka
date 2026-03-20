"""
Email validation utilities.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import asyncio
import re
from typing import Final

import dns.resolver

from config import get_settings

# Email regex pattern (RFC 5322 compliant)
EMAIL_REGEX: Final = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


async def is_valid_email(email: str) -> bool:
    """
    Comprehensive email validation.

    Performs three levels of validation:
    1. Format validation using regex
    2. Disposable domain check against blocklist
    3. MX record existence via DNS lookup

    Args:
        email: Email address to validate

    Returns:
        bool: True if email is valid, False otherwise
    """
    settings = get_settings()

    # 1. Format validation
    if not EMAIL_REGEX.match(email):
        return False

    # Normalize to lowercase
    email_lower = email.lower()
    domain = email_lower.split("@")[1]

    # 2. Disposable domain check
    if domain in settings.disposable_email_domains_parsed:
        return False

    # 3. MX record check (DNS lookup)
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5

        # Run DNS lookup in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: _resolve_mx(resolver, domain)
        )
        return True
    except Exception:
        # DNS lookup failed - email might be invalid
        return False


def _resolve_mx(resolver: dns.resolver.Resolver, domain: str) -> None:
    """
    Resolve MX records for domain.

    Args:
        resolver: DNS resolver instance
        domain: Domain to check

    Raises:
        Exception: If no MX records found
    """
    resolver.resolve(domain, "MX")
