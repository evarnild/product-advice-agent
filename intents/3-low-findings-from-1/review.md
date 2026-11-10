<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §3 review — Close the LOW review findings left open by §1

verdict: escalate
tier: reviewed
reviewed-commit: 61b37b88c163a8a87583431619d7b62360061ef8
round: 2
sampled: no
run: auto
live-check: owed

The rework closes round 1's only rework finding. Mutant C2 (`otel.propagate
= False` removed) is now killed by
`test_cli_stderr.py::test_export_failure_is_silent_even_with_a_root_handler`,
and that test does bite: with the probe's root handler gone, C2 survives
again. The rework touched only `tests/test_cli_stderr.py` and the plan's
Progress, and `git diff e5c12b1 HEAD -- src` is empty. No finding needs
rework, and the tier is Reviewed, so the verdict is escalate: the owner
reads the diff. The live check is still owed.

Tier: Reviewed, set by the path table as in round 1: `src/advisor/cli.py`
and `src/advisor/tracing.py` are Reviewed by meaning. `review_tier:
reviewed` agrees.

## Round-1 findings: resolution
| Round-1 finding | Resolution |
| --- | --- |
| LOW `cli.py:53` / `tests/test_cli_stderr.py`: C2 survives (Needs rework) | resolved in f2fcf23: `tests/test_cli_stderr.py:58-63` adds the root-handler case. The probe (`:28-30`) installs `logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))` before `cli.main` without `--debug`, and the test asserts exit 0, the answer, and no "Failed to export". C2 is killed. |
| LOW `cli.py:47-53`: repeated in-process `main()` stacks `NullHandler`s (Worth a look) | open, not taken (optional) |
| LOW `CLAUDE.md:164-166`: `tracer.py` listed under "I/O and wiring" (Worth a look) | open, not taken (optional) |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (one test and Progress, as round 1 asked; src diff since e5c12b1 empty) |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear) |
| 3 | Behaviour against the spec | pass (unchanged since round 1; Reproduction 2 strengthened) |
| 4 | Tests prove the behaviour, not only pass | pass (C2 killed; C1, C3 still killed; probe mutants show the new test bites) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (Progress "111 pytest tests" reproduced) |
| 7 | Documentation | pass (1 LOW carried, Worth a look) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 3, fix)
  error: A live check is owed and not recorded. Do the steps in intents/3-low-findings-from-1/review.md → ## Live check, then set live_checked: <date> in intents/3-low-findings-from-1/metadata.yml.
  note:  10 file(s), 265 line(s) changed outside intents/.
```
The only error is the owed live check, which round 1 set; it is the
owner's to clear (review skill, step 1). The line count rose by 11 from
round 1's 254: the added test lines.

## Findings
- **LOW** `src/advisor/cli.py:47-53` — each in-process `main()` without
  `--debug` adds another `NullHandler` to the `opentelemetry` logger and
  leaves `propagate = False` for the rest of the process, including the
  pytest session. A future `caplog` test on `opentelemetry` would see
  nothing. Carried from round 1. Worth a look: add the handler only if
  absent, or reset it in a fixture.
- **LOW** `CLAUDE.md:164-166` — `tracer.py` is listed under "I/O and wiring
  (not core; the live check covers them)", though it is SDK-free with no
  I/O. Carried from round 1. Worth a look.

Mutants this round (full `pytest -q -x` each; backup by copy, one exact
match, `git diff --quiet` non-zero asserted, restore by copy in `finally`):

| id | change | result | killing test |
| --- | --- | --- | --- |
| **C2** | `cli.py`: `otel.propagate = False` → `pass` | **KILLED** | test_cli_stderr::test_export_failure_is_silent_even_with_a_root_handler |
| C1 | `cli.py`: `otel.addHandler(logging.NullHandler())` → `pass` | KILLED | test_cli_stderr::test_export_failure_is_silent_without_debug |
| C3 | `cli.py`: `else:` → `if True:` | KILLED | test_cli_stderr::test_export_failure_shows_with_debug |
| P1 | probe: root-handler install → `pass` (src unmutated) | survived, 111 passed (expected: correct code passes either way) | — |
| P1+C2 | no root handler **and** `propagate = False` removed | survived, 111 passed: the new test's power comes from the root handler | — |

