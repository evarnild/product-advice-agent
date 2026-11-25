<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §37 spec — A very simple chat UI with multi-turn conversation

Accepted intent: [intent.md](intent.md)

Written against `main` at `d1a2a58`. Two facts about that commit matter:
`src/advisor/amounts.py` and the `question` parameter of `_execute` do **not**
exist on `main`; they are on the unmerged branch `fix/33-no-invented-price-cap`
(status `in-review`). B8 is written as if §33 is merged (see Assumptions, A1).

The spec decides **what** gets built. It points at existing sources and
records the decisions that have no other home.

## Open questions for the owner (one round; each has the default used below)

| # | Question | Default used in this spec |
| --- | --- | --- |
| Q1 | Web page, terminal chat, or both? | Web page only. Terminal chat is a later, small intent that reuses `conversation.py`. |
| Q2 | What does the model see of earlier turns, and the limit? | Earlier customer questions and the answers shown, not tool calls or tool results; the last 6 exchanges; older ones dropped, and the page says so. |
| Q3 | §33's stated amounts: all earlier customer turns or the last one? | All customer turns still in the history, plus the current question. Answers never count. |
| Q4 | Does a blocked turn stay in the history? | No: neither the question nor the refusal. |
| Q5 | One trace per turn or per conversation? | One trace per turn, tagged `conversation:<id>`, `turn:<n>`, `chat`. |
| Q6 | Where it lives, how it starts, the port? | New `src/advisor/chat.py`, console script `advisor-chat`, port 5300 (`--port`), 127.0.0.1 only. `cli.py` is not touched. |
| Q7 | Where is state kept? | In the server's memory, keyed by a signed session cookie; "New conversation" clears it. |
| Q8 | Any eval case multi-turn now? | No. Later, its own intent. |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/37-chat-ui/intent.md` | "the page binds to `127.0.0.1` only, loads no CDN or external asset, and has no login (the same rule as the local label viewer, `evals/view.py`): "not exposed" is the safety measure, not authentication." |
| `src/advisor/agent.py` (`main`) | `run_agent(question, client, tools, tracer)` builds `messages = [Message("user", question)]`; `answer_question` returns `str`; `MAX_TURNS = 5`; `SEARCH_FIRST_TEXT` fires once per run if no search happened. |
| `src/advisor/guardrails.py` | `check_input(question)` / `check_output(answer)`; a block gives `REFUSAL_TEXT`. |
| `intents/33-no-invented-price-cap/plan.md`, "Multi-turn" | "A future conversation feature must pass the customer's earlier turns to the helper; out of scope here." and "Prices the model reads in tool results are not amounts the customer stated." |
| `src/advisor/tracer.py` | "One tracer instance records exactly one run (one trace)." |
| `src/advisor/evals/view.py` | `LOCAL_HOST = "127.0.0.1"`; `serve` raises `ValueError` for any other host; `FastHTML(default_hdrs=False, pico=False, live=False, secret_key=...)`; tested with `starlette.testclient.TestClient`. |
| `tests/test_boundaries.py` | `_importers(package) == {"evals/view.py"}` for `fasthtml`, `starlette`, `uvicorn`. |
| `tests/conftest.py` | Any socket connect fails the test (only the Windows asyncio self-pipe over loopback is allowed, which `TestClient` needs). |
| `src/advisor/models/ollama_model.py` | `NUM_CTX = 8192`: the history limit must leave room for a 10-row tool result. |
| `REVIEW-POLICY.md` "Live checks" | Rule 1 lists `cli.py`, `models/`, `tracing.py`, `prompts/`, `infra/`; rule 3 covers model output on real input. |

## Behaviour

**The conversation (pure, new `src/advisor/conversation.py`, core code)**

- **B1. Turn and history.** A `Turn` is one `(question, answer)` pair. The
  history is a tuple of turns, oldest first. `MAX_HISTORY_TURNS = 6`. Adding a
  turn to a full history drops the oldest. Why 6: each answer is a short
  paragraph or list (a few hundred tokens), so six exchanges cost about 2-3k
  of the 8192-token Ollama context, leaving room for the system prompt, the
  tool schema and a 10-row search result.
- **B2. What the model receives.** `run_agent` takes `history: Sequence[Turn] = ()`.
  The messages are `user(q1), assistant(a1), ..., user(qn)`, then the current
  question as the last user message, then the loop continues as today. Earlier
  tool calls and tool results are **not** replayed: they are large, the answers
  already say what mattered, and a replayed row could be stale or hide a
  changed filter. With `history=()` the messages are exactly
  `[Message("user", question)]`, as today.
- **B3. The answer function.** `answer_question(question, client, tools, tracer, history=())`
  keeps returning `str`. It does not update the history; the caller does
  (B6), so the agent stays stateless.

**The checks across turns**

- **B4. Guardrails per turn.** `check_input` runs on each customer message
  alone and `check_output` on each answer, as today. A blocked turn returns
  `REFUSAL_TEXT`, never reaches the model (input block), and is **not**
  added to the history: neither the question nor the refusal, so a refused
  message cannot steer later turns.
- **B5. The search-first nudge.** Unchanged and per run: a follow-up answered
  from the history without a `search_products` call in that run gets
  `SEARCH_FIRST_TEXT` once, like any first question.
- **B8. Stated amounts across turns (§33).** The text given to
  `unstated_price_filters` is the customer's turns joined by a newline: every
  question in the history, then the current question. Answers never count
  (a price the assistant wrote is not an amount the customer stated). A
  history of `()` gives today's text (the question alone). A number stated in
  an earlier turn therefore supports a filter in a later turn: this errs
  towards keeping a filter, as §33's own tolerance does. Once a turn is dropped
  by B1, its amounts stop counting.

**The page (new `src/advisor/chat.py`, the second module that imports FastHTML, Starlette and uvicorn)**

- **B6. One page.** `GET /` shows, top to bottom: the title, the conversation
  (each turn as the customer's question then the answer, plain text with line
  breaks kept and HTML escaped), a note when older turns were dropped ("the
  advisor no longer sees your first N messages"), one text box with a
  "Send" button, and a "New conversation" button. No JavaScript, no CDN, no
  external asset; inline CSS only. `POST /ask` (field `question`) runs one turn
  then answers `303` back to `GET /`; reloading never resubmits.
- **B7. A turn.** `/ask` does, in order: strip the question; if empty, change
  nothing. If longer than `MAX_QUESTION_CHARS = 1000`, show an error line and
  send nothing to the model. Otherwise run `answer_question` with the session's
  history and a new tracer; on success append `Turn(question, answer)` to the
  history (B1) unless B4 blocked it. A tool-loop fallback answer
  (`FALLBACK_ANSWER`) is shown and kept: it is what the customer saw.
- **B9. Model or network failure.** `ModelUnreachableError` / `ModelNotAvailableError`
  show their ready message (as the CLI does), anything else shows
  `UNAVAILABLE` ("The advisor is unavailable right now."), in an error line.
  The failed question is not added to the history and stays in the text box.
  The server keeps running; no traceback reaches the page.
- **B10. State.** Conversations live in the server's memory only:
  `dict[session_id, Conversation]`, where `session_id` is a random id in
  FastHTML's signed session cookie (a new key at each start, so a restart
  forgets every conversation). At most 20 conversations are kept; opening a
  21st drops the least recently used. "New conversation" (`POST /new`) clears
  the history and starts a new conversation id (B11). Nothing is written to
  disk by the page.
- **B11. Tracing.** One tracer per turn, from `make_tracer(env, tags)` with
  tags `provider:<p>`, `model:<m>`, `chat`, `conversation:<hex id>`,
  `turn:<n>` (n counts the turns taken in the conversation, from 1, blocked
  ones included). So a turn is one trace as today; the conversation is the
  set of traces with one tag. The trace input is the current question, not the
  history; `tracer.py` and `tracing.py` do not change. It is a no-op unless the
  three `LANGFUSE_*` variables are set.
- **B12. Exposure.** `serve` binds `127.0.0.1` and raises `ValueError` for any
  other host (same as the viewer). A request whose `Host` header is not
  `127.0.0.1:<port>` or `localhost:<port>` gets `403`, and a `POST` whose
  `Origin` header is present and not the page's own origin gets `403` (a page
  in another browser tab must not be able to drive the model, which would cost
  money on the anthropic provider).
- **B13. One turn at a time per conversation.** A second `/ask` for a
  conversation while one is running waits for the first (a lock per
  conversation), so the history cannot interleave.

**The command**

- **B14. `advisor-chat [--port N] [--debug]`.** Console script
  `advisor-chat = "advisor.chat:main"`. It does what `advisor` does before it
  asks (load env and settings, unknown provider exit 1, missing key exit 1
  with the same message, Ollama URL check, catalogue load, `make_client`),
  prints `serving http://127.0.0.1:<port>; Ctrl+C stops it`, and serves. Exit
  codes: 0 after Ctrl+C, 1 for a configuration or catalogue failure, 2 for a
  bad argument. The default provider stays Ollama; no paid provider becomes a
  default. Logging follows the CLI (`NullHandler` unless `--debug`).
