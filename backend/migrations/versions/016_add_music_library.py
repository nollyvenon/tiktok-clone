"""Add Music/Sound Library (Module 22): drop vestigial sound_recommendations.draft_id, add music_id on drafts/videos

sound_recommendations.draft_id was never actually read or written anywhere
in the codebase - every browse/trending query already treated this table as
a shared catalog, ignoring draft_id entirely. Keeping it (even nullable)
while adding drafts.music_id -> sound_recommendations.id would create a
circular foreign key between drafts and sound_recommendations that SQLite
cannot resolve for DROP/ALTER without extra ceremony, so it's removed
outright rather than worked around.

Revision ID: 016
Revises: 015
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_sound_recommendations_draft_id', table_name='sound_recommendations')
    op.drop_constraint('sound_recommendations_draft_id_fkey', 'sound_recommendations', type_='foreignkey')
    op.drop_column('sound_recommendations', 'draft_id')

    op.add_column('drafts', sa.Column('music_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_drafts_music_id', 'drafts', 'sound_recommendations', ['music_id'], ['id'], ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_videos_music_id', 'videos', 'sound_recommendations', ['music_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_videos_music_id', 'videos', ['music_id'])


def downgrade():
    op.drop_index('ix_videos_music_id', table_name='videos')
    op.drop_constraint('fk_videos_music_id', 'videos', type_='foreignkey')

    op.drop_constraint('fk_drafts_music_id', 'drafts', type_='foreignkey')
    op.drop_column('drafts', 'music_id')

    op.add_column('sound_recommendations', sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'sound_recommendations_draft_id_fkey', 'sound_recommendations', 'drafts', ['draft_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_sound_recommendations_draft_id', 'sound_recommendations', ['draft_id'])
