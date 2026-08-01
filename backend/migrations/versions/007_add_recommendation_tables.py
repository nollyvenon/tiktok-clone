"""Add recommendation engine tables

Revision ID: 007
Revises: 006
Create Date: 2024-08-02 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('algorithm', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('shown', sa.Boolean(), default=False, nullable=False),
        sa.Column('clicked', sa.Boolean(), default=False, nullable=False),
        sa.Column('watched', sa.Boolean(), default=False, nullable=False),
        sa.Column('liked', sa.Boolean(), default=False, nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('shown_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_recommendations_user_id', 'recommendations', ['user_id'])
    op.create_index('ix_recommendations_video_id', 'recommendations', ['video_id'])
    op.create_index('ix_recommendations_score', 'recommendations', ['score'], postgresql_using='BTREE')

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('preferred_creators', sa.String(2000), nullable=True),
        sa.Column('preferred_hashtags', sa.String(2000), nullable=True),
        sa.Column('preferred_genres', sa.String(500), nullable=True),
        sa.Column('preferred_languages', sa.String(500), nullable=True),
        sa.Column('avg_watch_time', sa.Integer(), nullable=True),
        sa.Column('content_diversity_score', sa.Float(), default=0.5, nullable=False),
        sa.Column('recency_preference', sa.Float(), default=0.5, nullable=False),
        sa.Column('model_version', sa.String(50), default='v1', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])

    # Create recommendation_feedback table
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_recommendation_feedback_recommendation_id', 'recommendation_feedback', ['recommendation_id'])
    op.create_index('ix_recommendation_feedback_user_id', 'recommendation_feedback', ['user_id'])
    op.create_index('ix_recommendation_feedback_type', 'recommendation_feedback', ['feedback_type'])

    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('control_version', sa.String(50), nullable=False),
        sa.Column('treatment_version', sa.String(50), nullable=False),
        sa.Column('split_percentage', sa.Integer(), default=50, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('results_significant', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_ab_tests_is_active', 'ab_tests', ['is_active'])
    op.create_index('ix_ab_tests_started_at', 'ab_tests', ['started_at'])


def downgrade() -> None:
    op.drop_index('ix_ab_tests_started_at', table_name='ab_tests')
    op.drop_index('ix_ab_tests_is_active', table_name='ab_tests')
    op.drop_table('ab_tests')

    op.drop_index('ix_recommendation_feedback_type', table_name='recommendation_feedback')
    op.drop_index('ix_recommendation_feedback_user_id', table_name='recommendation_feedback')
    op.drop_index('ix_recommendation_feedback_recommendation_id', table_name='recommendation_feedback')
    op.drop_table('recommendation_feedback')

    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')

    op.drop_index('ix_recommendations_score', table_name='recommendations')
    op.drop_index('ix_recommendations_video_id', table_name='recommendations')
    op.drop_index('ix_recommendations_user_id', table_name='recommendations')
    op.drop_table('recommendations')
