"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models import UserRole


# ============================================================================
# Authentication Schemas
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response after login/registration"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class PasswordResetRequest(BaseModel):
    """Password reset request (forgot password)"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class TwoFactorSetupRequest(BaseModel):
    """Enable 2FA request"""
    password: str


class TwoFactorVerifyRequest(BaseModel):
    """Verify 2FA code"""
    code: str


class OAuthAuthorizationRequest(BaseModel):
    """OAuth authorization request"""
    provider: str
    code: str
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request - exchanges an authorization code for app tokens"""
    provider: str
    code: str
    state: str
    redirect_uri: str


class SessionResponse(BaseModel):
    """Active session / device info"""
    id: UUID
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    is_current: bool = False
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class SessionsListResponse(BaseModel):
    """List of active sessions"""
    sessions: list[SessionResponse]


class PhoneRegisterRequest(BaseModel):
    """Phone-based registration request"""
    phone: str = Field(..., min_length=10, max_length=20)
    country_code: str = Field(default="+1")
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=3, max_length=50)


class SendOTPRequest(BaseModel):
    """Send OTP request"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    """Verify OTP code request"""
    code: str = Field(..., min_length=6, max_length=6)
    phone_number: Optional[str] = None
    email: Optional[str] = None


# ============================================================================
# User Schemas (Base Classes)
# ============================================================================

class UserBase(BaseModel):
    """Base user information"""
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    website: Optional[str] = None
    is_creator: bool = False

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response (public-facing)"""
    id: UUID
    is_verified: bool
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetailedResponse(UserBase):
    """Detailed user response (private profile)"""
    id: UUID
    is_verified: bool
    is_active: bool
    role: UserRole
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Profile Schemas
# ============================================================================

class UserPublicProfile(BaseModel):
    """Public user profile (minimal info)"""
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    is_verified: bool
    is_creator: bool

    class Config:
        from_attributes = True


class UserFullProfile(UserBase):
    """Full user profile with all details"""
    id: UUID
    is_verified: bool
    is_active: bool
    role: UserRole
    is_creator: bool
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=150)
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)


class ProfileStatistics(BaseModel):
    """User profile statistics"""
    followers_count: int
    following_count: int
    videos_count: int
    likes_count: int
    total_views: int


class FollowResponse(BaseModel):
    """Follow/Unfollow response"""
    is_following: bool
    followers_count: int
    following_count: int


class FollowListUser(BaseModel):
    """A user in a followers/following list, with mutual-follow context"""
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    is_verified: bool
    is_creator: bool
    is_following: bool = False
    is_followed_by: bool = False

    class Config:
        from_attributes = True


class FollowersResponse(BaseModel):
    """List of followers"""
    users: list[FollowListUser]
    total: int
    cursor: Optional[str] = None


class FollowingResponse(BaseModel):
    """List of following"""
    users: list[FollowListUser]
    total: int
    cursor: Optional[str] = None


class BlockResponse(BaseModel):
    """Block/Unblock response"""
    is_blocked: bool
    message: str


class BlockedUsersResponse(BaseModel):
    """List of blocked users"""
    users: list[UserPublicProfile]
    total: int


class VerificationBadge(BaseModel):
    """User verification badge"""
    is_verified: bool
    verification_type: Optional[str] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserBadge(BaseModel):
    """User achievement badge"""
    id: UUID
    badge_type: str
    badge_name: str
    badge_icon_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Complete profile response"""
    user: UserFullProfile
    statistics: ProfileStatistics
    verification: Optional[VerificationBadge] = None
    badges: list[UserBadge] = []
    is_following: bool = False
    is_blocked: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Video Schemas
# ============================================================================

class VideoCreate(BaseModel):
    """Create video request"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2200)
    video_url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    hashtags: Optional[str] = None
    music_id: Optional[UUID] = None
    location: Optional[str] = None
    is_public: bool = True
    allow_comments: bool = True
    allow_duets: bool = True
    allow_stitches: bool = True


