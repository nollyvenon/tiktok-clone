"""
Database models for the TikTok Clone application
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Enum, UniqueConstraint, Float, CheckConstraint
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
    TIKTOK = "tiktok"


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


class RemixType(str, enum.Enum):
    """How a video relates to the original it references, if any"""
    DUET = "duet"
    STITCH = "stitch"


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
    music_id = Column(UUID(as_uuid=True), ForeignKey("sound_recommendations.id", ondelete="SET NULL"), nullable=True, index=True)
    location = Column(String(255), nullable=True)

    # Duets & Stitches: this video is a remix of original_video_id, of the
    # given type. Both null for an original (non-remix) upload.
    original_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    remix_type = Column(Enum(RemixType), nullable=True)

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
    # Nullable: views can be tracked for anonymous (unauthenticated) requests
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
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


class UploadStatus(str, enum.Enum):
    """Upload status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Upload(Base):
    """Video uploads in progress"""
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Upload info
    original_filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Bytes
    mime_type = Column(String(100), nullable=False)  # video/mp4, etc.
    storage_path = Column(String(500), nullable=False)  # S3 or local path

    # Processing
    status = Column(Enum(UploadStatus), default=UploadStatus.UPLOADING, nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)  # 0-100%
    error_message = Column(Text, nullable=True)

    # Processing results
    processed_video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=True)  # Seconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class DraftStatus(str, enum.Enum):
    """Draft status"""
    EDITING = "editing"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"


class Draft(Base):
    """Video drafts for creators"""
    __tablename__ = "drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)

    # Draft content
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    hashtags = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Settings
    is_public = Column(Boolean, default=True, nullable=False)
    allow_comments = Column(Boolean, default=True, nullable=False)
    allow_duets = Column(Boolean, default=True, nullable=False)
    allow_stitches = Column(Boolean, default=True, nullable=False)

    # Duets & Stitches: set both to publish this draft as a remix of an
    # existing video. Validated at publish time (RemixType is defined on
    # Video, reused here rather than duplicated).
    original_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    remix_type = Column(Enum(RemixType), nullable=True)

    # Music Library: sound attached to this video (from sound_recommendations,
    # which doubles as the shared library catalog)
    music_id = Column(UUID(as_uuid=True), ForeignKey("sound_recommendations.id", ondelete="SET NULL"), nullable=True)

    # Status
    status = Column(Enum(DraftStatus), default=DraftStatus.EDITING, nullable=False, index=True)
    scheduled_publish_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_video_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to published video

    # Relationships
    edits = relationship("Edit", back_populates="draft", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="draft", cascade="all, delete-orphan")


class Edit(Base):
    """Video editing operations and timeline"""
    __tablename__ = "edits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Editing operations
    operation_type = Column(String(50), nullable=False)  # trim, split, merge, crop, rotate, speed, reverse
    start_time = Column(Integer, nullable=True)  # Milliseconds
    end_time = Column(Integer, nullable=True)  # Milliseconds
    duration = Column(Integer, nullable=True)  # Milliseconds

    # Operation parameters (JSON for flexibility)
    parameters = Column(String(2000), nullable=True)  # JSON string with operation params

    # Status
    order = Column(Integer, nullable=False)  # Order in timeline
    applied = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    draft = relationship("Draft", back_populates="edits")


class Segment(Base):
    """Video segments with effects and transitions"""
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Segment timing
    start_time = Column(Integer, nullable=False)  # Milliseconds
    end_time = Column(Integer, nullable=False)  # Milliseconds
    order = Column(Integer, nullable=False)  # Order in timeline

    # Content
    content_type = Column(String(50), nullable=False)  # video, image, text, music, voiceover
    content_url = Column(String(500), nullable=False)  # URL to content

    # Effects (JSON array)
    effects = Column(String(2000), nullable=True)  # JSON array of applied effects

    # Transition (to next segment)
    transition_type = Column(String(50), nullable=True)  # fade, slide, zoom, dissolve, etc.
    transition_duration = Column(Integer, default=300, nullable=False)  # Milliseconds

    # Volume
    volume = Column(Integer, default=100, nullable=False)  # 0-100%
    muted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    draft = relationship("Draft", back_populates="segments")


