# TikTok Clone - Complete Platform Specification
## 30-Module Enterprise-Grade Short-Video Platform

---

# MODULE 1: AUTHENTICATION & USER MANAGEMENT

## 1.1 FUNCTIONAL SPECIFICATION

### Core Features
- Email/Phone/Social registration and login
- JWT-based token authentication with refresh tokens
- 2FA (TOTP) and OTP support
- Password reset flow with email verification
- Session management (device tracking, logout all)
- OAuth2 integration (Google, Facebook, TikTok)
- Account security (password hashing, rate limiting)
- User verification and role management

### User Stories
- User can register with email, phone, or social account
- User can login securely with password or OTP
- User can enable 2FA for account protection
- User can reset forgotten password via email
- User can manage active sessions across devices
- User can login via Google/Facebook/TikTok
- User can verify their account via email link
- Admin can manage user roles and permissions

---

## 1.2 DATABASE SCHEMA

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(20) UNIQUE,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  bio TEXT,
  avatar_url VARCHAR(500),
  cover_url VARCHAR(500),
  website VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  is_verified BOOLEAN DEFAULT false,
  is_creator BOOLEAN DEFAULT false,
  role ENUM('user', 'creator', 'admin') DEFAULT 'user',
  two_factor_enabled BOOLEAN DEFAULT false,
  two_factor_secret VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  deleted_at TIMESTAMP -- soft delete
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_verified ON users(is_verified);

