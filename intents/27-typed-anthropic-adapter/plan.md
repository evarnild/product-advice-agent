<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §27 plan — Type the Anthropic adapter against the SDK's own types

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`src/advisor/models/anthropic_model.py` loses every `Any`. The SDK client
is typed `anthropic.Anthropic`. The request payloads are the SDK's
`MessageParam`, `TextBlockParam`, `ToolUseBlockParam`,
`ToolResultBlockParam` and `ToolParam` TypedDicts. The response is the
`anthropic.types.Message` that `messages.create` already returns, with its
blocks narrowed by `isinstance` to `TextBlock` and `ToolUseBlock`.
`mypy --strict` passes with no new `type: ignore` in `src/`. Every existing
adapter test in `tests/test_models.py` keeps its assertions. Only the
fake's response objects change: they become real SDK models, so the fake
can no longer drift from the real shape. That drift is the risk the intent
names.

## Design decision the intent left to the plan

The intent's assumptions offered two options: "a small `Protocol` over
`messages.create` … or `anthropic.Anthropic` plus a `cast` in tests". This
plan takes **`anthropic.Anthropic`, with no Protocol and no cast**.
Reasons:

- `mypy` checks only `src/advisor` (`pyproject.toml`: `[tool.mypy] files
  = ["src/advisor"]`, `strict = true`). The tests are not type-checked, so
  passing `FakeSdk` as `sdk_client` needs no cast. It works at run time as
  it does today.
- A Protocol would have to restate the overloaded `Messages.create`
  (`resources/messages/messages.py:122-150`, one overload per `stream`
  value) and the `cached_property` `messages` (`_client.py:314`). That is
  more surface than it guards.
- **Prototype:** the typed adapter sketched in this plan was run through
  `MYPYPATH=src uv run mypy --strict` and gave "Success: no issues found"
  on anthropic 2.6.0. It narrows by `isinstance` on `TextBlock` /
  `ToolUseBlock`, imports the param TypedDicts, and contains no `Any`.

## Risks

- **A changed response mapping.** Today the code matches `block.type ==
  "text"` / `"tool_use"` (`anthropic_model.py:83,85`). `isinstance` on
  `TextBlock` / `ToolUseBlock` is the same partition for the blocks
  `messages.create` returns, because the `ContentBlock` union is tagged by
  `type` (`types/content_block.py:20-35`). Any other block type
  (thinking, server tool use …) stays ignored, as now. The live check
  covers the real API.
- **The non-dict `input` branch** (`anthropic_model.py:86`). Nothing tests
  it today: test inputs are dicts only (`tests/test_models.py:139,181,210`).
  The SDK types `ToolUseBlock.input` as `Dict[str, object]`
  (`types/tool_use_block.py:21`), so a type-driven edit could drop the
  guard and change behaviour. A characterisation test (Tests, 1) pins
  "non-dict input yields `{}`" before anything is typed. The guard stays.
  `strict` does not enable `warn_unreachable`, so mypy accepts it.
- **Dict variance.** `ToolCall.arguments` is `dict[str, Any]`
  (`base.py:42`) and the block's `input` is `Dict[str, object]`. The
  prototype copies it with `dict(block.input)`, which mypy accepts.
  `base.py` does not change (intent constraint).
- **Fake fidelity.** Building the responses with the SDK's own validated
  constructors (`Message(...)`, `TextBlock(...)`, `ToolUseBlock(...)`,
  `Usage(...)`) makes the fake fail at construction time if the SDK shape
  changes. Only the characterisation test uses `model_construct`, to build
  an input the validator would refuse.
- **Tests that pass whatever the code does.** The assertions stay as they
  are, and each response-side test asserts mapped values (text, calls,
  usage, model), so a mapping that drops a block fails. Mutations to run
  are under Tests.
- **Stale line citations.** All lines were read at `1968ee6`.
- **Boundary.** `anthropic` stays imported only in
  `models/anthropic_model.py` (`tests/test_boundaries.py:26-27`). Tests
  may import `anthropic.types` (intent constraint), and the test file
  already imports `anthropic` (`tests/test_models.py:3`).
- REVIEW-POLICY.md pass 9 (repository-specific footguns) lists nothing yet.

## Verified against the codebase

Re-read on `main` at `1968ee6`.

