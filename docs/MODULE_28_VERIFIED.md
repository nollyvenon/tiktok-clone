# Module 28: AI Agents — Verified Documentation

**Verification status: deferred.** Mid-way through Module 27 the user
asked to pause running tests/builds until the whole app is declared
complete. Everything in this module was written to the same standard as
every prior module (real HTTP-level tests, real UI wiring, no faked
behavior) but the backend test suite, `tsc`/`next build`, and
`flutter analyze`/`flutter test` have **not been run** for this module's
changes. That happens in the deferred, whole-app verification pass.

---

## Scoping: agents that orchestrate real operations, not a real LLM

The spec calls for "Core AI feature (LLM integration)" and an "agent
execution engine." This app has never had a real LLM integration
anywhere - `OPENAI_API_KEY` exists in `config.py` but is never actually
read by any service, and every "AI" feature built so far (captions,
voiceovers, background removal, color correction, trend suggestions) is
a simulated/rule-based operation tracked through the `AIGeneration`
audit trail, not a real model call.

Rather than fake an LLM-backed agent (which would misrepresent what the
app can do) or skip the module outright, "AI Agents" was scoped as what
an *execution engine* honestly means here: a named recipe (`AIAgent`)
that chains several of the already-fully-built AI Creator Studio
operations into a single one-click run against a segment, with a real
audit trail (`AgentExecution`) of what ran, in what order, and what each
step cost. This is a genuine "agent execution engine" in the sense the
term is used in workflow automation - a fixed pipeline of real actions,
not an autonomous reasoning loop - and doesn't claim to be more than
that.

## What was built

### Backend
- `AIAgent` model: `name`, `label`, `description`, `steps` (JSON array of
  `{operation, params}`), `sort_order`, `is_active`.
- `AgentExecutionStatus` enum (running/completed/failed) and
  `AgentExecution` model: `agent_id`, `user_id`, `segment_id`, `status`,
  `steps_log` (JSON array of per-step results), `total_credits_used`,
  `error_message`, `started_at`/`completed_at`.
- Migration `021_add_ai_agents.py`, seeding 3 canonical agents:
  - **Auto Polish** - auto color correction + smart framing (9:16)
  - **Caption & Clean** - auto captions + blurred background cleanup
  - **Full Enhance** - all four operations: background cleanup, color
    correction, captions, smart framing
- `AIAgentService` (new `app/services/ai_agents.py`):
  - `list_agents` - seed-on-read from `DEFAULT_AGENTS`, same pattern as
    `FilterPreset` in Module 21, so the SQLite test fixture and a fresh
    Postgres deployment behave identically.
  - `execute_agent` - loads the agent's steps, runs each one **in
    sequence** by calling the corresponding already-existing
    `AIService` method (`remove_background`, `generate_captions`,
    `apply_color_correction`, `get_frame_suggestions`) with the step's
    stored params, logging each step's result/credits/error. Fails fast:
    if a step raises, the execution is marked `failed` with the
    triggering step's error and the remaining steps are never run -
    matching how a real orchestration engine should behave, rather than
    silently skipping failures.
  - `list_my_executions` - the caller's own execution history, newest
    first.
- Routes: `GET /ai/agents` (public), `POST /ai/agents/{agent_id}/execute`
  (auth required, `segment_id` query param; verifies the segment's draft
  belongs to the caller, the same ownership check already used by every
  other AI Creator Studio route), `GET /ai/agents/executions` (auth
  required, caller's own history).
- 8 new HTTP-level tests (written, not yet run): agents list and expose
  their steps, `full_enhance` runs all four underlying operations and
  reports completed with credits > 0, ownership is enforced (403 for a
  non-owner), a nonexistent segment/agent is rejected (400), auth is
  required on execute and on the history endpoint, and execution history
  lists a caller's own runs.

### Web
- `edit/[draftId]` page: an "AI Agents — one-click recipes" row per
  segment, below the existing AI tools row - one button per agent
  (showing a running state while in flight), and a per-step result list
  (✓/✗ per operation, with the error message on failure) after a run
  completes.

### Mobile
- `AIService` (Dart): `AIAgent`/`AgentExecution`/`AgentStepResult`
  model classes, `getAgents`/`executeAgent`.
- `EditorScreen`: mirrors the web row - agent chips per segment with a
  running state, and the per-step result list underneath after a run.

---

## Known gaps

- No real LLM reasoning - agents are fixed, admin-defined step
  sequences, not free-form task planning. This is a deliberate scoping
  choice (see Scoping above), not an oversight.
- No user-defined/custom agents - only the 3 seeded canonical recipes
  exist; there's no UI to create a new agent or edit an existing one's
  steps.
- No cost/credit limit enforcement before running an agent - like every
  other AI Creator Studio operation, `credits_used` is tracked for
  display only and never actually gates anything.
- No retry of a failed step - a failed execution has to be re-run from
  the start via a fresh "Run agent" click.
- Verification (tests, `next build`, `flutter analyze`/`test`) has not
  been run for this module - see the note at the top of this doc.

Unchanged from prior modules: web token storage in `localStorage`, no
mobile OAuth, no rate limiting, no Redis caching, offset-based feed
pagination, no real-time delivery for messages/notifications, no video
composition for duets/stitches, no real payment processor, no beauty/AR
filters.
