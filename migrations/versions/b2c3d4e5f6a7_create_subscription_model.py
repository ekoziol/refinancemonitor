"""create subscription model

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-18 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription table
    op.create_table('subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('initial_payment', sa.Boolean(), nullable=True, default=False),
        sa.Column('payment_status', sa.String(), nullable=True, default='incomplete'),
        sa.Column('paused_at', sa.DateTime(), nullable=True),
        sa.Column('initial_period_start', sa.Integer(), nullable=True),
        sa.Column('initial_period_end', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.Integer(), nullable=True),
        sa.Column('period_end', sa.Integer(), nullable=True),
        sa.Column('price_id', sa.String(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('created_on', sa.DateTime(), nullable=True),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_id')
    )
    op.create_index(op.f('ix_subscription_payment_status'), 'subscription', ['payment_status'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_customer_id'), 'subscription', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_subscription_id'), 'subscription', ['stripe_subscription_id'], unique=False)

    # Migrate existing data from alert to subscription
    # This SQL will create subscription records for all existing alerts that have payment data
    op.execute("""
        INSERT INTO subscription (
            alert_id,
            initial_payment,
            payment_status,
            paused_at,
            initial_period_start,
            initial_period_end,
            period_start,
            period_end,
            price_id,
            stripe_customer_id,
            stripe_invoice_id,
            stripe_subscription_id,
            created_on,
            updated_on
        )
        SELECT
            id,
            initial_payment,
            payment_status,
            paused_at,
            initial_period_start,
            initial_period_end,
            period_start,
            period_end,
            price_id,
            stripe_customer_id,
            stripe_invoice_id,
            stripe_subscription_id,
            created_on,
            updated_on
        FROM alert
        WHERE initial_payment IS NOT NULL OR payment_status IS NOT NULL
    """)


def downgrade():
    # Note: Downgrade does not migrate data back to alert table
    # The alert table still has the columns for backwards compatibility
    op.drop_index(op.f('ix_subscription_stripe_subscription_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_stripe_customer_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_payment_status'), table_name='subscription')
    op.drop_table('subscription')
