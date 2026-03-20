"""
Script to add database indexes for better query performance.
"""

import asyncio
import logging

from sqlalchemy import text

from config import get_settings
from infrastructure.database.connection import get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_database_indexes():
    """Add essential indexes to improve query performance."""
    settings = get_settings()
    db_manager = get_db_manager()

    await db_manager.initialize()

    async with db_manager.get_session() as session:
        # Define indexes to add
        indexes_to_add = [
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active_at);",
            "CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(is_email_verified);",
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);",
            # Config history indexes
            "CREATE INDEX IF NOT EXISTS idx_config_history_user_server ON config_history(user_id, server_id);",
            "CREATE INDEX IF NOT EXISTS idx_config_history_created_at ON config_history(created_at);",
            # Favorite items indexes
            "CREATE INDEX IF NOT EXISTS idx_favorite_items_user_active ON favorite_items(user_id, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_favorite_items_item_server ON favorite_items(item_id, server_id);",
            # Price alerts indexes
            "CREATE INDEX IF NOT EXISTS idx_price_alerts_user_active ON price_alerts(user_id, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_price_alerts_item_server ON price_alerts(item_id, server_id);",
            # Email verification tokens indexes
            "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user ON email_verification_tokens(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires ON email_verification_tokens(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_code ON email_verification_tokens(code);",
            # Login attempts indexes
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_created ON login_attempts(ip_address, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_fingerprint_created ON login_attempts(fingerprint, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_user_created ON login_attempts(user_id, created_at);",
            # Blocked IPs indexes
            "CREATE INDEX IF NOT EXISTS idx_blocked_ips_blocked_until ON blocked_ips(blocked_until);",
            # Device fingerprints indexes
            "CREATE INDEX IF NOT EXISTS idx_device_fingerprints_user_last_seen ON device_fingerprints(user_id, last_seen_at);",
            "CREATE INDEX IF NOT EXISTS idx_device_fingerprints_fingerprint ON device_fingerprints(fingerprint);",
            # Security audit logs indexes
            "CREATE INDEX IF NOT EXISTS idx_security_audit_logs_event_created ON security_audit_logs(event_type, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_logs_user_ip ON security_audit_logs(user_id, ip_address);",
            "CREATE INDEX IF NOT EXISTS idx_security_audit_logs_risk_suspicious ON security_audit_logs(risk_score, is_suspicious);",
            # Audit logs indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created ON audit_logs(action, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource, resource_id);",
            # Admin logs indexes
            "CREATE INDEX IF NOT EXISTS idx_admin_logs_event_created ON admin_logs(event_type, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_admin_logs_ip_created ON admin_logs(ip_address, created_at);",
            # User sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_started ON user_sessions(user_id, started_at);",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_started ON user_sessions(started_at);",
            # Page views indexes
            "CREATE INDEX IF NOT EXISTS idx_page_views_session_viewed ON page_views(session_id, viewed_at);",
            "CREATE INDEX IF NOT EXISTS idx_page_views_user_viewed ON page_views(user_id, viewed_at);",
            # User events indexes
            "CREATE INDEX IF NOT EXISTS idx_user_events_session_created ON user_events(session_id, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_user_events_type_created ON user_events(event_type, created_at);",
            # Conversions indexes
            "CREATE INDEX IF NOT EXISTS idx_conversions_session_converted ON conversions(session_id, converted_at);",
            "CREATE INDEX IF NOT EXISTS idx_conversions_user_converted ON conversions(user_id, converted_at);",
        ]

        for index_query in indexes_to_add:
            try:
                await session.execute(text(index_query))
                logger.info(f"Executed: {index_query[:50]}...")
            except Exception as e:
                logger.error(
                    f"Error executing index query: {index_query[:50]}... - Error: {e}"
                )

        await session.commit()
        logger.info("All indexes added successfully")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(add_database_indexes())
