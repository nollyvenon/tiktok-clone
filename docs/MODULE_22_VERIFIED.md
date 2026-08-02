# Module 22: Music/Sound Library — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: a browse UI over a permanently empty, permanently disconnected catalog

`SoundRecommendation` (title, artist, category, mood, genre, license) and
two browse endpoints (`/ai/sounds/recommendations`, `/ai/sounds/trending`)
already existed, and the web editor already had a "Browse sounds" section.
Three separate, compounding gaps meant none of it actually worked:

1. **Nothing anywhere ever created a `SoundRecommendation` row.** No seed
   script, no admin endpoint, no user-facing contribute flow - grepping
   the entire codebase found zero `SoundRecommendation(...)` constructor
   calls outside the model file itself. The browse UI would show "No
   sounds found" in every real deployment, forever.
2. **Even if a sound existed, there was no "select" action.** The
   browse UI rendered title/artist/trending-badge with no button, no
   click handler - purely decorative.
3. **Even if selection existed, it couldn't have reached a published
   video.** `Video.music_id` was a bare `UUID` column with no foreign
   key at all, and it only appeared on `VideoCreate`/`POST /videos` - the
   same dead direct-create endpoint discovered in Modules 19-20 that no
   real client ever calls. The actual publish pipeline
   (`Draft` → `publish_draft`) had no `music_id` concept whatsoever.

All three had to be fixed for "attach a sound to your video" to become a
real, working feature rather than three independent no-ops that looked
like one broken feature.

## A schema design mistake caught immediately by the FK-enforcement fixture from Module 17

The first attempt made `SoundRecommendation.draft_id` (previously a
required FK, despite every browse query already ignoring it) nullable
and added `Draft.music_id → sound_recommendations.id`. That created a
genuine circular foreign key: `drafts.music_id → sound_recommendations.id`
and `sound_recommendations.draft_id → drafts.id`. Because Module 17's
test fixture change turned on real SQLite foreign-key enforcement, this
surfaced immediately as `Base.metadata.drop_all()` failing at test
teardown with "Can't sort tables for DROP: unresolvable foreign key
dependency" - cascading into every other test in the file via a broken
fixture, not just the new ones.

Root cause fix, not a workaround: `sound_recommendations.draft_id` was
never read or written anywhere in the codebase (confirmed by grep before
touching it), so it was removed outright rather than patched with
`use_alter=True`. A permanently-unused column masquerading as a real
relationship is exactly the kind of dead weight this project avoids
elsewhere.

## A second bug found once FK enforcement was actually exercised end-to-end

With `Video.music_id` and `Draft.music_id` now real foreign keys,
submitting a fabricated `music_id` at **draft creation** time raised a
raw `IntegrityError` 500 instead of a clean error - because the FK
constraint itself rejects the row before any application-level
validation runs. Unlike the duet/stitch permission checks (which
genuinely need to be re-checked at publish time since permissions can
change), *existence* of a referenced video/sound can't become false
between draft-save and publish under a real FK constraint - so the fix
here is to validate existence up front, at draft create/update time, and
return a clean 400. This also retroactively closes the same latent gap
for `original_video_id` from Modules 19-20, which had never been tested
with a truly nonexistent video ID.

---

## What was built

### Backend
- Removed `SoundRecommendation.draft_id`; added `Draft.music_id` and a
  real FK on `Video.music_id` (previously bare, unvalidated).
  `migrations/versions/016_add_music_library.py`.
- `get_sound_recommendations`/`get_trending_sounds` now match
  `region IN (requested_region, 'Global')` - previously an exact-match
  filter meant a sound contributed as "Global" would never surface in
  any specific region's default browse.
- `AIService.create_sound` / `POST /ai/sounds` - any authenticated user
  can contribute a sound to the shared library (mirrors how Challenges
  are user-created in this app, not admin-seeded).
- `VideoService.validate_music` (existence check, shared between the
  direct-create path and the draft pipeline) and
  `VideoService.get_videos_using_sound`.
- `UploadService._validate_draft_references` - validates
  `original_video_id` and `music_id` at draft create/update time now,
  not just at publish; `publish_draft` copies `music_id` through to the
  created `Video` (the real, client-facing wiring that was missing
  entirely before).
- `GET /ai/sounds/{id}/videos` - videos using a given sound.
- `MusicPreview` attribution added to `VideoDetailResponse`, wired
  through all 7 places a video response gets built (feed, trending,
  search, single video, user videos, bookmarks, remixes) via a shared
  `_build_music_preview` helper, mirroring the pattern already
  established for duet/stitch attribution.
- 9 new HTTP-level tests: creating and browsing a sound, the
  Global-region visibility fix, attaching a sound through the real
  publish pipeline and seeing attribution on the resulting video,
  rejecting a fabricated sound at draft-save time, and listing videos by
  sound.

### Web
- Editor's sound browser gained an actual "Use this sound" button per
  row, calling `getDraft` + `updateDraft` (full-replace PUT, so the
  current draft is fetched first and merged rather than blindly
  overwritten - `DraftCreate`'s other fields would otherwise silently
  reset to defaults).
- Watch page: music attribution row (title + artist, linking to
  `/sounds/[id]`) alongside the existing duet/stitch attribution.
- New `/sounds/[id]` page: a grid of videos using that sound.

### Mobile
- `Draft` model gained `musicId` (and, closing a pre-existing gap,
  `allowComments`/`allowDuets`/`allowStitches`/`originalVideoId`/
  `remixType`, which had never been added to the mobile Draft model even
  when Modules 19-20 shipped) plus `copyWith`/`toUpdateJson`.
- `UploadService.getDraft`/`updateDraft` added (didn't exist at all
  before this pass - mobile had no way to modify a saved draft).
- Editor screen: "Use"/"Using" button per sound, mirroring web.
- `Video` model gained `MusicPreview`; feed's video-info overlay shows
  the attached sound, mirroring the existing duet/stitch attribution row.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **262/262 passing**
  (up from 256; +9 new tests, minus the one rewritten to match the
  corrected fail-fast behavior). Route registration checked directly.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 21 routes
  including `/sounds/[id]`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No AI music recommendation (spec's AI bullet) - browse is
  category/mood/region filtering only, no personalization.
- No licensing enforcement beyond storing a `license_type` string - no
  verification that a contributed sound's stated license is accurate.
- No audio trimming/syncing UI (choosing which portion of a track plays
  under the video) - attaching a sound is all-or-nothing.
- No mobile screen for "videos using this sound" (mirrors the same
  no-single-video-detail-screen limitation noted in Modules 13, 19-20).

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
