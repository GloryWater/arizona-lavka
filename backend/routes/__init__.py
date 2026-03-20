"""
Импорт роутов для main.py.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from routes.admin import router as admin_router
from routes.admin_metrics import router as admin_metrics_router
from routes.auth import router as auth_router
from routes.config import router as config_router
from routes.health import router as health_router
from routes.marketplace import router as marketplace_router
from routes.metrics import router as metrics_router
from routes.telegram_auth import router as telegram_auth_router
from routes.user import router as user_router
from routes.user_management_routes import router as user_management_router

__all__ = [
    "auth_router",
    "config_router",
    "marketplace_router",
    "user_router",
    "telegram_auth_router",
    "admin_router",
    "admin_metrics_router",
    "metrics_router",
    "health_router",
    "user_management_router",
]
