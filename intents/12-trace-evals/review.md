<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §12 review — Trace eval runs to Langfuse, tagged as evals

verdict: rework
tier: reviewed
reviewed-commit: cbda9824ec6efe80d8a1c53948a57068b6cddc03
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, set by input 2 (`review_tier: reviewed` in `metadata.yml`);
input 3 confirms it (HIGH findings). Input 1 (paths) alone gives Attested:
the delta touches `src/advisor/evals/run.py`, tests, `README.md`,
`CLAUDE.md` and `intents/`, no by-meaning path.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 12` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Scope: §12's own change, `git diff 1f45cd7..HEAD`. The branch is based on
§9's unmerged branch (intent constraint "Built on §9's branch until §9
merges"); `1f45cd7` is an ancestor of `feat/9-error-analysis`, and differs
from §9's current head only in `intents/9-error-analysis/metadata.yml`.
§9's content is reviewed in §9's own report.

The code does what the spec says. Three HIGH findings are gaps in the
proof: a guard, the forwarded arguments, and the `.env` path are not tested,
and 11 non-equivalent mutants survive. All three are mechanical: the spec
and the plan's Tests table determine the fix.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | pass (PASS against `main`, which counts §9's files too; see below) |
| 3 | Behaviour against the spec | pass in the code; the proof for B1 (`.env`), B6/B8 (`tool`) and AC3 (arguments) is missing (pass 4) |
| 4 | Tests prove the behaviour | findings (3 HIGH) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (491 = 481 + 10 new `def test_`; "up to 5 s per case" matches `FLUSH_TIMEOUT_SECONDS = 5.0`, `tracing.py:21`, joined at `:94`) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (no dependency; no secret) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 12, feature)
  note:  30 file(s), 4605 line(s) changed outside intents/.
```
Exit 0. `check:intent` measures against `main`, so the 30 files and 4605
lines are mostly §9's; §12's own delta is 6 files outside
`intents/12-trace-evals/`. It shows PASS because no `review.md` existed
yet; with this report's `live-check: owed` it FAILs until the owner records
`live_checked` (the owner's gate, not rework).

## Behaviour against the spec (code at HEAD)
- **B1.** `_default_tracer_factory` (`run.py:50-57`): `NoopTracer()` unless
  `all(env.get(k) for k in _LANGFUSE_ENV)`; otherwise a lazy `from
  advisor.tracing import make_tracer` and `make_tracer(env, tags)`. The
  factory gets `full_env = load_env(env)` (`run.py:247`, `:290`). The
  reviewer's probe outside the repo confirms `.env` keys reach the factory
  with `env=None`.
- **B2, B3.** One factory call per case, inside the loop (`run.py:290`);
  nothing before the first case; `fail` forwarded.
- **B4.** Tags `["eval", f"provider:{…}", f"model:{…}", f"run:{stamp}",
  f"case:{case.id}"]` (`run.py:283-289`), after the `--provider`/`--model`
  overrides; `stamp` from `started` once (`run.py:277`), reused for the
  report filename (`:338`); no extra `now()`.
- **B5, B10.** `git diff 1f45cd7..HEAD -- src/advisor/tracing.py
  src/advisor/agent.py src/advisor/cli.py src/advisor/tracer.py` is empty;
  `test_eval_runner_loads_no_sdk` unedited.
- **B6, B8.** Each `_FanOutTracer` method (`run.py:109-160`) calls the
  primary first, unguarded, then the secondary in `try/except Exception:
  pass`; `_recording_tool` gets the `RecordingTracer` (`run.py:295`);
  scoring and `_record` read it.
- **B9.** No module-level `advisor.tracing` import (only `run.py:55`);
  `NoopTracer`, `Tracer` from `advisor.tracer`.
- **B11.** README 46-47 and 127-135, `CLAUDE.md:172`, the `run.py`
  docstring (5-8), §8 spec B11 (one appended line).

## Findings
- **HIGH** `tests/test_evals_run.py:612-625`: the `try/except` around
  `self._secondary.tool(...)` (`run.py:143-146`) is unproven; mutant T-tool
  survives. `test_a_raising_tracer_changes_nothing` scripts `HP_BAD +
  [ModelError("boom")] + OFF_OK`, and no turn calls a tool. Without the
  guard a raising `tool()` ends the case as `ERROR … unexpected
  RuntimeError` (B6, B8, AC4). **Needs rework:** give the raising test's
  script a tool call (e.g. `HP_OK` for case hp, or the unknown-tool turns),
  keep comparing with the untraced run, and confirm T-tool is killed.
- **HIGH** `tests/test_evals_run.py:555-609`: AC3/B8 say the Langfuse side
  receives "the same events", but the test compares only method names and
  some arguments (`begin` first, `finish`/`fail` last, `check` tuples,
  `tool` name and arguments, generation `tool_names`). Never checked:
  `begin`'s question; the generation's model, usage, text; the tool's
  `result_count` and `error`; `finish`'s answer; `fail`'s error. Eight
  argument mutants survive. **Needs rework:** assert the full call tuples
  against values known in the test: `("begin", question)`; generation
  `(model, usage, text, tool_names)` from the scripted turns or the fake
  client; `("tool", name, args, len(results), error)` from
  `recording.tools`; `("finish", the report's answer)`; `("fail",
  "RuntimeError: x")`. (A-check, the guardrail `reason`, is equivalent with
  the skeleton guardrails, whose reason is always `""`, `guardrails.py:20`;
  killing it needs a patched `check_input` and is optional.)
- **HIGH** `src/advisor/evals/run.py:290`: nothing proves the factory
  receives the `.env`-merged environment; mutant W01 (`tracer_factory(env,
  tags)`) survives. Every test passes an explicit `env`, for which
  `load_env` returns a copy. In production `advisor-eval` calls `main()`
  with `env=None`, and W01 crashes the run (`AttributeError: 'NoneType'
  object has no attribute 'get'`, outside the case `try`); a non-crashing
  variant would ignore keys that live only in `.env`, the set-up README and
  the live check describe (B1). **Needs rework:** a test with
  `monkeypatch.chdir(tmp_path)`, a `tmp_path/.env` holding the three
  `LANGFUSE_*` placeholders (plus `ADVISOR_MODEL_PROVIDER`/`ADVISOR_MODEL`),
  `monkeypatch.delenv` for those names, `main(..., env=None,
  tracer_factory=recording_factory)`, asserting the factory's env holds the
  `.env` values.
- **LOW** `src/advisor/evals/run.py:290`: `tracer_factory(full_env, tags)`
  runs outside the case `try` and the fan-out's guard, so a raising factory
  ends the run. The default cannot realistically raise (`make_tracer`
  catches client construction errors). Worth a look.
- **LOW** (behaviour): `advisor-eval` configures no logging, unlike the CLI
  (`cli._configure_logging` gives the root logger a `NullHandler`, proven by
  `tests/test_cli_stderr.py`). With Langfuse down, OpenTelemetry's "Failed
  to export span batch" may reach stderr through Python's last-resort
  handler. B6 covers stdout only, so not a spec deviation; not observable
  offline. Worth a look during the live check.
- **Nits:** `CLAUDE.md:172` is one long unwrapped line; the plan's
  `test_the_recording_tracer_still_feeds_scores_and_report` shipped as
  `test_the_recording_tracer_feeds_the_report_when_traced`.

**Mutants** (`run.py` at HEAD; reviewer's harness outside the repo: one
replacement asserted applied, full pytest of 491 tests, restore by copy;
`git status --short` and `git diff --quiet HEAD` clean after; 48 mutants):

| Mutant | Line | Result | Killing test(s) |
| --- | --- | --- | --- |
| M01 `all` → `any` | 52 | KILLED | test_default_factory_is_noop_without_all_three_variables |
| M02 `env.get(k)` → `k in env` | 52 | KILLED | same |
| M03 guard removed | 52-53 | KILLED | same; test_an_untraced_eval_run_loads_neither_tracing_nor_langfuse |
| M04 eager `import advisor.tracing` | 37/55 | KILLED | test_eval_runner_loads_no_sdk (+2) |
| M05 `make_tracer(env, ())` | 57 | KILLED | test_default_factory_calls_make_tracer_with_env_and_tags_when_configured |
| M06 `make_tracer({}, tags)` | 57 | KILLED | same |
| M07 HOST dropped from `_LANGFUSE_ENV` | 45 | KILLED | test_eval_runner_langfuse_variables_match_the_tracing_module |
| P-begin, P-finish, P-fail (primary call removed) | 121, 149, 156 | survived (equivalent: no-ops in `RecordingTracer`) | – |
| P-check / P-generation / P-tool | 128 / 135 / 142 | KILLED | test_the_langfuse_side_… (+1) / 5 tests / 18 tests |
| S-* (each secondary call removed, 6) | 123-158 | KILLED | test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer |
| T-begin, T-check, T-generation, T-finish, T-fail (try/except removed) | 122-160 | KILLED | test_a_raising_tracer_changes_nothing |
| **T-tool** (try/except removed) | 143-146 | **SURVIVED** | – (HIGH 1) |
| **A-begin** secondary gets `""` | 123 | **SURVIVED** | – (HIGH 2) |
| A-check reason `""` | 130 | survived (equivalent with skeleton guardrails) | – |
| **A-gen** text None / model `""` / usage zero | 137 | **SURVIVED** (3) | – (HIGH 2) |
| **A-tool** result_count 0 / error False | 144 | **SURVIVED** (2) | – (HIGH 2) |
| **A-finish** answer `""` | 151 | **SURVIVED** | – (HIGH 2) |
| **A-fail** error `""` | 158 | **SURVIVED** | – (HIGH 2) |
| O-begin secondary first (still guarded) | 121-125 | survived (equivalent) | – |
| G01 `"eval"` dropped | 284 | KILLED | test_each_case_gets_a_tracer_with_eval_run_and_case_tags (+2) |
| G02 provider/model swapped | 285-286 | KILLED | test_each_case_…, test_trace_tags_follow_the_provider_and_model_flags |
| G03 / G04 provider / model from env settings | 285 / 286 | KILLED | test_trace_tags_follow_the_provider_and_model_flags |
| G05 run tag `started.isoformat()` | 287 | KILLED | 3 tag tests |
| G06 case tag always the first case | 288 | KILLED | test_each_case_gets_a_tracer_with_eval_run_and_case_tags |
| G07 case tag dropped | 288 | KILLED | 2 tag tests |
| G08 stamp from an extra `now()` | 277 | KILLED | test_run_tag_matches_the_report_file_name |
| **W01** `tracer_factory(env, …)` | 290 | **SURVIVED** | – (HIGH 3) |
| W02 factory not called | 290 | KILLED | 4 tests |
| W03 fan-out bypassed | 295 | KILLED | test_the_langfuse_side_… |
| W04 `_recording_tool` gets the fan-out | 295 | KILLED | 4 tests |
| W05 fan-out wraps a fresh `RecordingTracer` | 290 | KILLED | 18 tests |

The rework must kill: T-tool; A-begin; A-gen text, model, usage; A-tool
result_count, error; A-finish; A-fail; W01. A-check is optional. P-begin,
P-finish, P-fail and O-begin are equivalent.

## Not checked
- **The real Langfuse round trip:** traces arriving, the tags in the Tracing
  table, the `eval` filter (the live check, rule 3).
- **The real cost of a down Langfuse:** the 5 s bound is read from the code,
  not timed; nor whether the process exits promptly after the total line
  (the Langfuse/OTel shutdown runs at interpreter exit).
- **stderr from OpenTelemetry/Langfuse loggers with Langfuse down** (LOW 5).
- **A Langfuse client per case** over a 15- or 60-case run (connection
  reuse, the SDK's per-key singleton): not observable offline.
- **mypy and ruff on mutants:** only pytest decided the kills.

## Live check
Owed by rule 3 (the real Langfuse path); rule 1 does not apply
(`tracing.py`, `cli.py`, `models/`, `prompts/`, `infra/` unchanged). In
Windows PowerShell, in `C:\Users\eric\src\product-advice-agent-wt\12-trace-evals`
(or wherever the branch is checked out):

1. Start the local Langfuse: `docker compose -f
   infra/langfuse/docker-compose.yml up -d`, and wait until the UI opens at
   the root `.env`'s `LANGFUSE_HOST` (e.g. http://localhost:3000). The root
   `.env` has `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY` and
   `LANGFUSE_SECRET_KEY`; Ollama runs with the default model (or set
   `ADVISOR_MODEL_PROVIDER` as you normally do).
2. Pick two case ids (`Get-Content evals\cases.jsonl -TotalCount 2`) and run
   `uv run advisor-eval --only <id1>,<id2>`. Note the PASS/FAIL lines,
   `$LASTEXITCODE`, and the report path `evals\runs\<stamp>-<provider>.json`.
3. In Langfuse → Tracing, filter Tags on `eval`: exactly two new
   `advisor-run` traces, each with `eval`, `provider:<p>`, `model:<m>`,
   `run:<stamp>` (the report filename's stamp) and its own `case:<id>`.
   Open one: guardrail checks, model calls and tool calls are there as for
   a normal `advisor` run.
4. `uv run advisor "I need noise-cancelling headphones under 200 euros."`:
   its trace has only `provider:` and `model:` tags and does not show under
   the `eval` filter.
5. Stop Langfuse (`docker compose -f infra/langfuse/docker-compose.yml
   stop`), then `Measure-Command { uv run advisor-eval --only <id1>,<id2> |
   Out-Host }`: the same PASS/FAIL lines and exit code as step 2 (model
   nondeterminism aside), at most about 10 s slower for two cases, and the
   process exits right after the report line. Note any OpenTelemetry or
   Langfuse warnings on stderr (LOW 5).
6. Restart Langfuse if you use it: `docker compose -f
   infra/langfuse/docker-compose.yml start`.

You should see: two eval traces filterable by `eval` and `run:<stamp>`,
with case tags matching the report; the ordinary advisor trace without
`eval`; with Langfuse down, unchanged stdout and exit code with a bounded
delay.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/12-trace-evals` at cbda982; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; ruff "All checks
  passed!"; "116 files already formatted"; mypy "Success: no issues found
  in 26 source files"; pytest "491 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "30 file(s),
  4605 line(s)". Matches.
- **Coordinator, re-run:** every mutant the review lists as surviving, with
  my own harness (backup by copy, replacement asserted once, CRLF-aware,
  full pytest, restore by copy): T-tool, A-begin, A-gen text, A-gen model,
  A-gen usage, A-tool result_count, A-tool error, A-finish, A-fail, A-check,
  W01, P-begin, P-finish, P-fail all SURVIVED with "491 passed". Matches the
  reviewer. O-begin not re-run (equivalent by reading: the primary never
  raises and `begin` is a no-op).
- **Coordinator:** the implementer's mutant list (15 rows, all killed) is
  consistent with the reviewer's table; the survivors are outside it.

**Reviewer, verified:**
- HEAD cbda982 on `feat/12-trace-evals`; `1f45cd7` an ancestor of
  `feat/9-error-analysis`, differing only in §9's `metadata.yml`.
- `git diff 1f45cd7..HEAD` read line by line; the unedited-files check.
- `npm run verify` (kit 255/255, 491 passed); `npm run check:intent`
  (PASS).
- 491 = 481 + 10 by counting `def test_` in the diff (no parametrize).
- 48 mutants as tabled; `git status --short` empty after.
- A probe outside the repo (worktree venv, `-I`, a scratch dir with a
  placeholder `.env`): `main(env=None, tracer_factory=recording)` → rc 0,
  the factory received the three `.env` values and tags `['eval',
  'provider:ollama', 'model:m', 'run:20261112T181940Z', 'case:lap']`;
  `_default_tracer_factory(None, …)` raises `AttributeError`. No real
  Langfuse client, no network.
- Nothing pushed (`git ls-remote --heads origin` has no `12-trace`).

**Taken on trust:**
- §9's content up to 1f45cd7, as reviewed in §9's three rounds.
- The implementer's statement that each plan Tests-table row was
  mutation-checked (the reviewer ran its own set instead).
- Runtime behaviour against a real Langfuse (the live check).
