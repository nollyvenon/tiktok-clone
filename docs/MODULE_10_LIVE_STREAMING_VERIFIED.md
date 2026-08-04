# Module 10 (spec numbering): Live Streaming — Verified Documentation

**Filename note:** `docs/MODULE_10_VERIFIED.md` already exists and
documents Notifications - that file used an early "build order"
numbering scheme (Notifications happened to be the 10th feature built),
which doesn't match `COMPLETE_MODULE_SPECIFICATIONS.md`'s fixed
numbering (where Module 10 is Live Streaming, used consistently for
every other `MODULE_NN_VERIFIED.md` doc from Module 16 onward this
session). Rather than overwrite real prior documentation, this module
uses a distinct filename.

**Verification status: deferred.** The user paused running tests/builds
mid-session (2026-08-03) until the whole app is declared complete.
Everything in this module was written to the same standard as every
prior module (real HTTP-level tests, real UI wiring end to end, no
faked behavior) but the backend test suite, `tsc`/`next build`, and
`flutter analyze`/`flutter test` have **not been run** for this
module's changes yet - that happens in the deferred, whole-app
verification pass.

---

## Scoping: the social layer of live streaming, honestly, with no video

This is the last module of the original 30-module spec. Every other
"needs real infra" module this session (Creator Fund, Collaborations,
Creator Shop, Monetization) had an honest fallback: skip the real money
movement, keep everything else genuinely functional. Live Streaming is
different - actual video requires an RTMP ingest server and either HLS
or WebRTC playback, and there is no equivalent "keep it real, skip the
hard part" move for the *video* itself. Faking a video player (a canned
`<video>` element, a static placeholder claiming to be a live feed)
would misrepresent what this app can do far more than any other
scoping decision made this session.

So the scope drawn here is explicit: build the *social* layer of live
streaming completely for real - a stream session lifecycle a creator
actually starts and ends, real viewer presence tracking (not a fake
counter), and real chat - and be upfront in the UI itself (a visible
"No video preview in this build" note in the stream player area, on
both web and mobile) rather than silently omitting video and letting a
user assume it's just not loading. Nothing here pretends to be video
that isn't there.

## Design decisions

- **Viewer count is derived from real presence, not a bare counter.**
  `LiveStreamViewer` rows record join/leave per user, with a unique
  constraint on (stream, user) so the same viewer can't inflate the
  count by joining twice - `join_stream`/`leave_stream` are idempotent
  (a second join while already active, or a leave while not active,
  just returns the current state rather than erroring or double-
  counting). `viewer_count` and `peak_viewer_count` are still stored as
  denormalized integers on `LiveStream` for fast reads, updated
  transactionally alongside each viewer row change - the same
  denormalized-counter-plus-real-rows pattern `Video.likes_count`/
  `Like` already uses elsewhere in this app.
- **One live stream per creator at a time**, checked in the service
  (no partial unique index needed across most databases for this) -
  starting a second stream while one is already live is rejected with a
  clear error rather than silently ending the first.
- **Chat requires the stream to still be live.** Once a stream ends,
  its chat history remains readable but no new messages can be posted -
  consistent with how every other "can this action happen after the
  parent resource is finalized" case in this app is handled (e.g.
  Collaboration responses, Creator Fund decisions).
- **No real-time push (WebSocket/SSE) for chat or viewer count** - this
  app has never had a WebSocket layer for messages or notifications
  either, so live chat and viewer count use the same short-interval
  polling (3-5 seconds) already used elsewhere, not a new real-time
  mechanism introduced just for this module.

## What was built

### Backend
- `LiveStreamStatus` (live/ended), `LiveStream` model (creator, title,
  viewer/peak counts, started/ended timestamps).
- `LiveStreamViewer` model (join/leave tracking, unique per stream+user).
- `LiveChatMessage` model.
- `LiveStreamingService`: `start_stream` (rejects a second concurrent
  stream), `end_stream` (owner-only), `list_live_streams` (discovery,
  most-viewers-first), `get_stream`, `join_stream`/`leave_stream`
  (idempotent, maintain viewer/peak counts), `post_chat_message`/
  `list_chat_messages` (joined with `User` for the display username, so
  clients don't need a separate profile lookup per message).
- Routes: `POST /live/start`, `GET /live` (discovery), `GET /live/{id}`,
  `POST /live/{id}/end`, `POST /live/{id}/join`, `POST /live/{id}/leave`,
  `POST /live/{id}/chat`, `GET /live/{id}/chat`.
- Migration `024_add_live_streaming_tables.py`.
- 13 new HTTP-level tests (written, not yet run): start/list, rejecting
  a second concurrent stream, ending a stream removes it from the live
  list, non-owner blocked from ending, join incrementing and leave
  decrementing viewer count (with peak preserved), repeated join being
  idempotent, joining an ended stream rejected, posting and listing
  chat messages (with username resolution verified), chatting in an
  ended stream rejected, stream detail view, a nonexistent stream
  returning 400, and auth requirements on mutating endpoints.

### Web
- `/live`: discovery list of currently-live streams (polling every 10s)
  plus a "Go live" form that starts a stream and redirects into it.
- `/live/[streamId]`: the viewer room - title, LIVE/Ended status, live
  viewer count, a placeholder video area with the explicit "no video
  preview" note, and a chat panel (polling every 3s) with a send box.
  Joins on mount and leaves on unmount/navigation-away. The stream
  owner sees an "End stream" button.
- "Live" added to the navbar's main nav row (desktop and mobile menu),
  next to Discover.

### Mobile
- `LiveStreamingService`/`LiveStream`/`LiveChatMessage` models.
- `LiveDiscoveryScreen` and `LiveStreamScreen` mirror the two web pages,
  including the same explicit no-video-preview note and the same
  join-on-open/leave-on-close lifecycle (via `dispose`).
- Reached via a new AppBar action on `DiscoverScreen` (a "Live" podcast
  icon) rather than a new bottom-nav tab - the bottom nav is an
  intentionally small, fixed 5-tab shell per its own code comment, and
  every other module this session used an AppBar entry point instead of
  expanding it.

---

## Known gaps

- **No actual video transport** - no RTMP ingest, no HLS/WebRTC
  playback. This is the central, deliberate scoping boundary of this
  module (see Scoping above), not an oversight.
- No real-time push for chat/viewer count - both are polled, consistent
  with the rest of this app's lack of a WebSocket layer.
- No stream scheduling (spec's "upcoming streams") - a stream only
  exists once started; there's no "scheduled for later" state.
- No monetization tie-in (tips/gifts during a stream) - Module 18
  (Monetization) only credits earnings from Creator Fund and Shop
  orders, not live streams.
- No moderation tools specific to live chat (no per-stream mute/ban) -
  general user blocking still applies but isn't stream-scoped.
- Verification (tests, `next build`, `flutter analyze`/`test`) has not
  been run for this module - see the note at the top of this doc.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no video composition for duets/stitches, no beauty/AR
filters, no real LLM integration, no real payment processor.

---

## Where this leaves the 30-module spec

With this module, every one of the 30 spec modules has been addressed:
built to full real-infrastructure standard where that was possible, or
honestly scoped to the largest genuinely-buildable subset where it
wasn't (payments, live video). The deferred verification pass across
everything built since the pause began (Modules 16, 18, and this one)
is the natural next step before calling the app complete.