- `src/advisor/models/anthropic_model.py:9` — `from typing import Any`.
- `src/advisor/models/anthropic_model.py:25-48` — `_to_api_message(m) -> dict[str, Any]`, with `blocks: list[dict[str, Any]]` (line 27).
- `src/advisor/models/anthropic_model.py:51-52` — `_to_api_tool(t) -> dict[str, Any]`.
- `src/advisor/models/anthropic_model.py:56` — `sdk_client: Any | None = None`; `:61-65` `self._sdk: Any = (… anthropic.Anthropic(api_key=api_key, open_telemetry=False))`.
- `src/advisor/models/anthropic_model.py:71-77` — `response: Any = self._sdk.messages.create(model=…, max_tokens=MAX_TOKENS, system=system, messages=[…], tools=[…])`.
- `src/advisor/models/anthropic_model.py:78-79` — `except anthropic.AnthropicError` → `ModelError`.
- `src/advisor/models/anthropic_model.py:82-93` — the block loop (`block.type == "text"` / `"tool_use"`), the `isinstance(block.input, dict)` guard at 86, `Usage(response.usage.input_tokens, …)`, `model=response.model`.
- `src/advisor/models/base.py:42` — `arguments: dict[str, Any]` (unchanged).
- `.venv/.../anthropic/_version.py` — `__version__ = "2.6.0"`; `uv.lock:19,32` — anthropic 2.6.0.
- `.venv/.../anthropic/types/tool_use_block.py:21` — `input: Dict[str, object]`.
- `.venv/.../anthropic/types/message.py:30` — `content: List[ContentBlock]`; `:72` `model: Model`; `:123` `usage: Usage`.
- `.venv/.../anthropic/types/message_param.py:12` — `MessageParam: TypeAlias = Union[UserMessageParam, AssistantMessageParam, SystemMessageParam]`.
- `.venv/.../anthropic/types/tool_param.py:31-32` — `ToolParam(TypedDict, total=False)`, `input_schema: Required[InputSchema]` (`InputSchema` includes `Dict[str, object]`, line 28).
- `.venv/.../anthropic/resources/messages/messages.py:122-150` — the non-streaming `create` overload: `messages: Iterable[MessageParam]`, `system: Union[str, Iterable[TextBlockParam]] | Omit`, `tools: Iterable[ToolUnionParam] | Omit`, `-> Message`.
- `.venv/.../anthropic/_client.py:314` — `def messages(self) -> Messages` (cached property).
- `tests/test_models.py:37-47` — the OTel-off test (monkeypatched `anthropic.Anthropic`, unchanged); `:50-54` the env-var test with `# type: ignore[attr-defined]` (in tests, not `src/`); `:75-78` the key test.
- `tests/test_models.py:111-130` — `FakeSdk` and `_response` (`SimpleNamespace`).
- `tests/test_models.py:133-218` — the six adapter tests whose assertions stay.
- `tests/test_boundaries.py:26-27` — `_importers("anthropic") == {"models/anthropic_model.py"}`.
- `pyproject.toml` `[tool.mypy]` — `files = ["src/advisor"]`, `strict = true`.
- `REVIEW-POLICY.md:78-79` — `src/advisor/models/` owes a live check; `:123` — `src/advisor/models/` owes an eval run.

## Subtasks

1. **The characterisation test, before any typing.** Add a test to
   `tests/test_models.py` that sends a `tool_use` block whose `input` is
   not a dict, and asserts that the call's `arguments == {}` (Tests, 1). It
   passes against today's code. `npm run verify` green, commit.
2. **The fake builds real SDK responses.** Rewrite `_response` to return
   `anthropic.types.Message(id=…, type="message", role="assistant",
   model=model, stop_reason="end_turn", stop_sequence=None,
   content=content, usage=Usage(input_tokens=…, output_tokens=…))`.
   Replace the `SimpleNamespace(type="text", …)` /
   `SimpleNamespace(type="tool_use", …)` blocks with
   `TextBlock(type="text", text=…)` / `ToolUseBlock(type="tool_use", …)`.
   Keep `FakeSdk` itself. Assertions stay unchanged. Green against today's
   code, commit.
3. **Type the adapter.** In `anthropic_model.py`: drop `from typing import
   Any`. Type `sdk_client: anthropic.Anthropic | None` and `self._sdk:
   anthropic.Anthropic`. `_to_api_message` returns `MessageParam`, with
   `blocks: list[TextBlockParam | ToolUseBlockParam]` and the tool results
   as `list[ToolResultBlockParam]`. `_to_api_tool` returns `ToolParam`.
   The response is no longer annotated (mypy infers `Message`). The loop
   narrows with `isinstance(block, TextBlock)` / `isinstance(block,
   ToolUseBlock)`, and keeps the `isinstance(block.input, dict)` guard,
   copying with `dict(block.input)`. Keep `open_telemetry=False` and its
   comment. `npm run verify` green, with no new `type: ignore` in `src/`.
   Commit.
4. **Hand over.** Append to `## Progress` and set `status: in-review`.

## Tests

The failing-first rule for a refactor is the characterisation test. It must
pass **before** subtask 3 and still pass after.

1. **Non-dict input yields `{}`** (new, subtask 1): a response with
   `ToolUseBlock.model_construct(type="tool_use", id="tu_1",
   name="search_products", input=["x"])` gives `turn.tool_calls ==
   (ToolCall("tu_1", "search_products", {}),)`. It fails if the guard at
   line 86 is removed (the list would pass through).