If the probe's `sys.argv.remove("--root-handler")` were lost, the question
would start with "-", and `cli.main` would exit 2 (`cli.py:41-43`), failing
the `returncode == 0` assertion. This was read from the code, not run.
Round 1's other 13 mutants were not re-run: their targets and killing tests
are unchanged (empty src diff; `test_cli_stderr.py` changed only by
addition). No mutant survives in `src/`.

## Not checked
- **The real OpenTelemetry exporter** against an unreachable Langfuse:
  whether anything else, such as a `langfuse` logger record, reaches stderr
  at shutdown. The live check covers this.
- **The real Langfuse run** (trace content in the UI).
- **The socket guard does not reach the subprocess tests.** They run outside
  `tests/conftest.py`'s guard: safe today, but nothing enforces it.
- **The root-handler case under `--debug`**, or a root handler added after
  `main()` returns: outside the intent.
- **The subprocess tests on Linux or macOS.**
- **Whether `advisor.models` imports `anthropic`:** out of scope.
- **Round 1's 13 other mutants:** not re-run (inputs unchanged).

## Live check
- owed: rule 1 (`src/advisor/cli.py`, `src/advisor/tracing.py`), and rule 3
  for the real exporter's stderr with Langfuse down. Round 2 changes none of
  the steps.
- steps (Windows PowerShell; neither the worktree nor the main checkout has
  a root `.env`, so set the variables in the session):
  1. ```
     cd C:\Users\eric\src\product-advice-agent-wt\3-low-findings-from-1
     npm run setup:worktree
     $env:ANTHROPIC_API_KEY = "<your key>"
     ```
  2. **Langfuse running.** Copy your `infra/langfuse/.env` into this
     worktree's `infra/langfuse/`, then run `docker compose -f
     infra/langfuse/docker-compose.yml up -d`, then:
     ```
     $env:LANGFUSE_HOST = "http://localhost:3000"; $env:LANGFUSE_PUBLIC_KEY = "<pk>"; $env:LANGFUSE_SECRET_KEY = "<sk>"
     uv run advisor "I need noise-cancelling headphones under 200 euros"; echo "exit $LASTEXITCODE"
     ```
  3. **Langfuse stopped.** Run `docker compose -f
     infra/langfuse/docker-compose.yml stop`, then:
     ```
     uv run advisor "I need noise-cancelling headphones under 200 euros" 2> stderr.txt; echo "exit $LASTEXITCODE"; Get-Content stderr.txt
     ```
     Without Docker, `$env:LANGFUSE_HOST = "http://127.0.0.1:3999"` (a
     closed port) gives the same case.
  4. **Stopped, with `--debug`:**
     ```
     uv run advisor --debug "I need noise-cancelling headphones under 200 euros" 2> stderr.txt; echo "exit $LASTEXITCODE"; Get-Content stderr.txt
     ```
  5. **Clean up:** `Remove-Item stderr.txt; Remove-Item Env:LANGFUSE_*`. The
     worktree must stay clean (the copied `infra/langfuse/.env` is
     gitignored).
- you should see:
  - **Step 2:** an answer as in §1's live check, `exit 0`, nothing on
    stderr, and one new trace with §1's structure.
  - **Step 3:** the answer, `exit 0` (up to about 5 s slower), and an empty
    `stderr.txt`: no "Failed to export span batch …" and no `langfuse` log
    line.
  - **Step 4:** the answer, `exit 0`, and an OpenTelemetry export failure
    line in `stderr.txt`, perhaps after "Transient error … retrying"
    warnings.
  - If step 3 shows any stderr text, or step 4 shows none, it's a defect:
    leave `live_checked:` empty.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/3-low-findings-from-1` at 61b37b8, `git status --short` empty before and after):
- **Coordinator, re-run:** `git diff e5c12b1 HEAD -- src` → empty; `git
  diff --stat e5c12b1 HEAD` → `plan.md`, `review.md`,
  `tests/test_cli_stderr.py` (+11), plus `metadata.yml` (round write).
  Matches.
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "60 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "111 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL, exit 1, with only
  the owed-live-check error (above). Matches.
