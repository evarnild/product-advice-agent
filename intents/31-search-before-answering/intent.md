<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §31 — Search the catalogue before answering about products

**Type:** fix
**Originator:** the coordinator's analysis of 10 qwen3:8b eval runs of the
50 cases, for the owner ("write intents")
**Source:** `evals/runs/20261124T215703Z-ollama.json` (latest) and the nine
earlier qwen3:8b runs `evals/runs/2026112*-ollama.json`

## Problem

The model sometimes answers a product question without calling
`search_products` at all, and the agent takes that answer as final.
`run_agent` in `src/advisor/agent.py` returns the first text reply that has
no tool call:

```python
if not reply.tool_calls:
    if reply.text:
        return AgentResult(reply.text, turn, False)
```

In the latest run 9 cases have `searches: []`. Four are the `off-topic-*`
cases, which pass by declining. The other five fail:

- `tv-sound` ("Something to improve the sound of my TV"): the whole answer
  is "To improve the sound of your TV, you might consider a soundbar or a
  speaker system. Let me check the available options in the shop's
  catalogue." and the run stops there. It failed 6 of 10 runs (4 of the
  last 6); 4 of the failures had no search.
- `laptop-bathrom-projector`: no search in all 10 runs; "I couldn't find
  any laptops that are waterproof… Would you like me to search for such
  options?" without having searched.
- `pelagic-studio-back-soon`: no search in all 10 runs; "I don't have
  access to real-time inventory updates…".
- `norvik-fold-brother-gift`: no search in all 10 runs; it invents
  "Acme Foldable (P-004)" and "TechFold Pro (P-007)" (P-007 is the Norvik
  Slate 14).
- `aurelis-home-gift-mum`: no search in all 10 runs; it invents "Aurelis
  Home 2 (P-012)" and "Aurelis Home 3 (P-013)" (real ids of the Tolvane
  Chrome 11 and the Zephra One).

The last three are also in §30's out-of-stock group. `video-editing-laptop`
went without a search in one earlier run too.

A customer gets an answer that names no product, promises a search that
never happens, or recommends products that do not exist under ids that do.

## Outcome

- When the model's reply has text and no tool call and no
  `search_products` call has been made yet in the run, the agent asks the
  model once to search the catalogue before answering, instead of
  returning that text. A unit test with the scripted fake shows it.
- The 5-turn cap still holds: the extra request uses one of the 5 turns,
  and the fixed fallback answer is still what a run that reaches the cap
  without a final text gets.
- An eval run (`REVIEW-POLICY.md` → "Eval runs") shows the five cases above
  calling `search_products`, and states what happened to the four
  `off-topic-*` cases. Expected effect: 2 to 5 cases flip to PASS (the
  out-of-stock ones may still fail `expected` until §30 lands).

## Constraints

- `agent.py` is core code (`CORE_CODE`): pure orchestration over a
  `ModelClient`, no I/O, no provider SDK. The test drives
  `ScriptedModelClient` and asserts on what it received.
- At most one request to search per run, never a loop; `MAX_TURNS` stays 5.
- `FALLBACK_ANSWER` and `REFUSAL_TEXT` do not change.
- The trace stays one trace. It gains one generation for the extra turn
  (the tracer has no event for a message the agent adds itself); the
  plan says whether that message needs to show in the trace or in the eval
  report's `turns`.
- Off-topic and greeting questions must still be declined. Today the four
  `off-topic-*` cases (`must_decline: true`) pass because the model
  declines without searching; the guardrails cannot cover them
  (`check_input` and `check_output` always allow). After this change the
  model is asked to search on those too. Whether that is acceptable, or the
  request is phrased so the model may still decline, is an open point for
  the plan. No eval case is a bare greeting ("Hi"); two product cases begin
  with "Hi,".
- A change to `agent.py` owes an eval run. It is not a live-check path
  under rule 1; whether rule 3 applies is for `/review`.
- Out of scope: the system prompt (§33 changes it for another reason),
  §30's out-of-stock answers, and new eval cases.

## Type-specific questions

### Fix
- **What broke:** observed: a text-only first reply is the final answer,
  even when it names products or promises a search. Expected: an answer
  about products always follows a catalogue search.
- **Since when:** the loop's rule since §1 (`intents/1-stack-and-skeleton`);
  it shows with the local qwen3:8b model since §2. Not a regression.
- **Impact:** the customer sees a non-answer or invented products with real
  ids. In the evals, 5 of 50 cases fail on it in the latest run. Offline
  evals only so far; no data leak.
- **Reproduction:** `uv run advisor-eval --provider ollama --only
  tv-sound,laptop-bathrom-projector,pelagic-studio-back-soon,norvik-fold-brother-gift,aurelis-home-gift-mum`;
  `searches` is `[]` and `turns` has one entry for most of them. In a unit
  test: `ScriptedModelClient([final("Let me check the catalogue.")])`.
- **The test that will fail first:** `tests/test_agent.py`: a fake that
  replies with text and no tool call, then a search call, then a final
  text; the test asserts that `run_agent` does not return the first text,
  that the second request the fake received ends with the agent's
  request to search, and that the answer is the final text. A second test
  asserts that a text-only reply after that request is returned (asked
  once only).

## Assumptions I made

- "Before any search" counts any earlier `search_products` call in the run,
  not just turn 1: `test_empty_turn_counts_and_continues` (an empty turn,
  then text with no search) changes behaviour and is updated in the plan.
- The text-only reply is kept in the conversation as an assistant message
  before the request to search, so the model sees what it said; the exact
  wording of the request is the plan's.
- The request is a user-role message added by the agent, not a change to
  `prompts/system.md`, so this stays out of the prompt paths and §33.
- If the model answers in text again after the request, that text is the
  answer (no fallback), so a decline still reaches the user.
- `follows_up` is left empty: the loop works as §1 specified; no earlier
  change introduced a defect.
- `review_tier` left empty: `agent.py` is `src/**`, so Attested by the path
  table; it is not on the "by meaning" list.
