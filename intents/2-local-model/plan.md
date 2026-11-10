<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §2 plan — Locally run model (Ollama) as the advisor's default

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

With nothing configured, `uv run advisor "<question>"` answers through a
local `qwen3:8b` in Ollama. The answer goes through a second `ModelClient`
adapter, `src/advisor/models/ollama_model.py`, written by hand over
Ollama's native `/api/chat` with `httpx`.
- A keyless provider runs without any key check.
- Ollama being down, or the model not pulled, each give their own message.
- Traces carry `provider:` and `model:` tags, so Anthropic and Ollama runs
  can be compared in Langfuse.

Anthropic stays one variable away and unchanged. The suite stays offline:
the adapter is tested against `httpx.MockTransport`.

## Risks

- **Tests that pass whatever the code does** (§1 rounds 1–3: the recurring
  class).
  - A mapping test whose fixture already looks like the output, such as
    call ids that happen to be distinct, or arguments already a dict.
  - A request-body test that checks only some keys.
  - Every assertion on a request reads the JSON body the fake transport
    received, field by field. Every response fixture is a recorded-shape
    Ollama body that differs from the expected `ModelTurn` in each mapped
    field.
- **The error mapping is the user-facing surface.** A wrong branch shows
  "unavailable" where "start Ollama" was owed, or the reverse. Each of
  B10–B12 gets its own transport fixture, and `cli` tests assert the exact
  stderr text and exit code.
- **Secrets in a printed URL.** B10 prints the configured URL, which could
  carry `user:password@`. The strip is tested with credentials present.
- **Signature churn.** `make_client` and `ClientFactory` change. Every
  existing `tests/test_cli.py` fake factory must be updated, not deleted, so
  §1's CLI behaviour stays proven. Existing CLI test names stay.
- **The default flips to `ollama`.** Every existing test that relied on the
  `anthropic` default without setting `ADVISOR_MODEL_PROVIDER` (for example
  the missing-key test) must now set it, or it silently tests something
  else.
- **Langfuse tags.** SDK 5.2 has no `update_trace`. Tags are the
  `langfuse.trace.tags` span attribute (`LangfuseOtelSpanAttributes.TRACE_TAGS`)
  or `propagate_attributes(tags=…)`. Which one the server reads on a span
  started with `start_observation` is proven only by the live check. The
  in-memory exporter test proves the attribute is set.
- **Overlap.** §3 (LOW findings) changes `tracing.py` and
  `tests/test_boundaries.py`, and §4 (Langfuse v4) may change `tracing.py`.
  Whichever merges second rebases.
- **Stale line citations:** the lines below were read at `a8c8faf`; re-check
  before editing.

## Verified against the codebase

Re-read on `main` at `a8c8faf`.

