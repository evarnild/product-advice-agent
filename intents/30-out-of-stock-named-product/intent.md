<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §30 — A named out-of-stock product is answered as "not in our catalogue"

**Type:** fix
**Originator:** the coordinator's error analysis of the qwen3:8b eval runs
of 2026-11-24, turned into an intent on the owner's "write intents"
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
| `out-of-stock-quiet-pro` | P-004 Sonavo Quiet Pro (headphones) |
| `pelagic-studio-back-soon` | P-010 Pelagic Studio 15 (laptop) |
| `norvik-fold-brother-gift` | P-017 Norvik Fold (phone) |
| `norvik-fold-cheap-student` | P-017 Norvik Fold (phone) |
| `norvik-canvas-school` | P-024 Norvik Canvas 13 (tablet) |
| `aurelis-home-gift-mum` | P-032 Auralis Home 1 (speaker) |

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
2. **Filters other than stock also exclude it.** For
   `norvik-fold-cheap-student` the model searched
   `{"keywords": ["Norvik Fold"], "category": "tablet", "max_price": 200,
   "in_stock_only": true}` (also `"category": "smartwatch"` in one run, and
   `{"keywords": ["student"], …}` in the latest). The Norvik Fold is a
   €1499 phone, so category and price drop it even without the stock
   filter. Answer: "The Norvik Fold is not in our catalogue."
3. **No search at all** (`pelagic-studio-back-soon`,
   `norvik-fold-brother-gift`, `aurelis-home-gift-mum`, every run). That
   is §31's problem, not this one's.

## Outcome

- When a keyword search with `in_stock_only: true` finds keyword matches
  only among out-of-stock products, the tool result still shows the model
  that those products exist and are out of stock (their id, name and
  `in_stock: false`). It no longer looks as if the product is missing.
- A test drives the agent with the fake `ModelClient` and the search
  `{"keywords": ["Sonavo Quiet Pro"], "in_stock_only": true}`, on the
  committed catalogue. The tool result it gets back contains P-004 with
  `in_stock` false.
- An eval run (`REVIEW-POLICY.md` → "Eval runs") is made on the change.
  Among the six cases, every one that flips is named in the review, and
  so is every one that does not flip with the reason (mechanism 2 or 3).
  At most six cases can flip, and fewer are expected (see Assumptions).

## Constraints

- `agent.py` and `catalogue.py` are core code: pure and tested. The tool
  keeps its name and stays one tool. Provider and tracing boundaries are
  unchanged (`tests/test_boundaries.py`).
- `search_products` keeps its contract unless the plan shows the change
  belongs there. §22 B11 set the precedent: its fallback lives in the tool
  only.
- A search the customer meant as "in stock only" must still not present an
  out-of-stock product as available. Showing it is fine; recommending it
  as buyable is not.
- A change to `agent.py` owes an eval run (`EVAL_PATHS` in
  `src/advisor/evals/baseline.py`). Evals run on Ollama; a paid run only
  on the owner's request. Tests use the fake client only.
- If the prompt (`src/advisor/prompts/system.md`) changes too, the work
  becomes Reviewed tier and owes a live check (rule 1).
- Out of scope: making the model search at all (§31); the case
  definitions (`evals/cases.jsonl` is not loosened).

## Type-specific questions

### Fix
- **What broke:** observed: "X is not in our catalogue" (false), or
  invented alternatives. Expected: "X (P-…) is out of stock", with in-stock
  alternatives if the customer asked for them.
- **Since when:** the stock filter is from §1 (`search_products`, commit
  3d4f3ac). The prompt line telling the model to leave it off came with
  §22 (2e5a7943), and the model ignores it. §22's fallback makes the
  wrong answer look more plausible, because it returns ten other products
  instead of nothing. No single intent introduced the defect.
- **Impact:** an end user who names a product is told, falsely, that the
  shop does not carry it. When the model did not search, it invented
  products under real ids: "Acme Foldable (P-004)" and
  "TechFold Pro (P-007)" (`norvik-fold-brother-gift`), and
  "Aurelis Home 2 (P-012)" and "Aurelis Home 3 (P-013)"
  (`aurelis-home-gift-mum`). Those ids belong to the Sonavo Quiet Pro,
  Norvik Slate 14, Tolvane Chrome 11 and Zephra One. It happens on every
  run, on 6 of the 50 cases. There is no data leak.
- **Reproduction:** `search_tool(load_catalogue()).run({"keywords":
  ["Sonavo Quiet Pro"], "in_stock_only": True})` returns ten in-stock rows
  (P-243, P-107, P-392, …), all with `keywords_matched` 0, and no P-004.
  The same happens with `{"keywords": ["Norvik Canvas 13"], "category":
  "tablet", "in_stock_only": True}`: ten in-stock tablets and no P-024.
- **The test that will fail first:** a new test in `tests/test_agent.py`.
  It runs `run_agent` with a scripted fake client that calls
  `search_products` with `{"keywords": ["Sonavo Quiet Pro"],
  "in_stock_only": true}` on the committed catalogue. It asserts that the
  tool result the fake receives on its next turn contains P-004 with
  `in_stock` false. A second test does the same for P-024 with
  `"category": "tablet"`.

## Assumptions I made

- **What this fix reaches.** It covers mechanism 1 only. On the searches
  above, that is `out-of-stock-quiet-pro` and `norvik-canvas-school`. The
  three no-search cases flip only together with §31.
  `norvik-fold-cheap-student` flips only if the named-product rows also
  ignore category and price; the plan decides whether they should.
  `aurelis-home-gift-mum` misspells the name on purpose ("Aurelis" for
  "Auralis", `"variety: typo"` in its note). A search with the question's
  spelling matches nothing even without the stock filter. So "up to 6" is
  the ceiling, not the expectation.
- **How the tool shows the product** is left to the plan: added rows,
  marked rows or a note in the result. The outcome only requires that the
  model can see it and that it is flagged as out of stock.
- **`follows_up` is empty.** `git blame` points at §1's stock filter and
  §22's prompt line and fallback. None of them introduced the false
  answer on its own.
- **Tier.** The path table decides (Attested, `src/**`), so `review_tier`
  is empty. Changing the tool's description text in `agent.py` does not
  raise it. Changing `prompts/system.md` would raise it to Reviewed.
- §33 is linked as related work at the coordinator's request. Its folder
  does not exist yet, so I could not check what it covers.
