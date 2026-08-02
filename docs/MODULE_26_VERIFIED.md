# Module 26: Moderation — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: an admin role that did nothing

`UserRole.ADMIN` existed on the `User` model, but grepping the entire
codebase found zero references to it anywhere - no admin-only endpoint,
no role check, nothing. No content-reporting or moderation infrastructure
existed at all. Built from scratch this pass: reporting (videos,
comments, users), an admin review queue, and enforcement actions.

## Two real bugs found while writing the first tests

1. **SQLAlchemy `Enum` columns store the Python enum's `.name` by
   default, not `.value`.** The `ContentReport` CHECK constraint
   (`ck_content_report_single_target`) does raw-SQL string comparison
   against `content_type` - written as `content_type = 'video'` (the
   lowercase `.value`), but the column was actually storing `'VIDEO'`
   (the uppercase `.name`), so the constraint failed on every insert.
   Every prior Enum column in this codebase only gets compared
   Python-side (`video.status == VideoStatus.PUBLISHED`), so this
   name-vs-value mismatch never mattered before - this is the first raw
   SQL predicate against an Enum column in the whole project. Fixed with
   `values_callable=lambda e: [x.value for x in e]` on all four new Enum
   columns, keeping the on-disk representation aligned with the
   lowercase values already used in the migration and the API's wire
   format.
2. **`decide_report`'s `remove_content` action only set
   `video.deleted_at`, not `video.status = VideoStatus.DELETED`.**
   `VideoService.get_video` filters on `status != VideoStatus.DELETED`,
   not on `deleted_at` - every other soft-delete path in this codebase
   (`VideoService.delete_video`) sets both fields together, but this new
   code only copied the field name, not the actual video-deletion
   contract. Caught immediately by a test that removed a video via a
   moderation decision and then checked it was actually gone. Fixed to
   set both fields, matching the established pattern.

## Design decisions

- **Polymorphic reports via three nullable FK columns, not a single
  generic `content_id`.** SQLAlchemy/Postgres have no native polymorphic
  foreign key, so `ContentReport` has `reported_video_id`/
  `reported_comment_id`/`reported_user_id`, with a CHECK constraint
  enforcing exactly one is set matching `content_type`. This keeps
  referential integrity (a report can't point at a nonexistent video)
  instead of the simpler-but-unsafe alternative of a bare UUID column.
- **`ModerationDecision` is a separate append-only audit table**, not a
  status field mutated in place - matches the spec's explicit call for
  an audit trail, and means a report's history survives even if it's
  later revisited.
- **`remove_content` and `suspend_user`/`ban_user` are real, not just
  logged.** Removing content soft-deletes the actual video/comment
  (reusing the existing soft-delete mechanism everywhere else in the
  app); suspending/banning sets `User.is_active = False`, which the
  existing login flow already checks and rejects - no new enforcement
  mechanism needed, this just finally exercises the two mechanisms
  that already existed.
- **A report can target a user directly, or a video/comment can be
  removed while separately deciding whether to also suspend its
  author** - `decide_report` resolves the target user from the video/
  comment's owner when the report itself was against content rather
  than a user, so "remove this video and suspend whoever posted it" is
  two independent decision calls, not implicit.
- **No mobile admin queue**, per spec ("Mobile: Report submission
  screen" - the review/decide UI is explicitly web-focused).

---

## What was built

### Backend
- `ContentReport`, `ModerationDecision` models and four new enums
  (`ReportedContentType`, `ReportReason`, `ReportStatus`,
  `ModerationActionType`). `migrations/versions/017_add_moderation_tables.py`.
- `require_admin` dependency in `routes/auth.py` - the first place
  `UserRole.ADMIN` is actually checked anywhere in this codebase.
- `ModerationService`: `create_report` (validates the target exists and
  isn't the reporter's own content/self), `get_user_reports`,
  `get_report_queue` (admin, oldest-pending-first, filterable by status/
  content type), `decide_report` (applies the action, logs the decision,
  rejects deciding an already-decided report).
- `routes/moderation.py`: `POST /moderation/reports`,
  `GET /moderation/reports/me`, `GET /moderation/reports` (admin),
  `POST /moderation/reports/{id}/decide` (admin).
- 14 new HTTP-level tests covering all three report types, self-report
  rejection, nonexistent-target rejection, admin-only access (403 for
  non-admins on both the queue and decide endpoints), dismiss, content
  removal (and that the removed video actually 404s afterward), user
  suspension (and that the suspended user actually can't log in
  afterward), and rejecting a second decision on an already-decided
  report.

### Web
- `ReportModal` component (reason selection + optional description),
  wired into the watch page (report video), `CommentSection` (report any
  comment that isn't your own), and the profile page's overflow menu
  (report user, alongside the existing block action).
- `/admin/moderation`: status-filtered queue with per-report action
  buttons (dismiss, remove content, warn/suspend/ban), client-side
  gated on `user.role === 'admin'` (the server enforces this
  regardless via `require_admin` - the gate is just so non-admins
  don't see a broken-looking page).
- Added `role` to the frontend `User` type - it existed on every backend
  user response already but was never surfaced client-side.

### Mobile
- `ModerationService.createReport`, `ReportSheet` (bottom sheet, mirrors
  the web modal), wired into the feed's engagement bar (report video),
  the comments sheet (report any comment that isn't your own), and the
  profile screen (report user, alongside block).
- Used the newer `RadioGroup` API instead of the now-deprecated
  `RadioListTile.groupValue`/`onChanged` pair, keeping `flutter analyze`
  at zero issues rather than shipping with deprecation warnings.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **276/276 passing**
  (up from 262; +14 new tests). Route registration checked directly.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 22 routes
  including `/admin/moderation`.
- Mobile: `flutter analyze` - 0 issues (including fixing two deprecation
  warnings surfaced during this pass); `flutter test` - 2/2 passing.

## Known gaps

- No automated content flagging (spec's AI bullet) - reports are
  entirely user-submitted.
- No appeal process for a moderation decision (spec's security bullet).
- No batch actions in the admin queue (one report decided at a time).
- No audit-log archiving/retention policy - `ModerationDecision` rows
  accumulate indefinitely.
- Suspending/banning a user just flips `is_active` - there's no
  distinction between a temporary suspension and a permanent ban beyond
  the label recorded in the decision (both currently produce identical
  enforcement).

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
