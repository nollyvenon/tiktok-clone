"""Add tiktok value to oauthprovider enum

Revision ID: 010
Revises: 009
Create Date: 2026-08-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE oauthprovider ADD VALUE IF NOT EXISTS 'tiktok'")


def downgrade():
    # PostgreSQL does not support removing enum values directly.
    # A downgrade would require recreating the type and column; left as a no-op
    # since removing 'tiktok' is not expected to be needed in practice.
    pass
