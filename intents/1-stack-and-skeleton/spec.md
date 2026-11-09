<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §1 spec — Stack decision (Python + Langfuse) and project skeleton

Accepted intent: [intent.md](intent.md)
Written against `main` at `a7a70f7`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Owner's decisions (2026-11-09, question round)

| Question (intent → open design questions) | Owner's answer |
| --- | --- |
| 1. Model provider | **Provider-agnostic** |
| 4. Langfuse hosting | **Compose file in repo**: Langfuse v3 started by hand for live runs; the suite never needs it; tracing off when no keys are set |
| 5. Entry point | **CLI first**; an HTTP API is a later intent |
| 3. Catalogue search | **Structured filter tool** over a small committed JSON catalogue |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/1-stack-and-skeleton/intent.md` | Scope is a walking skeleton; "Out of scope: advice quality, the evaluation suite, guardrails beyond a placeholder seam, a UI and any deployment." |
| `CLAUDE.md` → "Conventions that already apply" | "Model calls and external APIs are faked or recorded in tests, never called live from the suite"; "No secret, token or real user data is committed, including in fixtures and logs"; "No new dependency arrives without a line in the intent's `plan.md` saying why." |
| `CLAUDE.md` → "Commands" | "§1 extends `verify` with the product's build, lint and tests, whatever the stack is. Keep it **one** command." |
| `CLAUDE.md` → "Architecture" | §1 "narrows `CORE_CODE` in `scripts/intent-check-lib.mjs`", "names the runtime paths that owe a live check", "names the paths behind the Reviewed tier's 'by meaning' list", "defines `npm run setup:worktree`". |
| `REVIEW-POLICY.md` → "Live checks", rule 1 | "§1 adds the product's entry points, UI and integration adapters; until then this rule names nothing". |
| `REVIEW-POLICY.md` → "Tiers" | the "by meaning" list: "model prompts and agent instructions the product ships, anything that sends text to a user or an external system without a human in between, credential handling, and storage or logging of users' personal data". |
| `scripts/intent-check-lib.mjs:153` | `export const CORE_CODE = [/^src\//];` |
| `package.json` | `"verify": "npm run test:kit"` |
| Langfuse self-hosting docs (https://langfuse.com/self-hosting/docker-compose) | Langfuse v3 runs as `langfuse-web` + `langfuse-worker` with Postgres, ClickHouse, Redis and S3-compatible storage (MinIO) |

## Behaviour

**Stack (recorded in `docs/decisions/0001-stack.md`)**

- **B1.** The product is a Python package `advisor` under `src/advisor/`,
  managed by `uv` (`pyproject.toml` + committed `uv.lock`), requiring
  Python ≥ 3.12. Lint and format: `ruff`. Types: `mypy --strict` on
  `src/`. Tests: `pytest`. The decision record states each choice and its
  reason, and the owner's four answers above.

**Catalogue**

- **B2.** A synthetic catalogue of 25–40 electronics products is committed
  at `src/advisor/data/catalogue.json`. Each product has `id` (`P-###`),
  `name`, `brand` (fictional), `category` (one of a closed list, e.g.
  `laptop`, `phone`, `headphones`, `monitor`, `tablet`, `smartwatch`),
  `price_eur` (number > 0), `in_stock` (bool), `specs` (string → string
  map) and `description`. No real brand, product or person appears.
- **B3.** The catalogue is loaded and validated at start-up. A malformed
  file (missing field, wrong type, duplicate id, unknown category) stops
  the run with exit code 1 and a message naming the product and the field.
- **B4.** `search_products(category?, min_price?, max_price?, keywords?,
  in_stock_only=false, limit=5)` is a pure function over the loaded
  catalogue. A product matches when it satisfies every given filter;
  `keywords` match when every keyword appears, case-insensitively, in the
  name, brand or description. Results are sorted by price ascending, then
  id, and cut to `limit` (1–10; out-of-range values are clamped). No match
  returns an empty list, not an error.

**Model interface (provider-agnostic)**

- **B5.** The agent talks to models only through an internal protocol
  (`ModelClient`): given the system prompt, the conversation so far and the
  tool definitions, it returns one turn, which is either final text or one
  or more tool calls, plus usage (input/output tokens) and the model name.
  Nothing outside `src/advisor/models/` imports a provider SDK.
- **B6.** §1 ships one adapter, Anthropic, and the fake used by tests. The
  adapter is chosen by `ADVISOR_MODEL_PROVIDER` (default `anthropic`) and
  the model by `ADVISOR_MODEL` (default: a small, inexpensive model of
  that provider, named in config). An unknown provider stops the run with
  exit code 1 and a message listing the known ones.
- **B7.** A missing provider key (e.g. `ANTHROPIC_API_KEY`) stops the run
  with exit code 1 and a message naming the variable, before any network
  call.

**Agent**

- **B8.** The agent loop: send the question with the system prompt and the
  `search_products` tool; run every tool call the model asks for and send
  back the results; repeat until the model returns final text. The loop is
  pure orchestration over a `ModelClient` and the tool functions, so it
  runs under test with the fake.
- **B9.** After 5 model turns without final text, the loop stops and the
  answer is the fixed fallback "I couldn't find a good answer to that. Try
  asking about a product category or a price range."
- **B10.** A tool call with an unknown tool name or invalid arguments is
  answered to the model with an error result (not raised), so the model can
  correct itself; it counts as a turn.
- **B11.** The system prompt lives in a file, `src/advisor/prompts/system.md`.
  It tells the model to recommend only products returned by the tool, to
  cite each one by name and id, to say so when nothing matches, and to stay
  on the catalogue's topic.

**Guardrail seam**

- **B12.** Every run passes the question through `check_input` before the
  agent and the answer through `check_output` after it
  (`src/advisor/guardrails.py`). Each returns allow or block (with a
  reason). In §1 both always allow. On block, the user gets a fixed refusal
  ("I can only help with questions about our electronics catalogue.") and
  the agent (or its answer) is not used.

**CLI**

- **B13.** `uv run advisor "<question>"` prints the answer to stdout and
  exits 0. With no question or a blank one, it prints a usage line to
  stderr and exits 2.
- **B14.** A model or network failure prints "The advisor is unavailable
  right now." to stderr and exits 1, with no stack trace (a `--debug` flag
  shows it).

**Tracing**

- **B15.** When `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and
  `LANGFUSE_HOST` are all set, each CLI run produces exactly one Langfuse
  trace, with observations for: the input check, each model call (as a
  generation, with model name and token usage), each tool call (arguments
  and result count), and the output check. The trace input is the
  question, its output the answer.
- **B16.** When any of the three is unset, tracing is a no-op: nothing
  connects to Langfuse and nothing is logged about it beyond one debug line.
- **B17.** A tracing failure (Langfuse down, bad keys) never changes the
  answer or the exit code; the run flushes traces with a bounded wait
  (≤ 5 s) before exiting.

**Local Langfuse**

- **B18.** `infra/langfuse/docker-compose.yml` starts a self-hosted
  Langfuse v3 (web, worker, Postgres, ClickHouse, Redis, MinIO) on
  `http://localhost:3000`, bound to localhost only. Its secrets come from
  an uncommitted `infra/langfuse/.env`; a committed
  `infra/langfuse/.env.example` holds placeholders only. `README.md` gives
  the steps: copy the example, set secrets, `docker compose up -d`, create
  a project and keys in the UI, put them in the root `.env`.

**Config and secrets**

- **B19.** Config comes from environment variables, with a root `.env`
  loaded if present. `.env` files are gitignored; a root `.env.example`
  lists every variable with a placeholder.

**Verify and the kit's hand-offs**

- **B20.** `npm run verify` runs the kit's tests, then `ruff check`,
  `ruff format --check`, `mypy` and `pytest` via `uv run`, and fails if any
  step fails. It remains one command.
- **B21.** The pytest suite makes no network connection: a session-wide
  fixture makes any socket connect attempt fail the test.
- **B22.** `npm run setup:worktree` runs `uv sync --frozen`, so a fresh
  worktree from `npm run spawn` passes `npm run verify` after it.
- **B23.** `CLAUDE.md` → "Architecture" describes the modules, the pure vs
  I/O boundary (pure: `catalogue`, `agent`, `guardrails`; I/O: `models/*`
  adapters, `tracing`, `cli`, `config`) and the conventions. The
  "Project overview" and "Commands" sections stop saying there is no
  product code.
- **B24.** `CORE_CODE` in `scripts/intent-check-lib.mjs` is narrowed to the
  agent loop, the catalogue search, the guardrails and the model
  interface: `src/advisor/agent.py`, `src/advisor/catalogue.py`,
  `src/advisor/guardrails.py`, `src/advisor/models/`. The kit's tests that
  cover `CORE_CODE` still pass, updated if they assert the old pattern.
- **B25.** `REVIEW-POLICY.md` names: (a) live-check runtime paths for rule
  1: `src/advisor/cli.py`, `src/advisor/models/` (adapters),
  `src/advisor/tracing.py`, `src/advisor/prompts/`, `infra/`; (b) the "by
  meaning" Reviewed paths: `src/advisor/prompts/**` (prompts),
  `src/advisor/guardrails.py` and `src/advisor/cli.py` (user-facing
  output), `src/advisor/config.py` and `.env.example` files (credentials),
  `src/advisor/tracing.py` (what is logged externally). It also lifts the
  "Until §1 adds the product's test suite" suspension now that it exists.
- **B26.** `README.md` says how to install (`uv sync`), configure, run the
  CLI, start Langfuse, and run `npm run verify`.

## Interpretations

- **"Provider-agnostic"** (owner's answer) is read as an internal
  `ModelClient` protocol with one shipped adapter (Anthropic), not as a
  third-party abstraction such as LiteLLM, and not as shipping two adapters
  in §1. Reason: it keeps the dependency count and the tracing surface
  small, and the fake proves the seam works; a second adapter is a small
  later intent. Comment site: `src/advisor/models/base.py`.
- **"tracing" in the product line** is read as Langfuse traces of each
  run, not as application logs. Comment site: `src/advisor/tracing.py`.
- **"guardrails beyond a placeholder seam" are out of scope** (intent) is
  read as: the seam is real and tested (B12), the checks always allow.
  Comment site: `src/advisor/guardrails.py`.
- **"green on a fresh clone"** (intent Outcome) is read as: after
  `uv sync --frozen` (B22); the kit's own "no `npm install`" stays true.
  Comment site: `package.json` has no comments, so in `CLAUDE.md` →
  "Commands".

## Acceptance criteria

- **AC1** (B1): `docs/decisions/0001-stack.md` exists and records each
  stack choice with a reason and the owner's four answers. *Proof:*
  reviewer reads it.
- **AC2** (B2, B3): the committed catalogue loads; a fixture with each kind
  of defect (missing field, wrong type, duplicate id, unknown category)
  fails with a message naming product and field. *Proof:*
  `tests/test_catalogue.py`.
- **AC3** (B4): filters combine with AND, keywords are case-insensitive and
  all-must-match, sort is price then id, `limit` is clamped, no match is
  `[]`. *Proof:* `tests/test_catalogue.py`.
- **AC4** (B5, B8): with a fake `ModelClient` scripted as tool call →
  final text, the agent runs `search_products` with the given arguments,
  sends the result back, and returns the final text. *Proof:*
  `tests/test_agent.py`.
- **AC5** (B9, B10): a fake that never stops calling tools gets the
  fallback after 5 turns; an unknown tool or bad arguments yield an error
  tool result, not an exception. *Proof:* `tests/test_agent.py`.
- **AC6** (B5): no module outside `src/advisor/models/` imports
  `anthropic`. *Proof:* a test that scans imports
  (`tests/test_boundaries.py`).
- **AC7** (B6, B7): unknown provider and missing key each exit 1 with the
  stated message and make no network call. *Proof:* `tests/test_cli.py`.
- **AC8** (B12): a blocking `check_input` or `check_output` (patched in the
  test) yields the refusal and skips the agent / replaces the answer;
  the default checks allow. *Proof:* `tests/test_guardrails.py`.
- **AC9** (B13, B14): blank question exits 2 with usage; a fake that raises
  exits 1 with the unavailable message and no traceback. *Proof:*
  `tests/test_cli.py`.
- **AC10** (B15, B16, B17): with tracing off, no Langfuse client is
  created; with a fake tracer, one run records the expected observations
  in order; a tracer that raises does not change answer or exit code.
  *Proof:* `tests/test_tracing.py`.
- **AC11** (B20, B21): `npm run verify` runs all five steps and fails when
  any fails; a test that opens a socket fails. *Proof:* reviewer re-runs
  `npm run verify`, and mutates one step (e.g. a lint error) to see it go
  red; `tests/test_no_network.py` or the conftest fixture's own test.
- **AC12** (B22): a fresh worktree from `npm run spawn -- 1` passes
  `npm run verify`. *Proof:* the implementer's worktree itself, re-run by
  the coordinator.
- **AC13** (B23–B26): `CLAUDE.md` → "Architecture", `CORE_CODE`,
  `REVIEW-POLICY.md` paths and `README.md` say what B23–B26 say;
  `npm run test:kit` is green. *Proof:* reviewer reads; `npm run verify`.
- **AC14** (B11, B13, B15, B18; live): the owner starts Langfuse with the
  README steps, runs `uv run advisor "I need noise-cancelling headphones
  under 200 euros"` with a real key, gets an answer naming catalogue
  products by name and id, and sees one trace with the generation(s), the
  tool call and both checks in the Langfuse UI. *Proof:* **live check** by
  the owner.

## Non-functional

- **Boundaries:** pure, tested logic in `catalogue.py`, `agent.py`,
  `guardrails.py`; I/O in `models/<provider>.py`, `tracing.py`, `config.py`,
  `cli.py`. `cli.py` wires them together and holds no logic worth a
  `CORE_CODE` entry.
- **Data:** synthetic only. No personal data is collected; the question
  typed at the CLI goes to the model provider and, if tracing is on, to the
  local Langfuse, which keeps it until its volumes are removed. No secret
  in the repo, fixtures, or logs.
- **Model use:** one tool (`search_products`), at most 5 model turns per
  question, a small model by default; a live run should cost at most a few
  cents. The prompt is in `src/advisor/prompts/system.md`. When the model is
  down: B14. When it is wrong: out of scope (the eval suite is a later
  intent).
- **Autonomy:** the agent only answers. It writes nothing anywhere except
  traces to the self-hosted Langfuse.

## Out of scope

Advice quality and prompt tuning; the evaluation suite and datasets; any
real guardrail logic; multi-turn conversations; an HTTP API or UI; a second
model adapter; deployment, CI and release; embeddings.

## Assumptions I made

- **Anthropic is the one adapter shipped**, and the default model is its
  small, inexpensive tier; the exact model id is the plan's, checked
  against current docs.
- **The catalogue size (25–40) and categories** are mine.
- **Turn limit 5, `limit` 1–10, flush wait ≤ 5 s, and the fallback and
  refusal wordings** are mine.
- **`mypy --strict`** rather than `pyright`: it installs through `uv`
  without a Node-downloaded binary.
- **No pytest plugin for blocking the network** (B21): a fixture in
  `conftest.py` does it, avoiding a dependency.
- **Langfuse Python SDK** version and its integration style (decorators vs
  explicit spans) are left to the plan, which must keep the tracer behind
  `tracing.py` so tests can fake it.
- **Single-question CLI**, no conversation memory between runs.
