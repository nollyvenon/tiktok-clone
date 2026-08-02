# Module 13: Bookmarks/Saved — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: toggle existed, list never did

The `Bookmark` model, the toggle endpoint (`POST /videos/{id}/bookmark`),
and `is_bookmarked` on video responses already existed. What was
completely missing - and blocks the entire feature per the spec ("Saved
videos page with grid", "BookmarksScreen") - was any way to list a user's
bookmarks. There was no `GET` endpoint at all for "videos I've saved."

## A second, related bug found while building this

While wiring up the bookmarks list, three *other* video endpoints were
checked for how they report `is_liked`/`is_bookmarked`, since that's
exactly the data this feature depends on being correct. All three had
hardcoded the flags to `False` unconditionally, regardless of whether the
request was authenticated:

- `GET /videos/search/trending`
- `GET /videos/search`
- `GET /videos/user/{user_id}/videos` (used by every profile page's video
  grid)

None of these routes even had a `current_user` dependency - they simply
never looked. This is distinct from (but related to) the Module 12
optional-auth bug: that one was a broken dependency that always resolved
to `None`; this one never tried to resolve a user at all. Fixed all three
by adding `get_optional_current_user` and computing the real
`is_liked`/`is_bookmarked` per video, exactly like `get_feed` and
`get_video` already did correctly.

New regression tests lock this in:
`test_search_reflects_like_and_bookmark_state_when_authenticated`, plus
bookmarks-specific tests below.

---

## What was built

### Backend
- `VideoService.get_bookmarked_videos`: bookmarked videos for a user,
  most-recently-saved first, excluding videos that were later unpublished
  or soft-deleted (the bookmark row itself isn't touched, so re-publishing
  would make it reappear - consistent with how the rest of the codebase
  treats soft-deleted content as "hidden, not gone"). Built with the same
  count-via-`func.count()` and preserve-original-ordering fixes already
  applied to followers/following in Module 12, rather than repeating
  those bugs in new code.
- `GET /videos/bookmarks`: new route, registered *before* `/{video_id}`
  in `videos.py` (verified via direct route introspection) so the literal
  `bookmarks` segment isn't shadowed and misparsed as a UUID - the exact
  bug class found and fixed multiple times earlier in this project.
  Requires auth; bookmarks are never listable for anyone but their owner.
- Fixed the three hardcoded `is_liked=False`/`is_bookmarked=False` sites
  above.

### Web
- `/bookmarks`: a grid of `VideoCard`s (reusing the existing component
  rather than building a new one). `VideoCard` gained an optional
  `onBookmarkChange` callback so this page can remove a card from the
  grid the instant it's unsaved, instead of leaving a stale "still saved"
  card until the next reload.
- A "Saved Videos" link added to the navbar's user dropdown (desktop) and
  mobile menu.

### Mobile
- `FeedService.getBookmarkedVideos`.
- `BookmarksScreen`: a thumbnail grid (same `GridView` pattern already
  used by `ChallengeDetailScreen`), each tile with a bookmark-icon overlay
  to unsave directly from the grid, removing it from the list
  immediately. No tap-to-play navigation, since no standalone
  single-video detail/player screen exists anywhere in the mobile app yet
  (the only playback surface is the full `FeedScreen` PageView) - this
  matches the existing precedent set by `ChallengeDetailScreen`'s entry
  grid, which has the same limitation.
- Wired into `ProfileScreen`'s app bar as a bookmark icon, next to the
  existing preferences/logout actions (own profile only).

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **226/226 passing**
  (up from 222; +4 new tests). Route registration checked directly to
  confirm `/videos/bookmarks` isn't shadowed by `/videos/{video_id}`.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 18 routes
  including the new `/bookmarks` page.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No tap-to-play from the mobile bookmarks grid (see note above).
- No "saved content recommendations" (the spec's AI bullet) - no
  recommendation logic reads bookmark history yet.
- No pagination beyond a single page of up to 50 bookmarks on either
  platform.
- Bookmarks are private by construction (the list endpoint only ever
  returns the requesting user's own bookmarks - there's no other-user
  bookmark-list endpoint to accidentally expose), which covers the
  spec's "private bookmarks" requirement without needing a separate
  visibility flag.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination.
