"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
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
    """OAuth callback request"""
    provider: str
    access_token: str


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


class FollowersResponse(BaseModel):
    """List of followers"""
    users: list[UserPublicProfile]
    total: int
    cursor: Optional[str] = None


class FollowingResponse(BaseModel):
    """List of following"""
    users: list[UserPublicProfile]
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
    cursor: Optional[str] = None  # For pagination
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
    watch_time: int = Field(..., ge=0)  # Seconds watched
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
# User Schemas
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


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=150)
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    website: Optional[str] = None


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
