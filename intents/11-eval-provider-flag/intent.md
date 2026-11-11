<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §11 — Choose the eval's model provider with a flag on `advisor-eval`

**Type:** adjustment
**Originator:** me (the owner)
**Source:** intents/8-offline-evals (the owner's live check of `advisor-eval`)

## Problem

"Running eval for ollama or anthropic should be possible using a parameter
passed to advisor-eval." Today `advisor-eval` takes its provider and model
only from the environment or `.env` (`ADVISOR_MODEL_PROVIDER`,
`ADVISOR_MODEL`, via `load_settings`). Comparing the two providers means
editing `.env` or setting and clearing environment variables between runs,
and the main checkout's `.env` pins `anthropic`, so a run there silently
uses Anthropic unless the owner remembers to change it.

## Outcome

- `uv run advisor-eval --provider ollama` and `uv run advisor-eval
  --provider anthropic` run the suite against that provider, whatever
  `ADVISOR_MODEL_PROVIDER` says in the environment or `.env`; the total
  line and the report name show the provider used.
- `--model <name>` overrides the model the same way; without it, the
  provider's default model applies (`qwen3:8b`, `claude-haiku-5-5`) whenever
  `--provider` is given, even if it names the provider the environment
  already selects; without `--provider`, `ADVISOR_MODEL` as today.
  *(Amended 2026-11-11, owner: "a", review round 1's Needs decision.)*
- Without the flags, behaviour is unchanged. An unknown `--provider` value
  exits 2 with the known providers listed (argparse `choices`); `--provider
  anthropic` without `ANTHROPIC_API_KEY` exits 2 with today's message.
- Tests in `tests/test_evals_run.py` (fake client factory, no network)
  prove the flag wins over the environment, the default model per provider,
  and the error cases. `README.md` → "Evaluating answers" shows both runs.

## Constraints

- Only `advisor-eval` changes; `uv run advisor` (the CLI) and `config.py`'s
  defaults stay as they are.
- No new dependency. No change to the scorers (`cases.py`, `score.py`), so
  no core code.
- Tests use the fake client factory; `verify` makes no model call. An
  Anthropic run costs money and needs the owner's key: only the owner runs
  it, never `verify` or an agent.
- No secret in the repo, the report or the output (the key is never printed).
- Depends on §8: built on `feat/8-offline-evals` after it ships to `main`.

## Type-specific questions

### Adjustment
- **Exactly what changes:** `src/advisor/evals/run.py` gains `--provider
  {ollama,anthropic}` (choices from `KNOWN_PROVIDERS`) and `--model`; the
  values are layered over `load_settings`'s result before the key check
  and `make_client`.
- **Blast radius:** `src/advisor/evals/run.py`, `tests/test_evals_run.py`,
  `README.md` (3 files, about 50 lines). No core code; `run.py` is not on
  the live-check rule-1 path list.

## Assumptions I made

- A `--model` flag comes with `--provider`, so a run is fully set from the
  command line; drop it if you want only the provider.
- When `--provider` is given without `--model`, the provider's default model
  applies even if `ADVISOR_MODEL` is set (that variable usually belongs to
  the `.env` provider, e.g. `claude-haiku-5-5`, and would be wrong for
  Ollama).
- The flags apply to `advisor-eval` only, not to `uv run advisor`.
- An adjustment, not a feature: it stays within 3 files and about 50 lines
  with no core code. If the owner wants the same flag on `advisor` too, it
  becomes a feature (the CLI is Reviewed tier and owes a live check).
