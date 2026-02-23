"""
Импорт роутов для main.py.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

from routes.auth import router as auth_router
from routes.config import router as config_router
from routes.marketplace import router as marketplace_router
from routes.user import router as user_router

__all__ = ["auth_router", "config_router", "marketplace_router", "user_router"]
