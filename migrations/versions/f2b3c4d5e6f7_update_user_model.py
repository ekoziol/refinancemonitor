"""update user model with new fields

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-01-11 10:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b3c4d5e6f7'
down_revision = 'e1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to user table
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('user', sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('user', sa.Column('deactivated_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('last_login_ip', sa.String(length=45), nullable=True))
    op.add_column('user', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_user_email_verified'), 'user', ['email_verified'], unique=False)
    op.create_index(op.f('ix_user_is_active'), 'user', ['is_active'], unique=False)
    op.create_index(op.f('ix_user_deleted_at'), 'user', ['deleted_at'], unique=False)

    # Backfill: Set email_verified = True and is_active = True for existing users
    # (Done via server_default, but for existing rows we update them)
    op.execute("UPDATE \"user\" SET email_verified = true, is_active = true WHERE email_verified IS NULL OR is_active IS NULL")


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_user_deleted_at'), table_name='user')
    op.drop_index(op.f('ix_user_is_active'), table_name='user')
    op.drop_index(op.f('ix_user_email_verified'), table_name='user')

    # Drop columns
    op.drop_column('user', 'deleted_at')
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'failed_login_attempts')
    op.drop_column('user', 'last_login_ip')
    op.drop_column('user', 'deactivated_at')
    op.drop_column('user', 'is_active')
    op.drop_column('user', 'phone_verified')
    op.drop_column('user', 'phone_number')
    op.drop_column('user', 'email_verified_at')
    op.drop_column('user', 'email_verified')
