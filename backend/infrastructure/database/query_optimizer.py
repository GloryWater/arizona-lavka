"""
Database query optimization utilities.
"""

from typing import List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from models import Base

ModelType = TypeVar("ModelType", bound=Base)


class QueryOptimizer:
    """Utility class for optimizing database queries."""

    @staticmethod
    def add_index_if_not_exists(
        table_name: str, column_names: List[str], index_name: Optional[str] = None
    ) -> str:
        """
        Generate SQL to add an index if it doesn't exist (PostgreSQL).
        """
        if not index_name:
            index_name = f"idx_{table_name}_{'_'.join(column_names)}"

        return f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE tablename = '{table_name}'
                AND indexname = '{index_name}'
            ) THEN
                CREATE INDEX {index_name} ON {table_name} ({', '.join(column_names)});
            END IF;
        END$$;
        """

    @staticmethod
    async def get_with_joins(
        db: AsyncSession,
        model: Type[ModelType],
        filters: Optional[dict] = None,
        joins: Optional[List[tuple]] = None,
        options: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ModelType]:
        """
        Optimized query with joins and filters.
        """
        query = select(model)

        # Add joins if specified
        if joins:
            for join_model, join_condition in joins:
                query = query.join(join_model, join_condition)

        # Add filters if specified
        if filters:
            for attr, value in filters.items():
                if hasattr(model, attr):
                    column = getattr(model, attr)
                    if isinstance(value, (list, tuple)):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)

        # Add options (like selectinload) if specified
        if options:
            for opt in options:
                query = query.options(opt)

        # Add limit and offset if specified
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count_with_filters(
        db: AsyncSession, model: Type[ModelType], filters: Optional[dict] = None
    ) -> int:
        """
        Count records with filters efficiently.
        """
        query = select(model)

        if filters:
            for attr, value in filters.items():
                if hasattr(model, attr):
                    column = getattr(model, attr)
                    if isinstance(value, (list, tuple)):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)

        query = select(func.count()).select_from(query.subquery())
        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def exists_with_filters(
        db: AsyncSession, model: Type[ModelType], filters: dict
    ) -> bool:
        """
        Check if records exist with filters efficiently.
        """
        query = select(model)

        for attr, value in filters.items():
            if hasattr(model, attr):
                column = getattr(model, attr)
                if isinstance(value, (list, tuple)):
                    query = query.where(column.in_(value))
                else:
                    query = query.where(column == value)

        query = query.exists()
        result = await db.execute(select(query))
        return result.scalar_one()


from sqlalchemy import func
