<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §27 — Type the Anthropic adapter against the SDK's own types

**Type:** refactor
**Originator:** the owner ("why any as return type?", on
`src/advisor/models/anthropic_model.py:71`)
**Source:** none (conversation, 2026-11-16)

## Problem

The Anthropic adapter is the one module that talks to the `anthropic` SDK,
and `mypy --strict` checks almost none of that conversation:

- `self._sdk` is typed `Any` (`anthropic_model.py:61`) so that a test can
  inject a fake through `sdk_client`. Everything reached through it is
  `Any`, including the response (`response: Any`, line 71).
- The request side builds `dict[str, Any]` (`_to_api_message`,
  `_to_api_tool`) instead of the SDK's `MessageParam` / `ToolParam`
  TypedDicts, so a misspelt key or wrong block shape is not caught.
- On the response side, `response.content`, `block.text`, `block.input`,
  `response.usage` and `response.model` are unchecked attribute accesses.
  Line 86 already guards `block.input` with an `isinstance` by hand. A typo
  or an SDK rename fails only at runtime, and the adapter tests in
  `tests/test_models.py` catch it only if `FakeSdk` and `_response` happen
  to mirror the real shape.

## Outcome

- `src/advisor/models/anthropic_model.py` contains no `Any`: the SDK client,
  the request payloads and the response are typed with the SDK's own types
  (`anthropic.Anthropic` or a narrow `Protocol` over `messages.create`,
  `MessageParam`, `ToolParam`, `anthropic.types.Message`), and `mypy
  --strict` passes with no new `type: ignore` in `src/`.
- Behaviour is unchanged: every existing adapter test in
  `tests/test_models.py` passes with its assertions untouched. Only the
  fake's construction may change, to satisfy the new types.
- A live run with `--provider anthropic` (or the CLI's equivalent) answers a
  catalogue question with a tool call, as before.

## Constraints

- `anthropic` stays imported only in `models/anthropic_model.py`
  (`tests/test_boundaries.py`). Its types may be imported in tests.
- The `ModelClient` protocol and `models/base.py` do not change. Neither do
  the agent, the CLI, the Ollama adapter or tracing.
- The SDK client keeps `open_telemetry=False` (§5). The tests that pin it
  stay green.
- No new dependency and no SDK version bump (`anthropic` 2.6.0 per
  `uv.lock`).
- Tests never call the real API. The fake stays a fake (`tests/conftest.py`
  blocks sockets).
- Touches `src/advisor/models/`, so a live check is owed (REVIEW-POLICY.md →
  "Live checks", rule 1). It costs a few Anthropic calls on the owner's key.
- Out of scope: typing the Ollama adapter's JSON (a separate intent if
  wanted), and streaming.

## Type-specific questions

### Refactor
- **What is restructured:** `src/advisor/models/anthropic_model.py` (client
  attribute, the two converters, the response handling) and the fake SDK
  helpers in `tests/test_models.py` (`FakeSdk`, `_response`).
- **How behaviour is held constant:** the adapter tests in
  `tests/test_models.py` stay green with their assertions unchanged:
  request translation (assistant text plus tool_use blocks, tool_result
  with `is_error`), response translation (text, tool calls, usage, model),
  `AnthropicError` wrapped as `ModelError`, the OTel-off and key-passing
  tests. Before typing anything, add a characterisation test for a
  `tool_use` block whose `input` is not a dict, which today yields `{}`
  (line 86). Nothing pins that branch yet.
- **Why now:** the adapter is the boundary where a wrong shape is most
  expensive (it fails only against the live API, in a live check), and the
  type checker is the cheapest guard there. It also makes the adapter the
  pattern a future provider copies.

## Assumptions I made

- **No characterisation test for the non-dict `input` branch.** A grep of
  `tests/test_models.py` shows only dict inputs (lines 139, 181, 210). I did
  not read the whole file.
- **Fake versus types, left to the plan.** Either a small `Protocol` over
  `messages.create` that both `anthropic.Anthropic` and the test fake
  satisfy, or `anthropic.Anthropic` plus a `cast` in tests. A `Protocol`
  avoids casts in tests.
- **`review_tier` left empty.** `models/` is not in the "by meaning" list,
  so the path table decides.
- **Nothing blocks this.** No open intent touches the adapter.