class TextOverlay(Base):
    """Text overlays on video"""
    __tablename__ = "text_overlays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Text content
    text = Column(Text, nullable=False)
    font_family = Column(String(100), default="Arial", nullable=False)
    font_size = Column(Integer, default=24, nullable=False)
    color = Column(String(7), default="#FFFFFF", nullable=False)  # Hex color

    # Position & size
    x = Column(Integer, nullable=False)  # Pixels
    y = Column(Integer, nullable=False)  # Pixels
    width = Column(Integer, nullable=False)  # Pixels
    height = Column(Integer, nullable=False)  # Pixels

    # Animation
    animation_type = Column(String(50), nullable=True)  # fadeIn, slideIn, typewriter, etc.
    animation_duration = Column(Integer, nullable=True)  # Milliseconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Sticker(Base):
    """Stickers applied to video"""
    __tablename__ = "stickers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sticker info
    sticker_url = Column(String(500), nullable=False)
    sticker_type = Column(String(50), nullable=False)  # emoji, gif, effect, etc.

    # Position & size
    x = Column(Integer, nullable=False)  # Pixels
    y = Column(Integer, nullable=False)  # Pixels
    width = Column(Integer, nullable=False)  # Pixels
    height = Column(Integer, nullable=False)  # Pixels
    rotation = Column(Integer, default=0, nullable=False)  # Degrees

    # Animation
    animation_type = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AIGenerationStatus(str, enum.Enum):
    """Status of AI generation operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AIGeneration(Base):
    """AI generation operations tracking"""
    __tablename__ = "ai_generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Operation details
    operation_type = Column(String(50), nullable=False, index=True)  # voiceover, caption, background, etc.
    status = Column(Enum(AIGenerationStatus), default=AIGenerationStatus.PENDING, nullable=False)

    # Parameters and results
    input_data = Column(String(2000), nullable=True)  # JSON input parameters
    output_data = Column(String(5000), nullable=True)  # JSON output/result
    error_message = Column(String(500), nullable=True)  # Error details if failed

    # Credit tracking
    credits_used = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="ai_generations")
    draft = relationship("Draft", backref="ai_generations")


class BackgroundRemoval(Base):
    """Background removal/replacement operations"""
    __tablename__ = "background_removals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_generation_id = Column(UUID(as_uuid=True), ForeignKey("ai_generations.id", ondelete="CASCADE"), nullable=False)

    # Operation mode
    mode = Column(String(50), nullable=False)  # blur, remove, replace, green_screen
    blur_level = Column(Integer, default=5, nullable=False)  # 0-10 for blur

    # Replace background
    background_url = Column(String(500), nullable=True)  # URL to replacement background
    background_type = Column(String(50), nullable=True)  # image, video, color, blur

    # Results
    output_url = Column(String(500), nullable=True)  # Processed video/image URL
    preview_url = Column(String(500), nullable=True)  # Preview thumbnail

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("Segment", backref="background_removals")


class Voiceover(Base):
    """Text-to-speech voiceover generation"""
    __tablename__ = "voiceovers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_generation_id = Column(UUID(as_uuid=True), ForeignKey("ai_generations.id", ondelete="CASCADE"), nullable=False)

    # Text input
    text = Column(Text, nullable=False)

    # Voice configuration
    language = Column(String(20), default="en", nullable=False)  # en, es, fr, de, etc.
    voice_id = Column(String(50), nullable=False)  # Specific voice identifier
    gender = Column(String(20), nullable=True)  # male, female, neutral
    emotion = Column(String(50), nullable=True)  # happy, sad, angry, neutral, etc.

    # Audio properties
    speed = Column(Integer, default=100, nullable=False)  # 50-200% (100 = normal)
    pitch = Column(Integer, default=100, nullable=False)  # 50-200% (100 = normal)
    volume = Column(Integer, default=100, nullable=False)  # 0-100%

    # Results
    audio_url = Column(String(500), nullable=True)  # Generated audio file URL
    duration = Column(Integer, nullable=True)  # Audio duration in milliseconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("Segment", backref="voiceovers")


class AutoCaption(Base):
    """Auto-generated captions/subtitles"""
    __tablename__ = "auto_captions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_generation_id = Column(UUID(as_uuid=True), ForeignKey("ai_generations.id", ondelete="CASCADE"), nullable=False)

    # Caption configuration
    language = Column(String(20), default="en", nullable=False)
    style = Column(String(50), default="default", nullable=False)  # default, bold, shadow, background, etc.

    # Styling
    font_family = Column(String(100), default="Arial", nullable=False)
    font_size = Column(Integer, default=24, nullable=False)
    color = Column(String(7), default="#FFFFFF", nullable=False)  # Hex color
    background_color = Column(String(7), nullable=True)

    # Position
    position = Column(String(50), default="bottom", nullable=False)  # top, middle, bottom

    # Results
    captions_data = Column(String(5000), nullable=True)  # JSON array of caption objects
    vtt_url = Column(String(500), nullable=True)  # WebVTT subtitle file URL

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("Segment", backref="auto_captions")


class SoundRecommendation(Base):
    """
    Sounds/music in the shared library. Despite the historical name, this
    doubles as the Music Library catalog - entries aren't tied to any one
    draft, they're contributed to (and browsed from) a shared catalog.
    """
    __tablename__ = "sound_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sound details
    sound_url = Column(String(500), nullable=False)
    sound_title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)  # background, sound_effect, music, etc.
    mood = Column(String(50), nullable=True)  # happy, sad, epic, calm, energetic, etc.
    genre = Column(String(50), nullable=True)  # pop, rock, classical, etc.
    region = Column(String(50), nullable=True)  # trending in region

    # Properties
    duration = Column(Integer, nullable=True)  # Duration in milliseconds
    is_trending = Column(Boolean, default=False, nullable=False)

    # License info
    license_type = Column(String(50), nullable=False)  # royalty_free, creative_commons, etc.
    credit_required = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="sound_recommendations")


class ColorCorrection(Base):
    """AI color grading/correction"""
    __tablename__ = "color_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_generation_id = Column(UUID(as_uuid=True), ForeignKey("ai_generations.id", ondelete="CASCADE"), nullable=False)

    # Correction method
    method = Column(String(50), nullable=False)  # preset, auto_enhance, lut, custom
    preset_name = Column(String(100), nullable=True)  # cinematic, vintage, desaturated, etc.

    # Color adjustments
    brightness = Column(Integer, default=0, nullable=False)  # -100 to 100
    contrast = Column(Integer, default=0, nullable=False)  # -100 to 100
    saturation = Column(Integer, default=0, nullable=False)  # -100 to 100
    hue = Column(Integer, default=0, nullable=False)  # -180 to 180
    temperature = Column(Integer, default=0, nullable=False)  # -100 to 100 (warm to cool)

    # Results
    output_url = Column(String(500), nullable=True)  # Processed video URL
    preview_url = Column(String(500), nullable=True)  # Preview thumbnail
    lut_file_url = Column(String(500), nullable=True)  # LUT file if applicable

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("Segment", backref="color_corrections")


class AutoFrame(Base):
    """Smart framing suggestions"""
    __tablename__ = "auto_frames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_generation_id = Column(UUID(as_uuid=True), ForeignKey("ai_generations.id", ondelete="CASCADE"), nullable=False)

    # Framing configuration
    target_aspect_ratio = Column(String(20), nullable=False)  # 16:9, 9:16, 1:1, etc.
    detected_objects = Column(String(500), nullable=True)  # JSON array of detected objects

    # Suggested crop
    crop_x = Column(Integer, nullable=False)  # Starting X coordinate
    crop_y = Column(Integer, nullable=False)  # Starting Y coordinate
    crop_width = Column(Integer, nullable=False)  # Crop width
    crop_height = Column(Integer, nullable=False)  # Crop height

    # Alternatives
    alternative_crops = Column(String(1000), nullable=True)  # JSON array of alternative crops

    # Results
    output_url = Column(String(500), nullable=True)  # Framed video/image URL
    preview_url = Column(String(500), nullable=True)  # Preview thumbnail
    confidence = Column(Integer, nullable=False)  # 0-100 confidence score

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    segment = relationship("Segment", backref="auto_frames")


class TrendSuggestion(Base):
    """AI trending content suggestions"""
    __tablename__ = "trend_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Trend details
    trend_type = Column(String(50), nullable=False, index=True)  # hashtag, sound, effect, format, etc.
    trend_value = Column(String(255), nullable=False)  # The actual trend (#TikTokDance, etc.)

    # Metadata
    region = Column(String(50), nullable=False)  # US, UK, Global, etc.
    popularity_score = Column(Integer, nullable=False)  # 0-100 based on current popularity
    growth_rate = Column(Integer, nullable=True)  # Positive/negative growth percentage

    # Usage recommendations
    recommended_duration = Column(Integer, nullable=True)  # Milliseconds for optimal engagement
    best_posting_time = Column(String(50), nullable=True)  # Time of day recommendation

    # Related trends
    related_trends = Column(String(500), nullable=True)  # JSON array of related trends

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # When trend expires

    # Relationships
    user = relationship("User", backref="trend_suggestions")
    draft = relationship("Draft", backref="trend_suggestions")


class Recommendation(Base):
    """Recommendation records for personalized feed"""
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Recommendation metadata
    score = Column(Float, nullable=False)  # 0-1 recommendation score
    algorithm = Column(String(50), nullable=False)  # collaborative, content_based, trending, etc.
    reason = Column(String(255), nullable=True)  # Why recommended (tags, creator, similar_to, etc.)

    # Feedback tracking
    shown = Column(Boolean, default=False, nullable=False)
    clicked = Column(Boolean, default=False, nullable=False)
    watched = Column(Boolean, default=False, nullable=False)
    liked = Column(Boolean, default=False, nullable=False)

    # Timestamps
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    shown_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="recommendations")
    video = relationship("Video", backref="recommendations")


class UserPreference(Base):
    """User viewing and engagement history for recommendations"""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Preference data (JSON for flexibility)
    preferred_creators = Column(String(2000), nullable=True)  # JSON array of creator IDs
    preferred_hashtags = Column(String(2000), nullable=True)  # JSON array of hashtags
    preferred_genres = Column(String(500), nullable=True)  # JSON array of genres
    preferred_languages = Column(String(500), nullable=True)  # JSON array of language codes

    # Engagement metrics
    avg_watch_time = Column(Integer, nullable=True)  # Average watch time in seconds
    content_diversity_score = Column(Float, default=0.5, nullable=False)  # 0-1 preference for diversity
    recency_preference = Column(Float, default=0.5, nullable=False)  # 0-1 preference for recent content

    # Model version
    model_version = Column(String(50), nullable=False, default="v1")

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="preferences")


class RecommendationFeedback(Base):
    """Feedback on recommendation quality for model improvement"""
    __tablename__ = "recommendation_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Feedback
    feedback_type = Column(String(50), nullable=False)  # relevant, irrelevant, duplicate, nsfw, not_interested
    rating = Column(Integer, nullable=True)  # 1-5 star rating if applicable

    # Explanation
    reason = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recommendation = relationship("Recommendation", backref="feedback")
    user = relationship("User", backref="recommendation_feedback")


class ABTest(Base):
    """A/B test configuration for recommendation algorithm testing"""
    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Test configuration
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False)  # algorithm, weights, ranking, etc.

    # Variants
    control_version = Column(String(50), nullable=False)  # Control algorithm version
    treatment_version = Column(String(50), nullable=False)  # Treatment algorithm version

    # Test parameters
    split_percentage = Column(Integer, default=50, nullable=False)  # Percentage of users in treatment

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    results_significant = Column(Boolean, nullable=True)  # Is result statistically significant?

    # Timestamps
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# MODULE 9: HASHTAG TRENDING SYSTEM
# ============================================================================

class HashtagTrend(Base):
    """Trending hashtag tracking"""
    __tablename__ = "hashtag_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashtag = Column(String(100), nullable=False, index=True)

    # Metrics
    usage_count = Column(Integer, default=0, nullable=False)
    unique_creators = Column(Integer, default=0, nullable=False)
    total_views = Column(Integer, default=0, nullable=False)
    total_likes = Column(Integer, default=0, nullable=False)

    # Ranking
    popularity_score = Column(Float, default=0.0, nullable=False)  # 0-100
    trend_velocity = Column(Float, default=0.0, nullable=False)  # Growth rate
    rank_position = Column(Integer, nullable=True)  # Daily/weekly rank

    # Metadata
    region = Column(String(50), nullable=False, index=True)  # US, UK, Global, etc
    category = Column(String(50), nullable=True)  # music, dance, comedy, etc
    is_challenge = Column(Boolean, default=False, nullable=False)
    challenge_rules = Column(Text, nullable=True)

    # Lifecycle
    peak_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class HashtagAnalytics(Base):
    """Hashtag usage analytics"""
    __tablename__ = "hashtag_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashtag = Column(String(100), nullable=False, index=True)

    # Daily metrics
    date = Column(DateTime, nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    unique_creators = Column(Integer, default=0, nullable=False)
    total_views = Column(Integer, default=0, nullable=False)
    total_engagement = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Challenge(Base):
    """Hashtag challenges"""
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashtag = Column(String(100), nullable=False, unique=True)

    # Challenge details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    prize_pool = Column(Integer, nullable=True)  # In cents

    # Images/video
    thumbnail_url = Column(String(500), nullable=True)
    demo_video_url = Column(String(500), nullable=True)

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    participation_count = Column(Integer, default=0, nullable=False)
    total_views = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================================
# MODULE 11: COMMENTS & REPLIES
# ============================================================================

class Comment(Base):
    """Video comments, with one level of threaded replies via parent_comment_id"""
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)

    content = Column(Text, nullable=False)

    likes_count = Column(Integer, default=0, nullable=False)
    replies_count = Column(Integer, default=0, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class CommentLike(Base):
    """Likes on comments"""
    __tablename__ = "comment_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='unique_comment_like'),
    )


# ============================================================================
# MODULE 14: DIRECT MESSAGING
# ============================================================================

class Conversation(Base):
    """
    A 1-on-1 conversation between two users. user1_id is always the
    lexicographically-smaller UUID of the pair - normalizing the order
    lets a unique constraint prevent duplicate conversations for the same
    pair regardless of who started it.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_conversation_pair'),
    )


