"""Add collaboration tables (Module 29)

Revision ID: 019
Revises: 018
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'collaborations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initiator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('pending', 'active', 'cancelled', name='collaborationstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_collaborations_video_id', 'collaborations', ['video_id'])
    op.create_index('ix_collaborations_initiator_id', 'collaborations', ['initiator_id'])
    op.create_index('ix_collaborations_status', 'collaborations', ['status'])
    op.create_index('ix_collaborations_created_at', 'collaborations', ['created_at'])

    op.create_table(
        'collaborators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('collaboration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('revenue_split_percent', sa.Float(), nullable=False),
        sa.Column('is_initiator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.Enum('invited', 'accepted', 'declined', name='collaboratorstatus'), nullable=False, server_default='invited'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['collaboration_id'], ['collaborations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('collaboration_id', 'user_id', name='unique_collaboration_participant'),
    )
    op.create_index('ix_collaborators_collaboration_id', 'collaborators', ['collaboration_id'])
    op.create_index('ix_collaborators_user_id', 'collaborators', ['user_id'])
    op.create_index('ix_collaborators_status', 'collaborators', ['status'])


def downgrade():
    op.drop_table('collaborators')
    op.drop_table('collaborations')
