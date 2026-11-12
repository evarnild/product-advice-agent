<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §12 review — Trace eval runs to Langfuse, tagged as evals

verdict: escalate
tier: reviewed
reviewed-commit: cfd48a3754a6cde43e2d799ff7489dc5eaafaaa5
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed, set by input 2 (`review_tier: reviewed` in `metadata.yml`).
Input 1 alone gives Attested (the round-2 delta is tests and `intents/`);
no HIGH or CRITICAL finding this round.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 12` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

All three round-1 HIGH findings are fixed with tests only (b88caf0); every
must-kill mutant is killed. No finding needs rework. `check:intent` FAILs
only on the owed live check (the owner's gate). The tier is Reviewed, so
the verdict is escalate: the owner reads the diff.

Scope: §12's own change is `git diff 1f45cd7..HEAD` (the branch is based on
§9's unmerged branch). The round-2 delta is `git diff cbda982..HEAD`:
b88caf0 (`tests/test_evals_run.py` +122/−45, and a Progress entry appended to
`plan.md`), 6eca700 (review) and cfd48a3 (metadata). `src/advisor/evals/run.py`
and every other source file are unchanged since round 1.

## Round-1 findings: resolution
| Round 1 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| HIGH | `try/except` around `self._secondary.tool(...)` unproven (T-tool) | fixed | `test_a_raising_tracer_changes_nothing` (`tests/test_evals_run.py:645`) scripts `HP_OK + [ModelError("boom")] + OFF_OK`, asserts the tool ran (`:657`), still compares with an untraced run; T-tool KILLED |
| HIGH | Langfuse-side arguments unchecked (A-begin, A-gen ×3, A-tool ×2, A-finish, A-fail) | fixed | `test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer` (`:555`) asserts full call tuples against literals from the script (distinct models, usages, texts per turn), the tool's `result_count` from the report, `error` `False`/`True`, `finish` equal to the report's answer, `("fail", "RuntimeError: x")`; all eight KILLED |
| HIGH | factory not proven to get the `.env`-merged env (W01) | fixed | `test_the_tracer_factory_gets_the_dotenv_merged_environment` (`:607`): `delenv` for the five names, `chdir(tmp_path)`, `tmp_path/.env`, `main(env=None, …)`; asserts the three `.env` values reach the factory and `tags[2] == "model:m-env"`; W01 KILLED |
| LOW | a raising `tracer_factory` ends the run (`run.py:290`) | open, carried | Worth a look |
| LOW | `advisor-eval` configures no logging; OTel warnings may reach stderr | open, carried | Worth a look during the live check |
| Nits | `CLAUDE.md:172` unwrapped; planned test name differs | open, carried | – |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (tests plus a Progress entry below the marker; exactly what round 1 asked) |
| 2 | Type check | FAIL on the owed live check only (the owner's gate, not rework) |
| 3 | Behaviour against the spec | pass (code unchanged; the proof for B1 `.env`, B6/B8 `tool()`, AC3 arguments is now in place) |
| 4 | Tests prove the behaviour | pass (all 10 must-kill mutants and A-gen tool names killed; A-check equivalent) |
| 5 | Conventions | pass (scripted fake client and fake tracer factory; conftest socket guard active) |
| 6 | Numbers in prose | pass ("491 → 492": +2/−1 `def test_`; the Progress mutant list matches) |
| 7 | Documentation | pass (README, CLAUDE.md not in the delta; passed in round 1) |
| 8 | Guardrails and hygiene | pass (placeholders only: `pk-dotenv`, `sk-dotenv`, `http://langfuse.invalid`; no dependency) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 12, feature)
  error: A live check is owed and not recorded. Do the steps in intents/12-trace-evals/review.md → ## Live check, then set live_checked: <date> in intents/12-trace-evals/metadata.yml.
  note:  30 file(s), 4639 line(s) changed outside intents/.