- **B15. `advisor "<question>"` is unchanged.** `cli.py` is not edited; its
  output, exit codes and trace (one question, no history, no conversation
  tag) are the same. The evals call `run_agent` / `answer_question` with no
  history and behave the same, with the same prompt and case hashes.

## Interpretations

- **"Multi-turn" is questions plus answers, not the full transcript.** The
  intent asks whether the model also sees earlier tool results; read as no
  (B2). Code comment at the message-building site in `run_agent`.
- **"The question" in §33 becomes "the customer's turns".** The plan said a
  future feature must pass the earlier turns; read as all turns still in the
  history, not just the last one (B8). Code comment where `run_agent` builds
  the text for `_execute`.
- **"A blocked turn" is a turn either guardrail refused.** An output block
  also leaves the question out, since the model's answer to it was unfit.
  Both are covered by B4 ("not added").
- **"Very simple" allows a redirect after POST.** No JavaScript still means
  one full page load per turn; the user waits on a blank-but-sending page
  while the model runs (seconds on a local model). Accepted for simplicity.
- **The trace holds the question, not the context.** The generation records
  what the model said, not what it was sent (today's tracer); a reader sees
  earlier turns by opening the traces with the same `conversation:` tag.

## Acceptance criteria

- **AC1.** With history `()` the messages sent to the model are
  `[Message("user", q)]`, byte for byte as before (test: `tests/test_agent.py`,
  a scripted `ScriptedModelClient`, comparing `client.requests[0].messages`).
- **AC2.** With a history of two turns the first request's messages are
  `user q1, assistant a1, user q2, assistant a2, user q3`, with no tool calls
  or tool results from earlier turns (test: `tests/test_agent.py`).
- **AC3.** The history never exceeds 6 turns; adding a 7th drops the first
  (test: `tests/test_conversation.py`).
- **AC4.** A `max_price` of 150 supported only by an earlier customer turn
  ("under 150 euros") is kept in a later turn ("and in stock?"); a number that
  appears only in an earlier **answer** is dropped; a number from a turn that
  fell out of the window is dropped (tests: `tests/test_conversation.py`,
  `tests/test_agent.py`; needs §33 merged).
- **AC5.** `check_input` blocking turn 2 returns `REFUSAL_TEXT`, never calls
  the model, and the history still holds only turn 1; `check_output` blocking
  does the same (tests: `tests/test_chat.py` with the guardrail functions
  patched).
- **AC6.** `GET /` shows no turns on a new session; after two `POST /ask` the
  page shows both questions and answers in order, HTML-escaped (a question
  `<script>x</script>` appears as text), and the second model request holds
  the first turn (test: `tests/test_chat.py`, `TestClient`, scripted model).
- **AC7.** `POST /new` empties the page, a following turn's request holds no
  earlier turn, and its trace carries a different `conversation:` tag (test:
  `tests/test_chat.py`).
- **AC8.** Two sessions (two clients, separate cookies) do not see each
  other's turns; a 21st conversation drops the oldest (test: `tests/test_chat.py`).
- **AC9.** A scripted `ModelUnreachableError` shows its message in the page,
  adds no turn, keeps the question in the box, and the next `/ask` works
  (test: `tests/test_chat.py`).
- **AC10.** Every turn creates one tracer with the tags of B11 (a recording
  tracer factory injected into `make_app`; test: `tests/test_chat.py`).
- **AC11.** A request with `Host: evil.example` gets 403; a `POST /ask` with
  `Origin: http://evil.example` gets 403 and calls no model (test:
  `tests/test_chat.py`). `serve(app, "0.0.0.0", port)` raises `ValueError`.
- **AC12.** `tests/test_boundaries.py`: the importers of `fasthtml`,
  `starlette`, `uvicorn` are exactly `{"evals/view.py", "chat.py"}`; `cli`,
  `agent`, `conversation` and the evals runner load none of them (subprocess
  test, as for the viewer); `conversation.py` is added to `CORE_CODE` in
  `scripts/intent-check-lib.mjs`.
- **AC13.** `advisor-chat` with `ADVISOR_MODEL_PROVIDER=anthropic` and no key
  exits 1 with the CLI's message; `--port abc` exits 2 (test: `tests/test_chat_cli.py`
  with `serve` and `client_factory` injected, as `advisor-analysis view` does).
