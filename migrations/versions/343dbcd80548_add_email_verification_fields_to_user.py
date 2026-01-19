"""add email verification fields to user

Revision ID: 343dbcd80548
Revises: d9a8a8bbda9d
Create Date: 2026-01-18 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '343dbcd80548'
down_revision = 'd9a8a8bbda9d'
branch_labels = None
depends_on = None


def upgrade():
    # Add email verification fields to user table
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('email_verification_token', sa.String(length=255), nullable=True))
    op.add_column('user', sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True))

    # Create unique index on verification token
    op.create_index(op.f('ix_user_email_verification_token'), 'user', ['email_verification_token'], unique=True)

    # Set default value for existing users (mark them as verified)
    op.execute("UPDATE \"user\" SET email_verified = true WHERE email_verified IS NULL")

    # Now make email_verified non-nullable
    op.alter_column('user', 'email_verified', nullable=False, server_default='false')


def downgrade():
    op.drop_index(op.f('ix_user_email_verification_token'), table_name='user')
    op.drop_column('user', 'email_verification_sent_at')
    op.drop_column('user', 'email_verification_token')
    op.drop_column('user', 'email_verified')
