"""Add duet/stitch remix columns to videos and drafts (Modules 19-20)

Revision ID: 014
Revises: 013
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    remix_type_enum = postgresql.ENUM('duet', 'stitch', name='remixtype')
    remix_type_enum.create(op.get_bind(), checkfirst=True)
    remix_type_col = sa.Enum('duet', 'stitch', name='remixtype')

    op.add_column('videos', sa.Column('original_video_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('videos', sa.Column('remix_type', remix_type_col, nullable=True))
    op.create_foreign_key(
        'fk_videos_original_video_id', 'videos', 'videos', ['original_video_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_videos_original_video_id', 'videos', ['original_video_id'])

    op.add_column('drafts', sa.Column('original_video_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('drafts', sa.Column('remix_type', sa.Enum('duet', 'stitch', name='remixtype', create_type=False), nullable=True))
    op.create_foreign_key(
        'fk_drafts_original_video_id', 'drafts', 'videos', ['original_video_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_drafts_original_video_id', 'drafts', type_='foreignkey')
    op.drop_column('drafts', 'remix_type')
    op.drop_column('drafts', 'original_video_id')

    op.drop_index('ix_videos_original_video_id', table_name='videos')
    op.drop_constraint('fk_videos_original_video_id', 'videos', type_='foreignkey')
    op.drop_column('videos', 'remix_type')
    op.drop_column('videos', 'original_video_id')
    postgresql.ENUM(name='remixtype').drop(op.get_bind(), checkfirst=True)
