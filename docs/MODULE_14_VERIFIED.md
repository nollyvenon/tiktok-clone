# Module 14: Direct Messaging — Verified Documentation

Same standard as the prior verified docs: everything below was checked by
actually running it, not inferred from reading the code.

---

## Starting point: nothing but a fictional stub

Like Modules 10 and 11, this module had **no models, service, routes,
schemas, or migration at all** - only a commented-out
`# app.include_router(messages.router, ...)` placeholder in `main.py`. The
web side additionally had a fully fictional `messageApi` in `lib/api.ts`
(and matching camelCase `Message`/`Conversation` types) that had clearly
been written speculatively against an imagined API shape: it wrapped every
response in a nonexistent `{ data: ... }` envelope, called
`/api/conversations/{id}/messages` (missing the `/messages` prefix
entirely), and sent `participantId` in a JSON body instead of
`recipient_id` as a query param - the same pattern of pre-written, never-
tested stubs found in every other module's frontend this session.
Rewrote both to match the real backend built in this pass.

## Design decisions made while building

- **1-on-1 only**, per spec scope. `Conversation.user1_id`/`user2_id`
  are stored in canonical (lexicographically-sorted) order so the same
  pair always resolves to the same row regardless of who messages first -
  verified with `test_conversation_same_regardless_of_who_starts_it` and
  `test_start_conversation_is_idempotent`.
- **REST only, no WebSocket.** The spec calls for real-time delivery, but
  there is no WebSocket/pub-sub infrastructure anywhere in this codebase
  (confirmed by searching the whole project) - adding one from scratch for
  a single feature would be a much larger, separate infrastructure
  project. Instead this follows the exact precedent already set by
  Module 10 (notifications shipped with no push-delivery infra, documented
  as a known gap): messages are sent via REST and the chat screen
  short-polls every 4 seconds on both web and mobile. This is called out
  explicitly in both `ChatDetailScreen` (mobile) and the watch-page-style
  polling comment (web) so it isn't mistaken for an oversight later.
- **Blocking is enforced at both ends of the message lifecycle**: you
  can't start a conversation with someone who has blocked you (or whom
  you've blocked), and - separately - blocking someone *after* a
  conversation already exists immediately stops further messages in
  either direction, even though the conversation and message history
  remain visible. Covered by
  `test_blocked_user_cannot_start_conversation` and
  `test_blocking_mid_conversation_stops_new_messages`.
- Sending a message reuses `NotificationService.send_notification` with
  the `NotificationType.MESSAGE` type and `message_notifications`
  preference flag - both of which already existed on the `Notification`/
  `NotificationPreference` models from Module 10 but were unused until
  now, since nothing produced a MESSAGE notification before this module.

---

## What was built

### Backend
- `models.py`: `Conversation` (canonical user1/user2 ordering, unique
  constraint on the pair, `last_message_at` for sorting) and `Message`
  (soft-deletable, though delete isn't exposed via any endpoint yet - see
  gaps).
- `schemas.py`: `MessageCreate`, `MessageResponse`, `MessageListResponse`,
  `ConversationResponse` (includes the other participant, last message
  preview, and unread count - all computed from the *requesting* user's
  point of view), `ConversationListResponse`.
- `services/messages.py`: `get_or_create_conversation`,
  `get_user_conversations`, `send_message`, `get_messages` (oldest-first,
  chat order), `mark_conversation_read`, plus the block-enforcement and
  canonical-ordering logic above.
- `routes/messages.py`: `POST/GET /messages/conversations`,
  `GET/POST /messages/conversations/{id}/messages`,
  `PUT /messages/conversations/{id}/read` - mounted with its own
  `/messages` prefix, consistent with every other router in this project.
- `migrations/versions/013_add_message_tables.py`.
- Written HTTP-level from the start (`test_messages.py`, 15 tests),
  continuing the rule established after Module 10.

### Web
- `/messages`: conversation list with unread dot, last-message preview,
  relative timestamps.
- `/messages/[id]`: chat thread, sends on Enter or button click, marks
  the conversation read on open, polls every 4s for new messages.
- Wired the profile page's message-icon button - previously a dead
  `<button>` with no `onClick` at all - to start a conversation and
  navigate to the thread. Disabled (along with Follow) when the viewed
  user is blocked.
- Fixed the fictional `messageApi`/`Message`/`Conversation` types
  described above.
- Added a Messages icon to the navbar.

### Mobile
- `models/message.dart` (`ChatMessage`, `Conversation`, reusing
  `VideoAuthor` for the other participant), `services/message_service.dart`.
- `MessagesScreen` (conversation list) and `ChatDetailScreen` (thread,
  same 4s polling as web).
- Wired into `ProfileScreen`: a Messages icon in the own-profile app bar,
  and a message button next to Follow on other users' profiles (disabled
  when blocked, matching web).

---

## Verification performed

- Backend: `pytest tests/ -W error::RuntimeWarning` - **239/239 passing**
  (up from 226; +15 new tests). Route registration checked directly for
  conflicts.
- Web: `npx tsc --noEmit` clean; `next build` succeeds, 20 routes
  including `/messages` and `/messages/[id]`.
- Mobile: `flutter analyze` - 0 issues; `flutter test` - 2/2 passing.

## Known gaps

- **No real-time delivery** (no WebSocket infrastructure exists anywhere
  in this project) - both clients poll every 4 seconds instead. This is
  the single biggest gap relative to the spec, which calls for
  "real-time 1-on-1 messaging."
- No typing indicators (would require the same real-time transport this
  module doesn't have).
- No message editing or deletion exposed via any endpoint (the `Message`
  model has `deleted_at` for future use, but nothing sets it yet).
- No smart reply suggestions (spec's AI bullet) - no LLM integration
  reads message content.
- No encryption at rest or in transit beyond standard TLS (spec's
  "Security: Encryption" bullet is aspirational, same honesty standard
  applied to every other module's unimplemented security bullets).
- No media/image messages, text only.
- No pagination UI beyond a single page of up to 50 conversations / 50
  messages on either platform.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination.
