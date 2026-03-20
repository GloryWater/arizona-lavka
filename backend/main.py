"""
Arizona Lavka Marketplace - Main Application Entry Point.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from config import Settings, get_settings

# =============================================================================
# Logging Configuration
# =============================================================================

# Logs directory is created by Docker in production
# For local development, create it only if needed
LOGS_DIR = Path(__file__).parent / "logs"
try:
    LOGS_DIR.mkdir(exist_ok=True)
except (PermissionError, OSError):
    # If we can't create logs directory, use temp
    import tempfile

    LOGS_DIR = Path(tempfile.gettempdir()) / "arizonalavka_logs"
    LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# =============================================================================
# Application Lifespan
# =============================================================================

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def scheduled_cleanup_job():
    """Daily cleanup job for unverified users."""
    try:
        from infrastructure.database.connection import get_db_session
        from services.cleanup_service import CleanupService

        async for db in get_db_session():
            try:
                cleanup_service = CleanupService(db)
                deleted = await cleanup_service.cleanup_unverified_users()
                if deleted > 0:
                    logger.info(f"[Cleanup] Deleted {deleted} unverified users")
            except Exception as e:
                logger.error(f"[Cleanup] Error during cleanup: {e}")
            finally:
                await db.close()
                break
    except Exception as e:
        logger.error(f"[Cleanup] Scheduler job failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    global scheduler

    settings = get_settings()

    # Инициализация базы данных
    from infrastructure.database.connection import get_db_manager

    db_manager = get_db_manager()

    try:
        await db_manager.initialize()
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise

    app.state.db_manager = db_manager
    logger.info(
        f"База данных инициализирована | CORS: {settings.cors_origins_parsed} | Rate Limit: {settings.RATE_LIMIT_PER_MINUTE}/мин"
    )

    # Инициализация Redis
    from infrastructure.cache.redis_connection import get_redis_manager
    from infrastructure.cache.application_cache import get_application_cache

    redis_manager = get_redis_manager()

    try:
        await redis_manager.initialize()
    except Exception as e:
        logger.error(f"Ошибка инициализации Redis: {e}")
        # Не прерываем запуск при проблемах с Redis, используем fallback
        logger.warning("Продолжаем запуск без Redis...")
    else:
        app.state.redis_manager = redis_manager
        logger.info("Redis инициализирован для кэширования и сессий")

    # Инициализация прикладного кэша
    try:
        from infrastructure.cache.application_cache import get_application_cache
        application_cache = get_application_cache()
        await application_cache.initialize()
        app.state.application_cache = application_cache
        logger.info("Прикладной кэш инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации прикладного кэша: {e}")

    # Инициализация метрик Prometheus
    from metrics.prometheus import app_workers, set_app_info

    set_app_info(
        version=settings.APP_VERSION,
        environment="production" if settings.PRODUCTION else "development",
    )
    app_workers.set(1)  # Для uvicorn без workers
    logger.info("Prometheus metrics initialized")

    # Initialize and start APScheduler for cleanup jobs
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_cleanup_job,
        CronTrigger(hour=3, minute=0, timezone="UTC"),  # Daily at 03:00 UTC
        id="cleanup_unverified_users",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started - Daily cleanup job scheduled at 03:00 UTC")

    yield

    # Завершение работы
    logger.info("Остановка приложения...")

    # Shutdown scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("APScheduler stopped")

    if db_manager:
        await db_manager.close()

    # Close Redis connection
    if hasattr(app.state, "redis_manager") and app.state.redis_manager:
        await app.state.redis_manager.close()
        logger.info("Redis connection closed")

    # Close application cache
    if hasattr(app.state, "application_cache"):
        logger.info("Application cache closed")

    logger.info("Приложение остановлено")


# =============================================================================
# Application Initialization
# =============================================================================

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Arizona Lavka Marketplace API v3.0

BFF (Backend-For-Frontend) для marketplace Arizona RP (GTA 5 Online).
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# =============================================================================
# Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_parsed,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register middleware
from interfaces.http.middleware import (
    create_logging_middleware,
    create_maintenance_middleware,
    create_rate_limit_middleware,
)

# Security middleware
from interfaces.http.middleware.security_middleware import create_security_middleware

create_security_middleware(app)

create_logging_middleware(app)
create_maintenance_middleware(app)
create_rate_limit_middleware(app)

# Prometheus metrics middleware
from metrics.middleware import create_prometheus_middleware

create_prometheus_middleware(app)

# =============================================================================
# Exception Handlers
# =============================================================================

from error_handler import register_exception_handlers

register_exception_handlers(app)

# =============================================================================
# Health Check Endpoints
# =============================================================================


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from infrastructure.database.connection import get_db_manager

    health_status = {
        "status": "healthy",
        "service": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "checks": {
            "database": "unknown",
            "rate_limiter": "unknown",
        },
    }

    # Проверка БД
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            await session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    return {
        "status": "ok",
        "service": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
    }


# =============================================================================
# Router Registration
# =============================================================================

from metrics.router import router as prometheus_router
from routes import (
    admin_metrics_router,
    admin_router,
    auth_router,
    config_router,
    health_router,
    marketplace_router,
    metrics_router,
    telegram_auth_router,
    user_management_router,
    user_router,
)

app.include_router(health_router, tags=["🏥 Health Checks"])
app.include_router(prometheus_router, tags=["📊 Prometheus Metrics"])
app.include_router(auth_router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(config_router, prefix="/api/config", tags=["⚙️ Config Generator"])
app.include_router(
    marketplace_router, prefix="/api/marketplace", tags=["🏪 Marketplace"]
)
app.include_router(user_router, prefix="/api/user", tags=["👤 User"])
app.include_router(telegram_auth_router, tags=["🔐 Telegram Auth"])
app.include_router(
    user_management_router, prefix="/api/users", tags=["👥 User Management"]
)
app.include_router(admin_router, prefix="/api/v1/admin", tags=["🛡️ Admin Panel"])
app.include_router(
    admin_metrics_router, prefix="/api/v1/admin/metrics", tags=["🛡️ Admin Metrics"]
)
app.include_router(metrics_router, prefix="/api/metrics", tags=["📊 Metrics"])


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True,
    )
