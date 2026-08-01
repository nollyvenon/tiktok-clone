"""Add upload and draft tables.

Revision ID: 004
Revises: 003
Create Date: 2024-08-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Uploads table
    op.create_table(
        'uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='uploading'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_video_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_uploads_user_id'), 'uploads', ['user_id'], unique=False)
    op.create_index(op.f('ix_uploads_status'), 'uploads', ['status'], unique=False)

    # Drafts table
    op.create_table(
        'drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hashtags', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_comments', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_duets', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_stitches', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(50), nullable=False, server_default='editing'),
        sa.Column('scheduled_publish_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_drafts_user_id'), 'drafts', ['user_id'], unique=False)
    op.create_index(op.f('ix_drafts_status'), 'drafts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('drafts')
    op.drop_table('uploads')
