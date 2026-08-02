"""Make views.user_id nullable for anonymous view tracking

Anonymous (unauthenticated) view tracking previously inserted a fabricated
all-zero UUID as user_id to satisfy the NOT NULL constraint, referencing a
user row that never existed. This passed silently in SQLite tests (which
don't enforce foreign keys by default) but would raise a ForeignKeyViolation
against the real Postgres database on every anonymous view.

Revision ID: 015
Revises: 014
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('views', 'user_id', existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade():
    # Not reversible without deciding what to do with existing anonymous
    # (NULL) rows - left as a manual step if ever needed.
    pass
