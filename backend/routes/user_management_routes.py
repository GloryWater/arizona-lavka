"""
Example API routes demonstrating Unit of Work pattern usage.

Shows how to properly inject and use the Unit of Work in FastAPI endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos import UserRegisterDTO
from application.interfaces.uow import IUnitOfWork
from application.services import UserManagementAppService
from dependencies import get_settings, get_unit_of_work

router = APIRouter()


@router.post("/users/register-with-setup")
async def register_user_with_setup(
    user_data: UserRegisterDTO,
    uow: IUnitOfWork = Depends(get_unit_of_work),
    user_mgmt_service: UserManagementAppService = Depends(UserManagementAppService),
):
    """
    Register a new user with initial setup performed in a single transaction.

    This endpoint demonstrates the Unit of Work pattern by ensuring all operations
    (user creation, audit logging, etc.) happen atomically.
    """
    try:
        result = await user_mgmt_service.register_user_with_initial_setup(
            uow=uow, user_dto=user_data
        )
        return result
    except Exception as e:
        # The Unit of Work will automatically rollback on exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/users/transfer-data")
async def transfer_user_data(
    source_user_id: int,
    target_user_id: int,
    uow: IUnitOfWork = Depends(get_unit_of_work),
    user_mgmt_service: UserManagementAppService = Depends(UserManagementAppService),
):
    """
    Transfer user data from one user to another in a single transaction.

    This endpoint demonstrates how multiple repository operations can be coordinated
    atomically using the Unit of Work pattern.
    """
    try:
        success = await user_mgmt_service.transfer_user_data(
            uow=uow, source_user_id=source_user_id, target_user_id=target_user_id
        )
        if success:
            return {"message": "Data transferred successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source or target user not found",
            )
    except Exception as e:
        # The Unit of Work will automatically rollback on exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data transfer failed: {str(e)}",
        )


@router.post("/users/create-with-preferences")
async def create_user_with_preferences(
    user_data: UserRegisterDTO,
    favorite_items: list = [],
    price_alerts: list = [],
    uow: IUnitOfWork = Depends(get_unit_of_work),
    user_mgmt_service: UserManagementAppService = Depends(UserManagementAppService),
):
    """
    Create a user with multiple associated preferences in a single transaction.

    This endpoint demonstrates complex operations involving multiple entities
    that must all succeed or all fail together.
    """
    try:
        result = await user_mgmt_service.create_user_with_multiple_preferences(
            uow=uow,
            user_dto=user_data,
            favorite_items_data=favorite_items,
            price_alerts_data=price_alerts,
        )
        return result
    except Exception as e:
        # The Unit of Work will automatically rollback on exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation with preferences failed: {str(e)}",
        )


# Alternative approach: Direct injection in route handler
@router.post("/users/register-simple")
async def register_user_simple(
    user_data: UserRegisterDTO, uow: IUnitOfWork = Depends(get_unit_of_work)
):
    """
    Simple example of using Unit of Work directly in a route handler.

    Sometimes it's appropriate to use the Unit of Work directly in the route
    handler for simpler operations.
    """
    from application.dtos import UserProfileDTO
    from core.entities.user import UserEntity

    async with uow:  # Explicit transaction boundary
        # Create user
        user_entity = UserEntity(
            username=user_data.username,
            email=user_data.email,
            hashed_password=user_data.password,  # Should be hashed in real implementation
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        created_user = await uow.users.create(user_entity)

        # Create audit log
        await uow.audit_logs.create(
            user_id=created_user.id,
            action="user_registration",
            resource="user",
            resource_id=created_user.id,
            ip_address="127.0.0.1",
            user_agent="API",
            details=f"Registered user: {created_user.username}",
            status="success",
            error_message=None,
        )

        # Commit transaction
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
