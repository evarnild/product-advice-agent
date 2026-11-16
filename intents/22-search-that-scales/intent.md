<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §22 — Product search that still finds the right product in 500

**Type:** feature
**Originator:** me (the owner), from §14's live check: "I confirm that F5 of the review is a problem", then "accept the regression but write a new follow up intent"
**Source:** `intents/14-catalogue-500/review.md` → F5 and "Live check result (2026-11-16, owner)"

## Problem

On the 500-product catalogue (§14) the agent recommends the cheapest
matching products rather than the ones that fit the question. The live
check measured it: `advisor-eval --provider ollama` fell from 11/15 on
`main` (32 products) to 9/15.

- `student-laptop` ("A laptop for a student, under 700 euros"): the model
  searched `{category: laptop, max_price: 700}`. The search returned the
  five cheapest laptops (P-241, P-012, P-281, P-073, P-033), and P-009,
  the one described "for students", ranks 10th. A keyword search for
  `student` would have returned only P-009, but the model did not use one.
- `nc-headphones-under-200`: P-001 is no longer among the five cheapest
  noise-cancelling headphones under 200.
- The same search shape fails in older cases too:
  - `tv-sound`: the keywords `["soundbar", "external"]` must all match, so the search finds nothing;
  - `sport-earbuds`: the model searched `["wireless", "earbuds"]` under 50 and found nothing.

The cause is in how the search ranks results:
- results are ordered price-then-id, cheapest first;
- the tool returns 5 by default (at most 10);
- every keyword must appear.

That was fine with 32 products. With 500, a real customer asking for a
student laptop is shown five budget laptops.

## Outcome

- **Both regressions recover.** On the committed 500-product catalogue,
  `student-laptop` and `nc-headphones-under-200` pass again in
  `uv run advisor-eval --provider ollama`, in two runs out of two.
- **No new failures.** No case that passes on §14's branch fails, and the
  pass rate is at least 11/15 in both runs.
- **Unit tests prove the new behaviour.** A question whose words match a
  product's description finds that product even when 10 or more cheaper
  products match the other filters. This is tested deterministically with
  a fake client, on the real 500-product catalogue.
- **The search contract stays honest.** Nothing returned is outside the
  category, price or stock filters, and no product id is invented
  (`grounded` and `prices` stay green).

## Constraints

- **Code boundaries.** `catalogue.py` and `agent.py` are core code, pure and
  tested. The tool keeps its name and stays one tool. Provider and tracing
  boundaries are unchanged (`tests/test_boundaries.py`).
- **No new dependency.** No embedding model, vector store or search library
  without a plan line saying why. A ranking computed from the catalogue's
  own text is the default.
- **Evals.** They run on Ollama. A paid (Anthropic) run happens only on the
  owner's request. Model calls are faked in tests.
- **Prompt changes.** If the fix touches `src/advisor/prompts/system.md`,
  that is Reviewed tier, and it owes a live check (rule 1).
- **The cases are not loosened.** Fixing the eval cases (§15's
  `cites_a_match`) is not this intent's way to the outcome.
- **Out of scope.** Growing the catalogue again; the other failing cases
  (`video-editing-laptop` makes no search at all; `out-of-stock-quiet-pro`)
  unless the change fixes them as a side effect.

## Type-specific questions

### Feature
- **Users:**
  - the end user asking for advice;
  - the owner, through the eval pass rate.
- **What exists today:**
  - `search_products` (`src/advisor/catalogue.py:113`): AND of filters, all keywords required, price-then-id order, limit clamped to 1..10;
  - the tool (`src/advisor/agent.py`): default `limit` 5;
  - the system prompt tells the model to search with "the category, price range, keywords and stock filter that match".
- **Open design questions** (for spec.md):
  1. **Ranking.** Should results be ranked by how many of the question's
     keywords they match (then price), rather than by price alone?
  2. **Keyword logic.** Should keywords stay all-required (AND), or should
     a product match on any of them and rank by the count, so that extra
     words like "external" or "wireless" no longer empty the result?
  3. **Default limit.** Should it rise from 5, to 10 or another number?
     Weigh this against prompt size and the model's attention.
  4. **The prompt.** Does it need a line telling the model to put the
     question's distinguishing words ("student", "noise-cancelling",
     "sport") into `keywords`? This raises the tier to Reviewed and owes a
     live check.
  5. **Empty results.** Should a search with no result say which filter
     emptied it, so the model can widen the search itself?
  6. **Measuring it.** What counts as "fixed" when model runs are
     nondeterministic: two runs, three, or a pass rate over N runs?

## Assumptions I made

- It is a feature, not a fix: the search behaves as §1 specified, and the
  catalogue outgrew it. The spec settles the new behaviour.
- It is blocked by §14: the outcome is measured on the 500-product
  catalogue, so §14 merges first.
- Tier: Attested by the path table unless the prompt changes. A prompt
  change makes it Reviewed. `review_tier` is left empty for now.
- "Two runs out of two" is my first reading of question 6. The spec can
  change it.
- §15 (fifty cases) and this intent touch different files. They may run
  in either order after §14.
