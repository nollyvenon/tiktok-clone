# Module 25: Admin Dashboard — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: `require_admin` existed, nothing used it beyond the moderation queue

Module 26 (built the prior pass) added the first-ever admin authorization
check in this codebase and a report review queue. What it didn't cover -
and what's specifically Module 25's scope per the spec - was platform-wide
visibility (stats) and direct user management: before this pass, the
*only* way to suspend a user was to decide a report against them. An
admin had no way to look up a user directly and act on their account
without someone reporting them first, and no aggregate view of the
platform (user counts, content counts, report backlog) existed anywhere.

## Design decisions

- **No new tables.** Everything here reads existing data
  (`User`, `Video`, `Comment`, `ContentReport`, `ModerationDecision`) -
  the "admin_reports" table the spec mentions is already `ContentReport`
  from Module 26, and "audit_logs" is already `ModerationDecision`. This
  module is purely a new read/management surface over data that already
  exists, not a new data model.
- **Direct suspend/reactivate is a separate path from the report-driven
  suspend/ban actions in the moderation queue.** Both ultimately just
  flip `User.is_active`, but conceptually: the moderation queue's
  `suspend_user`/`ban_user` actions are *responses to a specific report*
  and get logged as a `ModerationDecision`; `AdminService.set_user_active`
  is a direct action an admin can take on any user account without a
  report existing at all (e.g. proactively, or based on an external
  signal). Neither path is redundant - removing either would leave a real
  gap.
- **The audit log is read-only and enriches `ModerationDecision`** with
  the moderator's username and the originating report's content type/
  reason at query time, rather than denormalizing that data onto the
  decision row - decisions are immutable once created, so there's no
  data-drift risk in doing the join per-request.
- **No role promotion/demotion endpoint.** Making another user an admin
  is a highly sensitive, hard-to-audit action; scoping it out here rather
  than exposing a fast, undertested path to privilege escalation. Table
  stakes for a first pass at admin tooling are stats + user suspension +
  an audit trail - role management is flagged as a known gap rather than
  rushed.
- **No mobile UI**, per the spec's own guidance ("Mobile: Limited admin
  panel (web-focused)") - this is an explicit scope decision matching
  the spec, not an oversight the way other "no mobile" gaps in this
  project have been.

---

## What was built

### Backend
- `AdminService.get_stats`: total/active/suspended user counts, total
  non-deleted videos and comments, and a breakdown of reports by status
  (pending/actioned/dismissed).
- `AdminService.get_users`: paginated, searchable (username or email,
  case-insensitive) user list for management.
- `AdminService.set_user_active` / `POST /admin/users/{id}/suspend` and
  `/reactivate`: the direct admin path described above.
- `AdminService.get_audit_log`: paginated `ModerationDecision` history,
  enriched with moderator username and report context.
- `require_admin`-gated routes for all of the above: `GET /admin/stats`,
  `GET /admin/users`, `POST /admin/users/{id}/suspend`,
  `POST /admin/users/{id}/reactivate`, `GET /admin/audit-log`.
- No migration needed - every table already existed.
- 10 new HTTP-level tests: 403 for non-admins on every endpoint, stats
  aggregation correctness, user list/search, suspend-then-verify-login-
  fails, reactivate-then-verify-login-succeeds, suspending a nonexistent
  user, and the audit log correctly showing a decision made through the
  Module 26 moderation queue (proving the two features share the same
  underlying data correctly).

### Web
- `/admin` (Overview): stat cards.
- `/admin/users`: searchable user list with suspend/reactivate actions
  and status badges (admin, suspended).
- `/admin/audit-log`: chronological decision history.
- `/admin/moderation` (already existed from Module 26): now shares the
  same `AdminNav` tab bar as the three new pages, unifying what were
  previously two disconnected admin surfaces into one dashboard.
- All four pages client-side gate on `user.role === 'admin'` (the server
  enforces this regardless via `require_admin` on every endpoint - the
  gate is just so non-admins don't see a broken-looking page).

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **286/286 passing**
  (up from 276; +10 new tests). Route registration checked directly.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 24 routes
  including all four `/admin/*` pages.
- Mobile: not touched this pass (see design decision above) -
  `flutter analyze`/`flutter test` were last verified clean at the end
  of Module 26 and nothing in this pass changed any mobile code.

## Known gaps

- No role promotion/demotion UI (see design decision above).
- No automated content flagging feeding the stats/queue (spec's Module
  26 AI bullet, still unaddressed).
- No time-series charting on the overview (current-state counts only,
  same limitation as the Module 17 creator dashboard).
- No pagination UI on the user list or audit log beyond a single page of
  up to 50/100 rows.
- Suspending a user directly (this module) and suspending via a
  moderation decision (Module 26) both just flip `is_active` - there's
  still no distinction between a temporary suspension and a permanent
  ban anywhere in the system.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
