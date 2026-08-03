# Module 16: Creator Shop — Verified Documentation

**Verification status: deferred.** The user paused running tests/builds
mid-session (2026-08-03) until the whole app is declared complete.
Everything in this module was written to the same standard as every
prior module (real HTTP-level tests, real UI wiring end to end, no
faked behavior) but the backend test suite, `tsc`/`next build`, and
`flutter analyze`/`flutter test` have **not been run** for this
module's changes yet - that happens in the deferred, whole-app
verification pass.

---

## Scoping: a real storefront and order system, with no real payment

The spec explicitly calls for "Security: Payment processing (Stripe)."
No module built in this app has ever had a real payment processor - the
same boundary was already drawn and documented for Creator Fund (Module
27) and Collaborations (Module 29). Creator Shop follows the identical
pattern: everything up to and including "placing an order" is fully
real - a creator lists real products with real stock tracking, a buyer
places a real order that really decrements stock and creates a
persisted record, and the seller has a real fulfill/cancel workflow.
What's missing is only the part that requires external infrastructure
this app doesn't have: no card is ever charged, "payment" is simply the
order existing with a status.

## Design decisions

- **One shop per user**, enforced with a unique constraint on
  `Shop.user_id`. `POST /shop/me` upserts - a second call updates the
  existing shop rather than erroring or creating a duplicate, since a
  creator naturally iterates on their shop's name/description over time.
- **Stock is optional, not required.** `stock_quantity = None` means
  unlimited (digital goods, made-to-order items); a set number is
  decremented on order and restored on cancellation. This mirrors how
  `FundingProgram`/`FilterPreset` use `None` for "not applicable" rather
  than a magic sentinel value.
- **`total_amount` is a snapshot at order time** (`price * quantity`),
  not a live lookup - so a seller changing a product's price later
  doesn't retroactively alter an already-placed order's total, the same
  reasoning already applied to Creator Fund's eligibility snapshot.
- **A seller can't order their own product** - an explicit check, since
  nothing else would prevent a creator from inflating their own "sales"
  in a system with no real payment to make that meaningless anyway.
- **Only pending orders can be fulfilled or cancelled** - once decided,
  an order's status is final, matching the same one-shot-decision
  pattern used for Creator Fund applications and Collaboration
  responses.

## What was built

### Backend
- `Shop`, `ShopProduct`, `ShopOrder` models (`ShopOrderStatus`:
  pending/fulfilled/cancelled). Products soft-delete via `deleted_at`,
  consistent with `Video`/`Comment`/`User`.
- `ShopService`: shop upsert/lookup (by id or by user id), product
  create/update/soft-delete (ownership-checked), `place_order` (stock
  check, self-order block, total snapshot), `list_my_orders`/
  `list_received_orders`, `fulfill_order`/`cancel_order`
  (seller-only, pending-only, cancellation restocks).
- Routes: `POST/GET /shop/me`, `GET /shop/{shop_id}`,
  `GET /shop/user/{user_id}` (discovery from a profile), `POST /shop/products`,
  `PUT/DELETE /shop/products/{id}`, `POST /shop/products/{id}/order`,
  `GET /shop/orders/me`, `GET /shop/orders/received`,
  `POST /shop/orders/{id}/fulfill`, `POST /shop/orders/{id}/cancel`.
  Route order was checked deliberately: `/shop/me`, `/shop/orders/*`,
  and `/shop/user/{id}` are all registered before the catch-all
  `GET /shop/{shop_id}`, so a request like `/shop/orders/me` can't be
  misrouted into the single-segment shop-by-id handler.
- Migration `022_add_creator_shop_tables.py`.
- 20 new HTTP-level tests (written, not yet run): shop create/update/
  404-when-none, product creation requires a shop, viewing a shop by id
  and by user id (plus the 400 when a user has no shop), product-update
  ownership (403 for a non-owner), soft-delete, order placement
  decrementing stock, insufficient-stock rejection, unlimited-stock
  always orderable, self-order rejection, ordering a nonexistent
  product, seller fulfill/cancel (with restock verified), a buyer unable
  to fulfill someone else's order, a second decision on an already-
  decided order rejected, listing both "my orders" and "received
  orders," and auth requirements.

### Web
- `/shop/manage`: shop details form (create/update), product list with
  add/delete, and a received-orders panel with fulfill/cancel actions -
  all gated behind having created a shop first.
- `/shop/[shopId]`: public storefront - product grid with price/stock
  and an Order button per product.
- `/shop/orders`: the buyer's own order history with status.
- Entry points: "My Shop" link added to the Creator Dashboard header
  (next to Creator Fund and Collaborations), "My Orders" added to the
  navbar's user menu (desktop dropdown and mobile menu), and a "Shop"
  button added to another user's profile page - shown only when that
  user actually has a shop (fetched via `GET /shop/user/{id}`, silently
  absent otherwise so it doesn't imply every creator sells things).

### Mobile
- `ShopService`/`Shop`/`ShopProduct`/`ShopOrder`/`ShopWithProducts`
  models, mirroring the web API client.
- `ManageShopScreen`, `ShopScreen` (storefront), `MyOrdersScreen` -
  mirror the three web pages.
- Entry points: a storefront AppBar icon on `DashboardScreen` (next to
  Creator Fund and Collaborations), "My Orders" added to the
  `SettingsScreen` hub, and a storefront icon button on another user's
  `ProfileScreen` when they have a shop.

---

## Known gaps

- No real payment processor - see Scoping above. This is the same
  documented boundary as Creator Fund and Collaborations, not an
  oversight specific to this module.
- No product images beyond an optional URL field - no upload flow, so a
  seller has to host an image elsewhere and paste the link.
- No shop discovery/browse page - a buyer finds a shop only via a
  specific creator's profile (if they have one) or a direct link; there's
  no `/shop` index listing all active shops.
- No email/push notification when an order is placed or decided.
- Verification (tests, `next build`, `flutter analyze`/`test`) has not
  been run for this module - see the note at the top of this doc.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches, no beauty/AR filters, no real LLM
integration.
