# 0002 — A local model (Ollama) as the default

Status: accepted with intent §2 (2026-11-10). Spec: `intents/2-local-model/spec.md`.

Supersedes the "Model provider" and "Default model" rows of
[0001](0001-stack.md). The rest of 0001 stands.

## Decision

| Choice | Decision | Reason |
| --- | --- | --- |
| Default provider | `ollama`; `ADVISOR_MODEL_PROVIDER=anthropic` still selects Claude, unchanged | The owner wants no API cost, privacy and offline use, a proof of the provider-agnostic seam, and a quality comparison. |
| Runtime | Ollama, at `ADVISOR_OLLAMA_URL` (default `http://localhost:11434`) | The owner's choice. Not `OLLAMA_HOST`, which the server reads as a bind address. |
| Default model | `qwen3:8b`, overridable with `ADVISOR_MODEL` | About 8B with tool support, for the owner's machine (RTX 3060 Laptop 6 GB VRAM, 16 GB RAM): partly on CPU, slower but better advice and tool calls than a small model. Checked against the Ollama library on 2026-11-10; the live check is the real test, and the default may change in config without a new intent. |
| Adapter | Hand-written over the native `/api/chat` with `httpx`, in `models/ollama_model.py`; no `ollama` package, no `/v1` endpoint, no LiteLLM | Keeps 0001's provider-agnostic seam. The native API reports token counts and takes `think` and `num_ctx` directly. `httpx` was already locked and becomes a direct dependency. |
| Comparison | Traces tagged `provider:<p>` and `model:<m>`; compared in the Langfuse UI | The owner chose "Langfuse tags only". Nothing is committed. |

## Consequences

- A `.env` copied from the old `.env.example` pins `anthropic` and keeps
  winning. The README says so.
- No cost is attached to a local generation: Langfuse prices a generation
  only when its model name matches a price definition.
- A keyless provider skips the missing-key check and is never given a key.
