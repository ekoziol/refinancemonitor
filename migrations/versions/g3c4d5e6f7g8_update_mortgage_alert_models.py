"""update mortgage and alert models with new fields

Revision ID: g3c4d5e6f7g8
Revises: f2b3c4d5e6f7
Create Date: 2026-01-11 10:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g3c4d5e6f7g8'
down_revision = 'f2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    # Create property_type enum
    property_type_enum = sa.Enum('single_family', 'condo', 'townhouse', 'multi_family', name='property_type_enum')
    property_type_enum.create(op.get_bind(), checkfirst=True)

    # Create occupancy_type enum
    occupancy_type_enum = sa.Enum('primary', 'secondary', 'investment', name='occupancy_type_enum')
    occupancy_type_enum.create(op.get_bind(), checkfirst=True)

    # Add new fields to mortgage table
    op.add_column('mortgage', sa.Column('last_updated_by', sa.Integer(), nullable=True))
    op.add_column('mortgage', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('mortgage', sa.Column('estimated_property_value', sa.Float(), nullable=True))
    op.add_column('mortgage', sa.Column('property_type', property_type_enum, nullable=True))
    op.add_column('mortgage', sa.Column('occupancy_type', occupancy_type_enum, nullable=True, server_default='primary'))
    op.add_column('mortgage', sa.Column('lender_name', sa.String(length=100), nullable=True))
    op.add_column('mortgage', sa.Column('loan_number', sa.String(length=50), nullable=True))
    op.add_column('mortgage', sa.Column('last_rate_check_date', sa.DateTime(), nullable=True))

    # Create foreign key for last_updated_by
    op.create_foreign_key('fk_mortgage_last_updated_by', 'mortgage', 'user', ['last_updated_by'], ['id'])

    # Create indexes for mortgage
    op.create_index(op.f('ix_mortgage_deleted_at'), 'mortgage', ['deleted_at'], unique=False)

    # Add new fields to alert table
    op.add_column('alert', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('alert', sa.Column('paused_at', sa.DateTime(), nullable=True))
    op.add_column('alert', sa.Column('last_notification_sent_at', sa.DateTime(), nullable=True))
    op.add_column('alert', sa.Column('notification_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('alert', sa.Column('first_triggered_at', sa.DateTime(), nullable=True))
    op.add_column('alert', sa.Column('last_triggered_at', sa.DateTime(), nullable=True))
    op.add_column('alert', sa.Column('total_triggers', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('alert', sa.Column('user_dismissed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('alert', sa.Column('dismissed_at', sa.DateTime(), nullable=True))
    op.add_column('alert', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Create indexes for alert
    op.create_index(op.f('ix_alert_is_active'), 'alert', ['is_active'], unique=False)
    op.create_index(op.f('ix_alert_deleted_at'), 'alert', ['deleted_at'], unique=False)


def downgrade():
    # Drop alert indexes
    op.drop_index(op.f('ix_alert_deleted_at'), table_name='alert')
    op.drop_index(op.f('ix_alert_is_active'), table_name='alert')

    # Drop alert columns
    op.drop_column('alert', 'deleted_at')
    op.drop_column('alert', 'dismissed_at')
    op.drop_column('alert', 'user_dismissed')
    op.drop_column('alert', 'total_triggers')
    op.drop_column('alert', 'last_triggered_at')
    op.drop_column('alert', 'first_triggered_at')
    op.drop_column('alert', 'notification_count')
    op.drop_column('alert', 'last_notification_sent_at')
    op.drop_column('alert', 'paused_at')
    op.drop_column('alert', 'is_active')

    # Drop mortgage indexes
    op.drop_index(op.f('ix_mortgage_deleted_at'), table_name='mortgage')

    # Drop foreign key
    op.drop_constraint('fk_mortgage_last_updated_by', 'mortgage', type_='foreignkey')

    # Drop mortgage columns
    op.drop_column('mortgage', 'last_rate_check_date')
    op.drop_column('mortgage', 'loan_number')
    op.drop_column('mortgage', 'lender_name')
    op.drop_column('mortgage', 'occupancy_type')
    op.drop_column('mortgage', 'property_type')
    op.drop_column('mortgage', 'estimated_property_value')
    op.drop_column('mortgage', 'deleted_at')
    op.drop_column('mortgage', 'last_updated_by')

    # Drop enums
    sa.Enum(name='occupancy_type_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='property_type_enum').drop(op.get_bind(), checkfirst=True)
