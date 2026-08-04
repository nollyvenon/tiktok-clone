"""Add live streaming tables (Module 10)

Revision ID: 024
Revises: 023
Create Date: 2026-08-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'live_streams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('live', 'ended', name='livestreamstatus'), nullable=False, server_default='live'),
        sa.Column('viewer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('peak_viewer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_live_streams_creator_id', 'live_streams', ['creator_id'])
    op.create_index('ix_live_streams_status', 'live_streams', ['status'])
    op.create_index('ix_live_streams_started_at', 'live_streams', ['started_at'])

    op.create_table(
        'live_stream_viewers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('stream_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['stream_id'], ['live_streams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('stream_id', 'user_id', name='unique_stream_viewer'),
    )
    op.create_index('ix_live_stream_viewers_stream_id', 'live_stream_viewers', ['stream_id'])
    op.create_index('ix_live_stream_viewers_user_id', 'live_stream_viewers', ['user_id'])

    op.create_table(
        'live_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('stream_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['stream_id'], ['live_streams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_live_chat_messages_stream_id', 'live_chat_messages', ['stream_id'])
    op.create_index('ix_live_chat_messages_created_at', 'live_chat_messages', ['created_at'])


def downgrade():
    op.drop_table('live_chat_messages')
    op.drop_table('live_stream_viewers')
    op.drop_table('live_streams')
