"""
Cleanup service for removing unverified users.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from infrastructure.database.models import AuditLog, User


class CleanupService:
    """
    Service for cleaning up unverified user accounts.

    Automatically deletes users who haven't verified their email
    within the configured expiry period (default: 24 hours).
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def cleanup_unverified_users(self) -> int:
        """
        Delete unverified users older than configured expiry hours.

        This method:
        1. Finds users where is_email_verified=False
        2. And created_at < (now - EMAIL_VERIFICATION_EXPIRY_HOURS)
        3. Deletes them (cascade deletes related tokens, fingerprints, etc.)
        4. Logs the cleanup operation

        Returns:
            int: Number of deleted users
        """
        expiry_hours = self.settings.EMAIL_VERIFICATION_EXPIRY_HOURS
        cutoff_time = datetime.utcnow() - timedelta(hours=expiry_hours)

        # Delete unverified users older than expiry period
        result = await self.db.execute(
            delete(User)
            .where(User.is_email_verified == False)
            .where(User.created_at < cutoff_time)
        )

        deleted_count = result.rowcount
        await self.db.commit()

        # Log cleanup operation if any users were deleted
        if deleted_count > 0:
            await self._log_cleanup(deleted_count)

        return deleted_count

    async def _log_cleanup(self, count: int) -> None:
        """
        Log cleanup operation to audit log.

        Args:
            count: Number of deleted users
        """
        audit_log = AuditLog(
            event="cleanup_unverified_users",
            details={
                "deleted_count": count,
                "expiry_hours": self.settings.EMAIL_VERIFICATION_EXPIRY_HOURS,
            },
            timestamp=datetime.utcnow(),
        )
        self.db.add(audit_log)
        await self.db.commit()
