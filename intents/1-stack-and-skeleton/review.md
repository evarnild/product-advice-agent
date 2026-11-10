<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §1 review — Stack decision (Python + Langfuse) and project skeleton

verdict: rework
tier: reviewed
reviewed-commit: b07e8ac3cc47819e2cb903fd856071c73fd2ce94
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed, as round 1 (path table: `REVIEW-POLICY.md`,
`scripts/intent-check-lib.mjs`; `review_tier: reviewed`; the HIGH below would
escalate it anyway). Policy used: main's `REVIEW-POLICY.md` (ffade02) for
tiers, passes, report format and merging; the branch's rule-1 path list only
to decide `live-check`.

Scope: f3fb5d6..b07e8ac — 7eccff5 round-1 `review.md`; 1525cab, 51ce473
metadata and the plan amendment (owner decision B); 9583c64, daf4d06 the
rework; e951c31 Progress entry; b07e8ac `auto_round: 2`.

Bottom line: the rework does what round 1 asked, but no test proves that
`SafeTracer` forwards anything, and production always runs through it, so
B15 and decision A are unproven on the path that runs (new HIGH).

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (decisions A and B done as stated; nothing beyond scope) |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's gate) |
| 3 | Behaviour against the spec | pass (decision-A behaviour present; its proof on the `SafeTracer` path is pass 4) |
| 4 | Tests prove the behaviour, not only pass | findings (3): 47 mutants, 31 killed, 16 survived (4 equivalent, 2 carried LOW) |
| 5 | Conventions | pass (round-1 LOW on `agent.py` importing `tracing` carried as Worth a look) |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; two candidates below) |

**Pass 1, against the round-1 asks:**
- Decision A: `answer_question` (`agent.py:186-193`) wraps `run_agent` in
  `try/except Exception`, calls `tracer.fail(f"{type(e).__name__}: {e}")`
  and re-raises; the CLI still exits 1 with the unavailable message
  (`test_model_failure_exit_1_no_traceback`). `fail()` is on the `Tracer`
  protocol (`tracing.py:42-44`), `NoopTracer` (`:63-64`), `LangfuseTracer`
  (`:118-119`, `_close(output=error, level="ERROR")`) and `SafeTracer`
  (`:159-160`); `_close` (`:121-130`) is shared with `finish`, so the same
  bounded flush runs on both paths. Only the exception class and message are
  recorded; `ModelError` reads "Anthropic call failed: <SDK error class>",
  no key or env value.
- Decision B: `opentelemetry-sdk` and `httpx` in the dev group
  (`pyproject.toml:20-21`); `uv.lock` adds only those two dev entries, no
  version changes; `uv lock --check --offline` and `uv sync --frozen
  --offline` exit 0. The plan's Dependencies section lists hatchling,
  opentelemetry-sdk and httpx (51ce473, owner's decision).
- Optional items taken: the dead `except UnknownProviderError` handler and
  its import dropped from `cli.py` (provider still rejected first at
  `cli.py:53`; no behaviour change); `test_blank_text_field_is_rejected`
  added.
- The implementer's claim on round-1 finding 5 holds: with the checks
  present every `ToolError` already names the argument (`'max_price' must be
  a number`, `'limit' must be an integer`); A1, A2, A8 survived only because
  the catch-all hid removed checks, and are now killed by
  `test_bad_argument_errors_name_the_argument`. A3 still survives but is
  equivalent (`float(v)` vs `v` compare equal for an int).

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 1, feature)
  error: A live check is owed and not recorded. Do the steps in intents/1-stack-and-skeleton/review.md → ## Live check, then set live_checked: <date> in intents/1-stack-and-skeleton/metadata.yml.
  note:  40 file(s), 4243 line(s) changed outside intents/.