class VideoUpdate(BaseModel):
    """Update video request"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2200)
    thumbnail_url: Optional[str] = None
    hashtags: Optional[str] = None
    is_public: Optional[bool] = None
    allow_comments: Optional[bool] = None
    allow_duets: Optional[bool] = None
    allow_stitches: Optional[bool] = None


class VideoResponse(BaseModel):
    """Video response"""
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    hashtags: Optional[str] = None
    location: Optional[str] = None
    is_public: bool
    views_count: int
    likes_count: int
    comments_count: int
    shares_count: int
    bookmarks_count: int
    completion_rate: int
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoDetailResponse(VideoResponse):
    """Detailed video response with user info"""
    user: UserPublicProfile
    is_liked: bool = False
    is_bookmarked: bool = False
    allow_comments: bool
    allow_duets: bool
    allow_stitches: bool

    class Config:
        from_attributes = True


class FeedResponse(BaseModel):
    """Video feed response"""
    videos: list[VideoDetailResponse]
    cursor: Optional[str] = None
    total: Optional[int] = None


class LikeResponse(BaseModel):
    """Like/unlike response"""
    is_liked: bool
    likes_count: int


class BookmarkResponse(BaseModel):
    """Bookmark/unbookmark response"""
    is_bookmarked: bool
    bookmarks_count: int


class ViewTrackingRequest(BaseModel):
    """Track video view request"""
    watch_time: int = Field(..., ge=0)
    completed: bool = False
    device_type: Optional[str] = None
    platform: Optional[str] = None
    country: Optional[str] = None


class VideoAnalytics(BaseModel):
    """Video analytics"""
    video_id: UUID
    views: int
    likes: int
    comments: int
    shares: int
    bookmarks: int
    completion_rate: float
    average_watch_time: int
    engagement_rate: float

    class Config:
        from_attributes = True


# ============================================================================
# Upload & Draft Schemas
# ============================================================================

class UploadResponse(BaseModel):
    """Upload response"""
    id: UUID
    status: str
    progress: int
    file_size: int
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    processed_video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DraftCreate(BaseModel):
    """Create/update draft"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2200)
    hashtags: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: bool = True
    allow_comments: bool = True
    allow_duets: bool = True
    allow_stitches: bool = True
    scheduled_publish_at: Optional[datetime] = None


class DraftResponse(BaseModel):
    """Draft response"""
    id: UUID
    upload_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: bool
    allow_comments: bool
    allow_duets: bool
    allow_stitches: bool
    status: str
    scheduled_publish_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishDraftRequest(BaseModel):
    """Publish draft request"""
    draft_id: UUID
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2200)
    hashtags: Optional[str] = None
    is_public: bool = True
    allow_comments: bool = True
    allow_duets: bool = True
    allow_stitches: bool = True


class UploadPresignedURLRequest(BaseModel):
    """Request presigned URL for upload"""
    filename: str
    file_size: int
    mime_type: str


class UploadPresignedURLResponse(BaseModel):
    """Presigned URL response"""
    upload_id: UUID
    presigned_url: str
    expires_in: int


# ============================================================================
# Editor Schemas
# ============================================================================

class EditOperation(BaseModel):
    """Video edit operation"""
    operation_type: str = Field(..., description="trim, split, merge, crop, rotate, speed, reverse")
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    parameters: Optional[dict] = None


class SegmentCreate(BaseModel):
    """Create video segment"""
    start_time: int = Field(..., ge=0, description="Start time in ms")
    end_time: int = Field(..., ge=0, description="End time in ms")
    content_type: str = Field(..., description="video, image, text, music, voiceover")
    content_url: str
    effects: Optional[list[str]] = None
    transition_type: Optional[str] = None
    transition_duration: int = 300
    volume: int = Field(100, ge=0, le=100)
    muted: bool = False


