<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §37 plan — A very simple chat UI with multi-turn conversation

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Add a local web page where a customer asks follow-up questions and the
advisor sees the earlier questions and answers: a pure `conversation.py`
(turn, 6-exchange window, the customer's text for §33), a `history` argument
on `run_agent` / `answer_question` that leaves every existing caller
byte-identical, a new `chat.py` (the second and last module that imports
FastHTML, Starlette and uvicorn) serving one page on 127.0.0.1:5300 with a
signed-cookie session, one Langfuse trace per turn, a Host/Origin 403 check,
and the console script `advisor-chat`. `cli.py`, `tracer.py`, `tracing.py`,
`guardrails.py`, the prompt, the models and the evals do not change.

## Risks

- **A message list that is not what the CLI sent.** `run_agent` is the core
  loop and the evals call it. Mitigation: `history=()` is the default,
  AC1 compares the full request list of a run with no `history` argument and
  with `history=()`, and the 50-case eval run must compare clean.
- **§33's rule over several turns (B8).** The text for `_execute` must be the
  customer's turns only, never an answer, and only turns still in the window.
  A test that only checks "a number from an earlier turn is kept" passes if the
  code joined answers too; AC4 has all three arms (earlier question kept,
  earlier answer ignored, dropped turn ignored) and the mutations in Tests.
- **A blocked turn detected by comparing `answer == REFUSAL_TEXT`.**
  `answer_question` keeps returning `str` (B3). The only way for the caller to
  know a guardrail refused is that fixed string. A model answer equal to it is
  not realistic, and the cost of the false positive is one turn missing from
  the history. Recorded in Assumptions.
- **Tests that pass whatever the code does.** Escaping (a template that
  forgets to escape passes any test using plain text), Host/Origin (the
  `TestClient` default host is `testserver`, so a test that never sets the
  host proves nothing), the lock (a sequential test passes without one), the
  session secret (a constant key passes every functional test). Each has a
  named test and mutation below.
- **Socket guard.** `tests/conftest.py` fails any connect except the Windows
  asyncio self-pipe; `TestClient` is the only way the page is driven; uvicorn
  is only reached through an injected `serve` (and `uvicorn.run` monkeypatched,
  as `test_serve_binds_to_loopback_only` does).
- **Resource use per turn.** `make_tracer` builds a new `Langfuse` client at
  every call (`tracing.py:151-165`). One per turn in a long-running server is
  new behaviour; `tracing.py` must not change (spec). Watched in the live
  check; if it leaks, that is a follow-up intent, not this plan's to fix.
- **Stale citations.** §33 is not on `main`; its lines are cited from the
  branch and must be re-read at spawn (below).
- **Prose numbers.** The README and CLAUDE.md say "6 exchanges", "20
  conversations", "port 5300"; each is a constant in the code and a test
  pins the constant.

## Verified against the codebase

Re-read on `main` at `b24c9da`. **Prerequisite not on `main`:** §33
(`blocked_by: 33`). The lines marked **[§33]** were read on the unmerged
branch `fix/33-no-invented-price-cap` at `7246505` (worktree
`C:/Users/eric/src/product-advice-agent-wt/33-no-invented-price-cap`, working
tree has an uncommitted edit to that intent's `plan.md` only). The build
starts after §33 is merged. **At spawn, re-read every [§33] citation and
every `agent.py` line on the new `main`, and rewrite `agent.py:<n>` numbers
below; the shape (not the numbers) is what this plan relies on.** §30
(`named_products`, `search_tool` rows) and §31 (the `searched`/`asked` loop)
are merged and cited on `main`.

On `main` (`b24c9da`):

- `src/advisor/agent.py:195-225` — `run_agent(question, client, tools, tracer)`;
  `:207` `messages: list[Message] = [Message("user", question)]`; `:208-209`
  `searched`/`asked` (§31); `:215` the answer returned when `searched or asked
  or turn == MAX_TURNS`; `:223` `_execute(c, by_name, tracer)` (no question).
- `src/advisor/agent.py:228-255` — `answer_question(question, client, tools,
  tracer) -> str`: `tracer.begin(question)` `:236`, `check_input` `:237`,
  refusal `:239-241`, `run_agent` `:243`, `tracer.fail` then re-raise `:244-249`,
  `check_output` `:250`, refusal for a blocked answer `:252-253`,
  `tracer.finish` `:254`.
- `src/advisor/agent.py:30-38` — `MAX_TURNS = 5`, `FALLBACK_ANSWER`,
  `SEARCH_FIRST_TEXT`; `:107-175` `search_tool` (§30 named rows `:151-159`).
- **[§33]** `src/advisor/agent.py:187` `_execute(call, tools, tracer, question)`;
  `:196` `ignored = unstated_price_filters(question, arguments)` for
  `search_products` only; `:243` `_execute(c, by_name, tracer, question)` inside
  `run_agent`; `:11` `from advisor.amounts import unstated_price_filters`;
  `IGNORED_NOTE` and the wrapped result `{ignored_filters, note, results}`
  (`:170-210` region).
- **[§33]** `src/advisor/amounts.py:26` `stated_amounts(question) -> frozenset[float]`
  (digits only, `"150"`, `"1,299"`, `"1.5k"`); `:49`
  `unstated_price_filters(question, arguments) -> dict[str, float]` (tolerance 1,
  `min_price` 0 never reported); `:16-17` `PRICE_FILTERS`, `TOLERANCE`. §33's
  `plan.md` Amendment 2 (`:300`) and "Multi-turn" say a conversation feature
  must pass the earlier customer turns and that prices in tool results are not
  stated amounts.
- `src/advisor/cli.py:58-118` — `main(argv, *, env, client_factory)`: usage exit
  2 `:68-69`; `_configure_logging` `:42-55`; `load_env`/`load_settings`
  `:75-76`; unknown provider exit 1 `:77-81`; key check `:84-90`; Ollama URL
  `:91-96`; `load_catalogue` `:97-100`; `make_client` `:102-105`; tags
  `:106`; `make_tracer(full_env, tags)` `:107`;
  `answer_question(question, client, [search_tool(catalogue)], tracer)` `:108`;
  `ModelUnreachableError`/`ModelNotAvailableError` print `str(e)` `:109-112`;
  anything else prints `UNAVAILABLE` `:113-116`. `:22-23` `USAGE`, `UNAVAILABLE`;
  `:26-34` `ClientFactory`; `:37-39` `_fail`.
- `src/advisor/tracer.py:133-158` — `Tracer` protocol (`begin`, `check`,
  `generation`, `tool`, `finish`, `fail`); `:133` "One tracer instance records
  exactly one run".
- `src/advisor/tracing.py:151-165` — `make_tracer(env, tags=())`: no-op unless
  the three variables are set; a new `Langfuse(...)` per call.
- `src/advisor/guardrails.py:12` `REFUSAL_TEXT`; `:19` `check_input`; `:23`
  `check_output`; both allow.
- `src/advisor/models/base.py:21,25` `ModelUnreachableError`,
  `ModelNotAvailableError`; `:53` `Message`; `:83` `ModelClient`.
  `src/advisor/models/fake.py:22-` `ScriptedModelClient` (`requests`,
  `repeat_last`). `src/advisor/models/__init__.py:9-10` `PROVIDER_KEY_ENV`,
  `KNOWN_PROVIDERS`. `src/advisor/config.py:33,54,65` `Settings`, `load_env`,
  `load_settings`. `src/advisor/catalogue.py:95` `load_catalogue`.
- `src/advisor/evals/view.py:60` `LOCAL_HOST`; `:278` `FastHTML(default_hdrs=False,
  pico=False, live=False, secret_key=secrets.token_hex(32))`; `:259-262` `_route`
  (typed `app.get/post`); `:489-493` `serve` raises `ValueError` for any host
  but `127.0.0.1`, else `uvicorn.run(app, host=host, port=port, log_level="warning")`.
  `tests/test_analysis_view.py:380-389` pins `serve` by monkeypatching
  `view.uvicorn.run`. `src/advisor/evals/analysis.py:277-280` imports
  `view` only in the `view` subcommand and takes `serve` injected.
- FastHTML 0.14.14 (installed, read with `inspect`): `FastHTML.__init__` takes
  `before=`, `secret_key=`, `session_cookie='session_'`, `same_site='lax'`,
  `sess_https_only=False`, `key_fname='.sesskey'` (used only when `secret_key`
  is `None`, so always pass a key: nothing is written to disk), `htmx=`,
  `surreal=`; `Beforeware(f, skip=None)`.
- `tests/test_boundaries.py:11-24` `_importers`; `:122-124`
  `test_only_the_viewer_imports_the_web_framework` expects `{"evals/view.py"}`
  (must change); `:127-169` `_WEB`, `_loads_none_of`, the viewer-guard tests.
- `tests/conftest.py:20-35` the socket guard and its one allowed exception.
  `tests/test_cli_stderr.py:11-50` the subprocess probe pattern.
  `tests/helpers.py:6-30` `RecordingTracer`. `tests/test_agent.py:28-45` the
  `CAT`, `call`, `final` helpers.
- `scripts/intent-check-lib.mjs:155-160` `CORE_CODE` (`agent|catalogue|guardrails`
  on `main`; **[§33]** adds `amounts`); `scripts/intent-check-lib.test.mjs:407`
  lists the core paths a test iterates.
- `src/advisor/evals/run.py:295` `answer_question(case.question, client, [tool],
  traced)` (no history: unchanged). `src/advisor/evals/baseline.py:15-26`
  `EVAL_PATHS` contains `src/advisor/agent.py`: **an eval run is owed**.
- `pyproject.toml` `[project.scripts]` (three scripts), `python-fasthtml==0.14.14`
  already a dependency; `[[tool.mypy.overrides]]` for `fasthtml` already there.
- `README.md:69-79` "## Run"; `CLAUDE.md:33-36` command list, `:198-208` the
  statement that `view.py` is "the only module that imports `fasthtml`,
  `starlette` or `uvicorn`".

## Subtasks

Each is one commit with `npm run verify` green. Tests first inside each.

1. **`conversation.py` (pure) and its core-code entry.** New
   `src/advisor/conversation.py` (no I/O, no SDK, no import of `agent`):
   `Turn(question, answer)` frozen; `MAX_HISTORY_TURNS = 6`;
   `add_turn(history, turn) -> tuple[Turn, ...]` (append, then keep the last 6);
   `customer_text(history, question) -> str` (`"\n".join(` every
   `turn.question` oldest first, then `question`) — answers never); a
   `Conversation` dataclass: `id` (random hex, injected for tests),
   `history: tuple[Turn, ...]`, `transcript: list[Turn]` (every turn shown,
   for the page), `turns_taken: int` (counts every attempt that created a
   tracer), `lock: threading.Lock`, with `dropped` = `len(transcript) -
   len(history)`; `ConversationStore(max_conversations=20)` with
   `get_or_create(session_id)` (least recently used out at the 21st; every
   call touches) and `reset(session_id)` (a new `Conversation`, new id).
   Add `conversation` to `CORE_CODE` in `scripts/intent-check-lib.mjs:156` and
   its path to the list in `scripts/intent-check-lib.test.mjs:407`. Tests:
   `tests/test_conversation.py`; `npm run test:kit` green.
2. **`history` through the agent (B2, B3, B4 seam, B5, B8).** `run_agent(...,
   history: Sequence[Turn] = ())` builds `messages` = for each turn
   `Message("user", q)`, `Message("assistant", a)`, then `Message("user",
   question)`; passes `customer_text(history, question)` as the `question`
   argument of `_execute` (the [§33] parameter); the code comment at both sites
   carries the two interpretations from the spec. `answer_question(...,
   history=())` passes it on; `tracer.begin(question)` stays the current
   question only. Tests in `tests/test_agent.py` (AC1, AC2, AC4 agent arm) and
   `tests/test_guardrails.py` (a refusal with a history). `cli.py` and
   `evals/run.py` are not edited.
3. **`chat.py`, the page and the turn (B1 use, B4, B6, B7, B10, B11, B13).**
   New `src/advisor/chat.py`: `make_app(client, tools, tracer_factory, *,
   base_tags, port=DEFAULT_PORT, secret_key=None, store=None) -> FastHTML` with
   `FastHTML(default_hdrs=False, pico=False, live=False, htmx=False,
   surreal=False, secret_key=secret_key or secrets.token_hex(32))`; routes `GET /`,
   `POST /ask`, `POST /new`; one inline stylesheet, no script, no external URL;
   a module function `take_turn(conversation, question, client, tools,
   tracer_factory, base_tags)` that holds `conversation.lock`, increments
   `turns_taken`, builds the tracer with tags `[*base_tags, "chat",
   f"conversation:{id}", f"turn:{n}"]`, calls `answer_question(question,
   client, tools, tracer, history=conversation.history)`, and appends the turn
   to `history` (via `add_turn`) and to `transcript` unless `answer ==
   REFUSAL_TEXT`. The session holds only `sid` (random hex, set on the first
   request). Page text is built with FastHTML components so it is escaped; a
   question's line breaks are kept by CSS `white-space: pre-wrap`. Handlers:
   empty (after strip) redirects without a turn; over `MAX_QUESTION_CHARS = 1000`
   renders the page with an error line and the draft, status 422, no model
   call; success redirects `303` to `/`. Update
   `tests/test_boundaries.py:122-124` to `{"evals/view.py", "chat.py"}`.
   Tests: `tests/test_chat.py` (AC5-AC8, AC10, the escaping and lock tests).
4. **Failures and exposure (B9, B12) in `chat.py`.** `Beforeware` running
   `request_allowed(host, origin, method, port)` (pure function in `chat.py`,
   tested by table): `Host` must be `127.0.0.1:<port>` or `localhost:<port>`,
   else 403; a `POST` with an `Origin` that is present and not
   `http://127.0.0.1:<port>` or `http://localhost:<port>` (including `null`)
   gets 403 before any model call. `/ask` catches `ModelUnreachableError` /
   `ModelNotAvailableError` (message = `str(e)`) and any other `Exception`
   (message `UNAVAILABLE`, imported from `advisor.cli`), re-renders the page
   with an error line, the draft in the box and status 503, adds no turn, and
   leaves the server up; no traceback in the body. `serve(app, host, port)`
   raises `ValueError` unless `host == "127.0.0.1"`, else `uvicorn.run(app,
   host=host, port=port, log_level="warning")`. Tests: AC9, AC11.
5. **`advisor-chat` (B14, B15).** `chat.main(argv=None, *, env=None,
   client_factory=make_client, serve=serve) -> int`: parse `[--port N]
   [--debug]` by hand as `cli.main` does (any other argument, a non-integer
   port or a port outside 1..65535: usage line on stderr, return 2); call
   `advisor.cli._configure_logging`; then the same checks as `cli.main:75-100`
   (settings, unknown provider exit 1, key check, Ollama URL, catalogue), build
   `client_factory(...)`, `make_app(client, [search_tool(catalogue)],
   lambda tags: make_tracer(full_env, tags), base_tags=[f"provider:{p}",
   f"model:{m}"], port=port)`, `print(f"serving http://127.0.0.1:{port}; Ctrl+C
   stops it")`, call `serve(app, "127.0.0.1", port)`, return 0 (a
   `KeyboardInterrupt` also returns 0). `pyproject.toml`: `advisor-chat =
   "advisor.chat:main"`. Tests: `tests/test_chat_cli.py` (AC13 and the stderr
   subprocess test). `cli.py` is not edited; `uv run advisor-chat --help` is
   not a feature (an unknown flag is usage, exit 2).
6. **Docs (AC16).** `README.md`: a "Chat in a browser" section after "Run"
   (`:69-79`): the command, `http://127.0.0.1:5300`, `--port`, "the advisor
   sees your last 6 exchanges; older ones are dropped and the page says so",
   "local only, no login, nothing saved to disk, conversations forgotten on
   restart", the Host/Origin 403, one trace per turn tagged `chat` and
   `conversation:<id>`, the default provider is still local Ollama.
   `CLAUDE.md`: `uv run advisor-chat` in the command list (`:33-36`); the
   architecture text: `conversation.py` among the pure core modules, `chat.py`
   among the I/O modules, and the viewer sentence at `:206-208` becomes "`view.py`
   and `chat.py`, the only modules that import `fasthtml`, `starlette` or
   `uvicorn`"; the live-check list is unchanged (rule 1 paths untouched; rule 3
   covers this change).

