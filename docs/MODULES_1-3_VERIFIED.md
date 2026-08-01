# Modules 1-3: Verified Documentation

**Scope of this document:** Authentication (Module 1), User Profiles (Module 2),
Video Feed (Module 3) — backend + web (Next.js) + mobile (Flutter).

Everything in this document was checked by actually running the code
(`pytest`, `flutter analyze`, `flutter test`, `flutter build web`), not
inferred from reading it. Where something is known to be incomplete, it is
called out explicitly rather than omitted. See "Known Gaps" at the end
before treating this as a deployment green light.

---

## 1. Functional Specification

### Module 1 — Authentication
- Email/password registration and login, JWT access + refresh tokens
- TOTP-based 2FA (setup via QR code, verify, disable)
- Email/phone OTP verification
- Password change (authenticated) and password reset (forgot-password flow)
- OAuth login via Google, Facebook, TikTok (authorization-code flow)
- Session/device management: list active sessions, revoke a specific
  session, log out the current device or every device

### Module 2 — User Profiles
- View a profile by user ID or username, with follower/following/video/like
  counts, verification badge, and badges
- Edit own profile (name, bio, avatar, cover, website)
- Follow/unfollow (single toggle endpoint), block/unblock
- Paginated followers and following lists

### Module 3 — Video Feed
- For-you and following feeds, offset-paginated
- Like, bookmark, view-tracking (each a toggle or fire-and-forget endpoint)
- Video search, trending, per-creator video listing
- Creator-only analytics endpoint

---

## 2. Database Schema

| Table | Module | Key columns |
|---|---|---|
| `users` | 1 | email (unique), username (unique), password_hash, two_factor_secret, role |
| `sessions` | 1 | user_id, access_token_jti (unique), refresh_token_jti (unique), is_active, device_name, ip_address |
| `oauth_tokens` | 1 | user_id, provider, provider_user_id, access_token, refresh_token |
| `password_resets` | 1 | user_id, token (unique), expires_at |
| `otps` | 1 | user_id, code, verification_type, expires_at |
| `follows` | 2 | follower_id, following_id, unique(follower_id, following_id) |
| `blocks` | 2 | blocker_id, blocked_id, unique(blocker_id, blocked_id) |
| `verifications` | 2 | user_id (unique), verification_type |
| `badges` | 2 | user_id, badge_type, unique(user_id, badge_type) |
| `videos` | 3 | user_id, video_url, status, views/likes/comments/shares/bookmarks_count |
| `likes`, `bookmarks`, `views` | 3 | user_id, video_id |

Migrations: `001_initial_schema.py` through `010_add_tiktok_oauth_provider.py`,
all with reversible `downgrade()` functions.

---

## 3. API Endpoints (verified against actual route files, not aspirational)

