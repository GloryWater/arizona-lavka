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
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from config import get_settings, Settings

# =============================================================================
# Logging Configuration
# =============================================================================

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    settings = get_settings()

    logger.info("=" * 60)
    logger.info(f"Запуск {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Database: PostgreSQL ({settings.POSTGRES_HOST}:{settings.POSTGRES_PORT})")
    logger.info("=" * 60)

    # Инициализация базы данных
    from infrastructure.database.connection import get_db_manager
    db_manager = get_db_manager()

    try:
        await db_manager.initialize()
        logger.info("База данных успешно инициализирована ✓")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise

    app.state.db_manager = db_manager
    logger.info(f"CORS Origins: {settings.cors_origins_parsed}")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE} запросов/мин")

    yield

    # Завершение работы
    logger.info("Остановка приложения...")
    if db_manager:
        await db_manager.close()
        logger.info("Подключение к базе данных закрыто ✓")
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

create_logging_middleware(app)
create_maintenance_middleware(app)
create_rate_limit_middleware(app)

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

from routes import (
    auth_router,
    config_router,
    marketplace_router,
    user_router,
    telegram_auth_router,
    admin_router,
)

app.include_router(auth_router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(config_router, prefix="/api/config", tags=["⚙️ Config Generator"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["🏪 Marketplace"])
app.include_router(user_router, prefix="/api/user", tags=["👤 User"])
app.include_router(telegram_auth_router, tags=["🔐 Telegram Auth"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["🛡️ Admin Panel"])


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