The build is not complete without the eval run (Validation); it is the
coordinator's at review.

## Tests

Conventions: scripted `ScriptedModelClient` (`requests[n].messages` asserted),
`RecordingTracer` from `tests/helpers.py` extended in the test file with
the tags it was made with, `starlette.testclient.TestClient(app,
base_url="http://127.0.0.1:5300")` (the default `testserver` host would be
403), no socket, no uvicorn, no Langfuse, no Ollama. Every mutation below is
"change the line, run the full suite, this test fails".

`tests/test_conversation.py` (new; subtask 1)

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1, AC3 | `test_history_keeps_the_last_six_turns`: add 7 turns, history is turns 2-7, `dropped == 1`, 6 turns stays 6 | `MAX_HISTORY_TURNS = 7`; `[:6]` instead of `[-6:]` (keeps the oldest) |
| B1 | `test_max_history_turns_is_six` pins the constant | change the constant |
| B8, AC4 | `test_customer_text_is_the_questions_oldest_first_then_the_current_one` | answers joined in; current question first; no newline separator |
| B8 | `test_customer_text_of_no_history_is_the_question` (`customer_text((), q) == q`) | a trailing newline, a prefix |
| B8, AC4 | `test_a_turn_dropped_from_the_window_no_longer_counts`: 7 turns, the first states "150", `customer_text` lacks it | computing from `transcript` instead of `history` |
| B10, AC8 | `test_store_keeps_20_conversations_and_drops_the_least_recently_used`: touch #1 again after #2..#20, open #21: #2 gone, #1 kept | cap 21; evict the oldest created instead of least recently used |
| B10 | `test_reset_gives_a_new_id_and_no_history` | reset keeping the id or the history |
| B11 | `test_turns_taken_counts_every_attempt` (counter is a field, not derived from `len(history)`) | derive `turn:<n>` from history length (blocked turns would repeat a number) |

