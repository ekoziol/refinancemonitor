"""update trigger model with new fields and enums

Revision ID: h4d5e6f7g8h9
Revises: g3c4d5e6f7g8
Create Date: 2026-01-11 10:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h4d5e6f7g8h9'
down_revision = 'g3c4d5e6f7g8'
branch_labels = None
depends_on = None


def upgrade():
    # Create trigger_status enum
    trigger_status_enum = sa.Enum('triggered', 'notified', 'acknowledged', 'expired', name='trigger_status_enum')
    trigger_status_enum.create(op.get_bind(), checkfirst=True)

    # Create user_action enum
    user_action_enum = sa.Enum('none', 'contacted_lender', 'dismissed', 'snoozed', name='user_action_enum')
    user_action_enum.create(op.get_bind(), checkfirst=True)

    # Add new fields to trigger table
    # New status field (will replace alert_trigger_status after migration)
    op.add_column('trigger', sa.Column('status', trigger_status_enum, nullable=True))
    op.add_column('trigger', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('trigger', sa.Column('triggered_at', sa.DateTime(), nullable=True))

    # Trigger details
    op.add_column('trigger', sa.Column('threshold_value', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('trigger', sa.Column('current_value', sa.Numeric(precision=10, scale=2), nullable=True))

    # Notification tracking
    op.add_column('trigger', sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trigger', sa.Column('notification_sent_at', sa.DateTime(), nullable=True))

    # User interaction
    op.add_column('trigger', sa.Column('user_viewed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trigger', sa.Column('viewed_at', sa.DateTime(), nullable=True))
    op.add_column('trigger', sa.Column('user_action', user_action_enum, nullable=True))
    op.add_column('trigger', sa.Column('action_taken_at', sa.DateTime(), nullable=True))

    # Expiration
    op.add_column('trigger', sa.Column('expires_at', sa.DateTime(), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_trigger_status'), 'trigger', ['status'], unique=False)
    op.create_index(op.f('ix_trigger_triggered_at'), 'trigger', ['triggered_at'], unique=False)

    # Migrate data from old fields to new fields
    # Map alert_trigger_status (integer) to status (enum)
    # Typically: 1 = triggered, 0 = expired
    op.execute("""
        UPDATE trigger SET
            status = CASE
                WHEN alert_trigger_status = 1 THEN 'triggered'
                WHEN alert_trigger_status = 0 THEN 'expired'
                ELSE 'triggered'
            END::trigger_status_enum,
            reason = alert_trigger_reason,
            triggered_at = alert_trigger_date
        WHERE status IS NULL
    """)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_trigger_triggered_at'), table_name='trigger')
    op.drop_index(op.f('ix_trigger_status'), table_name='trigger')

    # Drop columns
    op.drop_column('trigger', 'expires_at')
    op.drop_column('trigger', 'action_taken_at')
    op.drop_column('trigger', 'user_action')
    op.drop_column('trigger', 'viewed_at')
    op.drop_column('trigger', 'user_viewed')
    op.drop_column('trigger', 'notification_sent_at')
    op.drop_column('trigger', 'notification_sent')
    op.drop_column('trigger', 'current_value')
    op.drop_column('trigger', 'threshold_value')
    op.drop_column('trigger', 'triggered_at')
    op.drop_column('trigger', 'reason')
    op.drop_column('trigger', 'status')

    # Drop enums
    sa.Enum(name='user_action_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='trigger_status_enum').drop(op.get_bind(), checkfirst=True)
