"""Add creator fund tables (Module 27)

Revision ID: 018
Revises: 017
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'funding_programs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('min_followers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_published_videos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('award_amount', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'creator_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('program_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('followers_count', sa.Integer(), nullable=False),
        sa.Column('published_videos_count', sa.Integer(), nullable=False),
        sa.Column('total_views_count', sa.Integer(), nullable=False),
        sa.Column('meets_requirements', sa.Boolean(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='applicationstatus'), nullable=False, server_default='pending'),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('awarded_amount', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['program_id'], ['funding_programs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('program_id', 'user_id', name='unique_program_applicant'),
    )
    op.create_index('ix_creator_applications_program_id', 'creator_applications', ['program_id'])
    op.create_index('ix_creator_applications_user_id', 'creator_applications', ['user_id'])
    op.create_index('ix_creator_applications_status', 'creator_applications', ['status'])
    op.create_index('ix_creator_applications_created_at', 'creator_applications', ['created_at'])


def downgrade():
    op.drop_table('creator_applications')
    op.drop_table('funding_programs')
