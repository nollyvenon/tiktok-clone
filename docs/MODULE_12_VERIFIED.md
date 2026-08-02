# Module 12: Followers/Following — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: mostly already built, but never truly exercised

Unlike Modules 10-11, the backend for follow/unfollow, followers/following
lists, and block/unblock already existed (built as part of the Profiles
module) and had passing HTTP-level tests. What was missing per the module
spec was the UI layer (dedicated followers/following pages with search,
block management UI) and "mutual follow detection." Building those
surfaced two serious, previously-invisible backend bugs.

## Bug #1: every "optional current user" endpoint in the app was silently broken

While adding mutual-follow flags to the followers/following list, a new
test authenticated the request and asserted `is_following`/`is_followed_by`
came back correctly — it failed. Root-causing this uncovered a systemic
bug affecting **9 endpoints across `auth.py`, `profiles.py`, and
`videos.py`**, everywhere the codebase used this pattern to support both
authenticated and anonymous requests:

```python
current_user: Optional[User] = Depends(
    lambda auth=Header(None), db=Depends(get_db): get_current_user(auth, db) if auth else None
)
```

Two independent bugs stacked on top of each other here:

1. **Wrong header binding.** FastAPI derives the HTTP header name for a
   `Header()` parameter from the parameter's own name. The parameter is
   named `auth`, so FastAPI looked for a header literally called `Auth` -
   never `Authorization`. The header was never found, so `auth` was
   always `None`, and the lambda's `else None` branch always ran. No
   exception, no visible symptom - just a request that silently behaved
   as anonymous no matter what token was sent.
2. **Lambdas can't be `async def`.** Even after fixing the parameter
   name, calling `get_current_user(authorization, db)` - an `async def` -
   from inside a plain sync lambda produces an *unawaited coroutine
   object*, not a `User`. FastAPI only awaits a sync dependency's return
   value if the dependency callable itself is a coroutine function; a
   lambda never is. Pytest run with `-W error::RuntimeWarning` surfaced
   this immediately as "coroutine 'get_current_user' was never awaited."

**Endpoints affected, and what was silently wrong on every one of them for
the entire lifetime of this project:**
- `GET /profiles/{user_id}` and `/profiles/username/{username}`:
  `is_following`/`is_blocked` on someone's profile were always `False`
  for every logged-in viewer.
- `GET /videos/feed`: `is_liked`/`is_bookmarked` on every video in the
  feed were always `False` regardless of actual state, and
  **`feed_type=following` silently behaved exactly like `for_you`** -
  the following-feed filter (`if feed_type == "following" and user_id`)
  never ran because `user_id` was always `None`.
- `GET /videos/{video_id}`: same `is_liked`/`is_bookmarked` bug.
- `POST /videos/{video_id}/view` (view tracking): per-user view
  deduplication never had a real user to key off.
- `POST /auth/send-otp`, `POST /auth/verify-otp`: optional
  already-logged-in context was always dropped.

**Fix**: replaced the lambda with a proper `async def
get_optional_current_user(...)` in `routes/auth.py` (the same pattern
already correctly used, and never buggy, in `routes/comments.py`'s
`_get_optional_user` - which has now been consolidated to reuse the
shared helper instead of duplicating it). All 9 call sites updated.
Verified with `pytest -W error::RuntimeWarning` - zero unawaited-coroutine
warnings anywhere in the suite afterward.

New regression tests added directly for this:
`test_get_video_reflects_own_like_and_bookmark_when_authenticated`,
`test_following_feed_only_shows_followed_creators`,
`test_feed_reflects_like_state_when_authenticated`,
`test_followers_list_mutual_follow_flags`,
`test_followers_list_anonymous_has_no_mutual_flags`.

## Bug #2: followers/following list ordering was silently wrong

`ProfileService.get_followers`/`get_following` queried `Follow` rows
ordered by `created_at desc` ("most recently followed first"), but then
fetched the actual `User` rows via a separate, unordered
`User.id.in_(follower_ids)` query and returned that result directly - so
the "most recent first" ordering was discarded before it ever reached the
API response. Fixed by re-sorting the fetched users back into the
original `Follow`-query order. Also switched the total-count queries from
`len(result.scalars().all())` (fetches every matching row just to count
it) to `select(func.count()).select_from(Follow)...`.
`test_followers_list_ordered_most_recent_first` locks this in.

---

## What was built

### Backend
- `FollowListUser` schema (extends the public-profile shape with
  `is_following`/`is_followed_by`) and
  `ProfileService.get_mutual_follow_status` (two batched queries, not one
  round trip per row) - real mutual-follow detection, wired into both
  `GET /profiles/{id}/followers` and `/following` when the request is
  authenticated; anonymous requests get both flags as `False`.
- Blocking is now enforced in `CommentService.create_comment` - a user
  cannot comment on a video if either party has blocked the other. This
  was a real gap: Module 11 shipped comments with zero awareness of the
  Module 12 block feature.
- The two ordering/counting bugs above.

### Web
- `/profile/[id]/followers` and `/profile/[id]/following`: a shared
  `FollowList` component with client-side search, "Follows you" /
  "Following" badges from the new mutual-follow fields.
- Follower/Following stat numbers on the profile page are now links
  instead of static text.
- A block/unblock action (overflow menu next to Follow) on the profile
  page, with a visible "You have blocked this user" notice.

### Mobile
- `FollowListScreen` (already existed) gained a search field and now
  shows "Follows you" / "Following" using the new mutual-follow fields on
  `User`.
- `ProfileScreen` gained a block/unblock action in the app bar overflow
  menu for other users' profiles (`ProfileService.toggleBlock`, fixed
  from a `blockUser` method that silently discarded the response and
  never exposed the resulting state to the UI - it was written but never
  actually wired to anything).

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **222/222 passing**
  (up from 215; +7 new tests), with unawaited-coroutine warnings promoted
  to errors to guard against the exact bug class found this pass.
- Web: `npx tsc --noEmit` clean (one real type error caught and fixed:
  `{error && (...)}` doesn't type-check when `error` is `unknown` -
  changed to `{!!error && (...)}`); `next build` succeeds, 19 routes
  including the two new dynamic follower/following pages.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No pagination beyond a single page of up to 100 followers/following on
  either platform (no infinite scroll / load-more).
- Blocking is enforced for comments but not yet for direct messaging
  (no DM feature exists yet) or for hiding a blocked user's videos from
  the blocker's feed.
- No "mutual friends" style suggestions - mutual-follow status is
  surfaced per-row in the list, not used for any recommendation logic.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination.