class Message(Base):
    """A single message within a conversation"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)


# ============================================================================
# MODULE 10: NOTIFICATIONS SYSTEM
# ============================================================================

class NotificationType(str, enum.Enum):
    """Notification types"""
    FOLLOW = "follow"
    LIKE = "like"
    COMMENT = "comment"
    MENTION = "mention"
    SHARE = "share"
    REPLY = "reply"
    MESSAGE = "message"
    LIVE_START = "live_start"
    CREATOR_UPDATE = "creator_update"
    GIFT = "gift"
    DUET_STITCH = "duet_stitch"


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification details
    type = Column(Enum(NotificationType), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Who triggered it
    related_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)
    related_comment_id = Column(UUID(as_uuid=True), nullable=True)  # For comment notifications

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)

    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Channel preferences
    push_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    # Type preferences
    follow_notifications = Column(Boolean, default=True, nullable=False)
    like_notifications = Column(Boolean, default=True, nullable=False)
    comment_notifications = Column(Boolean, default=True, nullable=False)
    mention_notifications = Column(Boolean, default=True, nullable=False)
    message_notifications = Column(Boolean, default=True, nullable=False)

    # Email digest
    email_digest_enabled = Column(Boolean, default=True, nullable=False)
    email_digest_frequency = Column(String(50), default="daily")  # daily, weekly, never

    # Quiet hours
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# MODULE 26: MODERATION
# ============================================================================

class ReportedContentType(str, enum.Enum):
    """What kind of content a report targets"""
    VIDEO = "video"
    COMMENT = "comment"
    USER = "user"


class ReportReason(str, enum.Enum):
    """Why content was reported"""
    SPAM = "spam"
    HARASSMENT = "harassment"
    NUDITY = "nudity"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    SELF_HARM = "self_harm"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    """Lifecycle of a content report"""
    PENDING = "pending"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class ModerationActionType(str, enum.Enum):
    """What a moderator did in response to a report"""
    DISMISS = "dismiss"
    REMOVE_CONTENT = "remove_content"
    WARN_USER = "warn_user"
    SUSPEND_USER = "suspend_user"
    BAN_USER = "ban_user"


class ContentReport(Base):
    """
    A user-submitted report against a video, comment, or user. Exactly one
    of reported_video_id/reported_comment_id/reported_user_id is set,
    matching content_type - enforced by a CHECK constraint rather than a
    single polymorphic FK, since SQLAlchemy/Postgres have no native
    polymorphic foreign key.
    """
    __tablename__ = "content_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # values_callable: store the enum's lowercase .value ("video") rather
    # than SQLAlchemy's Enum-column default of the uppercase Python member
    # .name ("VIDEO") - the CHECK constraint below does raw-SQL string
    # comparison against .value, and without this it silently compares
    # against the wrong casing and fails on every insert.
    content_type = Column(
        Enum(ReportedContentType, values_callable=lambda e: [x.value for x in e]),
        nullable=False, index=True,
    )
    reported_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    reported_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    reported_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    reason = Column(Enum(ReportReason, values_callable=lambda e: [x.value for x in e]), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(ReportStatus, values_callable=lambda e: [x.value for x in e]),
        default=ReportStatus.PENDING, nullable=False, index=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "(content_type = 'video' AND reported_video_id IS NOT NULL AND reported_comment_id IS NULL AND reported_user_id IS NULL) OR "
            "(content_type = 'comment' AND reported_comment_id IS NOT NULL AND reported_video_id IS NULL AND reported_user_id IS NULL) OR "
            "(content_type = 'user' AND reported_user_id IS NOT NULL AND reported_video_id IS NULL AND reported_comment_id IS NULL)",
            name="ck_content_report_single_target",
        ),
    )


class ModerationDecision(Base):
    """A moderator's decision on a content report - the audit trail"""
    __tablename__ = "moderation_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("content_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    moderator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(Enum(ModerationActionType, values_callable=lambda e: [x.value for x in e]), nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# MODULE 27: CREATOR FUND
# ============================================================================

class FundingProgram(Base):
    """An admin-defined funding program creators can apply to"""
    __tablename__ = "funding_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Eligibility requirements, checked against the applicant's live stats
    min_followers = Column(Integer, default=0, nullable=False)
    min_published_videos = Column(Integer, default=0, nullable=False)
    min_total_views = Column(Integer, default=0, nullable=False)

    # Amount awarded to an approved applicant, in cents - credited to an
    # internal ledger only; this app has no real payment processor, so no
    # money actually moves.
    award_amount = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ApplicationStatus(str, enum.Enum):
    """Status of a creator's fund application"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CreatorApplication(Base):
    """A creator's application to a funding program, with the eligibility
    snapshot computed at application time and the admin's final decision"""
    __tablename__ = "creator_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("funding_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Eligibility snapshot at time of application - requirements can change
    # later without retroactively altering a pending application's basis
    followers_count = Column(Integer, nullable=False)
    published_videos_count = Column(Integer, nullable=False)
    total_views_count = Column(Integer, nullable=False)
    meets_requirements = Column(Boolean, nullable=False)

    status = Column(
        Enum(ApplicationStatus, values_callable=lambda e: [x.value for x in e]),
        default=ApplicationStatus.PENDING, nullable=False, index=True,
    )
    decision_reason = Column(Text, nullable=True)
    awarded_amount = Column(Integer, nullable=True)  # Cents, set on approval
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('program_id', 'user_id', name='unique_program_applicant'),
    )