- **AC14.** `uv run advisor "<question>"` is unchanged: `tests/test_cli.py`
  and `tests/test_cli_stderr.py` pass unedited, `git diff main -- src/advisor/cli.py`
  is empty, and a full `advisor-eval` run compares clean against the committed
  baseline (`advisor-analysis compare`; owed by `REVIEW-POLICY.md` "Eval runs"
  because `agent.py` changes).
- **AC15.** Live check (manual, owner): see below.
- **AC16.** `npm run verify` is green; the README gains an `advisor-chat`
  section (port, the 6-turn window, "local only").

### How the page is tested with no socket and no real model

`make_app(client, tools, tracer_factory, env=...)` takes everything injected,
like `evals.view.make_app`. A test builds it with a `ScriptedModelClient`
(scripted `ModelTurn`s, `repeat_last=True` for follow-ups), a recording
tracer factory and the catalogue's `search_tool`, wraps it in
`starlette.testclient.TestClient` (which `conftest.py` already allows) and posts
forms. Assertions are on the HTML and on `client.requests[n].messages`. No
uvicorn, no socket, no Ollama, no Langfuse.

### Live check the owner runs (owed: rule 3; the page and the model's behaviour in a conversation only show live)

1. `ollama serve` is up with `qwen3:8b`; `uv run advisor-chat`; open
   `http://127.0.0.1:5300`.
