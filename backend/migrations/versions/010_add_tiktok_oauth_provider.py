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
    # oauth_tokens.provider was created as a plain VARCHAR(50) in migration
    # 001 (op.create_table used sa.Column('provider', sa.String(50), ...)),
    # not a native Postgres ENUM type - so there is no 'oauthprovider' type
    # to alter, and none is needed: a VARCHAR column already accepts any
    # string value up to its length, including 'tiktok'. This migration is
    # a no-op against the schema as it actually exists.
    pass


def downgrade():
    # PostgreSQL does not support removing enum values directly.
    # A downgrade would require recreating the type and column; left as a no-op
    # since removing 'tiktok' is not expected to be needed in practice.
    pass
