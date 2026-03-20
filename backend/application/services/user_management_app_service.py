"""
Example application service demonstrating Unit of Work pattern usage.

This service shows how to properly use the Unit of Work pattern to coordinate
multiple repository operations within a single transaction.
"""

from datetime import datetime
from typing import Optional

from application.dtos import UserProfileDTO, UserRegisterDTO
from application.interfaces.uow import IUnitOfWork
from core.entities.favorite import FavoriteItemEntity
from core.entities.price_alert import PriceAlertEntity
from core.entities.user import UserEntity
from core.exceptions import BusinessRuleViolationError


class UserManagementAppService:
    """
    Application service demonstrating Unit of Work pattern usage.

    This service coordinates multiple operations that need to be executed
    atomically within a single transaction.
    """

    async def register_user_with_initial_setup(
        self, uow: IUnitOfWork, user_dto: UserRegisterDTO
    ) -> UserProfileDTO:
        """
        Register a new user and perform initial setup operations in a single transaction.

        This method demonstrates the Unit of Work pattern by coordinating
        multiple repository operations that must all succeed or all fail together.

        Args:
            uow: Unit of Work instance managing the transaction
            user_dto: User registration data

        Returns:
            UserProfileDTO: Created user profile

        Raises:
            BusinessRuleViolationError: If business rules are violated
        """
        async with uow:
            # Step 1: Create the user
            user_entity = UserEntity(
                username=user_dto.username,
                email=user_dto.email,
                hashed_password=user_dto.password,  # Should be hashed in a real implementation
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
            )

            created_user = await uow.users.create(user_entity)

            # Step 2: Create initial audit log entry
            await uow.audit_logs.create(
                user_id=created_user.id,
                action="user_registration",
                resource="user",
                resource_id=created_user.id,
                ip_address="127.0.0.1",  # Would come from request in real implementation
                user_agent="System",
                details=f"User registered with username: {created_user.username}",
                status="success",
                error_message=None,
            )

            # Step 3: Create initial favorite items if needed
            # This is just an example - in real app you might want to create default favorites
            # based on user preferences or system defaults

            # Commit all operations together
            await uow.commit()

            # Return the created user profile
            return UserProfileDTO(
                id=created_user.id,
                username=created_user.username,
                email=created_user.email,
                first_name=created_user.first_name,
                last_name=created_user.last_name,
                is_premium=created_user.is_premium,
                role=created_user.role,
                is_telegram_user=created_user.is_telegram_user,
                last_active_at=created_user.last_active_at,
                created_at=created_user.created_at,
                configs_count=0,  # New user has no configs yet
            )

    async def transfer_user_data(
        self, uow: IUnitOfWork, source_user_id: int, target_user_id: int
    ) -> bool:
        """
        Transfer user data from one user to another within a single transaction.

        This method demonstrates how Unit of Work can coordinate complex operations
        involving multiple repositories that must be atomic.

        Args:
            uow: Unit of Work instance managing the transaction
            source_user_id: ID of the source user
            target_user_id: ID of the target user

        Returns:
            bool: True if transfer was successful
        """
        async with uow:
            # Get source and target users
            source_user = await uow.users.get_by_id(source_user_id)
            target_user = await uow.users.get_by_id(target_user_id)

            if not source_user or not target_user:
                return False

            # Transfer favorite items
            source_favorites = await uow.favorites.get_by_user_id(source_user_id)
            for favorite in source_favorites:
                # Update user_id to target user
                favorite.user_id = target_user_id
                await uow.favorites.update(favorite)

            # Transfer price alerts
            source_alerts = await uow.price_alerts.get_by_user_id(source_user_id)
            for alert in source_alerts:
                # Update user_id to target user
                alert.user_id = target_user_id
                await uow.price_alerts.update(alert)

            # Log the transfer operation
            await uow.audit_logs.create(
                user_id=target_user_id,
                action="data_transfer",
                resource="user_data",
                resource_id=source_user_id,
                ip_address="127.0.0.1",
                user_agent="System",
                details=f"Transferred data from user {source_user_id} to {target_user_id}",
                status="success",
                error_message=None,
            )

            await uow.commit()
            return True

    async def create_user_with_multiple_preferences(
        self,
        uow: IUnitOfWork,
        user_dto: UserRegisterDTO,
        favorite_items_data: list,
        price_alerts_data: list,
    ) -> UserProfileDTO:
        """
        Create a user with multiple associated preferences in a single transaction.

        Args:
            uow: Unit of Work instance managing the transaction
            user_dto: User registration data
            favorite_items_data: List of favorite items to create
            price_alerts_data: List of price alerts to create

        Returns:
            UserProfileDTO: Created user profile with preferences
        """
        async with uow:
            # Create the user
            user_entity = UserEntity(
                username=user_dto.username,
                email=user_dto.email,
                hashed_password=user_dto.password,
                first_name=user_dto.first_name,
                last_name=user_dto.last_name,
            )

            created_user = await uow.users.create(user_entity)

            # Create favorite items
            for fav_data in favorite_items_data:
                favorite_entity = FavoriteItemEntity(
                    user_id=created_user.id,
                    item_id=fav_data["item_id"],
                    item_name=fav_data["item_name"],
                    target_price=fav_data.get("target_price"),
                    target_percentage=fav_data.get("target_percentage", -5.0),
                    mode=fav_data.get("mode", "BUY"),
                    server_id=fav_data.get("server_id", 0),
                    notes=fav_data.get("notes"),
                )
                await uow.favorites.create(favorite_entity)

            # Create price alerts
            for alert_data in price_alerts_data:
                alert_entity = PriceAlertEntity(
                    user_id=created_user.id,
                    item_id=alert_data["item_id"],
                    item_name=alert_data["item_name"],
                    server_id=alert_data.get("server_id", 0),
                    target_price=alert_data["target_price"],
                    condition=alert_data.get("condition", "below"),
                )
                await uow.price_alerts.create(alert_entity)

            # Log the creation
            await uow.audit_logs.create(
                user_id=created_user.id,
                action="user_creation_with_preferences",
                resource="user",
                resource_id=created_user.id,
                ip_address="127.0.0.1",
                user_agent="System",
                details=f"Created user with {len(favorite_items_data)} favorites and {len(price_alerts_data)} alerts",
                status="success",
                error_message=None,
            )

            await uow.commit()

            return UserProfileDTO(
                id=created_user.id,
                username=created_user.username,
                email=created_user.email,
                first_name=created_user.first_name,
                last_name=created_user.last_name,
                is_premium=created_user.is_premium,
                role=created_user.role,
                is_telegram_user=created_user.is_telegram_user,
                last_active_at=created_user.last_active_at,
                created_at=created_user.created_at,
                configs_count=0,
            )