```
Exit 1, only on the owed live check. The count is against `main` and
includes §9's unmerged change; +34 lines since round 1 is the test delta.

## Findings
No new findings; nothing needs rework or a decision. Carried:
- **LOW** `src/advisor/evals/run.py:290`: `tracer_factory(full_env, tags)`
  runs outside the case `try` and the fan-out guard, so a raising factory
  ends the run. The default cannot realistically raise. Worth a look.
- **LOW** (behaviour): `advisor-eval` configures no logging, unlike
  `cli._configure_logging`; with Langfuse down, OpenTelemetry's "Failed to
  export span batch" may reach stderr. B6 covers stdout only. Worth a look
  during the live check.
- **Nits:** `CLAUDE.md:172` is one long line; the plan's
  `test_the_recording_tracer_still_feeds_scores_and_report` shipped as
  `test_the_recording_tracer_feeds_the_report_when_traced`; the `.env` test
  is sensitive to an invalid `ADVISOR_OLLAMA_URL` in the caller's shell.

Test soundness (reviewer): no network (scripted `Factory`, in-test
`TracerFactory`/`FakeTracer`, conftest guard); the `.env` test's cwd holds
its own `.env`, nearest wins, so no parent `.env` is picked; `delenv`/`chdir`
are undone by monkeypatch and `load_env` does not write `os.environ`; the
raising test compares with an untraced run and asserts the tool path ran;
expected tuples are literals or report values, never the fake against itself.

**Mutants** (`run.py` at cfd48a3; reviewer's harness outside the repo:
CRLF-aware replacement asserted once, bytes changed, `git diff --quiet`
non-zero, full pytest of 492, restore by copy; `git status --short` empty
and `git diff --quiet HEAD` exit 0 after):

| Mutant | Line | Result | Killing test |
| --- | --- | --- | --- |
| T-tool: try/except around `secondary.tool` removed | 143-146 | KILLED | test_a_raising_tracer_changes_nothing |
| A-begin: `begin("")` | 123 | KILLED | test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer |
| A-gen text `None` | 137 | KILLED | same |
| A-gen model `""` | 137 | KILLED | same |
| A-gen usage `Usage(0, 0)` | 137 | KILLED | same |
| A-gen tool_names `[]` (extra) | 137 | KILLED | same |
| A-tool result_count `0` | 144 | KILLED | same |
| A-tool error `False` | 144 | KILLED | same |
| A-finish `finish("")` | 151 | KILLED | same |
| A-fail `fail("")` | 158 | KILLED | same |
| A-check reason `""` | 130 | survived (equivalent with skeleton guardrails; optional) | – |
| W01 `tracer_factory(env, tags)` | 290 | KILLED | test_the_tracer_factory_gets_the_dotenv_merged_environment |

Survived: A-check (equivalent). Round 1's P-begin, P-finish, P-fail,
O-begin are equivalent and unchanged; round 1's other kills (M01-M07,
G01-G08, W02-W05, S-*, the other T-*) were not re-run: their code and tests
are unchanged.

## Not checked
- **The real Langfuse round trip:** traces arriving, the tags, the `eval`
  filter (the live check, rule 3).
- **The real cost of a down Langfuse:** the 5 s bound read from the code,
  not timed; nor a prompt process exit.
- **stderr from OTel/Langfuse loggers with Langfuse down** (LOW).
- **One Langfuse client per case** over a long run: not observable offline.
- **mypy and ruff on mutants:** only pytest decided the kills.
- **Round-1 mutants on unchanged code and tests:** not re-run.

## Live check
Owed by rule 3 (the real Langfuse path); rule 1 does not apply
(`tracing.py`, `cli.py`, `models/`, `prompts/`, `infra/` unchanged). In
Windows PowerShell, in `C:\Users\eric\src\product-advice-agent-wt\12-trace-evals`:

1. Start the local Langfuse: `docker compose -f
   infra/langfuse/docker-compose.yml up -d`, and wait until the UI opens at
   the root `.env`'s `LANGFUSE_HOST`. The root `.env` has the three
   `LANGFUSE_*` keys; Ollama runs with the default model (or set
   `ADVISOR_MODEL_PROVIDER` as you normally do).
2. Pick two case ids (`Get-Content evals\cases.jsonl -TotalCount 2`) and run
   `uv run advisor-eval --only <id1>,<id2>`. Note the PASS/FAIL lines,
   `$LASTEXITCODE` and the report path `evals\runs\<stamp>-<provider>.json`.
3. In Langfuse → Tracing, filter Tags on `eval`: exactly two new
   `advisor-run` traces, each with `eval`, `provider:<p>`, `model:<m>`,
   `run:<stamp>` (the report filename's stamp) and its own `case:<id>`.
   Open one: guardrail checks, model calls and tool calls are there.
4. `uv run advisor "I need noise-cancelling headphones under 200 euros."`:
   its trace has only `provider:` and `model:` tags and does not show under
   the `eval` filter.
5. Stop Langfuse (`docker compose -f infra/langfuse/docker-compose.yml
   stop`), then `Measure-Command { uv run advisor-eval --only <id1>,<id2> |
   Out-Host }`: the same PASS/FAIL lines and exit code as step 2 (model
   nondeterminism aside), at most about 10 s slower, and a prompt exit after
   the report line. Note any OpenTelemetry or Langfuse warnings on stderr.
6. Restart Langfuse if you use it: `docker compose -f
   infra/langfuse/docker-compose.yml start`.

You should see: two eval traces filterable by `eval` and `run:<stamp>`,
with case tags matching the report; the ordinary advisor trace without
`eval`; with Langfuse down, unchanged stdout and exit code with a bounded
delay.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/12-trace-evals` at cfd48a3; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; ruff "All checks
  passed!"; "117 files already formatted"; mypy "Success: no issues found
  in 26 source files"; pytest "492 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL on the owed live
  check only, "30 file(s), 4639 line(s)". Matches.
