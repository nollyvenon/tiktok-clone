# Module 30: Settings/Preferences — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: real settings pages that were unreachable, and real APIs with no UI

Three settings pages already existed on web
(`/settings/notifications`, `/settings/preferences`, `/settings/two-factor`)
but there was no `/settings` index and no navbar link to any of them -
`/settings/notifications` was only reachable from a link buried in the
notifications page, `/settings/preferences` from an icon on the profile
page, and **`/settings/two-factor` had zero inbound links anywhere in the
app** - a fully-built page nobody could ever navigate to. On mobile, none
of this existed as a connected hub at all - only a standalone
`PreferencesScreen`.

Grepping for other settings-adjacent code turned up two more dead ends:
- `authApi.changePassword` existed in `lib/api.ts` and the backend
  `POST /auth/change-password` endpoint worked and was tested - but no
  web or mobile screen ever called it.
- `profileApi.getBlockedUsers()` existed and worked - but nothing in the
  UI ever displayed the list or offered to unblock anyone. On mobile,
  `ProfileService` didn't even have a `getBlockedUsers` method to call.

None of this needed "fixing" in the sense of a bug - the code was
correct, it was just never wired to anything a user could reach. Module
30's real scope ended up being exactly the spec's ask: an actual
`SettingsPage`/`SettingsScreen` hub tying these together, plus the two
missing capabilities the spec explicitly calls for that didn't exist at
all yet - data export and account deletion.

## What was actually missing vs. what just needed connecting

**Never existed anywhere (built from scratch):**
- `DELETE /auth/me` (soft-delete own account, password-confirmed, revokes
  every active session immediately).
- `GET /auth/me/export` (JSON export of profile/videos/comments/
  notification preferences).
- A `/settings` hub (web) and `SettingsScreen` (mobile) tying every
  settings surface together.
- A blocked-users management screen on both platforms (mobile had no
  `getBlockedUsers` service method at all).
- Password change UI on both platforms.

**Already fully built, just disconnected (wired up, not rebuilt):**
- The three existing web settings pages, now reachable via a shared
  `SettingsNav` tab bar and an actual navbar entry point.
- 2FA setup (web and mobile) - previously reachable on web only by typing
  the URL directly, and on mobile only via whatever screen originally
  linked to `TwoFactorSetupScreen` (now added to the new
  `SettingsScreen` hub).

## Design decisions

- **Account deletion revokes sessions, not just flags the row.**
  `AuthService.delete_account` sets `is_active = False` on every active
  `Session` for the user in the same transaction as the soft-delete,
  because `get_current_user` checks session validity per-request (the
  mechanism already used for logout and the Module 25/26 suspend/ban
  actions) - without this, a deleted account's existing access token
  would keep working until it naturally expired.
- **Deletion requires the current password**, mirroring the pattern
  already established for 2FA disable and other sensitive actions in
  this codebase, not a bare "are you sure?" confirmation.
- **Data export is synchronous and JSON, not a queued/emailed file.**
  Given the modest realistic data volume for a demo-scale account (one
  user's own videos/comments), an async export pipeline would be over-
  engineering; the endpoint just aggregates and returns JSON directly,
  and the web/mobile clients render it as a downloadable file / an
  in-app viewer respectively.
- **The mobile profile screen's separate "Preferences" and "Logout"
  icons were removed and folded into the new Settings icon** - once a
  `SettingsScreen` hub exists containing Preferences and Logout as menu
  items, keeping them as separate top-level icons too would just be
  redundant clutter, not additional functionality.

---

## What was built

### Backend
- `AccountDeleteRequest`/`DataExportResponse` schemas.
- `AuthService.delete_account`, `AuthService.export_user_data`.
- `DELETE /auth/me`, `GET /auth/me/export`.
- 6 new HTTP-level tests: export content correctness, export requires
  auth, delete requires the correct password, successful delete revokes
  both the ability to log in again *and* the currently-held access
  token, delete requires auth.

### Web
- `SettingsNav` shared tab bar, added to all settings pages (including
  the two-factor and preferences pages that previously had no way back
  to any other settings surface).
- `/settings` (redirects to `/settings/account`).
- `/settings/account`: change password, download data export, delete
  account (with a password-confirmation step).
- `/settings/privacy`: blocked users list with unblock.
- A "Settings" entry added to the navbar's user menu (desktop dropdown
  and mobile menu) - previously absent entirely.

### Mobile
- `AuthService.changePassword`/`exportMyData`/`deleteAccount`,
  `ProfileService.getBlockedUsers` - none of these existed before this
  pass.
- `SettingsScreen`: hub linking Account, Notifications, For You
  Preferences, Blocked Users, Two-Factor, and Logout.
- `AccountSettingsScreen`: change password, view data export (shown
  in-app as formatted JSON), delete account with password confirmation.
- `BlockedUsersScreen`: list + unblock, mirroring the web privacy page.
- `ProfileScreen`'s own-profile actions consolidated: a single Settings
  icon replaces the previously-separate Preferences and Logout icons.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **291/291 passing**
  (up from 286; +6 new tests, all in `test_auth.py`). Route registration
  checked directly (`DELETE /auth/me` alongside the pre-existing
  `GET /auth/me` - different HTTP methods on the same path, no conflict).
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 27 routes
  including `/settings`, `/settings/account`, `/settings/privacy`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No recommendation-settings-specific AI tuning beyond the existing For
  You preferences (categories/creators/diversity score) already built in
  Module 7.
- No settings caching (spec's performance bullet) - every settings page
  fetches fresh on load, same as every other page in this app.
- Data export is a point-in-time snapshot of profile/videos/comments
  only - doesn't include messages, notifications history, or likes/
  bookmarks, which a more complete GDPR-style export would cover.
- No email address change flow (only password change) - changing your
  email isn't exposed anywhere.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