2. **The existing adapter tests, assertions untouched**
   (`tests/test_models.py:133-218`):
   - `test_adapter_maps_tool_use_and_usage` fails if the text block or the
     tool block is not mapped, or if usage or model are not;
   - `test_adapter_translates_tool_round_trip_messages` and
     `test_adapter_assistant_with_empty_text_sends_no_text_block` fail if
     a request key or shape changes (`is_error`, the empty-text skip);
   - `test_adapter_wraps_sdk_errors` fails if the `except` is narrowed or
     dropped;
   - `test_adapter_reports_the_model_the_response_names` fails if `model=`
     comes from the configuration.
3. **The OTel and key tests** (`:37-54`, `:75-78`) stay green unchanged.
   They fail if `open_telemetry=False` or `api_key` is dropped.
4. **Mutations the review should run** (each must be killed):
   `isinstance(block, TextBlock)` → `ToolUseBlock` (killed by test 2,
   first bullet); remove the `isinstance(block.input, dict)` guard (killed
   by test 1); `"is_error": r.is_error` → `False` (killed by the round-trip
   test); `open_telemetry=False` → `True` (killed by test 3).

No test calls the real API. `tests/conftest.py` blocks sockets, and the SDK
models are built in memory.

## Validation

- `npm run verify` green: ruff, format, `mypy --strict` and pytest.
- `npm run check:intent` PASS.
- `grep -n "Any" src/advisor/models/anthropic_model.py` prints nothing, and
  `git diff main -- src | grep "type: ignore"` prints nothing.
- **Eval run (owed: `src/advisor/models/` is in REVIEW-POLICY.md "Eval
  runs").** The coordinator runs it on Ollama at the reviewed commit and
  compares it against `evals/baseline.json`. The Ollama path does not use
  this adapter, so no case is expected to flip. A flip is re-run with
  `--only` per the policy.
- **Live check (owed: `src/advisor/models/`, REVIEW-POLICY.md:78-79).** It
  costs a few Anthropic calls on the owner's key. In the worktree, in
  PowerShell:
  1. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"; uv run advisor "Which noise-cancelling headphones under 200 euros do you have?"`.
     Expect an answer that cites real ids with their prices (the agent ran
     `search_products`, so the tool round trip works), exit code 0.
  2. Optional, if Langfuse is up: the trace shows one generation per model
     turn, with a tool span between, and no separate SDK spans (§5).
  3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER`.

## Assumptions I made

- `anthropic.Anthropic` rather than a Protocol, for the reasons above. The
  intent left this to the plan.
- Unknown block types stay silently ignored, as now. No logging is added.
- `review_tier` stays empty: `src/advisor/models/` is Attested by the path
  table (REVIEW-POLICY.md:28-29), and is not in the "by meaning" list.
- §24 (the judge's structured output) may also touch this adapter. Neither
  blocks the other, and whichever merges second takes the first in through
  `npm run update-branch`.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-24 — implementation (all subtasks)

- Commits: characterisation test, SDK-built fake responses, typed adapter
  (subjects "§27: characterise non-dict tool input…", "§27: build real SDK
  responses…", "§27: type the Anthropic adapter…").
- Shipped: `anthropic_model.py` has no `Any`, uses `anthropic.Anthropic`, the
  SDK param TypedDicts and `isinstance` narrowing; the non-dict guard and
  `open_telemetry=False` are kept. The test fake builds `Message`,
  `TextBlock`, `ToolUseBlock` and `Usage`. No `type: ignore` added in `src/`.
- Tests: 859 -> 860 passed (one new characterisation test); existing
  assertions unchanged.
- Mutations (tests/test_models.py): TextBlock->ToolUseBlock (3 failed), drop
  non-dict guard (1 failed), `is_error` -> False (1 failed),
  `open_telemetry=True` (4 failed). All killed.
- Divergences: none. The eval run and live check remain owed.

### 2026-11-24 — review round 1 rework

- Finding (MEDIUM): `isinstance` narrowing alone accepted blocks whose tag
  the SDK does not know (it falls back to `TextBlock`/`ToolUseBlock` and
  keeps the foreign `type`). Fixed by also checking `block.type == "text"` /
  `"tool_use"`, as on main.
- Tests: two new, a text-shaped and a tool-shaped block with tag
  `"futuristic"` next to a real text block. Both failed before the fix.
  860 -> 862 passed.
- Mutants: dropping the text tag check is killed by
  `test_adapter_ignores_text_shaped_blocks_with_an_unknown_tag`; dropping the
  tool tag check by `test_adapter_ignores_tool_shaped_blocks_with_an_unknown_tag`.
- LOW (`dict(block.input)`, equivalent mutant): no action, as instructed.
