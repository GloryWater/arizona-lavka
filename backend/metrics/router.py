"""
Arizona Lavka Marketplace - Prometheus Metrics Router.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License

Endpoint для экспорта метрик Prometheus.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from config import Settings, get_settings
from metrics.prometheus import get_metrics, get_metrics_content_type, set_app_info

logger = logging.getLogger(__name__)

router = APIRouter(tags=["📊 Prometheus Metrics"])


@router.get("/metrics")
async def get_prometheus_metrics(
    settings: Settings = Depends(get_settings),
):
    """
    Экспорт метрик для Prometheus.

    Prometheus будет опрашивать этот endpoint для сбора метрик.
    Формат: Prometheus text format

    **Доступ**: Только из внутренней сети (Prometheus)
    """
    # Инициализируем метрики приложения
    set_app_info(
        version=settings.APP_VERSION,
        environment="production" if settings.PRODUCTION else "development",
    )

    # Получаем метрики
    metrics = get_metrics()

    return Response(
        content=metrics,
        media_type=get_metrics_content_type(),
    )


@router.get("/metrics/health")
async def metrics_health_check():
    """
    Проверка доступности метрик.

    Returns:
        dict: Статус системы метрик
    """
    try:
        metrics = get_metrics()
        metrics_size = len(metrics)

        return {
            "status": "healthy",
            "metrics_size_bytes": metrics_size,
            "metrics_available": metrics_size > 0,
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metrics unavailable: {str(e)}",
        )
