<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §5 review — Turn off the Anthropic SDK's own OpenTelemetry spans

verdict: attest
tier: attested
reviewed-commit: 8fa3314143c9fe757932f179fcd86ee24b9d9762
round: 1
sampled: no
run: auto
live-check: owed

Tier: set by the path table. `src/advisor/models/anthropic_model.py` is
`src/**`, not on the Reviewed list, so it is Attested. `tests/test_models.py`
is Attested, and `CLAUDE.md` and `intents/**` sit at or below Attested.
`review_tier` is empty, and no CRITICAL or HIGH finding raises it.

Branch: 3 commits ahead of `main`, 1 behind. The missing commit, 5948c6f,
changes only §6's metadata, so no rebase was done. Nothing pushed.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (subtasks 1–4, nothing else; `tracing.py`, `models/__init__.py`, `conftest.py`, `pyproject.toml`, `uv.lock` untouched) |
| 2 | Type check | pass |
| 3 | Behaviour against the intent (Outcome 1–3, Reproduction) | pass |
| 4 | Tests prove the behaviour, not only pass | pass (7/7 mutants killed); 1 LOW on the env test's framing |
| 5 | Conventions | pass (`anthropic` still imported only in the adapter; the suite stays offline) |
| 6 | Numbers in prose | pass (111; fails-on-main "2 failed, 10 passed"; mutant counts reproduce) |
| 7 | Documentation | pass (`CLAUDE.md:178-179` accurate; `README.md:49` "one trace" is now true again) |
| 8 | Guardrails and hygiene | findings (1, LOW) |
| 9 | Repository-specific footguns | pass (list empty; §1's "test passes whatever the code does" checked in pass 4) |

**Pass 3.**
- **Outcome 1:** the adapter builds `anthropic.Anthropic(api_key=api_key,
  open_telemetry=False)` (`anthropic_model.py:64`). Probing `anthropic`
  2.6.0:
  - the default resolves to `{'propagation': True, 'traces': {'enabled':
    True, …}}`;
  - the fix resolves to `{'propagation': True, 'traces': {'enabled': False,
    …}}`, so propagation stays on, as the intent assumes;
  - `get_tracer` returns `None` when traces are off (`_tracing.py:249-250`);
  - a `with_options()` copy keeps `enabled: False`.
- **Outcome 2:** both new tests fail on `main`'s adapter (pass 4).
- **Outcome 3:** `resolve_open_telemetry` (`_tracing.py:154-173`) reads the
  environment only when the option is `None`, so an explicit `False`
  ignores it. That is true, but see the LOW: the SDK acts on
  `ANTHROPIC_OPEN_TELEMETRY` only as `"false"`.
- **Reproduction 1:** the probe prints `True` on the default and `False` on
  the fixed client. Reproduction 2 is the live check.
- **The injected `sdk_client` path:** unchanged (reflowed only; M7 proves it
  is exercised). The boundary test passes.

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 5, fix)
  note:  3 file(s), 29 line(s) changed outside intents/.
```

## Findings
- **LOW** `tests/test_models.py:41-42` (also `intent.md:36-37`,
  `plan.md:17,113`) — the env test's premise is vacuous. The test sets
  `ANTHROPIC_OPEN_TELEMETRY=true`, but the SDK reads that variable only as
  `"false"` (`.venv/Lib/site-packages/anthropic/_tracing.py:203`), and
  `"true"` equals unset.
  - With the `setenv` line removed, the test still fails on `main` and
    passes on the fix. It really proves "the real SDK client the adapter
    builds has traces off", which is still worth having: it is the only test
    reading the SDK's resolved state.
  - The plan's optional live step with `"true"` likewise proves nothing
    beyond the plain run.
  - The name could lead a reader to think `=true` turns SDK spans on.

  Worth a look: rename it (for example
  `test_the_real_sdk_client_has_traces_off`) in a later tidy-up. The plan
  wording is above the Progress marker: the owner's call.
- **LOW** `tests/test_models.py:45` — `# type: ignore[attr-defined]` is noise:
  `[tool.mypy] files = ["src/advisor"]` (`pyproject.toml:38-40`), so mypy
  never checks `tests/`. Worth a look: drop it when next touching the file.

Mutants (full suite each; `git diff --quiet` asserted non-zero; restore by
copy in `finally`):

