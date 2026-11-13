<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §12 plan — Trace eval runs to Langfuse, tagged as evals

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`uv run advisor-eval` sends one Langfuse trace per case when the three
`LANGFUSE_*` variables are set, tagged `eval`, `provider:`, `model:`,
`run:<stamp>` and `case:<id>` (spec B1-B4), through the existing
`make_tracer`, beside the recording tracer the scorers read (B8). A run
without the variables loads neither `advisor.tracing` nor `langfuse` (B9),
and nothing the run prints, returns or reports changes apart from
`duration_s` (B6). `tracing.py`, `agent.py` and `cli.py` are not edited
(B10). The branch is based on `feat/9-error-analysis` (intent constraint 1)
and is rebased onto `main` after §9 merges.

## Risks

- **A failing Langfuse tracer reaching the run.** `make_tracer` returns a
  `SafeTracer`, but a test-injected factory need not. The fan-out guards its
  second tracer itself, so B8 holds whatever the factory returns.
- **The recording tracer's order or content changing.** The scorers read
  `searches`; §9's report reads `turns`, `tools`, `guardrails` and the
  `offer_results` hand-over from `_recording_tool`. The fan-out must pass
  every call to the recording tracer first and unchanged, and
  `_recording_tool` must keep receiving the `RecordingTracer` itself, not
  the fan-out (it calls `offer_results`, which is not on the protocol).
- **An eager import.** A top-level `from advisor.tracing import …` in
  `run.py` breaks `test_eval_runner_loads_no_sdk` (B9, AC6). The import is
  inside the default factory only.
- **The env rule drifting.** The lazy check must name the same three
  variables as `tracing.REQUIRED_ENV`; a test compares them.
- **Extra clock reads.** `ticking_clock` tests count `now()` calls
  (`tests/test_evals_run.py:64`, `:137`). The stamp is computed from the
  existing `started`, with no new `now()` call.
- **Tests that pass whatever the code does.** Tag tests compare the whole
  list (order fixed by B4) per case, with two cases and a fixed clock, so a
  tag built once for the run, or with the wrong case, fails.
- **Stale citations.** Lines below are on the §9 branch; the implementer
  re-checks them at launch, and again after §9's round 3 if it reworks
  `run.py`.
- **Pass 9 footguns:** the list in `REVIEW-POLICY.md` is empty.

## Verified against the codebase

Re-read on `main` at `4dd068a` and on `feat/9-error-analysis` at `2421d9e`
(for `src/advisor/evals/run.py`, `tests/test_evals_run.py`, `README.md`,
`CLAUDE.md`).

- `src/advisor/tracing.py:21` — `FLUSH_TIMEOUT_SECONDS = 5.0`.
- `src/advisor/tracing.py:27` — `REQUIRED_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")`.
- `src/advisor/tracing.py:39-47` — `begin` starts `advisor-run` and sets `langfuse.trace.tags` when tags are given.
- `src/advisor/tracing.py:86-94` — `_close` ends the root and flushes, joined for at most 5 s.
- `src/advisor/tracing.py:97-125` — `SafeTracer` swallows every exception.
- `src/advisor/tracing.py:128-142` — `make_tracer(env, tags=())`: `NoopTracer` unless all of `REQUIRED_ENV` are set; `SafeTracer(LangfuseTracer(client, tags))`.
- `src/advisor/tracer.py` — the `Tracer` protocol (`begin`, `check`, `generation`, `tool`, `finish`, `fail`) and `NoopTracer`; SDK-free.
- `src/advisor/agent.py:172-198` — `answer_question` calls `begin`, `check("input")`, the loop, `check("output")`, `finish`; `fail` on an exception; `finish(REFUSAL_TEXT)` on an input block.
- `src/advisor/cli.py:106-107` — `tags = [f"provider:{settings.provider}", f"model:{settings.model}"]`; `make_tracer(full_env, tags)`.
- `src/advisor/evals/run.py:1-7` (§9) — the docstring: "never imports `advisor.tracing`, so an eval run does not reach Langfuse."
- `src/advisor/evals/run.py:40-86` (§9) — `RecordingTracer`, with `offer_results` (not on the protocol).
- `src/advisor/evals/run.py:89-102` (§9) — `_recording_tool(tool, tracer: RecordingTracer)`.
- `src/advisor/evals/run.py:130-137` (§9) — `main(argv, *, env, client_factory=make_client, out, err, now=_utc_now)`.
- `src/advisor/evals/run.py:172` (§9) — `settings = load_settings(load_env(env))`.
- `src/advisor/evals/run.py:200-210` (§9) — `started = now()`; per case `tracer = RecordingTracer()` and `answer_question(case.question, client, [_recording_tool(tool, tracer)], tracer)`.
- `src/advisor/evals/run.py:253` (§9) — `stamp = started.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")`, after the loop.
- `tests/test_evals_run.py:64-85` (§9) — `ticking_clock`, `run(tmp_path, script, *extra, cases, env, now)` calling `main(..., env=env, client_factory=..., now=now)`.
- `tests/test_boundaries.py:64-77` — `test_eval_runner_loads_no_sdk` (subprocess; `advisor.tracing` must not be loaded by importing `advisor.evals.run`).
- `tests/test_tracing.py:283-295`, `:315-319` — the CLI's tag tests and `make_tracer` passing tags.
- `README.md:127` (§9) — "and does not trace to Langfuse."
- `README.md:44-46` — "Every trace is tagged `provider:<name>` and `model:<name>`."
- `CLAUDE.md` "Offline evals" — "It imports neither `advisor.tracing` nor a provider SDK."
- `intents/8-offline-evals/spec.md:139-140` — B11.