```
The only error is the owed live check, the owner's to clear (review skill,
step 1's exception).

## Round-1 findings: resolution
| Round-1 finding | Resolution |
| --- | --- |
| HIGH tool arguments unproven (A9, A11, A12, A13, A14) | resolved: `test_each_tool_argument_alone_changes_the_results`, `test_tool_result_carries_all_fields_including_specs` kill all five |
| HIGH sort tie-break (C24, C24b) | partly: C24 killed; C24b and the new C24c survive (MEDIUM below) |
| HIGH B15 observation content (T4, T5, T8, T9, T10) | resolved: real-SDK test asserts type, input, output, level, incl. an unknown-tool span at ERROR |
| HIGH B17 flush (T14, T20) | resolved: `flushed.wait(1)` and `FLUSH_TIMEOUT_SECONDS <= 5` asserted |
| MEDIUM failed run leaves a broken trace (decision A) | implemented, proven for `answer_question` and `LangfuseTracer` (R1–R9 killed); not proven through `SafeTracer` (HIGH below) |
| MEDIUM bad-argument errors (A1, A2, A3, A8) | resolved: A1, A2, A8 killed; A3 equivalent |
| LOW adapter (N1, N14) | resolved, both killed |
| LOW hard-coded host (T21) | resolved, killed |
| LOW dependencies (decision B) | resolved |
| LOW `agent.py` imports `tracing` (and langfuse) | not taken; carried as Worth a look |
| LOW untested CLI lines (L5, L6, L12) | L12's dead handler removed; L5, L6 carried |
| LOW catalogue (C4b, C13) | C4b killed; C13 carried |
| LOW OpenTelemetry stderr line | not taken; carried |

## Findings

- **HIGH** `tests/test_tracing.py` (code `src/advisor/tracing.py:144-160`,
  `SafeTracer`) — no test shows `SafeTracer` forwarding any call to the
  tracer it wraps. Every delegation line survives: R14 `begin` → `pass`, R15
  `check`, R16 `generation`, R17 `tool`, R18 `finish`, R11 `fail`, R12 `fail`
  forwarded as `"finish"`. The only `SafeTracer` tests use `RaisingTracer`
  and check that errors are swallowed; the real-SDK tests drive
  `LangfuseTracer` directly. Production always gets `make_tracer`'s
  `SafeTracer(LangfuseTracer(client))`, so a `SafeTracer` that dropped calls
  would send empty or broken traces with the suite green. (Missed in round 1:
  the delegation lines were not mutated.)
  Needs rework: a test that wraps a `RecordingTracer` in `SafeTracer`, runs
  `answer_question` through it and asserts the same `events`, with
  arguments, as the unwrapped run (begin, check, generation, tool,
  generation, check, finish); and a failing run through it asserting
  `("fail", "ModelError: down")`. Kills R11, R12, R14, R15, R16, R17, R18.

- **MEDIUM** `tests/test_catalogue.py:130-150` (code `src/advisor/catalogue.py:138`)
  — the "then id" tie-break is still not fully proven. P-003 now precedes
  P-002 (kills C24), but the tied names ("Beta Phone" P-002, "Gamma Laptop"
  P-003) sort the same way as their ids, so C24c (`key=(price, name)`, a
  natural slip) and C24b survive. AC3 requires "sort is price then id".
  Needs rework: give the tied pair names whose order disagrees with their
  ids (e.g. rename P-002 to "Zeta Phone"; no current keyword assertion uses
  "beta"); keep the expected `["P-002", "P-003", …]`. Kills C24b, C24c.

- **LOW** `tests/test_tracing.py:117-143` (code `src/advisor/tracing.py:116`)
  — the root's level on a successful run is not asserted: R13 (`finish`
  closes with `level="ERROR"`) survives, so a success could show in Langfuse
  as an error.
  Needs rework: in `test_langfuse_tracer_with_real_sdk_and_in_memory_exporter`,
  assert the root has no `langfuse.observation.level` attribute or that it is
  `DEFAULT`. Kills R13.

- **LOW** (carried) `src/advisor/agent.py:19`, `src/advisor/tracing.py:16` —
  the pure core module `agent.py` imports `advisor.tracing`, which imports
  `langfuse` at load. Worth a look: move `Tracer`/`NoopTracer` into an
  SDK-free module, or import `Langfuse` lazily in `make_tracer`.

- **LOW** (carried) `src/advisor/cli.py:46,49` — L5 (debug log level) and L6
  (UTF-8 stdout reconfigure) untested. Worth a look.

- **LOW** (carried) `src/advisor/catalogue.py:103` — C13: the not-a-list check
  is removable; the per-entry check still raises. Worth a look.

- **LOW** (carried, runtime) — with Langfuse unreachable, OpenTelemetry prints
  "Failed to export spans batch due to timeout, max retries or shutdown." to
  stderr. Worth a look.

Survivors judged equivalent, no rework: A3 (`float(v)` vs `v`), A21 (fake
copies the list), T2 (root-None guard; `SafeTracer` swallows), R10 (`_root =
None` after close; each tracer closes once per run). From round 1, unchanged
lines: C12, C16, N12, K2, N7 (live-only).

Pass 9 candidates:
1. **"A fixture already in the expected order, or a test value equal to the
   default, cannot kill a mutant."** Round 1 (C24, T21, N14) and again here
   (tied names in id order, C24c).
2. **"A wrapper tested only for swallowing errors, not for forwarding calls,
   proves nothing about the path that runs."** (R11–R18.)

## Not checked
- Live runtime: real Anthropic tool-use round trips, model id
  `claude-haiku-5-5`, answers citing name and id; the Langfuse v3 stack
  starting and the trace rendering in its UI; whether Langfuse 5.2 shows the
  root span's input/output as the trace's; how a failed run's ERROR-level
  root renders in the UI.
- The live query's keywords: "noise-cancelling" with a hyphen matches no
  description, so the model may retry. Advice quality, out of scope, but it
  bears on AC14.
- The flush bound against a host that blackholes packets (only a refused
  connection on 127.0.0.1:1 was tested in round 1); the SDK's atexit
  `shutdown()` flushes again outside the 5 s join.
- AC12 (a fresh `npm run spawn` worktree passes verify): not re-created
  (read-only review); `uv sync --frozen --offline` passes in this worktree.
- No containers started.
- Survivors not re-run under the full `npm run verify`: `src/advisor`
  mutants ran under `pytest -q -x`, so ruff or mypy could kill a few
  (none looks likely). No `scripts/` file changed this round, so no kit
  mutants.
- Round-1 killed mutants on unchanged lines were not re-run; only the rework
  set, moved equivalents, L5/L6/L16 and the new lines.
- Test files were not mutated.

## Live check
- owed: rule 1 (the diff touches `src/advisor/cli.py`,
  `src/advisor/models/`, `src/advisor/tracing.py`, `src/advisor/prompts/`,
  `infra/`, as named by the branch's policy); rule 3 (real model output, the
  Langfuse UI, the ERROR-level trace of a failed run — Not checked); spec
  AC14.
- steps:
  1. In the worktree (or on main after merge): `uv sync --frozen`.
  2. `cp infra/langfuse/.env.example infra/langfuse/.env`; replace every
     `replace-me` (`openssl rand -hex 32` for `NEXTAUTH_SECRET`, `SALT`,
     `ENCRYPTION_KEY` — the last must be 64 hex chars; `openssl rand -base64
     24` for passwords).
  3. `docker compose -f infra/langfuse/docker-compose.yml up -d`; wait until
     `docker compose -f infra/langfuse/docker-compose.yml ps` shows
     `langfuse-web` running.
  4. Open http://localhost:3000, sign up, create an organisation, a project
     and API keys.
  5. `cp .env.example .env`; set `ANTHROPIC_API_KEY` (real),
     `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` from step 4, keep
     `LANGFUSE_HOST=http://localhost:3000`.
  6. `uv run advisor "I need noise-cancelling headphones under 200 euros"`.
  7. Failed-run trace (decision A): the same tool with an invalid key for one
     command (the real environment overrides `.env`). PowerShell:
     `$env:ANTHROPIC_API_KEY="invalid-key"; uv run advisor "test"; Remove-Item Env:ANTHROPIC_API_KEY`.
     Git Bash: `ANTHROPIC_API_KEY=invalid-key uv run advisor "test"`.
  8. Optional: `docker compose -f infra/langfuse/docker-compose.yml stop`,
     then step 6 again.
  9. Afterwards `docker compose -f infra/langfuse/docker-compose.yml down`
     (`-v` to delete stored traces).
