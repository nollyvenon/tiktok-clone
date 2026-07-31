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


class Follow(Base):
    """User follow relationships"""
    __tablename__ = "follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_follower_following'),
    )


class Block(Base):
    """User block relationships"""
    __tablename__ = "blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    blocked_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='unique_blocker_blocked'),
    )


class Verification(Base):
    """User verification status (blue checkmarks)"""
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_type = Column(String(50), nullable=True)  # influencer, business, artist, etc.
    verified_by = Column(UUID(as_uuid=True), nullable=True)  # Admin user who verified

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)


class Badge(Base):
    """Achievement badges for users"""
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_type = Column(String(100), nullable=False)  # early_adopter, creator_fund, million_followers, etc.
    badge_name = Column(String(255), nullable=False)
    badge_icon_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'badge_type', name='unique_user_badge'),
    )


class VideoStatus(str, enum.Enum):
    """Video status"""
    DRAFT = "draft"
    PROCESSING = "processing"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Video(Base):
    """User videos"""
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds

    # Metadata
    hashtags = Column(String(500), nullable=True)  # Comma-separated
    music_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to music/sound
    location = Column(String(255), nullable=True)

    # Status & Visibility
    status = Column(Enum(VideoStatus), default=VideoStatus.DRAFT, nullable=False, index=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    allow_comments = Column(Boolean, default=True, nullable=False)
    allow_duets = Column(Boolean, default=True, nullable=False)
    allow_stitches = Column(Boolean, default=True, nullable=False)

    # Analytics (denormalized for performance)
    views_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    bookmarks_count = Column(Integer, default=0, nullable=False)

    # Engagement metrics
    completion_rate = Column(Integer, default=0, nullable=False)  # Percentage
    average_watch_time = Column(Integer, default=0, nullable=False)  # Seconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    likes = relationship("Like", back_populates="video", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="video", cascade="all, delete-orphan")
    views = relationship("View", back_populates="video", cascade="all, delete-orphan")


class Like(Base):
    """Video likes"""
    __tablename__ = "likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    video = relationship("Video", back_populates="likes")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='unique_user_video_like'),
    )


class Bookmark(Base):
    """Bookmarked/saved videos"""
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    video = relationship("Video", back_populates="bookmarks")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='unique_user_video_bookmark'),
    )


class View(Base):
    """Video views/watches for analytics"""
    __tablename__ = "views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Watch metrics
    watch_time = Column(Integer, default=0, nullable=False)  # Seconds watched
    completed = Column(Boolean, default=False, nullable=False)  # Did user watch to end?

    # Device info
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    platform = Column(String(50), nullable=True)  # iOS, Android, Web
    country = Column(String(2), nullable=True)  # ISO country code

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    video = relationship("Video", back_populates="views")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', 'created_at', name='unique_user_video_view_day'),
    )
