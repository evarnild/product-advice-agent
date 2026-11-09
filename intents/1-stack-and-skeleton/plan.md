<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §1 plan — Stack decision (Python + Langfuse) and project skeleton

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Turn the kit-only repository into a Python product with a walking
skeleton: `uv run advisor "<question>"` answers from a synthetic catalogue
through a provider-agnostic model interface (Anthropic adapter), wrapped in
a guardrail seam and traced to a self-hosted Langfuse. `npm run verify`
becomes the one check for kit and product, and the kit's §1 hand-offs
(`CLAUDE.md` → "Architecture", `CORE_CODE`, `REVIEW-POLICY.md` paths,
`setup:worktree`, README) are done. Spec B1–B26, AC1–AC14.

## Risks

- **Tests that pass whatever the code does.** Every agent/CLI test drives
  a scripted fake `ModelClient`; assert on what the fake *received* (tool
  results, messages), not only on the returned text, or a loop that skips
  the tool would still pass.
- **A live call from the suite.** The Anthropic adapter and Langfuse client
  must never be constructed in tests unless patched. B21's socket guard is
  the backstop; it must itself be tested (AC11).
- **Narrowing `CORE_CODE` breaks kit tests.** `scripts/intent-check-lib.test.mjs`
  and `scripts/ship.test.mjs` use `src/core/*.ts` and `src/x18.txt` as
  examples of core code. Update those fixtures to paths under the new
  `CORE_CODE`; don't weaken an assertion. This file is Reviewed-tier.
- **Secrets.** `.env`, `infra/langfuse/.env` must be gitignored before any
  is created; `.env.example` files hold placeholders only. The Langfuse
  compose file must not carry default secrets that look real, and must
  bind ports to `127.0.0.1`.
- **SDK drift.** The Langfuse Python SDK changed API between majors
  (v2 decorators vs v3 OpenTelemetry-based client). Use the current major's
  documented API, keep it entirely inside `tracing.py`, and pin via
  `uv.lock`.
- **Windows.** The owner runs Windows (Git Bash / PowerShell). `npm run
  verify` must not rely on POSIX-only shell syntax beyond `&&`.
- **Stale line citations.** The `path:line` list below was read at the
  commit named there; re-check before editing the kit files.
- **Pass 9 footguns:** the list in `REVIEW-POLICY.md` is empty so far;
  nothing repo-specific to add yet.

## Verified against the codebase

Re-read on `main` at `7a4b288` (code unchanged since `fda34d9`).

- `package.json:16` — `"verify": "npm run test:kit"`; no `setup:worktree`.
- `scripts/intent-check-lib.mjs:144-147` — comment: "The stack is not
  chosen yet (§1 decides it)… §1 narrows CORE_CODE".
- `scripts/intent-check-lib.mjs:153` — `export const CORE_CODE = [/^src\//];`
- `scripts/intent-check-lib.mjs:148-152` — `TEST_RE` already matches
  `test_*.py`, `*_test.py` and anything under `tests/`.
- `scripts/intent-check-lib.test.mjs:30-31,124,150,163` — fixtures using
  `src/core/router.ts`, `src/core/config.ts`, `src/core/triage.ts` as core
  code.
- `scripts/intent-check-lib.test.mjs:381-382` — Python test-name fixtures
  with `src/core/router.py`.
- `scripts/ship.test.mjs:256-265` — "core code (CORE_CODE) without a test
  routes the change", via `src/x18.txt` / `src/x19.txt`.
- `scripts/ship-lib.test.mjs:43-45` — `src/x.ts` as a changed file (not a
  `CORE_CODE` assertion; check before editing).
- `scripts/spawn-intent.mjs:74` — `const SETUP_COMMAND = 'npm run
  setup:worktree --if-present';`
- `REVIEW-POLICY.md:30` — Reviewed tier row, "**and, by meaning until §1
  names the paths:**…".
- `REVIEW-POLICY.md:45` — "**Until §1 adds the product's test suite, only
  the kit itself (`scripts/`) meets this**".
