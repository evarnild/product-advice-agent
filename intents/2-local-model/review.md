<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §2 review — Locally run model (Ollama) as the advisor's default

verdict: rework
tier: reviewed
reviewed-commit: a7ff0feb8dbfc398b903fafdbddf7d9064516ec8
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, set by the path table (input 1). The diff touches
`src/advisor/cli.py`, `src/advisor/config.py`, `.env.example` and
`src/advisor/tracing.py`, all Reviewed by meaning. `review_tier: reviewed`
in `metadata.yml` (input 2) agrees, and the HIGH finding (input 3) would
escalate anyway. Status is `in-review`.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): commit ca0eca7 not verify-green, against the plan's "each … with `npm run verify` green" |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (B1–B21, AC1–AC9 in code and tests; AC10 is the live check) |
| 4 | Tests prove the behaviour, not only pass | findings (5): 74 mutants, 65 killed, 9 survived (1 equivalent) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): Progress says "was 128", `main` has 104 |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (`httpx` moved to runtime deps with the plan's why-line; placeholders only) |
| 9 | Repository-specific footguns | pass (list empty; candidate below) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 2, feature)
  note:  21 file(s), 936 line(s) changed outside intents/.
```

## Findings

- **HIGH** `src/advisor/models/__init__.py:31`, `:35` — no test proves
  `make_client` passes its arguments to the adapter.
  - Survivors:
    - M02: `base_url=base_url or DEFAULT_BASE_URL` → `base_url=DEFAULT_BASE_URL`;
    - R04: `OllamaClient(model=model, …)` → `model="qwen3:8b"`;
    - R03: `api_key=api_key or ""` → `api_key=""`.
  - Why the suite misses it: every CLI test injects a fake
    `client_factory`, and `tests/test_models.py:28` asserts only
    `isinstance`.
  - What could ship green: `ADVISOR_OLLAMA_URL` ignored (B5),
    `ADVISOR_MODEL` ignored for Ollama (B1, and AC10's `nonexistent:1b`
    step), or the Anthropic key dropped (§1 B7).
  - The code is correct today; a probe confirmed the wiring. The gap is the
    tests: the plan's first named risk.
  - Needs rework: in `tests/test_models.py`, assert:
    - `make_client("ollama", "m-x", base_url="http://box:9/")` yields a
      client with model `m-x` and base URL `http://box:9`, via its
      attributes or one `complete` over `httpx.MockTransport`;
    - `make_client("ollama", "m")` with no `base_url` uses
      `http://localhost:11434`;
    - `make_client("anthropic", "m", api_key="placeholder-key")` gives an
      SDK client whose `api_key == "placeholder-key"`, built without
      connecting.

    Kills M02, R03, R04.
- **LOW** `src/advisor/models/base.py:21`, `:25` — no test asserts that
  `ModelUnreachableError` and `ModelNotAvailableError` subclass
  `ModelError`; mutants B01 and B02 (base changed to `Exception`) survive.
  Plan subtask 2 makes this the contract. Needs rework: `assert
  issubclass(ModelUnreachableError, ModelError) and
  issubclass(ModelNotAvailableError, ModelError)`. Kills B01, B02.
- **LOW** `src/advisor/models/ollama_model.py:135` — only a 500 is tested as
  "other HTTP error" (B12). M25 (`not response.is_success` →
  `status_code >= 500`) survives: a non-404 4xx with a `message` body
  would be read as a turn. Needs rework: add `httpx.Response(400,
  json={"message": {"role": "assistant", "content": "x"}})` to
  `test_other_failures_are_plain_model_errors`. Kills M25.
- **LOW** `src/advisor/models/ollama_model.py:46` — the IPv6 bracket branch
  of `_display_url` is never exercised; M39 (branch removed) survives. The
  URL is the user-facing B10 text. Needs rework: a connect-error test with
  base `http://[::1]:11434` asserting the message contains
  `http://[::1]:11434`. Kills M39.
- **LOW** `intents/2-local-model/plan.md` (Progress) — "162 pytest tests
  (was 128 …)". 162 is right; `main` at dfb0811 collects **104** (a `git
  archive` snapshot, `--collect-only`). Needs rework: change "was 128" to
  "was 104" (below the Progress marker: the implementer's to edit).
- **LOW** commit `ca0eca7` — not verify-green on its own. A `git archive`
  snapshot gives pytest "13 failed, 91 passed" and one mypy error
  (`cli.py:36`, incompatible default for `client_factory`). It hurts only
  bisecting after the `--no-ff` merge; HEAD is green. Needs rework: record
  the deviation in `## Progress` (which commit, what was red, that 20c9316
  restores green). Rewriting history instead is the owner's choice and not
  required.
