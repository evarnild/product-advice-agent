<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §24 plan — Constrain the LLM judge's reply to its verdict schema

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

Checked against `main` at `6ebf3c6`. The spec was written at `ca8b032`,
before §27 (the typed Anthropic adapter) merged; every adapter and adapter
test line below is re-cited from the typed code on `6ebf3c6`.

## Goal

A judge call (`judge` and `judge-validate`) asks Anthropic for a reply that
fits the verdict schema `{"reason": string, "pass": boolean}` through
`output_config.format` (spec B3, I1), reads it with a strict `json.loads`
instead of `extract_json` (B8), and turns a refusal or a cut-off at the
token limit into a named `JudgeError` (B4, B7). The way there is one
optional keyword-only `schema` on `ModelClient.complete` (B1) that the fake
records (B2), the Anthropic adapter maps (B3, B4) and the Ollama adapter
refuses (B5, owner's Q2). Every call without a schema, including all of the
agent's, behaves exactly as today. The owner's `judge-validate` run then
replaces `evals/judge/validation.md` (B11).

## Risks

- **Pass 9 (repository footguns)** lists no class yet (`REVIEW-POLICY.md`
  → "Passes", 9: "This list starts empty and grows from findings"). The
  classes this repo has hit in this area, from §16 and §27: a test that
  checks only `isinstance(..., JudgeError)` and so survives a change of
  reason (today's `test_anything_else_is_a_judge_error`,
  `tests/test_judge.py:200-214`); line citations that rot between spec and
  build (this spec's adapter lines already did, see "Verified").
- **Tests that pass whatever the code does.** `_response` in
  `tests/test_models.py:128-138` hard-codes `stop_reason="end_turn"`, so a
  B4 check that fired without a schema, or never fired, would pass every
  existing test. Subtask 2 adds a parameter and tests both stop reasons
  with and without a schema. AC3 is asserted as an equality on the whole
  keyword set in both cases, since the existing adapter tests check the
  keywords one by one and would miss an extra one.
- **Passing `output_config=omit`** would satisfy the SDK but break AC3
  (the keyword would be present). The adapter calls `create` without the
  key when there is no schema.
- **Protocol drift.** Adding the keyword to `ModelClient` makes
  `make_client`'s return (`src/advisor/models/__init__.py:23`, `->
  ModelClient`) fail `mypy --strict` until both adapters accept it, so the
  protocol and every `src` implementation change in one commit. The test
  double `RoutedClient` (`tests/judge_world.py:94-110`) is not
  type-checked; it breaks at run time (`TypeError`) only once `_ask` passes
  the keyword, so it changes in the same commit as `_ask`.
- **CRLF.** The shipped prompt is read with CRLF line endings in this
  checkout (`judge-no-fit.md` ends `"}\r\n` on disk). The AC9 test compares
  lines (`splitlines()`), not a string with `\n`.
- **Model support is unknowable offline.** Whether `claude-haiku-5-5`
  accepts `output_config.format` (and with `tools=[]` beside it) shows
  only in the live check; a rejection is an API error, i.e. an `ERROR`
  line naming it (B7), never a verdict.
- **The reviewed commit and `validation.md`.** The owner's new
  `validation.md` is a branch file, so it must be committed before the
  round whose `reviewed-commit` is merged (`REVIEW-POLICY.md` → "Merging",
  1: "Nothing but that intent's `review.md` or `metadata.yml` differs
  between `reviewed-commit` and the branch"). §16 did the same: its
  live-check commit `241dfd9` is an ancestor of its reviewed commit
  `1d79fe9`.

## Verified against the codebase

Re-read on `main` at `6ebf3c6`.

The interface and the fake:

- `src/advisor/models/base.py:83-88` — `class ModelClient(Protocol): def complete(self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]) -> ModelTurn:`; no reply-shape parameter. `typing.Any` is already imported (`base.py:14`); `Mapping` is not (`base.py:12` imports only `Sequence`).
- `src/advisor/models/base.py:17-18` — `class ModelError(Exception)`, the error `_ask` already catches.
- `src/advisor/models/fake.py:15-19` — `@dataclass(frozen=True) class Request: system, messages, tools`.
- `src/advisor/models/fake.py:35-38` — `ScriptedModelClient.complete(self, system, messages, tools)`, `self.requests.append(Request(system, tuple(messages), tuple(tools)))`; the only `Request(` construction in `src/` and `tests/`.
- `src/advisor/models/__init__.py:17-35` — `make_client(...) -> ModelClient` returns `OllamaClient` or `AnthropicClient`, so both must satisfy the protocol.

The Anthropic adapter (typed by §27; the spec's `anthropic_model.py:67-93` and `:22` are now these lines):

- `src/advisor/models/anthropic_model.py:10-19` — `import anthropic`; `from anthropic.types import (MessageParam, TextBlock, TextBlockParam, ToolParam, ToolResultBlockParam, ToolUseBlock, ToolUseBlockParam)`.
- `src/advisor/models/anthropic_model.py:30` — `MAX_TOKENS = 1024`.
- `src/advisor/models/anthropic_model.py:69` — `self._sdk: anthropic.Anthropic = (...)`.
- `src/advisor/models/anthropic_model.py:75-87` — `def complete(self, system, messages, tools) -> ModelTurn:`; `response = self._sdk.messages.create(model=self._model, max_tokens=MAX_TOKENS, system=system, messages=[_to_api_message(m) for m in messages], tools=[_to_api_tool(t) for t in tools])`; `except anthropic.AnthropicError as e: raise ModelError(f"Anthropic call failed: {type(e).__name__}") from e`.
- `src/advisor/models/anthropic_model.py:88-101` — the content loop (`isinstance(block, TextBlock) and block.type == "text"`, `isinstance(block, ToolUseBlock) and block.type == "tool_use"`) and `return ModelTurn(text="".join(texts) if texts else None, ...)`; `response.stop_reason` is never read.

The SDK, `anthropic` 2.6.0 (`.venv/Lib/site-packages/anthropic/_version.py:2`, `__version__ = "2.6.0"`):

- `anthropic/types/__init__.py:134` — `from .output_config_param import OutputConfigParam as OutputConfigParam`; `:219` — `from .json_output_format_param import JSONOutputFormatParam as JSONOutputFormatParam`. Both importable from `anthropic.types`.
- `anthropic/types/output_config_param.py:11,20` — `class OutputConfigParam(TypedDict, total=False)`, `format: Optional[JSONOutputFormatParam]`.
- `anthropic/types/json_output_format_param.py:9-13` — `schema: Required[Dict[str, object]]`, `type: Required[Literal["json_schema"]]`. A `Mapping[str, Any]` therefore goes in as `dict(schema)`.
- `anthropic/resources/messages/messages.py:133` — the non-streaming `create` overload takes `output_config: OutputConfigParam | Omit = omit`.
- `anthropic/types/message.py:91` — `stop_reason: Optional[StopReason] = None`; `anthropic/types/stop_reason.py:5-7` — `Literal["end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal", "model_context_window_exceeded"]`.

The Ollama adapter:

- `src/advisor/models/ollama_model.py:111-123` — `def complete(self, system, messages, tools) -> ModelTurn:`, builds `body` (`model`, `messages`, `tools`, `stream`, `think`, `options`) and posts it at line 123; nothing precedes the body, so a check at the top runs before any request.
- `src/advisor/models/ollama_model.py:25-34` — `ModelError` already imported.

The judge:

- `src/advisor/evals/judge.py:20` — `from advisor.evals.modeljson import extract_json` (its only use is line 117).
- `src/advisor/evals/judge.py:10,13,17` — `import json`, `from collections.abc import Mapping, Sequence`, `from typing import Any` already imported.
- `src/advisor/evals/judge.py:115-126` — `parse_verdict`: `value = extract_json(text)`; `"the model answer holds no JSON object"`; `"the JSON has no boolean 'pass'"`; `"the JSON has no string 'reason'"`; `return Verdict(passed, reason.strip())`.
- `src/advisor/evals/judging.py:143-148` — `_ask`: `reply = client.complete("", [Message("user", prompt)], [])`; `except ModelError as e: return jg.JudgeError(str(e))`; `return jg.parse_verdict(reply.text or "")`. Called by `judge` at `judging.py:225` and by `judge-validate` at `judging.py:313`.
- `src/advisor/evals/judging.py:151-154` — `_prompt_hash` hashes `jg.build_prompt(None, "[[conversation]]", examples)`, i.e. the template, so a template edit changes it (B9).
- `src/advisor/evals/prompts/judge-no-fit.md:34-35` — `Reply with one JSON object and nothing else:` / `{"pass": true or false, "reason": "<one sentence>"}` (the last two lines; the file is 35 lines).
- `src/advisor/evals/modeljson.py:12` — `def extract_json(text: str) -> Any | None`; used by `generate.py:100` and `taxonomy.py:119` (the spec's `generate.py:132` and `analysis.py:289` are those commands' `complete` calls, not the `extract_json` uses). Untouched here (B10).
- Other `complete` callers, all positional and unchanged: `src/advisor/agent.py:179`, `src/advisor/evals/generate.py:132`, `src/advisor/evals/analysis.py:289`.

Tests:

- `tests/test_models.py:93-103` — `test_fake_records_requests_and_plays_script` (AC1 goes next to it).
- `tests/test_models.py:114-125` — `class FakeSdk`, `_create(self, **kwargs)` appends `kwargs` to `self.calls`.
- `tests/test_models.py:128-138` — `_response(content, model="m-1", usage=(11, 7))` builds a real `anthropic.types.Message` with `stop_reason="end_turn"` hard-coded (line 134).
- `tests/test_models.py:141-165` — `test_adapter_maps_tool_use_and_usage` asserts `sent["model"]`, `["system"]`, `["messages"]`, `["tools"]` one by one, never the key set.
- `tests/test_ollama_model.py:28-45` — `Server` records `self.requests` and `self.bodies`; `:53-79` — `test_request_shape` asserts the whole body.
- `tests/test_agent.py:41-60` — `test_tool_call_then_final_text` holds `fake.requests` (two requests) — AC2's assertion goes here.
- `tests/test_judge.py:125-129` — `test_the_shipped_template_has_both_slots` (`'"pass"' in template`); `:175-178` — `test_the_shipped_template_states_each_rule_of_b3`; `:184-197` — `test_valid_verdicts`, whose cases at lines 189 (`<think>`) and 190-193 (fenced) become errors (AC8); `:200-214` — `test_anything_else_is_a_judge_error`, `isinstance` only.
- `tests/judge_world.py:94-110` — `RoutedClient.complete(self, system, messages, tools)` (no `schema`); `:113-114` — `verdict()` dumps `{"pass": ..., "reason": ...}`.
- `tests/test_analysis_judge.py:43-49` — `ANSWERS["h2"] = "I cannot tell"`; `:95` — expects `"ERROR h2: the model answer holds no JSON object"` (changes with B8's message); `:161-166` — `test_a_model_failure_is_an_error_line_not_a_verdict` (`ModelUnreachableError("Anthropic is down")`).
- `tests/test_analysis_judge_validate.py:30-54` — `h2: "no idea"` is a judge error row; `:51` asserts `owner fail, judge ERROR`.
- `tests/test_boundaries.py:26-27` — `_importers("anthropic") == {"models/anthropic_model.py"}`; `:48-49` — `httpx` only in `models/ollama_model.py`.

Rules and docs:

- `src/advisor/evals/baseline.py:14-25` — `EVAL_PATHS` holds `"src/advisor/models/"` (line 17); `src/advisor/evals/prompts/` is not in it.
- `REVIEW-POLICY.md` → "Live checks", rule 1 — "`src/advisor/models/` (the model adapters)".
- `REVIEW-POLICY.md` → "Tiers" — the Reviewed row's by-meaning paths are `src/advisor/prompts/**`, `guardrails.py`, `cli.py`, `config.py`, `.env.example` files, `tracing.py`; none is touched, so the tier is **Attested** (`src/**` not listed, tests).
- `README.md:314-317` — "a model failure or an answer that is not the JSON verdict is an `ERROR`, never a pass or fail".
- `CLAUDE.md` → "Architecture", the `models/` bullet ("the `ModelClient` protocol and message types (`base.py`) ...").
- `evals/judge/validation.md:8` — "Held-out conversations: 35 (33 with a verdict, 2 judge errors)"; unchanged since `241dfd9`, so the old rates on `6ebf3c6` are the spec's `ca8b032` rates.
- Baseline: `uv run pytest -q` on `6ebf3c6`: 863 passed.

## Subtasks

Each ends with `npm run verify` green and its own commit.

1. **The `schema` keyword through the interface (B1, B2, B3, B5).**
   - `base.py`: `ModelClient.complete(self, system, messages, tools, *, schema: Mapping[str, Any] | None = None) -> ModelTurn`, docstring: "`schema`, when given, is a JSON Schema the reply's text must fit; an adapter that cannot ask its provider for one raises `ModelError`." Import `Mapping`.
   - `fake.py`: `Request` gains `schema: Mapping[str, Any] | None = None` as its last field; `complete` takes the keyword and records it.
   - `anthropic_model.py`: `complete` takes the keyword. Build the messages and tools once; with `schema is None` call `create` with exactly today's five keywords; otherwise the same five plus `output_config=output_config`, where `output_config: OutputConfigParam = {"format": {"type": "json_schema", "schema": dict(schema)}}` (import `OutputConfigParam` from `anthropic.types`; `JSONOutputFormatParam` only if mypy needs the inner dict annotated). Comment at that line: I1 (why `output_config.format`, not a forced tool).
   - `ollama_model.py`: at the top of `complete`, `if schema is not None: raise ModelError("structured output is not supported for Ollama")`, before the body is built (B5; comment: owner's Q2, refuse for now).
   - Tests: AC1, AC2, AC3, AC5 (see Tests).
2. **Refusal and cut-off are errors when a schema was asked for (B4).**
   - `anthropic_model.py`: after the `create` call and only when `schema is not None`: `response.stop_reason == "refusal"` raises `ModelError("Anthropic refused to give the structured reply (stop_reason: refusal)")`; `== "max_tokens"` raises `ModelError(f"Anthropic reply cut off at the token limit ({MAX_TOKENS} tokens)")`. No text is returned in either case. Comment: I3 (only with a schema, since a call without one behaves as today).
   - `tests/test_models.py`: `_response` gains `stop_reason="end_turn"` as a keyword; tests for AC4.
3. **The verdict schema, the strict read and the prompt line (B6, B8, B9).**
   - `judge.py`: `VERDICT_SCHEMA: Mapping[str, Any] = {"type": "object", "properties": {"reason": {"type": "string"}, "pass": {"type": "boolean"}}, "required": ["reason", "pass"], "additionalProperties": False}` with a comment that `reason` comes first so the model writes it before the verdict.
   - `parse_verdict`: `try: value = json.loads(text) except ValueError: value = None`; not a `dict` → `JudgeError("the model answer is not a JSON object")`; the `pass` and `reason` checks and the return as today. Docstring updated to B8; comment: I2 (the shape is still checked by hand). Drop the `extract_json` import (`judge.py:20`).
   - `judge-no-fit.md`: the last line becomes `{"reason": "<one sentence>", "pass": true or false}`; nothing else changes.
   - Tests: AC6, AC8, AC9; `tests/test_analysis_judge.py:95` now expects `"ERROR h2: the model answer is not a JSON object"`.
4. **Every judge call asks for the schema (B7).**
   - `judging.py:145`: `client.complete("", [Message("user", prompt)], [], schema=jg.VERDICT_SCHEMA)`. The `ModelError` path is unchanged.
   - `tests/judge_world.py`: `RoutedClient.complete(..., *, schema=None)` records `self.schemas.append(schema)`; `verdict()` dumps `reason` before `pass` (the shape the schema asks for; either order parses).
   - Tests: AC7.
5. **Docs.** `README.md` → the `judge` bullet (lines 314-317): the judge asks the model for the verdict schema (Anthropic structured output), the reply is read as one JSON object, and a refusal or a reply cut off at the token limit is an `ERROR` naming it. `CLAUDE.md` → the `models/` bullet: `complete` takes an optional `schema`; the Anthropic adapter sends it as `output_config.format` and turns a `refusal` / `max_tokens` stop into `ModelError`, the Ollama adapter refuses it. The **LLM judge** paragraph: `parse_verdict` reads strictly; `extract_json` serves `generate` and `taxonomy` only.
6. **The re-validation (B11; not the implementer's: the owner's live check).** After the review stops for the live check, the owner runs the steps under Validation. The new `evals/judge/validation.md` is committed on the branch (by the owner, or by an agent on the owner's request), followed by a new review round, so the committed file is part of the reviewed commit. `evals/judgements/*.jsonl` are not touched (B12).

## Tests

Every model call is faked (`FakeSdk`, `httpx.MockTransport`, `ScriptedModelClient`, `RoutedClient`); `tests/conftest.py` fails any socket connect. For each behavioural line, the test that fails if it is mutated:

| Line (subtask) | Mutation | Test that fails |
| --- | --- | --- |
| fake records `schema` (1) | record `None` always | `test_fake_records_the_schema_it_was_given` (`test_models.py`, AC1): one call with `schema={"type": "object"}`, one without; asserts `[r.schema for r in fake.requests] == [{"type": "object"}, None]` |
| agent sends no schema (1) | agent passes any schema | `test_tool_call_then_final_text` gains `assert [r.schema for r in fake.requests] == [None, None]` (AC2) |
| adapter adds `output_config` with a schema (1) | drop it / wrong `type` / pass a different schema | `test_adapter_sends_the_schema_as_output_config_format` (AC3): `sent["output_config"] == {"format": {"type": "json_schema", "schema": SCHEMA}}` and `set(sent) == {"model", "max_tokens", "system", "messages", "tools", "output_config"}`, other values as `test_adapter_maps_tool_use_and_usage` asserts |
| no `output_config` without a schema (1) | always send it, or send `omit` | `test_adapter_without_a_schema_sends_exactly_todays_arguments` (AC3): `set(sent) == {"model", "max_tokens", "system", "messages", "tools"}` |
| Ollama refuses a schema (1) | remove the check, or check after the post | `test_a_schema_is_refused_before_any_request` (`test_ollama_model.py`, AC5): `pytest.raises(ModelError)`, message contains `"not supported for Ollama"`, `server.requests == []` (the `Server` gets no responses, so a request would also fail differently) |
| Ollama body unchanged without a schema (1) | add any key | `test_request_shape` (unchanged, whole-body equality) |
| `refusal` raises with a schema (2) | drop the check / return the text | `test_with_a_schema_a_refusal_is_a_model_error` (AC4): message contains `"refusal"` |
| `max_tokens` raises with a schema (2) | drop the check | `test_with_a_schema_a_cut_off_is_a_model_error` (AC4): message contains `"token limit"` |
| `end_turn` with a schema returns the text (2) | raise on every stop reason | `test_with_a_schema_end_turn_returns_the_text` (AC4) |
| checks only with a schema (2) | check regardless of schema | `test_without_a_schema_a_cut_off_returns_its_text_as_today` and the same for `refusal` (AC4) |
| `VERDICT_SCHEMA` content (3) | swap the order, drop a `required`, change a type, drop `additionalProperties` | `test_verdict_schema_asks_for_a_reason_then_a_boolean_pass` (`test_judge.py`, AC6): `list(VERDICT_SCHEMA["properties"]) == ["reason", "pass"]`, the two types, `set(required) == {"reason", "pass"}`, `additionalProperties is False`, `type == "object"` |
| strict `json.loads` (3) | restore `extract_json` | `test_anything_else_is_a_judge_error` gains the prose-wrapped JSON, the fenced reply and the `<think>`-prefixed reply (the two moved from `test_valid_verdicts`), and now asserts the reason: `parse_verdict(text) == JudgeError(expected_reason)` (AC8) |
| not-an-object message (3) | change it | the same parametrised test, reason `"the model answer is not a JSON object"` for prose, fence, `<think>`, `""`, `"[true]"` |
| `pass` / `reason` checks (3) | drop either | the same test: `'{"reason": "r", "pass": "yes"}'` → `"the JSON has no boolean 'pass'"`; `'{"reason": 3, "pass": false}'` → `"the JSON has no string 'reason'"` |
| valid verdicts (3) | drop `.strip()`, invert `pass`, reject extra keys | `test_valid_verdicts`: both key orders, `'  \n{"reason": " ok ", "pass": true}\n'` → `Verdict(True, "ok")`, an extra key accepted (AC8) |
| prompt reply line (3) | revert the order | `test_the_shipped_template_ends_with_the_reply_line_reason_first` (AC9): the last two lines of `PROMPT_PATH.read_text().splitlines()` (after dropping trailing blanks) are `Reply with one JSON object and nothing else:` and `{"reason": "<one sentence>", "pass": true or false}`; `test_the_shipped_template_states_each_rule_of_b3` unchanged |
| `_ask` passes the schema (4) | drop `schema=` / pass another | `test_every_judge_call_asks_for_the_verdict_schema` (`test_analysis_judge.py`, AC7): `client.schemas == [VERDICT_SCHEMA] * 5`; the same for `judge-validate` (`test_analysis_judge_validate.py`, `* 3`) |
| a `ModelError` names itself (4) | swallow the reason | `test_a_refusal_is_an_error_line_naming_it` (`test_analysis_judge.py`): `ModelError("Anthropic refused ... refusal")` for `h1` → `"ERROR h1: Anthropic refused ..."`; in `judge-validate`, the row is a judge error and `validation.md` carries the reason (AC7) |

AC10 is `npm run verify` itself: the `generate` and `taxonomy` tests and `tests/test_boundaries.py` pass unchanged (no new import of `anthropic` outside the adapter; `judge.py` gains none).

Expected count: 863 today, about 880 after (the parametrised additions dominate).

## Validation

- `npm run verify` green after every subtask.
- `npm run check:intent` PASS (feature; core code changes with tests).
- `uv run advisor-analysis owes-run --base main` lists `src/advisor/models/...` (AC12): **an eval run is owed**. The coordinator runs `uv run advisor-eval` on Ollama in the worktree at the reviewed commit and compares it with `evals/baseline.json` (`advisor-analysis compare <report>`). The agent's path sends no schema and its arguments are byte-identical, so no flip is expected; any flip is re-run with `--only` before it is called a regression (`REVIEW-POLICY.md` → "Eval runs").
- **Live check: owed** (rule 1, `src/advisor/models/`). The owner, in the §24 worktree (it has no `evals/runs/`, which is gitignored), with `ANTHROPIC_API_KEY` set in the environment or the worktree's `.env`:
  1. `uv run advisor-analysis judge-validate --runs-dir <main checkout>/evals/runs` → it completes on `claude-haiku-5-5` (the model accepts `output_config.format`; a rejection shows as an `ERROR <ref>: Anthropic call failed: <error class>` line, e.g. `BadRequestError`, for every conversation). Open `evals/judge/validation.md`: no judge error reads "the model answer is not a JSON object", "the JSON has no boolean 'pass'" or "the JSON has no string 'reason'" (I4); a refusal or cut-off, if any, is named. The prompt sha256 differs from `a6cff797...` (B9). 35 paid calls.
  2. `ADVISOR_MODEL_PROVIDER=anthropic uv run advisor "<a catalogue question>"` → a normal answer (the no-schema path of the adapter, unchanged).
  3. The new `validation.md` is committed on the branch (subtask 6), then a review round; the review quotes the old rates (TPR 0.52 (11/21), TNR 0.75 (9/12), 2 judge errors, from `6ebf3c6` = `ca8b032`) beside the new ones.
- Tier: Attested (no by-meaning path; `review_tier` empty).

## Assumptions I made

- **One message for "not valid JSON" and "valid JSON but not an object".** B8 names "the model answer is not a JSON object" for invalid JSON and says a non-object value is a `JudgeError` "as today". Today's wording ("holds no JSON object") described the lenient scan, which is gone; the new message is literally true of both, so both use it. Both are B8 (format) reasons for I4 either way.
- **Two `create` calls behind one `if`**, not a `**kwargs` dict: it keeps `create`'s overloads type-checked under `mypy --strict` and keeps the keyword set exact for AC3.
- **`dict(schema)`** in the adapter: `JSONOutputFormatParam.schema` is `Dict[str, object]` and B1's parameter is a `Mapping`; a shallow copy also keeps the SDK from holding the module constant.
- **`model_context_window_exceeded` is not handled.** The spec names only `refusal` and `max_tokens` (B4); a judge prompt of a few thousand tokens cannot reach it. If it did, the truncated text would fail the strict read and show as a B8 reason.
- **The error message texts** (`"Anthropic refused to give the structured reply (stop_reason: refusal)"`, `"Anthropic reply cut off at the token limit (1024 tokens)"`, `"structured output is not supported for Ollama"`) are mine; the spec fixes only what they must name. They hold no model text.
- **`RoutedClient.verdict()` dumps `reason` first** so the test world sends what the schema asks for; the parse accepts either order (AC8), so no behaviour rests on it.
- **Docs (subtask 5)** are not in the spec's ACs but pass 7 asks for them (`REVIEW-POLICY.md` → "Passes", 7).
- **No new dependency, no SDK bump**: `OutputConfigParam` is in the installed 2.6.0.
- **§27 is the only prerequisite** and is merged (`blocked_by: 27` is already cleared); no other blocker found.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