| id | change | result | killed by |
| --- | --- | --- | --- |
| M1 | keyword removed | 2 failed / 109 passed | both new tests |
| M2 | `open_telemetry=None` | 2 failed / 109 passed | both new tests |
| M3 | `open_telemetry=True` | 3 failed / 108 passed | both new tests and `test_make_client_anthropic_does_not_connect` (the SDK cannot resolve `True`) |
| M4 | `{"traces": {"enabled": True}}` | 2 failed / 109 passed | both new tests |
| M5 | `{}` | 2 failed / 109 passed | both new tests |
| M6 | `{"traces": False}` (equivalent behaviour) | 1 failed / 110 passed | the keyword test only, as expected |
| M7 | `if sdk_client is not None` → `if False` | 5 failed / 106 passed | test_adapter_maps_tool_use_and_usage, …_text_only_response, …_round_trip_messages, …_no_text_block, …_response_names |

The comment lines need no mutant. No mutant survived.

## Not checked
- **The behavioural outcome:** no test shows that zero
  `anthropic.messages.create` spans reach the global OTel provider or
  Langfuse during a real call. The plan rejected an in-process provider
  test, because of global provider state. The proof rests on the resolved
  option, on `get_tracer` returning `None` (read in the source, not run),
  and on the owner's live check.
- **Streaming and async clients:** not relevant; the adapter uses sync
  `messages.create` only.
- **Propagation left on:** W3C trace headers still go to Anthropic, which
  is the owner's separate choice per the intent. Verified as `True`, not
  judged.
- **The textual rebase with §2,** which touches the same test file.
- **A real run:** no Anthropic call, no Langfuse, no Docker.

## Live check
- owed: rule 1 (`src/advisor/models/anthropic_model.py`). It is also the
  only behavioural proof of Outcome 1.
- steps (Windows PowerShell; the Langfuse v4 stack running on
  http://localhost:3000):
  1. ```
     Copy-Item C:\Users\eric\src\product-advice-agent\.env C:\Users\eric\src\product-advice-agent-wt\5-anthropic-sdk-otel-off\.env
     Copy-Item C:\Users\eric\src\product-advice-agent\infra\langfuse\.env C:\Users\eric\src\product-advice-agent-wt\5-anthropic-sdk-otel-off\infra\langfuse\.env
     ```
     The root `.env` sets `ADVISOR_MODEL_PROVIDER=anthropic`,
     `ANTHROPIC_API_KEY` and the `LANGFUSE_*` keys. This check needs that
     provider, because §2 is not merged.
  2. ```
     cd C:\Users\eric\src\product-advice-agent-wt\5-anthropic-sdk-otel-off
     uv run advisor "I need noise-cancelling headphones under 200 euros"
     ```
  3. Open http://localhost:3000 → the project → Traces, sorted by time.
- you should see:
  - an answer, exit 0;
  - exactly **one** new trace, `advisor-run`, with its §1 shape;
  - **no** new `anthropic.messages.create` trace beside it (before the fix
    there was one per model call).

  If an `anthropic.messages.create` trace still appears, it's a defect:
  leave `live_checked:` empty.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/5-anthropic-sdk-otel-off` at 8fa3314, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "64 files already formatted";
  mypy "Success: no issues found in 11 source files"; pytest "111 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0. Matches.
- **Coordinator, re-run:** M1 (keyword removed) and M2 (`open_telemetry=None`)
  with my harness (backup by copy, one replacement, file-changed assertion,
  full `pytest -q -x`, restore by copy): both KILLED by
  `test_models.py::test_anthropic_adapter_turns_off_sdk_tracing`, the first
  failure under `-x`. That matches the reviewer's "both new tests" and the
  implementer's report.
- **Coordinator:** the committed `anthropic_model.py`, `tests/test_models.py`
  and `CLAUDE.md` decode as UTF-8; the source has one well-formed `§`.

**Reviewer, verified:**
- `verify` and `check:intent` as above.
- `sdlc:scan --sample-due auto --exclude 5` → "nth attested auto change =
  1, every 3, sampled: no".
- Fails-on-main with `main`'s adapter copied in: "2 failed, 10 passed".
- 7 mutants (harness `…/scratchpad/mut5r/`).
- The env-test probes: without `setenv` it still fails on `main`;
  `ANTHROPIC_OPEN_TELEMETRY=false` makes `main` pass.
- SDK probes and source: `_tracing.py:154-213, 249-250`,
  `_types.py:120-216`, `_client.py:175-180`.
- `pyproject.toml`'s mypy scope.

**Taken on trust:**
- that the Langfuse SDK's global provider is what received the SDK spans;
- the owner's §4 observation of the extra traces;
- that `get_tracer` returning `None` means no span on a real call.