`tests/test_agent.py` (subtask 2)

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B2, AC1 | `test_no_history_sends_exactly_the_question`: `requests[0].messages == (Message("user", q),)` with no `history` and with `history=()`, and the full request list and tracer events of a tool-call run equal between the two | always inserting a message; a default of `None` handled differently |
| B2, AC2 | `test_history_is_replayed_as_user_assistant_pairs_then_the_question`: two turns give `user q1, assistant a1, user q2, assistant a2, user q3` and no `tool_calls`/`tool_results` on any earlier message; a second-model-turn request still starts with those five | putting the question first; replaying tool results; dropping the assistant messages |
| B2 | `test_a_followup_after_a_search_does_not_replay_earlier_tool_results`: first run searched; the history passed has only text; request 0 of the second run holds no `ToolResult` | storing tool messages in `Turn` |
| B3 | `test_answer_question_returns_str_and_does_not_touch_the_history` (passes a tuple; the tuple is unchanged; the return is `str`) | making it mutate/return a pair |
| B4 | `test_a_blocked_input_with_a_history_never_reaches_the_model` (patch `advisor.agent.check_input`; `client.requests == []`; returns `REFUSAL_TEXT`); same for `check_output` in `tests/test_guardrails.py` | skipping the input check when history is non-empty |
| B5 | `test_a_followup_answered_without_searching_gets_the_search_first_text_once` | clearing `asked`/`searched` logic when history is non-empty; applying the nudge twice |
| B8, AC4 | `test_a_price_limit_stated_in_an_earlier_customer_turn_is_kept`: history `Turn("headphones under 150 euros", "…")`, question "and in stock?", the model calls `search_products(max_price=150)`; tool result is the plain row list (no `ignored_filters`) | passing `question` only to `_execute` |
| B8, AC4 | `test_a_number_only_in_an_earlier_answer_is_dropped`: history `Turn("anything good?", "Try X at 150 euros")`; tool result has `ignored_filters` with `max_price` 150 | joining answers into the text |
| B8 | `test_history_empty_gives_the_old_behaviour_for_the_price_rule` (the existing §33 tests unedited stay green) | changing the text for `history=()` |

