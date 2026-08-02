# Modules 19-20: Duets & Stitches — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: permission flags with nothing behind them

`Video.allow_duets`/`allow_stitches` and a `DUET_STITCH` notification type
already existed, but there was no way to actually create a duet or stitch
anywhere in the codebase - no linking column, no validation, no UI. Built
both modules together this pass since they share nearly identical
mechanics (a video referencing another as its source, differing only in
composition style) and the spec bullets are otherwise duplicative.

## A significant discovery while wiring this up: the direct video-create endpoint is dead code

The obvious place to add duet/stitch creation was `VideoService.create_video`
/ `POST /videos`, and that's where the first pass of this work went. But
before writing web/mobile UI against it, grepping the frontend for any
caller of that endpoint turned up **nothing** - `POST /api/videos` is never
called anywhere in the web or mobile apps. The actual, real publish
pipeline both clients use is entirely different:

```
create upload -> complete upload -> create/update draft -> POST /uploads/drafts/{id}/publish
```

`UploadService.publish_draft` builds the `Video` row directly from the
`Draft` + `Upload` rows - it does not call `VideoService.create_video` or
go through `VideoCreate` at all. This means the duet/stitch fields I'd
added to `VideoCreate`/`POST /videos` would have been **completely
unreachable by any real user** - a classic case of building against the
wrong entry point. Caught before any UI was written against it, by
checking what actually calls the endpoint rather than assuming the
schema I was editing was the live one.

**Fix**: added the same `original_video_id`/`remix_type` fields to
`Draft` and `DraftCreate`/`DraftResponse`, and extracted the validation
logic into a shared `VideoService.validate_remix()` static method called
from *both* `create_video` (kept working, still reachable via direct API
use/testing) and `publish_draft` (the pipeline real clients actually use).
Permission is re-checked at **publish time, not draft-save time** -
`test_publish_draft_duet_revoked_between_draft_and_publish` locks in that
disabling duets on the original video after a duet draft already
references it still blocks the publish.

## Design decisions

- **No real video composition.** An actual "duet" (side-by-side
  recording) or "stitch" (clipping and appending) requires client-side
  video processing that doesn't exist anywhere in this app - not even for
  original video creation (upload is a plain file picker; the "editor"
  module only applies post-hoc metadata/effects to an already-uploaded
  file, never composites multiple video sources). Given that, a
  duet/stitch here is exactly what an original video upload already is -
  a separately-recorded/selected file - plus a link back to the video it
  responds to. This isn't a shortcut around building the real feature;
  it's the only feature buildable given the app's existing (lack of)
  video-processing capability, and is documented honestly rather than
  faked.
- Permission and blocking checks mirror the exact patterns already
  established: `allow_duets`/`allow_stitches` (existing flags, finally
  enforced), and the same mutual-block check used for comments in
  Module 12/13.
- `original_video_id` uses `ondelete='SET NULL'` (on both `videos` and
  `drafts`) rather than cascading delete - a duet/stitch is independent
  content and must survive the original being removed, just losing its
  attribution.
- Reused the pre-existing `DUET_STITCH` notification type and
  `related_video_id` field rather than adding new notification
  infrastructure.

---

## What was built

### Backend
- `models.py`: `RemixType` enum, `Video.original_video_id`/`remix_type`,
  `Draft.original_video_id`/`remix_type`.
- `schemas.py`: `OriginalVideoPreview` (attribution preview: id, title,
  thumbnail, author), fields added to `VideoCreate`, `VideoDetailResponse`,
  `DraftCreate`, `DraftResponse`.
- `VideoService.validate_remix` (shared), `VideoService.get_remixes`
  (paginated, optionally filtered to just duets or just stitches).
- `routes/videos.py`: `original_video_id`/`remix_type` on
  `POST /videos`; `GET /videos/{id}/remixes`; a shared
  `_build_original_video_preview` helper applied to all 6 places a
  `VideoDetailResponse` gets built (feed, trending, search, single video,
  user videos, bookmarks).
- `routes/uploads.py`: `publish_draft` now validates and carries remix
  fields through to the created `Video`, and sends the `DUET_STITCH`
  notification - the real, reachable path.
- `migrations/versions/014_add_duet_stitch_columns.py` (both tables, one
  enum).
- 12 new HTTP-level tests split across `test_videos.py` (direct-create
  path + `get_remixes`) and `test_uploads.py` (the real draft/publish
  path, including the permission-revoked-mid-draft case).

### Web
- Watch page: attribution banner ("Duet with @x" / "Stitch of @x",
  linking to the original), Duet/Stitch buttons (shown only when the
  video allows that type) linking to `/create?originalVideoId=...&remixType=...`,
  and a "Duets & Stitches" grid of remixes via the new endpoint.
- `/create` reads those query params (wrapped in `<Suspense>` - the
  `useSearchParams` static-export requirement hit and fixed twice already
  this session) and passes them through to `createDraft`, with a small
  banner confirming what's being uploaded.

### Mobile
- `Video` model gained `allowDuets`/`allowStitches` (previously absent
  entirely on mobile despite existing on every other platform),
  `remixType`, `originalVideo`.
- Feed screen: Duet/Stitch icons in the engagement bar (shown only when
  allowed) opening `UploadScreen` with the original video's id/username/
  remix type pre-filled; attribution row in the video-info overlay.
- `UploadScreen` accepts and displays the remix context, passes it
  through `UploadService.createDraft`.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **251/251 passing**
  (up from 239; +12 new tests). Route registration checked directly.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 20 routes.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No actual side-by-side or clip-and-append video composition (see design
  note above) - a duet/stitch is a normal upload plus a link, not a
  composited video.
- No mobile screen lists a video's duets/stitches the way the web watch
  page does (mobile has no single-video detail screen at all yet, per
  the same limitation noted in Module 13).
- `POST /videos` (direct video creation) remains unused by any real
  client - kept working and tested since it's a reasonable direct-API
  surface, but flagged here so it isn't mistaken for the live path in
  future work.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications.
