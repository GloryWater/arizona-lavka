"""
Импорт роутов для main.py.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from routes.auth import router as auth_router
from routes.config import router as config_router
from routes.marketplace import router as marketplace_router
from routes.user import router as user_router
from routes.telegram_auth import router as telegram_auth_router
from routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "config_router",
    "marketplace_router",
    "user_router",
    "telegram_auth_router",
    "admin_router",
]
