"""Add moderation tables (Module 26)

Revision ID: 017
Revises: 016
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'content_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.Enum('video', 'comment', 'user', name='reportedcontenttype'), nullable=False),
        sa.Column('reported_video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reported_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reported_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'reason',
            sa.Enum('spam', 'harassment', 'nudity', 'violence', 'hate_speech', 'misinformation', 'self_harm', 'other', name='reportreason'),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'actioned', 'dismissed', name='reportstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "(content_type = 'video' AND reported_video_id IS NOT NULL AND reported_comment_id IS NULL AND reported_user_id IS NULL) OR "
            "(content_type = 'comment' AND reported_comment_id IS NOT NULL AND reported_video_id IS NULL AND reported_user_id IS NULL) OR "
            "(content_type = 'user' AND reported_user_id IS NOT NULL AND reported_video_id IS NULL AND reported_comment_id IS NULL)",
            name='ck_content_report_single_target',
        ),
    )
    op.create_index('ix_content_reports_reporter_id', 'content_reports', ['reporter_id'])
    op.create_index('ix_content_reports_content_type', 'content_reports', ['content_type'])
    op.create_index('ix_content_reports_reported_video_id', 'content_reports', ['reported_video_id'])
    op.create_index('ix_content_reports_reported_comment_id', 'content_reports', ['reported_comment_id'])
    op.create_index('ix_content_reports_reported_user_id', 'content_reports', ['reported_user_id'])
    op.create_index('ix_content_reports_status', 'content_reports', ['status'])
    op.create_index('ix_content_reports_created_at', 'content_reports', ['created_at'])

    op.create_table(
        'moderation_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('moderator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'action',
            sa.Enum('dismiss', 'remove_content', 'warn_user', 'suspend_user', 'ban_user', name='moderationactiontype'),
            nullable=False,
        ),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['content_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_moderation_decisions_report_id', 'moderation_decisions', ['report_id'])
    op.create_index('ix_moderation_decisions_moderator_id', 'moderation_decisions', ['moderator_id'])


def downgrade():
    op.drop_table('moderation_decisions')
    op.drop_table('content_reports')
