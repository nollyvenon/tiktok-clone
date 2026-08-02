# Module 11: Comments & Replies — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: nothing but a placeholder

Like Module 10, this module had **no models, service, routes, schemas, or
tests at all** before this pass — only a `COMMENT` value in the
pre-existing `NotificationType` enum and a `related_comment_id` placeholder
column on `Notification`. The web watch page had an explicit
"Comments are coming soon" placeholder. Built entirely from scratch in this
session.

## Design decisions made while building

- **One level of threading only.** A reply's `parent_comment_id` always
  points at a top-level comment; replying to a reply is rejected with a
  400 (`CommentService.create_comment` checks `parent.parent_comment_id
  is not None` and raises). This matches the common "flat replies" pattern
  (Instagram/YouTube-style) rather than arbitrary nesting.
- **Soft delete**, consistent with every other deletable entity in this
  codebase (`deleted_at` column, excluded from all list/count queries).
- **Delete is allowed for the comment's author OR the video's owner**
  (moderation), same pattern already established for comment pinning.
- **Pin is video-owner-only and top-level-only** — replies can't be
  pinned (`toggle_pin` raises if `parent_comment_id is not None`).
- Notification routing: a top-level comment notifies the **video owner**;
  a reply notifies the **parent comment's author**, not the video owner a
  second time. Both go through the existing `NotificationService.
  send_notification`, which already refuses self-notification and respects
  per-type/in-app preference flags from Module 10 — no new suppression
  logic needed.

No pre-existing bugs were "found" this pass (there was nothing to have a
bug in), but the response-builder pattern from every prior module
(`_build_video_response`, `_build_recommendation_response`, etc.) was
applied from the first line of `routes/comments.py` rather than discovered
after a crash — `Comment.user_id` is a bare FK with no ORM relationship
loaded, so `_build_comment_response` explicitly fetches the author via
`ProfileService.get_user_profile` before constructing `CommentResponse`.

---

## What was built

### Backend
- `models.py`: `Comment` (video_id, user_id, parent_comment_id FKs;
  likes_count/replies_count/is_pinned; soft delete) and `CommentLike`
  (unique per comment+user).
- `schemas.py`: `CommentCreate`, `CommentUpdate`, `CommentResponse`,
  `CommentListResponse`, `CommentLikeResponse`.
- `services/comments.py`: `create_comment` (video/comments-disabled/
  reply-threading validation), `get_video_comments` (top-level, pinned
  first then newest first), `get_replies` (oldest first), `is_liked_by`,
  `update_comment`, `delete_comment`, `toggle_like`, `toggle_pin`.
- `routes/comments.py`: `GET/POST /videos/{video_id}/comments`,
  `GET /comments/{id}/replies`, `PUT/DELETE /comments/{id}`,
  `POST /comments/{id}/like`, `POST /comments/{id}/pin` — mounted with no
  router-level prefix (paths already include their own literal segments),
  same as `videos.router`.
- `migrations/versions/012_add_comment_tables.py`.
- **Real triggers wired in**: creating a top-level comment or a reply now
  actually sends a notification end to end (`COMMENT` / `REPLY` types),
  reusing Module 10's `NotificationService` untouched.
- Written HTTP-level from the start (`test_comments.py`, 18 tests) — no
  service-only test file, following the rule established after Module 10.

### Web
- `components/features/CommentSection.tsx`: list (pinned-first), post,
  reply (one level, expand/collapse), edit own, delete (own or as video
  owner), like toggle, pin toggle (video owner only) — all via
  `react-query` mutations that invalidate the comments/replies queries.
- Replaced the "Comments are coming soon" placeholder on
  `/watch/[id]` with `<CommentSection>`.
- Fixed `commentApi` in `lib/api.ts`, which (like every other module's
  pre-existing stub found in this session) was fictional: it wrapped
  responses in a nonexistent `{ data: ... }` envelope, sent camelCase
  `parentCommentId`, and had no edit/pin/replies methods at all. Rewrote
  to match the real snake_case response shapes and full endpoint set.
- Fixed the `Comment` type in `types/index.ts` for the same reason (was
  camelCase `videoId`/`userId`/`author`/`likesCount` matching nothing real).

### Mobile
- `models/comment.dart`: `Comment`, `CommentPage`, reusing `VideoAuthor`
  from `models/video.dart` for the nested author (same shape as
  `UserPublicProfile`/`PublicUser` on the backend/web side).
- `services/comment_service.dart`: full CRUD + like + pin + replies.
- `widgets/comments_sheet.dart`: a `DraggableScrollableSheet` bottom sheet
  (`CommentsSheet.show(...)`) with a `_CommentTile` that recursively
  renders one level of replies, matching the web component's feature set
  (like, reply, edit-free but delete/pin same as web — edit was left
  web-only since no other mobile screen in this app currently supports
  inline text editing of an existing item; deleting and re-posting covers
  the same need on mobile).
- Wired the feed's comment icon (`Icons.comment`, previously a dead
  `onTap: () {}`) to open `CommentsSheet`, and made `Video.commentsCount`
  mutable so the feed's counter updates live after posting/deleting.

---

## Verification performed

- Backend: `pytest tests/` — **215/215 passing** (up from 197; +18 new
  comment tests). Route registration checked directly (no conflicts with
  `/videos/{video_id}` or notification routes).
- Web: `npx tsc --noEmit` clean; `next build` succeeds (19 routes,
  `/watch/[id]` still dynamic as expected).
- Mobile: `flutter analyze` — 0 issues; `flutter test` — 2/2 passing
  (pre-existing login tests; no comment-specific mobile tests were added,
  consistent with this project's existing mobile test coverage pattern).

## Known gaps

- No mention/@ parsing or notification inside comment text.
- No comment editing on mobile (see design note above).
- No comment reporting/moderation flagging beyond delete.
- No push/email delivery for the new COMMENT/REPLY notification types —
  same known gap documented in Module 10, unchanged here.
- Replies are not paginated beyond the standard limit/offset params (no
  infinite-scroll wiring in either UI yet — both fetch the first page of
  replies on expand and don't offer "load more").

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination.

## Note on repo state

While verifying, `frontend` was found to be a stale git submodule gitlink
(`160000` mode entry in the top-level index, no `.gitmodules`) pointing at
a commit, but the nested `frontend/.git` directory referenced by the
two-step-commit workflow used earlier this session no longer exists on
disk. `git add frontend/<file>` now fails with "Pathspec is in submodule
'frontend'" from the top level. This wasn't caused by this module's work
and hasn't been fixed — flagging it here since it blocks committing the
web changes from this module until resolved (either restore/re-init the
nested repo, or remove the stale gitlink so `frontend/` is tracked as a
normal directory in the top-level repo).
