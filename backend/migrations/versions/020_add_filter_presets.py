"""Add filter presets table (Module 21)

Revision ID: 020
Revises: 019
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None

PRESETS = [
    ("original", "Original", 0, 0, 0, 0, 0, 0),
    ("cinematic", "Cinematic", -5, 20, -10, 0, -15, 1),
    ("vintage", "Vintage", 5, -10, -30, 10, 20, 2),
    ("black_and_white", "Black & White", 0, 15, -100, 0, 0, 3),
    ("warm", "Warm", 5, 0, 10, 0, 30, 4),
    ("cool", "Cool", 0, 0, 5, 0, -30, 5),
    ("vivid", "Vivid", 5, 15, 35, 0, 0, 6),
    ("dramatic", "Dramatic", -10, 35, -15, 0, -10, 7),
]


def upgrade():
    op.create_table(
        'filter_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('brightness', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contrast', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('saturation', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hue', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('temperature', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    filter_presets = sa.table(
        'filter_presets',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('label', sa.String),
        sa.column('brightness', sa.Integer),
        sa.column('contrast', sa.Integer),
        sa.column('saturation', sa.Integer),
        sa.column('hue', sa.Integer),
        sa.column('temperature', sa.Integer),
        sa.column('sort_order', sa.Integer),
    )
    op.bulk_insert(filter_presets, [
        {
            "id": uuid.uuid4(),
            "name": name,
            "label": label,
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "hue": hue,
            "temperature": temperature,
            "sort_order": sort_order,
        }
        for name, label, brightness, contrast, saturation, hue, temperature, sort_order in PRESETS
    ])


def downgrade():
    op.drop_table('filter_presets')
