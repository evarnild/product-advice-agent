# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project overview

product-advice-agent: A small product-advice agent for a synthetic electronics catalogue, with evaluation, tracing and guardrails.

The repository holds the AI-native SDLC kit (from ai-sdlc-kit, first built
for heraklios) and the product's walking skeleton: a Python package
`advisor` (`src/advisor/`), managed by `uv`, that answers a question from a
synthetic catalogue through a provider-agnostic model interface, wrapped in
a guardrail seam and traced to a self-hosted Langfuse. The stack and the
reasons are in `docs/decisions/0001-stack.md`.

## Commands

```
npm run verify        # THE check before a change is done: kit tests, then ruff check, ruff format --check, mypy, pytest
npm run check:intent  # does this branch's change match its intent? (intents/README.md)
npm run sdlc:scan     # the evidence behind docs/sdlc-grid.md
npm run queue         # the intent queue, generated from metadata.yml (--next-id, --json); nobody edits it
npm run spawn -- <id> # parallel session for an intent (see "Parallel sessions")
npm run sessions      # what every worktree/session is doing (--json for data, --log for the event tail)
npm run ship -- <id>  # merge a reviewed intent, bookkeep, push, remove worktree and branch (the /ship skill)
npm run test:kit      # node --test over scripts/*.test.mjs
npm run verify:product  # the product half of verify (uv run ruff/mypy/pytest)
npm run setup:worktree  # uv sync --frozen: installs the product's dependencies
uv run advisor "<question>"  # run the agent (local Ollama by default; ANTHROPIC_API_KEY only for anthropic, see README.md)
uv run advisor-analysis generate|view|taxonomy|counts|queue|import  # error analysis on top of the evals (README.md; generate and taxonomy call a model; queue and import need the three LANGFUSE_* variables)
uv run advisor-eval  # score the agent on evals/cases.jsonl with a real model (README.md "Evaluating answers"; not part of verify)
```

The kit itself needs Node ≥ 22 and nothing else: no `npm install`. The
product needs `uv`. `verify` is **one** command that runs both halves, and
"green on a fresh clone" means green after `npm run setup:worktree` (`uv sync
--frozen`); `npm run spawn` runs that for a new worktree.

## How work flows

`sdlc.md` is the step-by-step version for the owner: intent → spec → plan →
build → review → merge, and what each type requires. If it disagrees with the
rules below or with `intents/README.md` and `REVIEW-POLICY.md`, those win.

- The queue is generated, never hand-kept: `npm run queue` lists every
  intent with its status (from its branch while unmerged, else `main`).
  `OVERVIEW.md` is the short, owner-edited snapshot. Each work item's detail
  lives in `intents/<id>-<slug>/`: intent, spec (features), plan, review
  report, metadata. Read `intents/README.md` for the types, the gates and
  branch naming (`feat/2-…`, `fix/2-…`).
- No code before the plan's gate is recorded in `metadata.yml`.
- `/intent` drafts an intent, `/spec` a feature's spec, `/build-plan` a
  plan, `/review` runs `REVIEW-POLICY.md` and writes `review.md`, `/grid`
  refreshes `docs/sdlc-grid.md`, `/spawn` and `/sessions` run parallel work
  (below), and `/ship <id>` merges a reviewed intent when the owner asks
  (`REVIEW-POLICY.md` → "Merging").
- The `product-advice-agent-implementer` agent builds an approved plan, and the
  `product-advice-agent-reviewer` agent does the adversarial passes for `/review`.
- `/auto <id>` (coordinator only) carries one accepted intent through the
  steps above: spec (a feature stops once, for the owner's `spec_accepted`),
  plan, spawn, implement, review, and rework, for at most three review
  rounds. The owner's `/auto <id>` is a request to record that intent's
  `plan_approved` and nothing else (`intents/README.md` → "Who edits what").
  It stops for the owner's questions, a "Needs decision:" finding, an
  `escalate` verdict (the owner reads the diff; the next `/auto <id>` goes
  on), a spec or plan amendment, running out of rounds, the live check, a
  CRITICAL finding, any red it cannot trace, a re-check mismatch, a plan
  that exists unapproved, a ship dry-run that is blocked, a worktree held by
  another session, a fourth open session or an agent error, and ends at
  "ready: `/ship <id>`". It never ships, and never records `spec_accepted`
  or `live_checked` without the owner's yes; the `/auto` authorisation
  covers neither. A stop shows in `npm run sessions` as
  `auto · r<n> · <reason>`.
- An agent records a gate (`metadata.yml`) only on the owner's request in
  the current conversation, with `by-agent` after the date; a subagent never
  does (`intents/README.md` → "Who edits what").
- Merges into `main` are local. An agent merges, pushes, deletes a branch
  or removes a worktree only when the owner explicitly asks for that action
  in the current conversation, never on its own initiative, and only after
  the preconditions in `REVIEW-POLICY.md` → "Merging".
- **Never `git checkout` a branch in the main checkout.** It belongs to the
  coordinator session. Implementers and reviewers work in their own
  worktrees.
- A change owes a **live check** when `REVIEW-POLICY.md` → "Live checks"
  says so. The owner runs it; `live_checked: <date>` is recorded, by the
  owner or by an agent on their request, before the merge. An agent's own
  run is evidence, never that gate.

## Parallel sessions

Several intents can run at once, each in its own worktree with its own
Claude Code session. One session, in the main checkout, is the
**coordinator**.

```
npm run spawn -- <id>           # worktree ../product-advice-agent-wt/<id>-<slug> on the intent's branch,
                                # npm run setup:worktree if defined, port 5200+(id mod 100), CLAUDE.local.md brief
npm run spawn -- <id> --remove  # after merge; refuses if unmerged, dirty or holding a link
npm run sessions                # every worktree: status, gates, ±main, dirty, session state
npm run sessions -- --log 30    # the raw event tail
```

- **State lives in three places, each with one owner.** Intent status and
  gates are in `metadata.yml` on the intent's branch; `npm run sessions`
  reads it from each worktree. Git facts (ahead/behind, uncommitted files)
  come from git. What each session is doing is in
  `.git/product-advice-agent-sessions.jsonl`, written by the hooks in
  `.claude/settings.json` on start, prompt, turn end, notification and end.
  That file is never committed, and no agent writes to it by hand. It holds
  **no prompt text**: a prompt is logged by its length only. Events are
  filed under the session's project directory, so a session that `cd`s into
  another worktree still shows as itself. A permission prompt or question
  shows as `needs you`. Claude Code's idle "waiting for your input"
  reminder shows as `idle`, but never hides a prompt still waiting on you:
  only your next prompt, the turn ending or the session ending clears it.
- **Only the coordinator** runs `/spawn`, `/sessions`, `/review` and
  `/auto`, and sends "main moved, rebase" notices. The owner merges (or
  asks the coordinator to, per "Merging"), one branch at a time, running
  `npm run verify` on `main` after each merge.
- **A spawned session** works only on its branch and its intent. Its
  `CLAUDE.local.md` (gitignored, written by spawn) says which intent, branch
  and port it has. It never edits the queue (it is generated), never
  merges, and sets `status: in-review` when done.
- **`/spawn` launches the implementer itself** when `metadata.yml` already
  records the gate the type needs (`plan_approved` for feature/fix/refactor,
  `intent_accepted` for adjustment/experiment): a background
  `product-advice-agent-implementer` agent working in the worktree. With a gate missing
  it hands over instead. On completion the coordinator reports and offers
  `/review`; outside an `/auto <id>` run (`.claude/skills/auto/SKILL.md`) it
  never runs it unprompted, and it never records a gate or merges.
- **A launched implementer is not a session in `npm run sessions`.** Hooks
  run per session and file events under `CLAUDE_PROJECT_DIR`, so the
  implementer files none under the worktree (its row shows `no events`) and
  the coordinator's row reflects only the coordinator's own session.
  Progress shows in the worktree's `status`, `dirty` and `ahead` columns
  (the implementer commits early), and `in-review` means it finished.
- Keep it to about three intent sessions (or launched implementers) at
  once. Merges and reviews are serial, so more sessions mostly add rebases.
- Spawned worktrees live outside the repo on purpose, so the project's
  tools never pick up a nested checkout. Each worktree installs its own
  dependencies: `npm run setup:worktree` (`uv sync --frozen`), which spawn
  runs.

## Architecture

Python package `advisor` in `src/advisor/`, tests in `tests/`, local
Langfuse stack in `infra/langfuse/`.

**Pure, tested logic** (the `CORE_CODE` modules in
`scripts/intent-check-lib.mjs`):

- `catalogue.py`: `Product`, `load_catalogue` (validates, names product and
  field), `search_products` (AND of filters, price-then-id order, limit
  clamped to 1..10, keywords case-insensitive, a hyphen counts as a space). Data: `data/catalogue.json`, synthetic.
- `agent.py`: `run_agent` (the tool loop, at most 5 model turns, error tool
  results for bad calls, fixed fallback answer) and `answer_question` (input
  guardrail, agent, output guardrail, one trace). Pure orchestration over a
  `ModelClient` and tool functions.
- `guardrails.py`: `check_input` / `check_output`, the seam (both allow in
  the skeleton); a block gives the fixed refusal.
- `models/`: the `ModelClient` protocol and message types (`base.py`), the
  scripted fake for tests and evals (`fake.py`), and `make_client` with the
  provider registry. `models/anthropic_model.py` is the Anthropic adapter and
  `models/ollama_model.py` the Ollama adapter (the local default, keyless,
  over `/api/chat` with `httpx`, imported only there).

**Offline evals** (`src/advisor/evals/`, console script `advisor-eval`):
`cases.py` (the case model and file validation) and `score.py` (the
deterministic checks) are pure and core code (in `CORE_CODE`); `run.py` is the I/O (case file, client,
clock, stdout, the JSON report in `evals/runs/`) with its own recording
tracer. It loads `advisor.tracing` only when the three `LANGFUSE_*` variables are set (it then traces each case, tagged `eval`), and imports no provider SDK. Cases are
data in `evals/cases.jsonl`.
`cases.catalogue_problems` checks the cases against the catalogue (a test in
`verify` runs it on the committed file; rules in `docs/decisions/0003-catalogue-changes.md`),
and the run report records `catalogue_sha256` beside the cases and prompt hashes.

**Error analysis** (`advisor-analysis`, §9 and §10, same package). Pure: `coverage.py`
(the question grid and the catalogue check), `labels.py`, `taxonomy.py`,
`counts.py`, `report.py`, `modeljson.py`, `annotate.py` (§10: the `Annotations`
protocol for Langfuse annotation queues, case selection, trace matching and
label building; SDK-free), `generate.py` (prompt and filter
over a `ModelClient` it is given), and `dimensions` in `cases.py`. I/O:
`analysis.py` (the subcommands `generate`, `view`, `taxonomy`, `counts`,
`queue` and `import`, files, clock, exit codes; it imports `advisor.tracing`
only inside `queue` and `import`) and `view.py`,
the local FastHTML label viewer, the only module that imports `fasthtml`,
`starlette` or `uvicorn` (`tests/test_boundaries.py`); it binds 127.0.0.1
only. The prompts for `generate` and `taxonomy` are `evals/prompts/*.md`.
`run.py` also records turns, tool results and guardrail checks per case.
Committed data: `evals/generated.jsonl`, `evals/labels/*.jsonl`,
`evals/taxonomy.json` (format in README.md "Error analysis").

**Shared protocol** (neither core nor I/O): `tracer.py` holds the `Tracer`
protocol and the no-op, SDK-free and without I/O, so the pure modules
import it.

**I/O and wiring** (not core; the live check covers them): `cli.py` (entry
point, exit codes), `config.py` (environment and `.env`), `tracing.py` (the
Langfuse tracer, `SafeTracer`, `make_tracer`, and `LangfuseAnnotations` /
`make_annotations`, the only code that calls Langfuse's queue, score-config,
score and observation APIs; a tool observation carries the rows the tool returned; it re-exports `Tracer` and
`NoopTracer` from `tracer.py`), `prompts/system.md` (the shipped prompt).

**Conventions worth knowing before editing**

- Provider and tracing libraries are imported in exactly one module each:
  `anthropic` only in `models/anthropic_model.py`, `httpx` only in
  `models/ollama_model.py`, `langfuse` only in
  `tracing.py` (`tests/test_boundaries.py` enforces it). The agent and CLI
  see the `ModelClient` and `Tracer` protocols only. The pure modules load
  neither `langfuse` nor `opentelemetry` (a subprocess test in
  `tests/test_boundaries.py` enforces it).
- The CLI speaks to the user through `print` only. Library log lines that
  propagate to the root logger (e.g. OpenTelemetry's "Failed to export span
  batch") reach stderr only with `--debug`; without it,
  `cli._configure_logging` gives the root logger a `NullHandler` unless
  logging is already set up. `tests/test_cli_stderr.py` proves the cases.
  One known exception: importing `langfuse` attaches its own stderr handler
  to the `httpx` logger at WARNING, so an `httpx` warning can still show.
- Tracing never changes a run: every Langfuse call is wrapped and swallowed,
  flush waits at most 5 s, and tracing is a no-op unless `LANGFUSE_HOST`,
  `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are all set.
- Provider SDK clients are built with their own tracing off (the Anthropic
  adapter passes `open_telemetry=False`), so a run is one Langfuse trace.
- Tests drive a scripted fake `ModelClient` and assert on what it received.
  `tests/conftest.py` makes any socket connect fail the test. Never build
  the real adapter or Langfuse client in a test without patching it.
- `mypy --strict` covers `src/advisor`; ruff lints and formats everything.
- Secrets live in `.env` and `infra/langfuse/.env` (both gitignored); only
  `.env.example` files with placeholders are committed.
- A new provider is a new `models/<provider>.py`, a name in `KNOWN_PROVIDERS`
  and a branch in `make_client`, and its own tests. A provider that needs a
  key also gets a line in `PROVIDER_KEY_ENV`; a keyless one (ollama) has none,
  and the CLI then skips the key check and passes no key.

**Live checks (`REVIEW-POLICY.md` → "Live checks", rule 1)** are owed for
changes to `src/advisor/cli.py`, `src/advisor/models/`,
`src/advisor/tracing.py`, `src/advisor/prompts/` and `infra/`.

**Reviewed tier by meaning**: `src/advisor/prompts/**`,
`src/advisor/guardrails.py`, `src/advisor/cli.py`, `src/advisor/config.py`,
`.env.example` files, `src/advisor/tracing.py`.

## Conventions that already apply

- Model calls and external APIs are faked or recorded in tests, never called
  live from the suite.
- No secret, token or real user data is committed, including in fixtures
  and logs.
- No new dependency arrives without a line in the intent's `plan.md` saying
  why.
