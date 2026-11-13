# product-advice-agent

A small product-advice agent for a synthetic electronics catalogue, with evaluation, tracing and guardrails.

Run with the AI-native SDLC from the start. See [`sdlc.md`](sdlc.md) for how
a change moves from intent to merge, [`OVERVIEW.md`](OVERVIEW.md) for the
snapshot, and `npm run queue` for what is queued. The stack decision is in
[`docs/decisions/0001-stack.md`](docs/decisions/0001-stack.md).

## Install

Needs [uv](https://docs.astral.sh/uv/) (Python >= 3.12 is fetched if absent)
and Node >= 22 for the kit's scripts.

```
uv sync            # or: npm run setup:worktree  (uv sync --frozen)
```

## Configure

```
cp .env.example .env     # then edit; .env is gitignored
```

With nothing set, the advisor answers through a local model in
[Ollama](https://ollama.com), with no key and no API cost:

1. Install Ollama and make sure it is running (the Ollama app, or
   `ollama serve`).
2. `ollama pull qwen3:8b` (about 5 GB).
3. `uv run advisor "..."` (see Run).

The question stays on your machine apart from traces to your own Langfuse.
`ADVISOR_OLLAMA_URL` (default `http://localhost:11434`, must be `http://` or
`https://`) says where Ollama is; if you point it at another machine, your
questions go there. `OLLAMA_HOST` is not read.

To use Claude instead, set `ADVISOR_MODEL_PROVIDER=anthropic` and
`ANTHROPIC_API_KEY` (model default `claude-haiku-5-5`, override with
`ADVISOR_MODEL`). **A `.env` copied from the old `.env.example` pins
`ADVISOR_MODEL_PROVIDER=anthropic` and so keeps using Claude: remove that
line to get the local default.**

Tracing is on only when `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY` and
`LANGFUSE_SECRET_KEY` are all set. Every trace is tagged `provider:<name>`
and `model:<name>`. Traces from `advisor-eval` also carry `eval`, `run:<stamp>`
and `case:<id>` (see "Evaluating answers").

If the run cannot reach Ollama it prints `Ollama is not reachable at <url>.
Start Ollama (the Ollama app, or "ollama serve") and try again.` If the model
is not pulled it prints `Model '<model>' is not available in Ollama. Run:
ollama pull <model>`. Both exit 1.

### Comparing providers

Run these 5 questions once with the default (Ollama) and once with
`ADVISOR_MODEL_PROVIDER=anthropic`, with Langfuse tracing on:

1. I need noise-cancelling headphones under 200 euros.
2. Which phone with at least 128 GB of storage is the cheapest one in stock?
3. Compare the laptops you have for someone who edits video.
4. Do you have a smartwatch with GPS under 150 euros?
5. I want a gift for a gamer, budget 80 euros.

In the Langfuse UI, filter traces by tag `provider:ollama` and then
`provider:anthropic` and read the answers, model names, token usage and
latency side by side. Nothing is committed.

## Run

```
uv run advisor "I need noise-cancelling headphones under 200 euros"
```

Prints the answer and exits 0. A blank question exits 2 with a usage line;
another model or network failure prints "The advisor is unavailable right now."
and exits 1 (`--debug` shows the traceback).

## Trace to a local Langfuse (optional)

```
cp infra/langfuse/.env.example infra/langfuse/.env   # set every secret (see the file)
docker compose -f infra/langfuse/docker-compose.yml up -d
```

Open http://localhost:3000, create an account, an organisation and a
project, create API keys, and put `LANGFUSE_HOST=http://localhost:3000`
and the two keys in the root `.env`. Each run then appears as one trace
(input check, model calls with token usage, tool calls, output check).
All ports are bound to 127.0.0.1. The stack is Langfuse v4 with every image
pinned to an exact version. `docker compose ... down -v` removes the stored
traces. The compose file needs `infra/langfuse/.env` to exist; to only
check that it parses, run `docker compose --env-file infra/langfuse/.env.example
-f infra/langfuse/docker-compose.yml config -q`.

**Coming from the v3 stack.** v4 replaces v3; it is not upgraded in place.
Run `docker compose -f infra/langfuse/docker-compose.yml down -v` first (this
deletes the v3 traces), then `up -d`, and create the account, project and
keys again. The traces are local test data, and the in-place path needs the
latest v3, finished background migrations and a backup, with no way back. If
you have data to keep, follow
https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4.

**Updating a pin.** Change the tag in `infra/langfuse/docker-compose.yml`,
then run `npm run verify` (`tests/test_compose.py` checks the pins).
`npm run check:pins` (needs Docker and network; not part of verify) shows
whether each pin still resolves, and the newer MinIO digest.

## Evaluating answers

```
uv run advisor-eval                       # all cases in evals/cases.jsonl
uv run advisor-eval --only nc-headphones-under-200,gps-watch
uv run advisor-eval --cases other.jsonl --report-dir some/dir --debug
uv run advisor-eval --provider ollama     # local model (qwen3:8b unless --model)
uv run advisor-eval --provider anthropic  # claude-haiku-5-5 unless --model; needs ANTHROPIC_API_KEY
```

`--provider` and `--model` win over `ADVISOR_MODEL_PROVIDER` and
`ADVISOR_MODEL`; `--provider` without `--model` uses that provider's default
model. An Anthropic run **costs money** and needs `ANTHROPIC_API_KEY`.

The suite asks each question in `evals/cases.jsonl` once, through the same
agent as `advisor`, and scores the answer with fixed checks. There is no
judge model. **A run uses a real model**: the local one by default (slow on
CPU, minutes for the 15 cases), or Anthropic when `ADVISOR_MODEL_PROVIDER` is
set (cents per run). It reads the same environment and `.env` as `advisor`.
When `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are all
set, each case is also one Langfuse trace (the same spans as an `advisor`
run), tagged `eval`, `provider:<name>`, `model:<name>`, `run:<stamp>` and
`case:<id>`. The stamp is the run's start, as in the report's filename
`evals/runs/<stamp>-<provider>.json`. In the Langfuse UI, filter on tag `eval`,
then on `run:<stamp>` from the report's filename. Tracing never changes the
scores, output or report (apart from `duration_s`); with Langfuse down, a run
takes up to 5 s longer per case.

Each case prints `PASS`, `FAIL` (with the failing reasons) or `ERROR` (the
model call failed), then a total. A report with the answers, search calls and
checks goes to `evals/runs/<UTC time>-<provider>.json` (gitignored). Exit
code 0 when every case passes, 1 when any fails or errors, 2 for a bad case
file or bad arguments.

Checks (a product is cited by its id, `P-` and three digits, as the prompt
asks):

- **grounded**: every cited id is in the catalogue.
- **prices**: each cited product's price appears as a number (not which
  product it sits next to); a cited out-of-stock product needs none when
  the answer says "out of stock".
- **expected** / **forbidden**: the case's `expect_ids` are cited, its
  `forbid_ids` are not.
- **declines** (off-topic cases): no product id is cited, or the answer is
  the refusal text. Wording is not judged.
- **stock**: a cited out-of-stock product comes with "out of stock".
- **search** (when the case has `expect_search`): at least one
  `search_products` call matched `category`, `max_price`, `min_price`,
  `in_stock_only` and `keywords_any`.

The suite reports; it does not gate anything, and `npm run verify` never runs
it (it tests the scorers and the runner with a scripted fake).

### Error analysis: from questions to failure modes

The first loop of the field guide, on top of the suite. Every command here
that calls a model uses the local one by default and never runs from
`npm run verify`.

```
uv run advisor-analysis generate                     # ~60 questions -> evals/generated.jsonl
uv run advisor-eval --cases evals/generated.jsonl    # a report that keeps every conversation
uv run advisor-analysis view evals/runs/<report>.json   # label them at http://127.0.0.1:5209
uv run advisor-analysis taxonomy evals/labels/<report>.jsonl   # draft failure modes
uv run advisor-analysis counts evals/runs/<report>.json        # the tables
```

1. **generate** asks the model for questions only, one call per cell of
   feature x scenario x persona (two questions a cell, `--count`, `--seed`,
   `--force` to overwrite). Each question comes with a *probe*, the
   `search_products` arguments it expresses, and is kept only if the probe
   fits its scenario against the real catalogue (a "no match" question must
   match nothing, and so on). It prints asked / kept / dropped per scenario.
   Read and edit `evals/generated.jsonl` before you use it. Cases carry an
   optional `dimensions` object (`feature`, `scenario`, `persona`).
2. **advisor-eval** records, per case, the model turns, each tool call with
   the products it returned, and the guardrail checks, plus `prompt_sha256`
   in the report.
3. **view** is a local page (127.0.0.1 only, `--port`): one conversation per
   screen. `p` labels pass, `f` labels fail and moves to the critique box,
   `Enter` saves the critique and goes to the next one, `j` / `k` move on and
   back. A fail needs a critique. Filter by dimension, label or status.
   Every change is saved at once.
4. **Labels** go to `evals/labels/<report name>.jsonl` (committed): one JSON
   line per change with `case_id`, `label` (`pass` or `fail`), `critique`,
   `labelled_at` (UTC), `question` and `answer`. The last line for a
   `case_id` is the current label. Other tools may write the same format.
5. **taxonomy** sends the critiques of the fails to the model in one call and
   writes `evals/taxonomy.draft.json` (not committed). Edit it and save it as
   `evals/taxonomy.json` (committed): `labels` (the labels file it maps),
   `modes` (`id`, `name`, `description`) and `mapping` (failed case id to
   mode ids). Every failed case needs a mode.
6. **counts** prints failed conversations per mode, per mode and dimension,
   and where the automatic status and your label disagree (`--out` also
   writes them to a file). It reports; it changes no check.

No model grades an answer: you label every conversation. Reports stay local
(`evals/runs/`); questions, labels and the taxonomy are committed.

## Check

```
npm run verify        # kit tests, then ruff check, ruff format --check, mypy, pytest
npm run check:intent  # does this branch match its intent?
npm run queue         # every intent by status, generated from metadata.yml
```

`verify` calls `uv run`, so run `npm run setup:worktree` (or `uv sync`)
first. The suite never calls a model or Langfuse; any socket connect fails
the test.
