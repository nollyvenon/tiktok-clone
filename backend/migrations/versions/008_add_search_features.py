"""Add search and discovery features (Module 8)

Revision ID: 008
Revises: 007
Create Date: 2026-08-01 00:00:00.000000

Note: This module adds search features using existing tables (videos, users)
No new tables required for basic search functionality.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add full-text search indexes to videos table for search performance
    op.create_index('ix_videos_title', 'videos', ['title'])
    op.create_index('ix_videos_description', 'videos', ['description'])
    op.create_index('ix_videos_hashtags', 'videos', ['hashtags'])

    # Add index for creator search
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_first_name', 'users', ['first_name'])
    op.create_index('ix_users_last_name', 'users', ['last_name'])

    # Add index for trending/popular sorting
    op.create_index('ix_videos_views_published', 'videos', ['views_count', 'published_at'])
    op.create_index('ix_videos_likes_published', 'videos', ['likes_count', 'published_at'])


def downgrade():
    op.drop_index('ix_videos_likes_published')
    op.drop_index('ix_videos_views_published')
    op.drop_index('ix_users_last_name')
    op.drop_index('ix_users_first_name')
    op.drop_index('ix_users_username')
    op.drop_index('ix_videos_hashtags')
    op.drop_index('ix_videos_description')
    op.drop_index('ix_videos_title')
