# 0001 — Stack: Python, uv, Langfuse (self-hosted)

Status: accepted with intent §1 (2026-11-09). Spec: `intents/1-stack-and-skeleton/spec.md`.

## Decision

| Choice | Decision | Reason |
| --- | --- | --- |
| Language | Python >= 3.12 | The agent, evaluation and tracing ecosystems (model SDKs, Langfuse SDK, eval libraries) are Python-first; the owner's intended stack. |
| Package manager | `uv` (`pyproject.toml` + committed `uv.lock`) | One fast tool for the venv, locked installs (`uv sync --frozen`) and running commands; a fresh worktree is reproducible. |
| Lint and format | `ruff` (`ruff check`, `ruff format --check`) | One tool for both, no plugin zoo. |
| Types | `mypy --strict` on `src/advisor` | Installs through `uv` with no extra binary (pyright would need a Node download). Tests are type-checked leniently. |
| Tests | `pytest`, with a session-wide guard that fails any socket connect | No network in the suite (spec B21) without another dependency. |
| Model provider | Provider-agnostic: an internal `ModelClient` protocol, one shipped Anthropic adapter, plus a scripted fake | Keeps the dependency count and tracing surface small; the fake proves the seam; a second adapter is a small later intent. Not LiteLLM. |
| Default model | `claude-haiku-5-5`, overridable with `ADVISOR_MODEL` | A small, inexpensive model: a live run costs a few cents. |
| Tracing | Langfuse, self-hosted with the v3 docker-compose in `infra/langfuse/` (web, worker, Postgres, ClickHouse, Redis, MinIO), bound to localhost | Data stays on the owner's machine. Started by hand for live runs; the suite never needs it; tracing is off unless the three `LANGFUSE_*` variables are set. |
| Entry point | CLI first (`uv run advisor "<question>"`) | An HTTP API is a later intent. |
| Catalogue search | A structured filter tool (`search_products`) over a small committed JSON catalogue | Deterministic, testable, no embeddings. |
| One check | `npm run verify` = kit tests, then `ruff check`, `ruff format --check`, `mypy`, `pytest` | The kit's single-command rule; `npm run setup:worktree` (`uv sync --frozen`) installs the product's dependencies. |

## The owner's four answers (2026-11-09, spec question round)

1. Model provider: **provider-agnostic**.
2. Langfuse hosting: **compose file in repo**, v3, started by hand for live runs; tracing off when no keys are set.
3. Entry point: **CLI first**; an HTTP API is a later intent.
4. Catalogue search: **structured filter tool** over a small committed JSON catalogue.

## Consequences

- The Langfuse SDK major (v5 at the time of writing) is pinned by `uv.lock`;
  all of its use is inside `src/advisor/tracing.py`, and the Anthropic SDK is
  used only in `src/advisor/models/anthropic_model.py` (a test enforces both).
- Node stays a kit-only requirement; the product needs Python and `uv`.
