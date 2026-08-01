"""Add video editor tables

Revision ID: 005
Revises: 004
Create Date: 2024-08-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create edits table
    op.create_table(
        'edits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('start_time', sa.Integer(), nullable=True),
        sa.Column('end_time', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('parameters', postgresql.JSON(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('applied', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_edits_draft_id', 'edits', ['draft_id'])
    op.create_index('ix_edits_user_id', 'edits', ['user_id'])
    op.create_index('ix_edits_operation_type', 'edits', ['operation_type'])

    # Create segments table
    op.create_table(
        'segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.Integer(), nullable=False),
        sa.Column('end_time', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=False),
        sa.Column('effects', postgresql.JSON(), nullable=True),
        sa.Column('transition_type', sa.String(50), nullable=True),
        sa.Column('transition_duration', sa.Integer(), default=300, nullable=False),
        sa.Column('volume', sa.Integer(), default=100, nullable=False),
        sa.Column('muted', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_segments_draft_id', 'segments', ['draft_id'])
    op.create_index('ix_segments_order', 'segments', ['draft_id', 'order'])

    # Create text_overlays table
    op.create_table(
        'text_overlays',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.String(500), nullable=False),
        sa.Column('font_family', sa.String(100), default='Arial', nullable=False),
        sa.Column('font_size', sa.Integer(), default=24, nullable=False),
        sa.Column('color', sa.String(20), default='#FFFFFF', nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('animation_type', sa.String(50), nullable=True),
        sa.Column('animation_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_text_overlays_segment_id', 'text_overlays', ['segment_id'])

    # Create stickers table
    op.create_table(
        'stickers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sticker_url', sa.String(500), nullable=False),
        sa.Column('sticker_type', sa.String(50), nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('rotation', sa.Integer(), default=0, nullable=False),
        sa.Column('animation_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_stickers_segment_id', 'stickers', ['segment_id'])
    op.create_index('ix_stickers_sticker_type', 'stickers', ['sticker_type'])


def downgrade() -> None:
    op.drop_index('ix_stickers_sticker_type', table_name='stickers')
    op.drop_index('ix_stickers_segment_id', table_name='stickers')
    op.drop_table('stickers')

    op.drop_index('ix_text_overlays_segment_id', table_name='text_overlays')
    op.drop_table('text_overlays')

    op.drop_index('ix_segments_order', table_name='segments')
    op.drop_index('ix_segments_draft_id', table_name='segments')
    op.drop_table('segments')

    op.drop_index('ix_edits_operation_type', table_name='edits')
    op.drop_index('ix_edits_user_id', table_name='edits')
    op.drop_index('ix_edits_draft_id', table_name='edits')
    op.drop_table('edits')
