"""Add video and engagement tables.

Revision ID: 003
Revises: 002
Create Date: 2024-08-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Videos table
    op.create_table(
        'videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('hashtags', sa.String(500), nullable=True),
        sa.Column('music_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='published'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allow_comments', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_duets', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_stitches', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('likes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shares_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bookmarks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_rate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_watch_time', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_videos_user_id'), 'videos', ['user_id'], unique=False)
    op.create_index(op.f('ix_videos_status'), 'videos', ['status'], unique=False)
    op.create_index(op.f('ix_videos_created_at'), 'videos', ['created_at'], unique=False)
    op.create_index(op.f('ix_videos_published_at'), 'videos', ['published_at'], unique=False)

    # Likes table
    op.create_table(
        'likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'video_id', name='unique_user_video_like'),
    )
    op.create_index(op.f('ix_likes_user_id'), 'likes', ['user_id'], unique=False)
    op.create_index(op.f('ix_likes_video_id'), 'likes', ['video_id'], unique=False)

    # Bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'video_id', name='unique_user_video_bookmark'),
    )
    op.create_index(op.f('ix_bookmarks_user_id'), 'bookmarks', ['user_id'], unique=False)
    op.create_index(op.f('ix_bookmarks_video_id'), 'bookmarks', ['video_id'], unique=False)

    # Views table
    op.create_table(
        'views',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('watch_time', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_views_user_id'), 'views', ['user_id'], unique=False)
    op.create_index(op.f('ix_views_video_id'), 'views', ['video_id'], unique=False)
    op.create_index(op.f('ix_views_created_at'), 'views', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('views')
    op.drop_table('bookmarks')
    op.drop_table('likes')
    op.drop_table('videos')
