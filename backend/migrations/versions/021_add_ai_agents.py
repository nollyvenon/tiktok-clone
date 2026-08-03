"""Add AI agents tables (Module 28)

Revision ID: 021
Revises: 020
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json
import uuid

revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None

AGENTS = [
    (
        "auto_polish",
        "Auto Polish",
        "Auto color correction plus smart framing for 9:16.",
        [
            {"operation": "color_correction", "params": {"method": "auto_enhance"}},
            {"operation": "smart_frame", "params": {"target_aspect_ratio": "9:16"}},
        ],
        0,
    ),
    (
        "caption_and_clean",
        "Caption & Clean",
        "Auto captions plus a blurred background cleanup.",
        [
            {"operation": "caption", "params": {"language": "en", "style": "default"}},
            {"operation": "background_removal", "params": {"mode": "blur", "blur_level": 5}},
        ],
        1,
    ),
    (
        "full_enhance",
        "Full Enhance",
        "Runs every AI Creator Studio operation in sequence: background cleanup, color correction, captions, and smart framing.",
        [
            {"operation": "background_removal", "params": {"mode": "blur", "blur_level": 5}},
            {"operation": "color_correction", "params": {"method": "auto_enhance"}},
            {"operation": "caption", "params": {"language": "en", "style": "default"}},
            {"operation": "smart_frame", "params": {"target_aspect_ratio": "9:16"}},
        ],
        2,
    ),
]


def upgrade():
    op.create_table(
        'ai_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('label', sa.String(150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('running', 'completed', 'failed', name='agentexecutionstatus'), nullable=False, server_default='running'),
        sa.Column('steps_log', sa.Text(), nullable=True),
        sa.Column('total_credits_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_agent_executions_agent_id', 'agent_executions', ['agent_id'])
    op.create_index('ix_agent_executions_user_id', 'agent_executions', ['user_id'])
    op.create_index('ix_agent_executions_segment_id', 'agent_executions', ['segment_id'])
    op.create_index('ix_agent_executions_status', 'agent_executions', ['status'])
    op.create_index('ix_agent_executions_started_at', 'agent_executions', ['started_at'])

    ai_agents = sa.table(
        'ai_agents',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('label', sa.String),
        sa.column('description', sa.Text),
        sa.column('steps', sa.Text),
        sa.column('sort_order', sa.Integer),
    )
    op.bulk_insert(ai_agents, [
        {
            "id": uuid.uuid4(),
            "name": name,
            "label": label,
            "description": description,
            "steps": json.dumps(steps),
            "sort_order": sort_order,
        }
        for name, label, description, steps, sort_order in AGENTS
    ])


def downgrade():
    op.drop_table('agent_executions')
    op.drop_table('ai_agents')
