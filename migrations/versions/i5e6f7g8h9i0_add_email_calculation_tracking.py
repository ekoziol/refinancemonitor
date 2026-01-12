"""add email_log and calculation_history tables

Revision ID: i5e6f7g8h9i0
Revises: h4d5e6f7g8h9
Create Date: 2026-01-11 10:44:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i5e6f7g8h9i0'
down_revision = 'h4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_type enum
    email_type_enum = sa.Enum(
        'welcome', 'alert_notification', 'password_reset', 'email_verification',
        'payment_receipt', 'payment_failed', 'rate_drop_alert',
        'weekly_digest', 'marketing',
        name='email_type_enum'
    )
    email_type_enum.create(op.get_bind(), checkfirst=True)

    # Create email_status enum
    email_status_enum = sa.Enum(
        'queued', 'sent', 'failed', 'bounced', 'opened', 'clicked',
        name='email_status_enum'
    )
    email_status_enum.create(op.get_bind(), checkfirst=True)

    # Create calc_type enum
    calc_type_enum = sa.Enum(
        'monthly_payment', 'break_even', 'efficient_frontier',
        'refinance_savings', 'amortization',
        name='calc_type_enum'
    )
    calc_type_enum.create(op.get_bind(), checkfirst=True)

    # Create email_log table
    op.create_table('email_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('email_type', email_type_enum, nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('trigger_id', sa.Integer(), nullable=True),
        sa.Column('status', email_status_enum, nullable=False, server_default='queued'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['trigger_id'], ['trigger.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_log_user_id'), 'email_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_log_recipient_email'), 'email_log', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_email_log_email_type'), 'email_log', ['email_type'], unique=False)
    op.create_index(op.f('ix_email_log_status'), 'email_log', ['status'], unique=False)
    op.create_index(op.f('ix_email_log_provider_message_id'), 'email_log', ['provider_message_id'], unique=False)
    op.create_index(op.f('ix_email_log_created_at'), 'email_log', ['created_at'], unique=False)
    op.create_index('idx_email_user_created', 'email_log', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_email_type_status', 'email_log', ['email_type', 'status', 'created_at'], unique=False)

    # Create calculation_history table
    op.create_table('calculation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('mortgage_id', sa.Integer(), nullable=True),
        sa.Column('calculation_type', calc_type_enum, nullable=False),
        sa.Column('input_params', sa.JSON(), nullable=False),
        sa.Column('output_results', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mortgage_id'], ['mortgage.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calculation_history_user_id'), 'calculation_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_calculation_history_session_id'), 'calculation_history', ['session_id'], unique=False)
    op.create_index(op.f('ix_calculation_history_calculation_type'), 'calculation_history', ['calculation_type'], unique=False)
    op.create_index(op.f('ix_calculation_history_created_at'), 'calculation_history', ['created_at'], unique=False)
    op.create_index('idx_calc_user_created', 'calculation_history', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_calc_session', 'calculation_history', ['session_id', 'created_at'], unique=False)


def downgrade():
    # Drop calculation_history
    op.drop_index('idx_calc_session', table_name='calculation_history')
    op.drop_index('idx_calc_user_created', table_name='calculation_history')
    op.drop_index(op.f('ix_calculation_history_created_at'), table_name='calculation_history')
    op.drop_index(op.f('ix_calculation_history_calculation_type'), table_name='calculation_history')
    op.drop_index(op.f('ix_calculation_history_session_id'), table_name='calculation_history')
    op.drop_index(op.f('ix_calculation_history_user_id'), table_name='calculation_history')
    op.drop_table('calculation_history')

    # Drop email_log
    op.drop_index('idx_email_type_status', table_name='email_log')
    op.drop_index('idx_email_user_created', table_name='email_log')
    op.drop_index(op.f('ix_email_log_created_at'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_provider_message_id'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_status'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_email_type'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_recipient_email'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_user_id'), table_name='email_log')
    op.drop_table('email_log')

    # Drop enums
    sa.Enum(name='calc_type_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='email_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='email_type_enum').drop(op.get_bind(), checkfirst=True)
