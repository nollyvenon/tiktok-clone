# Module 27: Creator Fund — Verified Documentation

Same standard as every prior verified doc: everything below was checked by
actually running it, not inferred from reading the code.

---

## Scoping: what's honestly buildable without a real payment processor

The spec's Monetization (18) and Creator Shop (16) modules explicitly call
for Stripe integration, which this app has never had anywhere - no module
built so far moves real money. Creator Fund's spec, by contrast, only
calls for "funding opportunities," "eligibility prediction," and "fund
distribution" - none of which strictly require real payment rails. The
scope built here treats an approved award as an internal ledger figure
(`awarded_amount`, in cents) recorded on the application row - the same
non-real-money boundary the rest of the app already has, made explicit
rather than glossed over.

The spec's "AI: Eligibility prediction" became a straightforward
rules-based eligibility check against the applicant's live stats
(followers, published videos, total views) rather than a trained model -
there's no training data or ML infra anywhere in this app, and a simple
threshold comparison is the honest equivalent for a project this size.
Final approval is still an explicit admin decision, mirroring the
Moderation/Admin Dashboard pattern where automated signals inform but
never replace a human decision.

## What was built

### Backend
- `FundingProgram` model: name, description, eligibility thresholds
  (`min_followers`, `min_published_videos`, `min_total_views`), and
  `award_amount` (cents), admin-managed.
- `CreatorApplication` model: one application per (program, user) pair
  (unique constraint), storing an eligibility *snapshot* at application
  time - `followers_count`/`published_videos_count`/`total_views_count`/
  `meets_requirements` - so a program's requirements changing later
  doesn't retroactively alter an already-submitted application's basis.
  `status` (pending/approved/rejected), `decision_reason`,
  `awarded_amount`, `reviewed_by`, `reviewed_at` form the audit trail.
- `CreatorFundService`: `list_active_programs`, `create_program`,
  `apply_to_program` (computes live stats, checks eligibility, rejects
  duplicate applications and applications to inactive programs),
  `list_my_applications`, `list_applications` (admin, filterable by
  status), `decide_application` (admin approve/reject; approval sets
  `awarded_amount` from the program's `award_amount`; rejects a
  double-decision on an already-decided application).
- Routes: `GET /creator-fund/programs`, `POST /creator-fund/programs`
  (admin), `POST /creator-fund/programs/{id}/apply`,
  `GET /creator-fund/me/applications`,
  `GET /creator-fund/admin/applications` (admin),
  `POST /creator-fund/admin/applications/{id}/decide` (admin).
- Alembic migration `018_add_creator_fund_tables.py` for both tables.
- 13 new HTTP-level tests covering: admin-only program creation,
  listing active programs, applying when requirements are met/unmet,
  duplicate-application rejection, applying to a nonexistent/inactive
  program, auth requirements, listing your own applications, admin
  approve (verifying the awarded amount matches the program), admin
  reject, rejecting a second decision on an already-decided application,
  and non-admin access being blocked on both admin endpoints.

### Web
- `/creator-fund`: lists active programs with their requirements and
  award amount, an "Apply"/"Applied" button per program, and a list of
  the creator's own applications with status and (if approved) the
  awarded amount.
- `/admin/creator-fund`: status-filtered admin queue (pending/approved/
  rejected) with approve/reject actions, added as a new tab in the
  shared `AdminNav`.
- A "Creator Fund" link added to the Creator Dashboard header - the
  natural entry point for a creator, mirroring how Settings was reached
  from the navbar.

### Mobile
- `CreatorFundScreen`: mirrors the web creator-facing page - program
  list with apply action, and the creator's own applications with
  status. Reached via a new AppBar action on `DashboardScreen`.
- No mobile admin review screen was built - Module 25 (Admin Dashboard)
  already established that admin surfaces are web-focused on this app;
  the admin review queue here follows the same precedent.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **304/304 passing**
  (up from 291; +13 new tests, all in `test_creator_fund.py`). Route
  registration checked directly via `app.routes` introspection - no path
  conflicts among the six new `creator-fund` routes.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 29 routes
  including `/creator-fund` and `/admin/creator-fund`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Bugs found and fixed during this pass

- The first test-suite run for `_make_follows` failed because it created
  `Follow` rows with a random, non-existent `follower_id`. The SQLite
  test fixture enforces foreign keys (`PRAGMA foreign_keys=ON`, added in
  Module 17), so this correctly rejected the row rather than silently
  accepting a dangling reference. Fixed by registering real follower
  users in the test instead of fabricating UUIDs - not a bug in the
  service, but a reminder that this fixture keeps catching exactly the
  class of bug it was added for.

## Known gaps

- No real payment processor - `awarded_amount` is an internal ledger
  figure only, consistent with every other part of this app.
- No AI/ML eligibility prediction - eligibility is a straightforward
  threshold check against live stats, not a trained model.
- No mobile admin review screen (web-only, matching Module 25's
  precedent for admin surfaces).
- No email/push notification when an application is decided - creators
  find out by checking the Creator Fund page again.
- No pagination on the creator-facing `/creator-fund` program list or
  "my applications" list - fine at demo scale, would need it at real
  scale.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
