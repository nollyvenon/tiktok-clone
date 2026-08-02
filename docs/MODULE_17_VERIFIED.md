# Module 17: Analytics Dashboard — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: per-video analytics existed, nothing aggregate did

`GET /videos/{id}/analytics` (owner-only, single video) already existed
and worked. There was no way for a creator to see analytics across all
their videos at once - no aggregate endpoint, no dashboard UI anywhere on
web or mobile.

## A major discovery while building this: enabling real FK enforcement in tests surfaced three separate, previously-invisible production bugs

Building the dashboard meant querying across all of a creator's videos,
which meant looking closely at how views are tracked. That led to
noticing `VideoService.track_view` inserted `user_id=user_id or
UUID(int=0)` for anonymous views - a fabricated all-zero UUID standing in
for "no user," even though `View.user_id` is a `NOT NULL` foreign key to
`users.id`. No such user has ever existed. Checking `tests/conftest.py`
confirmed why this never failed a test: the test database is SQLite,
which does not enforce foreign key constraints unless explicitly told to
- and nothing did. Under the real Postgres database, **every single
anonymous view (the majority of real-world traffic on a public video
app) would have raised a `ForeignKeyViolation` and 500'd.**

Rather than just patch this one call site, the test fixture itself was
hardened: `tests/conftest.py` now enables `PRAGMA foreign_keys=ON` on the
SQLite connection, so the test suite actually enforces the same
constraints Postgres does. Running the full suite with this on
immediately surfaced two *more* real, unrelated bugs that had been
silently broken the same way:

1. **Every AI Creator Studio operation** (background removal, voiceover,
   captions, color correction, smart framing - 5 of 5 operations)
   called `AIService.create_ai_generation(db, user_id, segment_id, ...)`,
   but that function's third parameter is `draft_id`, not `segment_id`.
   Every single AI operation had been recording its tracking row against
   a nonexistent draft - the two IDs are both UUIDs so nothing caught it
   at the type level, and SQLite let the wrong-but-well-formed value
   through silently. Fixed by fetching `segment.draft_id` before calling
   `create_ai_generation` in all 5 methods in `services/ai.py`.
2. **Recommendation feedback** (`POST /recommendations/{id}/feedback`)
   never validated that `recommendation_id` referred to a real
   `Recommendation` row before inserting `RecommendationFeedback` -  a
   stale, expired, or fabricated ID would 500 with a raw FK violation
   instead of a clean 404. Fixed by validating existence first
   (`RecommendationService.record_recommendation_feedback` now raises
   `ValueError` → mapped to 404), and rewrote the 5 existing feedback
   tests (which had all been asserting `201` against a `uuid4()` that
   was never a real recommendation - passing only because SQLite let the
   bogus insert through) to create a real `Recommendation` row first,
   plus one new dedicated test for the 404 case.

All three were caught in a single afternoon by one infrastructure change
to the test fixture, rather than three separate investigations - a good
argument for why the fixture change is worth keeping despite its cost
(see below).

**Cost**: enabling FK enforcement roughly quadruples per-connection
overhead in SQLite (each new connection re-runs the pragma), taking the
full suite from ~6-9 minutes to ~8-9 minutes in practice - a real but
acceptable tradeoff for catching this exact bug class going forward.

---

## What was built

### Backend
- `View.user_id` changed to nullable (it always should have been -
  anonymous views are a real, expected case, not an error condition);
  `track_view` now passes `None` straight through instead of a fake
  sentinel. `migrations/versions/015_make_view_user_id_nullable.py`.
- Fixed the 5 AI-operation `draft_id` mixups in `services/ai.py`.
- Added existence validation to
  `RecommendationService.record_recommendation_feedback` /
  `routes/recommendations.py`.
- `tests/conftest.py`: SQLite FK enforcement enabled via an `event.
  listens_for(engine.sync_engine, "connect")` pragma hook.
- `CreatorDashboardResponse`/`TopVideoSummary` schemas,
  `VideoService.get_creator_dashboard` (aggregate totals across all of a
  user's own non-deleted videos - public and private both included,
  since it's the owner's own view - plus a configurable top-N list
  sorted by views), `GET /videos/dashboard` (literal route, verified
  registered before `/{video_id}`).
- New tests: the dashboard endpoint (aggregate correctness, empty state,
  auth requirement), the anonymous-view-tracking regression, and the
  updated/added recommendation-feedback tests.

### Web
- `/dashboard`: stat cards (views/likes/comments/followers), average
  engagement rate, and a ranked top-videos list linking to each video's
  watch page. Added to the navbar's user menu (both desktop dropdown and
  mobile menu).

### Mobile
- `DashboardScreen`: same stats + top-videos list, added as an app-bar
  icon on the own-profile screen next to Saved Videos and Preferences.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **256/256 passing**
  (up from 251; +5 new tests), now with SQLite foreign-key enforcement
  active for the entire suite - the first time this project's tests have
  actually matched Postgres's constraint behavior.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 21 routes
  including the new `/dashboard`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No time-series/historical charting (views-over-time, etc.) - the
  dashboard is current-state aggregates only, no `View`-table time-bucket
  queries yet.
- No per-video breakdown beyond the top-N list (no full sortable/
  paginated table of every video's stats).
- No demographic or traffic-source breakdown, despite `View` already
  capturing `device_type`/`platform`/`country` per row - none of that is
  surfaced anywhere yet.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
