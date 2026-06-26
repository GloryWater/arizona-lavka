"""Create or update a local demo admin user.

This script is intentionally guarded and is meant only for local/dev README
screenshots. It never prints passwords, tokens, or password hashes.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.database.connection import get_db_manager
from infrastructure.database.models import User
from services.auth_service import PasswordHandler


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


async def main() -> None:
    if os.environ.get("ALLOW_DEMO_ADMIN_CREATE") != "1":
        raise SystemExit("Refusing to run without ALLOW_DEMO_ADMIN_CREATE=1")

    email = _require_env("DEMO_ADMIN_EMAIL")
    password = _require_env("DEMO_ADMIN_PASSWORD")
    username = os.environ.get("DEMO_ADMIN_USERNAME", "admin_demo").strip()

    if len(password) < 8:
        raise SystemExit("DEMO_ADMIN_PASSWORD must be at least 8 characters")

    db = get_db_manager()
    await db.initialize()

    try:
        async with db.get_session() as session:
            result = await session.execute(
                select(User).where((User.email == email) | (User.username == username))
            )
            user = result.scalars().first()

            if user is None:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=PasswordHandler.hash(password),
                    role="admin",
                    is_email_verified=True,
                    login_attempts=0,
                    locked_until=None,
                )
                session.add(user)
                action = "created"
            else:
                user.username = username
                user.email = email
                user.hashed_password = PasswordHandler.hash(password)
                user.role = "admin"
                user.is_email_verified = True
                user.login_attempts = 0
                user.locked_until = None
                action = "updated"

            await session.flush()
            print(f"Demo admin {action}: id={user.id}, username={user.username}, role={user.role}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
