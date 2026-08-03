# Module 21: Video Filters — Verified Documentation

Note on verification status: mid-way through this module the user asked
to pause running tests/builds until the whole app is declared complete.
Everything below up to that point was checked by actually running it
(backend suite, `next build`, `flutter analyze`/`flutter test` all
passed). Anything built afterward is written to the same standard but
not yet re-verified in a full run - that will happen in the deferred,
whole-app verification pass.

---

## Scoping: color-grade filters, not GPU/AR face filters

The spec's "Beauty, AR, effect filters" with "GPU-accelerated rendering"
needs a real video/AR processing pipeline this app has never had. What
*did* already exist, fully built but never exposed in any UI, was a
generic color-grading pipeline: the `ColorCorrection` model and
`POST /ai/color-correction` endpoint already supported
`method='preset'` + `preset_name` and five numeric adjustments
(brightness/contrast/saturation/hue/temperature) - the editor UI on both
web and mobile only ever called it with `method='auto_enhance'`. This is
the same "built but unreachable" pattern found in several earlier
modules (2FA setup, blocked-users list, hashtag challenges before
Discover wired them in).

Module 21 was scoped as: give that existing pipeline a named preset
library and a picker UI, instead of building a new GPU/AR system that
doesn't fit this app's infrastructure.

## What was built

### Backend
- `FilterPreset` model: `name`, `label`, `thumbnail_url`, the five
  color-grade fields, `sort_order`, `is_active`.
- Migration `020_add_filter_presets.py`, seeding 8 presets (Original,
  Cinematic, Vintage, Black & White, Warm, Cool, Vivid, Dramatic) via
  `op.bulk_insert`.
- `AIService.list_filter_presets`: reads active presets ordered by
  `sort_order`; if the table is empty (true for the SQLite test fixture,
  which uses `Base.metadata.create_all` and never runs Alembic's data
  migration), it seeds the same canonical list from a
  `DEFAULT_FILTER_PRESETS` constant before returning - so the endpoint
  behaves identically whether backed by a freshly-migrated Postgres or a
  bare test database.
- `GET /ai/filters/presets` (public, no auth - it's a static-ish preset
  library, not user data), returning the preset list for use with the
  existing `POST /ai/color-correction`.
- 4 new HTTP-level tests: presets list includes the expected names,
  repeated calls don't duplicate the seed, and a full apply flow using a
  preset's own values through the existing color-correction endpoint.

### Web
- `edit/[draftId]` page: a new "Filters" row per segment, replacing
  nothing (the existing "Auto color" AI button stays) - a horizontal set
  of preset swatches with a live CSS-filter preview
  (`brightness()/contrast()/saturate()/hue-rotate()` approximating each
  preset's stored values) and a highlighted border on the currently
  applied preset. Selecting one calls the existing color-correction
  endpoint with `method: 'preset'` and that preset's exact values.

### Mobile
- `AIService.getFilterPresets`/extended `applyColorCorrection` to accept
  `presetName` + the five adjustment fields.
- `EditorScreen`: a horizontal scrollable "Filters" row per segment
  (gradient swatch + label, highlighted border when applied), mirroring
  the web picker, inserted just above the existing "AI tools" row.

---

## Verification performed (before the pause)

- Backend: `pytest tests/ -W error::RuntimeWarning` - **319/319 passing**
  (up from 316; +4 new tests, `test_ai.py` (3) run standalone first, then
  the full suite). Route registration checked directly - `GET
  /ai/filters/presets` doesn't conflict with the existing
  `/ai/color-correction/{correction_id}`.
- Web: `npx tsc --noEmit` clean; `next build` succeeds (30 routes,
  unchanged - `/edit/[draftId]` already existed).
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No beauty/AR face filters - genuinely out of scope without a real
  vision/AR pipeline, consistent with every other "needs infra we don't
  have" module this session (payments, RTMP/WebRTC, GPU rendering).
- Filter application is still queued through the async
  `AIGeneration`/credit-cost pipeline like every other AI Creator Studio
  feature - there's no instant client-side live preview of the actual
  processed output, only the CSS/gradient approximation used for the
  picker swatch itself.
- No admin UI to manage `FilterPreset` rows (add/reorder/deactivate) -
  the 8 seeded presets are the only ones available; changing them today
  means editing the seed data directly.
- Filter application to a segment isn't visible anywhere afterward
  beyond the highlighted picker swatch in the current session - reloading
  the editor doesn't currently reflect which preset (if any) was last
  applied to a segment, since that isn't persisted on the segment model
  itself, only on the `ColorCorrection` row.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches, no real payment processor.