- `src/advisor/models/__init__.py:7` — `PROVIDER_KEY_ENV: dict[str, str] = {"anthropic": "ANTHROPIC_API_KEY"}`
- `src/advisor/models/__init__.py:8` — `KNOWN_PROVIDERS: tuple[str, ...] = tuple(PROVIDER_KEY_ENV)`: a provider is known only if it has a key variable.
- `src/advisor/models/__init__.py:15-23` — `make_client(provider, model, api_key)`; lazy `from advisor.models.anthropic_model import AnthropicClient`; else `UnknownProviderError`.
- `src/advisor/models/base.py:17-18` — `class ModelError(Exception)`, the only model error type.
- `src/advisor/models/base.py:30-41` — `ToolCall(id, name, arguments)`, `ToolResult(call_id, content, is_error)`.
- `src/advisor/models/base.py:44-56` — `Message(role, text, tool_calls, tool_results)`; tool results ride on a `user` message.
- `src/advisor/models/anthropic_model.py:55-88` — the adapter shape to mirror (injectable SDK client, `ModelError` wrapping, `ModelTurn` mapping).
- `src/advisor/config.py:17-18` — `DEFAULT_PROVIDER = "anthropic"`, `DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5"}`.
- `src/advisor/config.py:27-33` — `Settings.key_variable` / `api_key()` from `PROVIDER_KEY_ENV` (already `None` for a keyless provider).
- `src/advisor/config.py:47-50` — `load_settings`: `ADVISOR_MODEL_PROVIDER or DEFAULT_PROVIDER`, `ADVISOR_MODEL or DEFAULT_MODELS.get(provider, "")`.
- `src/advisor/cli.py:22` — `UNAVAILABLE = "The advisor is unavailable right now."`
- `src/advisor/cli.py:24` — `ClientFactory = Callable[[str, str, str], ModelClient]`.
- `src/advisor/cli.py:53-56` — unknown provider → message listing `KNOWN_PROVIDERS`.
- `src/advisor/cli.py:59-60` — `if not api_key: return _fail(f"Missing {settings.key_variable}: …")`: stops every keyless provider today.
- `src/advisor/cli.py:66-74` — `client_factory(settings.provider, settings.model, api_key)`, `make_tracer(full_env)`, `answer_question(...)`, `except Exception` → `UNAVAILABLE` (traceback only with `--debug`).
- `src/advisor/agent.py:95-97` — `unknown = set(args) - set(_SEARCH_SCHEMA["properties"])` → `ToolError("unknown argument(s): …")`: what B8's `_unparsable_arguments` relies on.
- `src/advisor/agent.py:134-148` — `_execute` returns `ToolResult` with content `error: …` and `is_error=True` on failures.
- `src/advisor/agent.py:151-166` — `run_agent` passes the full message list each turn and records `tracer.generation(reply.model, reply.usage, …)`.
- `src/advisor/tracing.py:16` — `from langfuse import Langfuse` (module level).
- `src/advisor/tracing.py:79-82` — `LangfuseTracer.begin` → `start_observation(name="advisor-run", as_type="span", input=question)`.
- `src/advisor/tracing.py:97-104` — generation records `model` and `usage_details`, no cost.
- `src/advisor/tracing.py:163-177` — `make_tracer(env)`; `SafeTracer(LangfuseTracer(client))`.
- `langfuse` 5.2.0 in `.venv`: `LangfuseOtelSpanAttributes.TRACE_TAGS == "langfuse.trace.tags"`; `langfuse.propagate_attributes(*, tags=…, …)` exists; `LangfuseSpan` has no `update_trace`.
- `httpx` 0.28.1 in `uv.lock` (dev group and transitive via `anthropic`); `pyproject.toml:6-10` runtime deps are `anthropic`, `langfuse`, `python-dotenv`.
- `tests/conftest.py:12-23` — session-wide socket block (`connect`, `connect_ex`, `create_connection`). `httpx.MockTransport` opens no socket.
- `tests/test_boundaries.py:24-29` — the AST import scan; `anthropic` only in `models/anthropic_model.py`, `langfuse` only in `tracing.py`.
- `tests/test_tracing.py:94-105` — `_real_tracer()` with `InMemorySpanExporter`: the place to assert tags.
- `.env.example:4` — `ADVISOR_MODEL_PROVIDER=anthropic` uncommented; `:8` `ANTHROPIC_API_KEY=…`.
- `docs/decisions/0001-stack.md:14-15` — "Model provider" and "Default model" rows.
- `CLAUDE.md:30` — `uv run advisor "<question>"  # run the agent (needs ANTHROPIC_API_KEY, see README.md)`.
- `README.md:25` — "Set `ANTHROPIC_API_KEY`. …"
- `scripts/intent-check-lib.mjs:154-156` — `CORE_CODE` includes `src/advisor/models/`; this change has core code and test changes.

## Subtasks

Each is one or more commits with `npm run verify` green.