- you should see:
  - Step 6: exit 0; only catalogue products, each by name and id. In-stock
    noise-cancelling headphones under €200 are Auralis Calm 300 (P-001,
    €189) and Kestrel Air Plus (P-005, €129); Sonavo Quiet Pro (P-004, €159)
    is out of stock and should be flagged if mentioned. No invented
    products, no traceback.
  - Step 6 trace in Langfuse (Tracing), one new trace: root `advisor-run`,
    input the question, output the printed answer, not level ERROR; under it
    in order `input-check` (guardrail, `allowed: true`), `model-call`
    generations with model `claude-haiku-5-5` and non-zero token usage,
    `search_products` tool observations with arguments and `result_count`,
    `output-check` (`allowed: true`).
  - Step 7: stderr "The advisor is unavailable right now.", exit 1, no
    traceback; in Langfuse one new trace, root `advisor-run` at level ERROR,
    input "test", output like `ModelError: Anthropic call failed:
    AuthenticationError` (no key), only the `input-check` child.
  - Step 8: same answer, exit 0, process exits within ~5 s of printing; at
    most one export-failure line on stderr.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/1-stack-and-skeleton` at b07e8ac, worktree clean before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "51 files already formatted";
  mypy "Success: no issues found in 11 source files"; pytest "102 passed".
  Matches reviewer and implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL, exit 1, only the
  owed-live-check error (pasted above). Matches.
- **Coordinator, re-run:** all 16 round-2 survivors (C24b A3 A21 T2 R10 L5
  L6 R11 R12 R13 C24c R14 R15 R16 R17 R18), new definitions read first,
  through the reviewer's `harness2.py` (checked identical to round 1's
  harness apart from file names: copy backup, one change, diff-guard,
  `pytest -q -x`, restore by copy, diff check) → all 16 SURVIVED. Matches.
- **Coordinator, re-run:** the round-1 mutants the rework claimed to kill
  (C4b C24 A1 A2 A8 A9 A11 A12 A13 A14 N1 N14 T4 T5 T8 T9 T10 T14 T20 T21)
  → all killed, by the same tests the reviewer names; A3 and C24b survive
  as listed. Matches.
- **Coordinator, re-run:** `git status --short` empty afterwards.

**Reviewer, verified:**
- `git rev-parse HEAD` b07e8ac, worktree clean at start, nothing checked out.
- `npm run verify` at b07e8ac: exit 0, counts as above. The format count
  rose 50 → 51 because ruff 0.17 also formats Markdown and round 1 committed
  `review.md`; the tracked `.py` count is unchanged at 23 (`ruff check
  --show-files`, `ruff format --check -v`).
- `npm run check:intent`: FAIL with only the owed live check.
- `uv lock --check --offline` exit 0 ("Resolved 49 packages"); `uv sync
  --frozen --offline` exit 0 ("Audited 48 packages").
- `git diff f3fb5d6 HEAD` for `src/`, `tests/`, `pyproject.toml`,
  `uv.lock`, `plan.md`, `metadata.yml` read in full; decisions A and B as
  described in pass 1.
- Mutation testing, 47 mutants via `harness2.py` (pytest `-q -x`): 31 killed,
  16 survived. Killed: C4b, C24, A1, A2, A8, A9, A11, A12, A13, A14, N1,
  N14, T4, T5, T8, T9, T10, T14, T20, T21, T13, L16, R1–R9. Survived: C24b,
  C24c, R11–R18 (rework); A3, A21, T2, R10 (equivalent); L5, L6 (carried).
- `git status --short` empty after each batch; main unchanged at ffade02; no
  remote.

**Taken on trust:** that a fresh spawn worktree passes (AC12); Anthropic and
Langfuse runtime behaviour.

**Mutants the rework should kill** (to re-run next round): R11, R12, R14,
R15, R16, R17, R18 (`tracing.py` `SafeTracer`, lines 145-160); C24b, C24c
(`catalogue.py:138`); R13 (`tracing.py:116`).

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: f3fb5d63c4c628ce3bddb602677b94077641b00d
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, set by the path table (`REVIEW-POLICY.md`,
`scripts/intent-check-lib.mjs`) and by `review_tier: reviewed` in
`metadata.yml`; the HIGH findings would escalate it anyway.

Policy used: the branch edits `REVIEW-POLICY.md`, so main's copy (ffade02)
was applied for tiers, passes, report format and merging. The branch's
rule-1 path list was used only to decide `live-check`; rule 3 and spec AC14
make the check owed under either copy.

Code is identical between 314f611 (where `verify` was first run) and
f3fb5d6 (HEAD); the commits in between touch only `metadata.yml`.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (declared divergences judged below) |
| 2 | Type check | pass (PASS) |
| 3 | Behaviour against the spec | findings (1) |
| 4 | Tests prove the behaviour, not only pass | findings (8): 135 mutants, 102 killed, 33 survived (7 equivalent or live-only) |
| 5 | Conventions | findings (1) |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | findings (1) |
| 9 | Repository-specific footguns | pass (list empty; one candidate proposed below) |

**Pass 1, declared divergences:**
- `answer_question` (guardrails + agent + trace) in `agent.py`, not
  `cli.py`: accepted; the wiring stays pure, covered by `CORE_CODE`.
- `Tracer` protocol and `NoopTracer` in `tracing.py`: plan subtask 6 says
  so; not a divergence. Purity side effect: see the LOW finding on
  `agent.py:19`.
- `make_client(provider, model, api_key)`: accepted; the key is never
  printed (`test_key_is_never_printed`).
- Extra `tests/helpers.py`, `test_config.py`, `test_cli.py`: accepted.
- Real-SDK tracing test: accepted; runs offline (in-memory exporter, socket
  guard active).
- `docker compose … config -q` exits 1 without `infra/langfuse/.env`
  (required `${VAR:?}` secrets), 0 with `--env-file
  infra/langfuse/.env.example`: accepted as safer than defaulted secrets;
  README and Progress record it. The plan's Validation line is stale but
  the Progress entry covers it.

**Pass 3:** B1–B14, B16, B18–B26 met (B3 names product and field; B6/B7
exit 1 before the adapter is built; B9 cap 5 with the exact fallback; B12
block gives the refusal; B13/B14 exit 2/1 and `--debug`; B18 all 9
published ports bound to 127.0.0.1; B21 session-wide socket guard with its
own test). B15 and B17 met on the success path only (MEDIUM below).

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 1, feature)
  note:  40 file(s), 4007 line(s) changed outside intents/.
```

