"""
Secure Secrets Manager for Arizona Lavka Marketplace.

This module provides secure handling of sensitive data using environment variables,
Docker secrets, or encrypted files. It avoids hardcoding sensitive information
in configuration files or source code.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from dotenv import load_dotenv


class SecretsManager:
    """
    A secure secrets manager that handles sensitive data retrieval
    from various sources with fallback mechanisms.
    """

    def __init__(self, secrets_dir: str = "secrets"):
        """
        Initialize the secrets manager.

        Args:
            secrets_dir: Directory where encrypted secrets are stored
        """
        # Load environment variables from .env file
        load_dotenv()

        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(exist_ok=True)

        # Generate encryption key from environment or create a new one
        encryption_key = os.getenv("SECRETS_ENCRYPTION_KEY")
        if not encryption_key:
            # In production, this should come from a secure source
            print(
                "WARNING: Using temporary encryption key. Set SECRETS_ENCRYPTION_KEY in production!"
            )
            encryption_key = Fernet.generate_key().decode()

        self.cipher_suite = Fernet(encryption_key.encode())

    def get_secret(
        self, secret_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Retrieve a secret value with the following priority:
        1. Docker secret file (if *_FILE environment variable exists)
        2. Environment variable
        3. Encrypted file in secrets directory
        4. Default value

        Args:
            secret_name: Name of the secret to retrieve
            default: Default value if secret is not found

        Returns:
            Secret value or default
        """
        # 1. Check for Docker secret file
        secret_file_var = f"{secret_name.upper()}_FILE"
        secret_file_path = os.getenv(secret_file_var)
        if secret_file_path:
            try:
                with open(secret_file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except FileNotFoundError:
                print(f"Secret file {secret_file_path} not found")

        # 2. Check environment variable
        env_value = os.getenv(secret_name.upper())
        if env_value:
            return env_value

        # 3. Check encrypted file in secrets directory
        encrypted_file = self.secrets_dir / f"{secret_name}.enc"
        if encrypted_file.exists():
            try:
                with open(encrypted_file, "rb") as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                    return decrypted_data.decode("utf-8")
            except Exception as e:
                print(f"Failed to decrypt secret {secret_name}: {e}")

        # 4. Return default value
        return default

    def store_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret securely in encrypted form.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret to store

        Returns:
            True if successful, False otherwise
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(secret_value.encode("utf-8"))
            encrypted_file = self.secrets_dir / f"{secret_name}.enc"

            with open(encrypted_file, "wb") as f:
                f.write(encrypted_data)

            # Also set as environment variable for current session
            os.environ[secret_name.upper()] = secret_value

            return True
        except Exception as e:
            print(f"Failed to store secret {secret_name}: {e}")
            return False

    def validate_required_secrets(self, required_secrets: list) -> Dict[str, bool]:
        """
        Validate that all required secrets are available.

        Args:
            required_secrets: List of required secret names

        Returns:
            Dictionary mapping secret names to their availability status
        """
        results = {}
        for secret in required_secrets:
            value = self.get_secret(secret)
            results[secret] = value is not None and value != ""

        return results


# Global instance for easy access
_secrets_manager = None


def get_secrets_manager() -> SecretsManager:
    """
    Get the global secrets manager instance.

    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret value.

    Args:
        secret_name: Name of the secret to retrieve
        default: Default value if secret is not found

    Returns:
        Secret value or default
    """
    return get_secrets_manager().get_secret(secret_name, default)


def store_secret(secret_name: str, secret_value: str) -> bool:
    """
    Convenience function to store a secret value.

    Args:
        secret_name: Name of the secret
        secret_value: Value of the secret to store

    Returns:
        True if successful, False otherwise
    """
    return get_secrets_manager().store_secret(secret_name, secret_value)


def validate_required_secrets(required_secrets: list) -> Dict[str, bool]:
    """
    Convenience function to validate required secrets.

    Args:
        required_secrets: List of required secret names

    Returns:
        Dictionary mapping secret names to their availability status
    """
    return get_secrets_manager().validate_required_secrets(required_secrets)


# Example usage and initialization
if __name__ == "__main__":
    # Example of how to use the secrets manager
    sm = get_secrets_manager()

    # Store some example secrets
    sm.store_secret("db_password", "secure_db_password_123")
    sm.store_secret("jwt_secret", "super_secret_jwt_key_456")

    # Retrieve secrets
    db_password = sm.get_secret("db_password")
    jwt_secret = sm.get_secret("jwt_secret")

    print(f"DB Password retrieved: {'Yes' if db_password else 'No'}")
    print(f"JWT Secret retrieved: {'Yes' if jwt_secret else 'No'}")
