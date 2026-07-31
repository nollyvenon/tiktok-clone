"""
Database models for the TikTok Clone application
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles in the system"""
    USER = "user"
    CREATOR = "creator"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and profiles"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)

    # Profile info
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_creator = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # 2FA
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255), nullable=True)

    # Account metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('email', 'deleted_at', name='unique_active_email'),
    )


class Session(Base):
    """Active user sessions for token management"""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(255), nullable=True, index=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Token info
    access_token_jti = Column(String(255), unique=True, nullable=False)
    refresh_token_jti = Column(String(255), unique=True, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


class OAuthProvider(str, enum.Enum):
    """Supported OAuth providers"""
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class OAuthToken(Base):
    """OAuth provider tokens for third-party authentication"""
    __tablename__ = "oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(Enum(OAuthProvider), nullable=False, index=True)
    provider_user_id = Column(String(255), nullable=False)

    # Tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), default="Bearer")

    # Expiration
    expires_in = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="oauth_tokens")

    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='unique_user_provider'),
    )


class PasswordReset(Base):
    """Password reset tokens for password recovery"""
    __tablename__ = "password_resets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24), nullable=False, index=True)


class OTPVerificationType(str, enum.Enum):
    """OTP verification types"""
    PHONE = "phone"
    EMAIL = "email"


class OTP(Base):
    """One-time passwords for two-factor authentication and phone verification"""
    __tablename__ = "otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    code = Column(String(6), nullable=False)
    verification_type = Column(Enum(OTPVerificationType), nullable=False, index=True)

    # Status
    is_verified = Column(Boolean, default=False, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10), nullable=False, index=True)
    verified_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'verification_type', name='unique_user_verification_type'),
    )
