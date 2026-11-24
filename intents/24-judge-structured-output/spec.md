<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §24 spec — Constrain the LLM judge's reply to its verdict schema

Accepted intent: [intent.md](intent.md)

Written against `main` at `ca8b032`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/16-llm-judge/spec.md` B4 | "The model answers JSON `{"pass": true\|false, "reason": "<one sentence>"}`, read with `extract_json`. Anything else is a judge error for that case: recorded, never a pass or fail." This spec **amends B4**: the reply is constrained by a schema and read strictly (B5, B6 below); "a judge error, never a pass or fail" stays. |
| `intents/16-llm-judge/spec.md` B5 | The judge is `anthropic`, `claude-haiku-5-5`; "`--model` may override the model, not the provider". Unchanged. |
| `src/advisor/evals/judging.py:143-148` (`_ask`) | Today: `client.complete("", [Message("user", prompt)], [])`, a `ModelError` becomes `JudgeError(str(e))`, the text goes to `jg.parse_verdict(reply.text or "")`. |
| `src/advisor/evals/judge.py:115-126` (`parse_verdict`) | Today: `extract_json`, then "the model answer holds no JSON object", "the JSON has no boolean 'pass'", "the JSON has no string 'reason'". |
| `src/advisor/evals/prompts/judge-no-fit.md` (last two lines) | "Reply with one JSON object and nothing else:" / `{"pass": true or false, "reason": "<one sentence>"}` |
| `src/advisor/models/base.py:83-88` | `ModelClient.complete(self, system, messages, tools) -> ModelTurn`: no way to ask for a reply shape. |
| `src/advisor/models/anthropic_model.py:67-93` | `complete` calls `self._sdk.messages.create(model=…, max_tokens=MAX_TOKENS, system=…, messages=…, tools=…)`, never reads `stop_reason`; `MAX_TOKENS = 1024` (line 22). |
| Installed SDK, `anthropic` 2.6.0 (`.venv/Lib/site-packages/anthropic/_version.py:2`) | See "The mechanism the SDK supports" below. |
| `evals/judge/validation.md:8` | "Held-out conversations: 35 (33 with a verdict, 2 judge errors)"; both errors (lines 22 and 51) read "judge: the model answer holds no JSON object". |
| `REVIEW-POLICY.md` → "Live checks", rule 1 | The diff touches `src/advisor/models/` ("the model adapters"): a live check is owed. |
| `REVIEW-POLICY.md` → "Eval runs" | `src/advisor/models/` is in `EVAL_PATHS` (`src/advisor/evals/baseline.py:14-25`): an eval run is owed, "on the local model (Ollama)". |
| `CLAUDE.md` → "Conventions worth knowing" | "`anthropic` only in `models/anthropic_model.py` … (`tests/test_boundaries.py` enforces it)". |

### The mechanism the SDK supports

The installed SDK 2.6.0 supports **structured outputs on the plain, non-beta
`messages.create`** through `output_config.format`:

- `resources/messages/messages.py:133`: the non-streaming `create` overload
  takes `output_config: OutputConfigParam | Omit = omit`; its docstring
  (line 264): "output_config: Configuration options for the model's output,
  such as the output format."
- `types/output_config_param.py:20-25`: `format: Optional[JSONOutputFormatParam]`,
  "A schema to specify Claude's output format in responses. See [structured
  outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)".
- `types/json_output_format_param.py:9-13`: `schema: Required[Dict[str, object]]`
  and `type: Required[Literal["json_schema"]]`.
- `resources/messages/messages.py:1292-1366` (`stream`) and `1408`ff
  (`parse`) also take `output_format`, a Python **type** turned into a
  schema by `lib/_parse/_transform.py:98` (`transform_schema`, which sets
  `additionalProperties` to `False`, line 177); a dict there raises
  "`output_format` must be a type; pass a schema dict as
  `output_config={'format': ...}` instead" (line 1343).
- `types/stop_reason.py`: `StopReason` includes `"max_tokens"` and
  `"refusal"`; `types/message.py:85-91`: `stop_details` and `stop_reason`
  on the response.

The alternative, a forced single tool call, is also available:
`tool_choice` on `create` (`messages.py:140`, `types/tool_choice_tool_param.py`,
`{"type": "tool", "name": …}`) with `strict: bool` on a tool
(`types/tool_param.py:79-80`, "When true, guarantees schema validation on
tool names and inputs"). This spec uses `output_config.format` (B3,
Interpretation I1). No SDK bump and no new dependency are needed.

What the SDK cannot tell: whether `claude-haiku-5-5` accepts
`output_config.format` (the SDK has no per-model capability list;
`types/model_param.py:10` only names the model). The live check (AC11)
settles it; an unsupported model gives an API error, which B7 already
turns into a named `JudgeError`.

## Behaviour

**The interface**

- **B1. A reply shape can be asked for.** `ModelClient.complete` gains one
  optional keyword-only parameter, `schema: Mapping[str, Any] | None = None`,
  a JSON Schema for the reply's text. `None` (the default) means exactly
  today's behaviour, in every adapter and in the fake. Positional calls
  (`agent.run_agent`, `generate`, `taxonomy`) do not change and send no
  schema.
- **B2. The fake records it.** `ScriptedModelClient` records the schema it
  received on each `Request` (`schema`, `None` when none was given), so a
  test can assert what a caller asked for.

**The Anthropic adapter**

- **B3. A schema goes to the provider's structured output.** With a schema,
  `AnthropicClient.complete` adds
  `output_config={"format": {"type": "json_schema", "schema": <schema>}}`
  to `messages.create`; every other argument is as today. Without one, the
  `messages.create` arguments are exactly today's (no `output_config` key
  at all).
- **B4. A reply the provider could not complete is an error, when a schema
  was asked for.** With a schema, a response whose `stop_reason` is
  `"refusal"` raises `ModelError` with a message naming the refusal, and
  one whose `stop_reason` is `"max_tokens"` raises `ModelError` naming the
  cut-off at the token limit. The text is not returned in either case.
  Without a schema, `stop_reason` is not read (today's behaviour).

**The Ollama adapter**

- **B5. Ollama refuses a schema.** `OllamaClient.complete` with a schema
  raises `ModelError` ("structured output is not supported for Ollama" or
  similar) before any HTTP request. Without one, the request body is
  exactly today's. (Open question Q2: map it to Ollama's `format` instead.)

**The judge**

- **B6. The verdict schema.** `judge.py` holds `VERDICT_SCHEMA`, a JSON
  Schema object with properties `reason` (string) then `pass` (boolean),
  both required, `additionalProperties: false`. `reason` comes first so the
  model writes its reason before its verdict.
- **B7. Every judge call asks for it.** `judging._ask` (used by both `judge`
  and `judge-validate`) calls `client.complete("", [Message("user",
  prompt)], [], schema=jg.VERDICT_SCHEMA)`. A `ModelError` (an API error, a
  refusal or a cut-off per B4) is a `JudgeError` with `str(e)` as its
  reason, as today, so the ERROR line and `validation.md` say which.
- **B8. The verdict is read strictly.** `parse_verdict` reads the reply
  with `json.loads` of the whole text (surrounding whitespace allowed), not
  with `extract_json`. Not valid JSON (prose, a code fence, `<think>`
  blocks, an empty reply) is a `JudgeError` "the model answer is not a JSON
  object"; a JSON value that is not an object, or lacks a boolean `pass` or
  a string `reason`, is a `JudgeError` as today. A valid verdict is
  `Verdict(pass, reason.strip())` as today; extra keys are ignored.
- **B9. The prompt's reply line matches the schema.** The prompt keeps its
  "Reply with one JSON object and nothing else:" line, with the example
  reordered to `{"reason": "<one sentence>", "pass": true or false}`. The
  rest of the prompt is unchanged. The prompt hash (`_prompt_hash`, of the
  template) changes, which marks every new judgement and `validation.md` as
  a new prompt.
- **B10. `extract_json` stays** in `modeljson.py`, used by `generate`
  (`generate.py:132`) and `taxonomy` (`analysis.py:289`) exactly as today.

**The record**

- **B11. Re-validation.** Once built, and at the owner's request (paid
  Anthropic tokens), `advisor-analysis judge-validate` is run on the
  committed split and the new `evals/judge/validation.md` replaces the old
  one in the branch. Its judge errors, if any, carry a reason from B4 or an
  API error, never a B8 format reason. The review quotes the old and new
  rates side by side (the old ones from `ca8b032`).
- **B12. Old judgements stay.** `evals/judgements/*.jsonl` are not
  rewritten by this intent; each line already names its `prompt_sha256`,
  so old and new judgements stay distinguishable. A later `judge` run
  rewrites its file whole, as §16 B9 says.

## Interpretations

- **I1. "The provider's own structured-output mechanism"** (intent,
  Outcome) is read as `output_config.format` with `type: "json_schema"`,
  not a forced tool call. Reason: it is the SDK's named structured-output
  parameter (`output_config_param.py:20-25`), it returns the verdict as the
  reply's text so `ModelTurn.text` carries it with no new field, and it
  keeps the judge apart from the tool path the agent uses. A forced tool
  would need `tool_choice` on the protocol too. (Comment at the
  `output_config` line in `anthropic_model.py`.)
- **I2. "Read without the lenient scan"** is read as `json.loads` of the
  whole text, with only surrounding whitespace allowed. The schema still is
  checked by hand after parsing (B8), because a fake, a future provider or
  a changed schema can return any shape; the check costs nothing. (Comment
  in `parse_verdict`.)
- **I3. "A reply the provider still could not complete (a refusal, a
  cut-off at the token limit, an API error)"** is read as the adapter
  raising `ModelError` on `stop_reason` `refusal` or `max_tokens` when a
  schema was asked for (B4), so the existing `ModelError` → `JudgeError`
  path names it. It is not done without a schema, because the intent's
  constraint says "a call without a schema behaves exactly as today".
  (Comment at the `stop_reason` check.)
- **I4. "0 judge errors that are format errors"** (intent, Outcome) is read
  as: no `JudgeError` in the new `validation.md` carries a B8 reason (not a
  JSON object, no boolean `pass`, no string `reason`). A refusal, a cut-off
  or an API error may still occur and is reported by name; it is not a
  format error. Today's two errors cannot be told apart after the fact:
  "the model answer holds no JSON object" covers both prose and a reply cut
  off mid-JSON, since the adapter never read `stop_reason`.
- **I5. The judge's provider pin stays** (§16 B5): B5's Ollama refusal is
  reached only if someone wires the judge to Ollama, which nothing does.

## Acceptance criteria

- **AC1** (B1, B2): the fake records `schema` per request, `None` when the
  caller gave none. (test: `tests/test_models.py`, next to
  `test_fake_records_requests_and_plays_script`)
- **AC2** (B1, agent unchanged): every request the agent sends in the
  existing agent tests has `schema is None`. (test: one new assertion in
  `tests/test_agent.py`)
- **AC3** (B3): with a schema, the faked SDK receives `output_config ==
  {"format": {"type": "json_schema", "schema": <the schema>}}` and the
  other arguments as today; without one, the received keyword set is
  exactly `{model, max_tokens, system, messages, tools}`. (test:
  `tests/test_models.py` with `FakeSdk`)
- **AC4** (B4): with a schema, a faked response with `stop_reason`
  `"refusal"` and one with `"max_tokens"` each raise `ModelError` whose
  message names which; with `"end_turn"` the text comes back; without a
  schema, a `"max_tokens"` response returns its text as today. (test:
  `tests/test_models.py`)
- **AC5** (B5): `OllamaClient.complete(..., schema=…)` raises `ModelError`
  and its transport receives no request; without a schema the body is as
  in `test_request_shape`. (test: `tests/test_ollama_model.py`)
- **AC6** (B6): `VERDICT_SCHEMA` has `reason` before `pass` in
  `properties`, both `required`, the types string and boolean, and
  `additionalProperties: false`. (test: `tests/test_judge.py`)
- **AC7** (B7): `judge` and `judge-validate` over a fake client send
  `schema == VERDICT_SCHEMA` on every call; a `ModelError("…refusal…")`
  from the client gives an `ERROR <id>: …refusal…` line and, in
  `judge-validate`, a judge-error row with that reason. (test:
  `tests/test_analysis_judge.py`, `tests/test_analysis_judge_validate.py`;
  `RoutedClient` in `tests/judge_world.py` accepts and records `schema`)
- **AC8** (B8): `parse_verdict` accepts `{"reason": …, "pass": …}` in either
  key order and with surrounding whitespace; it returns a `JudgeError` for
  JSON inside prose, inside a code fence, after a `<think>` block, for
  `""`, `[true]`, a non-boolean `pass` and a non-string `reason`. The two
  lenient cases of today's `test_valid_verdicts` (the `<think>` and the
  fenced reply) move to the error list. (test: `tests/test_judge.py`)
- **AC9** (B9): the shipped prompt ends with the reply line naming
  `"reason"` before `"pass"`, and the B3 rule assertions
  (`test_the_shipped_template_states_each_rule_of_b3`) still pass. (test:
  `tests/test_judge.py`)
- **AC10** (B10, boundaries): `generate` and `taxonomy` tests pass
  unchanged; `tests/test_boundaries.py` passes (`anthropic` only in the
  adapter; `judge.py` imports no SDK). (`npm run verify`)
- **AC11** (B3, B4, B11; live check, owed by rule 1): the owner runs
  `uv run advisor-analysis judge-validate` with `ANTHROPIC_API_KEY` set; it
  completes on `claude-haiku-5-5` (the model accepts `output_config.format`),
  and the new `validation.md` shows 0 judge errors with a B8 reason. The
  owner also runs one `uv run advisor "<question>"` with
  `ADVISOR_MODEL_PROVIDER=anthropic` and sees a normal answer (the
  no-schema path). The new `validation.md` is committed; the review quotes
  old and new rates. (manual, the owner)
- **AC12** (eval run owed): `advisor-analysis owes-run --base main` lists
  `src/advisor/models/…`; the coordinator's Ollama run, compared against
  the baseline, is named in the review, and any flip is explained (the
  agent's path does not change, so none is expected). (review, per
  `REVIEW-POLICY.md` → "Eval runs")

## Non-functional

- **Boundaries:** the schema and the strict parse live in `judge.py` (pure,
  tested like core). The SDK mapping (`output_config`, `stop_reason`) lives
  only in `models/anthropic_model.py`. `judging.py` passes the schema and
  imports no SDK. `ModelClient` in `models/base.py` changes (B1): every
  implementation (`AnthropicClient`, `OllamaClient`, `ScriptedModelClient`,
  and the tests' `RoutedClient`) accepts the keyword. **This touches the
  same `complete` that §23 (`refactor/23-typed-anthropic-adapter`) is
  typing**; see Q1.
- **Data:** no new data. Judged conversations and reasons are eval data
  (§19); nothing in logs or the review quotes session transcripts.
  `validation.md` is replaced (B11); judgements are not (B12).
- **Model use:** the judge's calls only: one Anthropic call per in-scope
  conversation, `claude-haiku-5-5`, `max_tokens` 1024 as today, plus the
  schema. Latency and cost about as today; a re-validation is 35 calls on
  the owner's key, run only at the owner's request. When the model is down
  or rejects the schema, each conversation is an ERROR line with the API
  error's name (B7), never a pass or fail. The agent's calls and the
  Ollama default are unchanged.
- **Autonomy:** none changes. The judge scores; it never edits labels or
  answers anyone. Agents never run the paid judge on their own.

## Out of scope

- Structured output for `generate` and `taxonomy`, and for the agent's tool
  calls (intent, Constraints).
- Mapping a schema to Ollama's `format` (B5 refuses; Q2).
- A new provider for the judge, or a change of judge model.
- Changing the judging rules, the few-shot split or the trust thresholds.
  The new rates are reported whatever they are; making the judge trusted is
  not this intent's outcome.
- Re-running `judge` on the existing reports (B12).
- Using `messages.parse` / `output_format` with a Python type (a pydantic
  model would bring a typed parse path into the adapter; the dict schema
  is enough).

## Assumptions I made

- **The intent's open design questions**, answered:
  - *How a schema reaches the provider:* an optional keyword on
    `ModelClient.complete` (B1), not a judge-only protocol. It is one
    defaulted parameter, the agent's calls do not change, and `generate` /
    `taxonomy` can use it later. A narrower path (a second protocol only
    the Anthropic adapter implements) would avoid touching Ollama and the
    fake but would make `judging.py` depend on a concrete adapter shape.
  - *Field order:* `reason` before `pass` (B6, B9). The judge is
    re-validated anyway (B11), and a reason written first is the usual
    reason to order it so. Not verified: that the API generates properties
    in schema order (see weak points).
  - *Mechanism:* `output_config.format` (I1), supported by SDK 2.6.0 on
    plain `messages.create`; `claude-haiku-5-5` support is left to the live
    check (AC11).
  - *The prompt's "Reply with one JSON object" line:* kept, reordered (B9).
    The schema constrains the shape, but the line still tells the model
    what `reason` and `pass` mean, and dropping it changes more than needed.
  - *Old judgements and `validation.md`:* `validation.md` replaced, with
    the old rates quoted in the review and kept in git; judgements kept
    (B11, B12).
- **Refusal and cut-off are raised in the adapter, not carried on
  `ModelTurn`** (B4, I3). A `stop_reason` field on `ModelTurn` would change
  the protocol's data type for every adapter; raising `ModelError` reuses
  the path `_ask` already has. It applies only when a schema was asked
  for.
- **Ollama refuses rather than maps** (B5): nothing sends it a schema, the
  intent puts other callers out of scope, and a mapping could not be
  checked without a live Ollama run. Q2 asks the owner.
- **The two current errors are not shown to be format errors.** Both read
  "the model answer holds no JSON object", which today also covers a reply
  cut off at 1024 tokens (`stop_reason` is never read). The spec promises
  only that B8 reasons disappear (I4), not that the count goes to 0.
- **No test calls a model**: the adapter is tested through `FakeSdk`, the
  judge through `ScriptedModelClient` / `RoutedClient`; the only real calls
  are the owner's (AC11).
- **No `blocked_by`.** §24 is buildable on `main` as it is; the overlap
  with §23 is a merge, not a prerequisite (Q1).

## Open questions for the owner

- **Q1. Build §24 after §23 merges?** Both change
  `AnthropicClient.complete` and `tests/test_models.py` (`FakeSdk`). §23
  types the `messages.create` call against the SDK (`MessageParam`,
  `anthropic.types.Message`); §24 adds `output_config` and reads
  `stop_reason` in the same call. Recommended: yes, build §24 on top of
  §23 (record `23` in `blocked_by`), because `output_config` then gets the
  SDK's `OutputConfigParam` type for free and `stop_reason` is a typed
  field instead of an `Any` attribute; the alternative is a hand merge of
  the same twenty lines.
- **Q2. Should Ollama map a schema to its `format` field instead of
  refusing it?** Recommended: refuse now (B5), map it in the later intent
  that brings structured output to `generate` / `taxonomy`, where an Ollama
  caller exists and a live run can check it.
