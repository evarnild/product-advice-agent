<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §30 review — a named out-of-stock product is answered as "not in our catalogue"

verdict: rework
tier: reviewed
reviewed-commit: 3fa2a49
main: b1bfbbe
round: 1
sampled: no
run: auto
live-check: owed

Tier: the path table makes this Attested (`src/**` core code) and
`review_tier` is empty. Rule 3 raises it to Reviewed: finding 1 is HIGH, and
Not-checked item N1 (how the model words an answer from a `filters_failed`
row) bears on what a user receives.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | one finding (2); both declared divergences hold (§32's `fold`; the unchanged-search test compares against the B11 fallback rows) |
| 2 | Type check | pass |
| 3 | Behaviour against the intent's reproduction | pass: all three reproductions re-run on main and on the branch |
| 4 | Tests prove the behaviour | findings (1 and 2): 32 mutants, 27 killed, 2 real survivors, 2 equivalent, 1 trivial |
| 5 | Conventions | pass |
| 6 | Numbers in prose | one LOW finding (4) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check

```
type-check: PASS (intent 30, fix)
  note:  6 file(s), 287 line(s) changed outside intents/.
```

## Findings

1. **HIGH** `src/advisor/agent.py:147`: the `min_price` argument to
   `failed_filters` in the tool is not proven. Mutant A-min-none
   (`filters["min_price"]` to `None`) survives the full suite (955 passed).
   The tool's only `min_price` test (`tests/test_agent.py:505`, `min_price: 100`
   against P-017 at 1499 euros) has the product passing the minimum. With the
   mutant, a named product under the customer's minimum loses `"min_price"`
   from `filters_failed`, and if the minimum is the only filter it fails the
   product is not appended at all: the "vanishes" bug this fix exists for.
   **Needs rework:** add a tool-level test where the named product fails
   `min_price` (for example `{"keywords": ["Sonavo Quiet Pro"],
   "min_price": 200}` must put P-004 last with `filters_failed ==
   ["min_price"]`) and re-run A-min-none.
2. **MEDIUM** `src/advisor/agent.py:149` and the plan's Assumptions ("a named
   product cut by `limit`"): the plan says "the ordering already puts a name
   match first". On the committed catalogue that is false for a multi-keyword
   search: `{"keywords": ["Norvik Fold", "phone", "camera"]}` with no filters
   and the default limit returns 10 rows without P-017 (every row matches 2
   keywords and P-017, at 1499 euros, loses the price tiebreak). The named
   product still vanishes, here through `limit`, not a filter. It occurs in 0
   of the 543 recorded searches and is outside the intent's literal outcome
   ("the filters drop that product"). Mutant A-append-all (`failed and` to
   `p.id not in shown`) survives because no test covers it; the plan's
   mutation map credits the wrong guard.
   **Needs decision (owner):** (a, recommended) keep the plan's behaviour and
   add a test that pins "a passing named product cut by `limit` is not
   appended" (kills A-append-all); (b) append limit-cut named products too,
   with no `filters_failed` key or an empty one: this amends the plan above
   its Progress marker and makes the `shown` guard live.
3. **LOW** `src/advisor/agent.py:144,149`: `shown` and `p.id not in shown` are
   dead code today (every row in `found` passes all four filters). Mutants
   A-no-dedupe and A-shown-empty are equivalent. Drop the guard, or keep it
   with a comment that it is defensive; under 2(b) it becomes live and needs
   its own test.
4. **LOW** `plan.md:251` (Progress, below the marker): says "12 in
   `tests/test_agent.py`"; the diff adds 13 `def test_` functions there
   (5 in `test_catalogue.py` is right). **Needs rework:** change it to 13 in
   a new Progress entry.
5. **LOW** `src/advisor/agent.py:164`: dropping the list of filter names from
   the tool description survives (A-desc-filterlist); the description test
   asserts the other two phrases. No rework needed.

## Mutations

32 mutants on a `git archive HEAD` copy (reviewer, never the worktree), each a
full pytest run: killed (27): each of the four filter checks dropped, the
boundaries, each filter-name string, the order reversed, substring and prefix
name match, `lower()` for `fold`, the cap dropped or at 9, reversed catalogue
order, `passes` forced, the loop disabled, the field dropped or empty,
`keywords_matched` 0, `rows[:limit]` (the limit exemption), prepend instead of
append, the swaps and Nones for min, max, stock and category, and the
description sentence. Survived: A-min-none (finding 1), A-append-all (finding
2), A-no-dedupe and A-shown-empty (equivalent, finding 3), A-desc-filterlist
(finding 5).

