<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §2 spec — Locally run model (Ollama) as the advisor's default

Accepted intent: [intent.md](intent.md)
Written against `main` at `21578e4`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Owner's decisions

| Question | Owner's answer | When |
| --- | --- | --- |
| Why a local model | No API cost; privacy and offline use; prove the provider-agnostic seam; compare quality | intent round, 2026-11-10 |
| Runtime | **Ollama** | intent round |
| Default provider | **Local by default**; Anthropic stays opt-in | intent round |
| Default model size (owner's machine: RTX 3060 Laptop 6 GB VRAM, 16 GB RAM, Ollama 0.40.9 installed, no model pulled) | **~8B, partly on CPU**: better advice and tool calls, slower | spec round, 2026-11-10 |
| Side-by-side comparison | **Langfuse tags only**: runs are tagged by provider and compared in the Langfuse UI; nothing committed | spec round |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/2-local-model/intent.md` | Outcome: "with **no environment variables set** and no API key [the advisor] answers through the local model"; "`ADVISOR_MODEL_PROVIDER=anthropic` still selects Claude, unchanged"; a clear message "that says what to start or pull". Out of scope: "the evaluation suite and any scoring, prompt tuning for quality, … running Ollama in the repo's Docker Compose, other local runtimes …, and streaming." |
| `docs/decisions/0001-stack.md` | "Provider-agnostic: an internal `ModelClient` protocol, one shipped Anthropic adapter, plus a scripted fake … a second adapter is a small later intent. Not LiteLLM."; "Default model \| `claude-haiku-5-5`". §2 changes the default, so this record gets a superseding decision. |
| `CLAUDE.md` → "Architecture" | "A new provider is a new `models/<provider>.py`, a line in `PROVIDER_KEY_ENV` and `make_client`, and its own tests."; "Provider and tracing SDKs are imported in exactly one module each … (`tests/test_boundaries.py` enforces it)."; "Never build the real adapter or Langfuse client in a test without patching it." |
| `CLAUDE.md` → "Conventions that already apply" | "Model calls and external APIs are faked or recorded in tests, never called live from the suite."; "No new dependency arrives without a line in the intent's `plan.md` saying why." |
| `src/advisor/models/__init__.py` | `PROVIDER_KEY_ENV: dict[str, str] = {"anthropic": "ANTHROPIC_API_KEY"}` and `KNOWN_PROVIDERS: tuple[str, ...] = tuple(PROVIDER_KEY_ENV)`: today a provider is known only if it has a key variable. |
| `src/advisor/models/__init__.py` | `def make_client(provider: str, model: str, api_key: str) -> ModelClient`: the factory takes a key for every provider. |
| `src/advisor/config.py` | `DEFAULT_PROVIDER = "anthropic"`, `DEFAULT_MODELS: dict[str, str] = {"anthropic": "claude-haiku-5-5"}`. |
| `src/advisor/cli.py` | `if not api_key: return _fail(f"Missing {settings.key_variable}: set it in the environment or in .env.")`, and every other failure → `UNAVAILABLE = "The advisor is unavailable right now."` |
| `.env.example` | `ADVISOR_MODEL_PROVIDER=anthropic` is set, not commented, so a `.env` copied from it pins Anthropic. |
| `src/advisor/agent.py` (`search_tool` → `run`) | `unknown = set(args) - set(_SEARCH_SCHEMA["properties"])` → `ToolError("unknown argument(s): …")`, answered to the model as an error result (§1 B10). |
| `src/advisor/tracing.py` | `LangfuseTracer.begin` starts the root observation `advisor-run`; `generation` records `model` and `usage_details`. |
| Ollama API docs (https://github.com/ollama/ollama/blob/main/docs/api.md, "Generate a chat completion") | `POST /api/chat` with `model`, `messages`, `tools`, `stream`, `think`, `options`; a response carries `message.content`, `message.tool_calls[].function.{name, arguments}` (arguments as an object, **no call id**), `prompt_eval_count` and `eval_count`; tool results go back as messages with `role: "tool"`. A model that is not pulled gives HTTP 404 with an `error` text. Default address `http://localhost:11434`. |

## Behaviour

**Provider and defaults**

- **B1.** A provider named `ollama` exists. With `ADVISOR_MODEL_PROVIDER`
  unset or empty, the provider is `ollama`; with `ADVISOR_MODEL` unset, the
  model is the Ollama default model named in config (B2).
  `ADVISOR_MODEL_PROVIDER=anthropic` selects the Anthropic adapter, whose
  behaviour, default model and key rule (§1 B6, B7) are unchanged.
- **B2.** The default Ollama model is an ~8B instruct model with tool support
  in the Ollama library, `qwen3:8b` unless the plan, checked against the
  library at the time, names a better tool-capable model of that size. Its
  id is in one place in config.
- **B3.** The unknown-provider message (§1 B6) lists both providers.

**Keys and addresses**

- **B4.** The missing-key rule (§1 B7) applies only to providers that need a
  key. With provider `ollama`, no key variable is required, read or sent,
  even when `ANTHROPIC_API_KEY` is set.
- **B5.** The Ollama address comes from `ADVISOR_OLLAMA_URL`, default
  `http://localhost:11434`. A value without a scheme, or with one other than
  `http`/`https`, stops the run with exit code 1 and a message naming the
  variable, before any network call.

**The adapter (`src/advisor/models/ollama_model.py`)**

- **B6.** The adapter implements `ModelClient` over `POST
  <ADVISOR_OLLAMA_URL>/api/chat`, non-streaming, with the system prompt as a
  `system` message, the conversation, and the tools as function tools
  (name, description, the same JSON-Schema parameters). It sends `think:
  false` and a context window (`options.num_ctx`) of 8192 tokens.
- **B7.** It maps the response to a `ModelTurn`: `message.content` (if not
  blank) as text, each `message.tool_calls[]` entry as a `ToolCall`, usage
  from `prompt_eval_count` and `eval_count` (0 when absent), and the model
  name from the response. Ollama gives no call id, so the adapter makes one
  per call, unique within the run, and sends each tool result back as a
  `role: "tool"` message carrying that call's tool name.
- **B8.** Tool-call arguments that arrive as a JSON string are parsed. When
  they cannot be parsed into an object, the `ToolCall` carries them as
  `{"_unparsable_arguments": "<raw text>"}`. The agent's existing check
  ("unknown argument(s)") then answers the model with an error result and
  the turn counts (§1 B9, B10). No change to `agent.py`.
- **B9.** A model call that has not finished after **180 s** fails as a
  model failure (§1 B14).

**Failure messages (CLI)**

- **B10.** Ollama not reachable (connection refused, DNS failure, connect
  timeout) exits 1 with: `Ollama is not reachable at <url>. Start Ollama
  (the Ollama app, or "ollama serve") and try again.` `<url>` is the
  configured `ADVISOR_OLLAMA_URL` without any user or password part.
- **B11.** The model is not available (HTTP 404 naming the model) exits 1
  with: `Model '<model>' is not available in Ollama. Run: ollama pull
  <model>`.
- **B12.** Any other Ollama failure (other HTTP error, malformed response,
  the B9 timeout) gives §1 B14: "The advisor is unavailable right now.",
  exit 1, traceback only with `--debug`. None of the B10–B12 messages
  includes a stack trace without `--debug`.
- **B13.** The provider-specific messages of B10 and B11 reach the CLI
  through the `models` package's own error types, so `cli.py` imports no
  HTTP library and no provider module.

**Tracing**

- **B14.** Every trace carries the tags `provider:<provider>` and
  `model:<model>` (as configured for the run), for every provider, so
  Anthropic and Ollama runs of the same question can be filtered and set
  side by side in the Langfuse UI.
- **B15.** An Ollama generation is recorded like an Anthropic one: model
  name and input/output token usage. No cost is attached to it.

**Privacy**

- **B16.** With provider `ollama`, a run opens network connections only to
  `ADVISOR_OLLAMA_URL`, and to `LANGFUSE_HOST` when tracing is on. The
  `anthropic` SDK is not imported in that run.

**Config, docs and decision**

- **B17.** `.env.example` no longer pins a provider: `ADVISOR_MODEL_PROVIDER`
  and `ADVISOR_MODEL` are commented out with their defaults stated,
  `ADVISOR_OLLAMA_URL` is listed with its default, and `ANTHROPIC_API_KEY`
  is marked as needed only for `anthropic`.
- **B18.** `README.md` gives the local setup (install Ollama, `ollama pull
  <default model>`, run with no key), how to switch to Anthropic, the two
  B10/B11 messages, and the comparison: a list of 5 fixed questions to run
  once per provider and how to compare them in Langfuse by the B14 tags. It
  warns that a `.env` copied from the old example still pins `anthropic`.
- **B19.** `docs/decisions/0002-local-model.md` records the local default,
  Ollama, the model and why (hardware, owner's answers), and that it
  supersedes the "Model provider" and "Default model" rows of 0001. 0001
  gets a one-line pointer to it. `CLAUDE.md` → "Commands" stops saying the
  run "needs ANTHROPIC_API_KEY".

**Tests and boundaries**

- **B20.** The adapter is tested only through an injected HTTP transport
  that serves recorded or hand-written Ollama responses. No test opens a
  socket (§1 B21 stays), and `npm run verify` does not need Ollama.
- **B21.** `tests/test_boundaries.py` also asserts that the HTTP library the
  adapter uses is imported only by `models/ollama_model.py`.

## Interpretations

- **"no environment variables set"** (intent Outcome) is read as: none of
  the advisor's variables are set, and no `.env` supplies them. An
  existing `.env` that pins `ADVISOR_MODEL_PROVIDER=anthropic` keeps
  winning. That is the variable doing its job, so it is documented (B18)
  and not overridden. Comment site: `src/advisor/config.py`
  (`DEFAULT_PROVIDER`).
- **"A documented, repeatable side-by-side run … records how the two
  compare"** (intent Outcome) is narrowed by the owner's "Langfuse tags
  only" answer. "Documented, repeatable" is the README's 5 fixed questions
  (B18). "Records" is the tagged traces in the local Langfuse (B14). No
  result is committed. Comment site: `src/advisor/tracing.py` (tags).
- **"a clear message that says what to start or pull"** (intent Outcome) is
  read as two dedicated messages (B10, B11). Every other local failure keeps
  §1's generic message, so the CLI does not grow a message per HTTP status.
  Comment site: `src/advisor/models/ollama_model.py` (error mapping).
- **`OLLAMA_HOST` is not reused.** The Ollama server reads `OLLAMA_HOST` as
  its bind address (often `0.0.0.0`), which is not a valid address to
  connect to. The advisor uses its own `ADVISOR_OLLAMA_URL`. Comment site:
  `src/advisor/config.py`.
- **"Provider-agnostic, … not LiteLLM"** (0001) is kept. The second adapter
  is hand-written over Ollama's native API, not the `ollama` package and
  not the OpenAI-compatible `/v1` endpoint. The native API reports token
  counts and takes `think`/`num_ctx` directly. Comment site:
  `src/advisor/models/ollama_model.py`.
- **"zero cost"** (intent Outcome) is read as: no cost is attached (B15).
  Langfuse prices a generation only when its model name matches a price
  definition, and a local model's name does not. Comment site:
  `src/advisor/tracing.py`.

## Acceptance criteria

- **AC1** (B1, B2, B3): with an empty environment, settings give provider
  `ollama` and the default Ollama model. `anthropic` still gives
  `claude-haiku-5-5`. An unknown provider's message lists both. *Proof:*
  `tests/test_config.py`, `tests/test_cli.py`.
- **AC2** (B4, B16): with provider `ollama` and no key, the CLI runs (with a
  fake client factory) and the factory receives no key. With
  `ANTHROPIC_API_KEY` set, the key is still not passed. With provider
  `anthropic` and no key, §1's missing-key message is unchanged. *Proof:*
  `tests/test_cli.py`.
- **AC3** (B5): `ADVISOR_OLLAMA_URL` defaults to `http://localhost:11434`. A
  value without a scheme, or with `ftp://`, exits 1 naming the variable and
  makes no request. *Proof:* `tests/test_config.py` / `tests/test_cli.py`.
- **AC4** (B6, B7): against a fake transport, the adapter sends one `POST
  /api/chat` whose body has the system message, the conversation, the tool
  as a function tool, `stream: false`, `think: false` and `options.num_ctx:
  8192`. A recorded tool-call response becomes a `ModelTurn` with
  generated, distinct call ids, the arguments and the usage. A follow-up
  request carries the tool result as a `role: "tool"` message with the tool
  name. A text response becomes final text. *Proof:*
  `tests/test_ollama_model.py`.
- **AC5** (B8): string arguments are parsed. Unparsable arguments yield
  `{"_unparsable_arguments": …}`, and `run_agent` with that call answers
  with an error tool result and goes on. *Proof:*
  `tests/test_ollama_model.py`, `tests/test_agent.py`.
- **AC6** (B9–B13): a transport that raises a connect error gives the B10
  message with user/password stripped from the URL. A 404 "model not found"
  gives the B11 message. A 500, a malformed body or a read timeout gives
  "The advisor is unavailable right now." There is no traceback without
  `--debug`. The timeout is 180 s. *Proof:* `tests/test_ollama_model.py`,
  `tests/test_cli.py`.
- **AC7** (B14, B15): with a fake Langfuse client, a run's root observation
  carries `provider:<p>` and `model:<m>` tags for both providers. An Ollama
  generation records model and usage and no cost. *Proof:*
  `tests/test_tracing.py`.
- **AC8** (B13, B20, B21): the boundaries test passes with the new
  assertion, `cli.py` imports no HTTP library, and `npm run verify` is
  green with no Ollama installed (the reviewer re-runs it). *Proof:*
  `tests/test_boundaries.py`, `npm run verify`.
- **AC9** (B17, B18, B19): `.env.example`, `README.md`,
  `docs/decisions/0002-local-model.md`, the 0001 pointer and `CLAUDE.md`
  say what B17–B19 say. *Proof:* reviewer reads.
- **AC10** (B1, B2, B10, B11, B14, B16; live): the owner, with Ollama
  running and the default model pulled, and with
  `ADVISOR_MODEL_PROVIDER`/`ANTHROPIC_API_KEY` unset in the shell and
  `.env`, runs `uv run advisor "I need noise-cancelling headphones under
  200 euros"`. The answer names catalogue products by name and id. With
  Ollama stopped, the same command prints the B10 message. With
  `ADVISOR_MODEL=nonexistent:1b`, it prints the B11 message. With tracing
  on, the owner runs the README's 5 questions once with each provider and
  can filter both sets by the `provider:` tag in the Langfuse UI. *Proof:*
  **live check** by the owner.

## Non-functional

- **Boundaries:** all Ollama code is in `src/advisor/models/ollama_model.py`.
  The registry change (keyless providers, the factory signature) is in
  `src/advisor/models/__init__.py`, and the error types are in
  `models/base.py`. All of these are `CORE_CODE`. `config.py`, `cli.py` and
  `tracing.py` change only in wiring, messages and tags. `agent.py`,
  `catalogue.py`, `guardrails.py` and `prompts/system.md` do not change.
- **Data:** synthetic catalogue only. With the local default, the question
  stays on the machine apart from traces to the self-hosted Langfuse. If
  the owner points `ADVISOR_OLLAMA_URL` elsewhere, it goes there, and the
  README says so. No key is needed or logged for `ollama`.
- **Model use:** the same single `search_products` tool, at most 5 turns
  (§1 B9), the shared prompt. Latency budget: an ~8B model partly offloaded
  to the CPU on this machine is expected to take tens of seconds per answer,
  plus the model load on the first run. The 180 s timeout bounds one call.
  Cost is zero per question. When Ollama is down or the model is missing:
  B10/B11. When the model is wrong (bad tool calls, invented products):
  B8 and the turn limit contain bad calls. Wrong advice is the eval suite's
  and the guardrails' concern, not this intent's.
- **Autonomy:** unchanged. The agent only answers.

## Out of scope

The evaluation suite and any scoring; prompt changes or per-provider prompts;
streaming; Ollama in the repo's Docker Compose; LM Studio, llama.cpp, vLLM
or the OpenAI-compatible endpoint; pulling models automatically; GPU and
driver setup beyond the README steps; changing `agent.py`'s turn limit or
validation; a committed comparison report.

## Assumptions I made

- **Native `/api/chat` over plain HTTP, with `httpx` as the client.**
  `httpx` is already in `uv.lock` (as an `anthropic` dependency and in the
  dev group) and supports an injected transport for tests. It becomes a
  direct runtime dependency, and the plan carries the line saying why. The
  `ollama` package is not added.
- **`qwen3:8b` as the default**, chosen on the owner's "~8B" answer and
  hardware. The plan re-checks the Ollama library, and the live check
  confirms it answers with tool calls. If it does not, the default changes
  in config without a new intent.
- **`think: false`**: Qwen3-style thinking would multiply the latency on
  this hardware. **`num_ctx` 8192**: enough for the prompt, 5 turns and
  tool results, and stops Ollama silently truncating at a smaller default.
- **The 180 s timeout, the wording of B10 and B11, the 5 comparison
  questions and the tag format** are mine.
- **The prompt stays shared and unchanged.** If the live check shows the
  local model ignoring it, a prompt change is a follow-up adjustment, not
  part of §2. This keeps §2 off the `prompts/` Reviewed path.
- **No pre-flight check** (for example `GET /api/tags`) before the run. The
  first `/api/chat` reveals both failures, and the trace records the failed
  run like any other.
- **Hardware facts** (RTX 3060 Laptop 6 GB, 16 GB RAM, Ollama 0.40.9, no
  model pulled) were read from this machine during drafting. Running
  `ollama list` to check briefly started the Ollama app, which then shut
  down again.