- **Coordinator, re-run:** C2 (`otel.propagate = False` → `pass`) KILLED by
  test_cli_stderr::test_export_failure_is_silent_even_with_a_root_handler;
  C1 KILLED by test_cli_stderr::test_export_failure_is_silent_without_debug.
  Same harness as round 1 (backup by copy, one replacement, file-changed
  assertion, full `pytest -q -x`, restore by copy). Matches.

**Reviewer, verified:**
- HEAD 61b37b8.
- `e5c12b1..HEAD` = 533412a, f2fcf23, 61b37b8.
- `main` moved only through §4's intent artefacts (no overlap).
- Nothing pushed.
- `verify` and `check:intent` as above.
- `sdlc:scan --sample-due auto --exclude 3` → "nth attested auto change =
  1, every 3, sampled: no".
- Mutants C2, C1, C3, P1 and P1+C2 (harness `…/scratchpad/mut3r2/harness.py`).
- The rework diff and `tests/test_cli_stderr.py` read in full. The new
  test's comment is accurate: a `NullHandler` does not stop propagation to
  root.

**Taken on trust:** round 1's results for the 13 mutants not re-run, and
its Reproduction and failing-first checks (inputs unchanged); that §1's
live check looked as described. No real Langfuse, Anthropic, Docker or
network service was contacted.

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: e5c12b1a45eb477f5b4a3252121e2b7612d2652b
- round: 1
- sampled: no
- run: auto
- live-check: owed

The fix does what the intent asks. All five §1 findings are closed, both new
subprocess tests fail on `main`'s code, and 15 of 16 mutants are killed. The
verdict is rework for one surviving mutant, C2: removing `otel.propagate =
False` in `cli.py`. The plan's Tests table claims the stderr test kills it,
but it doesn't. The fix is one more test case.

Tier: Reviewed, set by the path table: `src/advisor/cli.py` and
`src/advisor/tracing.py` are Reviewed by meaning. `review_tier: reviewed`
agrees, and no finding raises it further. Status is `in-review`.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (exactly plan subtasks 1–8; no unplanned scope) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec (intent Outcome, Reproduction 1–3) | pass |
| 4 | Tests prove the behaviour, not only pass | findings (1): 16 mutants, 15 killed, 1 survived (C2) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (Progress "110 pytest tests" reproduced; cited SDK lines match) |
| 7 | Documentation | pass (1 LOW, Worth a look) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 3, fix)
  note:  10 file(s), 254 line(s) changed outside intents/.
