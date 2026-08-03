# Module 29: Collaborations — Verified Documentation

Same standard as every prior verified doc: everything below was checked
by actually running it, not inferred from reading the code.

---

## Scoping: revenue split as a recorded agreement, not a money transfer

The spec calls for "team content creation" with a "profit split" and
"revenue split verification." As with Creator Fund (Module 27), nothing
in this app moves real money, so the honest scope is a revenue split
that's *agreed and recorded* - a percentage on each collaborator's row -
rather than one that's actually paid out. The "AI: Team recommendation"
bullet was dropped rather than faked: there's no signal in this app (past
collaboration history, follower overlap, etc.) that would make a
recommendation meaningful yet, and a placeholder suggestion box that
recommends nothing real would be worse than not having it.

## Design decisions

- **The initiator is a collaborator row, not a separate concept.** A
  `Collaboration` has an `initiator_id` for authorization (only they can
  create it or cancel it), but the initiator's own revenue share is just
  another `Collaborator` row with `is_initiator=True`, pre-accepted at
  creation time. This means the split validation logic (splits across
  all collaborators must sum to exactly 100) doesn't need a special case
  for "the owner's implicit remainder" - every participant, initiator
  included, states their share explicitly and it's checked the same way.
- **Collaboration status is derived, not set directly.** A collaboration
  starts `pending`. If every collaborator accepts, it becomes `active`
  automatically. If *any* collaborator declines, it's immediately
  `cancelled` - one decline kills the whole arrangement rather than
  leaving it in limbo, since a partial team with an unassigned share
  doesn't make sense to keep open.
- **Splits are locked in at creation**, not renegotiated after invites go
  out - if the split needs to change, the initiator cancels and creates
  a new collaboration. This keeps the accept/decline semantics simple:
  a collaborator is agreeing to a specific, fixed percentage.

## What was built

### Backend
- `Collaboration` model: `video_id`, `initiator_id`, `title`, `status`
  (pending/active/cancelled).
- `Collaborator` model: `collaboration_id`, `user_id`,
  `revenue_split_percent`, `is_initiator`, `status`
  (invited/accepted/declined), `responded_at`. Unique constraint on
  (collaboration, user) - one row per participant.
- `CollaborationService`: `create_collaboration` (verifies the caller
  owns the video, that they're included among the collaborators, and -
  via the schema validator - that splits sum to exactly 100 and no user
  appears twice), `respond` (accept/decline, deriving the collaboration's
  overall status), `cancel` (initiator-only, while still pending),
  `list_my_collaborations` (both as initiator and as an invited
  collaborator), `get_collaboration` (participants only).
- Routes: `POST /collaborations`, `GET /collaborations/me`,
  `GET /collaborations/{id}`, `POST /collaborations/{id}/respond`,
  `POST /collaborations/{id}/cancel`.
- Alembic migration `019_add_collaboration_tables.py`.
- 12 new HTTP-level tests: ownership required to create, splits must sum
  to 100 (Pydantic validation), initiator must be included, the full
  workflow to `active`, a decline cancelling the whole collaboration, an
  uninvited user unable to respond, no double-responding, initiator-only
  cancellation, non-initiator cancellation rejected, listing collaborations
  from both roles, non-participants blocked from viewing, and auth
  required to create.

### Web
- `/collaborations`: a form to start a collaboration (pick one of your
  own videos, set your own split, search creators by username and add
  them with a split), plus a list of your collaborations showing every
  participant's share and status, with accept/decline for pending
  invitations and cancel for your own pending collaborations.
- Linked from the Creator Dashboard header, next to the Creator Fund
  link added in Module 27.

### Mobile
- `CollaborationsScreen`: mirrors the web page - create form with a
  video dropdown (via a new `FeedService.getUserVideos`), username
  search (via a new `ProfileService.searchCreators`), and the same
  accept/decline/cancel list. Reached via a new AppBar action on
  `DashboardScreen`, next to the Creator Fund action.

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **316/316 passing**
  (up from 304; +12 new tests, all in `test_collaborations.py`). Route
  registration checked directly via `app.routes` introspection -
  `/collaborations/me` is registered ahead of
  `/collaborations/{collaboration_id}`, so it isn't shadowed by the
  dynamic route.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 30 routes
  including `/collaborations`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- No real payment processor - revenue splits are recorded percentages
  only, consistent with Creator Fund and every other part of this app.
- No AI-driven team recommendations (dropped rather than faked - see
  Scoping above).
- No renegotiation flow - a collaborator who wants a different split has
  to be re-invited into a new collaboration.
- No notification when you're invited to collaborate - you find out by
  opening the Collaborations page/screen again.
- No pagination on "my collaborations" - fine at demo scale.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches.
