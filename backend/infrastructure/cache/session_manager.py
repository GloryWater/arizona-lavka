"""
Session management using Redis.
"""

import json
import logging
import secrets
import time
from typing import Any, Dict, Optional

from config import get_settings
from infrastructure.cache.redis_connection import get_redis_manager

logger = logging.getLogger(__name__)


class SessionManager:
    """Session management using Redis."""

    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.settings = get_settings()

    async def create_session(
        self, user_id: int, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "data": data or {},
        }

        try:
            success = await self.redis_manager.set(
                f"session:{session_id}",
                json.dumps(session_data),
                ex=self.settings.SESSION_EXPIRE_SECONDS,
            )

            if success:
                # Also store user's active sessions
                await self.redis_manager.sadd(
                    f"user_sessions:{user_id}",
                    session_id,
                    ex=self.settings.SESSION_EXPIRE_SECONDS,
                )

                return session_id
            else:
                raise Exception("Failed to create session in Redis")
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID."""
        try:
            session_data_json = await self.redis_manager.get(f"session:{session_id}")
            if session_data_json:
                session_data = json.loads(session_data_json)

                # Update last accessed time
                session_data["last_accessed"] = time.time()
                await self.redis_manager.set(
                    f"session:{session_id}",
                    json.dumps(session_data),
                    ex=self.settings.SESSION_EXPIRE_SECONDS,
                )

                return session_data
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data."""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            session_data.update(data)
            session_data["last_accessed"] = time.time()

            return await self.redis_manager.set(
                f"session:{session_id}",
                json.dumps(session_data),
                ex=self.settings.SESSION_EXPIRE_SECONDS,
            )
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                user_id = session_data.get("user_id")
                # Remove from user's active sessions
                if user_id:
                    await self.redis_manager.srem(
                        f"user_sessions:{user_id}", session_id
                    )

            return await self.redis_manager.delete(f"session:{session_id}")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        try:
            session_ids = await self.redis_manager.smembers(f"user_sessions:{user_id}")
            if not session_ids:
                return 0

            # Delete all session keys
            session_keys = [f"session:{sid}" for sid in session_ids]
            deleted_count = await self.redis_manager.delete(*session_keys)

            # Delete the user sessions set
            await self.redis_manager.delete(f"user_sessions:{user_id}")

            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting sessions for user {user_id}: {e}")
            return 0

    async def extend_session(self, session_id: str) -> bool:
        """Extend session expiration."""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            session_data["last_accessed"] = time.time()

            return await self.redis_manager.set(
                f"session:{session_id}",
                json.dumps(session_data),
                ex=self.settings.SESSION_EXPIRE_SECONDS,
            )
        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            return False

    async def is_valid_session(
        self, session_id: str, user_id: Optional[int] = None
    ) -> bool:
        """Check if session is valid."""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            # Check if user_id matches if provided
            if user_id and session_data.get("user_id") != user_id:
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {e}")
            return False


# Global instance
_session_manager_instance: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get session manager instance."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance
