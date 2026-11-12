<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §12 — Trace eval runs to Langfuse, tagged as evals

**Type:** feature
**Originator:** the owner, 2026-11-12: "I would like to trace the evals,
adding a tag saying it is an eval"
**Source:** `intents/8-offline-evals/spec.md` B11 and its note "No Langfuse
tracing during evals … A later intent could add it";
`intents/10-langfuse-annotation/intent.md` (assumes eval traces exist)

## Problem

`uv run advisor-eval` never reaches Langfuse. §8 decided this on purpose
(spec B11: "The suite does not trace to Langfuse: it uses its own recording
tracer, not `make_tracer`"), and `src/advisor/evals/run.py` says so in its
docstring: "It uses its own recording tracer and never imports
`advisor.tracing`, so an eval run does not reach Langfuse."
`tests/test_boundaries.py::test_eval_runner_loads_no_sdk` enforces it.

So when an eval case fails, the owner can read the run report (and, after
§9, the viewer), but cannot open the run in Langfuse next to the advisor's
other traces: the model turns, the tool calls, the guardrail checks and the
timing are not there. §10 (labelling in Langfuse annotation queues) assumes
eval traces exist and cannot start without them. And once eval traffic does
reach Langfuse, it must not be confused with ordinary `uv run advisor` runs.

## Outcome

- **Eval runs are traced whenever Langfuse is configured.** With the three
  `LANGFUSE_*` variables set (the same rule as `uv run advisor`),
  `uv run advisor-eval` sends one trace per case to the self-hosted
  Langfuse. Without them, nothing is sent and the run behaves as today.
- **Each eval trace is tagged so it can be found and told apart:**
  - `eval`, which no `uv run advisor` trace carries;
  - `provider:<p>` and `model:<m>`, as `cli.py` already tags;
  - the run (the report's timestamp, so the traces of one run filter
    together) and the case id, so a trace matches its line in the run
    report.

  In the Langfuse Tracing table, filtering on the `eval` tag shows exactly
  one run's cases, or several runs, and no ordinary advisor runs.
- **Tracing never changes a run.** Scores, the stdout lines, the exit code
  and the JSON report are the same with tracing on or off, and with a
  Langfuse that is down or refuses the keys (beyond what the spec settles
  for the report, e.g. a trace id).
- **Tests without a network.** `npm run verify` covers the tags, the
  on/off rule and "a failing tracer changes nothing", with a faked tracer
  factory. The real round trip (a run, then the traces filtered by `eval`
  in the Langfuse UI) is the live check.

## Constraints

- **Built on §9's branch until §9 merges** (owner, 2026-11-12: "we can
  run it until the merge"). `run.py`'s `RecordingTracer` and the tool
  wrapper change in §9 (`feat/9-error-analysis`), so §12's branch starts
  from §9's branch, not from `main`, and is rebased onto `main` once §9 is
  merged. §12 merges only after §9; if §9's last round reworks `run.py`,
  §12 rebases onto it. §10 then builds on this (tool results, dimensions,
  queues); this intent does none of §10's work.
- **Architecture (`CLAUDE.md`).** `langfuse` is imported only in
  `tracing.py`. The eval suite keeps its recording tracer, which the
  scorers read; the Langfuse tracer is added alongside it, not instead.
  The pure modules still load no `langfuse` or `opentelemetry`.
  `test_eval_runner_loads_no_sdk` changes to match the new rule (the spec
  says how: for example, `advisor.tracing` is loaded only when tracing is
  configured). `CLAUDE.md`'s "Offline evals" paragraph and §8's B11 are
  superseded and are updated to say so.
- **"Tracing never changes a run"**: every Langfuse call stays wrapped and
  swallowed (`SafeTracer`), and the flush stays bounded.
- **Data.** Eval questions are synthetic (`evals/cases.jsonl`, §9's
  generated questions) and the catalogue is synthetic. The traces carry what
  `uv run advisor` already sends; no new kind of data goes to Langfuse.
- **Self-hosted only**: the local stack in `infra/langfuse/` with the
  existing keys. No Langfuse Cloud and no new secret.
- **Cost.** No extra model calls; the same run, traced.
- **Live check owed** if `tracing.py` changes (`REVIEW-POLICY.md` rule 1),
  and in any case by rule 3: the real Langfuse path is not covered by the
  suite.
- **Out of scope:** tool results in traces, §9 dimensions as tags, score
  configs, annotation queues and label import (all §10); sending eval
  scores or §8 check results to Langfuse as scores; Langfuse datasets and
  experiments; changing `infra/langfuse/`.

## Type-specific questions

### Feature
- **Users:** the owner, reading a failed eval case in Langfuse; later §10's
  labelling.
- **What exists today:** eval runs reach no Langfuse; `uv run advisor` runs
  are traced with `provider:` and `model:` tags (`cli.py:106-107`,
  `tracing.py:43-47`).
- **Open design questions:**
  1. How the run and case appear: tags (`run:<stamp>`, `case:<id>`), trace
     metadata, the trace name (`advisor-run` today), or a session id per run
     (Langfuse sessions group traces). Tags were asked for; metadata or a
     session may filter better. The spec settles it.
  2. How the recording tracer and the Langfuse tracer are combined: a small
     fan-out tracer in `run.py` that calls both, or a change to the tracer
     protocol.
  3. The cost of a down Langfuse: `finish` waits up to 5 s per trace, so a
     60-case run could wait up to 5 minutes. One flush at the end of the
     run, a shorter wait, or giving up after the first timeout.
  4. Whether the run report records the trace id per case (it would help
     §10 match traces to cases), or only the tags.
  5. How the boundary test changes, and whether `tracing.py` itself must
     change (tags only at construction today; a per-case tag set means one
     tracer per case, as `cli.py` already does per run).
  6. Whether the stdout total line says that tracing was on.

## Assumptions I made

- **Always on when configured**, the owner's choice: like `uv run advisor`,
  no `--trace` flag. A run with the keys in `.env` will send traces; there
  is no flag to turn it off for one run unless the spec adds one (the owner
  can unset the variables).
- **One trace per case**, matching one `answer_question` call, as the CLI
  traces one question.
- **The tag text is `eval`**, lower case, like the existing tags.
- **The owner's choice of tags** (eval, provider, model, run, case) is the
  outcome; whether run and case are tags or metadata is left to the spec
  (question 1), as long as the Tracing table can filter on them.
- **Reviewed tier**: it changes what reaches Langfuse (by meaning, as for
  §10) and likely touches `tracing.py`.
