"""Initial schema with auth tables.

Revision ID: 001
Revises:
Create Date: 2024-08-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_creator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('two_factor_secret', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', 'deleted_at', name='unique_active_email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # Sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', sa.String(255), nullable=True),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('access_token_jti', sa.String(255), nullable=False),
        sa.Column('refresh_token_jti', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token_jti'),
        sa.UniqueConstraint('refresh_token_jti'),
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sessions_device_id'), 'sessions', ['device_id'], unique=False)
    op.create_index(op.f('ix_sessions_expires_at'), 'sessions', ['expires_at'], unique=False)

    # OAuthTokens table
    op.create_table(
        'oauth_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(50), nullable=False, server_default='Bearer'),
        sa.Column('expires_in', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='unique_user_provider'),
    )
    op.create_index(op.f('ix_oauth_tokens_user_id'), 'oauth_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_oauth_tokens_provider'), 'oauth_tokens', ['provider'], unique=False)

    # PasswordResets table
    op.create_table(
        'password_resets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index(op.f('ix_password_resets_user_id'), 'password_resets', ['user_id'], unique=False)
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=False)
    op.create_index(op.f('ix_password_resets_expires_at'), 'password_resets', ['expires_at'], unique=False)

    # OTPs table
    op.create_table(
        'otps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('verification_type', sa.String(50), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'verification_type', name='unique_user_verification_type'),
    )
    op.create_index(op.f('ix_otps_user_id'), 'otps', ['user_id'], unique=False)
    op.create_index(op.f('ix_otps_verification_type'), 'otps', ['verification_type'], unique=False)
    op.create_index(op.f('ix_otps_expires_at'), 'otps', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_table('otps')
    op.drop_table('password_resets')
    op.drop_table('oauth_tokens')
    op.drop_table('sessions')
    op.drop_table('users')
