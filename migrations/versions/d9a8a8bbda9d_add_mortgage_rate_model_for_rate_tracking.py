"""add mortgage rate model for rate tracking

Revision ID: d9a8a8bbda9d
Revises: 205cfc5952d1
Create Date: 2026-01-10 22:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9a8a8bbda9d'
down_revision = '205cfc5952d1'
branch_labels = None
depends_on = None


def upgrade():
    # Create the rate_type enum
    rate_type_enum = sa.Enum(
        '30_year_fixed', '15_year_fixed', 'FHA_30', 'VA_30',
        '5_1_ARM', '7_1_ARM', '10_1_ARM',
        name='rate_type_enum'
    )
    rate_type_enum.create(op.get_bind(), checkfirst=True)

    # Create the mortgage_rate table
    op.create_table('mortgage_rate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('rate_type', rate_type_enum, nullable=False),
        sa.Column('rate', sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column('points', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('apr', sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column('change_from_previous', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='mortgagenewsdaily'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'rate_type', name='uq_rate_date_type')
    )

    # Create indexes
    op.create_index(op.f('ix_mortgage_rate_date'), 'mortgage_rate', ['date'], unique=False)
    op.create_index(op.f('ix_mortgage_rate_rate_type'), 'mortgage_rate', ['rate_type'], unique=False)
    op.create_index('idx_rate_date_type', 'mortgage_rate', ['date', 'rate_type'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_rate_date_type', table_name='mortgage_rate')
    op.drop_index(op.f('ix_mortgage_rate_rate_type'), table_name='mortgage_rate')
    op.drop_index(op.f('ix_mortgage_rate_date'), table_name='mortgage_rate')

    # Drop the table
    op.drop_table('mortgage_rate')

    # Drop the enum type
    sa.Enum(name='rate_type_enum').drop(op.get_bind(), checkfirst=True)