class SegmentResponse(BaseModel):
    """Segment response"""
    id: UUID
    start_time: int
    end_time: int
    order: int
    content_type: str
    content_url: str
    effects: Optional[list[str]] = None
    transition_type: Optional[str] = None
    transition_duration: int
    volume: int
    muted: bool
    created_at: datetime

    @field_validator("effects", mode="before")
    @classmethod
    def parse_effects_json(cls, v):
        """The `effects` column stores a JSON-encoded string; deserialize it here
        rather than at every call site that builds a SegmentResponse."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class TextOverlayCreate(BaseModel):
    """Create text overlay"""
    text: str = Field(..., max_length=500)
    font_family: str = "Arial"
    font_size: int = Field(24, ge=8, le=120)
    color: str = "#FFFFFF"
    x: int
    y: int
    width: int
    height: int
    animation_type: Optional[str] = None
    animation_duration: Optional[int] = None


class TextOverlayResponse(BaseModel):
    """Text overlay response"""
    id: UUID
    text: str
    font_family: str
    font_size: int
    color: str
    x: int
    y: int
    width: int
    height: int
    animation_type: Optional[str] = None
    animation_duration: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StickerCreate(BaseModel):
    """Create sticker"""
    sticker_url: str
    sticker_type: str
    x: int
    y: int
    width: int
    height: int
    rotation: int = 0
    animation_type: Optional[str] = None


class StickerResponse(BaseModel):
    """Sticker response"""
    id: UUID
    sticker_url: str
    sticker_type: str
    x: int
    y: int
    width: int
    height: int
    rotation: int
    animation_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EditorStateResponse(BaseModel):
    """Complete editor state"""
    draft_id: UUID
    segments: list[SegmentResponse]
    text_overlays: list[TextOverlayResponse]
    stickers: list[StickerResponse]
    total_duration: int


class ExportResponse(BaseModel):
    """Export response"""
    export_id: UUID
    draft_id: UUID
    quality: str
    format: str
    status: str
    progress: int
    preview_url: Optional[str] = None
    export_url: Optional[str] = None
    created_at: datetime


# ============================================================================
# AI Creator Studio Schemas
# ============================================================================

class AIGenerationResponse(BaseModel):
    """AI generation operation response"""
    id: UUID
    operation_type: str
    status: str
    credits_used: int
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BackgroundRemovalRequest(BaseModel):
    """Background removal request"""
    segment_id: UUID
    mode: str = Field(..., description="blur, remove, replace, green_screen")
    blur_level: int = Field(5, ge=0, le=10)
    background_url: Optional[str] = None
    background_type: Optional[str] = Field(None, description="image, video, color, blur")


class BackgroundRemovalResponse(BaseModel):
    """Background removal response"""
    id: UUID
    ai_generation_id: UUID
    mode: str
    blur_level: int
    output_url: Optional[str] = None
    preview_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceoverRequest(BaseModel):
    """Voiceover generation request"""
    segment_id: UUID
    text: str = Field(..., max_length=2000)
    language: str = Field("en", description="en, es, fr, de, ja, zh, etc.")
    voice_id: str
    gender: Optional[str] = Field(None, description="male, female, neutral")
    emotion: Optional[str] = Field(None, description="happy, sad, angry, neutral")
    speed: int = Field(100, ge=50, le=200)
    pitch: int = Field(100, ge=50, le=200)
    volume: int = Field(100, ge=0, le=100)


class VoiceoverResponse(BaseModel):
    """Voiceover response"""
    id: UUID
    ai_generation_id: UUID
    text: str
    language: str
    voice_id: str
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AutoCaptionRequest(BaseModel):
    """Auto-caption generation request"""
    segment_id: UUID
    language: str = Field("en", description="en, es, fr, de, ja, zh, etc.")
    style: str = Field("default", description="default, bold, shadow, background")
    font_family: str = "Arial"
    font_size: int = Field(24, ge=12, le=48)
    color: str = "#FFFFFF"
    background_color: Optional[str] = None
    position: str = Field("bottom", description="top, middle, bottom")


class CaptionSegment(BaseModel):
    """Individual caption segment"""
    start_time: int
    end_time: int
    text: str


class AutoCaptionResponse(BaseModel):
    """Auto-caption response"""
    id: UUID
    ai_generation_id: UUID
    language: str
    captions: list[CaptionSegment] = []
    vtt_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SoundRecommendationResponse(BaseModel):
    """Sound recommendation response"""
    id: UUID
    sound_url: str
    sound_title: str
    artist: Optional[str] = None
    category: str
    mood: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    is_trending: bool
    license_type: str
    credit_required: Optional[str] = None

    class Config:
        from_attributes = True


class SoundRecommendationsListResponse(BaseModel):
    """List of sound recommendations"""
    sounds: list[SoundRecommendationResponse]
    total: int
    category: str
    region: str


class ColorCorrectionPreset(BaseModel):
    """Color correction preset"""
    preset_name: str
    description: Optional[str] = None
    brightness: int
    contrast: int
    saturation: int
    hue: int
    temperature: int


class ColorCorrectionRequest(BaseModel):
    """Color correction request"""
    segment_id: UUID
    method: str = Field("auto_enhance", description="preset, auto_enhance, lut, custom")
    preset_name: Optional[str] = None
    brightness: int = Field(0, ge=-100, le=100)
    contrast: int = Field(0, ge=-100, le=100)
    saturation: int = Field(0, ge=-100, le=100)
    hue: int = Field(0, ge=-180, le=180)
    temperature: int = Field(0, ge=-100, le=100)


class ColorCorrectionResponse(BaseModel):
    """Color correction response"""
    id: UUID
    ai_generation_id: UUID
    method: str
    preset_name: Optional[str] = None
    output_url: Optional[str] = None
    preview_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CropSuggestion(BaseModel):
    """Crop suggestion for framing"""
    crop_x: int
    crop_y: int
    crop_width: int
    crop_height: int
    confidence: int


class AutoFrameResponse(BaseModel):
    """Smart framing response"""
    id: UUID
    ai_generation_id: UUID
    target_aspect_ratio: str
    suggested_crop: CropSuggestion
    alternative_crops: list[CropSuggestion] = []
    output_url: Optional[str] = None
    preview_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrendSuggestionResponse(BaseModel):
    """Trend suggestion response"""
    id: UUID
    trend_type: str
    trend_value: str
    region: str
    popularity_score: int
    growth_rate: Optional[int] = None
    recommended_duration: Optional[int] = None
    best_posting_time: Optional[str] = None
    related_trends: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class TrendSuggestionsListResponse(BaseModel):
    """List of trend suggestions"""
    trends: list[TrendSuggestionResponse]
    total: int
    region: str


class AIPreviewRequest(BaseModel):
    """Request AI operation preview"""
    operation_type: str
    segment_id: UUID
    parameters: dict


class AIPreviewResponse(BaseModel):
    """Preview of AI operation"""
    preview_id: UUID
    operation_type: str
    preview_url: str
    estimated_credits: int
    estimated_processing_time: int


class AICreditsResponse(BaseModel):
    """AI credits information"""
    total_credits: int
    available_credits: int
    used_credits: int
    monthly_limit: int
    renewal_date: Optional[datetime] = None


class AIOperationHistoryResponse(BaseModel):
    """AI operation history"""
    id: UUID
    operation_type: str
    status: str
    credits_used: int
    created_at: datetime


# ============================================================================
# Session Schemas
# ============================================================================

class SessionInfo(BaseModel):
    """Session information"""
    id: UUID
    device_name: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Recommendation Engine Schemas
# ============================================================================

class RecommendationResponse(BaseModel):
    """Recommendation response"""
    id: UUID
    video_id: UUID
    score: float
    algorithm: str
    reason: Optional[str] = None
    video: VideoDetailResponse
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationsListResponse(BaseModel):
    """List of recommendations"""
    recommendations: List[RecommendationResponse]
    cursor: Optional[str] = None
    total: int


class UserPreferenceResponse(BaseModel):
    """User preference response"""
    id: UUID
    preferred_creators: Optional[List[str]] = []
    preferred_hashtags: Optional[List[str]] = []
    preferred_genres: Optional[List[str]] = []
    preferred_languages: Optional[List[str]] = []
    avg_watch_time: Optional[int] = None
    content_diversity_score: float
    recency_preference: float
    updated_at: datetime

    @field_validator(
        "preferred_creators", "preferred_hashtags", "preferred_genres", "preferred_languages",
        mode="before",
    )
    @classmethod
    def parse_json_list(cls, v):
        """These columns store JSON-encoded strings, not native lists"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class UserPreferenceUpdate(BaseModel):
    """Update user preferences"""
    preferred_creators: Optional[List[UUID]] = None
    preferred_hashtags: Optional[List[str]] = None
    preferred_genres: Optional[List[str]] = None
    preferred_languages: Optional[List[str]] = None
    content_diversity_score: Optional[float] = Field(None, ge=0, le=1)
    recency_preference: Optional[float] = Field(None, ge=0, le=1)


