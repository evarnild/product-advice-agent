<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §2 — Locally run model (Ollama) as the advisor's default

**Type:** feature
**Originator:** me (the owner), via `/intent add a locally run model for the advisor`
**Source:** §1 (`intents/1-stack-and-skeleton`), branch `feat/1-stack-and-skeleton`, not yet merged

## Problem

The advisor can only answer through a paid, remote model. On the §1 branch,
`src/advisor/models/__init__.py` has
`PROVIDER_KEY_ENV: dict[str, str] = {"anthropic": "ANTHROPIC_API_KEY"}`, and
`src/advisor/config.py` has `DEFAULT_MODELS: dict[str, str] = {"anthropic":
"claude-haiku-5-5"}`. `src/advisor/cli.py:59–60` stops every run without a
key: `Missing {settings.key_variable}: set it in the environment or in .env.`

This causes four problems for the owner:

- **Cost.** Every live run costs money. The evaluation suite and prompt
  tuning that come later will run many questions, so this cost grows with
  each later intent.
- **Privacy and offline use.** Every question goes to a third-party
  provider. The advisor does not run without internet access and an API
  key.
- **An unproven seam.** §1 chose "provider-agnostic: an internal
  `ModelClient` protocol, one shipped Anthropic adapter, plus a scripted
  fake", and noted that "a second adapter is a small later intent"
  (`docs/decisions/0001-stack.md`). Until a second real adapter exists,
  nothing shows that the seam holds. For example, the key check in
  `cli.py` and `config.py` assumes that every provider needs a key.
- **No comparison point.** We cannot tell how a local model's advice
  compares with Claude's on the same questions.

## Outcome

- With Ollama running locally and the chosen model pulled,
  `uv run advisor "<question>"` with **no environment variables set** and no
  API key answers through the local model. It names catalogue products by
  name and id, and nothing leaves the machine except traces to the
  self-hosted Langfuse when tracing is on. `ADVISOR_MODEL_PROVIDER=anthropic`
  still selects Claude, unchanged.
- The local adapter sits behind `ModelClient` alone. No module outside
  `src/advisor/models/` knows which provider runs, and key handling works
  for a provider that needs no key. When Ollama is not running or the model
  is not pulled, the run fails with a clear message that says what to start
  or pull. It does not fail with the generic error or a stack trace.
- Each local run in Langfuse shows the model name and token usage like an
  Anthropic run, with zero cost. A documented, repeatable side-by-side run
  of a small fixed set of questions through both providers records how the
  two compare. This is not the evaluation suite.

## Constraints

- **Architecture (§1, `CLAUDE.md` once merged):** provider code stays in
  `src/advisor/models/`. The agent loop, catalogue and guardrails stay pure
  and unchanged in meaning. Spec B5 says: "Nothing outside
  `src/advisor/models/` imports a provider SDK."
- **Tests:** "Model calls and external APIs are faked or recorded in tests,
  never called live from the suite" (`CLAUDE.md`). The suite's socket guard
  (§1 spec B21) stays, so the adapter is tested against recorded or faked
  HTTP and never against a running Ollama. `npm run verify` must not need
  Ollama installed.
- **Dependencies:** "No new dependency arrives without a line in the
  intent's `plan.md` saying why." The plan says whether the adapter uses the
  `ollama` package, the OpenAI-compatible endpoint, or plain HTTP through an
  existing dependency.
- **Data:** synthetic only, as in §1. Running locally removes the
  third-party provider from the data path.
- **Cost:** zero per question for local runs. Hardware is the owner's own
  machine. The default model must run acceptably on it (see the open
  questions).
- **Autonomy:** unchanged. The agent only answers, and talks only to
  localhost Ollama and the self-hosted Langfuse.
- **Review tier:** **Reviewed**. The work touches `src/advisor/config.py`
  and `.env.example` (credentials), `src/advisor/cli.py` (user-facing
  output) and possibly `src/advisor/prompts/` (local models may need prompt
  changes). It also touches `src/advisor/models/`, which is `CORE_CODE` and
  a live-check runtime path, so a **live check is owed**.
- **Depends on §1 merging first.** The branch starts from `main` after §1
  ships.
- **Out of scope:** the evaluation suite and any scoring, prompt tuning for
  quality, GPU or driver setup beyond the README steps, running Ollama in
  the repo's Docker Compose, other local runtimes (LM Studio, llama.cpp,
  vLLM), and streaming.

## Type-specific questions

### Feature
- **Users:** the owner, as developer and operator: live runs, later eval
  runs, and offline use.
- **What exists today:** on the §1 branch there is one Anthropic adapter
  and a fake, the default provider is `anthropic`, and a key is required.
  Nothing runs locally.
- **Open design questions** (for `spec.md`):
  1. **Default model.** Which Ollama model with reliable tool calling (for
     example a 7–8B Qwen or Llama instruct model) runs acceptably on the
     owner's hardware? What are its id and minimum RAM or VRAM?
  2. **API style.** Use Ollama's native `/api/chat` with tools, or its
     OpenAI-compatible `/v1` endpoint? Which one gives tool calls and token
     usage reliably?
  3. **Key handling.** How does `PROVIDER_KEY_ENV` and the B7 missing-key
     rule change for a keyless provider? Is there an `OLLAMA_HOST` or base
     URL variable, with what default?
  4. **Failure messages.** Ollama unreachable, model not pulled, the model
     ignores or garbles tool calls. Which of these get their own message,
     and which fall under B14 ("The advisor is unavailable right now.")?
  5. **Tool-call robustness.** Small local models emit malformed tool
     arguments more often. Is the existing B10 error-result-plus-turn-limit
     enough?
  6. **Prompt.** Does `src/advisor/prompts/system.md` stay shared across
     providers, or does a provider get its own variant?
  7. **Side-by-side comparison.** What form does it take: a script, a
     `docs/` note, or Langfuse tags? How many questions are in it, and
     where do its results live?
  8. **Docs.** What changes in `docs/decisions/0001-stack.md` (the default
     model row) or a new decision record `0002-…`, in `.env.example`, and
     in the README setup steps (install Ollama, `ollama pull <model>`)?

## Assumptions I made

- **Ollama is the only local runtime.** Owner's answer. Other runtimes are
  out of scope.
- **The local model becomes the default provider.** Owner's answer. Anthropic
  stays available through `ADVISOR_MODEL_PROVIDER`. This changes §1's
  documented default, so the stack decision record is updated, not left
  stale.
- **"Compare quality" is a lightweight side-by-side, not an evaluation.**
  The owner listed it as a goal, but the evaluation suite is its own later
  intent. Here it means a repeatable run of a few fixed questions through
  both providers, with results recorded, and no automated scoring. If you
  want real measurement, this becomes an experiment that follows the eval
  suite instead.
- **Ollama is installed and run by hand**, like Langfuse in §1. It is not
  added to the repo's Docker Compose.
- **Type is feature.** It adds new behaviour, changes a default, and has
  open design questions. It is too large for an adjustment and touches
  `CORE_CODE`.
- **Owner's hardware is unknown.** The model choice depends on it, so the
  spec asks for it.