## Subtasks

1. **The tracer seam in `run.py`** (B1, B2, B4, B8, B9).
   - `full_env = load_env(env)`; `settings = load_settings(full_env)`.
   - A module constant `_LANGFUSE_ENV`, the same three names as
     `tracing.REQUIRED_ENV`, and `_default_tracer_factory(env, tags) ->
     Tracer`: `NoopTracer()` unless all three are non-empty in `env`;
     otherwise `from advisor.tracing import make_tracer` **inside the
     function** and `return make_tracer(env, tags)`. Comment: the spec's
     Interpretation on the lazy load (B9).
   - `main(..., tracer_factory: Callable[[Mapping[str, str], Sequence[str]], Tracer] = _default_tracer_factory)`.
   - `_FanOutTracer(primary: RecordingTracer, secondary: Tracer)`: each
     protocol method calls `primary` first, then `secondary` inside
     `try/except Exception: pass` (comment: B8, "a failure in the Langfuse
     tracer never reaches the recording tracer or the run").
   - Compute `stamp` from `started` right after `started = now()` (no new
     `now()` call) and reuse it for the report filename.
   - Per case: `tags = ["eval", f"provider:{settings.provider}",
     f"model:{settings.model}", f"run:{stamp}", f"case:{case.id}"]`;
     `recording = RecordingTracer()`; `traced = _FanOutTracer(recording,
     tracer_factory(full_env, tags))`; `answer_question(case.question,
     client, [_recording_tool(tool, recording)], traced)`. Everything that
     reads the recording tracer keeps reading `recording`.
   - Tests (AC1-AC4) in `tests/test_evals_run.py`, written first.
   - Commit.
2. **The boundary tests** (B9, AC1, AC6).
   - `tests/test_boundaries.py`: a subprocess test that runs
     `advisor.evals.run.main` on one case with the scripted fake client and
     an env without `LANGFUSE_*`, then asserts neither `advisor.tracing`
     nor `langfuse` is in `sys.modules`. `test_eval_runner_loads_no_sdk`
     stays unedited.
   - A test that `advisor.evals.run._LANGFUSE_ENV` equals
     `advisor.tracing.REQUIRED_ENV` (as sets, then as tuples).
   - Commit.
3. **Docs** (B11, AC7).
   - `src/advisor/evals/run.py` docstring: traces to Langfuse through
     `make_tracer` when configured, loaded lazily; the recording tracer
     still feeds the scorers.
   - `README.md` "Evaluating answers": replace "does not trace to
     Langfuse" with the rule, the tags, and "filter on tag `eval`, then on
     `run:<stamp>` from the report's filename"; one sentence that a down
     Langfuse adds up to 5 s per case.
   - `README.md` tracing paragraph: eval traces also carry `eval`, `run:`
     and `case:`.
   - `CLAUDE.md` "Offline evals": "It loads `advisor.tracing` only when
     the three `LANGFUSE_*` variables are set, and imports no provider SDK."
   - `intents/8-offline-evals/spec.md` B11: append the one line of spec
     B11 ("Superseded by §12: eval runs are traced when Langfuse is
     configured."). Nothing else in that file.
   - Commit; `status: in-review`; a Progress entry.

## Tests

All in `verify`; no network (`tests/conftest.py`), no real Langfuse client.
A `FakeTracer` in the test module records `(method, args)` calls; the
`tracer_factory` passed to `main` records the `(env, tags)` it was called
with and returns a `FakeTracer`.

| Test | Proves | Mutant it kills |
| --- | --- | --- |
| `test_each_case_gets_a_tracer_with_eval_run_and_case_tags` (two cases, fixed clock) | B4, AC2 | drop `"eval"`; a run-level tag list built once (case tag wrong on case 2); wrong stamp format |
| `test_trace_tags_follow_the_provider_and_model_flags` (`--provider anthropic --model m`) | B4, AC2 | tags from the env settings instead of the flagged ones |
| `test_run_tag_matches_the_report_file_name` | B4 | stamp computed from another clock read |
| `test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer` (a passing case, an unknown-tool case, a raising-model case) | B2, B8, AC3 | skip `secondary` for any one method; `fail` not forwarded |
| `test_a_raising_tracer_changes_nothing` (stdout, exit code, report minus `duration_s` equal to a run with the default factory and no `LANGFUSE_*`) | B6, B8, AC4 | remove the `try/except` in the fan-out; call `secondary` first |
| `test_the_recording_tracer_still_feeds_scores_and_report` (existing `expect_search` and §9 `tools`/`turns` tests unchanged and green) | B8 | `_recording_tool` given the fan-out |
| `test_default_factory_is_noop_without_all_three_variables` (each one missing or empty: no `advisor.tracing` import; patched `make_tracer` not called) | B1, B9, AC1 | `any` for `all`; the empty-string check removed |
| `test_default_factory_calls_make_tracer_with_env_and_tags_when_configured` (`advisor.tracing.make_tracer` monkeypatched to a fake) | B1, AC1 | tags or env not passed through |
| `tests/test_boundaries.py`: the subprocess run test; `_LANGFUSE_ENV == REQUIRED_ENV` | B9, AC1, AC6 | a top-level import of `advisor.tracing`; a renamed variable |
| existing `tests/test_tracing.py` tag tests, `test_eval_runner_loads_no_sdk` | B5, B10, AC5, AC6 | green and unedited |

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (it FAILs on the owed live check until the
  owner records it).
- Live check (owed by `REVIEW-POLICY.md` rule 3; spec AC8), for the owner:
  1. Start the local Langfuse (`docker compose -f
     infra/langfuse/docker-compose.yml up -d`), with its keys and
     `LANGFUSE_HOST` in the root `.env`.
  2. `uv run advisor-eval --only <two case ids>`; note the report filename
     stamp.
  3. In the Langfuse Tracing table, filter on tag `eval`: the two traces
     show, each with `provider:`, `model:`, `run:<that stamp>` and its own
     `case:<id>`; turns, tools and guardrail checks look as for a normal run.
  4. `uv run advisor "I need noise-cancelling headphones under 200 euros."`:
     its trace has no `eval`, `run:` or `case:` tag.
  5. Stop Langfuse, run step 2 again: the same PASS/FAIL lines and exit
     code, at most about 5 s slower per case.

## Assumptions I made

- **The branch is created from `feat/9-error-analysis`** with `npm run
  spawn -- 12 --base feat/9-error-analysis`, after §9's round 3 reports
  (intent constraint 1). If round 3 reworks `run.py`, the implementer
  rebases §12 onto §9's new head before starting (the coordinator says so in
  the brief).
- **The lazy check restates the three variable names** in `run.py`, guarded
  by a test that compares them with `tracing.REQUIRED_ENV`. Importing
  `REQUIRED_ENV` from `tracing.py` would load `langfuse` (B9), and moving it
  to `tracer.py` would edit `tracing.py` (B10).
- **`make_tracer` re-checks the variables**, so the rule is applied twice
  with the same names; the runner's check only decides whether to import.
- **The fan-out lives in `run.py`**, not in `tracer.py`, since only the
  runner needs it.
- **No new dependency.**

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-12 — build (subtasks 1-3)

Commits: e81c4d3 (tracer seam, fan-out, tag tests), 516328f (boundary
tests), 7fc7a56 (docs), plus the Progress/status commit that follows.

Shipped: `_LANGFUSE_ENV`, `_default_tracer_factory` (lazy `make_tracer`),
`_FanOutTracer` (recording first, secondary guarded), `tracer_factory`
parameter on `main`, per-case tags `eval`, `provider:`, `model:`,
`run:<stamp>`, `case:<id>` with the stamp taken from the existing `started`
(no new `now()` call). `tracing.py`, `agent.py`, `cli.py` untouched;
`test_eval_runner_loads_no_sdk` unedited. Docs: README (two places),
CLAUDE.md "Offline evals", run.py docstring, §8 spec B11 one line.

Tests: pytest 481 -> 491 (10 added: 8 in `tests/test_evals_run.py`, 2 in
`tests/test_boundaries.py`). Each Tests-table row was mutation-checked and
killed.

Divergences: line numbers in "Verified against the codebase" drifted
(e.g. `RecordingTracer` now at run.py:40 as planned, `main` settings at
:172 became :189 after the added code); no behavioural drift. Nothing
else diverged.

### 2026-11-12 — rework after review round 1 (tests only)

Commit: the one following 6eca700 (see `git log`). `run.py` and the other
source files are unchanged.

- Raising-tracer test: its script now starts with `HP_OK`, so a tool call is
  made, and the test asserts the case's tool was exercised.
- Same-calls test: now asserts the full call tuples (begin question;
  generation model, usage, text, tool names; tool name, arguments,
  result_count, error; finish answer; fail `RuntimeError: x`; check
  stage/allowed/reason) for a passing, an unknown-tool and a raising case.
- New `test_the_tracer_factory_gets_the_dotenv_merged_environment`
  (`main(env=None)`, a `.env` in `tmp_path`, `chdir`, env vars deleted).

Tests: pytest 491 -> 492 (one added; two rewritten).

Mutants (full pytest, restore by copy, tree clean after), all KILLED:
T-tool (no try/except around `secondary.tool`) by
`test_a_raising_tracer_changes_nothing`; A-begin, A-gen text, A-gen model,
A-gen usage, A-gen tool names, A-tool result_count, A-tool error, A-finish,
A-fail by `test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer`;
W01 (`tracer_factory(env, tags)`) by
`test_the_tracer_factory_gets_the_dotenv_merged_environment`.
A-check was not mutated (skeleton reason is always empty).
