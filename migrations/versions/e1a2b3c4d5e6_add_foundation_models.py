"""add foundation models (user_preference, password_reset_token, email_verification_token)

Revision ID: e1a2b3c4d5e6
Revises: d9a8a8bbda9d
Create Date: 2026-01-11 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'd9a8a8bbda9d'
branch_labels = None
depends_on = None


def upgrade():
    # Create alert_frequency enum
    alert_frequency_enum = sa.Enum('instant', 'daily', 'weekly', name='alert_frequency_enum')
    alert_frequency_enum.create(op.get_bind(), checkfirst=True)

    # Create user_preference table
    op.create_table('user_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_frequency', alert_frequency_enum, nullable=False, server_default='instant'),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('theme', sa.String(length=20), nullable=False, server_default='light'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('date_format', sa.String(length=20), nullable=False, server_default='MM/DD/YYYY'),
        sa.Column('min_rate_drop_threshold', sa.Numeric(precision=4, scale=3), nullable=False, server_default='0.125'),
        sa.Column('auto_calculate_refi_cost', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_refi_term', sa.Integer(), nullable=False, server_default='360'),
        sa.Column('share_anonymous_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preference_user_id'), 'user_preference', ['user_id'], unique=True)

    # Create password_reset_token table
    op.create_table('password_reset_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_password_reset_token_user_id'), 'password_reset_token', ['user_id'], unique=False)
    op.create_index(op.f('ix_password_reset_token_token'), 'password_reset_token', ['token'], unique=True)
    op.create_index(op.f('ix_password_reset_token_expires_at'), 'password_reset_token', ['expires_at'], unique=False)

    # Create email_verification_token table
    op.create_table('email_verification_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('resent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_resent_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_email_verification_token_user_id'), 'email_verification_token', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_verification_token_token'), 'email_verification_token', ['token'], unique=True)
    op.create_index(op.f('ix_email_verification_token_expires_at'), 'email_verification_token', ['expires_at'], unique=False)


def downgrade():
    # Drop email_verification_token
    op.drop_index(op.f('ix_email_verification_token_expires_at'), table_name='email_verification_token')
    op.drop_index(op.f('ix_email_verification_token_token'), table_name='email_verification_token')
    op.drop_index(op.f('ix_email_verification_token_user_id'), table_name='email_verification_token')
    op.drop_table('email_verification_token')

    # Drop password_reset_token
    op.drop_index(op.f('ix_password_reset_token_expires_at'), table_name='password_reset_token')
    op.drop_index(op.f('ix_password_reset_token_token'), table_name='password_reset_token')
    op.drop_index(op.f('ix_password_reset_token_user_id'), table_name='password_reset_token')
    op.drop_table('password_reset_token')

    # Drop user_preference
    op.drop_index(op.f('ix_user_preference_user_id'), table_name='user_preference')
    op.drop_table('user_preference')

    # Drop enum
    sa.Enum(name='alert_frequency_enum').drop(op.get_bind(), checkfirst=True)
