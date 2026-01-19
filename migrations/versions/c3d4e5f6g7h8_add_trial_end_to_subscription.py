"""add trial_end to subscription

Revision ID: c3d4e5f6g7h8
Revises: f2g3h4i5j6k7
Create Date: 2026-01-18 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'f2g3h4i5j6k7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('subscription', sa.Column('trial_end', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('subscription', 'trial_end')
