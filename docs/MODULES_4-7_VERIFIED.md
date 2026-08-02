# Modules 4-7: Verified Documentation

**Scope:** Uploads & Drafts (4), Video Editor (5), AI Creator Studio (6),
Recommendations (7) — backend + web (Next.js) + mobile (Flutter).

Same standard as [`docs/MODULES_1-3_VERIFIED.md`](MODULES_1-3_VERIFIED.md):
everything below was checked by actually running it — `pytest`, `tsc
--noEmit`, `next build`, `flutter analyze`, `flutter test` — not inferred
from reading the code.

---

## Starting point: 23 real backend bugs, not just missing UI

Modules 4-7 backends had been claimed "production-ready" without ever
running their tests. Running them surfaced 23 failures, all fixed and
covered by tests (see git history "Fix all 23 remaining backend test
failures across Modules 4-7"):

- **Module 4**: a missing `await` on the presigned-URL call left a coroutine
  object where a string was expected; `GET /uploads/drafts` was registered
  after the UUID-typed `GET /uploads/{upload_id}`, so "drafts" was parsed as
  an upload id and 422'd; `DraftResponse` was missing `scheduled_publish_at`.
- **Module 5**: `update_segment` never applied `start_time`/`end_time`;
  `apply_effect`/`remove_effect` stored effects as `{name, params}` dicts
  while the schema (and create/update) treat effects as `list[str]` — the
  resulting Pydantic `ValidationError` (a `ValueError` subclass) was
  silently miscaught as a 404 by the route's own error handling, hiding the
  real bug; `ExportResponse` was missing `draft_id`/`quality`/`format`.
- **Module 6**: `BackgroundRemoval`/`Voiceover`/`AutoCaption`/
  `ColorCorrection`/`AutoFrame` have no `status` column of their own (it
  lives on the related `AIGeneration` row) — every POST/GET handler for all
  four sub-resources did a blind `Response.from_orm(row)` and crashed on the
  missing required field, every single time. `AutoCaptionResponse.captions`
  and `AutoFrameResponse.suggested_crop`/`alternative_crops` didn't match
  their underlying columns at all.
- **Module 7**: `GET /preferences` faked a default response with
  `id=None`/`updated_at=None` for non-optional Pydantic fields — always
  500'd for a new user. Now persists a real default row on first access.
  The four `list[str]` preference fields read raw JSON strings with no
  parsing.

## Full-stack build-out this pass

### Module 4 — Uploads & Drafts
- **Web**: rewrote `create/page.tsx` around the real contract — presigned
  URL → direct `PUT` to storage (with progress) → mark complete → create
  draft → publish. Added `/drafts` (list/publish/schedule/delete — didn't
  exist before).
- **Mobile**: `upload_service.dart` (same contract), `upload_screen.dart`
  (`image_picker` video selection + live preview + staged progress UI),
  `drafts_screen.dart`. Added a Drafts tab to the bottom nav.

### Module 5 — Video Editor
- **Web**: `/edit/[draftId]` — per-segment effect picker, speed/volume
  sliders, mute toggle, text-overlay dialog, sticker add/list/delete,
  up/down segment reordering (calls the real reorder-segments endpoint),
  export button. Linked from the drafts list.
- **Mobile**: `editor_service.dart` + `editor_screen.dart`, same capability
  set, linked from the drafts screen.
- Not built: a real drag-handle timeline (up/down buttons exercise the same
  reorder endpoint without a new drag-and-drop dependency), trim UI
  (endpoint exists, unused).

### Module 6 — AI Creator Studio
- **Web + Mobile**: an "AI tools" section on each segment in the editor
  (remove background, auto captions, auto color, smart frame, voiceover
  with script + voice picker), with inline status/credit-cost feedback.
  Plus a Sound Recommendations browser (category filter, trending badge) —
  browse-only, since there's no "apply sound to video" endpoint on the
  backend.
- Not built: trend suggestions UI, AI credits/usage dashboard (`GET
  /ai/credits` exists, no UI reads it yet).

### Module 7 — Recommendations
- **Web + Mobile**: `/settings/preferences` (content-diversity/recency
  sliders, preferred hashtags) and `/for-you` — the real
  `RecommendationResponse`-shaped feed (score/algorithm-labeled cards,
  cursor-based pagination, thumbs up/down feedback keyed by
  `recommendation_id`). This was deferred in the original pass pending two
  backend bugs (below) that made it impossible to build correctly; both
  are now fixed.

---

## Second pass: 3 more real bugs found closing these gaps

Building the deferred UI surfaced bugs the original (service-level-only)
tests never exercised, because no test had ever populated the rows needed
to trigger them:

- `GET /recommendations/for-you`: `RecommendationResponse.from_orm(r)` on a
  `Recommendation` row that has no `video` relationship (only a `video_id`
  FK) — 500'd whenever a real recommendation existed. No test had ever
  created one. Fixed with a helper that fetches and nests the video.
- `GET /recommendations/similar/{video_id}`: built `{"video": v}`-only
  dicts missing every other required field — always 500'd. Switched the
  response model to `FeedResponse` since similarity matches aren't scored
  `Recommendation` records to begin with.
- `HashtagAnalyticsResponse.total_likes` — the `HashtagAnalytics` model has
  no such column, only `total_engagement`. Fixed the schema to match.

Added tests for all three; full suite: **182/182 passing**.

---

## Verification performed

- Backend: `pytest tests/` — **182/182 passing** (up from 165), including
  new tests for the bugs found in the second pass.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 17 routes.
- Mobile: `flutter analyze` — 0 issues; `flutter test` — 2/2 passing.

## Known gaps carried over from Modules 1-3

Unchanged: web token storage in `localStorage` (XSS-exposed), no mobile
OAuth, no rate limiting on auth endpoints, no Redis caching despite being
configured, offset-based (not cursor-based) feed pagination.
