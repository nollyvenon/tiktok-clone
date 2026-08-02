# Modules 8-9: Verified Documentation

**Scope:** Search & Discovery (8), Hashtag Trending & Challenges (9) —
backend + web (Next.js) + mobile (Flutter).

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Real bugs found and fixed this pass

Both modules had only ever been tested at the service layer
(`SearchService`/`HashtagService` called directly in tests) — never through
an actual HTTP request. That gap hid two more real, load-bearing bugs on
top of the ones already fixed in the Modules 1-9 pass:

- **Module 9 routing**: `routes/hashtags.py`'s router already declared
  `prefix="/hashtags"`... no — it declared `prefix="/api/hashtags"`, and
  `main.py` registered it with *another* `prefix="/api"` on top, doubling
  every hashtag endpoint to `/api/api/hashtags/...`. Every hashtag route
  was unreachable at its documented path. Fixed by dropping the redundant
  `/api` from the router's own prefix.
- **Module 8 & 9 response building**: `routes/search.py`'s `/videos`,
  `/discover/{category}`, and `/advanced`, plus `routes/hashtags.py`'s
  `/challenges/{id}/videos`, all did a blind `VideoDetailResponse.from_orm
  (video)` (or, in the hashtags case, returned raw ORM rows with no
  conversion at all). `VideoDetailResponse.user` is a required
  `UserPublicProfile` — a bare `Video` row only has `user_id`, not a
  populated `user` attribute, so every one of these endpoints either
  500'd or (in the no-response-model case) leaked internal ORM columns
  with no `user` object for clients to render. Added a shared
  `_build_video_response()` helper in each route file that fetches the
  author via `ProfileService` and builds the response properly.
- Added `test_hashtags_routes.py` and `test_search_routes.py` — HTTP-level
  tests that would have caught both of the above; the old service-level
  test files (`test_hashtags.py`, `test_search.py`) are left in place since
  they still cover business logic, but they cannot catch route-registration
  or response-construction bugs by design.

## Full-stack build-out this pass

### Module 8 — Search & Discovery
Web UI already existed from the Modules 1-3 pass (`/search`); this pass
fixed the underlying `/videos` and `/discover/{category}` endpoints it
depends on, and made `/search` read an initial `?q=` from the URL (needed
so Discover's hashtag links actually prefill the search box — required
wrapping the page in `Suspense` per Next.js's `useSearchParams` rule).

### Module 9 — Hashtag Trending & Challenges
Did not have any UI at all before this pass.
- **Web**: `/discover` — active challenges (with prize pool / entry count)
  and ranked trending hashtags (with a trend-velocity indicator), linked
  from the Navbar. Challenge cards link to `/discover/challenges/
  [challengeId]` (challenge info + video-grid entries). Hashtag rows link
  to `/discover/hashtags/[hashtag]` (stat tiles + a CSS-only 30-day usage
  bar chart).
- **Mobile**: `hashtag_service.dart` + `DiscoverScreen` as a bottom-nav tab,
  with taps opening `ChallengeDetailScreen` and `HashtagAnalyticsScreen`
  (a simple `FractionallySizedBox`-based bar chart — no charting package
  needed).
- **Not built**: challenge creation UI (admin-only endpoint, no admin
  surface exists yet).

---

## Second pass: closing the challenge/analytics gaps surfaced one more bug

`GET /hashtags/{hashtag}/analytics` was covered by the service-level tests
but never through HTTP. Adding a real HTTP test for it (`test_get_hashtag_
analytics_route`) immediately failed: `HashtagAnalyticsResponse.total_likes`
doesn't exist on the `HashtagAnalytics` model — it's `total_engagement`.
Fixed the schema to match (tracked in the Modules 4-7 doc alongside the
other schema/model mismatches found the same way).

## Verification performed

- Backend: `pytest tests/` — **182/182 passing** (up from 179).
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 17 routes.
- Mobile: `flutter analyze` — 0 issues; `flutter test` — 2/2 passing.

## Known gaps carried over

Unchanged from Modules 1-7: web token storage in `localStorage`, no mobile
OAuth, no rate limiting, no Redis caching, offset-based feed pagination.
