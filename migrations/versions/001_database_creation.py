"""Database creation

Revision ID: 001
Revises: 
Create Date: 2026-03-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('registered_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create links table
    op.create_table(
        'links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('short_code', sa.String(length=50), nullable=False),
        sa.Column('original_url', sa.String(length=2048), nullable=False),
        sa.Column('custom_alias', sa.String(length=50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_used_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_original_url', 'links', ['original_url'], unique=False)
    op.create_index('idx_user_created', 'links', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_links_custom_alias'), 'links', ['custom_alias'], unique=True)
    op.create_index(op.f('ix_links_short_code'), 'links', ['short_code'], unique=True)
    op.create_index(op.f('ix_links_user_id'), 'links', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_links_user_id'), table_name='links')
    op.drop_index(op.f('ix_links_short_code'), table_name='links')
    op.drop_index(op.f('ix_links_custom_alias'), table_name='links')
    op.drop_index('idx_user_created', table_name='links')
    op.drop_index('idx_original_url', table_name='links')
    op.drop_table('links')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