### Findings

- **HIGH** `tests/test_agent.py:61-67` (code `src/advisor/agent.py:86,115,117-119`)
  — most tool arguments are not proven to reach `search_products`. Surviving:
  A9 `min_price=None`, A11 `keywords=None`, A12 `in_stock_only=False`, A13
  `limit=5`, A14 `"specs"` dropped from the tool result JSON. AC4 requires
  the agent to run the search "with the given arguments"; a model asking for
  in-stock items or a minimum price would silently get unfiltered results,
  and specs are what the prompt tells the model to cite. The existing test's
  one-laptop catalogue makes `keywords` and `limit` irrelevant.
  Needs rework: in `tests/test_agent.py`, one case per argument
  (`min_price`, `keywords`, `in_stock_only`, `limit`) where that argument
  alone changes the returned ids (fixture with an out-of-stock item, several
  items in one category, a keyword that excludes one); assert `specs` is in
  the tool result JSON. Kills A9, A11, A12, A13, A14.

- **HIGH** `tests/test_catalogue.py:130-150` (code `src/advisor/catalogue.py:138`)
  — the price-then-id tie-break is unproven: C24 (key `(price,)`) and C24b
  (key `(price, name[::-1])`) survive because the tied fixture products are
  already in id order and Python's sort is stable. AC3 and the plan's Tests
  table require a sort-key change to fail.
  Needs rework: list the tied products out of id order (P-003 before
  P-002), keep the expected `["P-002", "P-003", …]`. Kills C24, C24b.

