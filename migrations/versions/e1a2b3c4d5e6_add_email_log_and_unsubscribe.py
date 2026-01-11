"""add email log model and unsubscribe fields

Revision ID: e1a2b3c4d5e6
Revises: d9a8a8bbda9d
Create Date: 2026-01-11 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'd9a8a8bbda9d'
branch_labels = None
depends_on = None


def upgrade():
    # Add unsubscribe fields to user table
    op.add_column('user', sa.Column('email_unsubscribed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user', sa.Column('unsubscribe_token', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_user_unsubscribe_token'), 'user', ['unsubscribe_token'], unique=True)

    # Create the email_type enum
    email_type_enum = sa.Enum(
        'alert_triggered', 'payment_confirmation', 'welcome',
        'alert_created', 'unsubscribe_confirmation',
        name='email_type_enum'
    )
    email_type_enum.create(op.get_bind(), checkfirst=True)

    # Create the email_status enum
    email_status_enum = sa.Enum(
        'pending', 'sent', 'delivered', 'failed', 'bounced',
        name='email_status_enum'
    )
    email_status_enum.create(op.get_bind(), checkfirst=True)

    # Create the email_log table
    op.create_table('email_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_type', email_type_enum, nullable=False),
        sa.Column('recipient_email', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('status', email_status_enum, nullable=False, server_default='pending'),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('trigger_id', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ),
        sa.ForeignKeyConstraint(['trigger_id'], ['trigger.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_email_log_email_type'), 'email_log', ['email_type'], unique=False)
    op.create_index(op.f('ix_email_log_status'), 'email_log', ['status'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_email_log_status'), table_name='email_log')
    op.drop_index(op.f('ix_email_log_email_type'), table_name='email_log')

    # Drop the email_log table
    op.drop_table('email_log')

    # Drop the enum types
    sa.Enum(name='email_type_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='email_status_enum').drop(op.get_bind(), checkfirst=True)

    # Remove user columns
    op.drop_index(op.f('ix_user_unsubscribe_token'), table_name='user')
    op.drop_column('user', 'unsubscribe_token')
    op.drop_column('user', 'email_unsubscribed')
