"""add subscription and invoice models for payment separation

Revision ID: a1b2c3d4e5f6
Revises: d9a8a8bbda9d
Create Date: 2026-01-18 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd9a8a8bbda9d'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription table
    op.create_table('subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_period_start', sa.Integer(), nullable=True),
        sa.Column('current_period_end', sa.Integer(), nullable=True),
        sa.Column('trial_start', sa.Integer(), nullable=True),
        sa.Column('trial_end', sa.Integer(), nullable=True),
        sa.Column('canceled_at', sa.Integer(), nullable=True),
        sa.Column('ended_at', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('interval', sa.String(length=20), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=True),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_user_id'), 'subscription', ['user_id'], unique=False)
    op.create_index(op.f('ix_subscription_alert_id'), 'subscription', ['alert_id'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_customer_id'), 'subscription', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_subscription_id'), 'subscription', ['stripe_subscription_id'], unique=True)
    op.create_index(op.f('ix_subscription_status'), 'subscription', ['status'], unique=False)

    # Create invoice table
    op.create_table('invoice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=100), nullable=True),
        sa.Column('amount_due', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_pdf_url', sa.String(length=500), nullable=True),
        sa.Column('hosted_invoice_url', sa.String(length=500), nullable=True),
        sa.Column('created_on', sa.DateTime(), nullable=True),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscription.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_subscription_id'), 'invoice', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_invoice_user_id'), 'invoice', ['user_id'], unique=False)
    op.create_index(op.f('ix_invoice_stripe_invoice_id'), 'invoice', ['stripe_invoice_id'], unique=True)
    op.create_index(op.f('ix_invoice_status'), 'invoice', ['status'], unique=False)


def downgrade():
    # Drop invoice table
    op.drop_index(op.f('ix_invoice_status'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_stripe_invoice_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_user_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_subscription_id'), table_name='invoice')
    op.drop_table('invoice')

    # Drop subscription table
    op.drop_index(op.f('ix_subscription_status'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_stripe_subscription_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_stripe_customer_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_alert_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_user_id'), table_name='subscription')
    op.drop_table('subscription')
