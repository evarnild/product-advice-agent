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
and `model:<name>`.

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

## Check

```
npm run verify        # kit tests, then ruff check, ruff format --check, mypy, pytest
npm run check:intent  # does this branch match its intent?
npm run queue         # every intent by status, generated from metadata.yml
```

`verify` calls `uv run`, so run `npm run setup:worktree` (or `uv sync`)
first. The suite never calls a model or Langfuse; any socket connect fails
the test.