- **LOW** `src/advisor/models/ollama_model.py:141` — M42 (`.get("tool_calls")
  or []` → `.get("tool_calls", [])`) survives; it differs only on
  `"tool_calls": null`, which Ollama does not send (it omits the field).
  Worth a look: a one-line `null` fixture would pin it.
- **LOW** `src/advisor/tracing.py:93` — tags are set through the SDK's
  private `_otel_span`. The in-memory exporter test runs the real SDK, so an
  SDK change that drops it fails a test rather than silently; in production
  `SafeTracer` would drop only the tags. Whether the server reads
  `langfuse.trace.tags` from a `start_observation` root is the live check's.
  Worth a look.
- **LOW** `src/advisor/models/ollama_model.py:36` vs `src/advisor/config.py:25`
  — the default URL is defined twice (`DEFAULT_BASE_URL`,
  `DEFAULT_OLLAMA_URL`). The spec's single-place rule covers only the model
  id, which holds. Worth a look.
- **LOW** `src/advisor/models/ollama_model.py:132` — every HTTP 404 becomes
  the B11 "pull the model" message; spec B11 says "HTTP 404 naming the
  model", and the approved plan narrowed it to "HTTP 404". With
  `ADVISOR_OLLAMA_URL` at a non-Ollama server, the user is told to pull a
  model. Settled by the plan: Worth a look.
- **Pass 9 candidate:** "factory or registry wiring that every test
  bypasses with an injected fake" — the plan's first risk recurred as the
  HIGH above. An owner edit to `REVIEW-POLICY.md`, not part of this rework.

Mutants (74; full `pytest -q -x` each; backup by copy, `git diff --quiet`
non-zero asserted, restore by copy). Survivors: M02, R03, R04 (HIGH); B01,
B02, M25, M39 (LOW); M42 (near-equivalent); M40 (`parts.path.rstrip('/')` →
`parts.path`, equivalent: `__init__` already strips). The other 65 are
killed:
- the request body (M01, M03–M10);
- the message mapping (M11–M19);
- the error mapping (M20–M24, M26–M28);
- the response mapping (M29–M37);
- `_display_url` (M38, M41);
- the registry (R01, R02);
- config (C01–C08);
- the CLI (L01–L13);
- tracing (T01–T05).

The full table is in the reviewer's report. The plan's named risks were
handled well otherwise:
- request bodies are compared whole;
- fixtures differ from the outputs (served model name, string arguments,
  reversed result order);
- the existing CLI tests now set `ADVISOR_MODEL_PROVIDER=anthropic`, so they
  kept their meaning.

## Not checked
- Real Ollama:
  - whether 0.40.9 accepts `tool_name` on tool messages, and honours `think`
    and `num_ctx`;
  - the `prompt_eval_count`/`eval_count` shape;
  - whether `qwen3:8b` emits tool calls and names catalogue products.

  Rule 3.
- Whether the Langfuse server reads `langfuse.trace.tags` from a
  `start_observation` root and shows it as filterable tags. Rule 3.
- Langfuse not pricing `qwen3:8b` (only "no cost attribute sent" is shown).
- The README's "about 5 GB" for `qwen3:8b`.
- The real `--debug` traceback for a connect error with `user:pw@` in the
  URL: the chained httpx exception may show it, in debug output only.
- Proxy settings (`HTTP_PROXY`, `trust_env`) on the `httpx.Client`, which
  could route localhost traffic through a proxy.
- Ship preconditions after `main` moved (dfb0811 → 82bb545, intent
  artefacts of §3 and §4 only): not test-merged.

## Live check
- owed:
  - rule 1: the diff touches `src/advisor/cli.py`, `src/advisor/models/` and
    `src/advisor/tracing.py`;
  - rule 3: the real Ollama `/api/chat` tool-call round trip, and the
    server reading `langfuse.trace.tags`.

  Run after the rework.