## Not checked

- N1: what a real model says when it gets a `filters_failed` row: does it name
  the product with its real category, price and stock, and not offer it as a
  fit? The eval scorer only checks that an answer citing an out-of-stock
  product contains "out of stock" (`score.py:111`), so "the Norvik Fold is out
  of stock, but it is a cheap option" would pass. Bears on what a user
  receives: the live check.
- That the eval run flips the named cases (below).

## Live check

Owed under rule 3 (N1): the tool result the model sees changes, and the new
tool-description sentence is model-facing instruction text. Rule 1 does not
apply (no `cli.py`, `models/`, `tracing.py`, `prompts/` or `infra/`).

Steps, in the worktree
`C:/Users/eric/src/product-advice-agent-wt/30-out-of-stock-named-product`, at
the reviewed commit after rework, with Ollama running (the default) and
ideally the local Langfuse stack and the three `LANGFUSE_*` variables set:
1. `uv run advisor "Is the Sonavo Quiet Pro available? I only want something in stock."`
2. `uv run advisor "hey is the Norvik Fold still available? im a student so i cant really spend much, is it cheap?"`
3. `uv run advisor "My son wants the Norvik Canvas 13 tablet for school, is it in stock?"`

For each answer, with Langfuse up, open the trace's `search_products`
observation. You should see:
- each answer names the product with its id (P-004, P-017, P-024);
- each says the product is out of stock, and for the Fold that it is a
  1499 euro phone, not cheap;
- no answer recommends the named product as a fit or says it is "not in our
  catalogue";
- in the trace, when the model set a filter that drops the product, the last
  tool row is that product with `filters_failed` (for the Fold search with
  category tablet, max 200 and stock: category, max_price, in_stock_only).

## Eval run

- Report: `evals/runs/20261125T095700Z-ollama.json` (ollama, qwen3:8b), made by
  the coordinator in the worktree at 3fa2a49. `advisor-analysis hashes` exits
  0 (cases, prompt, catalogue hashes match the reviewed content).
- `compare` against `evals/baseline.json` (now the §31 run, 40/50): 38/50.
  This branch was merged with `main` before §31 merged, so two of the four
  PASS to FAIL are §31's effect and not this change: `tv-sound` and
  `laptop-bathrom-projector` (both searched in the baseline, made no search
  here). The other two, `waterproof-camera` and `out-of-stock-quiet-pro`,
  re-run with `--only` three times: PASS 2 of 3 for each; the failure of
  `out-of-stock-quiet-pro` was "price of P-123 (Kestrel Calm 46) not stated"
  (an alternative's price), the one of `waterproof-camera` "does not cite
  P-029": variation, not regressions. Fixed (2): `voice-speaker`,
  `monitor-curved-tuner-300` (random).
- What the run shows for this change: `out-of-stock-quiet-pro` and
  `norvik-canvas-school` answers now name the product, say it is out of stock
  and give its real price (799 euros for the Canvas), where the baseline said
  "not in our catalogue". `norvik-canvas-school` and
  `norvik-fold-cheap-student` still FAIL `expected` (the answers do not cite
  P-024 or P-017 by id: the prompt asks for name and id, the model wrote the
  name only). `pelagic-studio-back-soon`, `norvik-fold-brother-gift` and
  `aurelis-home-gift-mum` made no search here, as in §31's baseline run (and
  "Aurelis" is misspelt, so an exact name match never reaches P-032).
- A fresh full run on the branch merged with current `main` is made in round 2.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run), in the worktree at 3fa2a49: the full
  eval run, `hashes`, `compare` and the three `--only` re-runs above. No
  mutant of this round's review survives that I re-ran: the real survivors
  (A-min-none, A-append-all) are re-run after the rework in round 2.
- Verified by the reviewer: `npm run verify` exit 0 (955 passed, kit tests,
  ruff, mypy); `npm run check:intent` PASS; the intent's three reproductions on
  main and on the branch; the replay of 543 distinct recorded
  `search_products` argument sets old code vs new code: 529 identical, 14
  differ and in all 14 main's result is an exact prefix of the branch's plus
  one appended named row (P-004, P-024, P-017, P-032 or P-010), no ordinary
  search changed; no false positive from a keyword equal to a whole name
  (all 500 names are brand plus model, unique when folded); the 32 mutants.
- Taken on trust: the six cases' recorded searches as the intent quotes
  them, beyond the replay.
