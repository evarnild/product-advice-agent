<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §30 — A named out-of-stock product is answered as "not in our catalogue"

**Type:** fix
**Originator:** the coordinator's error analysis of the qwen3:8b eval runs
of 2026-11-24, turned into an intent on the owner's "write intents";
widened by the owner on 2026-11-25: "for 30 try to fix the category and
price filters as well"
**Source:** `evals/runs/20261124T215703Z-ollama.json` (latest) and the
earlier qwen3:8b runs of 2026-11-24; `intents/22-search-that-scales`
(B11, the keyword fallback)

## Problem

A customer who asks about a product by name, when that product is out of
stock, is told it is not in the catalogue, or is offered products with
invented names. Six cases fail in every qwen3:8b run; all six ask about a
product with `in_stock: false`:

| Case | Product |
| --- | --- |
| `out-of-stock-quiet-pro` | P-004 Sonavo Quiet Pro (headphones, €159) |
| `pelagic-studio-back-soon` | P-010 Pelagic Studio 15 (laptop, €1299) |
| `norvik-fold-brother-gift` | P-017 Norvik Fold (phone, €1499) |
| `norvik-fold-cheap-student` | P-017 Norvik Fold (phone, €1499) |
| `norvik-canvas-school` | P-024 Norvik Canvas 13 (tablet, €799) |
| `aurelis-home-gift-mum` | P-032 Auralis Home 1 (speaker, €119) |

There are three mechanisms:

1. **The model sets the stock filter and the tool hides the product.** It
   searches the product's name with `in_stock_only: true`, although
   `src/advisor/prompts/system.md:12` says "Set `in_stock_only` only when
   the customer asks for products in stock; otherwise leave it off, so an
   out-of-stock match can still be named and flagged." The filter drops
   the only row that matches. The §22 B11 fallback then returns ten other
   in-stock products, each with `keywords_matched` 0. From the latest run:
   - `out-of-stock-quiet-pro`: `{"keywords": ["Sonavo Quiet Pro"],
     "in_stock_only": true}` → "The Sonavo Quiet Pro is not available in
     our catalogue. Here are some similar products…" (P-123, P-107, P-291).
   - `norvik-canvas-school`: `{"keywords": ["Norvik Canvas 13"],
     "category": "tablet", "in_stock_only": true}` → "The Norvik Canvas 13
     is not available in our catalogue."
   The same searches without `in_stock_only` return exactly the named
   product (`{"keywords": ["Sonavo Quiet Pro"]}` → P-004 alone,
   `keywords_matched` 1).
2. **The model guesses a wrong category or price, and those filters hide
   it.** For `norvik-fold-cheap-student` the model searched
   `{"keywords": ["Norvik Fold"], "category": "tablet", "max_price": 200,
   "in_stock_only": true}` (three runs), `{…, "category": "smartwatch",
   "max_price": 200, …}` (one run) and `{"keywords": ["Norvik Fold"],
   "category": "tablet", "min_price": 100, "in_stock_only": true}` (one
   run). The Norvik Fold is a €1499 phone, so category and price drop it
   even without the stock filter. Answer: "The Norvik Fold is not in our
   catalogue." In the latest run it searched `["student"]` only, with no
   name at all.
3. **No search at all** (`pelagic-studio-back-soon`,
   `norvik-fold-brother-gift`, `aurelis-home-gift-mum`, every run). That
   is §31's problem, not this one's.

## Outcome

