"""add paused_reason to subscription

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-18 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Add paused_reason column to subscription table
    op.add_column('subscription', sa.Column('paused_reason', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('subscription', 'paused_reason')
