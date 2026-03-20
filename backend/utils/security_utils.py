"""
Enhanced security utilities for the application.
"""

import html
import re
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, validator

from config import get_settings


class InputSanitizer:
    """Utility class for sanitizing user inputs."""

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """
        Sanitize a string input by removing dangerous characters and limiting length.
        """
        if not input_str:
            return input_str

        # Strip leading/trailing whitespace
        sanitized = input_str.strip()

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # Escape HTML characters
        sanitized = html.escape(sanitized)

        # Remove potentially dangerous characters/sequences
        # This is a basic example - you might want to customize based on your needs
        sanitized = re.sub(r'[<>"\';]', "", sanitized)

        return sanitized

    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column names) to prevent SQL injection.
        Only allows alphanumeric characters and underscores.
        """
        if not identifier:
            return identifier

        # Only allow alphanumeric characters and underscores
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            raise ValueError("SQL identifier cannot start with a digit")

        return sanitized

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """
        Basic email format validation.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format.
        """
        if len(username) < 3 or len(username) > 50:
            return False

        # Only allow alphanumeric characters, underscores, and hyphens
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, username))


class SecurityValidator:
    """Utility class for security validations."""

    @staticmethod
    def is_safe_sql_query(query: str) -> bool:
        """
        Basic validation to check if a SQL query is potentially safe.
        """
        if not query:
            return True

        # Convert to lowercase for case-insensitive matching
        lower_query = query.lower().strip()

        # Check for dangerous SQL keywords
        dangerous_keywords = [
            "drop",
            "truncate",
            "delete",
            "insert",
            "update",
            "exec",
            "execute",
            "xp_",
            "sp_",
            "sysobjects",
            "syscolumns",
            "information_schema",
            "union",
            "having",
            "concat",
            "benchmark",
            "sleep",
            "waitfor delay",
        ]

        for keyword in dangerous_keywords:
            if keyword in lower_query:
                return False

        # Check for SQL comment patterns
        if "/*" in lower_query or "--" in lower_query:
            return False

        return True

    @staticmethod
    async def validate_csrf_token(request: Request, expected_token: str) -> bool:
        """
        Validate CSRF token from request.
        """
        # Check header first
        csrf_header = request.headers.get("X-CSRF-Token")
        if csrf_header and csrf_header == expected_token:
            return True

        # Check form data
        try:
            form_data = await request.form()
            form_dict = {}
            for field_name, field_value in form_data.multi_items():
                form_dict[field_name] = field_value

            if "csrf_token" in form_dict and form_dict["csrf_token"] == expected_token:
                return True
        except:
            pass

        # Check query params
        if request.query_params.get("csrf_token") == expected_token:
            return True

        return False

    @staticmethod
    def detect_malicious_payload(payload: str) -> Dict[str, Any]:
        """
        Detect potentially malicious content in payload.
        """
        results = {"is_malicious": False, "threat_types": [], "details": {}}

        if not payload:
            return results

        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            r"(\'\s*(OR|AND)\s*\'\s*=)",
            r"(;\s*(DROP|EXEC|CALL|PREPARE))",
            r"(\/\*.*\*\/)",  # SQL comments
            r"(--\s+)",  # SQL line comment
        ]

        for i, pattern in enumerate(sql_patterns):
            if re.search(pattern, payload, re.IGNORECASE):
                results["is_malicious"] = True
                results["threat_types"].append("SQL_INJECTION")
                results["details"][f"sql_pattern_{i}"] = bool(
                    re.search(pattern, payload, re.IGNORECASE)
                )

        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"<iframe[^>]*>",
            r"<embed[^>]*>",
            r"<object[^>]*>",
        ]

        for i, pattern in enumerate(xss_patterns):
            if re.search(pattern, payload, re.IGNORECASE):
                results["is_malicious"] = True
                if "XSS" not in results["threat_types"]:
                    results["threat_types"].append("XSS")
                results["details"][f"xss_pattern_{i}"] = bool(
                    re.search(pattern, payload, re.IGNORECASE)
                )

        # Check for command injection patterns
        cmd_patterns = [
            r"[;&|]",
            r"\$\(",
            r"`.*`",
            r"exec\b",
            r"system\b",
            r"shell_exec\b",
        ]

        for i, pattern in enumerate(cmd_patterns):
            if re.search(pattern, payload, re.IGNORECASE):
                results["is_malicious"] = True
                if "COMMAND_INJECTION" not in results["threat_types"]:
                    results["threat_types"].append("COMMAND_INJECTION")
                results["details"][f"cmd_pattern_{i}"] = bool(
                    re.search(pattern, payload, re.IGNORECASE)
                )

        return results


def require_csrf_protection(expected_token_field: str = "csrf_token"):
    """
    Decorator to enforce CSRF protection on route handlers.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs or args
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found",
                )

            # Get expected token from session or wherever it's stored
            # This is a simplified example - in practice, you'd retrieve the token from session
            expected_token = kwargs.get(expected_token_field)
            if not expected_token:
                # Try to get from session if available
                if hasattr(request.state, "session") and hasattr(
                    request.state.session, "csrf_token"
                ):
                    expected_token = request.state.session.csrf_token

            if not expected_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token not found"
                )

            # Validate the token
            if not SecurityValidator.validate_csrf_token(request, expected_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