```

### Behaviour (pass 3)

- **Reproduction 1** on the branch: `import advisor.agent` leaves
  `langfuse` and every `opentelemetry*` module out of `sys.modules`.
  `advisor.tracing.Tracer is advisor.tracer.Tracer`, and the same holds for
  `NoopTracer`.
- **Reproduction 2:** `tests/test_cli_stderr.py`, on the real exporter
  logger name (`opentelemetry.exporter.otlp.common.http`, per the installed
  SDK's `http.py:28`, `:223`):
  - without `--debug`: exit 0, the answer on stdout, no "Failed to export"
    on stderr;
  - with `--debug`: the line shows.
- **Reproduction 3:** R20, L5, L6 and C13 are each killed by a named test.
- **Failing first:** with `main`'s `agent.py`, `tracing.py` and `cli.py`
  copied in, both
  `test_boundaries.py::test_pure_modules_load_no_tracing_sdk` and
  `test_cli_stderr.py::test_export_failure_is_silent_without_debug` FAILED.
  The `--debug` test passed there, as expected, since it asserts kept
  behaviour.
- **No change** in answers, refusals, exit codes or trace content. The
  existing suite is unmodified apart from the C13 assertion
  (`tests/test_catalogue.py:110-112`).
- `follows_up: 1` is right.

### Findings

- **LOW** `src/advisor/cli.py:53`, `tests/test_cli_stderr.py` — mutant C2
  (`otel.propagate = False` removed) survives the full suite.
  - The plan's Tests table says the stderr test "fails if the
    `NullHandler`/`propagate` lines are removed". That holds only for the
    `NullHandler`.
  - The plan's own reason for `propagate = False` is a root handler
    "someone adds later". No test covers that case; the implementer
    recorded it as a divergence.
  - Needs rework: in `tests/test_cli_stderr.py`, add a case whose probe
    installs `logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))`
    before `cli.main(["q"], …)` without `--debug`. Assert exit 0, the answer
    on stdout, and no "Failed to export" on stderr. The reviewer's scratch
    probe showed this kills C2 and passes on the unmutated code. Mutant to
    re-run: C2.
- **LOW** `src/advisor/cli.py:47-53` — each in-process `main()` without
  `--debug` adds another `NullHandler` to the `opentelemetry` logger, and
  leaves `propagate = False` for the rest of the process, including the
  pytest session. That is harmless for a one-shot CLI, and no current test
  depends on it, but a future `caplog` test on `opentelemetry` would see
  nothing. Worth a look: add the handler only if absent, or reset it in a
  fixture.
- **LOW** `CLAUDE.md:164-166` — `tracer.py` is listed under "I/O and wiring
  (not core; the live check covers them)", though it is SDK-free with no
  I/O, and the plan keeps it out of `CORE_CODE`. Its category is wrong, not
  its description. Worth a look.

Mutants (full `pytest -q` each; backup by copy, `git diff --quiet` non-zero
asserted, restore by copy):

| id | change | result | killing test |
| --- | --- | --- | --- |
| A1 | `agent.py:20` imports `Tracer` from `advisor.tracing` again | KILLED | test_boundaries::test_pure_modules_load_no_tracing_sdk |
| T1 | `tracing.py:19` re-export removed | KILLED | collection errors (test_agent, test_cli, test_tracing) |
| TR1 | `tracer.py` adds `import langfuse` | KILLED | test_only_tracing_imports_langfuse, test_pure_modules_load_no_tracing_sdk |
| TR2 | `tracer.py` adds `import opentelemetry.trace` | KILLED | test_pure_modules_load_no_tracing_sdk |
| TR3 | `NoopTracer.finish` raises | KILLED | test_cli::test_happy_path_prints_answer_exit_0 |
| TR4 | `NoopTracer.check` raises | KILLED | test_cli::test_happy_path_prints_answer_exit_0 |
| C1 | `otel.addHandler(logging.NullHandler())` removed | KILLED | test_cli_stderr::test_export_failure_is_silent_without_debug |
| **C2** | **`otel.propagate = False` removed** | **SURVIVED** | — |
| C3 | `else:` → `if True:` (quiet with `--debug` too) | KILLED | test_cli_stderr::test_export_failure_shows_with_debug |
| C4 | `getLogger("opentelemetry")` → `("opentelemetry.sdk")` | KILLED | test_export_failure_is_silent_without_debug |
| C5 | `NullHandler()` → `StreamHandler()` | KILLED | test_export_failure_is_silent_without_debug |
| R20 | `SafeTracer.check` forwards `True` for `allowed` | KILLED | test_tracing::test_safe_tracer_forwards_a_blocked_check |
| L5 | `logging.getLogger("advisor").setLevel(logging.DEBUG)` removed | KILLED | test_cli::test_debug_sets_advisor_logger_to_debug |
| L6 | `reconfigure(encoding="utf-8", errors="replace")` → `pass` | KILLED | test_cli::test_stdout_is_reconfigured_to_utf8 |
| L6b | `encoding="utf-8"` → `"ascii"` | KILLED | test_cli::test_stdout_is_reconfigured_to_utf8 |
| C13 | not-a-list check removed | KILLED | test_catalogue::test_not_a_list_bad_json_missing_file_bad_entry |

### Not checked
- **The real OpenTelemetry exporter** against an unreachable Langfuse
  (Reproduction 2 as written). The suite uses a log record on the real
  exporter's logger name. Whether the real export path at interpreter
  shutdown writes anything else to stderr is unverified. A record on the
  `langfuse` logger, which has no handler, would reach `logging.lastResort`
  and is not quietened. No export-related `langfuse_logger.error`/`warning`
  was found in `span_processor.py` or `resource_manager.py`. The live check
  covers this.
- **The real Langfuse run** (trace content unchanged in the UI): only code
  reading and the unmodified `test_tracing.py`.
- **The socket guard does not reach the subprocess tests.** They run
  outside `tests/conftest.py`'s guard. They are safe today, because the
  probe patches `cli.make_tracer` and injects a scripted client, but nothing
  enforces it.
- **The subprocess tests on Linux or macOS:** run only on Windows with
  Python 3.12.9.
- **Whether `advisor.models` imports `anthropic`:** the new import test
  checks only `langfuse` and `opentelemetry`.

### Live check
- owed: rule 1 (`src/advisor/cli.py`, `src/advisor/tracing.py`), and rule 3
  for the first Not-checked item (real exporter stderr with Langfuse down).
  Run after the rework.
- steps (Windows PowerShell; neither the worktree nor the main checkout has
  a root `.env`, so set the variables in the session):
  1. ```
     cd C:\Users\eric\src\product-advice-agent-wt\3-low-findings-from-1
     npm run setup:worktree
     $env:ANTHROPIC_API_KEY = "<your key>"
     ```
  2. **Langfuse running.** Copy your `infra/langfuse/.env` into this
     worktree's `infra/langfuse/`, then run `docker compose -f
     infra/langfuse/docker-compose.yml up -d`, then:
     ```
     $env:LANGFUSE_HOST = "http://localhost:3000"; $env:LANGFUSE_PUBLIC_KEY = "<pk>"; $env:LANGFUSE_SECRET_KEY = "<sk>"
     uv run advisor "I need noise-cancelling headphones under 200 euros"; echo "exit $LASTEXITCODE"
     ```
  3. **Langfuse stopped.** Run `docker compose -f
     infra/langfuse/docker-compose.yml stop`, then:
     ```
     uv run advisor "I need noise-cancelling headphones under 200 euros" 2> stderr.txt; echo "exit $LASTEXITCODE"; Get-Content stderr.txt
     ```
     Without Docker, `$env:LANGFUSE_HOST = "http://127.0.0.1:3999"` (a
     closed port) gives the same case.
  4. **Stopped, with `--debug`:**
     ```
     uv run advisor --debug "I need noise-cancelling headphones under 200 euros" 2> stderr.txt; echo "exit $LASTEXITCODE"; Get-Content stderr.txt
     ```
  5. **Clean up:** `Remove-Item stderr.txt; Remove-Item Env:LANGFUSE_*`. The
     worktree must stay clean (the copied `infra/langfuse/.env` is
     gitignored).
- you should see:
  - **Step 2:** an answer as in §1's live check, `exit 0`, nothing on
    stderr, and one new trace with §1's structure.
  - **Step 3:** the answer, `exit 0` (up to about 5 s slower), and an empty
    `stderr.txt`: no "Failed to export span batch …" and no `langfuse` log
    line.
  - **Step 4:** the answer, `exit 0`, and an OpenTelemetry export failure
    line in `stderr.txt`, perhaps after "Transient error … retrying"
    warnings.
  - If step 3 shows any stderr text, or step 4 shows none, it's a defect:
    leave `live_checked:` empty.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/3-low-findings-from-1` at e5c12b1, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "59 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "110 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0. Matches.
