<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §31 review — Search the catalogue before answering about products

verdict: rework
tier: reviewed
reviewed-commit: 9d31af303dcc65354d48a232e4262d2cfab2069e
main: 389d93d
round: 1
sampled: no
run: auto
live-check: owed

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: the code is as the plan wrote it; the eval run below shows the five no-search cases now search and the four off-topic cases still decline |
| 4 | Tests prove the behaviour | findings (1, HIGH) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1, LOW) |
| 7 | Documentation | pass: `CLAUDE.md:172-173` and `README.md:75-76` describe the behaviour accurately |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo-specific footguns | pass (the list is empty) |

Tier: the path table makes it Attested (`src/advisor/agent.py` and tests).
The HIGH finding raises it to Reviewed (rule 3). It would be Reviewed anyway
by meaning: `SEARCH_FIRST_TEXT` (`src/advisor/agent.py:32-36`) is an
instruction the product sends to the model on every no-search answer. It
lives outside `src/advisor/prompts/` only because the plan put it there. The
owner should read it as prompt text.

## Type check

```
type-check: PASS (intent 31, fix)
  note:  7 file(s), 132 line(s) changed outside intents/.
```

## Findings

1. **HIGH** `src/advisor/agent.py:195`: the "never ask on turn 5" boundary is
   tested from one side only. Mutant M5 (`turn == MAX_TURNS` changed to
   `turn >= MAX_TURNS - 1`) survived the full suite (932 passed). T8 pins
   turn 5 and T7 pins turn 1; nothing pins turn 4.
   **Needs rework:** add a test with the script
   `[call({}, name="nope")] * 3 + [final("x"), final("y")]` asserting
   `answer == "y"`, `turns == 5`, `not fallback`, 5 requests, and that the
   fifth request ends with `Message("user", SEARCH_FIRST_TEXT)`.
   Resolution: done in rework commit `7c6e888`
   (`test_text_on_turn_four_is_asked_and_text_on_turn_five_is_returned`).
2. **LOW** `plan.md` Progress: "932 passed (was 925 before: +7 net)" is wrong.
   Main collects 926 tests; the branch adds 6 test functions (T5 and T6
   rewritten in place), so the net is +6.
   **Needs rework:** correct it in a new Progress entry. Resolution: done in
   `7c6e888`.
3. **LOW** `tests/test_tracing.py:125`: the rule that `searched` stays true
   once a search has happened (`agent.py:202`) was pinned only by accident:
   mutant M17 (`searched = False or any(...)`) was killed only by an
   unrelated tracing test. Resolution: pinned directly in `7c6e888`
   (`test_a_search_keeps_counting_after_later_tool_turns`).

## Mutations

22 mutants on `agent.py` (reviewer), each a full pytest run on a byte backup,
restored after each. 21 killed. M5 survived (finding 1, now killed by the
turn-four test). The mutants cover the condition and each of its parts, the
two appended messages, their order and roles, the empty-reply path, what
counts as a search (any tool name, `any` against `all`), the initial values
of `searched` and `asked`, and the constant's wording (pinned by
`test_search_first_text_is_pinned`).

The 29 existing tests the change broke were checked one by one: the doubled
replies in `HP_BAD`, `LAP_OK`, `OFF_OK` and `answer_only`, the request
counts (3 to 5 and 2 to 4), the extra Langfuse `generation`, and the two
subprocess probes (`repeat_last=True`). None is weakened; with the old
behaviour 17 eval-run tests fail, so the doubling is load-bearing.

## Not checked

- What a real model does with the added request beyond the 50 cases (the
  eval run below covers those).
- The Anthropic provider is not exercised live: the message sequence (a
  text-only assistant message, then a plain user message) is valid by
  inspection of `models/anthropic_model.py:36-56`, not run against the API.
- The request does not appear as its own event in the trace or in the
  report's `turns`: one more generation, as the plan chose. A reader of a
  Langfuse trace cannot see that the agent asked.

## Live check

- Owed under rule 3: what a real model does with the agent-added request,
  including the off-topic risk the intent names. The eval run is an agent's
  run, so it is evidence and not the gate.
- Steps, in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/31-search-before-answering`
  with Ollama running and `qwen3:8b` pulled (the default; no key):
  1. `uv run advisor "Something to improve the sound of my TV"`
  2. `uv run advisor "What's the weather in Paris tomorrow?"`
  3. Optionally, with the local Langfuse up and the three `LANGFUSE_*`
     variables set, open each run's trace.
- You should see:
  1. An answer that names a real catalogue product with its id (expected
     P-031, a soundbar). Not "Let me check the available options…" and
     nothing more.
  2. A decline that names no product and no P-id.
  3. For question 1, two or more generations, with a `search_products`
     tool observation before the final one.
- If question 1 still ends on a promise to search, or question 2
  recommends a product, leave `live_checked:` empty and send it back.

## Eval run

- Report: `evals/runs/20261125T085756Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at 9d31af3. `advisor-analysis hashes`
  exits 0: cases, prompt and catalogue hashes match the reviewed content.
- `compare` against `evals/baseline.json`: 40/50 against 38/50.
  - fixed (4): `tv-sound`, `out-of-stock-quiet-pro`,
    `laptop-bathrom-projector`, `gaming-monitor`. The last is not this
    change (it fails at random on the unchanged prompt, 3 of 10 runs).
  - regressed (2): `voice-speaker` and `monitor-curved-tuner-300`, both
    PASS to FAIL. Re-run with `--only voice-speaker,monitor-curved-tuner-300`
    three times: PASS in all three. Variation, not regressions.
- The five cases that made no search in the baseline: `tv-sound`,
  `laptop-bathrom-projector`, `pelagic-studio-back-soon`,
  `norvik-fold-brother-gift` and `aurelis-home-gift-mum` now each make one
  search. The last three still fail on `expected` (they cite a product other
  than the out-of-stock one they were asked about): that is §30's.
- The four `off-topic-*` cases (`weather`, `poem`, `sourdough`, `zone-two`)
  all PASS, with no search and two turns each: the model declined after the
  request, as the wording allows.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run): the eval run, `hashes`, `compare`,
  the three `--only` re-runs and the case table above. The rework's own
  re-check (verify, check:intent, the two mutants) is in round 2.
- Verified by the reviewer: `git rev-parse HEAD` = 9d31af3; `npm run verify`
  exit 0 (490 kit tests, 932 pytest); `npm run check:intent` PASS; the 22
  mutants above; the plan's diff line by line; the 29 updated tests.
- Taken on trust: the plan's claim that a prototype broke exactly 29 tests
  (the updated set is consistent with it); the reviewer's reading of the
  Anthropic conversion code.