class RecommendationFeedbackRequest(BaseModel):
    """Feedback on recommendation"""
    feedback_type: str = Field(..., description="relevant, irrelevant, duplicate, nsfw, not_interested")
    rating: Optional[int] = Field(None, ge=1, le=5)
    reason: Optional[str] = None


class ABTestResponse(BaseModel):
    """A/B test response"""
    id: UUID
    name: str
    description: Optional[str] = None
    control_version: str
    treatment_version: str
    split_percentage: int
    is_active: bool
    results_significant: Optional[bool] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Hashtag Trending Schemas (Module 9)
# ============================================================================

class HashtagTrendResponse(BaseModel):
    """Hashtag trend response"""
    id: UUID
    hashtag: str
    region: str
    usage_count: int
    unique_creators: int
    total_views: int
    total_likes: int
    popularity_score: int
    trend_velocity: float
    rank_position: Optional[int] = None
    category: Optional[str] = None
    is_challenge: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HashtagAnalyticsResponse(BaseModel):
    """Hashtag analytics response"""
    id: UUID
    hashtag: str
    date: datetime
    usage_count: int
    unique_creators: int
    total_views: int
    total_engagement: int

    class Config:
        from_attributes = True


class ChallengeResponse(BaseModel):
    """Hashtag challenge response"""
    id: UUID
    hashtag: str
    title: str
    description: Optional[str] = None
    rules: Optional[str] = None
    thumbnail_url: Optional[str] = None
    demo_video_url: Optional[str] = None
    start_date: datetime
    end_date: datetime
    prize_pool: Optional[int] = None
    participation_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChallengeCreateRequest(BaseModel):
    """Create challenge request"""
    hashtag: str
    title: str
    description: Optional[str] = None
    rules: Optional[str] = None
    thumbnail_url: Optional[str] = None
    demo_video_url: Optional[str] = None
    start_date: datetime
    end_date: datetime
    prize_pool: Optional[int] = None