- **Coordinator, re-run:** mutants with my own harness (backup by copy, one
  replacement, file-changed assertion, full `pytest -q -x`, restore by copy):
  - C2 (`otel.propagate = False` → `pass`) SURVIVED, "110 passed";
  - C1 (`otel.addHandler(logging.NullHandler())` → `pass`) KILLED by
    test_cli_stderr::test_export_failure_is_silent_without_debug;
  - A1 KILLED by test_boundaries::test_pure_modules_load_no_tracing_sdk;
  - R20 KILLED by test_tracing::test_safe_tracer_forwards_a_blocked_check.

  Each matches the reviewer.

**Reviewer, verified:**
- HEAD e5c12b1 on `fix/3-low-findings-from-1`; no upstream; `main` moved
  only through §4's intent artefacts, with no overlap.
- `verify` and `check:intent` as above.
- `sdlc:scan --sample-due auto --exclude 3` → "nth attested auto change =
  1, every 3, sampled: no".
- Failing-first with `main`'s three source files copied in.
- 16 mutants (harness `…/scratchpad/mut3r/harness.py`).
- The C2 kill probe (`…/scratchpad/mut3r/c2probe.py`, `roothandler.py`).
- Reproduction 1, and the re-export identity.
- `git diff main...HEAD` read in full for `src`, `tests` and `CLAUDE.md`.
- The installed `langfuse`/`opentelemetry` logging calls, by grep.

**Taken on trust:** the R20, L5, L6 and C13 definitions, from §1's
`review.md` text; that §1's live check looked as described. No real
Langfuse or Anthropic was run.