-- Sessions table
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  device_name VARCHAR(255),
  ip_address VARCHAR(45),
  user_agent TEXT,
  access_token_hash VARCHAR(255),
  refresh_token_hash VARCHAR(255),
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- OAuth tokens
CREATE TABLE oauth_tokens (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL, -- google, facebook, tiktok
  provider_user_id VARCHAR(255) NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_oauth_unique ON oauth_tokens(provider, provider_user_id);

-- Password reset tokens
CREATE TABLE password_resets (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  used_at TIMESTAMP
);
CREATE INDEX idx_password_resets_expires_at ON password_resets(expires_at);

-- OTP for 2FA and phone verification
CREATE TABLE otps (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  phone_number VARCHAR(20),
  email VARCHAR(255),
  code VARCHAR(6) NOT NULL,
  purpose VARCHAR(50), -- phone_verification, 2fa, password_reset
  attempts INT DEFAULT 0,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  verified_at TIMESTAMP
);
CREATE INDEX idx_otps_expires_at ON otps(expires_at);
CREATE INDEX idx_otps_user_id ON otps(user_id);
```

### Relationships
- `users` (1) ← → (many) `sessions`
- `users` (1) ← → (many) `oauth_tokens`
- `users` (1) ← → (many) `password_resets`
- `users` (1) ← → (many) `otps`

---

## 1.3 BACKEND IMPLEMENTATION

### Service Methods (20+)
```python
class AuthService:
    # Registration
    - async register(email, username, password, first_name, last_name) → User
    - async register_with_phone(phone, password, username) → User
    - async register_with_oauth(provider, oauth_data) → User

    # Login/Token Management
    - async login(email, password) → (access_token, refresh_token)
    - async login_with_phone_otp(phone, otp_code) → (access_token, refresh_token)
    - async refresh_token(refresh_token) → (new_access_token, new_refresh_token)
    - async logout(user_id, session_id) → None
    - async logout_all_sessions(user_id) → None

    # 2FA
    - async setup_2fa(user_id, password) → (qr_code, secret)
    - async verify_2fa_setup(user_id, code) → bool
    - async verify_2fa_login(user_id, code) → bool
    - async disable_2fa(user_id, password) → bool

    # OTP
    - async send_otp(phone_or_email, purpose) → OTP
    - async verify_otp(phone_or_email, code) → bool

    # Password Management
    - async change_password(user_id, current_password, new_password) → bool
    - async initiate_password_reset(email) → PasswordReset
    - async confirm_password_reset(token, new_password) → bool

    # Session Management
    - async get_active_sessions(user_id) → List[Session]
    - async get_session_details(session_id) → Session
    - async revoke_session(session_id) → bool

    # Account Management
    - async verify_email(email, token) → bool
    - async verify_phone(phone, otp_code) → bool
```

### API Routes (14 endpoints)
```
POST   /api/auth/register               - Email registration
POST   /api/auth/register/phone         - Phone registration
POST   /api/auth/login                  - Email/password login
POST   /api/auth/login/phone            - Phone OTP login
POST   /api/auth/oauth/authorize        - OAuth flow initiation
POST   /api/auth/oauth/callback         - OAuth callback handler
POST   /api/auth/refresh                - Refresh token
POST   /api/auth/logout                 - Logout current session
POST   /api/auth/logout-all             - Logout all sessions
POST   /api/auth/2fa/setup              - Setup 2FA
POST   /api/auth/2fa/verify             - Verify 2FA code
POST   /api/auth/password/change        - Change password
POST   /api/auth/password/reset         - Initiate password reset
POST   /api/auth/password/reset/confirm - Confirm reset with token
GET    /api/auth/sessions               - List active sessions
DELETE /api/auth/sessions/{session_id}  - Revoke session
```

---

## 1.4 FRONTEND IMPLEMENTATION (React/Next.js)

### Components
```typescript
// Pages
- app/(auth)/register/page.tsx       - Registration form
- app/(auth)/login/page.tsx          - Login form
- app/(auth)/2fa-setup/page.tsx      - 2FA setup flow
- app/(auth)/password-reset/page.tsx - Password reset flow
- app/(auth)/oauth-callback/page.tsx - OAuth callback handler
- app/settings/security/page.tsx     - Security settings

// Components
- components/AuthForm.tsx            - Reusable auth form
- components/OTPInput.tsx            - OTP code input
- components/SessionManager.tsx      - Active sessions list
- components/2FASetup.tsx            - 2FA QR code display
```

### State Management (Zustand)
```typescript
// stores/authStore.ts
interface AuthState {
  user: User | null;
  tokens: { accessToken: string; refreshToken: string } | null;
  isLoading: boolean;
  error: string | null;
  
  actions: {
    login: (email: string, password: string) => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    logout: () => Promise<void>;
    refreshTokens: () => Promise<void>;
    setup2FA: () => Promise<{ qr_code: string; secret: string }>;
  };
}
```

---

## 1.5 MOBILE IMPLEMENTATION (Flutter)

### Screens
```dart
// lib/screens/auth/
- login_screen.dart          - Login UI
- register_screen.dart       - Registration UI
- 2fa_setup_screen.dart      - 2FA setup
- password_reset_screen.dart - Password reset
- otp_input_screen.dart      - OTP verification

// lib/providers/
- auth_provider.dart         - Authentication state management
```

### State Management (Riverpod)
```dart
final authProvider = StateNotifierProvider((ref) => AuthNotifier());
final sessionProvider = FutureProvider((ref) => AuthService.getActiveSessions());
```

---

## 1.6 API ENDPOINTS

### Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}

Response 201:
{
  "user": { ... },
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Login with 2FA
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200 (2FA disabled):
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600
}

Response 202 (2FA enabled):
{
  "requires_2fa": true,
  "temp_token": "..."
}

POST /api/auth/2fa/verify
{
  "temp_token": "...",
  "code": "123456"
}

Response 200:
{
  "access_token": "...",
  "expires_in": 3600
}
```

---

## 1.7 SECURITY CONSIDERATIONS

### Authentication Security
- ✅ Password hashing with bcrypt (12+ rounds)
- ✅ JWT tokens with RS256 signing (asymmetric)
- ✅ Refresh token rotation on each refresh
- ✅ Short-lived access tokens (15-60 minutes)
- ✅ Long-lived refresh tokens (7-30 days) with rotating refresh strategy

### Input Validation
- ✅ Email format validation (RFC 5322)
- ✅ Password strength requirements (min 8 chars, uppercase, number, special char)
- ✅ Username format validation (alphanumeric, underscore, hyphen only)
- ✅ Phone number validation (E.164 format)

### Rate Limiting
- ✅ Login attempts: 5 attempts per 15 minutes per IP
- ✅ Password reset: 3 per hour per email
- ✅ OTP generation: 3 per 10 minutes per phone/email
- ✅ Registration: 10 per hour per IP

### Data Protection
- ✅ Passwords never logged
- ✅ Tokens sent only over HTTPS
- ✅ Tokens stored in secure, HTTP-only cookies (frontend)
- ✅ CSRF protection on all state-changing operations
- ✅ OAuth state parameter validation
- ✅ Soft delete for user accounts (30-day retention)

### 2FA Security
- ✅ TOTP (Time-based One-Time Password) with 30-second window
- ✅ Backup codes generated on 2FA setup (10 codes, single-use)
- ✅ OTP rate limiting (max 3 attempts per minute)
- ✅ Device fingerprinting for suspicious login detection

---

## 1.8 PERFORMANCE OPTIMIZATIONS

### Database Optimizations
- ✅ Indexed on frequently queried columns (email, username, user_id)
- ✅ Partial indexes on is_verified, is_active
- ✅ Connection pooling (min 5, max 20 connections)
- ✅ Prepared statements for all queries

### Caching Strategy
- ✅ User data cached for 1 hour (Redis)
- ✅ Session cache for 5 minutes
- ✅ OAuth token cache until expiration
- ✅ Cache invalidation on user updates

### API Performance
- ✅ Gzip compression on all responses
- ✅ CDN for static assets
- ✅ Async/await throughout (FastAPI)
- ✅ Connection pooling for OAuth providers

### Frontend Performance
- ✅ Code splitting by route
- ✅ Lazy loading of auth components
- ✅ Memoization of auth state selectors
- ✅ Service worker for token persistence

---

## 1.9 FUTURE ENHANCEMENTS

- Biometric authentication (fingerprint, face recognition)
- Hardware security key support (FIDO2/WebAuthn)
- Risk-based authentication (device fingerprinting, location verification)
- Social login with email linking
- Account recovery with security questions
- Compromised password detection (HaveIBeenPwned integration)
- Login notifications and anomaly detection
- Multi-device session management improvements

---

# MODULE 2: USER PROFILES & SOCIAL GRAPH

## 2.1 FUNCTIONAL SPECIFICATION

### Core Features
- Comprehensive user profiles (bio, avatar, cover, website)
- Social graph (follow/unfollow, block/unblock)
- User verification system with badges
- Profile statistics (followers, following, videos, views, likes)
- Public and private profiles
- Profile discovery and search
- User notifications for follows and mentions

### User Stories
- Creator can customize their profile with bio, avatar, links
- User can follow creators and see their content
- User can block abusive users
- Creator can get verified with badge
- User can discover creators through explore page
- Creator can see follower and engagement statistics
- User can view profile statistics and insights

---

## 2.2 DATABASE SCHEMA

```sql
CREATE TABLE follows (
  id UUID PRIMARY KEY,
  follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(follower_id, following_id)
);
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);

CREATE TABLE blocks (
  id UUID PRIMARY KEY,
  blocker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  blocked_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reason VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(blocker_id, blocked_id)
);
CREATE INDEX idx_blocks_blocker ON blocks(blocker_id);
CREATE INDEX idx_blocks_blocked ON blocks(blocked_id);

CREATE TABLE verifications (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  verification_type VARCHAR(50), -- creator, organization, artist
  verified_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP,
  document_url VARCHAR(500),
  status VARCHAR(50) DEFAULT 'verified'
);
CREATE INDEX idx_verifications_user_id ON verifications(user_id);

CREATE TABLE badges (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_type VARCHAR(50), -- creator, verified, official, partner
  badge_name VARCHAR(100),
  badge_icon_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_badges_user_id ON badges(user_id);
```

---

## 2.3 BACKEND IMPLEMENTATION

### Service Methods (15+)
```python
class ProfileService:
    - async get_user_profile(username) → UserProfile
    - async update_user_profile(user_id, data) → User
    - async get_profile_statistics(user_id) → ProfileStats
    
    # Follow/Unfollow
    - async follow_user(follower_id, following_id) → Follow
    - async unfollow_user(follower_id, following_id) → bool
    - async get_followers(user_id, limit, offset) → List[User]
    - async get_following(user_id, limit, offset) → List[User]
    - async is_following(user_id_1, user_id_2) → bool
    
    # Block/Unblock
    - async block_user(blocker_id, blocked_id) → Block
    - async unblock_user(blocker_id, blocked_id) → bool
    - async get_blocked_users(user_id) → List[User]
    - async is_blocked(user_id_1, user_id_2) → bool
    
    # Verification
    - async verify_user(user_id, verification_type) → Verification
    - async get_verification_status(user_id) → Verification
    
    # Badges
    - async add_badge(user_id, badge_type) → Badge
    - async remove_badge(badge_id) → bool
    - async get_user_badges(user_id) → List[Badge]
```

### API Routes (15 endpoints)
```
GET    /api/profiles/{username}         - Get user profile
PUT    /api/profiles/me                 - Update own profile
GET    /api/profiles/{username}/stats   - Get profile statistics
POST   /api/profiles/{username}/follow  - Follow user
DELETE /api/profiles/{username}/follow  - Unfollow user
GET    /api/profiles/{username}/followers - Get followers list
GET    /api/profiles/{username}/following - Get following list
POST   /api/profiles/{username}/block   - Block user
DELETE /api/profiles/{username}/block   - Unblock user
GET    /api/profiles/blocked            - Get blocked users
GET    /api/profiles/{username}/verification - Get verification status
GET    /api/profiles/badges/{user_id}   - Get user badges
GET    /api/discover                    - Discover creators
GET    /api/search/users                - Search users
```

---

## 2.4 FRONTEND IMPLEMENTATION

### Components
```typescript
- app/profile/[username]/page.tsx       - Profile view
- components/ProfileHeader.tsx          - Profile header with avatar, bio
- components/FollowButton.tsx           - Follow/unfollow button
- components/VerificationBadge.tsx      - Verification badge
- components/ProfileStats.tsx           - Follower/video counts
- components/FollowersModal.tsx         - Followers list modal
- components/BlockedUsersModal.tsx      - Blocked users management
```

### State Management
```typescript
interface ProfileState {
  profile: UserProfile | null;
  isFollowing: boolean;
  isBlocked: boolean;
  statistics: ProfileStatistics | null;
}
```

---

## 2.5 MOBILE IMPLEMENTATION (Flutter)

### Screens
```dart
- lib/screens/profile/profile_screen.dart
- lib/screens/profile/edit_profile_screen.dart
- lib/screens/profile/followers_screen.dart
- lib/screens/profile/blocked_users_screen.dart
```

---

## 2.6 SECURITY CONSIDERATIONS

- ✅ Private profiles: non-followers cannot see content
- ✅ Block functionality prevents all interaction
- ✅ Verification validation (document verification)
- ✅ Rate limiting on follow/unfollow
- ✅ Prevention of mass follow/unfollow (spam detection)
- ✅ Username enumeration protection

---

## 2.7 PERFORMANCE OPTIMIZATIONS

- ✅ Follower/following counts cached (1 hour)
- ✅ Profile data cached per user (30 minutes)
- ✅ Cursor-based pagination for followers (no offset)
- ✅ N+1 query prevention with eager loading
- ✅ Batch loading of follow statuses

---

# MODULE 3: VIDEO FEED & ENGAGEMENT

## 3.1 FUNCTIONAL SPECIFICATION

### Core Features
- Personalized for-you feed with AI recommendation
- Following feed (chronological from followed users)
- Like/unlike videos
- Bookmark/save videos
- View tracking and analytics
- Video search by title/description/hashtags
- Trending videos
- Video engagement metrics (views, likes, shares)

---

## 3.2 DATABASE SCHEMA

```sql
CREATE TABLE videos (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255),
  description TEXT,
  video_url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500),
  duration INT, -- milliseconds
  status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
  
  -- Metadata
  hashtags VARCHAR(500),
  location VARCHAR(255),
  music_id UUID,
  
  -- Access control
  is_public BOOLEAN DEFAULT true,
  allow_comments BOOLEAN DEFAULT true,
  allow_duets BOOLEAN DEFAULT true,
  allow_stitches BOOLEAN DEFAULT true,
  
  -- Analytics
  views_count INT DEFAULT 0,
  likes_count INT DEFAULT 0,
  comments_count INT DEFAULT 0,
  shares_count INT DEFAULT 0,
  bookmarks_count INT DEFAULT 0,
  completion_rate INT DEFAULT 0, -- percentage
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP
);
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_published_at ON videos(published_at DESC);
CREATE INDEX idx_videos_status ON videos(status);

CREATE TABLE likes (
  id UUID PRIMARY KEY,
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(video_id, user_id)
);
CREATE INDEX idx_likes_video_id ON likes(video_id);
CREATE INDEX idx_likes_user_id ON likes(user_id);

CREATE TABLE bookmarks (
  id UUID PRIMARY KEY,
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(video_id, user_id)
);
CREATE INDEX idx_bookmarks_video_id ON bookmarks(video_id);
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);

CREATE TABLE views (
  id UUID PRIMARY KEY,
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  watch_time INT, -- seconds
  completed BOOLEAN DEFAULT false,
  device_type VARCHAR(50),
  platform VARCHAR(50),
  country VARCHAR(2),
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_views_video_id ON views(video_id);
CREATE INDEX idx_views_user_id ON views(user_id);
CREATE INDEX idx_views_created_at ON views(created_at);
```

---

## 3.3 BACKEND IMPLEMENTATION

### Service Methods (20+)
```python
class VideoService:
    # Video CRUD
    - async create_video(user_id, data) → Video
    - async get_video(video_id) → Video
    - async update_video(video_id, data) → Video
    - async delete_video(video_id) → bool
    
    # Feed Operations
    - async get_for_you_feed(user_id, limit, cursor) → List[Video]
    - async get_following_feed(user_id, limit, cursor) → List[Video]
    - async get_trending_videos(limit) → List[Video]
    - async search_videos(query, limit, offset) → List[Video]
    
    # Engagement
    - async like_video(video_id, user_id) → Like
    - async unlike_video(video_id, user_id) → bool
    - async bookmark_video(video_id, user_id) → Bookmark
    - async unbookmark_video(video_id, user_id) → bool
    - async is_video_liked(video_id, user_id) → bool
    - async is_video_bookmarked(video_id, user_id) → bool
    
    # Analytics
    - async track_view(video_id, user_id, watch_time, completed) → View
    - async get_video_analytics(video_id) → VideoAnalytics
    - async get_user_video_analytics(user_id) → List[VideoAnalytics]
    
    # Publishing
    - async publish_video(video_id) → Video
    - async archive_video(video_id) → Video
```

### API Routes (18 endpoints)
```
GET    /api/videos/feed/for-you       - Get for-you feed
GET    /api/videos/feed/following     - Get following feed
GET    /api/videos/{video_id}         - Get video details
POST   /api/videos                    - Create video
PUT    /api/videos/{video_id}         - Update video
DELETE /api/videos/{video_id}         - Delete video
POST   /api/videos/{video_id}/like    - Like video
DELETE /api/videos/{video_id}/like    - Unlike video
POST   /api/videos/{video_id}/bookmark - Bookmark video
DELETE /api/videos/{video_id}/bookmark - Unbookmark video
POST   /api/videos/{video_id}/view    - Track view
GET    /api/videos/trending           - Get trending videos
GET    /api/search/videos             - Search videos
GET    /api/videos/{video_id}/analytics - Get video analytics
GET    /api/users/{user_id}/videos    - Get user's videos
```

---

## 3.4 FRONTEND IMPLEMENTATION

### Components
```typescript
- app/feed/page.tsx                     - Main feed
- components/VideoFeed.tsx              - Infinite scroll feed
- components/VideoPlayer.tsx            - Video player with controls
- components/VideoEngagement.tsx        - Like, bookmark, share buttons
- components/VideoComments.tsx          - Comments section
- components/UserVideos.tsx             - User's video grid
- app/video/[id]/page.tsx              - Video detail page
```

### State Management
```typescript
interface FeedState {
  videos: Video[];
  likedVideos: Set<UUID>;
  bookmarkedVideos: Set<UUID>;
  isLoading: boolean;
  cursor: string | null;
}
```

---

## 3.5 MOBILE IMPLEMENTATION (Flutter)

### Screens
```dart
- lib/screens/feed/feed_screen.dart
- lib/screens/video/video_detail_screen.dart
- lib/screens/video/video_player.dart
```

---

## 3.6 SECURITY CONSIDERATIONS

- ✅ Private video access control
- ✅ Rate limiting on engagement (prevent vote manipulation)
- ✅ View tracking without PII (anonymous views counted)
- ✅ Comment filtering (harassment, spam)
- ✅ Video content moderation flags

---

## 3.7 PERFORMANCE OPTIMIZATIONS

- ✅ Video thumbnails cached and optimized
- ✅ Cursor-based pagination (no offset scans)
- ✅ Like/bookmark counts cached (5 minutes)
- ✅ Lazy load video details
- ✅ Batch view tracking (async, non-blocking)
- ✅ Video feed algorithm cached (15 minutes per user)

---

# MODULE 4: VIDEO UPLOAD & DRAFT MANAGEMENT

## 4.1 FUNCTIONAL SPECIFICATION

### Core Features
- S3 presigned URL generation for direct upload
- Upload progress tracking
- Draft management (save, edit, delete)
- Scheduled publishing
- Video metadata editing
- Publish workflow with validation

---

## 4.2 DATABASE SCHEMA

```sql
CREATE TABLE uploads (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  filename VARCHAR(255),
  file_size INT,
  mime_type VARCHAR(50),
  status ENUM('uploading', 'processing', 'completed', 'failed') DEFAULT 'uploading',
  progress INT DEFAULT 0, -- 0-100
  duration INT, -- milliseconds
  thumbnail_url VARCHAR(500),
  processed_video_url VARCHAR(500),
  error_message VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE drafts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  upload_id UUID REFERENCES uploads(id) ON DELETE SET NULL,
  title VARCHAR(255),
  description TEXT,
  hashtags VARCHAR(500),
  thumbnail_url VARCHAR(500),
  
  -- Publishing options
  is_public BOOLEAN DEFAULT true,
  allow_comments BOOLEAN DEFAULT true,
  allow_duets BOOLEAN DEFAULT true,
  allow_stitches BOOLEAN DEFAULT true,
  
  -- Status and scheduling
  status ENUM('editing', 'ready_to_publish', 'published') DEFAULT 'editing',
  scheduled_publish_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP
);
CREATE INDEX idx_drafts_user_id ON drafts(user_id);
CREATE INDEX idx_drafts_status ON drafts(status);
```

---

## 4.3 BACKEND IMPLEMENTATION

### Service Methods (18+)
```python
class UploadService:
    # Upload Management
    - async create_upload(user_id, filename, file_size, mime_type) → Upload
    - async get_presigned_url(upload_id) → (presigned_url, expires_in)
    - async mark_upload_completed(upload_id, video_url, thumbnail_url, duration) → Upload
    - async mark_upload_failed(upload_id, error_message) → Upload
    - async update_upload_progress(upload_id, progress) → Upload
    
    # Draft Management
    - async create_draft(user_id, data) → Draft
    - async get_draft(draft_id) → Draft
    - async update_draft(draft_id, data) → Draft
    - async delete_draft(draft_id) → bool
    - async get_user_drafts(user_id, limit, offset) → List[Draft]
    
    # Publishing
    - async publish_draft(draft_id) → Video
    - async schedule_publish(draft_id, publish_at) → Draft
    - async get_scheduled_videos() → List[Draft]
    - async process_scheduled_publishes() → int
```

### API Routes (12 endpoints)
```
POST   /api/uploads/presigned-url      - Get presigned URL
POST   /api/uploads/{upload_id}/complete - Mark upload completed
POST   /api/uploads/{upload_id}/failed  - Mark upload failed
GET    /api/uploads/{upload_id}        - Get upload status

POST   /api/uploads/drafts             - Create draft
GET    /api/uploads/drafts             - List user's drafts
GET    /api/uploads/drafts/{draft_id}  - Get draft
PUT    /api/uploads/drafts/{draft_id}  - Update draft
DELETE /api/uploads/drafts/{draft_id}  - Delete draft

POST   /api/uploads/drafts/{draft_id}/publish - Publish draft
POST   /api/uploads/drafts/{draft_id}/schedule - Schedule publish
```

---

## 4.4 FRONTEND IMPLEMENTATION

### Components
```typescript
- app/upload/page.tsx                   - Upload page
- components/VideoUploader.tsx          - Drag-drop uploader
- components/DraftEditor.tsx            - Draft editing
- components/PublishModal.tsx           - Publish confirmation
- components/UploadProgress.tsx         - Upload progress bar
- app/drafts/page.tsx                  - Drafts list
```

---

## 4.5 MOBILE IMPLEMENTATION (Flutter)

### Screens
```dart
- lib/screens/upload/video_picker_screen.dart
- lib/screens/upload/video_editor_screen.dart
- lib/screens/upload/publish_screen.dart
- lib/screens/upload/drafts_screen.dart
```

---

## 4.6 SECURITY CONSIDERATIONS

- ✅ Presigned URLs expire (1 hour)
- ✅ File size limits (max 4GB)
- ✅ MIME type validation
- ✅ Virus scanning on upload
- ✅ User quota enforcement
- ✅ Video content moderation

---

## 4.7 PERFORMANCE OPTIMIZATIONS

- ✅ Direct S3 upload (bypass server)
- ✅ Multipart upload for large files
- ✅ Asynchronous video processing
- ✅ Thumbnail generation (background job)
- ✅ CDN distribution for processed videos

---

# MODULE 5: VIDEO EDITOR

## 5.1 FUNCTIONAL SPECIFICATION

### Core Features
- Timeline-based video editing
- Segment management (add, reorder, delete)
- Text overlays with animations
- Sticker placement
- Effect application (blur, brighten, etc.)
- Transitions between segments
- Speed/volume adjustments
- Video export with quality selection

---

## 5.2 BACKEND IMPLEMENTATION

### 20+ Service Methods
- Segment CRUD operations
- Text overlay management
- Sticker management
- Effect application and removal
- Timeline operations (trim, speed, volume, mute)
- Editor state retrieval
- Video export queuing

### 15+ API Endpoints
```
POST   /api/editor/drafts/{draft_id}/segments
GET    /api/editor/drafts/{draft_id}/segments
PUT    /api/editor/segments/{segment_id}
DELETE /api/editor/segments/{segment_id}
POST   /api/editor/drafts/{draft_id}/reorder-segments

POST   /api/editor/segments/{segment_id}/overlays
GET    /api/editor/segments/{segment_id}/overlays
DELETE /api/editor/overlays/{overlay_id}

POST   /api/editor/segments/{segment_id}/stickers
GET    /api/editor/segments/{segment_id}/stickers
DELETE /api/editor/stickers/{sticker_id}

POST   /api/editor/segments/{segment_id}/effects/{effect_name}
POST   /api/editor/segments/{segment_id}/trim
POST   /api/editor/segments/{segment_id}/speed
POST   /api/editor/segments/{segment_id}/volume
POST   /api/editor/segments/{segment_id}/mute

GET    /api/editor/drafts/{draft_id}/state
POST   /api/editor/drafts/{draft_id}/export
```

---

## 5.3 FRONTEND IMPLEMENTATION

### Components
```typescript
- components/Timeline.tsx               - Video timeline
- components/Segment.tsx                - Timeline segment
- components/EffectPanel.tsx            - Effect controls
- components/TextOverlayEditor.tsx      - Text overlay editor
- components/StickerPicker.tsx          - Sticker selector
- components/PreviewPlayer.tsx          - Preview playback
- app/editor/[draft_id]/page.tsx       - Main editor
```

---

## 5.4 SECURITY & PERFORMANCE

- ✅ Rate limiting on export requests
- ✅ Async video processing
- ✅ Cached editor state (auto-save)
- ✅ N+1 query prevention with eager loading

---

# MODULE 6: AI CREATOR STUDIO

## 6.1 FUNCTIONAL SPECIFICATION

### Core Features
- AI background removal/replacement
- Text-to-speech voiceover generation (30+ languages)
- Auto caption generation
- Sound recommendations by mood/category/region
- Auto color correction and presets
- Smart framing with aspect ratio optimization
- Real-time trend suggestions (hashtags, sounds, effects)
- AI credit system with tracking

---

## 6.2 BACKEND IMPLEMENTATION

### 20+ Service Methods
- Background removal operations
- Voiceover generation
- Caption generation
- Sound recommendations
- Color correction application
- Frame suggestion generation
- Trend fetching and filtering
- AI credit tracking and history

### 15+ API Endpoints
```
POST   /api/ai/background-removal
GET    /api/ai/background-removal/{id}

POST   /api/ai/voiceover
GET    /api/ai/voiceover/{id}

POST   /api/ai/captions
GET    /api/ai/captions/{id}

GET    /api/ai/sounds/recommendations
GET    /api/ai/sounds/trending

POST   /api/ai/color-correction
GET    /api/ai/color-correction/{id}

POST   /api/ai/smart-frame

GET    /api/ai/trends
GET    /api/ai/trends/hashtags
GET    /api/ai/trends/sounds

GET    /api/ai/credits
GET    /api/ai/history/{draft_id}
```

---

## 6.3 FRONTEND IMPLEMENTATION

### Components
```typescript
- components/AITools.tsx                - AI tools panel
- components/VoiceoverGenerator.tsx     - TTS UI
- components/BackgroundRemover.tsx      - Background removal
- components/AutoCaptions.tsx           - Caption generation
- components/SoundRecommendations.tsx   - Sound picker
- components/ColorGrader.tsx            - Color correction UI
- components/TrendExplorer.tsx          - Trend suggestions
```

---

## 6.4 SECURITY & PERFORMANCE

- ✅ AI operation credit system
- ✅ Rate limiting on AI operations
- ✅ Async processing with job queue
- ✅ Result caching (1 hour)

---

