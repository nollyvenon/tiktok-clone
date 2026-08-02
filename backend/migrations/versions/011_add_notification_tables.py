"""Add notification tables (Module 10)

Revision ID: 011
Revises: 010
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'type',
            sa.Enum(
                'follow', 'like', 'comment', 'mention', 'share', 'reply', 'message',
                'live_start', 'creator_update', 'gift', 'duet_stitch',
                name='notificationtype',
            ),
            nullable=False,
        ),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_video_id'], ['videos.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])

    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('follow_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('like_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('comment_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mention_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('message_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_digest_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_digest_frequency', sa.String(50), nullable=True, server_default='daily'),
        sa.Column('quiet_hours_start', sa.String(5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(5), nullable=True),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    op.execute('DROP TYPE IF EXISTS notificationtype')
