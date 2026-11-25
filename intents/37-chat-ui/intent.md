<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §37 — A very simple chat UI with multi-turn conversation

**Type:** feature
**Originator:** the owner ("have a very simple UI to ask questions and get
the answers, it should allow multi turn conversation", 2026-11-25)
**Source:** none. §1 listed "a UI" as a later intent; today the agent is
reached through `uv run advisor "<question>"` (one question, one answer, then
the process ends).

## Problem

The only way to talk to the agent is a command that takes one question and
exits. A person has to retype the whole context to follow up ("and
something cheaper?", "which of those has the longest battery?"), because
each run starts from nothing: `answer_question(question, ...)` and
`run_agent(question, ...)` take one string, and the model sees that string
as the only user message. There is no screen to type into and read answers
from, so the agent cannot be tried the way a customer would use it: a
conversation.

## Outcome

- A person opens a very simple page in a browser on their own machine,
  types a question, and reads the answer on the same page.
- They can keep going: a follow-up that depends on the earlier turns
  ("anything cheaper than the second one?") is answered with those turns in
  view, until they start a new conversation.
- Nothing else changes for the existing paths: `uv run advisor "<question>"`
  keeps its behaviour, the evals keep their one-question cases, and the
  guardrail seam still runs on every question and every answer.
- The checks that read the customer's question (the price-filter rule of §33
  in `amounts.py`, the evals' scoring) are not weakened by a longer
  conversation: what counts as "stated by the customer" is decided in the
  spec.

## Constraints

- **Data.** The catalogue is synthetic and there is no real user data
  (§1). A conversation lives only in the running page's memory and in
  traces to the self-hosted Langfuse; nothing is written to disk by the UI
  itself unless the spec says so. Traces must keep holding only what the
  person typed on a local machine; the page is for the owner's machine, not
  a public deployment.
- **Autonomy and exposure.** The agent still only answers about the
  catalogue (§1). The page binds to `127.0.0.1` only, loads no CDN or
  external asset, and has no login (the same rule as the local label
  viewer, `evals/view.py`): "not exposed" is the safety measure, not
  authentication. Anything that would let it be reached from another
  machine is out of scope.
- **Boundaries.** Provider and tracing libraries stay in their one module
  each (`tests/test_boundaries.py`); the web framework stays confined the way
  `fasthtml` is today. No new dependency without a line in `plan.md` saying
  why (FastHTML, Starlette and uvicorn are already dependencies).
- **Cost.** The default model is the local Ollama one; a UI must not make a
  paid provider the default. A long conversation grows the prompt sent each
  turn; the spec sets a limit.
- **Safety nets that already exist stay on:** `check_input` /
  `check_output`, the 5-turn tool loop, §31's ask-once-to-search, §33's price
  filter rule, §30's named-product rows.
- **Review tier.** A new user-facing surface and a change to the core agent
  loop (`agent.py`, core code); the tier is Reviewed by meaning ("anything
  that sends text to a user or an external system without a human in
  between"). A live check is owed (rule 1 covers `cli.py` if the UI is
  started from it, and the model's behaviour in a conversation is rule 3).
- **Out of scope:** accounts, saved conversations, streaming, a mobile
  layout, styling beyond readable, markdown rendering beyond what the
  answers already contain, any deployment, and changing the system prompt
  unless the spec finds it needed.

## Type-specific questions

### Feature
- **Users:** the owner and anyone trying the agent on the owner's machine;
  later possibly a demo.
- **What exists today:** the CLI (one question), the label viewer
  (FastHTML, `evals/view.py`, local only) as a precedent for a small local
  page, and the eval cases (one question each).
- **Open design questions for the spec:**
  1. **Web page or terminal chat.** "UI" is read as a web page; a terminal
     loop (`uv run advisor --chat`) would be far smaller. Which one, or both
     sharing the same conversation code?
  2. **What "multi-turn" passes to the agent.** The whole earlier
     conversation as messages, or a short summary, with what limit on length
     and what happens past it. Does the model also see its earlier tool
     results, or only the questions and answers?
  3. **The price-filter rule across turns.** §33's `amounts.py` drops a
     `max_price` that the question does not contain as a number; its spec
     says a future conversation feature must pass the customer's earlier
     turns to it. Are "stated amounts" from all earlier customer turns, or
     only the last one? Leaving it alone would drop a cap the customer
     stated two turns ago.
  4. **Guardrails per turn.** `check_input` on every customer message and
     `check_output` on every answer (a block gives the fixed refusal); does
     a blocked turn stay in the history?
  5. **Tracing.** One Langfuse trace per turn or one per conversation, and
     how a turn is linked to its conversation.
  6. **Where it lives and how it starts.** A new module (like `view.py`) and
     a console script (`advisor-chat`?) or a flag on `advisor`; the port.
  7. **State.** Where a conversation is kept (in the page, or in the
     server's memory keyed by a session) and what "new conversation" does.
  8. **Evals.** Whether any eval case should become multi-turn, now or
     later (probably later, its own intent).

## Assumptions I made

- "UI" means a web page on the owner's machine, not a terminal or a
  desktop app. It is the first open question, because a terminal chat is
  the smallest answer and would share the same history code.
- "Very simple" means one page, a text box, the conversation above it, a
  button for a new conversation, no styling work, and no JavaScript beyond
  what the framework needs.
- The default provider stays Ollama; the anthropic provider works as it does
  for the CLI (key from `.env`).
- It is a feature, not an adjustment: it touches the agent loop (core
  code) and adds a module, a console script and tests, well beyond 5 files
  and 60 lines.
- No `blocked_by`: it does not wait on any open intent. §36 (spec and plan
  agents) is unrelated.
