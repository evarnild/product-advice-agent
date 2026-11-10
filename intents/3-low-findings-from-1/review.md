<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §3 review — Close the LOW review findings left open by §1

verdict: rework
tier: reviewed
reviewed-commit: e5c12b1a45eb477f5b4a3252121e2b7612d2652b
round: 1
sampled: no
run: auto
live-check: owed

The fix does what the intent asks. All five §1 findings are closed, both new
subprocess tests fail on `main`'s code, and 15 of 16 mutants are killed. The
verdict is rework for one surviving mutant, C2: removing `otel.propagate =
False` in `cli.py`. The plan's Tests table claims the stderr test kills it,
but it doesn't. The fix is one more test case.

Tier: Reviewed, set by the path table: `src/advisor/cli.py` and
`src/advisor/tracing.py` are Reviewed by meaning. `review_tier: reviewed`
agrees, and no finding raises it further. Status is `in-review`.

## Passes
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

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 3, fix)
  note:  10 file(s), 254 line(s) changed outside intents/.
```

## Behaviour (pass 3)

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

## Findings

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

## Not checked
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

## Live check
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

## Verified myself vs. taken on trust

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