1. **Dependency.** Move `httpx` from the dev group to `[project].dependencies`
   in `pyproject.toml` and run `uv lock`. *Why (CLAUDE.md, "no new dependency
   without a line"):* the Ollama adapter talks plain HTTP to `/api/chat`.
   `httpx` is already locked (0.28.1, pulled in by `anthropic`), supports an
   injected `MockTransport` for offline tests, and replaces the `ollama`
   package the spec rules out. No other package is added. It stays in the
   dev group too only if `uv` requires it; otherwise it is removed from
   there.
2. **Error types** (`models/base.py`, B13). Add `ModelUnreachableError(ModelError)`
   and `ModelNotAvailableError(ModelError)`, each carrying a ready
   user-facing message (`str(e)`). They subclass `ModelError`, so
   `agent.answer_question`'s `tracer.fail` path and every existing
   `except ModelError` still hold. No other base change.
3. **Registry** (`models/__init__.py`, B1, B3, B4).
   - `KNOWN_PROVIDERS = ("ollama", "anthropic")`, no longer derived from
     `PROVIDER_KEY_ENV`, which keeps only key providers.
   - `make_client(provider, model, *, api_key: str | None = None,
     base_url: str | None = None)`: `ollama` lazily imports
     `OllamaClient(model=…, base_url=…)` and never receives a key;
     `anthropic` gets `api_key` as today.
   - The unknown-provider error lists both.
4. **Config** (`config.py`, B1, B2, B5, interpretations).
   - `DEFAULT_PROVIDER = "ollama"`.
   - `DEFAULT_MODELS = {"ollama": "qwen3:8b", "anthropic": "claude-haiku-5-5"}`:
     the Ollama model id appears in this one place.
   - `ADVISOR_OLLAMA_URL`, default `http://localhost:11434`, read by
     `Settings.ollama_url()`. It raises `ConfigError("ADVISOR_OLLAMA_URL must
     be an http:// or https:// URL")` for no scheme or another scheme, before
     any network call.
   - Comment sites, as the spec's Interpretations name them: why a `.env`
     pin wins; why not `OLLAMA_HOST`.
5. **The adapter** (`models/ollama_model.py`, B6–B9, B10–B12 mapping).
   `OllamaClient(model, base_url, transport: httpx.BaseTransport | None =
   None)`, holding one `httpx.Client` with `timeout=httpx.Timeout(180.0,
   connect=10.0)`.
   - **Request.** `POST {base_url}/api/chat` with `model`, `stream: false`,
     `think: false`, `options: {"num_ctx": 8192}`, and `tools` as
     `[{"type": "function", "function": {name, description, parameters}}]`.
     The messages are:
     - the system prompt as a `system` message;
     - a user text message as a `user` message;
     - an assistant message with `content` and
       `tool_calls: [{"function": {"name", "arguments"}}]`;
     - each `ToolResult` as a `{"role": "tool", "content", "tool_name"}`
       message, the name looked up from the matching earlier `ToolCall` by
       id.
   - **Response.**
     - `text`: `message.content` if not blank, else `None`.
     - `tool_calls`: one `ToolCall` per entry, with id `f"call_{n}"` from a
       counter on the client (one client per run, so ids are unique within
       the run).
     - `arguments`: a dict as-is; a JSON string parsed into a dict; anything
       else `{"_unparsable_arguments": raw}`.
     - `usage`: `Usage(prompt_eval_count or 0, eval_count or 0)`.
     - `model`: the response's `model`, falling back to the configured one.
   - **Errors.**
     - `httpx.ConnectError` / `ConnectTimeout` → `ModelUnreachableError` with
       the B10 text, URL credentials stripped.
     - HTTP 404 → `ModelNotAvailableError` with the B11 text.
     - Any other non-2xx, `ReadTimeout` or other `httpx.HTTPError`, invalid
       JSON, or a body without `message` → plain `ModelError`.
   - Comment sites: why the native API and not `/v1` or the `ollama` package;
     where the error mapping lives.
6. **CLI** (`cli.py`, B4, B5, B10–B13).
   - `ClientFactory` becomes the `make_client` keyword signature.
   - The missing-key check runs only when `settings.key_variable` is not
     `None`.
   - `ConfigError` from the URL → exit 1 with its message.
   - The factory gets `api_key` only for key providers and `base_url` only
     for `ollama`.
   - In the existing `try`, `except (ModelUnreachableError,
     ModelNotAvailableError) as e` → `_fail(str(e))` (traceback with
     `--debug`) before the generic `except Exception` → `UNAVAILABLE`.
   - `cli.py` imports only from `advisor.models` and `advisor.models.base`:
     no `httpx`, no provider module.
7. **Tracing tags** (`tracing.py`, B14, B15).
   - `make_tracer(env, tags: Sequence[str] = ())` passes the tags to
     `LangfuseTracer`, which sets them on the root at `begin` as the
     `langfuse.trace.tags` attribute, or by `propagate_attributes`. The
     test, not this plan, is the contract.
   - The CLI passes `[f"provider:{provider}", f"model:{model}"]`.
   - No cost fields. `agent.py` does not change.
8. **Boundaries** (B21, B16). In `tests/test_boundaries.py`, assert that
   `_importers("httpx") == {"models/ollama_model.py"}`.
9. **Docs** (B17–B19).
   - `.env.example`: provider and model commented with their defaults,
     `ADVISOR_OLLAMA_URL` with its default, `ANTHROPIC_API_KEY` marked
     "only for `anthropic`".
   - `README.md`:
     - local setup: install Ollama, `ollama pull qwen3:8b`, run with no key;
     - switching to Anthropic;
     - the B10 and B11 messages;
     - the warning that a `.env` copied from the old example pins
       `anthropic`;
     - the comparison: 5 fixed questions, run once per provider, filtered
       by the `provider:` tag in Langfuse;
     - that `ADVISOR_OLLAMA_URL` pointed elsewhere sends questions there.
   - `docs/decisions/0002-local-model.md`, superseding 0001's two rows, and a
     one-line pointer in 0001.
   - `CLAUDE.md`:
     - "Commands" no longer says the run needs `ANTHROPIC_API_KEY`;
     - "Architecture" names `models/ollama_model.py` and states that `httpx`
       is imported only there;
     - the new-provider convention covers keyless providers.
10. **Status.** Set `status: in-review` and append to `## Progress`.

## Tests

The fake transport is `httpx.MockTransport(handler)`. The handler records
each `request` (method, URL, `json.loads(request.content)`) and returns
canned Ollama bodies. No test opens a socket. The conftest guard stays and
would fail any that did.

| Spec | Test (file: what it asserts) | Fails if mutated |
| --- | --- | --- |
| B1, B2, AC1 | `test_config.py`: empty env → `("ollama", "qwen3:8b")`; `ADVISOR_MODEL_PROVIDER=anthropic` → `claude-haiku-5-5`; `ADVISOR_MODEL` overrides | default provider or model changed |
| B3, AC1 | `test_cli.py`: unknown provider → exit 1, stderr names `ollama` and `anthropic`, factory not called | provider dropped from `KNOWN_PROVIDERS` |
| B4, AC2 | `test_cli.py`: provider `ollama`, no key → exit 0, factory got `api_key=None`; same with `ANTHROPIC_API_KEY=sk-x` set → factory still got no key; provider `anthropic`, no key → §1's exact missing-key message, factory not called | key check made unconditional; key passed to `ollama` |
| B5, AC3 | `test_config.py`: default URL; `localhost:11434` and `ftp://h` → `ConfigError` naming `ADVISOR_OLLAMA_URL`; `test_cli.py`: same → exit 1, factory not called | scheme check removed or loosened |
| B6, AC4 | `test_ollama_model.py`: one `POST` to `<base>/api/chat`; body's `model`, `stream is False`, `think is False`, `options == {"num_ctx": 8192}`, first message `{"role":"system","content":<prompt>}`, user message, `tools[0]` equal to the function-tool dict built from the `ToolSpec` | any body field dropped or changed |
| B7, AC4 | tool-call response with two calls → two `ToolCall`s with distinct ids, names, dict args; usage from `prompt_eval_count`/`eval_count`; model from the response; second `complete` with tool results → request carries the assistant `tool_calls` and `{"role":"tool","content":…,"tool_name":<the call's name>}` per result; text-only response → `text`, no calls; blank content → `text is None`; missing counts → 0 | id counter constant; wrong name lookup; usage fields swapped |
| B8, AC5 | string args `'{"category":"phone"}'` → dict; `"not json"` → `{"_unparsable_arguments": "not json"}`; `test_agent.py`: a scripted turn with that call → error tool result containing `unknown argument(s): _unparsable_arguments`, run goes on | parse removed; fallback key renamed |
| B9, AC6 | the client's `timeout.read == 180.0`; `ReadTimeout` from the transport → `ModelError`, not the B10/B11 types | timeout changed |
| B10, AC6 | transport raising `httpx.ConnectError` (and `ConnectTimeout`) → `ModelUnreachableError` whose text is exactly the B10 sentence with `http://localhost:11434`; with base `http://u:p@host:1` the text has `http://host:1` and neither `u` nor `p`; `test_cli.py`: that error → stderr is the message, exit 1, no `Traceback` | strip removed; mapped to generic |
| B11, AC6 | 404 `{"error":"model 'x' not found"}` → `ModelNotAvailableError` with exactly `Model 'x' is not available in Ollama. Run: ollama pull x`; CLI → that line, exit 1 | 404 branch removed |
| B12, AC6 | 500, a non-JSON 200 body, a 200 body without `message` → plain `ModelError`; CLI → `The advisor is unavailable right now.`; `--debug` → traceback present | generic errors promoted to B10/B11 |
| B13, AC8 | `test_boundaries.py`: `cli.py` imports neither `httpx` nor `advisor.models.ollama_model`/`anthropic_model` (AST scan of `cli.py`) | CLI imports the adapter |
| B14, AC7 | `test_tracing.py` with `_real_tracer(tags=…)`: the exported root span carries `provider:ollama` and `model:qwen3:8b` (and, in a second test, the anthropic pair); `test_cli.py`: `make_tracer` receives those two tags for each provider | tags not set; wrong format |
| B15, AC7 | the generation span has model and usage attributes and no `cost_details` attribute | cost attached |
| B16 | a subprocess test (`sys.executable -c …`): import `advisor.cli`, build `make_client("ollama", …)` → `"anthropic" not in sys.modules`; adapter tests assert every request's host is the configured base URL's | eager adapter import |
| B20, B21, AC8 | `test_boundaries.py`: `_importers("httpx") == {"models/ollama_model.py"}`; whole suite runs with no Ollama | `httpx` imported elsewhere |
| AC9 | reviewer reads `.env.example`, `README.md`, `0002`, the 0001 pointer, `CLAUDE.md` | — |

Existing `tests/test_cli.py` and `tests/test_models.py` tests that relied on
the old default or the positional factory are updated in place to set the
provider explicitly. None is deleted.

## Validation

- `npm run verify` green (kit, ruff, ruff format, mypy --strict, pytest),
  with no Ollama installed or running.
- `npm run check:intent` PASS (feature; core code with test changes).
- Live check (owed by rule 1: `src/advisor/models/`, `src/advisor/cli.py`,
  `src/advisor/tracing.py`; spec AC10), run by the owner:
  1. `ollama pull qwen3:8b`; Ollama running. In the shell and in `.env`,
     `ADVISOR_MODEL_PROVIDER` and `ANTHROPIC_API_KEY` unset.
  2. `uv run advisor "I need noise-cancelling headphones under 200 euros"`:
     names catalogue products by name and id, exit 0.
  3. Ollama stopped: the same command prints the B10 message, exit 1.
  4. `ADVISOR_MODEL=nonexistent:1b`: prints the B11 message, exit 1.
  5. With Langfuse running and keys set: the README's 5 questions once per
     provider. In the Langfuse UI, filter by `provider:ollama` and
     `provider:anthropic`. Both sets show, with model names and token usage.

## Assumptions I made

- **Model: `qwen3:8b`, as the spec defaults it.** A library check
  (2026-11-10) found it still the most often recommended 8B tool-calling
  model in Ollama's library. The alternatives (`llama3-groq-tool-use:8b`,
  `gemma4:e4b`) are only lightly sourced, and the sources conflict. The
  live check is the real test, and the spec lets the default change in
  config without a new intent.
- **Message field `tool_name`** for tool results, per the current Ollama
  chat API docs. If the owner's Ollama version expects `name`, the live
  check shows it, and the fix is one key in the adapter.
- **Connect timeout 10 s** within the spec's 180 s call timeout, so "Ollama
  not reachable" comes quickly. It is not a design choice the spec made; a
  connect timeout maps to B10 either way.
- **`ConfigError` lives in `config.py`.** It is configuration, not a model
  failure, so the CLI handles it before building the client.
- **Tags set at `begin`, not per observation.** The trace carries them,
  which is what the Langfuse filter uses.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
