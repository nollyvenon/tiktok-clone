"""Add monetization tables (Module 18)

Revision ID: 023
Revises: 022
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'earnings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Enum('creator_fund', 'shop_order', name='earningsourcetype'), nullable=False),
        sa.Column('fund_application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('shop_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fund_application_id'], ['creator_applications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shop_order_id'], ['shop_orders.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "(source_type = 'creator_fund' AND fund_application_id IS NOT NULL AND shop_order_id IS NULL) OR "
            "(source_type = 'shop_order' AND shop_order_id IS NOT NULL AND fund_application_id IS NULL)",
            name='ck_earning_single_source',
        ),
    )
    op.create_index('ix_earnings_user_id', 'earnings', ['user_id'])
    op.create_index('ix_earnings_source_type', 'earnings', ['source_type'])
    op.create_index('ix_earnings_created_at', 'earnings', ['created_at'])

    op.create_table(
        'payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'cancelled', name='payoutstatus'), nullable=False, server_default='pending'),
        sa.Column('decided_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_payouts_user_id', 'payouts', ['user_id'])
    op.create_index('ix_payouts_status', 'payouts', ['status'])
    op.create_index('ix_payouts_requested_at', 'payouts', ['requested_at'])


def downgrade():
    op.drop_table('payouts')
    op.drop_table('earnings')