- steps (Windows PowerShell, in the worktree):
  1. ```
     cd C:\Users\eric\src\product-advice-agent-wt\2-local-model
     Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL, Env:ANTHROPIC_API_KEY, Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue
     ```
     No `.env` in this folder or a parent (`…\product-advice-agent-wt\`,
     `C:\Users\eric\src\`) may set `ADVISOR_MODEL_PROVIDER`; the worktree
     has none today.
  2. Start Ollama (the app, or `ollama serve`); run `ollama pull qwen3:8b`,
     then `ollama list`.
  3. `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
     then `$LASTEXITCODE`.
  4. Quit Ollama; repeat step 3.
  5. Start Ollama; `$env:ADVISOR_MODEL = "nonexistent:1b"`; repeat step 3;
     then `Remove-Item Env:ADVISOR_MODEL`.
  6. Tags:
     1. Start the local Langfuse (README).
     2. Set `$env:LANGFUSE_HOST`, `$env:LANGFUSE_PUBLIC_KEY` and
        `$env:LANGFUSE_SECRET_KEY`.
     3. Run the README's 5 "Comparing providers" questions with the default.
     4. Set `$env:ADVISOR_MODEL_PROVIDER = "anthropic"` and
        `$env:ANTHROPIC_API_KEY`, and run the 5 again.
     5. In Langfuse → Traces, filter by `provider:ollama`, then
        `provider:anthropic`.
  7. Optional (B16): during step 3, `Get-NetTCPConnection -State Established
     | Where-Object OwningProcess -eq (Get-Process python).Id`.
- you should see:
  - **Step 2:** `qwen3:8b` listed.
  - **Step 3:** an answer naming catalogue headphones by name and id
    (P-0xx), exit `0`. The first run can take tens of seconds.
  - **Step 4:** exactly `Ollama is not reachable at http://localhost:11434.
    Start Ollama (the Ollama app, or "ollama serve") and try again.`, no
    traceback, exit `1`.
  - **Step 5:** exactly `Model 'nonexistent:1b' is not available in Ollama.
    Run: ollama pull nonexistent:1b`, exit `1`.
  - **Step 6:**
    - 5 traces under each filter, tagged `provider:<p>` and
      `model:qwen3:8b` / `model:claude-haiku-5-5`;
    - each `model-call` with model and token counts;
    - no cost on the Ollama ones.
  - **Step 7:** only `127.0.0.1:11434`, plus the Langfuse port when tracing
    is on.
  - **If something differs:**
    - Tool calls failing in step 3 (no products named, or an Ollama 400
      about `tool_name`) is a defect.
    - Traces without tags in step 6 is a defect in the tag mechanism
      (`_otel_span` attribute vs `propagate_attributes`).

    Either way, leave `live_checked:` empty.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/2-local-model` at a7ff0fe, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "60 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "162 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0 (above).
  Matches.
- **Coordinator, re-run:** the 9 survivors with my own harness (backup by
  copy, exactly one replacement, file-changed assertion, full `pytest -q
  -x`, restore by copy).
  - M02, R03, R04, B01, B02, M25, M39 (`if ":" in host:` → `if False:`),
    M40 and M42 each SURVIVED, with "162 passed".
  - Matches the reviewer on all 9.
- **Coordinator, re-run:** `git status --short` empty after the mutants.

**Reviewer, verified:**
- HEAD a7ff0fe, merge base dfb0811, nothing pushed.
- `npm run verify` and `check:intent`, as above.
- `sdlc:scan --sample-due auto --exclude 2` → "nth attested auto change = 1,
  every 3, sampled: no".
- `agent.py`, `catalogue.py`, `guardrails.py` and `prompts/` are unchanged;
  `infra/` and `.claude/` are untouched.
- 74 mutants (harness `…/scratchpad/mut2/mut.py`, CRLF-aware).
- `main` snapshot collects 104 tests.
- `ca0eca7` snapshot: 13 failed, 91 passed, plus 1 mypy error.
- An end-to-end probe against the real modules:
  - `make_client` wiring returns `m-x http://box:9`;
  - the real CLI with `ADVISOR_OLLAMA_URL=http://usr:pw@127.0.0.1:1` (a
    refused local port) printed the B10 text with credentials stripped, rc 1;
  - a MockTransport 404 printed the B11 text;
  - a 500 printed the generic text.
- The AC9 docs were read.
- A grep of the diff for secrets found placeholders only.

**Taken on trust:**
- the Ollama API shape (`tool_name`, `think`, the 404 body), per the
  spec's citation;
- the server's handling of `langfuse.trace.tags`;
- the 5 GB model size;
- the plan's library check for `qwen3:8b`.

No real Ollama, Anthropic or Langfuse was contacted; Docker was not started.