- **HIGH** `tests/test_tracing.py:201-232` (code `src/advisor/tracing.py:86-87,103-105`)
  — B15's per-observation content is unproven; only span names, root
  input/output and generation model/usage are asserted. Surviving: T8 tool
  `input=arguments` removed, T9 `result_count` removed, T10 `level` always
  `DEFAULT`, T4 check `as_type="guardrail"` → `span`, T5 check output removed.
  Needs rework: in that test assert the `search_products` span's
  `langfuse.observation.input` holds `{"category": "phone"}` and its output
  holds `"result_count": 1`; assert `input-check`/`output-check` have
  `langfuse.observation.type == "guardrail"` and an `allowed` output; add an
  unknown-tool case whose tool observation has level `ERROR`. Kills T4, T5,
  T8, T9, T10.

- **HIGH** `tests/test_tracing.py:235-255` (code `src/advisor/tracing.py:60,114`)
  — B17's flush is unproven: T14 (flush thread target → no-op) survives, and
  T20 (`FLUSH_TIMEOUT_SECONDS` 5.0 → 50.0) survives because the test
  monkeypatches the constant. The spec says "a bounded wait (≤ 5 s)".
  Needs rework: make `Hanging.flush` record that it was called and assert
  it; add `assert tracing.FLUSH_TIMEOUT_SECONDS <= 5`. Kills T14, T20.