2. Ask "Do you have headphones under 150 euros?" then "anything cheaper than
   the second one?" then "which of those has the longest battery?": each
   answer follows from the earlier turns and names real catalogue products.
3. Ask "cheap laptop" then "something cheaper": no invented price limit is
   mentioned (the §33 rule across turns).
4. Click "New conversation": the page is empty, and "and cheaper?" now gets a
   clarifying answer, not a continuation.
5. With the `LANGFUSE_*` variables set, check the turns appear as separate traces
   with one `conversation:` tag.
6. Try `http://<your LAN address>:5300` from another machine or `0.0.0.0`: no
   connection. Stop Ollama and send a question: the page shows the "cannot
   reach Ollama" message and recovers when it is back.

## Non-functional

- **Boundaries:** `conversation.py` is pure (no I/O, no SDK, in `CORE_CODE`);
  `agent.py` changes only to accept `history`; `chat.py` is the only new
  importer of FastHTML/Starlette/uvicorn and the only I/O; `cli.py`,
  `tracer.py`, `tracing.py`, `guardrails.py`, `models/`, prompts, evals and
  `infra/` are unchanged. New files: `conversation.py`, `chat.py`, three test
  files. No new dependency (`pyproject.toml` gains only the console script).
- **Data:** synthetic catalogue, whatever a person types. Held in memory
  only (B10, at most 20 conversations, gone on restart); traces to the
  self-hosted Langfuse only when configured. No file written, no cookie
  beyond the signed session id.
- **Model use:** one `complete` loop per turn as today (at most 5 model
  calls); the prompt grows by at most 6 exchanges; same system prompt; the
  default stays local Ollama; anthropic works as in the CLI (key from `.env`).
  Model down: B9.
- **Autonomy:** answers about the catalogue only, no action, no escalation; no
  accounts, no login; reachable from this machine only (B12).

## Out of scope

Accounts, saved or exported conversations, streaming, JavaScript niceties, a
mobile layout, markdown rendering, deployment or any non-loopback bind, a
terminal chat, summarising old turns, replaying tool results, multi-turn eval
cases, a system prompt change, tracing changes (conversation id as a tag only),
and `cli.py` changes.

## Assumptions I made

- **A1. §33 is a prerequisite.** B8 and AC4 need `amounts.py` and the
  `question` argument of `_execute`, which are on `fix/33-no-invented-price-cap`
  and not on `main`. Recommend `blocked_by: 33` (not recorded: this draft did
  not touch `metadata.yml`). Everything else is independent of §33.
- A2. The window is 6 exchanges (B1); a number set by judgement against
  `NUM_CTX = 8192`, easy to change since it is one constant.
- A3. `chat.py` duplicates about 15 lines of `cli.main`'s configuration
  checks rather than factoring them out, so `cli.py` stays untouched (rule 1
  not triggered, AC14 trivial). A shared helper is a later refactor.
- A4. Port 5300 is outside spawn's 5200-5299 reservation; `--port` overrides.
- A5. The page is full-reload per turn (no JavaScript, no streaming).
- A6. A fallback answer stays in the history; a refusal does not.
- A7. Chat traces carry the tag `chat`, not `eval`, so `advisor-analysis
  queue`/`import` and the eval tooling do not pick them up.
- A8. The Host and Origin checks (B12) are a small addition beyond the
  intent, justified by cost on the anthropic provider; drop them if the owner
  thinks "not exposed" is enough.