- `REVIEW-POLICY.md:77-78` — live-check rule 1: "§1 adds the product's
  entry points, UI and integration adapters; until then this rule names
  nothing".
- `CLAUDE.md:6-13` — "Project overview": "Until §1 merges, there is no
  product code".
- `CLAUDE.md:28-30` — "§1 extends `verify`… Keep it **one** command."
- `CLAUDE.md:137-150` — "Architecture: None yet. §1 writes this section".
- `.gitignore` — no `.env`, `.venv`, `__pycache__`, `.mypy_cache`,
  `.pytest_cache`, `.ruff_cache` entries.
- No `src/`, `tests/`, `pyproject.toml`, `infra/` exist.
- Toolchain on the owner's machine: Python 3.14.0, uv 0.6.10, Docker 29.8.2,
  Compose v5.5.1, Node 24.11.0.

## Dependencies (each with its reason, per `CLAUDE.md`)

- `anthropic` (runtime) — the one shipped model adapter (spec B6). Imported
  only in `src/advisor/models/anthropic.py`.
- `langfuse` (runtime) — the tracing client for the self-hosted Langfuse
  (B15). Imported only in `src/advisor/tracing.py`.
- `python-dotenv` (runtime) — loads the root `.env` (B19); small, avoids a
  hand-written parser with quoting bugs.
- `pytest`, `ruff`, `mypy` (dev group) — the test, lint/format and type
  tools chosen in B1/B20.

No other dependency without amending this plan.

## Subtasks

Each ends with `npm run verify` green and a commit.

1. **Python project scaffold.** `pyproject.toml` (package `advisor`,
   `src/` layout, `requires-python = ">=3.12"`, console script
   `advisor = "advisor.cli:main"`, dev group, ruff config, mypy strict on
   `src/advisor`, pytest config), `uv.lock`, `src/advisor/__init__.py`,
   `tests/conftest.py` with the socket guard (B21) and its test.
   `.gitignore` gains `.env`, `.venv/`, `__pycache__/`, `.mypy_cache/`,
   `.pytest_cache/`, `.ruff_cache/`, `infra/langfuse/.env`.
   `package.json`: `setup:worktree` = `uv sync --frozen`; `verify:product`
   = `uv run ruff check && uv run ruff format --check && uv run mypy &&
   uv run pytest`; `verify` = `npm run test:kit && npm run verify:product`.
   (B1, B20, B21, B22)
2. **Catalogue.** `src/advisor/data/catalogue.json` (25–40 fictional
   products across the categories), `src/advisor/catalogue.py`: `Product`
   dataclass, `load_catalogue(path)` with validation errors naming product
   and field, `search_products(...)` per B4. Package data included in the
   build. Tests first. (B2–B4)
3. **Model interface.** `src/advisor/models/base.py`: `ModelClient`
   protocol, `ToolSpec`, `ToolCall`, `ModelTurn` (text | tool calls, usage,
   model name), the interpretation comment from the spec.
   `src/advisor/models/fake.py` (scripted fake, in `src/` so tests and
   future evals share it) and `src/advisor/models/anthropic.py`
   (translates to/from the Messages API tool-use format).
   `src/advisor/models/__init__.py`: `make_client(provider, model)`
   registry. Tests for the registry, the fake, and the Anthropic adapter's
   translation with the SDK client patched (no network). Boundary test
   AC6. (B5–B7)
4. **Agent loop + prompt.** `src/advisor/prompts/system.md`,
   `src/advisor/agent.py`: `run_agent(question, client, tools, tracer) ->
   AgentResult`, 5-turn cap, error tool results for bad calls, fallback
   text. Tests first. (B8–B11)
5. **Guardrail seam.** `src/advisor/guardrails.py`: `check_input`,
   `check_output` returning `Verdict(allow, reason)`, both allowing, with
   the spec's interpretation comment; refusal text constant. Tests. (B12)