- **MEDIUM** `src/advisor/agent.py:180-192` (`answer_question`) — a failed run
  leaves a broken trace. When `run_agent` raises (B14's model/network
  failure), `tracer.finish` is never called: the root `advisor-run` span is
  never ended, Langfuse gets only an orphan `input-check` observation with no
  trace input, and the bounded flush is skipped. Reproduced with the real SDK
  and an in-memory exporter: exported spans `[('input-check', parent set)]`;
  with Langfuse refusing connections the process still exited in ~5.4 s via
  the SDK's atexit flush. B15 says "each CLI run produces exactly one
  Langfuse trace"; the spec is silent on failed runs, which are the ones a
  trace helps most with.
  Needs decision: should a failed run close its trace (e.g. try/finally that
  ends the root with an error output/level and re-raises), and what should
  it record? Then a test with a raising fake and a `RecordingTracer`.

- **MEDIUM** `tests/test_agent.py:107-121` (code `src/advisor/agent.py:73,75,110`)
  — bad-argument tests assert only `is_error`. A1 (bool check), A2 (numeric
  check), A3 (`float(v)`) and A8 (limit type check) survive because the
  catch-all `except Exception` (`agent.py:144`) turns the `TypeError` into
  "error: tool failed (TypeError)", which gives the model no hint which
  argument to fix — B10 exists "so the model can correct itself".
  Needs rework: in `test_bad_arguments_give_error_result`, assert
  `res.content` names the bad argument (`'max_price'`, `'limit'`, …); add a
  `{"max_price": True}` case. Kills A1, A2, A3, A8.

- **LOW** `tests/test_models.py:255-287` (code `src/advisor/models/anthropic.py:28,87`)
  — N1 (`if m.text:` → `if True:`, which would send an empty text block the
  real Messages API rejects) and N14 (`model=response.model` → configured
  model; the test uses `"m-1"` for both) survive.
  Needs rework: a round-trip case with `Message("assistant", "",
  (ToolCall(...),))` asserting no text block; a response model name that
  differs from the configured one. Kills N1, N14.

- **LOW** `tests/test_tracing.py:174-185` (code `src/advisor/tracing.py:156`)
  — T21 (`host=` hard-coded to `http://localhost:3000`, the value the test
  passes) survives.
  Needs rework: use a distinctive host in `FULL_ENV`, e.g.
  `http://langfuse.test:3000`. Kills T21.

- **LOW** `pyproject.toml:21-23`, `tests/test_tracing.py:4`, `tests/test_models.py:4`
  — dependencies outside plan.md's list: `hatchling` (build backend), and
  tests import transitive packages directly (`opentelemetry.sdk` via
  langfuse, `httpx` via anthropic). The plan says "No other dependency
  without amending this plan". Runtime and dev lists in `pyproject.toml` and
  `uv.lock` otherwise match exactly.
  Needs decision: amend the plan's Dependencies section (owner-edited, above
  Progress), or declare `opentelemetry-sdk` and `httpx` in the dev group so
  tests don't lean on transitive pins (and say which build backend).

- **LOW** `src/advisor/agent.py:19`, `src/advisor/tracing.py:16` — the pure
  core module `agent.py` imports `advisor.tracing`, which imports `langfuse`
  (and OpenTelemetry) at load. B23 and CLAUDE.md call `agent` pure;
  `tests/test_boundaries.py` checks direct imports only. Worth a look: move
  `Tracer`/`NoopTracer` into an SDK-free module, or import `Langfuse` lazily
  in `make_tracer`.

- **LOW** `src/advisor/cli.py:46,49,70` — untested: L5 (debug log level), L6
  (UTF-8 stdout reconfigure); L12 (`except UnknownProviderError`) is dead
  code since `cli.py:53` rejects unknown providers first. Worth a look:
  drop the dead handler or test it.

- **LOW** `src/advisor/catalogue.py:65,103` — C4b (blank `name`/`brand`/
  `description` accepted without the `.strip()` check; no blank-string test)
  and C13 (not-a-list check removable; per-entry check still raises) survive.
  Worth a look: add a blank-name case.

