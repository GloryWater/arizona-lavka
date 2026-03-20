import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_engine_from_config,
    create_async_engine,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from infrastructure.database.connection import (  # Import all models
    AdminLog,
    BlockedIP,
    ConfigHistory,
    DeviceFingerprint,
    EmailVerificationToken,
    EncryptedUserDatum,
    GlobalSetting,
    LoginAttempt,
    PasswordResetToken,
    SecurityAuditLog,
    User,
)

# add your model's MetaData object here
# for 'autogenerate' support
from infrastructure.database.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (not used in production)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=False,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Build database URL from environment variables
    user = os.environ.get("POSTGRES_USER", config.get_main_option("sqlalchemy.user"))
    password = os.environ.get(
        "POSTGRES_PASSWORD", config.get_main_option("sqlalchemy.password")
    )
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    dbname = os.environ.get("POSTGRES_DB", "arizonalavka")

    # Construct URL
    if user and password:
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
    else:
        url = config.get_main_option("sqlalchemy.url")
        if not url:
            url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

    # Create async engine
    connectable: AsyncEngine = create_async_engine(
        url,
        poolclass=pool.NullPool,
        echo=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
