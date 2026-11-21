<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §22 spec — Product search that still finds the right product in 500

Accepted intent: [intent.md](intent.md)

Written against `main` at `1a38b99`.

## Owner's decisions (question round, 2026-11-16)

- **Ranking:** "Any keyword, rank by matches": a product matches when any
  keyword appears; results are ranked by the number of keywords matched,
  then price, then id.
- **Limit:** "Raise to 10": the tool's default `limit` becomes 10.
- **Prompt:** "Yes, one line": the system prompt tells the model to put
  the question's distinguishing words into `keywords`.
- **Measure:** "3 runs, majority": three `advisor-eval` runs on Ollama.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/22-search-that-scales/intent.md` | the problem, measured at §14's live check: 11/15 on `main` (32 products) → 9/15 on 500; `student-laptop` (P-009 ranks 10th of the cheapest-first `{laptop, max_price 700}`) and `nc-headphones-under-200` (P-001 not among the five cheapest) |
| `src/advisor/catalogue.py:113-142` (`search_products`) | today: AND of filters, "Keywords all have to appear", order `(price_eur, id)`, `limit` default 5 clamped to `MIN_LIMIT..MAX_LIMIT` (1..10); a hyphen counts as a space (§7) |
| `src/advisor/agent.py:51-66, 109` (`_SEARCH_SCHEMA`, the tool) | `keywords`: "Words that must all appear in the name, brand or description."; `limit`: "Maximum results, 1 to 10 (default 5)."; `limit = args.get("limit", 5)` |
| `src/advisor/prompts/system.md` | "Call it with the category, price range, keywords and stock filter that match what the customer asked for." |
| `src/advisor/evals/cases.py:169-191` (`_expected_results`) and `docs/decisions/0003-catalogue-changes.md` | §13's consistency check re-implements the search: "An expected product must be matched by the case's filters and rank within the first 10 results", ranked `(price_eur, id)`, keywords all-of |
| `src/advisor/evals/coverage.py` | §9's question grid probes the catalogue through `search_products` to keep a generated question |
| `REVIEW-POLICY.md` → "Live checks" rule 1 | `src/advisor/prompts/` owes a live check; it is Reviewed by meaning |

## Behaviour

**Matching and order** (`search_products`, core code)

- **B1.** The non-keyword filters are unchanged and all must hold:
  `category`, `min_price`, `max_price`, `in_stock_only`.
- **B2.** With keywords, a product matches when **at least one** keyword
  appears (case-insensitive, hyphen as space, in name, brand or
  description, as today). A product that matches none is not returned.
  Without keywords (or only blank ones), every product passing B1 matches.
- **B3.** Results are ordered by: the number of distinct keywords matched,
  most first; then price, cheapest first; then id. Without keywords the
  order is price then id, as today.
- **B4.** `limit` is still clamped to 1..10 and cuts the ordered list.
  The function's own default stays as the tool passes it (B5).

**The tool** (`agent.py`)

- **B5.** The tool's default `limit` is 10 when the model passes none.
- **B6.** The schema's `keywords` description says that any keyword can
  match and that products matching more keywords come first; `limit`'s
  says "1 to 10 (default 10)". The tool's name, arguments and result
  fields are unchanged.

**The prompt** (`src/advisor/prompts/system.md`, Reviewed tier)

- **B7.** One added sentence in the search rule tells the model to put the
  words that distinguish what the customer wants (a use such as "student"
  or "running", a feature such as "noise-cancelling") into `keywords`, and
  that extra keywords no longer empty a search. No other rule changes.

  **Amendment (2026-11-21, owner: "22 I choose option c", review round 2
  F8).** A second added sentence in the search rule tells the model to set
  `in_stock_only` only when the customer asks for products in stock, and
  otherwise to leave it off, so an out-of-stock match can still be named
  and flagged. AC6 also covers this line. (Round 2's eval run: every
  search set `in_stock_only`, against 6 of 12 on `main`, and
  `voice-speaker` lost its out-of-stock P-032.)

**The keyword fallback** (`agent.py`, the tool)

- **B11. Amendment (2026-11-21, owner: "22 c", then "In the tool" and "Yes,
  a field per row"; review round 4 F11).** When a tool search with
  keywords returns no rows, the tool runs the same search again without
  the keywords (the B1 filters and `limit` unchanged) and returns those
  rows. `search_products`, B2, B3, `_expected_results` and the eval's
  coverage checks are unchanged: the fallback lives in the tool only. On a
  search with keywords (non-blank), every returned row carries
  `keywords_matched`, the number of distinct keywords it matches (B3's
  count, the same function); fallback rows carry 0. This amends B6's
  "result fields unchanged" for that one field. A third added sentence in
  the prompt's search rule tells the model that a row with
  `keywords_matched` 0 does not have the features asked for, so it must
  say so rather than present it as a fit. (Round 4's eval run: the model
  added a keyword no product contains on 3 cases, `monitor-room-500`,
  `monitor-small-desk-400`, `phone-battery-all-day-400`, got 0 rows and
  cited nothing; keywords on 41 of 42 searches against 31 of 41 on
  `main`.)

**The eval consistency check** (§13, `cases.py`)

- **B8.** `_expected_results` ranks the same way as B2-B3, so "rank within
  the first 10" keeps meaning what a search can return; ADR 0003's wording
  is updated to match. `forbid_ids` still means "not matched by the
  filters" under B2.
- **B9.** The committed cases still pass `catalogue_problems` (the test in
  `verify`). A case whose `expect_search` keywords now match more widely
  is reported as before, and fixed in this change only if the check
  fails.

**Measured outcome**

- **B10.** On the committed 500-product catalogue, three `uv run
  advisor-eval --provider ollama` runs: `student-laptop` and
  `nc-headphones-under-200` each pass in at least 2 of 3; no case that
  passes in at least 2 of 3 runs on `main` (before this change) fails in at
  least 2 of 3 here.

## Interpretations

- **"Any keyword" and the old AND.** The intent's tv-sound example
  (`["soundbar", "external"]` → nothing) is the reason for OR; precision
  comes back through the ranking (B3), not through exclusion. Comment at
  the match function.
- **Counting matches.** A keyword counts once however often it appears;
  duplicate keywords count once (distinct, after normalising). Comment at
  the scorer.
- **Brand and name count like the description.** No field weighting: the
  intent asks for no new ranking signal beyond the catalogue's own text.
- **The function default (B4).** `search_products(limit=5)` keeps its
  Python default so existing callers (coverage probes, tests) do not
  change meaning; only the tool's default moves to 10. Comment at the tool.
- **"Fixed" (B10).** Majority over three runs, per the owner; a case that
  flips 1-of-3 is noise, not a regression.

## Acceptance criteria

- **AC1** (B2): any-keyword matching: a product with one of two keywords
  is returned, one with neither is not; blank keywords are ignored; hyphen
  as space still holds. (test: `tests/test_catalogue.py`)
- **AC2** (B3): ordering: two keywords, a product matching both ranks
  above a cheaper one matching one; equal counts fall back to price then
  id; no keywords keeps price then id. (test)
- **AC3** (B1, B4): non-keyword filters still exclude; the limit clamps at
  1 and 10. (test, existing ones kept green)
- **AC4** (B2-B3 on the real data): on the committed catalogue,
  `search_products(category="laptop", max_price=700, keywords=["student"])`
  returns P-009 first, and the tool called with `{category: laptop,
  max_price: 700}` and no limit returns 10 products including P-009.
  (test, fake-free: pure function over the committed file)
- **AC5** (B5, B6): the tool's default limit is 10 and its schema text
  says any keyword matches and the default is 10. (test:
  `tests/test_agent.py`)
- **AC6** (B7): the shipped prompt contains the keywords line and the
  stock line (B7 amendment). (test on the
  committed file) and the live check below.
- **AC9** (B11): a keyword search with no match returns the filter-only
  rows with `keywords_matched` 0; a search with matches returns no
  fallback rows and each row's count; a search without keywords has no
  `keywords_matched` field; the prompt contains the third sentence. (tests:
  `tests/test_agent.py`) The live check covers how the model uses it.
- **AC7** (B8, B9): `_expected_results` ranks like `search_products` for
  the same arguments (a test comparing both on the committed catalogue for
  every case's `expect_search`), and `catalogue_problems` on the committed
  cases is empty. (test)
- **AC8** (B10, live check, owed: rule 1, the prompt): the owner runs
  `uv run advisor-eval --provider ollama` three times on `main` before the
  merge and three times on the branch, and compares per case by majority.
  The review names the six reports.

## Non-functional

- **Boundaries:** matching and order in `catalogue.py` (core, pure); the
  tool default and schema text in `agent.py` (core); the prompt line in
  `prompts/system.md`; the check in `evals/cases.py` (core). No new module.
- **Data:** synthetic catalogue only; no personal data.
- **Model use:** no new call. Each search returns up to 10 products by
  default instead of 5, roughly doubling a search's tool-result tokens.
  Evals run on Ollama; a paid run only on the owner's request.
- **Autonomy:** unchanged; the agent answers only from tool results.
- **Dependencies:** none new.

## Out of scope

- Embeddings, fuzzy or stemmed matching, synonyms, field weighting.
- Telling the model which filter emptied a search (the intent's question
  5): with any-keyword matching, keywords no longer empty a search; an
  empty result now means the non-keyword filters exclude everything.
- Changing the eval cases' expectations (§15's `cites_a_match` is the
  eval-side complement), and the cases that fail for other reasons
  (`video-editing-laptop` makes no search, `out-of-stock-quiet-pro`).
- Growing or regenerating the catalogue.

## Assumptions I made

- Tier: **Reviewed**, because B7 changes `src/advisor/prompts/system.md`;
  `review_tier: reviewed` is set in `metadata.yml`.
- The prompt change changes every eval run's `prompt_sha256`. If §17 has
  merged by then, its baseline is re-taken from this change's runs at ship,
  as its policy says; if not, nothing to do.
- `coverage.py`'s probes call `search_products` directly; with any-keyword
  matching a probe may match more products, so a generated question kept
  today could change classification. The committed `evals/generated.jsonl`
  is data and is not regenerated here; the probe tests stay green or are
  updated to the new rule.
- The search result rows are unchanged (id, name, brand, price, stock,
  specs as today), so the agent's grounding checks are unaffected.
