#!/usr/bin/env python3
"""
Secure Secrets Generator for Arizona Lavka Marketplace

This script generates secure random values for all required secrets
and stores them in the appropriate files for the Docker Compose setup.
"""

import os
import secrets
import string
import argparse
from pathlib import Path


def generate_secure_password(length=32):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt_secret():
    """Generate a secure JWT secret key."""
    return secrets.token_urlsafe(64)


def generate_turnstile_keys():
    """Generate mock Cloudflare Turnstile keys (should be replaced with real ones)."""
    site_key = "1x00000000000000000000AA"
    secret_key = "0x0000000000000000000000000000000AA"
    return site_key, secret_key


def create_secrets_directory():
    """Create the secrets directory if it doesn't exist."""
    secrets_dir = Path("./secrets")
    secrets_dir.mkdir(exist_ok=True)
    return secrets_dir


def generate_and_save_secret(secret_name, generator_func, secrets_dir, force_overwrite=False):
    """Generate a secret and save it to a file."""
    secret_file = secrets_dir / f"{secret_name}.txt"

    # Check if secret already exists
    if secret_file.exists() and not force_overwrite:
        print(f"⚠️  Warning: {secret_file} already exists. Skipping generation.")
        return False

    # Generate and save the secret
    secret_value = generator_func()
    with open(secret_file, 'w', encoding='utf-8') as f:
        f.write(secret_value)

    status = "Updated" if secret_file.exists() else "Generated"
    print(f"✅ {status} {secret_name} to {secret_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate secure secrets for Arizona Lavka Marketplace')
    parser.add_argument('--force', action='store_true', help='Overwrite existing secrets')
    parser.add_argument('--legacy', action='store_true', help='Use legacy values from old-compose.yml')
    args = parser.parse_args()

    print("🔒 Generating secure secrets for Arizona Lavka Marketplace...")

    # Create secrets directory
    secrets_dir = create_secrets_directory()

    if args.legacy:
        print("🔧 Using legacy values from old-compose.yml...")
        # Define legacy secrets to generate
        secrets_to_generate = [
            ("db_user", lambda: "arizonalavka"),
            ("db_name", lambda: "arizonalavka"),
            ("db_password", lambda: "srGH8aQRVaFqM9XBxfd"),
            ("jwt_secret", lambda: "61b8d69611aa704f6fb0e19e9e2930aaa8cf98a4788712c6429549314bb39ff5"),
            ("turnstile_site_key", lambda: "0x4AAAAAACrUZmGD4_pjJq_a"),
            ("turnstile_secret_key", lambda: "0x4AAAAAACrUZuyg5ahuUkWhwFdDr4wko78"),
            ("gmail_username", lambda: "arz.lavka@gmail.com"),
            ("gmail_app_password", lambda: "nykgxzfthbhdqxhr"),
        ]
    else:
        # Define secrets to generate
        secrets_to_generate = [
            ("db_user", lambda: "arizonalavka"),
            ("db_name", lambda: "arizonalavka"),
            ("db_password", generate_secure_password),
            ("jwt_secret", generate_jwt_secret),
            ("turnstile_site_key", lambda: os.getenv("TURNSTILE_SITE_KEY", "1x00000000000000000000AA")),
            ("turnstile_secret_key", lambda: os.getenv("TURNSTILE_SECRET_KEY", "0x0000000000000000000000000000000AA")),
            ("gmail_username", lambda: os.getenv("GMAIL_USERNAME", "arz.lavka@gmail.com")),
            ("gmail_app_password", lambda: os.getenv("GMAIL_APP_PASSWORD", generate_secure_password(16))),
        ]

    generated_count = 0

    for secret_name, generator_func in secrets_to_generate:
        secret_file = secrets_dir / f"{secret_name}.txt"

        if secret_file.exists() and not args.force:
            print(f"⚠️  {secret_file} already exists. Use --force to overwrite.")
            continue

        # If forcing, show warning
        if secret_file.exists() and args.force:
            print(f"🔄 Overwriting existing {secret_name}...")

        # Generate and save the secret
        if generate_and_save_secret(secret_name, generator_func, secrets_dir, args.force):
            generated_count += 1

    print(f"\n🎉 Done! Generated {generated_count} secrets in {secrets_dir}/")
    print("\n📋 Next steps:")
    print("1. Review the generated secrets in the ./secrets/ directory")
    print("2. Update them with your actual values if needed")
    print("3. For production, use a proper secrets management solution")
    print("4. Run your application with: docker compose -f docker-compose.secure.yml up -d")


if __name__ == "__main__":
    main()