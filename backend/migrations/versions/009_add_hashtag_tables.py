"""Add hashtag trending and challenge tables

Revision ID: 009
Revises: 008
Create Date: 2026-08-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None
branch_labels = None
depends_on = None


def upgrade():
    # Create hashtag_trends table
    op.create_table(
        'hashtag_trends',
        sa.Column('id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('hashtag', sa.String(256), nullable=False),
        sa.Column('region', sa.String(10), nullable=False, server_default='US'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_creators', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('popularity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trend_velocity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rank_position', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('is_challenge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('challenge_rules', sa.Text(), nullable=True),
        sa.Column('peak_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_hashtag_trends_hashtag_region', 'hashtag_trends', ['hashtag', 'region'], unique=True)
    op.create_index('ix_hashtag_trends_region', 'hashtag_trends', ['region'])
    op.create_index('ix_hashtag_trends_rank', 'hashtag_trends', ['rank_position'])
    op.create_index('ix_hashtag_trends_category', 'hashtag_trends', ['category'])
    op.create_index('ix_hashtag_trends_popularity', 'hashtag_trends', ['popularity_score'])

    # Create hashtag_analytics table
    op.create_table(
        'hashtag_analytics',
        sa.Column('id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('hashtag', sa.String(256), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_creators', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_hashtag_analytics_hashtag_date', 'hashtag_analytics', ['hashtag', 'date'], unique=True)
    op.create_index('ix_hashtag_analytics_hashtag', 'hashtag_analytics', ['hashtag'])
    op.create_index('ix_hashtag_analytics_date', 'hashtag_analytics', ['date'])

    # Create challenges table
    op.create_table(
        'challenges',
        sa.Column('id', postgresql.UUID(), nullable=False, primary_key=True),
        sa.Column('hashtag', sa.String(256), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rules', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.String(512), nullable=True),
        sa.Column('demo_video_url', sa.String(512), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('prize_pool', sa.Integer(), nullable=True),
        sa.Column('participation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_challenges_hashtag', 'challenges', ['hashtag'])
    op.create_index('ix_challenges_is_active', 'challenges', ['is_active'])
    op.create_index('ix_challenges_dates', 'challenges', ['start_date', 'end_date'])


def downgrade():
    op.drop_table('challenges')
    op.drop_table('hashtag_analytics')
    op.drop_table('hashtag_trends')