### Auth (`/api/auth`)
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/register` | - | Returns access+refresh token pair |
| POST | `/login` | - | |
| POST | `/refresh` | - | Requires an active `Session` row |
| POST | `/password-reset` | - | Always returns success (no email enumeration) |
| POST | `/password-reset/confirm` | - | |
| POST | `/logout` | Bearer | `?everywhere=true` to revoke all devices; default revokes only the current session |
| GET | `/sessions` | Bearer | Lists active devices, flags `is_current` |
| DELETE | `/sessions/{id}` | Bearer | 404 if not found/not owned |
| GET | `/me` | Bearer | |
| POST | `/change-password` | Bearer | |
| POST | `/otp/send`, `/otp/verify` | Optional Bearer | |
| POST | `/2fa/setup`, `/2fa/verify`, `/2fa/disable` | Bearer | |
| GET | `/oauth/{provider}/authorize` | - | 307 redirect; `provider` ∈ {google, facebook, tiktok} |
| POST | `/oauth/callback` | - | Exchanges `code`+`state` for app tokens |

### Profiles (`/api/profiles`)
| Method | Path | Auth |
|---|---|---|
| GET | `/{user_id}` | Optional |
| GET | `/username/{username}` | Optional |
| PUT | `/me` | Bearer |
| POST | `/{user_id}/follow` | Bearer — **toggles**, no separate unfollow route |
| GET | `/{user_id}/followers`, `/{user_id}/following` | - |
| POST | `/{user_id}/block` | Bearer |
| GET | `/me/blocked` | Bearer |

### Videos (`/api/videos`)
| Method | Path | Auth |
|---|---|---|
| GET | `/feed` | Optional | `feed_type`, `limit`, `offset` — **not** cursor-based yet |
| GET | `/search`, `/search/trending` | - | Registered *before* `/{video_id}` (route-order matters in FastAPI) |
| GET | `/{video_id}` | Optional |
| GET | `/user/{user_id}/videos` | - |
| POST | `/` | Bearer |
| PUT/DELETE | `/{video_id}` | Bearer, owner-only |
| POST | `/{video_id}/like`, `/{video_id}/bookmark` | Bearer — **toggles** |
| POST | `/{video_id}/view` | Optional |
| GET | `/{video_id}/analytics` | Bearer, owner-only |

---

## 4. Security

**Fixed this pass** (previously broken — see git history for `Fix session
revocation gap`):
- Access tokens are now checked against a live `Session.is_active` row on
  every request, not just JWT signature/expiry. Logging out (or an admin
  revoking a session) takes effect immediately instead of waiting up to 24h
  for the JWT to expire.
- OAuth-issued tokens now have a backing `Session` row, so they're subject
  to the same revocation as password logins.
- Default logout only kills the current device's session; `?everywhere=true`
  is required to sign out all devices. (Previously the default silently
  logged out every device.)
- OAuth CSRF protection via a signed, provider-bound, 10-minute-TTL state
  token (no server-side session storage needed).

**Existing, unchanged:**
- bcrypt password hashing, TOTP 2FA, JWT access (24h) + refresh (7d) tokens
- Pydantic validation on all request bodies

**Known gaps (not fixed this pass):**
- Mobile stores tokens in `flutter_secure_storage` (Keychain/Keystore) —
  correct. Web stores the access token in `localStorage`
  (`frontend/src/stores/authStore.ts`), which is readable by any injected
  script (XSS risk). Migrating to an httpOnly cookie requires backend
  changes to set/read cookies during login/refresh and was out of scope
  for this pass.
- No rate limiting is actually wired up on `/login`, `/register`, or OTP
  endpoints despite `slowapi` being in `requirements.txt` — the dependency
  is installed but unused.
- No device fingerprinting or anomaly/suspicious-login detection.

---

## 5. Web (Next.js) — what's real

- Login/register: full validation, password strength meter, OAuth buttons
  (Google/Facebook/TikTok) redirecting to the new backend endpoints, and
  `/oauth/callback` page completing the exchange.
- Forgot-password page pre-existed and was not modified this pass.
- Session/device management UI (list/revoke sessions) has **no frontend
  yet** — only the backend endpoints exist. This is the most visible
  remaining gap for Module 1 on web.

## 6. Mobile (Flutter) — what's real

Newly created this pass (previously did not exist at all):
- `lib/screens/auth`: login, register, forgot-password, 2FA setup
- `lib/screens/profile`: view/edit profile, followers/following list
- `lib/screens/feed`: vertical swipeable video feed with like/bookmark/
  view-tracking, using `video_player` + `cached_network_image`
- `lib/services`: `ApiClient` (dio, secure-storage-backed token interceptor
  with automatic refresh-on-401), `AuthService`, `ProfileService`,
  `FeedService` — built directly against the verified route shapes above
- Verified: `flutter analyze` (0 issues), `flutter test` (2/2 passing),
  `flutter build web` (succeeds)
- **Not implemented:** session/device management screen, OAuth login on
  mobile (web-only for now — mobile OAuth needs a platform browser/deep-link
  flow, `flutter_web_auth_2` or similar, which was out of scope this pass),
  push notifications, biometric unlock

---

## 7. Performance

- Indexes added in migrations 008/009 for search (`title`, `description`,
  `hashtags`, `username`) and hashtag trending
- No caching layer is actually wired up despite Redis being configured in
  `settings` — `REDIS_URL`/`REDIS_CACHE_TTL` exist but nothing reads from
  Redis yet. Treat this as unimplemented, not "configured."

---

## 8. Future Enhancements (explicitly deferred, not silently dropped)

- Cursor-based feed pagination (currently offset-based; the `cursor` field
  in `FeedResponse` is a placeholder that's always `null`)
- Rate limiting on auth endpoints
- Web UI for session/device management
- Mobile OAuth (deep-link based)
- httpOnly-cookie token storage on web
- Redis caching for profile/feed reads
