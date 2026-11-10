<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §5 — Turn off the Anthropic SDK's own OpenTelemetry spans

**Type:** fix
**Originator:** the owner, from §4's live check
**Source:** §4's `metadata.yml` on `main` (9d83a5d): `live_checked: … # owner:
"passed" (extra anthropic.messages.create traces from the Anthropic SDK's
own OTel: pre-existing, follow-up fix)`

## Problem

A run with tracing on should give exactly one Langfuse trace (§1 spec B15:
"each CLI run produces exactly one Langfuse trace"). With the Anthropic
provider, the owner sees extra traces named `anthropic.messages.create`
next to the run's `advisor-run` trace, one per model call.

Why, as read in the installed SDKs:
- `anthropic` 2.6.0 traces every API call with OpenTelemetry by default.
  `anthropic.Anthropic(api_key='k')` resolves to `_open_telemetry["traces"]
  ["enabled"] == True` (probe, 2026-11-10).
- Its spans go to the global tracer provider, which the Langfuse SDK
  registers (`langfuse/_client/resource_manager.py:648-658`).
- `src/advisor/tracing.py` starts its observations with `start_observation`
  without making them the current context. So the SDK's span has no parent,
  and Langfuse shows it as a separate root trace.
- The adapter builds the client with no option:
  `src/advisor/models/anthropic_model.py:59`, `anthropic.Anthropic(api_key=api_key)`.

## Outcome

- The Anthropic adapter builds its SDK client with the SDK's OpenTelemetry
  tracing off. A run with tracing on yields one trace (`advisor-run`), with
  no `anthropic.messages.create` trace beside it.
- A test that fails on today's `main` proves the client is built with
  traces off.
- The `ANTHROPIC_OPEN_TELEMETRY` environment variable cannot turn the spans
  back on, because an explicit client option overrides it.

## Constraints

- **Architecture:** the change stays in `models/anthropic_model.py`, the
  only module that imports `anthropic` (`tests/test_boundaries.py`).
  `tracing.py` and the `Tracer` protocol are unchanged.
- **The suite stays offline:** no live Anthropic call; `conftest.py`'s
  socket block stays.
- **No new dependency.** The option exists in the locked `anthropic` 2.6.0.
- **Data:** the SDK spans record metadata only (`content_mode:
  metadata_only`) and go to the self-hosted Langfuse. Nothing leaked, and
  this fix removes them.
- **Out of scope:**
  - making the advisor's observations the current OTel context, so that
    library spans would nest under `advisor-run` instead. That is a design
    change for an observability intent;
  - the Ollama adapter (§2), which has no SDK tracing.

## Type-specific questions

### Fix
- **What broke:** each Anthropic model call adds a separate
  `anthropic.messages.create` trace in Langfuse. Expected: one trace per
  run (§1 B15).
- **Since when:** §1, the adapter's construction line (4361ced; the file
  was renamed in 727717d). It shows with `anthropic` 2.6.0, whose tracing
  is on by default. It was first noticed in §4's live check on Langfuse v4;
  the owner's note calls it pre-existing.
- **Impact:** no wrong answer and no data leak. The trace list is cluttered,
  every Anthropic run counts as several traces, and a later evaluation
  intent would read the wrong trace count.
- **Reproduction:**
  1. Probe: `uv run python -c "import anthropic;
     print(anthropic.Anthropic(api_key='k')._open_telemetry['traces']['enabled'])"`
     prints `True`.
  2. Live: with Langfuse running and keys set, `uv run advisor "I need
     noise-cancelling headphones under 200 euros"` adds an `advisor-run`
     trace and one `anthropic.messages.create` trace per model call.
- **The test that will fail first:** `tests/test_models.py`. A new test
  builds the client through `make_client("anthropic", "m",
  api_key="placeholder-key")` and asserts that the SDK client's traces are
  off. The plan chooses how: the resolved option, or, stronger, no span
  exported to an in-memory OTel provider during a call over a mocked
  transport.

## Assumptions I made

- **Type fix,** `follows_up: 1`: the defect line is §1's.
- **Turn off traces only, not the SDK's trace-context propagation**
  (`propagation`, which stays `True`). Propagation adds W3C trace headers
  to requests sent to Anthropic. Say if you want that off too; it is a
  second, separate choice.
- **Not nesting the spans** under `advisor-run` instead (see Out of scope).
  That would keep the SDK's per-call timing, but needs the advisor's
  observations to become the current context.
- **The tier is left to the path table:** `src/advisor/models/` is core
  code and a live-check path (rule 1), so a live check is owed: one run,
  one trace.
- **Overlap with §2:** its branch changes `tests/test_models.py` and
  `models/__init__.py`, not `anthropic_model.py`. Whichever merges second
  rebases.