- **Coordinator, re-run:** every mutant the round's resolutions say is now
  killed, and the one survivor, with my own harness (backup by copy,
  replacement asserted once, CRLF-aware, full pytest, restore by copy):
  T-tool KILLED by test_a_raising_tracer_changes_nothing; A-begin, A-gen
  text, A-gen model, A-gen usage, A-tool result_count, A-tool error,
  A-finish, A-fail KILLED by
  test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer; W01
  KILLED by test_the_tracer_factory_gets_the_dotenv_merged_environment;
  A-check SURVIVED ("492 passed"). Each kill "1 failed, 491 passed".
  Matches the reviewer and the implementer.

**Reviewer, verified:**
- HEAD cfd48a3 on `feat/12-trace-evals`; `git diff cbda982..HEAD` touches
  only `tests/test_evals_run.py`, `plan.md`, `metadata.yml`, `review.md`,
  read in full.
- `npm run verify` (kit 255/255, 492 passed); `npm run check:intent` (FAIL,
  live check only); the sampling line.
- 491 + 1 = 492 from the `def test_` delta.
- 12 mutants as tabled.
- Not merged into `main`; nothing pushed (`git ls-remote --heads origin`
  has no `12` branch).
- Read for soundness: `config.load_env` (`find_dotenv(usecwd=True)`), the
  conftest socket guard, `FakeTracer`/`TracerFactory`.

**Taken on trust:**
- §9's content up to 1f45cd7, as reviewed in §9's rounds.
- Round 1's kills for mutants whose code and tests are unchanged.
- Runtime behaviour against a real Langfuse (the live check).

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: cbda9824ec6efe80d8a1c53948a57068b6cddc03
- round: 1
- sampled: no
- run: auto
- live-check: owed

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

### Passes
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

### Type check
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

### Behaviour against the spec (code at HEAD)
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

### Findings
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

### Not checked
- **The real Langfuse round trip:** traces arriving, the tags in the Tracing
  table, the `eval` filter (the live check, rule 3).
- **The real cost of a down Langfuse:** the 5 s bound is read from the code,
  not timed; nor whether the process exits promptly after the total line
  (the Langfuse/OTel shutdown runs at interpreter exit).
- **stderr from OpenTelemetry/Langfuse loggers with Langfuse down** (LOW 5).
- **A Langfuse client per case** over a 15- or 60-case run (connection
  reuse, the SDK's per-key singleton): not observable offline.
- **mypy and ruff on mutants:** only pytest decided the kills.

### Live check
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

### Verified myself vs. taken on trust

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
