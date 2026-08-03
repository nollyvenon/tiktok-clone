# Module 18: Monetization — Verified Documentation

**Verification status: deferred.** The user paused running tests/builds
mid-session (2026-08-03) until the whole app is declared complete.
Everything in this module was written to the same standard as every
prior module (real HTTP-level tests, real UI wiring end to end, no
faked behavior) but the backend test suite, `tsc`/`next build`, and
`flutter analyze`/`flutter test` have **not been run** for this
module's changes yet - that happens in the deferred, whole-app
verification pass.

---

## Scoping: a real earnings ledger over records that already exist

The spec calls for "Earnings tracking, payouts" with "Security: Payment
processor integration." As with every money-adjacent module this
session (Creator Fund, Collaborations, Creator Shop), no real payment
processor exists anywhere in this app. What makes Monetization different
from those modules is that by this point in the build, two *real*
sources of "earnings" already exist and are already fully functional:
an approved Creator Fund application's `awarded_amount`, and a fulfilled
Shop order's `total_amount`. Monetization was scoped as the layer that
turns those two existing, real events into an actual earnings ledger
and a real (admin-reviewed) payout-request workflow - genuinely useful
functionality, not a UI shell around numbers that don't mean anything.

## Design decisions

- **`Earning` rows are created automatically, not manually.** A
  `CreatorFundService.decide_application` approval and a
  `ShopService.fulfill_order` call each insert an `Earning` row in the
  same transaction as the underlying decision - there's no separate
  "credit my earnings" action a user has to remember to take, and no
  path for an approved fund application or fulfilled order to exist
  without a matching ledger entry.
- **Polymorphic source via two nullable FKs + a CHECK constraint**,
  exactly the pattern already established by `ContentReport`
  (Module 26) for "exactly one of several possible targets": either
  `fund_application_id` or `shop_order_id` is set, never both, never
  neither.
- **Available balance is computed, not stored**: `total_earned -
  total_paid_out - pending_payout_total`. A *pending* payout request
  already reduces what's available to request again - so a creator
  can't request the same balance twice while the first request is still
  awaiting an admin decision. This mirrors how Creator Fund and
  Collaborations both use one-shot-decision state to prevent the same
  class of double-action bug.
- **A payout is "completed" only by explicit admin decision** - the
  same human-in-the-loop pattern used for Creator Fund applications,
  Moderation decisions, and Collaboration responses throughout this
  project. Admin notes on a decision (e.g. "Paid via bank transfer") are
  the honest record of *how* a payout was actually settled outside this
  app, since this app has no way to settle it itself.

## What was built

### Backend
- `EarningSourceType` enum (creator_fund/shop_order) and `Earning`
  model (polymorphic source, amount in cents).
- `PayoutStatus` enum (pending/completed/cancelled) and `Payout` model
  (amount, decided_by, notes, requested_at/decided_at).
- `CreatorFundService.decide_application` and `ShopService.fulfill_order`
  both updated to create an `Earning` row on success - the only changes
  to existing modules this pass required.
- `MonetizationService`: `get_earnings_summary` (totals + full earnings
  list), `request_payout` (validated against available balance),
  `list_my_payouts`, `list_payouts`/`decide_payout` (admin).
- Routes: `GET /monetization/summary`, `POST /monetization/payouts`,
  `GET /monetization/payouts/me`, `GET /monetization/admin/payouts`,
  `POST /monetization/admin/payouts/{id}/decide`.
- Migration `023_add_monetization_tables.py`.
- 12 new HTTP-level tests (written, not yet run): zero-earnings summary,
  a Creator Fund approval crediting an earning, a Shop order fulfillment
  crediting an earning, requesting a payout within balance, exceeding
  balance rejected, a pending payout reducing what a second request can
  draw against, admin completing a payout (and the summary reflecting
  it), a second decision on an already-decided payout rejected, non-admin
  blocked from the admin endpoints, listing a creator's own payouts, and
  auth requirements.

### Web
- `/monetization`: stat cards (total earned/paid out/pending/available),
  a payout-request form, the creator's own payout requests with status,
  and a full earnings history list labeled by source.
- `/admin/payouts`: status-filtered admin queue with "Mark Paid"/"Cancel"
  actions, added as a new `AdminNav` tab.
- Linked from the Creator Dashboard header, alongside Creator Fund,
  Collaborations, and My Shop.

### Mobile
- `MonetizationService`/`EarningsSummary`/`Earning`/`Payout` models.
- `MonetizationScreen`: mirrors the web dashboard - stat cards, payout
  request form, payout list, earnings history. Reached via a new AppBar
  action on `DashboardScreen`.
- No mobile admin payout-review screen - admin surfaces stay web-only,
  following the precedent set in Module 25 (Admin Dashboard).

---

## Known gaps

- No real payment processor - see Scoping above. Same documented
  boundary as Creator Fund, Collaborations, and Creator Shop.
- Only two earning sources exist (Creator Fund awards, fulfilled Shop
  orders) - no ad revenue, tips, or subscription income, since none of
  those features exist elsewhere in this app either.
- No partial-payout accounting nuance beyond a flat available-balance
  check - no minimum payout threshold, no payout scheduling.
- No email/push notification when a payout is decided.
- Verification (tests, `next build`, `flutter analyze`/`test`) has not
  been run for this module - see the note at the top of this doc.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches, no beauty/AR filters, no real LLM
integration, no RTMP/WebRTC live streaming.