`tests/test_chat.py` (subtasks 3 and 4). Helper `app_and_client(script, ...)`
returns the app, a `TestClient`, the `ScriptedModelClient` and the list of
`(tags, tracer)` the injected factory made.

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B6, AC6 | `test_a_new_session_shows_no_turns_and_the_form`: `GET /` 200, a field named `question`, a "Send" button, a "New conversation" button | removing either button or the field |
| B6, AC6 | `test_two_turns_show_in_order_and_the_second_request_holds_the_first_turn`: after two posts the page has q1, a1, q2, a2 in that order; `requests[1].messages[:2]` are q1, a1 | not threading `history`; page order reversed |
| B6, B8 | `test_html_in_a_question_or_an_answer_is_escaped`: question `<script>x</script>`, answer `<b>hi</b>`: the body contains `&lt;script&gt;` and `&lt;b&gt;` and no `<script>x` | `NotStr`/unescaped output |
| B6 | `test_the_page_has_no_script_and_no_external_url`: no `<script`, no `http://`/`https://` other than form actions (relative), no `src=`/`href=` to another host | adding a CDN link or script |
| B6 | `test_post_ask_redirects_303_to_the_page` and `test_reloading_does_not_resubmit` (a GET after the 303 adds no request to the model) | answering 200 on POST |
| B6, B1 | `test_a_note_says_how_many_messages_the_advisor_no_longer_sees`: 7 turns: note names 1 and the page still shows all 7 turns; at 6 turns there is no note | note off by one or always shown |
| B7 | `test_empty_question_changes_nothing` (no model request, no tracer, no turn) | treating `"  "` as a question |
| B7 | `test_a_question_over_1000_characters_is_refused_before_the_model`: 1001 characters: an error line, 422, `requests == []`, no tracer; exactly 1000 is accepted; `MAX_QUESTION_CHARS == 1000` | `>=`; limit applied after the call |
| B7, A6 | `test_the_fallback_answer_is_shown_and_kept` (model keeps calling tools: `FALLBACK_ANSWER` in the page and in the next request) | filtering fallbacks out |
| B4, AC5 | `test_a_blocked_input_gives_the_refusal_and_stays_out_of_the_history`: patch `advisor.agent.check_input` to block turn 2: refusal on the page, no model request for it, request of turn 3 holds only turn 1 | adding the refused pair to `history` |
| B4, AC5 | `test_a_blocked_output_gives_the_refusal_and_stays_out_of_the_history` (patch `check_output`) | same |
| B10, AC7 | `test_new_conversation_clears_the_page_and_the_next_request_has_no_history_and_a_new_tag`: after `POST /new` the page is empty, the next first request has one message, the tag `conversation:<id>` differs and `turn:1` restarts | `/new` not resetting history; reusing the id |
| B10, AC8 | `test_two_sessions_do_not_see_each_other`: two `TestClient`s on one app | one global conversation |
| B10, AC8 | `test_the_21st_conversation_drops_the_least_recently_used` (client 1 asks; 20 other clients `GET /`; client 1's page is empty; client 1 asked again between... variant keeps it) | cap 21; no eviction |
| B10 | `test_a_restart_forgets_every_conversation`: a cookie from app A used on a new app B (fresh store): empty page | persisting to disk or a class-level store |
| B10 | `test_the_session_secret_is_generated_per_app`: spy on `chat.secrets.token_hex`: called once per `make_app` without `secret_key`, not called with one; a hex string of 64 characters reaches `FastHTML(secret_key=...)` | a hard-coded key |
| B10 | `test_nothing_is_written_to_disk` (`tmp_path` as cwd, a turn, `list(tmp_path.iterdir()) == []`; in particular no `.sesskey`) | omitting `secret_key` (FastHTML would write `.sesskey`) |
| B11, AC10 | `test_each_turn_makes_one_tracer_with_the_tags`: tags exactly `[provider, model, "chat", "conversation:<hex>", "turn:1"]`, then `turn:2` with the same conversation tag; the tracer's `begin` got the current question only; a blocked turn also takes a tracer and a number | tag order/name drift; `begin(history text)`; no `chat` tag |
| B11 | `test_a_failed_turn_still_takes_a_number` (turn 1 fails, next is `turn:2`) | decrementing on failure |
| B9, AC9 | `test_a_model_failure_shows_its_message_and_keeps_the_question`: scripted `ModelUnreachableError("cannot reach Ollama")`: message in the page, 503, textarea holds the draft, no turn; the next `/ask` (script continues) works with a history of zero turns | adding the turn; losing the draft |
| B9 | `test_an_unexpected_exception_shows_unavailable_without_a_traceback` (`RuntimeError("secret detail")`: page has `UNAVAILABLE`, not `secret detail`, not `Traceback`); `ModelNotAvailableError` shows its own message | echoing `str(e)` for any exception |
| B12, AC11 | `test_request_allowed_table` (pure): hosts `127.0.0.1:5300`, `localhost:5300` allowed; `evil.example`, `127.0.0.1:9999`, `127.0.0.1.evil.example:5300`, empty, `0.0.0.0:5300` refused; POST origins `http://127.0.0.1:5300`, `http://localhost:5300`, none: allowed; `http://evil.example`, `null`, `http://127.0.0.1:5301`: refused; a GET with a foreign origin is not refused (the rule is for POST) | substring/`startswith` matching; allowing a missing port; checking Origin on GET only or never |
| B12, AC11 | `test_a_foreign_host_gets_403_on_every_route` (`GET /`, `POST /ask`, `POST /new`); `test_a_foreign_origin_post_gets_403_and_calls_no_model` (`requests == []`, no tracer, no history change) | the check missing on one route; check after the model call |
| B12, AC11 | `test_serve_binds_to_loopback_only` (monkeypatched `chat.uvicorn.run`: called with `127.0.0.1` and the port, `log_level="warning"`; `0.0.0.0`, `localhost`, `""` raise `ValueError`) | allowing other hosts |
| B13 | `test_two_turns_of_one_conversation_never_overlap`: `take_turn` in two threads on one `Conversation`; the client blocks on an event (bounded wait 2 s, never infinite) and records the maximum number of concurrent `complete` calls (must be 1) and that the second run's first request contains the first turn | removing the lock; taking the lock after reading `history` |

`tests/test_chat.py` (the §33 rule through the page, B8 + B1 together)

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B8, AC4 | `test_a_limit_from_a_turn_that_left_the_window_is_dropped_through_the_page`: turn 1 says "under 150 euros"; turns 2-7 state no amount; turn 8's search with `max_price=150` is wrapped with `ignored_filters` (and is kept at turn 3) | computing the amounts over `transcript` rather than the window |

`tests/test_chat_cli.py` (subtask 5)

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B14, AC13 | `test_anthropic_without_a_key_exits_1_with_the_cli_message` (same text as `cli`); unknown provider exits 1; bad `ADVISOR_OLLAMA_URL` exits 1; catalogue error exits 1 (monkeypatch `load_catalogue`) | skipping a check |
| B14, AC13 | `test_a_bad_port_or_argument_exits_2` (`--port abc`, `--port 0`, `--port 70000`, `--port`, `--bogus`; `serve` never called) | accepting the range loosely |
| B14 | `test_it_serves_on_loopback_and_prints_the_address`: injected `serve` receives `("127.0.0.1", 5300)` by default and `--port 5400` overrides; stdout is exactly `serving http://127.0.0.1:5300; Ctrl+C stops it`; exit 0; a `KeyboardInterrupt` from `serve` also returns 0 | binding another host; wrong default |
| B14 | `test_the_ollama_provider_needs_no_key_and_gets_none` (as `tests/test_cli_ollama.py`) | requiring a key for Ollama |
| B14 | `test_the_tracer_factory_uses_make_tracer_with_the_tags`: the app's factory calls the patched `make_tracer(env, tags)` | not wiring tracing |
| B14 | `test_library_log_lines_stay_off_stderr_without_debug` (subprocess, same probe pattern as `tests/test_cli_stderr.py`: an injected `serve` logs `logging.getLogger("langfuse").warning(...)`; stderr empty without `--debug`, contains the line with it) | omitting `_configure_logging` |
| B14 | `test_the_script_is_declared`: `pyproject.toml` has `advisor-chat = "advisor.chat:main"` | missing or wrong target |

`tests/test_boundaries.py` (subtask 3, AC12)

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| AC12 | `test_only_the_viewer_and_the_chat_import_the_web_framework`: `_importers(p) == {"evals/view.py", "chat.py"}` for the three packages | `conversation.py` or `agent.py` importing a web module |
| AC12 | `test_the_core_and_the_command_load_no_web_framework`: subprocess `_loads_none_of("advisor.cli,advisor.agent,advisor.conversation,advisor.evals.run,advisor.evals.analysis", _WEB)` returns 0; `_loads_none_of("advisor.chat", _WEB)` returns 1 (guards the guard) | a top-level `import fasthtml` in `agent.py` or `conversation.py` |
| AC12 | `npm run test:kit`: `conversation.py` matches `CORE_CODE` (`scripts/intent-check-lib.test.mjs:407`) | forgetting the regex entry |

Remaining spec lines:

| Spec | Check |
| --- | --- |
| B15, AC14 | `tests/test_cli.py`, `tests/test_cli_stderr.py`, `tests/test_cli_ollama.py` pass unedited (`git diff main --stat -- tests/test_cli*.py` empty); `git diff main -- src/advisor/cli.py` empty (the reviewer runs it); `tests/test_agent.py` AC1 test; the eval run (Validation) |
| AC15 | the live check below |
| AC16 | `npm run verify`; the reviewer greps `README.md` for `advisor-chat`, `5300`, `6` exchanges, `local` |

The `ScriptedModelClient` request list is the oracle for what the model saw;
no test asserts only that "a page contains text".

## Validation

- `npm run verify` green (kit tests, ruff check, ruff format --check, mypy
  strict on `src/advisor`, pytest).
- `npm run check:intent` PASS.
- `git diff main -- src/advisor/cli.py src/advisor/tracer.py
  src/advisor/tracing.py src/advisor/guardrails.py src/advisor/models/
  src/advisor/prompts/ evals/ infra/` is empty.
- **Eval run owed** (`agent.py` is in `EVAL_PATHS`; `uv run advisor-analysis
  owes-run --base main` says "owed"). The coordinator runs `uv run advisor-eval`
  on local Ollama in the worktree at the reviewed commit, then `advisor-analysis
  compare` against the committed baseline (the baseline on `main` after §33 is
  merged). It must show: no case flipped beyond run-to-run variation (the 50
  cases are single-turn, so `history=()` must give the same requests); a
  flipped case is re-run with `--only` before it is called a regression;
  `advisor-analysis hashes <report>` matches `prompt_sha256`,
  `cases_sha256`, `catalogue_sha256`. No new baseline is written by this
  change.
- **Live check owed** (rule 3: model behaviour in a conversation and a real
  browser; rule 1 is not triggered because `cli.py`, `models/`, `tracing.py`,
  `prompts/`, `infra/` do not change). The owner runs it:
  1. `ollama serve` up with `qwen3:8b`; `uv run advisor-chat`; open
     `http://127.0.0.1:5300`. Expect the line `serving http://127.0.0.1:5300;
     Ctrl+C stops it` and an empty page with a box, "Send", "New conversation".
  2. Ask "Do you have headphones under 150 euros?", then "anything cheaper than
     the second one?", then "which of those has the longest battery?". Each
     answer follows from the earlier turns and names real catalogue products.
  3. Ask "cheap laptop", then "something cheaper". No invented price limit is
     mentioned (the §33 rule across turns).
  4. Click "New conversation": the page is empty; "and cheaper?" now gets a
     clarifying answer, not a continuation.
  5. With the three `LANGFUSE_*` variables set: each turn is its own trace,
     all with one `conversation:<id>` tag, `chat` and `turn:<n>`. Send ten more
     turns and watch the process (memory and open threads do not grow without
     bound; this is the `make_tracer` per-turn risk).
  6. Send 8 questions: the note "the advisor no longer sees your first 2
     messages" shows and all 8 turns stay on the page. Type `<b>x</b>`: it
     shows as text.
  7. Try `http://<this machine's LAN address>:5300` from another machine (no
     connection) and `uv run advisor-chat` after setting no bind option (there
     is none). Stop Ollama and send a question: the page shows the "cannot
     reach Ollama" message and the box keeps the question; start Ollama and
     send again: it works with no restart.
  8. `uv run advisor "<question>"` still prints one answer as before (B15).

## Assumptions I made

- **A1. §33 is merged first.** `blocked_by: 33` is already in `metadata.yml`.
  `_execute(..., question)` and `unstated_price_filters(question, arguments)`
  are used as read on the branch at `7246505`; if §33's signatures move before
  merge, subtask 2 follows them (re-read at spawn).
- **A2. A blocked turn is `answer == REFUSAL_TEXT`.** B3 keeps `answer_question`
  returning `str`, so the caller cannot ask the pipeline; the fixed string is
  the signal. `chat.py` imports `REFUSAL_TEXT` from `guardrails`.
- **A3. The page shows every turn; the window is what the model sees.** I read
  B6 ("each turn", and a note "the advisor no longer sees your first N
  messages") as the transcript staying visible and `history` (B1) being the
  last 6. The alternative (the page shows only the last 6) is one line in the
  render function and one test. The transcript is not bounded per conversation
  (at most 20 conversations, memory only, gone on restart).
- **A4. `turn:<n>` counts every call that creates a tracer** (success, refusal,
  failure), so no two traces of a conversation share a tag. An empty question
  and one over 1000 characters create no tracer and take no number.
- **A5. Status codes.** 303 for success and for an empty question, 422 for a
  question over 1000 characters, 503 for a model failure, 403 for Host/Origin;
  the spec names only 303 and 403. The error pages re-render the page (not a
  redirect) so the draft stays in the box.
- **A6. `chat.py` imports `UNAVAILABLE`, `ClientFactory` and
  `_configure_logging` from `advisor.cli`** (not edited) instead of copying
  them; it duplicates only `cli.main`'s config checks (spec A3). That import
  loads `advisor.tracing` (so `langfuse`) when `chat` is imported; the
  boundary test only bans the web frameworks in `cli`, `agent`, `conversation`
  and the runner, and `chat` imports them by design.
- **A7. Origin rule.** The page's own origin is `http://127.0.0.1:<port>` or
  `http://localhost:<port>`; `null` and a different port are foreign. Only
  `POST` is checked for Origin; Host is checked on every request.
- **A8. The `question` field is a `<textarea>`**, no `maxlength`, so the
  server's over-1000 message is what a customer sees.
- **A9. Port in use.** uvicorn exits 1 on a failed bind; that is left as is
  (the spec's exit codes cover configuration, not the bind).
- **A10. No new dependency:** FastHTML, Starlette and uvicorn are already in
  `pyproject.toml` through `python-fasthtml`; only the console script is added.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