- **LOW** (runtime, reviewer's probe) — with Langfuse unreachable,
  OpenTelemetry prints "Failed to export spans batch due to timeout, max
  retries or shutdown." to stderr. Answer and exit code unchanged (B17).
  Worth a look: a user may read it as an advisor error.

Survivors judged equivalent or live-only, no rework: A21 (fake copies the
list anyway), C12 (no `float()` on price), C16 (`""` always matches), N12
(`""` vs `None` treated alike), T2 (`SafeTracer` swallows), K2 (CLI's `if not
api_key` treats them alike), N7 (`max_tokens`; live-only).

Pass 9 candidate: **"A fixture already in the expected order, or a test value
equal to the default, cannot kill a mutant."** Seen three times here (C24,
T21, N14).

### Not checked
- Live-only runtime: real Anthropic Messages API tool-use round trips,
  model id `claude-haiku-5-5` resolving, answers citing name and id; the
  Langfuse v3 stack starting and the trace rendering in its UI; whether
  Langfuse 5.2 shows the root span's input/output as the trace's (the SDK
  has no `update_trace`; only `langfuse.observation.input/output` are set).
- Keyword search on the live query: descriptions say "noise cancelling"
  without a hyphen; `keywords: ["noise-cancelling"]` returns `[]` and the
  model must retry within 5 turns. Advice quality is out of scope, but it
  bears on AC14.
- The flush bound when the Langfuse host blackholes packets (only a refused
  connection on 127.0.0.1:1 was tested); the SDK's atexit `shutdown()`
  flushes again with its own timeout, outside the 5 s join.
- AC12 (a fresh `npm run spawn` worktree passes verify): not re-created
  (read-only review); the implementer's worktree passes `uv sync --frozen`
  and `verify`.
- No containers started; only `docker compose config -q`.
- `src/advisor` mutants ran under `pytest -q -x`, not the full `npm run
  verify`; ruff or mypy could kill a few survivors (none looks likely).
  `intent-check-lib.mjs` mutants ran under `npm run test:kit` (equivalent:
  the product half of `verify` does not read it).
- Test files were not mutated, apart from the conftest guard, which
  `test_no_network.py` proves directly.

### Live check
- owed: rule 1 (the diff touches `src/advisor/cli.py`,
  `src/advisor/models/`, `src/advisor/tracing.py`, `src/advisor/prompts/`,
  `infra/`, as named by the branch's policy); rule 3 (real model output and
  the Langfuse UI, Not checked); spec AC14.
- steps:
  1. In the worktree (or on main after merge): `uv sync --frozen`.
  2. `cp infra/langfuse/.env.example infra/langfuse/.env`; replace every
     `replace-me` (`openssl rand -hex 32` for `NEXTAUTH_SECRET`, `SALT`,
     `ENCRYPTION_KEY` — the last must be 64 hex chars; `openssl rand -base64
     24` for passwords).
  3. `docker compose -f infra/langfuse/docker-compose.yml up -d`; wait until
     `docker compose -f infra/langfuse/docker-compose.yml ps` shows
     `langfuse-web` running.
  4. Open http://localhost:3000, sign up, create an organisation, a project
     and API keys.
  5. `cp .env.example .env`; set `ANTHROPIC_API_KEY` (real),
     `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` from step 4, keep
     `LANGFUSE_HOST=http://localhost:3000`.
  6. `uv run advisor "I need noise-cancelling headphones under 200 euros"`.
  7. Optional: the same with `ANTHROPIC_API_KEY` blanked → exit 1 naming
     `ANTHROPIC_API_KEY`.
  8. Optional: `docker compose -f infra/langfuse/docker-compose.yml stop`,
     then step 6 again.
  9. Afterwards `docker compose -f infra/langfuse/docker-compose.yml down`
     (`-v` to delete stored traces).
- you should see:
  - Step 6: exit 0; only catalogue products, each by name and id. In-stock
    noise-cancelling headphones under €200 are Auralis Calm 300 (P-001,
    €189) and Kestrel Air Plus (P-005, €129); Sonavo Quiet Pro (P-004, €159)
    is out of stock and should be flagged if mentioned. No invented
    products, no traceback.
  - One new trace in Langfuse (Tracing): root `advisor-run`, input the
    question, output the printed answer; under it in order `input-check`
    (guardrail, `allowed: true`), one or more `model-call` generations with
    model `claude-haiku-5-5` and non-zero token usage, `search_products`
    tool observations with arguments and `result_count`, `output-check`
    (`allowed: true`).
  - Step 8: same answer, exit 0, process exits within ~5 s of printing; at
    most one export-failure line on stderr.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/1-stack-and-skeleton` at f3fb5d6):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "50 files already formatted";
  mypy "Success: no issues found in 11 source files"; pytest "89 passed".
  Matches reviewer and implementer.
- **Coordinator, re-run:** `npm run check:intent` → `type-check: PASS
  (intent 1, feature)`, exit 0. Matches.
- **Coordinator, re-run:** all 33 surviving mutants (C4b C12 C13 C16 C24
  C24b A1 A2 A3 A8 A9 A11 A12 A13 A14 A21 N1 N7 N12 N14 T2 T4 T5 T8 T9 T10
  T14 T20 T21 K2 L5 L6 L12), each definition read first, run through the
  reviewer's harness (copy backup, one change, diff-guard, `pytest -q -x`,
  restore by copy, diff check) → all 33 SURVIVED. Matches the reviewer.
- **Coordinator, re-run:** `git status --short` empty afterwards.

**Reviewer, verified:**
- `git rev-parse HEAD` / branch / worktree list: branch checked out in the
  worktree; nothing checked out; `git diff --stat 314f611 HEAD` touches
  only `metadata.yml`.
- `npm run verify` at 314f611: exit 0, same counts as above.
- `npm run check:intent` at 314f611 and f3fb5d6: PASS.
- AC11: `import os` appended to `src/advisor/guardrails.py` (diff
  non-empty), `npm run verify:product` → exit 1; restored by copy; `verify`
  chains with `&&`.
- `docker compose -f infra/langfuse/docker-compose.yml config -q` → exit 1
  (required variables); with `--env-file infra/langfuse/.env.example` →
  exit 0. No container started.
- Secret grep over `git diff main...HEAD` (`sk-ant-`, `pk-lf-`/`sk-lf-`, AWS
  keys, private-key headers, literal passwords): none. `.env.example` files
  hold placeholders; `.env`, `infra/langfuse/.env`, `.venv/` gitignored;
  test values (`pk-test`, `sk-test`, `placeholder-key`, `sekrit-value`)
  fake.
- Catalogue: 32 products, 8 categories, fictional brands (Auralis,
  Kestrel, Lumino, Norvik, Pelagic, Sonavo, Tolvane, Zephra).
- No user- or model-supplied text reaches a shell, `eval`, SQL or HTML.
- `anthropic` imported only in `models/anthropic.py`, `langfuse` only in
  `tracing.py` (code read and `test_boundaries.py`).
- `uv.lock` project entry: anthropic, langfuse, python-dotenv; dev mypy,
  pytest, ruff. Installed langfuse 5.2.0, anthropic 2.6.0, Python 3.12.9.
- `CORE_CODE` is exactly `^src/advisor/(agent|catalogue|guardrails)\.py$`
  and `^src/advisor/models/`; kit fixtures moved, no assertion weakened, a
  core-vs-non-core test added.
- `REVIEW-POLICY.md` tier row, lifted suspension and rule 1 match B25;
  `CLAUDE.md` overview, Commands, Architecture match B23; README covers
  B26.
- Throwaway probes against the real modules: B17 success path with
  Langfuse at 127.0.0.1:1 → `main` returned 0 after 5.58 s, process exit
  5.74 s, answer unchanged, one export-failure line; B15 attributes on
  root, generations and tool span as listed; failure path with
  `ModelError` → only `input-check` exported, exit 1 at 5.45 s.
- Mutation testing: 135 mutants, 102 killed, 33 survived (killed ones:
  catalogue C1–C11, C14a/b, C15, C17–C23, C25; agent A4–A7, A10, A15–A20,
  A22–A35; guardrails G1–G3; models M1–M3, N2–N6, N8–N11, N13, N15; fake
  F1–F3; tracing T1, T3, T6, T7, T11–T13, T15–T19; config K1, K3–K7; cli
  L1–L4, L7–L11, L13–L17; `intent-check-lib.mjs` S1–S3 under `npm run
  test:kit`).
- `npm run sdlc:scan -- --sample-due auto --exclude 1` → "nth attested
  auto change = 1, every 3, sampled: no".
- `git status --short` empty after every batch; main unchanged at ffade02;
  no remote, nothing pushed.

**Taken on trust:** the owner's toolchain versions in the plan; that a fresh
`npm run spawn` worktree passes (AC12); Anthropic and Langfuse runtime
behaviour beyond what their SDKs show; the upstream accuracy of the Langfuse
compose adaptation beyond reading it.

**Mutants the rework should kill** (to re-run next round): A1, A2, A3, A8,
A9, A11, A12, A13, A14; C24, C24b; N1, N14; T4, T5, T8, T9, T10, T14, T20,
T21.
