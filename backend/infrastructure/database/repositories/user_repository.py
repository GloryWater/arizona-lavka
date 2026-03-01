"""
User repository implementation.
"""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.user import UserEntity
from application.interfaces.repositories import IUserRepository
from infrastructure.database.models import User


class UserRepository(IUserRepository):
    """
    Repository для работы с пользователями.

    Реализует интерфейс IUserRepository используя SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Args:
            session: Сессия базы данных
        """
        self.session = session

    def _to_entity(self, user: User) -> UserEntity:
        """Конвертирует ORM модель в domain сущность."""
        return UserEntity(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            is_premium=user.is_premium,
            role=user.role,
            telegram_id=user.telegram_id,
            telegram_username=user.telegram_username,
            is_telegram_user=user.is_telegram_user,
            last_active_at=user.last_active_at,
            login_attempts=user.login_attempts,
            locked_until=user.locked_until,
            refresh_token=user.refresh_token,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _from_entity(self, entity: UserEntity) -> User:
        """Конвертирует domain сущность в ORM модель."""
        return User(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            first_name=entity.first_name,
            last_name=entity.last_name,
            is_premium=entity.is_premium,
            role=entity.role,
            telegram_id=entity.telegram_id,
            telegram_username=entity.telegram_username,
            is_telegram_user=entity.is_telegram_user,
            last_active_at=entity.last_active_at,
            login_attempts=entity.login_attempts,
            locked_until=entity.locked_until,
            refresh_token=entity.refresh_token,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        user = await self.session.get(User, user_id)
        return self._to_entity(user) if user else None

    async def get_by_username(self, username: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        return self._to_entity(user) if user else None

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        return self._to_entity(user) if user else None

    async def get_by_telegram_id(self, telegram_id: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        return self._to_entity(user) if user else None

    async def get_by_username_or_email(self, username_or_email: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.username == username_or_email,
                    User.email == username_or_email,
                )
            )
        )
        user = result.scalar_one_or_none()
        return self._to_entity(user) if user else None

    async def create(self, user: UserEntity) -> UserEntity:
        db_user = self._from_entity(user)
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)
        return self._to_entity(db_user)

    async def update(self, user: UserEntity) -> UserEntity:
        db_user = await self.session.get(User, user.id)
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")

        # Обновляем поля
        for field, value in vars(user).items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)

        await self.session.flush()
        await self.session.refresh(db_user)
        return self._to_entity(db_user)

    async def delete(self, user_id: int) -> bool:
        user = await self.session.get(User, user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def get_all(
        self,
        page: int = 1,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: str = "created_at",
    ) -> List[UserEntity]:
        query = select(User)

        # Поиск
        if search:
            if search.isdigit():
                query = query.where(
                    or_(
                        User.username.ilike(f"%{search}%"),
                        User.id == int(search),
                    )
                )
            else:
                query = query.where(User.username.ilike(f"%{search}%"))

        # Сортировка
        if sort_by == "username":
            query = query.order_by(User.username)
        elif sort_by == "configs_count":
            # Сортировка по количеству конфигов через подзапрос
            from infrastructure.database.models import ConfigHistory
            configs_count_subquery = (
                select(func.count(ConfigHistory.id))
                .where(ConfigHistory.user_id == User.id)
                .correlate(User)
                .scalar_subquery()
            )
            query = query.order_by(desc(configs_count_subquery))
        else:  # created_at
            query = query.order_by(desc(User.created_at))

        # Пагинация
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        users = result.scalars().all()
        return [self._to_entity(u) for u in users]

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one() or 0

    async def count_active_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(func.distinct(User.id))).where(
                User.last_active_at >= since
            )
        )
        return result.scalar_one() or 0
