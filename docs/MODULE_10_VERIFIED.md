# Module 10: Notifications — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: models only, nothing else

Unlike every other module documented so far, Module 10 had **no service,
no routes, and no tests at all** before this pass — only the
`Notification`/`NotificationPreference` models existed, and the router
import in `main.py` was commented out. This is the one module in this
project that was built from scratch in this session rather than fixed.

Two real schema/model mismatches were caught before writing a single test,
just by reading the existing (unused) schemas against the models:
- `NotificationResponse` had a `body` field and a `data` dict field that
  don't exist on the `Notification` model at all — the real column is
  `message`, and there's no free-form data field, just `related_comment_id`.
- `NotificationPreferenceResponse.digest_frequency` doesn't match the
  model's `email_digest_frequency`, and it was missing
  `email_digest_enabled`/`quiet_hours_enabled` entirely.

Both fixed to match the models exactly before any code was written against
them.

## A second real bug, found while wiring in triggers

Building this module meant hooking it into existing follow/like actions -
doing that surfaced a genuine, unrelated bug in Module 2:
`ProfileService.follow_user` unconditionally set `Follow.is_active = False`
whenever an existing row was found, regardless of its current state. That
means **re-following a user after unfollowing them silently did nothing** -
the row was already inactive, and the code set it to inactive again.  Fixed
to toggle based on the row's actual current state, with a regression test
(`test_follow_user` now also exercises the re-follow case).

---

## What was built

### Backend
- `services/notifications.py`: `send_notification` (respects `in_app_enabled`
  and the per-type flag, and refuses to notify a user about their own
  action), `get_user_notifications` (with unread-only filter and unread
  count), `mark_as_read`, `mark_all_as_read`, `delete_notification`,
  `get_or_create_preferences`, `update_preferences`.
- `routes/notifications.py`: `GET /notifications`, `PUT /{id}/read`,
  `PUT /read-all`, `DELETE /{id}`, `GET /preferences`, `PUT /preferences`.
- `migrations/versions/011_add_notification_tables.py`.
- **Real triggers wired in**: following a user (`routes/profiles.py`) and
  liking a video (`routes/videos.py`) now actually create notifications for
  the recipient, end to end - not just CRUD scaffolding with nothing calling
  it.
- Written HTTP-level from the start this time (`test_notifications.py`,
  15 tests) - every other module's real bugs were only ever caught once
  something issued a real request through `test_client`, so this module
  skips the service-only-test phase entirely.

### Web
- `/notifications`: list with unread highlighting, per-type icons, mark
  read / mark all read / delete.
- `/settings/notifications`: channel toggles, per-type toggles, email
  digest frequency.
- Navbar bell icon with an unread-dot badge.

### Mobile
- `NotificationsScreen`: swipe-to-delete, tap-to-mark-read, mark-all-read,
  settings gear linking to `NotificationSettingsScreen` (same toggles as web).
- A bell icon with an unread-count `Badge` overlaid on the feed screen (the
  feed has no app bar - it's a full-screen immersive video view - so a
  floating badge matches the existing UI pattern better than adding one).

---

## Verification performed

- Backend: `pytest tests/` — **197/197 passing** (up from 182; +15 new
  notification tests, all passing on the first real run since the module
  was built test-first against already-fixed schemas).
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 19 routes.
- Mobile: `flutter analyze` — 0 issues; `flutter test` — 2/2 passing.

## Known gaps

- No push notification delivery (the `push_enabled` flag exists and is
  respected for *creating* the in-app record, but there's no APNs/FCM
  integration - flipping the flag doesn't currently do anything beyond
  gating in-app rows).
- No email digest sending (the `email_digest_frequency` preference is
  stored and editable, nothing reads it on a schedule yet).
- Comment, mention, message, gift, and duet/stitch notification triggers
  aren't wired up - those actions don't exist as backend features yet
  (Modules 11+), so there's nothing to trigger them from. The `follow` and
  `like` triggers built this pass are the only two currently-real actions
  in the app that produce a notification.
- No mention/@ parsing anywhere (there's no comments system yet to mention
  someone in).

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination.