# ============================================================================
# Notification Schemas (Module 10)
# ============================================================================

class NotificationTypeEnum(str):
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


class NotificationResponse(BaseModel):
    """Notification response - fields match the Notification model exactly"""
    id: UUID
    user_id: UUID
    type: str
    actor_id: Optional[UUID] = None
    related_video_id: Optional[UUID] = None
    related_comment_id: Optional[UUID] = None
    title: str
    message: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response - fields match the NotificationPreference model exactly"""
    id: UUID
    user_id: UUID
    push_enabled: bool
    email_enabled: bool
    in_app_enabled: bool
    follow_notifications: bool = True
    like_notifications: bool = True
    comment_notifications: bool = True
    mention_notifications: bool = True
    message_notifications: bool = True
    email_digest_enabled: bool = True
    email_digest_frequency: str = "daily"
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences"""
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    follow_notifications: Optional[bool] = None
    like_notifications: Optional[bool] = None
    comment_notifications: Optional[bool] = None
    mention_notifications: Optional[bool] = None
    message_notifications: Optional[bool] = None
    email_digest_enabled: Optional[bool] = None
    email_digest_frequency: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class MarkNotificationReadRequest(BaseModel):
    """Mark notification as read"""
    is_read: bool = True


class NotificationListResponse(BaseModel):
    """Notification list response"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int


# ============================================================================
# Comments & Replies (Module 11)
# ============================================================================

class CommentCreate(BaseModel):
    """Create a comment or reply"""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    """Edit a comment's content"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """Comment response"""
    id: UUID
    video_id: UUID
    user_id: UUID
    user: UserPublicProfile
    parent_comment_id: Optional[UUID] = None
    content: str
    likes_count: int
    replies_count: int
    is_pinned: bool
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Paginated list of comments"""
    comments: List[CommentResponse]
    total: int
    limit: int
    offset: int


class CommentLikeResponse(BaseModel):
    """Comment like/unlike response"""
    is_liked: bool
    likes_count: int


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationError(BaseModel):
    """Validation error response"""
    detail: str
    field: Optional[str] = None
    value: Optional[str] = None
