"""Add AI Creator Studio tables

Revision ID: 006
Revises: 005
Create Date: 2024-08-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_generations table
    op.create_table(
        'ai_generations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('input_data', sa.String(2000), nullable=True),
        sa.Column('output_data', sa.String(5000), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('credits_used', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ai_generations_user_id', 'ai_generations', ['user_id'])
    op.create_index('ix_ai_generations_draft_id', 'ai_generations', ['draft_id'])
    op.create_index('ix_ai_generations_status', 'ai_generations', ['status'])

    # Create background_removals table
    op.create_table(
        'background_removals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_generation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False),
        sa.Column('blur_level', sa.Integer(), default=5, nullable=False),
        sa.Column('background_url', sa.String(500), nullable=True),
        sa.Column('background_type', sa.String(50), nullable=True),
        sa.Column('output_url', sa.String(500), nullable=True),
        sa.Column('preview_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_generation_id'], ['ai_generations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_background_removals_segment_id', 'background_removals', ['segment_id'])

    # Create voiceovers table
    op.create_table(
        'voiceovers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_generation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(20), default='en', nullable=False),
        sa.Column('voice_id', sa.String(50), nullable=False),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('emotion', sa.String(50), nullable=True),
        sa.Column('speed', sa.Integer(), default=100, nullable=False),
        sa.Column('pitch', sa.Integer(), default=100, nullable=False),
        sa.Column('volume', sa.Integer(), default=100, nullable=False),
        sa.Column('audio_url', sa.String(500), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_generation_id'], ['ai_generations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_voiceovers_segment_id', 'voiceovers', ['segment_id'])
    op.create_index('ix_voiceovers_language', 'voiceovers', ['language'])

    # Create auto_captions table
    op.create_table(
        'auto_captions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_generation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(20), default='en', nullable=False),
        sa.Column('style', sa.String(50), default='default', nullable=False),
        sa.Column('font_family', sa.String(100), default='Arial', nullable=False),
        sa.Column('font_size', sa.Integer(), default=24, nullable=False),
        sa.Column('color', sa.String(7), default='#FFFFFF', nullable=False),
        sa.Column('background_color', sa.String(7), nullable=True),
        sa.Column('position', sa.String(50), default='bottom', nullable=False),
        sa.Column('captions_data', sa.String(5000), nullable=True),
        sa.Column('vtt_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_generation_id'], ['ai_generations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_auto_captions_segment_id', 'auto_captions', ['segment_id'])
    op.create_index('ix_auto_captions_language', 'auto_captions', ['language'])

    # Create sound_recommendations table
    op.create_table(
        'sound_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sound_url', sa.String(500), nullable=False),
        sa.Column('sound_title', sa.String(255), nullable=False),
        sa.Column('artist', sa.String(255), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('mood', sa.String(50), nullable=True),
        sa.Column('genre', sa.String(50), nullable=True),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('is_trending', sa.Boolean(), default=False, nullable=False),
        sa.Column('license_type', sa.String(50), nullable=False),
        sa.Column('credit_required', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_sound_recommendations_user_id', 'sound_recommendations', ['user_id'])
    op.create_index('ix_sound_recommendations_draft_id', 'sound_recommendations', ['draft_id'])
    op.create_index('ix_sound_recommendations_mood', 'sound_recommendations', ['mood'])

    # Create color_corrections table
    op.create_table(
        'color_corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_generation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('preset_name', sa.String(100), nullable=True),
        sa.Column('brightness', sa.Integer(), default=0, nullable=False),
        sa.Column('contrast', sa.Integer(), default=0, nullable=False),
        sa.Column('saturation', sa.Integer(), default=0, nullable=False),
        sa.Column('hue', sa.Integer(), default=0, nullable=False),
        sa.Column('temperature', sa.Integer(), default=0, nullable=False),
        sa.Column('output_url', sa.String(500), nullable=True),
        sa.Column('preview_url', sa.String(500), nullable=True),
        sa.Column('lut_file_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_generation_id'], ['ai_generations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_color_corrections_segment_id', 'color_corrections', ['segment_id'])

    # Create auto_frames table
    op.create_table(
        'auto_frames',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_generation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_aspect_ratio', sa.String(20), nullable=False),
        sa.Column('detected_objects', sa.String(500), nullable=True),
        sa.Column('crop_x', sa.Integer(), nullable=False),
        sa.Column('crop_y', sa.Integer(), nullable=False),
        sa.Column('crop_width', sa.Integer(), nullable=False),
        sa.Column('crop_height', sa.Integer(), nullable=False),
        sa.Column('alternative_crops', sa.String(1000), nullable=True),
        sa.Column('output_url', sa.String(500), nullable=True),
        sa.Column('preview_url', sa.String(500), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_generation_id'], ['ai_generations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_auto_frames_segment_id', 'auto_frames', ['segment_id'])

    # Create trend_suggestions table
    op.create_table(
        'trend_suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trend_type', sa.String(50), nullable=False, index=True),
        sa.Column('trend_value', sa.String(255), nullable=False),
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('popularity_score', sa.Integer(), nullable=False),
        sa.Column('growth_rate', sa.Integer(), nullable=True),
        sa.Column('recommended_duration', sa.Integer(), nullable=True),
        sa.Column('best_posting_time', sa.String(50), nullable=True),
        sa.Column('related_trends', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_trend_suggestions_user_id', 'trend_suggestions', ['user_id'])
    op.create_index('ix_trend_suggestions_draft_id', 'trend_suggestions', ['draft_id'])
    op.create_index('ix_trend_suggestions_region', 'trend_suggestions', ['region'])


def downgrade() -> None:
    op.drop_index('ix_trend_suggestions_region', table_name='trend_suggestions')
    op.drop_index('ix_trend_suggestions_trend_type', table_name='trend_suggestions')
    op.drop_index('ix_trend_suggestions_draft_id', table_name='trend_suggestions')
    op.drop_index('ix_trend_suggestions_user_id', table_name='trend_suggestions')
    op.drop_table('trend_suggestions')

    op.drop_index('ix_auto_frames_segment_id', table_name='auto_frames')
    op.drop_table('auto_frames')

    op.drop_index('ix_color_corrections_segment_id', table_name='color_corrections')
    op.drop_table('color_corrections')

    op.drop_index('ix_sound_recommendations_mood', table_name='sound_recommendations')
    op.drop_index('ix_sound_recommendations_category', table_name='sound_recommendations')
    op.drop_index('ix_sound_recommendations_draft_id', table_name='sound_recommendations')
    op.drop_index('ix_sound_recommendations_user_id', table_name='sound_recommendations')
    op.drop_table('sound_recommendations')

    op.drop_index('ix_auto_captions_language', table_name='auto_captions')
    op.drop_index('ix_auto_captions_segment_id', table_name='auto_captions')
    op.drop_table('auto_captions')

    op.drop_index('ix_voiceovers_language', table_name='voiceovers')
    op.drop_index('ix_voiceovers_segment_id', table_name='voiceovers')
    op.drop_table('voiceovers')

    op.drop_index('ix_background_removals_segment_id', table_name='background_removals')
    op.drop_table('background_removals')

    op.drop_index('ix_ai_generations_status', table_name='ai_generations')
    op.drop_index('ix_ai_generations_operation_type', table_name='ai_generations')
    op.drop_index('ix_ai_generations_draft_id', table_name='ai_generations')
    op.drop_index('ix_ai_generations_user_id', table_name='ai_generations')
    op.drop_table('ai_generations')
