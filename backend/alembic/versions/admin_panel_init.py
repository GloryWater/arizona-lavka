"""Add admin panel tables and user role fields

Revision ID: admin_panel_init
Revises: initial
Create Date: 2026-02-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'admin_panel_init'
down_revision = None  # Initial migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Добавляем поля role и last_active_at в таблицу users ===
    op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(), nullable=True))
    
    # Создаём индекс на role
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_index('ix_users_last_active_at', 'users', ['last_active_at'], unique=False)
    
    # === Создаём таблицу admin_logs ===
    op.create_table(
        'admin_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для admin_logs
    op.create_index('ix_admin_logs_user_id', 'admin_logs', ['user_id'], unique=False)
    op.create_index('ix_admin_logs_event_type', 'admin_logs', ['event_type'], unique=False)
    op.create_index('ix_admin_logs_created_at', 'admin_logs', ['created_at'], unique=False)
    op.create_index('ix_admin_logs_event_created', 'admin_logs', ['event_type', 'created_at'], unique=False)
    
    # === Создаём таблицу global_settings ===
    op.create_table(
        'global_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON, nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Индексы для global_settings
    op.create_index('ix_global_settings_key', 'global_settings', ['key'], unique=True)


def downgrade() -> None:
    # === Удаляем таблицы ===
    op.drop_index('ix_global_settings_key')
    op.drop_table('global_settings')
    
    op.drop_index('ix_admin_logs_event_created')
    op.drop_index('ix_admin_logs_created_at')
    op.drop_index('ix_admin_logs_event_type')
    op.drop_index('ix_admin_logs_user_id')
    op.drop_table('admin_logs')
    
    # === Удаляем поля из users ===
    op.drop_index('ix_users_last_active_at')
    op.drop_index('ix_users_role')
    op.drop_column('users', 'last_active_at')
    op.drop_column('users', 'role')
