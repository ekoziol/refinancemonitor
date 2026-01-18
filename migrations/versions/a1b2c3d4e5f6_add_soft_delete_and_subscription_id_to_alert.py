"""add soft delete and subscription id to alert

Revision ID: a1b2c3d4e5f6
Revises: d9a8a8bbda9d
Create Date: 2026-01-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd9a8a8bbda9d'
branch_labels = None
depends_on = None


def upgrade():
    # Add deleted_at column for soft delete functionality
    op.add_column('alert', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_alert_deleted_at'), 'alert', ['deleted_at'], unique=False)

    # Add stripe_subscription_id column for proper subscription tracking
    op.add_column('alert', sa.Column('stripe_subscription_id', sa.String(), nullable=True))


def downgrade():
    op.drop_column('alert', 'stripe_subscription_id')
    op.drop_index(op.f('ix_alert_deleted_at'), table_name='alert')
    op.drop_column('alert', 'deleted_at')
