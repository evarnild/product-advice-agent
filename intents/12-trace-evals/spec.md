<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §12 spec — Trace eval runs to Langfuse, tagged as evals

Accepted intent: [intent.md](intent.md)
Written against `main` at `0adf87b`, and against `src/advisor/evals/run.py`
on `feat/9-error-analysis` at `2421d9e` (the branch §12 builds on, per the
intent's first constraint).

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Owner's decisions

| Question | Owner's answer | When |
| --- | --- | --- |
| When eval runs are traced | **Always, when configured**: like `uv run advisor`, whenever the three `LANGFUSE_*` variables are set; no `--trace` flag | intent round, 2026-11-12 |
| What each trace carries | **`eval` + run + case**: the `eval` tag, the CLI's `provider:` and `model:` tags, the run's timestamp and the case id | intent round |
| Relation to §10 | **Separate, before §10**: only tagged eval traces; §10 adds tool results, dimensions and queues | intent round |
| Branch | **Built on §9's branch until §9 merges** ("we can run it until the merge") | 2026-11-12 |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/12-trace-evals/intent.md` | Outcome: one trace per case when configured, tagged so eval traces are told apart; "Tracing never changes a run"; tests without a network; the live check is the real round trip. Constraints: `langfuse` only in `tracing.py`; the recording tracer stays; self-hosted only; §10's work out of scope. |
| `intents/8-offline-evals/spec.md` B11 | "The suite does not trace to Langfuse: it uses its own recording tracer, not `make_tracer`. It imports no provider SDK and not `langfuse`." Superseded by this spec (B9). |
| `src/advisor/tracing.py:128-142` | `make_tracer(env, tags=())`: "A Langfuse tracer when all three variables are set, otherwise a no-op"; `REQUIRED_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")`; returns `SafeTracer(LangfuseTracer(client, tags))`. |
| `src/advisor/tracing.py:39-47` | `begin` starts the root span `advisor-run` with the question as input and sets the tags as the `langfuse.trace.tags` attribute. |
| `src/advisor/tracing.py:86-94` | `_close` ends the root span and flushes on a daemon thread, joined for at most `FLUSH_TIMEOUT_SECONDS = 5.0`. `finish` and `fail` both call it. |
| `src/advisor/tracing.py:97-125` | `SafeTracer` swallows every exception of the inner tracer. |
| `src/advisor/cli.py:106-107` | `tags = [f"provider:{settings.provider}", f"model:{settings.model}"]`; `tracer = make_tracer(full_env, tags)`: one tracer per question. |
| `src/advisor/agent.py:180-198` | `answer_question` calls `tracer.begin(question)`, `check("input", …)`, the turns and tools, `check("output", …)`, then `finish(answer)`; on an exception `fail(...)`; on an input block `finish(REFUSAL_TEXT)`. |
| `src/advisor/evals/run.py` (§9 branch) | Docstring: "It uses its own recording tracer and never imports `advisor.tracing`, so an eval run does not reach Langfuse." One `RecordingTracer` per case, passed to `answer_question`; `settings = load_settings(load_env(env))`; the report file is `<stamp>-<provider>.json` with `stamp = started.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")`. |
| `tests/test_boundaries.py::test_eval_runner_loads_no_sdk` | A fresh interpreter importing `advisor.evals.run` must not load `langfuse`, `opentelemetry`, `anthropic`, `httpx` or `advisor.tracing`. |
| `README.md` ("Evaluating answers", §9 branch line 127) | "It reads the same environment and `.env` as `advisor` and does not trace to Langfuse." |
| `README.md` ("Tracing is on only when…") | "Every trace is tagged `provider:<name>` and `model:<name>`." |
| `CLAUDE.md` ("Offline evals") | "`run.py` is the I/O … with its own recording tracer. It imports neither `advisor.tracing` nor a provider SDK." |

## Behaviour

**When tracing is on**

- **B1.** `uv run advisor-eval` traces when `LANGFUSE_HOST`,
  `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are all non-empty in the
  environment it already reads (`load_env`: the real environment over the
  nearest `.env`). Otherwise it traces nothing, as today. The rule is
  `make_tracer`'s; the runner does not restate it with different logic.
- **B2.** With tracing on, each case that reaches `answer_question` is one
  Langfuse trace, recorded by the existing Langfuse tracer: the same root
  span (`advisor-run`, the question as input, the answer as output) and the
  same child observations (guardrail checks, model calls, tool calls) as a
  `uv run advisor` run. A case whose `answer_question` raises gives a trace
  closed by `fail`, as in the CLI.
- **B3.** Nothing is traced for the run as a whole, and nothing before the
  first case: a run that stops before the cases (bad case file, unknown
  `--only` id, missing key, unreachable Ollama on the first case) sends
  only what `answer_question` already sent for that first case.

**Tags**

- **B4.** Every eval trace carries exactly these tags, in this order:
  1. `eval`;
  2. `provider:<provider>` and `model:<model>`, the values the run uses
     after `--provider` and `--model` (§11), the same text as the total
     line prints;
  3. `run:<stamp>`, where `<stamp>` is the run's start in the report
     filename's format (`%Y%m%dT%H%M%SZ`, UTC), so a trace's run tag names
     its report file `evals/runs/<stamp>-<provider>.json`;
  4. `case:<case id>`.
- **B5.** `uv run advisor` traces are unchanged: they carry `provider:` and
  `model:` only, never `eval`, `run:` or `case:`.

**Tracing never changes a run**

- **B6.** The scores, the stdout lines, the exit code and the report's
  contents are the same with tracing on, off, or failing (Langfuse down,
  keys refused, any exception inside the tracer), except `duration_s`, which
  includes the trace's flush (B7).
- **B7.** A case's flush waits at most `FLUSH_TIMEOUT_SECONDS` (5 s), as in
  the CLI. With tracing configured and Langfuse down, a run may take up to
  5 s longer per case. No retry, no shorter timeout and no
  stop-after-first-timeout is added (Assumption A1).
- **B8.** The recording tracer still receives every event it receives today,
  in the same order, so the scorers, `searches`, `turns`, `tools` and
  `guardrails` in the report are unchanged. The Langfuse tracer receives the
  same events. A failure in the Langfuse tracer never reaches the recording
  tracer or the run.

**Boundaries and documentation**

- **B9.** Importing `advisor.evals.run` still loads none of `langfuse`,
  `opentelemetry`, `anthropic`, `httpx` or `advisor.tracing`
  (`test_eval_runner_loads_no_sdk` stays as it is). `advisor.tracing` is
  loaded only when a run starts with the three variables set; a run without
  them loads neither `advisor.tracing` nor `langfuse`.
- **B10.** `langfuse` is still imported only in `tracing.py`;
  `tracing.py`'s behaviour is unchanged for the CLI (tags passed at
  construction, one tracer per question).
- **B11.** The documentation says eval runs are traced:
  - `README.md` "Evaluating answers": "does not trace to Langfuse" becomes
    the rule of B1, the tags of B4, and how to filter on them (tag `eval`,
    then `run:<stamp>` from the report filename);
  - `README.md` "Tracing is on only when…": eval traces also carry `eval`,
    `run:` and `case:`;
  - `CLAUDE.md` "Offline evals": the runner loads `advisor.tracing` only
    when tracing is configured;
  - `run.py`'s module docstring;
  - `intents/8-offline-evals/spec.md` B11 gets one line: "Superseded by
    §12: eval runs are traced when Langfuse is configured." Nothing else in
    §8's spec changes.

## Interpretations

- **"a tag saying it is an eval"** (owner): the literal tag `eval`, lower
  case, like the existing `provider:`/`model:` tags. It has no value part:
  it is the marker, and `run:` and `case:` carry the values.
- **"run" and "case" as tags** (owner's choice, intent question 1): tags,
  not metadata or a Langfuse session. Tags need no change to `tracing.py`
  (`make_tracer` takes them) and the Tracing table filters on them. A
  session per run would also group the traces, but needs `tracing.py` to set
  `session.id`; left out (Out of scope).
- **The run's timestamp** (owner: "the run's timestamp"): the same `stamp`
  the report filename uses, so a trace and its report file are matched by
  text, with no new id.
- **"Tracing never changes a run"** (`CLAUDE.md`, intent Outcome): read as
  B6. `duration_s` is the one field that can differ, because `finish`
  flushes inside `answer_question`, inside the timed span. Excluding the
  flush would need a change to `answer_question` or `tracing.py`; the
  difference is bounded (B7) and named here instead.
- **§8 B11 superseded**: a shipped spec is history; one line points at §12
  rather than rewriting it.

## Acceptance criteria

- **AC1** (B1, B9): with the three variables set, the runner builds a
  Langfuse tracer per case; with any one missing or empty, it builds none
  and `advisor.tracing` is not loaded. *Proof:* tests in
  `tests/test_evals_run.py` with a faked tracer factory (no network); a
  subprocess test that runs a case with the fake model and no `LANGFUSE_*`
  and checks `sys.modules` for `advisor.tracing` and `langfuse`.
- **AC2** (B4): each case's tracer receives exactly `["eval",
  "provider:<p>", "model:<m>", "run:<stamp>", "case:<id>"]`, with
  `<stamp>` equal to the report filename's, including after `--provider`
  and `--model`. *Proof:* `tests/test_evals_run.py`, a fixed clock.
- **AC3** (B2, B8): the Langfuse-side tracer receives the same sequence of
  calls as the recording tracer (begin, checks, generations, tools, finish
  or fail), for a passing case, an unknown-tool case and a raising case.
  *Proof:* `tests/test_evals_run.py` with a recording fake in place of the
  Langfuse tracer.
- **AC4** (B6, B8): a Langfuse-side tracer that raises on every call
  changes nothing: same stdout, exit code and report (ignoring
  `duration_s`) as a run with tracing off. *Proof:* `tests/test_evals_run.py`,
  a raising fake wrapped as the runner wraps the real one.
- **AC5** (B5, B10): `uv run advisor`'s tags are unchanged, and `langfuse`
  is imported only in `tracing.py`. *Proof:* the existing
  `tests/test_tracing.py` tag tests and `tests/test_boundaries.py`, green
  and unedited.
- **AC6** (B9): `test_eval_runner_loads_no_sdk` passes unedited. *Proof:*
  `tests/test_boundaries.py`.
- **AC7** (B11): the README, `CLAUDE.md`, `run.py` docstring and §8's B11
  line say what B11 lists. *Proof:* reviewer reading.
- **AC8** (B1-B4, B7, live check): with the local Langfuse up and its keys
  in `.env`, `uv run advisor-eval --only <two case ids>` gives two traces
  in the Langfuse Tracing table; filtering on tag `eval` shows them and no
  `uv run advisor` trace; each has `run:<stamp>` matching the report file
  and its own `case:<id>`; then one `uv run advisor "<question>"` shows
  without `eval`. With Langfuse stopped, the same eval command still
  finishes with the same PASS/FAIL lines, at most about 5 s slower per
  case. *Proof:* the owner's live check.

## Non-functional

- **Boundaries:** the wiring is in `src/advisor/evals/run.py` (I/O). It
  reaches Langfuse only through `make_tracer` in `tracing.py`, loaded
  lazily. `tracing.py` and `agent.py` are not changed (B10). The pure
  modules (`agent`, `catalogue`, `evals.cases`, `evals.score`, §9's pure
  modules) load no SDK.
- **Data:** the traces carry what `uv run advisor` traces already carry:
  the question, the answer, tool arguments, model text, tool names and
  token usage. Eval questions are synthetic (`evals/cases.jsonl`, §9's
  generated questions), and so is the catalogue. They go only to the
  self-hosted Langfuse in `infra/langfuse/`. The tags add the case id and a
  timestamp; no personal data.
- **Model use:** none added. The same calls, traced.
- **Autonomy:** nothing new: the runner sends traces and never reads,
  changes or deletes anything in Langfuse.
- **Cost and latency:** no money. Up to 5 s per case when tracing is
  configured and Langfuse is down (B7).
- **Live check:** owed by `REVIEW-POLICY.md` rule 3 (the real Langfuse path
  is not covered by the suite), not by rule 1 (`tracing.py` is unchanged).
  The steps are AC8.

## Out of scope

- Tool results, §9 dimensions as tags or metadata, score configs, annotation
  queues and label import (§10).
- A Langfuse session per run, trace metadata, a different trace name, or the
  trace id in the run report.
- A `--no-trace` flag (the owner chose "always, when configured"; unset the
  variables to run untraced).
- Sending §8's check results or §9's labels to Langfuse as scores; Langfuse
  datasets and experiments.
- Changing `tracing.py`, `agent.py`, `cli.py` or `infra/langfuse/`.

## Assumptions I made

- **A1. A down Langfuse costs up to 5 s per case, accepted.** The intent's
  question 3 offered a shorter wait, one flush at the end, or giving up
  after the first timeout. Each needs `tracing.py` to change (its flush is
  per trace and its outcome is swallowed), which would also make the live
  check owed by rule 1 and widen the change. Tracing is on only when the
  owner has put the keys in `.env`, which means the stack is normally up.
  If you want a faster failure, say so at this stop: it becomes a B that
  changes `tracing.py`.
- **A2. No line on stdout or stderr says tracing is on** (intent question
  6): B6 keeps stdout identical, and the CLI prints nothing about tracing
  either. `advisor-eval` configures no logging today, so `make_tracer`'s
  debug lines stay silent, also with `--debug` (which shows tracebacks
  only).
- **A3. The run report gets no trace id** (intent question 4): `run:` and
  `case:` match a trace to its report line; §10 can add the id if its
  queue matching needs one.
- **A4. One tracer per case**, built with that case's tags (intent question
  5), as the CLI builds one per question; `tracing.py` is unchanged.
- **A5. The recording tracer and the Langfuse tracer are combined in
  `run.py`** (intent question 2), by a small fan-out that calls both, the
  recording one first; the `Tracer` protocol is unchanged. How exactly is
  the plan's.
- **A6. The tag order of B4** is fixed so tests can compare lists; Langfuse
  does not depend on it.
