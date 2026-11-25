<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §31 plan — Search the catalogue before answering about products

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`run_agent` stops taking a text-only reply as the answer while no
`search_products` call has been made in the run. The first such reply is
kept in the conversation as an assistant message, the agent adds one
user-role message asking the model to search (`SEARCH_FIRST_TEXT`), and the
loop goes on within the same 5 turns. A text-only reply after that request
is the answer, whatever it says, so a model that declines an off-topic
question can still decline. The request is made at most once per run, and
never on turn 5 (no turn is left to answer it). `MAX_TURNS`,
`FALLBACK_ANSWER` and `REFUSAL_TEXT` do not change; the prompt does not
change. The eval run then shows whether the five no-search cases now search
and what the four `off-topic-*` cases did.

## Risks

- **Pass 9 footguns.** `REVIEW-POLICY.md:250` — "This list starts empty and
  grows from findings"; it names none yet, so nothing repo-specific to
  check beyond the general passes.
- **29 existing tests break with the change, and fixing them can hide it.**
  A prototype of the change in a scratch copy (not committed) failed 2 tests
  in `tests/test_agent.py`, 1 in `tests/test_boundaries.py`, 3 in
  `tests/test_cli_stderr.py` and 23 in `tests/test_evals_run.py`: every
  scripted fake whose first text comes before any search now gets a second
  request and runs out of script (or, in `test_evals_run.py`, eats the next
  case's script). The updates must keep what each test proved: a
  text-only fixture becomes "the model says the same thing again after the
  request" (`[ModelTurn(text=…)] * 2`), never "the model searches", so
  `test_expect_search_is_read_through_the_recording_tracer` still proves a
  no-search answer fails the search check. Request counts change only where
  the extra turn explains them.
- **Tests that pass whatever the code does.** `repeat_last=True` on a
  subprocess probe would also hide a loop that asks twice; it is used only
  in the two probes that test logging, not the loop, and the loop's own
  tests use exact scripts (an exhausted script raises).
- **Turn 5.** A text-only reply on turn 5 with no search: asking would
  replace a real answer with `FALLBACK_ANSWER`. The plan returns the text
  (see Assumptions); a test pins it.
- **Which call counts as a search.** A `search_products` call whose
  arguments were invalid still counts (the model tried the catalogue); a call
  to any other tool name does not. Both are pinned by tests.
- **Off-topic regressions.** The four `off-topic-*` cases may now search
  and then cite a product, which fails `declines`
  (`src/advisor/evals/score.py:218`). Reported by the eval run, decided by
  the owner per "Eval runs"; the request's wording invites a decline.
- **Stale line citations.** All below were read at `2e3b7f4`; §30, §32, §33
  and §35 are open and may move `agent.py`, `tests/test_agent.py` or
  `tests/test_evals_run.py`. Re-check before launch.
- **Provider adapters.** An assistant message with text and no tool calls,
  followed by a plain user message, must be valid for both adapters. Both
  already convert it (cited below); no adapter changes, so no rule-1 live
  check.

## Verified against the codebase

Re-read on `main` at `2e3b7f4`.

- `src/advisor/agent.py:28` — `MAX_TURNS = 5`
- `src/advisor/agent.py:29-31` — `FALLBACK_ANSWER = ("I couldn't find a good answer to that. Try asking about a product category or a price range.")`
- `src/advisor/agent.py:170-188` — `run_agent`: `messages: list[Message] = [Message("user", question)]`, `for turn in range(1, MAX_TURNS + 1):`, `reply = client.complete(system, list(messages), specs)`, `tracer.generation(...)`, then
  `if not reply.tool_calls:` / `if reply.text:` / `return AgentResult(reply.text, turn, False)` / `continue`; tool turns append `Message("assistant", reply.text or "", reply.tool_calls)` and `Message("user", tool_results=results)`; after the loop `return AgentResult(FALLBACK_ANSWER, MAX_TURNS, True)`.
- `src/advisor/agent.py:153-167` — `_execute`: unknown tool and `ToolError` give an error `ToolResult`; the call still reached `tracer.tool`.
- `src/advisor/agent.py:191-218` — `answer_question` calls `run_agent` once inside one trace; unchanged.
- `src/advisor/models/base.py:52-64` — `@dataclass(frozen=True) class Message`: `role`, `text`, `tool_calls`, `tool_results` (so `==` compares messages in tests).
- `src/advisor/models/fake.py:45` — `self.requests.append(Request(system, tuple(messages), tuple(tools), schema))` (each request is a snapshot); `fake.py:47-49` — an exhausted script raises `AssertionError` unless `repeat_last`.
- `src/advisor/models/anthropic_model.py:36-44` — an assistant message becomes text block plus tool_use blocks (text-only is valid); `:56` — `return {"role": "user", "content": m.text}`.
- `src/advisor/models/ollama_model.py:64-65` — `{"role": "assistant", "content": m.text}`; `:78` — `out.append({"role": "user", "content": m.text})`.
- `src/advisor/tracer.py:24-26` — `Tracer.generation(model, usage, text, tool_names)`; the protocol has no event for an agent-added message.
- `src/advisor/evals/run.py:96-97` — the recording tracer's `generation` appends `{"text": text, "tools": list(tool_names)}` to `turns`; `run.py:374` — `record["turns"] = tracer.turns`.
- `src/advisor/evals/score.py:215-218` — `if case.must_decline:` … `declined = not cited or answer.strip() == REFUSAL_TEXT`.
- `src/advisor/evals/baseline.py:15-17` — `EVAL_PATHS` contains `"src/advisor/agent.py"`: an eval run is owed.
- `scripts/intent-check-lib.mjs:155-156` — `CORE_CODE` includes `^src\/advisor\/(agent|catalogue|guardrails)\.py$`.
- `REVIEW-POLICY.md:76-81` — live-check rule 1 paths: `cli.py`, `models/`, `tracing.py`, `prompts/`, `infra/`; `agent.py` is not one.
- `tests/test_agent.py:31-32` — `def final(text)`; `:27-28` — `def call(args, name="search_products", cid="c1")`.
- `tests/test_agent.py:41-62` — `test_tool_call_then_final_text`: `assert len(fake.requests) == 2`.
- `tests/test_agent.py:82-92` — `test_fallback_after_exactly_five_turns`; `:95-99` — `test_final_text_on_fifth_turn_is_kept` (`[call({})] * 4 + [final("late")]`, searches, so unaffected).
- `tests/test_agent.py:102-108` — `test_unknown_tool_gives_error_result_and_counts_as_a_turn`: `[call({}, name="launch_rocket"), final("sorry")]` (breaks: no search before "sorry").
- `tests/test_agent.py:111-125` — `test_bad_arguments_give_error_result`: invalid `search_products` call, then `final("fixed")` (must keep passing: an invalid search counts).
- `tests/test_agent.py:155-158` — `test_empty_turn_counts_and_continues`: `[ModelTurn(), final("then text")]` (breaks; the intent says it is updated).
- `tests/test_agent.py:161-174` — `test_tracer_sees_generations_and_tools_in_order`.
- `tests/test_boundaries.py:80,93` — `test_an_untraced_eval_run_loads_neither_tracing_nor_langfuse`, probe line `"client = ScriptedModelClient([ModelTurn(text=text)])\n"`.
- `tests/test_cli_stderr.py:32` — probe line `client = ScriptedModelClient([ModelTurn(text="Fine answer.")])`.
- `tests/test_evals_run.py:42-44` — `HP_BAD`, `LAP_OK`, `OFF_OK`: one text-only `ModelTurn` each; `:111-116` — `assert len(factory.client.requests) == 3`; `:200-205` — `assert len(factory.client.requests) == 2`; `:231` — `answer_only = [ModelTurn(text=…)]`; `:556-600` — `test_the_langfuse_side_sees_the_same_calls_as_the_recording_tracer`, `lap = [` at `:568` (unknown tool, then text: breaks) and the expected `tf.tracers[1].calls`.
- `CLAUDE.md:171-174` — "`agent.py`: `run_agent` (the tool loop, at most 5 model turns, error tool results for bad calls, fixed fallback answer)".
- `README.md:69-77` — "## Run": what a run prints; no description of the loop.
- `evals/runs/20261124T215703Z-ollama.json` — qwen3:8b, 38/50 passed; `searches` empty for `tv-sound`, `laptop-bathrom-projector`, `pelagic-studio-back-soon`, `norvik-fold-brother-gift`, `aurelis-home-gift-mum` (FAIL, 1 turn each) and `off-topic-weather`, `off-topic-poem`, `off-topic-sourdough`, `off-topic-zone-two` (PASS, 1 turn each). `evals/baseline.json` has `source` `20261124T215703Z-ollama.json`.

## Subtasks

1. **Failing-first tests (not committed red).** Write tests T1, T2, T5,
   T6, T7, T8 and T9 below in `tests/test_agent.py`, run them against the
   unchanged `agent.py`, and record in Progress which fail and how. T1, T2,
   T5, T6, T7 and T9 must fail there (today the first text is returned);
   T8 passes today and guards the change against over-reach. Do not
   commit this state.
2. **The change, with every test updated (one commit, verify green).** In
   `src/advisor/agent.py`:
   - add the constant
     ```python
     SEARCH_FIRST_TEXT = (
         "You answered without searching the catalogue. If my question is about "
         "products, call search_products first and answer from what it returns. "
         "If it is not about the shop's products, reply without searching."
     )
     ```
   - in `run_agent`, two locals `searched = False` and `asked = False`;
     after a tool turn, `searched` becomes true if any call's name is
     `"search_products"` (whatever its result); on a text-only reply,
     return it if `searched or asked or turn == MAX_TURNS`, otherwise set
     `asked = True`, append `Message("assistant", reply.text)` and
     `Message("user", SEARCH_FIRST_TEXT)`, and `continue`. Empty replies
     keep today's `continue`. The docstring says the one request.
   - Update the broken tests as in "Tests" → "Existing tests", and add the
     new ones. `npm run verify` green; commit.
3. **Docs (one commit).** `CLAUDE.md:171-174`: add "asks once to search
   when the model answers in text before any `search_products` call (§31)"
   to the `agent.py` line. `README.md` "## Run": one sentence that the
   agent asks the model once to search the catalogue when it answers
   without searching. `npm run verify` green; commit. Set `status:
   in-review`.
4. **Eval run (coordinator, not the implementer).** Owed by path
   (`agent.py` is in `EVAL_PATHS`). Run on Ollama in the worktree at the
   reviewed commit, as in Validation.

## Tests

New tests in `tests/test_agent.py` (all with `ScriptedModelClient`, exact
scripts, no `repeat_last`):

- **T1 `test_text_before_any_search_gets_one_request_to_search`** (the
  failing-first test from the intent): script
  `[final("Let me check the catalogue."), call({"category": "phone", "max_price": 80}), final("Try P-002.")]`.
  Asserts `answer == "Try P-002."`, `turns == 3`, `not fallback`,
  `len(fake.requests) == 3`, and
  `fake.requests[1].messages[-2:] == (Message("assistant", "Let me check the catalogue."), Message("user", SEARCH_FIRST_TEXT))`.
  Kills: returning the first text (today's code); dropping the assistant
  message; a different or empty request text.
- **T2 `test_text_after_the_request_is_the_answer`**: script
  `[final("I only help with electronics."), final("Sorry, I only help with electronics.")]`.
  Asserts the answer is the second text, `turns == 2`, `not fallback`,
  2 requests, and `SEARCH_FIRST_TEXT` appears exactly once in
  `fake.requests[1].messages`. Kills: removing `asked` from the return
  condition or `asked = True` (asks again, script exhausted); returning
  `FALLBACK_ANSWER` after the request.
- **T3 (existing, tightened) `test_tool_call_then_final_text`**: keeps
  `len(fake.requests) == 2`; add that no message in
  `fake.requests[1].messages` has `text == SEARCH_FIRST_TEXT`. Kills:
  never setting `searched` (would ask after a search).
- **T4 (existing) `test_bad_arguments_give_error_result`**: unchanged; an
  invalid `search_products` call then `final("fixed")` must answer
  "fixed" with 2 requests. Kills: counting only successful searches.
- **T5 (replaces `test_unknown_tool_gives_error_result_and_counts_as_a_turn`)**:
  script `[call({}, name="launch_rocket"), final("sorry"), final("sorry again")]`.
  Asserts the error result as today, `answer == "sorry again"`, 3
  requests, and `fake.requests[2].messages[-1] == Message("user", SEARCH_FIRST_TEXT)`.
  Kills: counting any tool call as a search.
- **T6 (replaces `test_empty_turn_counts_and_continues`)**: script
  `[ModelTurn(), final("then text"), final("after request")]`. Asserts
  `answer == "after request"`, `turns == 3`, 3 requests. Kills: asking on
  an empty reply or treating the empty turn as a search.
- **T7 `test_the_request_uses_one_of_the_five_turns`**: script
  `[final("x")] + [call({"category": "phone"})] * 4`. Asserts 5 requests,
  `answer == FALLBACK_ANSWER`, `fallback`, `turns == MAX_TURNS`, and
  `fake.requests[1].messages[-1].text == SEARCH_FIRST_TEXT`. Kills: giving
  the request a turn of its own (6 requests) or a different cap.
- **T8 `test_text_on_the_last_turn_is_kept_without_a_search`**: script
  `[call({}, name="nope")] * 4 + [final("late")]`. Asserts
  `answer == "late"`, `not fallback`, 5 requests. Kills: dropping
  `turn == MAX_TURNS` from the return condition (would fall back).
- **T9 `test_the_request_shows_as_one_more_generation_in_the_trace`**:
  `RecordingTracer`, the T1 script. Asserts
  `tracer.kinds == ["generation", "generation", "tool", "generation"]` and
  `tracer.events[0][3] == "Let me check the catalogue."`. Kills: a tracer
  call added or lost around the request (the trace stays one trace with
  one generation more).
- **Pinned wording**: T1 compares with the constant; a separate assertion
  pins `SEARCH_FIRST_TEXT` to its text (as
  `test_fallback_after_exactly_five_turns` pins `FALLBACK_ANSWER`), so a
  wording change shows in review.

Existing tests updated, each keeping what it proved:

- `tests/test_evals_run.py:42-44`: `HP_BAD`, `LAP_OK`, `OFF_OK` become
  `[ModelTurn(text=…)] * 2` (the model says the same thing after the
  request); `:231` `answer_only` likewise (still never searches, so the
  search check still fails). `:116` request count 3 → 5; `:205` 2 → 4.
  `:568` `lap` gains a second `ModelTurn(text="Sorry, I could not look that up.", usage=u3, model="m-3")`,
  and the expected `tf.tracers[1].calls` gains one more `generation` entry
  before the output check.
- `tests/test_cli_stderr.py:32` and `tests/test_boundaries.py:93`: the
  probe's client gets `repeat_last=True`. These test logging and imports,
  not the loop; the answer printed is still the scripted text.
- No other test needs a change: the prototype run left every other
  failure to the scratch copy's missing files, which also failed without
  the change.

Every model call in the suite stays faked; `tests/conftest.py` still fails
any socket connect.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (fix: core code `agent.py` changed with
  tests in the same branch).
- Eval run (owed: `uv run advisor-analysis owes-run --base main` names
  `src/advisor/agent.py`). The coordinator runs `uv run advisor-eval
  --provider ollama` (all 50 cases, qwen3:8b as in the baseline) in the
  worktree at the reviewed commit, checks it with
  `uv run advisor-analysis hashes <report>`, compares with
  `uv run advisor-analysis compare <report>`, re-runs flipped cases with
  `--only`, and copies the report to the main checkout's `evals/runs/`.
  `review.md` → "## Eval run" states: `searches` for `tv-sound`,
  `laptop-bathrom-projector`, `pelagic-studio-back-soon`,
  `norvik-fold-brother-gift`, `aurelis-home-gift-mum` (non-empty is the
  outcome; PASS expected for 2 to 5 of them, the out-of-stock three may
  still fail `expected` until §30); and for each `off-topic-*` case its
  status, whether it searched and its turn count. An off-topic case that
  goes PASS → FAIL is a "Needs decision" finding.
- Live check: none owed by rule 1 (no path in `cli.py`, `models/`,
  `tracing.py`, `prompts/` or `infra/` changes). Whether rule 3 applies
  (model output on real input) is `/review`'s call; the eval run is the
  evidence for that behaviour.

## Assumptions I made

- **Off-topic (the intent's open point).** Settled by the intent's own
  assumption "If the model answers in text again after the request, that
  text is the answer (no fallback), so a decline still reaches the user",
  plus a request worded so the model may decline: "If it is not about the
  shop's products, reply without searching." No owner choice is needed to
  build it; the eval run reports what the four cases did, and a
  regression is the owner's decision under "Eval runs".
- **Trace and `turns`.** The request does not show as its own event in the
  trace or in the report's `turns`: the `Tracer` protocol has no event for
  it (`src/advisor/tracer.py:24-26`), and adding one would change
  `tracing.py` (a live-check path and Reviewed tier) for no outcome the
  intent needs. It shows as one more generation, and in `turns` as a
  text-only turn followed by another turn; the request's text is a fixed
  constant.
- **Turn 5.** A text-only reply on turn 5 with no search is returned, not
  replaced by the request: "the extra request uses one of the 5 turns",
  and on turn 5 none is left, so asking could only turn an answer into
  `FALLBACK_ANSWER`, which the intent reserves for "a run that reaches the
  cap without a final text".
- **What counts as a search.** Any `search_products` call, valid or not
  (the intent: "no `search_products` call has been made yet"); another
  tool name does not count.
- **Wording.** `SEARCH_FIRST_TEXT` as in subtask 2, a user-role message as
  the intent assumes; not in `prompts/system.md`.
- **No new dependency**, no change to `FALLBACK_ANSWER`, `REFUSAL_TEXT`,
  `MAX_TURNS`, the adapters or the scorers.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
