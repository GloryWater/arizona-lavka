"""add_performance_indexes

Revision ID: add_performance_indexes
Revises: admin_panel_init
Create Date: 2026-02-25

Добавляет индексы для улучшения производительности запросов.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_performance_indexes'
down_revision: Union[str, None] = 'admin_panel_init'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет индексы для улучшения производительности."""
    
    # Индексы для таблицы users
    op.create_index(
        'ix_users_role_active',
        'users',
        ['role', 'last_active_at'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'ix_users_telegram',
        'users',
        ['telegram_id', 'is_telegram_user'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'ix_users_created_at',
        'users',
        ['created_at'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы config_history
    op.create_index(
        'ix_config_history_server_mode',
        'config_history',
        ['server_id', 'mode', 'created_at'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы favorite_items
    op.create_index(
        'ix_favorite_items_active',
        'favorite_items',
        ['is_active', 'user_id'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'ix_favorite_items_mode_server',
        'favorite_items',
        ['mode', 'server_id'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы price_alerts
    op.create_index(
        'ix_price_alerts_active_triggered',
        'price_alerts',
        ['is_active', 'triggered', 'created_at'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'ix_price_alerts_server',
        'price_alerts',
        ['server_id', 'is_active'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы audit_logs
    op.create_index(
        'ix_audit_logs_status_created',
        'audit_logs',
        ['status', 'created_at'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'ix_audit_logs_resource',
        'audit_logs',
        ['resource', 'resource_id'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы admin_logs
    op.create_index(
        'ix_admin_logs_user_event',
        'admin_logs',
        ['user_id', 'event_type'],
        unique=False,
        if_not_exists=True
    )
    
    # Индексы для таблицы global_settings
    op.create_index(
        'ix_global_settings_updated_at',
        'global_settings',
        ['updated_at'],
        unique=False,
        if_not_exists=True
    )


def downgrade() -> None:
    """Удаляет индексы."""
    
    # Удаляем индексы в обратном порядке
    op.drop_index('ix_global_settings_updated_at', table_name='global_settings', if_exists=True)
    op.drop_index('ix_admin_logs_user_event', table_name='admin_logs', if_exists=True)
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs', if_exists=True)
    op.drop_index('ix_audit_logs_status_created', table_name='audit_logs', if_exists=True)
    op.drop_index('ix_price_alerts_server', table_name='price_alerts', if_exists=True)
    op.drop_index('ix_price_alerts_active_triggered', table_name='price_alerts', if_exists=True)
    op.drop_index('ix_favorite_items_mode_server', table_name='favorite_items', if_exists=True)
    op.drop_index('ix_favorite_items_active', table_name='favorite_items', if_exists=True)
    op.drop_index('ix_config_history_server_mode', table_name='config_history', if_exists=True)
    op.drop_index('ix_users_created_at', table_name='users', if_exists=True)
    op.drop_index('ix_users_telegram', table_name='users', if_exists=True)
    op.drop_index('ix_users_role_active', table_name='users', if_exists=True)
