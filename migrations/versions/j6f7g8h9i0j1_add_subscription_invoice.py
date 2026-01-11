"""add subscription and invoice tables

Revision ID: j6f7g8h9i0j1
Revises: i5e6f7g8h9i0
Create Date: 2026-01-11 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j6f7g8h9i0j1'
down_revision = 'i5e6f7g8h9i0'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription_status enum
    subscription_status_enum = sa.Enum(
        'active', 'canceled', 'past_due', 'unpaid', 'incomplete',
        'incomplete_expired', 'trialing',
        name='subscription_status_enum'
    )
    subscription_status_enum.create(op.get_bind(), checkfirst=True)

    # Create invoice_status enum
    invoice_status_enum = sa.Enum(
        'draft', 'open', 'paid', 'uncollectible', 'void',
        name='invoice_status_enum'
    )
    invoice_status_enum.create(op.get_bind(), checkfirst=True)

    # Create subscription table
    op.create_table('subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=100), nullable=False),
        sa.Column('status', subscription_status_enum, nullable=False, server_default='incomplete'),
        sa.Column('current_period_start', sa.Integer(), nullable=True),
        sa.Column('current_period_end', sa.Integer(), nullable=True),
        sa.Column('trial_start', sa.Integer(), nullable=True),
        sa.Column('trial_end', sa.Integer(), nullable=True),
        sa.Column('canceled_at', sa.Integer(), nullable=True),
        sa.Column('ended_at', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='usd'),
        sa.Column('interval', sa.String(length=20), nullable=False, server_default='month'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )
    op.create_index(op.f('ix_subscription_user_id'), 'subscription', ['user_id'], unique=False)
    op.create_index(op.f('ix_subscription_alert_id'), 'subscription', ['alert_id'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_customer_id'), 'subscription', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_subscription_stripe_subscription_id'), 'subscription', ['stripe_subscription_id'], unique=True)
    op.create_index(op.f('ix_subscription_status'), 'subscription', ['status'], unique=False)
    op.create_index('idx_subscription_user_status', 'subscription', ['user_id', 'status'], unique=False)
    op.create_index('idx_subscription_period', 'subscription', ['current_period_end'], unique=False)

    # Create invoice table
    op.create_table('invoice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=100), nullable=True),
        sa.Column('amount_due', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='usd'),
        sa.Column('status', invoice_status_enum, nullable=False, server_default='draft'),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_pdf_url', sa.String(length=500), nullable=True),
        sa.Column('hosted_invoice_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscription.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_invoice_id')
    )
    op.create_index(op.f('ix_invoice_subscription_id'), 'invoice', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_invoice_user_id'), 'invoice', ['user_id'], unique=False)
    op.create_index(op.f('ix_invoice_stripe_invoice_id'), 'invoice', ['stripe_invoice_id'], unique=True)
    op.create_index(op.f('ix_invoice_status'), 'invoice', ['status'], unique=False)
    op.create_index('idx_invoice_user_status', 'invoice', ['user_id', 'status', 'invoice_date'], unique=False)
    op.create_index('idx_invoice_subscription', 'invoice', ['subscription_id', 'invoice_date'], unique=False)


def downgrade():
    # Drop invoice
    op.drop_index('idx_invoice_subscription', table_name='invoice')
    op.drop_index('idx_invoice_user_status', table_name='invoice')
    op.drop_index(op.f('ix_invoice_status'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_stripe_invoice_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_user_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_subscription_id'), table_name='invoice')
    op.drop_table('invoice')

    # Drop subscription
    op.drop_index('idx_subscription_period', table_name='subscription')
    op.drop_index('idx_subscription_user_status', table_name='subscription')
    op.drop_index(op.f('ix_subscription_status'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_stripe_subscription_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_stripe_customer_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_alert_id'), table_name='subscription')
    op.drop_index(op.f('ix_subscription_user_id'), table_name='subscription')
    op.drop_table('subscription')

    # Drop enums
    sa.Enum(name='invoice_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_status_enum').drop(op.get_bind(), checkfirst=True)