6. **Tracing.** `src/advisor/tracing.py`: a `Tracer` protocol with a no-op
   implementation and a Langfuse implementation, `make_tracer(env)`
   returning no-op unless all three variables are set; every Langfuse call
   wrapped so a failure is logged at debug and swallowed; bounded flush.
   The agent and CLI record observations through the protocol only. Tests
   with a recording fake tracer and a raising tracer. (B15–B17)
7. **Config + CLI.** `src/advisor/config.py` (env + `.env`, provider,
   model, default model id, key lookup by provider without printing it),
   `src/advisor/cli.py` (`main(argv) -> int`, usage/exit 2, unavailable/
   exit 1, `--debug`), wiring guardrails → agent → guardrails inside one
   trace. Root `.env.example`. Tests per AC7, AC9. (B6, B7, B12–B14, B19)
8. **Local Langfuse.** `infra/langfuse/docker-compose.yml` adapted from
   Langfuse's documented self-host compose (v3: web, worker, Postgres,
   ClickHouse, Redis, MinIO), ports on `127.0.0.1`, secrets from
   `infra/langfuse/.env`; `infra/langfuse/.env.example` with placeholders
   and a note on generating them. `docker compose config` must parse it.
   (B18)
9. **Docs and kit hand-offs.** `docs/decisions/0001-stack.md` (B1, AC1);
   `README.md` run/setup/Langfuse/verify sections (B26); `CLAUDE.md`
   "Project overview", "Commands" (verify now includes the product;
   `setup:worktree` exists; "green on a fresh clone" means after
   `uv sync --frozen`), "Architecture" (B23); `CORE_CODE` narrowed to
   `^src/advisor/(agent|catalogue|guardrails)\.py$` and
   `^src/advisor/models/`, comment updated, kit test fixtures moved to
   those paths (B24); `REVIEW-POLICY.md` rows 30, 45, 77–78 updated with
   the paths from B25 (B25); `OVERVIEW.md` snapshot line.

## Tests

| Spec | Test | Fails if mutated |
| --- | --- | --- |
| B2, B3 | `tests/test_catalogue.py`: committed file loads with 25–40 products, all categories valid; one fixture per defect kind, message contains product id and field | dropping a validation branch; accepting duplicate ids |
| B4 | `tests/test_catalogue.py`: AND of filters; case-insensitive all-keywords; sort price-then-id with a price tie; limit clamp at 0 and 11; empty result | `and`→`or`; `all`→`any`; sort key change; clamp removed |
| B5, B8 | `tests/test_agent.py`: fake scripted tool-call → text; assert the fake's second request contains the tool result for the given args | skipping tool execution; sending wrong results |
| B9 | `tests/test_agent.py`: fake always calls tools → fallback after exactly 5 turns (fake records 5 calls) | cap 5→6; fallback text change |
| B10 | `tests/test_agent.py`: unknown tool and bad args → error tool result sent back, no exception | raising instead |
| B5 (AC6) | `tests/test_boundaries.py`: AST scan of `src/advisor/**/*.py`; only `models/anthropic.py` imports `anthropic`, only `tracing.py` imports `langfuse` | an import elsewhere |
| B6, B7 | `tests/test_models.py`, `tests/test_cli.py`: unknown provider → exit 1, message lists `anthropic`; missing key → exit 1 naming `ANTHROPIC_API_KEY`; adapter not constructed | wrong exit code; check after construction |
| B6 | `tests/test_models.py`: Anthropic adapter maps a patched SDK response with `tool_use` blocks to `ToolCall`s and usage, and a text response to final text | mapping errors |
| B12 | `tests/test_guardrails.py`: defaults allow; patched blocking input → refusal, fake model received no call; patched blocking output → refusal replaces answer | skipping a check; using agent output after block |
| B13, B14 | `tests/test_cli.py`: blank / missing question → exit 2, usage on stderr; raising fake → exit 1, unavailable text, no `Traceback` in stderr; `--debug` shows it | exit codes; message text |
| B15 | `tests/test_tracing.py`: recording tracer gets input-check, generation (model, usage), tool, output-check in order, one trace with question/answer | dropped or reordered observation |
| B16 | `tests/test_tracing.py`: with any of the three vars unset, `make_tracer` returns the no-op and `langfuse` client class is never instantiated (patched) | condition `all`→`any` |
| B17 | `tests/test_tracing.py`: a tracer whose every method raises → same answer and exit 0 | removing the swallow |
| B21 | `tests/test_no_network.py`: a socket connect inside a test raises | removing the fixture |
| B24 | kit tests in `scripts/intent-check-lib.test.mjs` using new core paths, plus one asserting a non-core `src/advisor/cli.py` change does not route as core | pattern too wide or too narrow |