- When a search's keywords name a catalogue product, and the category,
  price or stock filters drop that product, the tool result still lets
  the model see that the product exists. It shows the product's id and
  name, and its real category, price and stock, so the answer can name it
  truthfully ("the Norvik Fold (P-017) is a €1499 phone and is out of
  stock"). It no longer looks as if the product is missing.
- Tests drive the agent with the fake `ModelClient` on the committed
  catalogue, one per filter (see the failing-first tests below). Each
  tool result contains the named product with its real fields.
- A search whose keywords name no product behaves as today. That covers
  ordinary feature words such as "student" or "noise-cancelling", and
  the B11 fallback. The rows that pass the filters still pass them all.
- An eval run (`REVIEW-POLICY.md` → "Eval runs") is made on the change.
  The review names every one of the six cases that flips. For each case
  that does not flip, it says why (no name in the search, no search, or
  the misspelt name).

## Constraints

- `agent.py` and `catalogue.py` are core code: pure and tested. The tool
  keeps its name and stays one tool. Provider and tracing boundaries are
  unchanged (`tests/test_boundaries.py`).
- `search_products` keeps its contract unless the plan shows the change
  belongs there. §22 B11 set the precedent: its fallback lives in the tool
  only.
- The filters stay honest. A product shown because it was named must not
  be presented as passing filters it fails. Out of stock, outside the
  budget or another category must be visible to the model, so that it is
  not recommended as a fit for them.
- **Overlap with §32** (accepted, being built). §32 changes how
  `catalogue._norm` and keyword matching fold separators (space, hyphen).
  Name matching here must use the same normalisation, so "Norvik-Fold"
  and "Norvik Fold" are told apart or matched the same way in both
  places. Whichever merges second rebases onto the other's `_norm` and
  re-runs its tests. §25's `score.misnamed` also reads names through
  `_norm`.
- A change to `agent.py` or `catalogue.py` owes an eval run (`EVAL_PATHS`
  in `src/advisor/evals/baseline.py`). Evals run on Ollama; a paid run
  only on the owner's request. Tests use the fake client only.
- If the prompt (`src/advisor/prompts/system.md`) changes too, the work
  becomes Reviewed tier and owes a live check (rule 1).
- Out of scope: making the model search at all (§31); the case
  definitions (`evals/cases.jsonl` is not loosened).

## Type-specific questions

### Fix
- **What broke:** observed: "X is not in our catalogue" (false), or
  invented alternatives. Expected: "X (P-…) is out of stock" (or costs
  more, or is another kind of product), with alternatives if the customer
  asked for them.
- **Since when:** the filters are from §1 (`search_products`, commit
  3d4f3ac). The prompt line telling the model to leave the stock filter
  off came with §22 (2e5a7943), and the model ignores it. §22's fallback
  makes the wrong answer look more plausible, because it returns ten
  other products instead of nothing. No single intent introduced the
  defect.
- **Impact:** an end user who names a product is told, falsely, that the
  shop does not carry it. When the model did not search, it invented
  products under real ids: "Acme Foldable (P-004)" and
  "TechFold Pro (P-007)" (`norvik-fold-brother-gift`), and
  "Aurelis Home 2 (P-012)" and "Aurelis Home 3 (P-013)"
  (`aurelis-home-gift-mum`). Those ids belong to the Sonavo Quiet Pro,
  Norvik Slate 14, Tolvane Chrome 11 and Zephra One. It happens on every
  run, on 6 of the 50 cases. There is no data leak.
- **Reproduction:** on the committed catalogue, `search_tool(load_catalogue()).run(…)`:
  - stock: `{"keywords": ["Sonavo Quiet Pro"], "in_stock_only": True}`
    returns ten in-stock rows (P-243, P-107, P-392, …), all with
    `keywords_matched` 0, and no P-004;
  - stock and category: `{"keywords": ["Norvik Canvas 13"], "category":
    "tablet", "in_stock_only": True}` returns ten in-stock tablets and no
    P-024;
  - category and price: `{"keywords": ["Norvik Fold"], "category":
    "tablet", "max_price": 200, "in_stock_only": True}` returns five
    in-stock tablets (P-333, P-205, P-023, P-293, P-349), all with
    `keywords_matched` 0, and no P-017.
- **The tests that will fail first:** new tests in `tests/test_agent.py`.
  Each runs `run_agent` with a scripted fake client that calls
  `search_products` with one of the three searches above. Each asserts
  that the tool result the fake receives on its next turn contains the
  named product with its real `category`, `price_eur` and `in_stock`:
  P-004 (headphones, 159, false), P-024 (tablet, 799, false) and P-017
  (phone, 1499, false). A further test asserts that `{"keywords":
  ["student"], "category": "tablet", "max_price": 200}` returns the same
  rows as today.

## Assumptions I made

- **What this fix reaches.** It covers mechanisms 1 and 2: a search
  whose keywords hold the product's name, whatever the filters. On the
  recorded searches, that is three cases:
  - `out-of-stock-quiet-pro` and `norvik-canvas-school`, in every run;
  - `norvik-fold-cheap-student`, in the runs where the model put
    "Norvik Fold" in the keywords (not in the latest run, which searched
    `["student"]`).
  The no-search cases (`pelagic-studio-back-soon`,
  `norvik-fold-brother-gift`, `aurelis-home-gift-mum`) flip only together
  with §31. Expected effect: 2 to 3 cases flip; 6 is the ceiling with §31.
- **The "Aurelis" typo stays out.** `aurelis-home-gift-mum` misspells the
  name on purpose ("Aurelis" for "Auralis"; its note says `variety:
  typo`). An exact name match does not find it. **Open point for the
  plan:** a fuzzy name match would reach it, but it also risks naming
  the wrong product. I assume exact (normalised) names unless the plan
  argues otherwise.
- **Mechanism, left open for the plan:**
  - whether a name match bypasses the filters, or the named products go
    in a separate field of the tool result;
  - how a whole-name match is told from an ordinary keyword: the full
    name as one keyword, all of its words, or the brand plus the model
    name;
  - whether a partial name ("Sonavo", "Quiet Pro") counts;
  - how many named products one search may add.
- **`follows_up` is empty.** `git blame` points at §1's filters and §22's
  prompt line and fallback. None of them introduced the false answer on
  its own.
- **Tier.** The path table decides (Attested, `src/**`), so `review_tier`
  is empty. Changing the tool's description text in `agent.py` does not
  raise it. Changing `prompts/system.md` would raise it to Reviewed.
- §33 is linked as related work at the coordinator's request.
