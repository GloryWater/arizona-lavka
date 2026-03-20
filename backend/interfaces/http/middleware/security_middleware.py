"""
Security middleware for protecting against XSS, CSRF, and SQL injection.
"""

import logging
import re
from typing import Callable, Set

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response

from config import get_settings

logger = logging.getLogger(__name__)


def create_security_middleware(app: FastAPI) -> None:
    """
    Регистрирует middleware для защиты от XSS, CSRF и SQL-инъекций.
    """
    settings = get_settings()

    @app.middleware("http")
    async def security_middleware(request: Request, call_next: Callable) -> Response:
        # Apply security headers if enabled
        if settings.SECURE_HEADERS_ENABLED:
            request.state.security_headers_applied = True

        # Check for potential SQL injection attempts
        if await _detect_sql_injection(request):
            logger.warning(
                f"SQL injection attempt detected from IP: {request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request blocked due to potential SQL injection attempt",
            )

        # Check for potential XSS attempts
        if await _detect_xss(request):
            logger.warning(f"XSS attempt detected from IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request blocked due to potential XSS attempt",
            )

        response = await call_next(request)

        # Add security headers to response
        if settings.SECURE_HEADERS_ENABLED:
            response.headers["Content-Security-Policy"] = (
                settings.CONTENT_SECURITY_POLICY
            )
            response.headers["X-Frame-Options"] = settings.X_FRAME_OPTIONS
            response.headers["X-Content-Type-Options"] = settings.X_CONTENT_TYPE_OPTIONS
            response.headers["Referrer-Policy"] = settings.REFERRER_POLICY
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


async def _detect_sql_injection(request: Request) -> bool:
    """
    Advanced detection of potential SQL injection attempts.
    """
    # Get request body if available
    try:
        body_bytes = await request.body()
        if body_bytes:
            body_str = body_bytes.decode("utf-8")
            if _has_sql_injection_patterns(body_str):
                return True
    except Exception:
        pass

    # Check query parameters
    for param, value in request.query_params.items():
        if isinstance(value, str) and _has_sql_injection_patterns(value):
            return True

    # Check path parameters
    for param, value in request.path_params.items():
        if isinstance(value, str) and _has_sql_injection_patterns(value):
            return True

    # Check headers for potential injection
    for header_name, header_value in request.headers.items():
        if isinstance(header_value, str) and _has_sql_injection_patterns(header_value):
            return True

    return False


def _has_sql_injection_patterns(input_str: str) -> bool:
    """
    Check if input contains potential SQL injection patterns.
    """
    if not input_str:
        return False

    # Convert to lowercase for case-insensitive matching
    lower_str = input_str.lower().strip()

    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT|MERGE|GRANT|REVOKE|TRUNCATE|DECLARE|OPEN|FETCH|INTO|FROM|WHERE)\b)",
        r"(\'\s*(?:OR|AND)\s*\'\s*=)",
        r"(;\s*(?:DROP|EXEC|CALL|PREPARE|INSERT|UPDATE|DELETE|CREATE|ALTER|GRANT|REVOKE|TRUNCATE|MERGE))",
        r"(\/\*.*?\*\/)",  # SQL comments
        r"(--\s+)",  # SQL line comment
        r"(\b(?:OR|AND)\s+[^\s=]+\s*=\s*[^\s=]+)",  # Basic OR/AND injection
        r"(\'\s*(?:OR|AND)\s+[^\s=]+\s*=\s*[^\s=]+)",  # Basic OR/AND injection
        r"(\'\s*(?:OR|AND)\s+1\s*=\s*1)",  # Classic 1=1 injection
        r"(\'\s*(?:OR|AND)\s+0\s*=\s*0)",  # Alternative 0=0 injection
        r"(\'\s*>\s*\'\s*<)",  # Comparison injection
        r"(NULLIF\s*\()",  # NULLIF function
        r"(WAITFOR\s+DELAY\s+)",  # Time-based injection
        r"(SLEEP\s*\()",  # Sleep function
        r"(BENCHMARK\s*\()",  # Benchmark function
        r"(PG_SLEEP\s*\()",  # PostgreSQL sleep
        r"(DBMS_LOCK\.SLEEP\s*\()",  # Oracle sleep
    ]

    for pattern in sql_patterns:
        if re.search(pattern, lower_str):
            return True

    return False


async def _detect_xss(request: Request) -> bool:
    """
    Advanced detection of potential XSS attempts.
    """
    # Get request body if available
    try:
        body_bytes = await request.body()
        if body_bytes:
            body_str = body_bytes.decode("utf-8")
            if _has_xss_patterns(body_str):
                return True
    except Exception:
        pass

    # Check query parameters
    for param, value in request.query_params.items():
        if isinstance(value, str) and _has_xss_patterns(value):
            return True

    # Check path parameters
    for param, value in request.path_params.items():
        if isinstance(value, str) and _has_xss_patterns(value):
            return True

    # Check headers for potential XSS
    for header_name, header_value in request.headers.items():
        if isinstance(header_value, str) and _has_xss_patterns(header_value):
            return True

    return False


def _has_xss_patterns(input_str: str) -> bool:
    """
    Check if input contains potential XSS patterns.
    """
    if not input_str:
        return False

    # Normalize the input string
    normalized_str = input_str.lower().strip()

    # Common XSS patterns
    xss_patterns = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"vbscript:",  # VBScript protocol
        r"data:text/html",  # Data URI HTML
        r"onload\s*=",  # Event handlers
        r"onerror\s*=",
        r"onmouseover\s*=",
        r"onfocus\s*=",
        r"onblur\s*=",
        r"onclick\s*=",
        r"ondblclick\s*=",
        r"onmousedown\s*=",
        r"onmouseup\s*=",
        r"onkeydown\s*=",
        r"onkeyup\s*=",
        r"<iframe[^>]*>",  # Frame tags
        r"<frame[^>]*>",
        r"<frameset[^>]*>",
        r"<embed[^>]*>",  # Embed tags
        r"<object[^>]*>",  # Object tags
        r"<svg[^>]*>",  # SVG tags
        r"<img[^>]*src\s*=['\"]javascript:",  # JS in img src
        r"<img[^>]*src\s*=['\"]vbscript:",  # VBScript in img src
        r"<link[^>]*href\s*=['\"]javascript:",  # JS in link href
        r"<meta[^>]*http-equiv\s*=['\"]refresh['\"][^>]*url\s*=",  # Refresh meta tag
        r"expression\s*\(",  # CSS expressions
        r"eval\s*\(",  # Eval function
        r"alert\s*\(",  # Alert function
        r"document\.cookie",  # Cookie access
        r"window\.location",  # Location manipulation
        r"document\.location",  # Location manipulation
        r"String\.fromCharCode",  # Character code manipulation
        r"unescape\s*\(",  # Unescape function
        r"decodeURIComponent\s*\(",  # Decode function
        r"innerHTML\s*=",  # InnerHTML manipulation
        r"outerHTML\s*=",  # OuterHTML manipulation
    ]

    for pattern in xss_patterns:
        if re.search(pattern, normalized_str, re.IGNORECASE | re.DOTALL):
            return True

    return False
