"""
Health check endpoints for monitoring and Docker health checks.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from dependencies import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health Checks"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.

    Returns 200 OK if the service is running.
    Used by Docker health checks and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "arizonalavka-backend",
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe - checks if the application is running.

    Kubernetes: Used to determine when to restart a container.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """
    Readiness probe - checks if the application is ready to serve traffic.

    Kubernetes: Used to determine when to send traffic to a pod.
    Checks:
    - Database connectivity
    - Required configuration
    """
    settings = get_settings()

    checks = {
        "database": "unknown",
        "configuration": "unknown",
    }

    overall_status = "healthy"

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"disconnected: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Database health check failed: {e}")

    # Check configuration
    try:
        if settings.JWT_SECRET_KEY:
            checks["configuration"] = "valid"
        else:
            checks["configuration"] = "missing JWT_SECRET_KEY"
            overall_status = "degraded"
            logger.warning("JWT_SECRET_KEY not configured")
    except Exception as e:
        checks["configuration"] = f"invalid: {str(e)}"
        overall_status = "unhealthy"

    status_code = (
        status.HTTP_200_OK
        if overall_status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "arizonalavka-backend",
        "version": settings.APP_VERSION,
        "checks": checks,
    }, status_code


@router.get("/health/db", status_code=status.HTTP_200_OK)
async def database_health(db: AsyncSession = Depends(get_db_session)):
    """
    Database health check endpoint.

    Returns detailed database connection status.
    """
    try:
        result = await db.execute(text("SELECT version()"))
        db_version = result.scalar()

        return {
            "status": "connected",
            "database": "PostgreSQL",
            "version": db_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, status.HTTP_503_SERVICE_UNAVAILABLE


class HealthStatus:
    """Health status constants."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
