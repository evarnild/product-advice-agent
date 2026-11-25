<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §30 review — a named out-of-stock product is answered as "not in our catalogue"

verdict: escalate
tier: reviewed
reviewed-commit: 1017f32
main: b370233
round: 2
sampled: no
run: auto
live-check: owed

Tier: the path table alone makes this Attested (`src/**` core code). Round 1
raised it to Reviewed under rule 3 and the reason still holds: Not-checked
item N1, how a real model words an answer from a `filters_failed` row,
decides what a user receives. A tier is never lowered.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: round 1 finding 2 is decided as (a) and pinned by a test; `git diff main...HEAD -- src` is only §30's change |
| 2 | Type check | pass apart from the owed live check, which is the owner's to clear |
| 3 | Behaviour against the intent's reproduction | pass; the §30 and §31 interaction was probed (below); eval run below |
| 4 | Tests prove the behaviour | pass: 27 mutants, 26 killed, 1 equivalent |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: 15 new tests in `tests/test_agent.py`, 5 in `tests/test_catalogue.py`; 965 in the suite |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass: only model-facing description text changed |
| 9 | Repo-specific footguns | pass |

## Type check

```
type-check: FAIL (intent 30, fix)
  error: A live check is owed and not recorded. ...
  note:  6 file(s), 303 line(s) changed outside intents/.
```

The only error is the owed live check.

## Round 1 findings, re-checked

1. HIGH (`min_price` not proven): fixed.
   `test_named_product_failing_only_min_price_is_appended` is what was asked
   for; mutant A-min-none is killed by it alone.
2. MEDIUM (limit-cut named product), decided by the owner as option (a):
   pinned by `test_named_product_passing_every_filter_but_cut_by_limit_is_not_appended`;
   mutant A-append-all is killed by it alone.
3. LOW (dead `shown` guard): a comment marks it defensive; A-no-dedupe stays
   equivalent.
4. LOW (Progress count): corrected (13 + 2 = 15 in `tests/test_agent.py`).
5. LOW (description filter list): no rework asked.

## The merge with main (§31, §32)

The reviewer read the merged `run_agent` and `_execute`: §31 only touches
text-only replies, §30 only what `search_tool.run` returns; they do not
overlap. A scratch probe gave: a name search on the first turn makes 2
requests and shows P-017 once, last, with `["category","max_price","in_stock_only"]`;
a text-first reply, then the §31 request, then the same search shows the
same single row; two searches in one turn show P-017 once in each result.
No committed test combines the §31 re-ask with a named row (each half is
tested alone, the paths do not interact): not a finding.

## Findings

1. **LOW** `src/advisor/agent.py:150,155`: `shown` and `p.id not in shown`
   are still dead code (A-no-dedupe is equivalent). Kept on purpose, with a
   comment. No rework.

No finding needs rework or a decision.

## Mutations

27 mutants on a `git archive HEAD` copy (reviewer, never the worktree), each
a full pytest run: the tool's filter arguments (min, max, category, stock),
append-all, the limit exemption, prepend, the marker field, `keywords_matched`,
the loop, both description sentences, each of the four filter checks, the
boundaries, the order, the filter-name string, `fold` against `lower()`,
substring match, the `MAX_LIMIT` cap and `passes`. Killed: 26. Survived: 1
(A-no-dedupe, equivalent).

## Not checked

- N1: what a real model says when it gets a `filters_failed` row: does it
  name the product with its real category, price and stock, and avoid
  offering it as a fit? The eval scorer would pass "out of stock, but a cheap
  option". The live check.
- Round 1's mutant A-desc-filterlist (LOW, no rework) was not re-run.

## Live check

Owed under rule 3 (N1). Rule 1 does not apply (no `cli.py`, `models/`,
`tracing.py`, `prompts/` or `infra/`). In the worktree
`C:/Users/eric/src/product-advice-agent-wt/30-out-of-stock-named-product` at
1017f32 or later, with Ollama running (the default), ideally with the local
Langfuse up and the three `LANGFUSE_*` variables set:
1. `uv run advisor "Is the Sonavo Quiet Pro available? I only want something in stock."`
2. `uv run advisor "hey is the Norvik Fold still available? im a student so i cant really spend much, is it cheap?"`
3. `uv run advisor "My son wants the Norvik Canvas 13 tablet for school, is it in stock?"`

You should see:
- each answer names the product with its id (P-004, P-017, P-024);
- each says the product is out of stock, and for the Fold that it is a
  1499 euro phone, not cheap;
- no answer recommends the named product as a fit or says "not in our
  catalogue";
- in the trace, when the model set a filter that drops the product, the last
  tool row is that product with `filters_failed` (the Fold searched with
  category tablet, max 200 and stock: category, max_price, in_stock_only);
- if the model first answered without searching, a second generation follows
  the "You answered without searching..." request, and the named row appears
  exactly once in the tool result.

If an answer recommends the named product or says it is not in the
catalogue, leave `live_checked:` empty and describe it.

## Eval run

- Report: `evals/runs/20261125T103024Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at 1017f32, the reviewed content (it
  contains `main`, with §31 and §32). `advisor-analysis hashes` exits 0:
  cases, prompt and catalogue hashes match.
- `compare` against `evals/baseline.json` (the §31 run, 40/50): 43/50.
  Regressed (0). Fixed (3): `voice-speaker` and `monitor-curved-tuner-300`
  (both fail at random on unchanged code) and `norvik-fold-brother-gift`.
- What the run shows for this change: the six out-of-stock cases now search by
  name where they searched at all, and the answers name the product, say it
  is out of stock and give its real price (799 euros for the Canvas) where
  the baseline said "not in our catalogue":
  - `out-of-stock-quiet-pro` PASS and `norvik-fold-brother-gift` PASS (the
    answers cite P-004 and P-017);
  - `norvik-canvas-school` names P-024 at 799 euros but FAILs `prices` (it
    suggests two other tablets without stating their prices);
  - `norvik-fold-cheap-student` FAILs `expected` (no P-017 id; the model
    searched category tablet, max 200 and stock, so the row the tool appends
    is there but the answer does not cite it);
  - `pelagic-studio-back-soon` names the laptop but does not cite P-010;
  - `aurelis-home-gift-mum`: the model searched `["Aurelis"]` (the customer's
    spelling), which is not the product's name, so the exact-name rule does
    not reach P-032, as the intent's assumptions said.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run), in the worktree at 1017f32:
  - mutant A-min-none (`filters["min_price"]` to `None`, `agent.py:148`): 1
    failed, 964 passed; killed by
    `test_named_product_failing_only_min_price_is_appended`;
  - mutant A-append-all (`if failed and p.id not in shown:` to
    `if p.id not in shown:`, `agent.py:150`): 1 failed, 964 passed; killed by
    `test_named_product_passing_every_filter_but_cut_by_limit_is_not_appended`;
  - both restored by copy, `git status --short` clean;
  - the branch update (`update-branch` exit 0, merged `main`, `verify` green
    at the merge: 965 pytest, 490 kit tests); `npm run check:intent`: the one
    error above;
  - the full eval run, `hashes`, `compare` and the case table above.
- Verified by the reviewer: `verify` exit 0 (965 passed); the 27 mutants; the
  §30/§31 probe; the test counts; `git diff main...HEAD -- src`; the README
  and CLAUDE.md lines.
- Taken on trust: the model's wording beyond the eval run (the live check).

---

# Round 1 (history)

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
