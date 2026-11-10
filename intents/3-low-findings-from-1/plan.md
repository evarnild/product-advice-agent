<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §3 plan — Close the LOW review findings left open by §1

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Make the five §1 findings untrue (intent "Outcome").
- The pure modules (`agent`, `catalogue`, `guardrails`, `models`) load
  neither `langfuse` nor `opentelemetry`.
- A run prints no OpenTelemetry export error on stderr unless `--debug`.
- Mutants R20, L5, L6 and C13 each fail a named test.

Nothing changes in answers, refusals, exit codes or trace content.

## Risks

- **Tests that pass whatever the code does** (§1's recurring class).
  - Pytest installs its own handlers on the root logger. So an in-process
    test of "nothing on stderr" passes on today's `main` too, because
    `logging.lastResort` never fires under pytest. The stderr test must run
    in a fresh interpreter (subprocess). That is also where the import test
    must run, since the pytest process has already imported `langfuse`.
  - Each new test is run once against `main`'s code (or the mutant) and must
    fail there.
- **The `Tracer` move breaks importers.** `tests/test_agent.py:17`,
  `tests/test_cli.py:8` and `tests/test_tracing.py:15` import `NoopTracer`
  (and `SafeTracer` etc.) from `advisor.tracing`. `tracing.py` re-exports
  `Tracer` and `NoopTracer`, so those imports keep working unchanged.
- **Silencing too much.** Only the `opentelemetry` logger tree is quietened,
  and only without `--debug`. `advisor` logging and the CLI's own stderr
  messages (usage, missing key, unavailable) must stay. Existing CLI tests
  prove those.
- **Overlap with §2** (in flight on `feat/2-local-model`). §2 changes
  `cli.py` (keyless path, factory signature, tags), `tracing.py`
  (`make_tracer(env, tags)`, tags at `begin`) and `tests/test_boundaries.py`
  (new assertions). §3 touches the same three files. Whichever merges
  second rebases, and the rebase is textual: different functions or
  different tests.
- **Stale line citations:** read at `ccaedba`; re-check before editing.

## Verified against the codebase

Re-read on `main` at `ccaedba`.

- `src/advisor/agent.py:20` — `from advisor.tracing import Tracer` (the only tracing import in `agent.py`).
- `src/advisor/tracing.py:16` — `from langfuse import Langfuse` at module load.
- `src/advisor/tracing.py:21-64` — `class Tracer(Protocol)` and `class NoopTracer`; neither uses `langfuse`.
- `src/advisor/tracing.py:147-148` — `SafeTracer.check` → `self._guard("check", stage, allowed, reason)` (mutant R20: forward `True` instead of `allowed`).
- `src/advisor/tracing.py:163-177` — `make_tracer`; tests patch `tracing.Langfuse` (`tests/test_tracing.py:53,61,74,85`), so `Langfuse` stays a module-level name in `tracing.py`.
- `src/advisor/cli.py:19` — `from advisor.tracing import make_tracer`.
- `src/advisor/cli.py:44-46` — `if debug: logging.basicConfig(level=logging.WARNING, stream=sys.stderr); logging.getLogger("advisor").setLevel(logging.DEBUG)` (L5 is line 46).
- `src/advisor/cli.py:47-49` — `reconfigure = getattr(sys.stdout, "reconfigure", None)` … `reconfigure(encoding="utf-8", errors="replace")` (L6 is line 49).
- `src/advisor/catalogue.py:103-104` — `if not isinstance(data, list): raise CatalogueError("catalogue must be a JSON list of products")` (C13).
- `.venv/Lib/site-packages/opentelemetry/exporter/otlp/common/http.py:28` — `_logger = logging.getLogger(__name__)`; `:214`, `:223` log the export failures at ERROR (`"Failed to export %s batch due to timeout, max retries or shutdown."`); `:230` the retry warning. With no handler configured, `logging.lastResort` prints WARNING and above to stderr.
- `tests/helpers.py:6-30` — `RecordingTracer` records `("check", stage, allowed, reason)`.
- `tests/test_tracing.py:243-251` — the SafeTracer forwarding test runs only the allow path.
- `tests/test_catalogue.py:109-111` — `{"a": 1}` asserts only `CatalogueError`, not its message (why C13 survives: iterating the dict still fails per entry).
- `tests/test_cli.py:34-35` — autouse fixture replaces `cli.make_tracer`; `:98-103` `--debug` test asserts the traceback only.
- `tests/test_boundaries.py:9-29` — the AST import scan.
- `CLAUDE.md:165-166, 172-174` — "Architecture" says `tracing.py` holds the `Tracer` protocol and the no-op.

## Subtasks

1. **The failing-first test (item 1).** Add to `tests/test_boundaries.py`
   `test_pure_modules_load_no_tracing_sdk`. It runs `sys.executable -c` in a
   subprocess that imports `advisor.agent`, `advisor.catalogue`,
   `advisor.guardrails` and `advisor.models`, then asserts that no module
   named `langfuse`, `opentelemetry` or a submodule of either is in
   `sys.modules`. It fails on `main`. Commit it with the fix in step 2, so
   that every commit stays green.
2. **The fix (item 1).**
   - New SDK-free module `src/advisor/tracer.py` holding `Tracer` (the
     Protocol) and `NoopTracer`, moved verbatim with their docstrings.
   - `tracing.py` imports them from there and keeps both names importable
     (`from advisor.tracer import NoopTracer, Tracer`, listed in `__all__`
     or used, so ruff keeps them).
   - `agent.py` imports `Tracer` from `advisor.tracer`.
   - The `Langfuse` import stays at the top of `tracing.py`.
3. **The stderr fix (item 2), test first.** `tests/test_cli_stderr.py` runs
   a probe in a subprocess (fresh interpreter, no pytest log handlers). The
   probe calls `advisor.cli.main(["q"], env={...}, client_factory=<scripted
   fake>)` with `cli.make_tracer` patched to a tracer whose `finish` logs
   `"Failed to export span batch due to timeout, max retries or shutdown."`
   on `logging.getLogger("opentelemetry.exporter.otlp.common.http")` at
   ERROR. The test asserts:
   - (a) without `--debug`: exit 0, the answer on stdout, and `stderr` does
     not contain `Failed to export`;
   - (b) with `--debug`: the line is on stderr.

   (a) fails on `main`. Fix in `cli.py` (amended 2026-11-10, owner's
   request): a `_configure_logging(debug)` helper. Without `--debug`,
   `logging.basicConfig(handlers=[logging.NullHandler()])`: the CLI speaks
   through `print` only, so no library's log line reaches stderr, and an
   existing logging setup is left alone. With `--debug`, nothing changes,
   and `basicConfig` shows it. Comment site: why (spec §1 B17, a tracing
   failure never shows as a run error). The probe also logs a `langfuse`
   warning, and (c) asserts that a root handler installed before `main`
   still receives the line.
4. **R20 (item 3).** In `tests/test_tracing.py`, add
   `test_safe_tracer_forwards_a_blocked_check`: it runs `answer_question`
   with `check_input` monkeypatched to block, through
   `SafeTracer(RecordingTracer())`, and asserts that the events contain
   `("check", "input", False, <reason>)` and `("finish", REFUSAL_TEXT)`.
5. **L5, L6 (item 4).** In `tests/test_cli.py`:
   - `test_debug_sets_advisor_logger_to_debug`: after
     `main(["--debug", "q"], …)`, `logging.getLogger("advisor").level ==
     logging.DEBUG`, with the level restored in a `finally`/fixture;
   - `test_stdout_is_reconfigured_to_utf8`: `monkeypatch.setattr(sys,
     "stdout", <object with a recording reconfigure and write>)`, then
     `main(["q"], …)`, then assert `reconfigure` was called with
     `encoding="utf-8", errors="replace"`.
6. **C13 (item 5).** In `tests/test_catalogue.py`, the `{"a": 1}` case
   asserts the message contains `must be a JSON list`. Split it into its own
   test if that reads better; no other case is weakened.
7. **Docs.**
   - `CLAUDE.md` → "Architecture": `tracer.py` holds the `Tracer` protocol
     and the no-op (SDK-free, so the pure modules import it); `tracing.py`
     holds the Langfuse tracer, `SafeTracer` and `make_tracer`. Under
     "Conventions", the new boundary test, and that OpenTelemetry's own log
     lines show only with `--debug`.
   - `README.md`, only if it mentions the export line. It doesn't today;
     the implementer checks.
8. **Status.** Set `status: in-review` and append to `## Progress`.

## Tests

| Intent item | Test | Fails on `main` / when mutated |
| --- | --- | --- |
| 1 (failing first) | `test_boundaries.py::test_pure_modules_load_no_tracing_sdk` (subprocess) | fails on `main`; fails again if `agent.py` imports from `advisor.tracing` |
| 1 | existing `test_only_tracing_imports_langfuse` | `langfuse` imported in `tracer.py` |
| 2 | `test_cli_stderr.py` (a) without `--debug` | fails on `main`; fails if the root `NullHandler` is removed, or only `opentelemetry` is quietened |
| 2 | `test_cli_stderr.py` (b) with `--debug` | fails if the quietening also applies with `--debug` |
| 2 | `test_cli_stderr.py` (c) existing root handler | fails if the CLI overrides an existing logging setup (`force=True`) |
| 3 (R20) | `test_tracing.py::test_safe_tracer_forwards_a_blocked_check` | R20 (`allowed` → `True` in `SafeTracer.check`) |
| 4 (L5) | `test_cli.py::test_debug_sets_advisor_logger_to_debug` | L5 (line 46 removed) |
| 4 (L6) | `test_cli.py::test_stdout_is_reconfigured_to_utf8` | L6 (line 49 removed, or `encoding` changed) |
| 5 (C13) | `test_catalogue.py`: the not-a-list message | C13 (lines 103-104 removed) |
| unchanged behaviour | the whole existing suite, unmodified except the C13 assertion | — |

The implementer runs each mutant (R20, L5, L6, C13) once against the new
tests, and runs the item-1 and item-2 tests once against `main`'s code. It
reports the results in `## Progress`. It backs up and restores by copy and
finishes with `git status --short` clean.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (fix: carries test changes; the core-code
  change in `agent.py` comes with tests).
- Live check, owed by rule 1 (`src/advisor/cli.py`, `src/advisor/tracing.py`).
  The owner runs it:
  1. Langfuse running, keys set: `uv run advisor "I need noise-cancelling
     headphones under 200 euros"`. Same answer and trace as §1's live check.
  2. Langfuse stopped (`docker compose -f infra/langfuse/docker-compose.yml
     stop`): the same command answers, exit 0, and stderr shows nothing
     about exporting spans.
  3. The same, with `--debug`: the export-failure line does appear.

## Assumptions I made

- **Module name `tracer.py`** for the SDK-free protocol. Close to
  `tracing.py`, but it names what it holds. The intent left the choice to
  the plan; a lazy `Langfuse` import was the other option. It was rejected
  because tests patch `tracing.Langfuse` as a module attribute.
- **Silencing means a root `NullHandler` via `basicConfig`** (amended
  2026-11-10; was a `NullHandler` with `propagate = False` on the
  `opentelemetry` logger). The advisor never uses logging for user output,
  so all library log lines are quiet without `--debug`, the `langfuse`
  logger included. `basicConfig` is a no-op when logging is already set
  up, so repeated `main()` calls stack nothing, and a caller's own root
  handler is respected.
- **The stderr probe emits the log record itself** rather than starting a
  real exporter against a refused port. The test then needs no network or
  timing. The real exporter path is the live check's step 2.
- **`tracer.py` is not added to `CORE_CODE`.** It holds a Protocol and a
  no-op, with no logic worth the core-code rule.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-10 — implementation (single phase)

Commits: 1307fbc (fix items 1 and 2 with their failing-first tests), then the
R20/L5/L6/C13 tests commit, then the docs/status commit (hashes in the git log
of this branch).

Shipped:
- `src/advisor/tracer.py` (Tracer, NoopTracer, SDK-free); `agent.py` imports
  from it; `tracing.py` imports and still exposes both names.
- `cli.py`: without `--debug` the `opentelemetry` logger gets a NullHandler
  and `propagate = False`.
- Tests: `test_boundaries.py::test_pure_modules_load_no_tracing_sdk`,
  `test_cli_stderr.py` (2 tests, subprocess), `test_tracing.py::
  test_safe_tracer_forwards_a_blocked_check`, `test_cli.py::
  test_debug_sets_advisor_logger_to_debug` and
  `test_stdout_is_reconfigured_to_utf8`, and the C13 message assertion in
  `test_catalogue.py` (the only existing assertion changed).
- `CLAUDE.md` Architecture and Conventions updated. README does not mention
  the export line; unchanged.

Failing first (run on main's code before the fix):
- `test_pure_modules_load_no_tracing_sdk`: fails on main (yes).
- `test_cli_stderr.py::test_export_failure_is_silent_without_debug`: fails on
  main (yes). The `--debug` test passes on main, as expected (behaviour kept).

Mutants against the new tests (backup/restore by copy; tree clean after):
- R20 (`allowed` -> `True` in SafeTracer.check): KILLED by
  `test_safe_tracer_forwards_a_blocked_check`.
- L5 (advisor logger DEBUG line removed): KILLED by
  `test_debug_sets_advisor_logger_to_debug`.
- L6 (reconfigure call removed): KILLED by
  `test_stdout_is_reconfigured_to_utf8`.
- C13 (not-a-list check removed): KILLED by
  `test_catalogue.py::test_not_a_list_bad_json_missing_file_bad_entry`.
- Extra: `agent.py` importing from `advisor.tracing` again: KILLED by the
  boundary test. Removing the `NullHandler` line: KILLED by
  `test_export_failure_is_silent_without_debug`.

Divergences:
- Removing only the `propagate = False` line SURVIVES: the plan table says the
  stderr test fails if the NullHandler/propagate lines are removed, which
  holds for the NullHandler (it alone stops `logging.lastResort`), not for
  `propagate` alone. `propagate = False` only matters when a root handler
  exists, which the CLI never installs without `--debug`. Left as the plan
  specifies; not tested separately.
- `test_cli_stderr.py` runs an `advisor.cli` probe with `-c`, patching
  `cli.make_tracer` in the probe, as planned.
- The `--debug` stderr test passes on main (it asserts unchanged behaviour).

Test counts: see the final `npm run verify` in the report (110 pytest tests
before the docs commit).

### 2026-11-10 — Rework round 1

Commit: the "§3: cover propagate" commit on this branch (tests and Progress only).

- Added `test_cli_stderr.py::test_export_failure_is_silent_even_with_a_root_handler`:
  the probe takes a `--root-handler` flag and installs a root
  `StreamHandler(sys.stderr)` before `cli.main(["q"])` (no `--debug`); asserts
  exit 0, the answer on stdout, no "Failed to export" on stderr. Passes on
  unmutated code.
- C2 (`otel.propagate = False` replaced by `pass`): KILLED by that test.
  Backup/restore by copy; tree clean afterwards.
- Optional "worth a look" items not taken.
- `npm run verify`: green, 111 pytest tests passed.

### 2026-11-10 — Amendment: logging rule (owner's request, after round 2)

Owner asked for a cleaner fix of item 2 after reading the diff; subtask 3,
the Tests table and the Assumptions are amended above.

- `cli.py`: `_configure_logging(debug)`. Without `--debug`,
  `logging.basicConfig(handlers=[logging.NullHandler()])` replaces the
  `opentelemetry` `NullHandler` + `propagate = False`. Closes round 1/2's LOW
  "repeated `main()` stacks `NullHandler`s" (no logger is mutated when logging
  is already set up) and covers the `langfuse` logger too.
- `tests/test_cli_stderr.py`: the probe also logs a `langfuse` warning;
  tests renamed to `test_library_log_lines_are_silent_without_debug`,
  `test_library_log_lines_show_with_debug`; the root-handler test flips to
  `test_an_existing_logging_setup_is_left_alone` (the line reaches the
  caller's handler).
- `CLAUDE.md` Conventions: the rule and the helper.
- Mutants (backup/restore by copy, tree clean after), each KILLED:
  M1 root `NullHandler` line → `pass`; M2 `if debug:` → `if True:`;
  M5 the `_configure_logging` call removed (all three by
  `test_library_log_lines_are_silent_without_debug`); M3 `force=True`
  (by `test_an_existing_logging_setup_is_left_alone`); M4 the old fix,
  `opentelemetry` logger only (by the `langfuse` assertion in
  `test_library_log_lines_are_silent_without_debug`).
- `npm run verify`: green, 111 pytest tests passed.
