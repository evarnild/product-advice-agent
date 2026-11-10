<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §5 plan — Turn off the Anthropic SDK's own OpenTelemetry spans

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

The Anthropic adapter builds its SDK client with `open_telemetry=False`,
so the SDK records no span for its API calls and a run with tracing on is
one Langfuse trace again (intent Outcome). Two tests that fail on `main`
prove it:
- the adapter passes the option;
- the real SDK client it builds has traces off, even with
  `ANTHROPIC_OPEN_TELEMETRY` set in the environment.

## Risks

- **A test that passes whatever the code does** (§1's recurring class). A
  test that only checks `isinstance` or the model name would not see the
  option. Each new test must fail on `main` (the implementer runs both once
  against `main`'s adapter by copy) and fail again with the keyword
  removed.
- **Private SDK attributes.** `client._open_telemetry["traces"]["enabled"]`
  is the SDK's resolved option, a private name in `anthropic` 2.6.0. An SDK
  upgrade that renames it fails the test loudly (KeyError or
  AttributeError) rather than passing silently. The keyword-recording test
  carries no such dependency.
- **Global OpenTelemetry state.** A behavioural test (no span exported
  during a call) would need `opentelemetry.trace.set_tracer_provider`. That
  can be set once per process, and the Langfuse SDK also registers a
  provider (`resource_manager.py:648-658`), so it would make
  `tests/test_tracing.py` order-dependent. Rejected, as the intent allowed.
  The live check is the behavioural proof.
- **Overlap with §2** (in review): its branch changes `tests/test_models.py`
  (new wiring tests, including one that reads `client._sdk.api_key`) and
  `models/__init__.py`. §5 adds tests to the same file and does not touch
  `__init__.py`. Whichever merges second rebases; the rebase is textual
  (added tests).
- **Stale line citations:** read at `398d4e8`.

## Verified against the codebase

Re-read on `main` at `398d4e8`.

- `src/advisor/models/anthropic_model.py:11` — `import anthropic` (the only importer, per `tests/test_boundaries.py:24-25`).
- `src/advisor/models/anthropic_model.py:55-60` — `class AnthropicClient: def __init__(self, api_key, model, sdk_client=None)`; `self._sdk = sdk_client if sdk_client is not None else anthropic.Anthropic(api_key=api_key)`.
- `src/advisor/models/__init__.py:15-20` — `make_client("anthropic", model, api_key)` → `AnthropicClient(api_key=api_key, model=model)`.
- `tests/test_models.py:23-25` — `test_make_client_anthropic_does_not_connect` builds the real SDK client and asserts only `isinstance`.
- `tests/conftest.py:12-23` — the socket block. Building `anthropic.Anthropic` opens no connection (the existing test proves it).
- `.venv/Lib/site-packages/anthropic/_client.py:178-180` — the `open_telemetry: OpenTelemetryClientOption = None` parameter ("`False` disables the spans").
- `.venv/Lib/site-packages/anthropic/_tracing.py:203` — the environment variable is read only when the option is `None`: `if os.environ.get("ANTHROPIC_OPEN_TELEMETRY", "").lower() == "false": …`. The resolver's docstring says the environment applies to "a client that is given no option, `None`".
- Probe (2026-11-10, `anthropic` 2.6.0):
  - `anthropic.Anthropic(api_key='k')._open_telemetry` → `{'propagation': True, 'traces': {'enabled': True, …}}`;
  - with `open_telemetry=False` → `{'propagation': True, 'traces': {'enabled': False, …}}`.
- `src/advisor/tracing.py:79-82` — `start_observation(...)` without entering it as the current context: why the SDK's spans become separate root traces (intent Problem).

## Subtasks

1. **Failing tests first** (`tests/test_models.py`). Add two tests, run
   them once against `main`'s adapter, and record in `## Progress` that
   both fail:
   - `test_anthropic_adapter_turns_off_sdk_tracing`: monkeypatch
     `anthropic.Anthropic` (as the adapter module sees it) with a recorder
     of its keyword arguments, call `AnthropicClient(api_key="placeholder-key",
     model="m")`, and assert `open_telemetry is False` and `api_key ==
     "placeholder-key"`.
   - `test_sdk_tracing_stays_off_even_if_the_environment_enables_it`:
     `monkeypatch.setenv("ANTHROPIC_OPEN_TELEMETRY", "true")`, build through
     `make_client("anthropic", "m", "placeholder-key")`, and assert the SDK
     client's `_open_telemetry["traces"]["enabled"] is False`.

   Commit both with the fix in subtask 2, so every commit stays green.
2. **The fix.** In `src/advisor/models/anthropic_model.py:59`,
   `anthropic.Anthropic(api_key=api_key, open_telemetry=False)`. Add a
   two-line comment: why (the SDK's spans would become separate Langfuse
   traces, because the advisor's observations are not the current OTel
   context; §5), and that the explicit option also overrides the
   `ANTHROPIC_OPEN_TELEMETRY*` variables. Nothing else in the file changes;
   the injected `sdk_client` path is untouched.
3. **Docs.** In `CLAUDE.md` → "Architecture", under "Conventions worth
   knowing", add one line: provider SDK clients are built with their own
   tracing off, so a run is one trace. The intent already explains why, so
   no README change.
4. **Status.** Set `status: in-review` and append to `## Progress`.

## Tests

| Intent item | Test | Fails on `main` / when mutated |
| --- | --- | --- |
| Outcome 1–2 (failing first) | `test_models.py::test_anthropic_adapter_turns_off_sdk_tracing` | fails on `main` (no `open_telemetry` keyword); fails if the keyword is removed or set to `None`/`True` |
| Outcome 3 | `test_models.py::test_sdk_tracing_stays_off_even_if_the_environment_enables_it` | fails on `main` (the environment does not matter there: the default is on); fails if the keyword is removed |
| unchanged behaviour | the existing adapter tests (`test_adapter_*`, `test_make_client_anthropic_does_not_connect`) | unchanged |

The implementer runs the mutants `open_telemetry=False` → removed, and →
`open_telemetry=None`, once each against the full suite, and records which
test kills each. It backs up and restores by copy and finishes with `git
status --short` clean.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (fix: test changes present; `models/` is core
  code).
- Live check, owed by rule 1 (`src/advisor/models/`). The owner runs it on
  the v4 stack, with the main checkout's `.env` copied into the worktree
  (`ADVISOR_MODEL_PROVIDER=anthropic` and the Langfuse keys):
  1. `uv run advisor "I need noise-cancelling headphones under 200 euros"`.
  2. In Langfuse → Traces: exactly one new trace, `advisor-run`, with its
     §1 shape, and no `anthropic.messages.create` trace beside it.
  3. Optional: with `$env:ANTHROPIC_OPEN_TELEMETRY = "true"`, the same: one
     trace.

## Assumptions I made

- **Two unit tests and no global OTel provider test** (Risks), so the live
  check carries the behavioural proof.
- **Traces off; `propagation` left on,** as the intent assumes. The intent
  lists turning propagation off as the owner's separate choice.
- **The Ollama adapter (§2)** is not touched: it has no SDK and no tracing
  of its own.
- **One `CLAUDE.md` line,** so the next provider adapter follows the same
  rule.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