## Validation

- `npm run verify` green (kit tests + ruff check + ruff format --check +
  mypy + pytest).
- `npm run check:intent` PASS on `feat/1-stack-and-skeleton`.
- `docker compose -f infra/langfuse/docker-compose.yml config -q` exits 0
  (parse only; nothing is started by an agent).
- **Live check, owed** (rule 1, once the new paths are named, and spec
  AC14): the owner copies `infra/langfuse/.env.example` to `.env` and fills
  secrets, runs `docker compose -f infra/langfuse/docker-compose.yml up -d`,
  opens `http://localhost:3000`, creates a project and keys, writes them
  and `ANTHROPIC_API_KEY` into the root `.env`, runs
  `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
  and checks: the answer names catalogue products by name and id; one trace
  appears with the input check, the generation(s) with token usage, the
  `search_products` call and the output check.

## Assumptions I made

- Default model `claude-haiku-5-5` (the current small Claude model),
  overridable by `ADVISOR_MODEL`.
- The fake model client lives in `src/advisor/models/fake.py`, not under
  `tests/`, so later eval intents can reuse it; it is excluded from nothing.
- `mypy --strict` covers `src/advisor` only; tests are type-checked
  leniently (not strict) to keep fixtures short.
- `CORE_CODE` excludes `cli.py`, `config.py`, `tracing.py` and the catalogue
  data; they are wiring and I/O whose mistakes the live check catches.
- `uv 0.6.10` on the owner's machine supports `uv sync --frozen` and
  dependency groups; if not, the implementer reports it rather than working
  around it.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-09 — subtasks 1–9 (implementer)

Commits: ecf3f3a (scaffold), 3d4f3ac (catalogue), 4361ced (models), 5efe313
(agent, prompt, guardrails), 44b72e9 (tracing), a9323b2 (config, CLI),
2a2dd92 (Langfuse compose), 6453c2e (docs, CORE_CODE, REVIEW-POLICY,
CLAUDE.md). A stalled stream interrupted subtask 3; it resumed from the
uncommitted files.

Shipped: everything in subtasks 1–9. `npm run verify` = kit tests (255 pass)
+ ruff check + ruff format --check + mypy strict (11 source files) + pytest
(89 pass). `check:intent` PASS.

Divergences and notes:
- `answer_question` (input guardrail, agent, output guardrail, one trace)
  lives in `agent.py`, not `cli.py`, so the guardrail wiring is pure and
  testable; the CLI calls it. Plan said "wiring ... in cli".
- The `Tracer` protocol and `NoopTracer` are in `tracing.py` (created in
  subtask 4, filled in subtask 6); `SafeTracer` wraps every Langfuse call.
- `make_client(provider, model, api_key)` takes the key as an argument;
  config looks it up via `PROVIDER_KEY_ENV`.
- `docker compose -f infra/langfuse/docker-compose.yml config -q` exits 0
  only once `infra/langfuse/.env` exists, because secrets are required
  (`${VAR:?}`), not defaulted. With `--env-file infra/langfuse/.env.example`
  it exits 0 (done; documented in README). Nothing was started.
- Added `tests/helpers.py` (recording and raising tracers) and
  `tests/test_config.py`; a real-SDK tracing test uses Langfuse with an
  in-memory OpenTelemetry exporter (no network).
- Kit fixtures moved to `src/advisor/...`, `tests/...` paths; one kit test
  added for non-core vs core paths; no assertion weakened.
- Python resolved to 3.12.9 in `.venv` (`requires-python >=3.12`).