# ============================================================================
# MODULE 29: COLLABORATIONS
# ============================================================================

class CollaborationStatus(str, enum.Enum):
    """Status of a team-content collaboration as a whole"""
    PENDING = "pending"    # Waiting on one or more invited collaborators
    ACTIVE = "active"      # Every collaborator has accepted
    CANCELLED = "cancelled"


class CollaboratorStatus(str, enum.Enum):
    """Status of a single collaborator's participation"""
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Collaboration(Base):
    """A team content-creation collaboration on a single video, with a
    revenue split agreed upfront among all collaborators"""
    __tablename__ = "collaborations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    initiator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)

    status = Column(
        Enum(CollaborationStatus, values_callable=lambda e: [x.value for x in e]),
        default=CollaborationStatus.PENDING, nullable=False, index=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    collaborators = relationship("Collaborator", cascade="all, delete-orphan")


class Collaborator(Base):
    """A single collaborator's revenue share and response on a
    collaboration - the initiator is included as a row with is_initiator
    set and starts pre-accepted, so the split always accounts for 100%
    of participants regardless of who invited whom."""
    __tablename__ = "collaborators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collaboration_id = Column(UUID(as_uuid=True), ForeignKey("collaborations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    revenue_split_percent = Column(Float, nullable=False)
    is_initiator = Column(Boolean, default=False, nullable=False)
    status = Column(
        Enum(CollaboratorStatus, values_callable=lambda e: [x.value for x in e]),
        default=CollaboratorStatus.INVITED, nullable=False, index=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('collaboration_id', 'user_id', name='unique_collaboration_participant'),
    )


# ============================================================================
# MODULE 21: VIDEO FILTERS
# ============================================================================

class FilterPreset(Base):
    """A named color-grade look, applied via the existing color correction
    pipeline (method='preset'). No GPU/AR processing exists in this app,
    so this covers color-grade filters honestly - beauty/AR face filters
    are out of scope without a real vision pipeline."""
    __tablename__ = "filter_presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)

    brightness = Column(Integer, default=0, nullable=False)  # -100 to 100
    contrast = Column(Integer, default=0, nullable=False)    # -100 to 100
    saturation = Column(Integer, default=0, nullable=False)  # -100 to 100
    hue = Column(Integer, default=0, nullable=False)         # -180 to 180
    temperature = Column(Integer, default=0, nullable=False) # -100 to 100

    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# MODULE 28: AI AGENTS
# ============================================================================

class AIAgent(Base):
    """A named 'recipe' that runs a fixed sequence of the existing AI
    Creator Studio operations (background removal, captions, color
    correction, smart framing) against a segment in one call. This app
    has no real LLM/agent-framework integration (no OPENAI_API_KEY is
    ever actually used), so 'agent execution' here means orchestrating
    the AI operations that already exist, not free-form LLM reasoning."""
    __tablename__ = "ai_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    label = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(Text, nullable=False)  # JSON array of {operation, params}

    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AgentExecutionStatus(str, enum.Enum):
    """Status of an agent's run against a segment"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentExecution(Base):
    """A single run of an AIAgent against a segment - the audit trail of
    which underlying AI operations ran, in what order, and what each one
    cost in credits."""
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(
        Enum(AgentExecutionStatus, values_callable=lambda e: [x.value for x in e]),
        default=AgentExecutionStatus.RUNNING, nullable=False, index=True,
    )
    steps_log = Column(Text, nullable=True)  # JSON array of per-step results
    total_credits_used = Column(Integer, default=0, nullable=False)
    error_message = Column(String(500), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
