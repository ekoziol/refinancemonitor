"""Add is_admin field to User model for admin authorization.

Revision ID: k7g8h9i0j1k2
Revises: j6f7g8h9i0j1
Create Date: 2026-01-12

Security: This migration adds admin role support to fix the
missing authorization vulnerability on admin endpoints.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k7g8h9i0j1k2'
down_revision = 'j6f7g8h9i0j1'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_admin column with default False
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('user', 'is_admin')
