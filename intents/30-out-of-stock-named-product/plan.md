<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §30 plan — A named out-of-stock product is answered as "not in our catalogue"

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

When a `search_products` call's keywords contain a catalogue product's full
name, and the category, price or stock filters drop that product, the tool
result still carries it: an extra row at the end with its real fields and a
`filters_failed` list naming the filters it does not pass. The model can then
say "the Norvik Fold (P-017) is a €1499 phone and is out of stock" instead of
"not in our catalogue", and the marker keeps the row from being offered as a
fit. Searches that name no product, and every row that passes the filters,
are unchanged. The mechanism lives in the tool and in one pure helper in
`catalogue.py`; `search_products` keeps its contract (§22 B11 precedent). No
prompt change: the tool description tells the model what the field means.

## Risks

- **Tests that pass whatever the code does.** A test that only checks "P-004
  is in the result" passes if the filters were removed altogether. Each test
  also asserts the filter-passing rows, and that a passing named product is
  not duplicated.
- **A dishonest row.** A named row without `filters_failed`, or with it empty
  when a filter fails, would be read as a fit. Tests assert the exact list per
  filter.
- **Name match too loose.** A partial name ("Sonavo", "Quiet Pro", a brand)
  would add rows on ordinary searches. Exact full-name equality only; a test
  with a brand keyword and a name-substring keyword asserts no row is added.
- **Normalisation drift with §32.** §32 (not on main) changes how keywords are
  folded (`catalogue.fold`, separators). The match must go through
  `keyword_set`, not through a copy of `_norm`, so it follows whichever
  normalisation is on main. If §32 merges first, re-run subtask 1's tests; the
  "Norvik-Fold" test's expectation is the one to re-check.
- **Result size.** Extra rows add tokens. Capped by the number of distinct
  keywords naming a product and at most `MAX_LIMIT` (10).
- **Stale line citations.** §31 (`run_agent`) and §33 (`prompts/system.md`)
  are in flight; `agent.py:170-188` and prompt lines will drift.
- **Eval noise.** Model answers vary; a flipped case is re-run with
  `--only` before it is called a flip or a regression (REVIEW-POLICY "Eval
  runs").

## Verified against the codebase

Re-read on `main` at `ac69f5b`.

- `src/advisor/agent.py:57-75` — `_SEARCH_SCHEMA`: properties `category`,
  `min_price`, `max_price`, `keywords`, `in_stock_only`, `limit`;
  `additionalProperties: False`. No schema change is planned.
- `src/advisor/agent.py:87-97` — `_product_json`: id, name, brand, category,
  price_eur, in_stock, specs, description.
- `src/advisor/agent.py:100-150` — `search_tool` and its `run`. `:123-129`
  builds `filters` (category, min_price, max_price, in_stock_only, limit);
  `:130` `words = keyword_set(keywords)`; `:131` `search_products(...)`;
  `:132-133` no words returns plain rows; `:136-137` the B11 fallback when
  nothing matched; `:138` the return with `keywords_matched`. The change goes
  between `:137` and `:138`.
- `src/advisor/agent.py:140-149` — the `ToolSpec` description text, which says
  the filters "must all hold" and describes `keywords_matched`. It gets one
  sentence for `filters_failed`.
- `src/advisor/agent.py:153-167` — `_execute`: `json.dumps(results)` is what the
  model receives and the same `results` go to `tracer.tool`, so the extra rows
  reach both.
- `src/advisor/catalogue.py:109-110` — `_norm`: lower-case, hyphen to space.
- `src/advisor/catalogue.py:113-115` — `keyword_set`: distinct, normalised,
  non-blank keywords.
- `src/advisor/catalogue.py:118-124` — `keywords_matched(product, words)`.
- `src/advisor/catalogue.py:127-164` — `search_products`; `passes` at `:147-156`
  holds the four filter tests (category, min_price, max_price, in_stock_only).
  The new helper repeats that logic as a list of failed filter names; a test
  ties the two together (subtask 1).
- `src/advisor/catalogue.py:29-30`, `:15-24` — `CATEGORIES`; fields.
- `src/advisor/data/catalogue.json` — 500 products, names unique (checked on
  main); P-004 "Sonavo Quiet Pro" headphones 159 out of stock, P-017 "Norvik
  Fold" phone 1499 out, P-024 "Norvik Canvas 13" tablet 799 out, P-010 "Pelagic
  Studio 15", P-032 "Auralis Home 1" out. Some names occur inside other names,
  so only equality is safe.
- `tests/test_agent.py:25-45` — `CAT`, `call`, `final`, `tool_results_sent`;
  `:387-393` `_rows(args, catalogue)` helper over the scripted fake;
  `:373-383` an existing committed-catalogue test to copy the pattern from;
  `:397-451` the B11 tests that must stay green; `:345-353` the description
  tests.
- `tests/test_catalogue.py` — catalogue tests live here.
- `src/advisor/evals/baseline.py:15-26` — `EVAL_PATHS` includes `agent.py` and
  `catalogue.py`: an eval run is owed.
- `src/advisor/prompts/system.md:12-14` — the "Set `in_stock_only` only when…"
  line; not touched.
- `REVIEW-POLICY.md:70-98` — live checks: rule 1 lists `cli.py`, `models/`,
  `tracing.py`, `prompts/`, `infra/`. None is touched here.
- `evals/runs/20261124T215703Z-ollama.json` — latest qwen3:8b run the intent
  quotes; the six cases and their searches are as the intent states (not
  re-derived here; the reproduction in the intent is re-run in subtask 2).

## Subtasks

1. **Pure helpers in `catalogue.py`.** `failed_filters(product, category,
   min_price, max_price, in_stock_only) -> list[str]`, returning the names
   `"category"`, `"min_price"`, `"max_price"`, `"in_stock_only"` that the
   product does not pass, in that order. `named_products(catalogue, keywords)
   -> list[Product]`: products whose name, normalised through `keyword_set`
   (`keyword_set([p.name])`), equals one of `keyword_set(keywords)`; catalogue
   order, at most `MAX_LIMIT`. Tests first (catalogue tests). Commit.
2. **The tool adds the named rows.** In `search_tool.run`, with words present,
   after the B11 fallback: for each product in `named_products` that is not
   already in `found` and fails at least one filter, append
   `{**_product_json(p), "keywords_matched": keywords_matched(p, words),
   "filters_failed": failed_filters(...)}` after the filter-passing rows.
   These rows do not count towards `limit`. A named product that passes all
   filters is already in `found` (or was cut by `limit`; see Assumptions) and
   is not added. Failing-first tests in `tests/test_agent.py` (below). Commit.
3. **Tool description.** One sentence in the `ToolSpec` description (agent.py
   only, no prompt): a row with `filters_failed` is a product the customer
   named that fails the listed filters; say so and do not present it as a fit.
   A test asserts the sentence. Commit.
4. **Docs.** `CLAUDE.md` architecture line for `agent.py`/`catalogue.py`
   (named rows, `filters_failed`) and `README.md` where it describes the
   search tool. Commit.
5. **Hand-over.** `npm run verify` green, `npm run check:intent` PASS,
   `status: in-review`, a Progress entry with commits and test counts. The
   eval run is made by the coordinator (Ollama), not by the implementer.

Subtask 1 is committable alone (new helpers, tested, unused); 2 and 3 each
leave verify green.

## Tests

Failing-first (they fail on main, which returns no P-004, P-024 or P-017):
in `tests/test_agent.py`, over `load_catalogue()` through `_rows`:

- **Stock** — `{"keywords": ["Sonavo Quiet Pro"], "in_stock_only": True}`:
  the last row is P-004 with `category` "headphones", `price_eur` 159,
  `in_stock` false, `filters_failed == ["in_stock_only"]`,
  `keywords_matched` 1; the rows before it are the B11 fallback rows
  (`keywords_matched` 0, all in stock, no `filters_failed` key).
- **Stock and category** — `{"keywords": ["Norvik Canvas 13"], "category":
  "tablet", "in_stock_only": True}`: P-024 appended, `["in_stock_only"]`
  (it is a tablet, so category passes).
- **Category and price** — `{"keywords": ["Norvik Fold"], "category":
  "tablet", "max_price": 200, "in_stock_only": True}`: P-017 appended,
  `["category", "max_price", "in_stock_only"]`; and a `min_price` variant
  (`"min_price": 100`, category "tablet") gives `["category", "in_stock_only"]`
  (1499 passes a minimum of 100).
- **Unchanged searches** — `{"keywords": ["student"], "category": "tablet",
  "max_price": 200}` returns the same rows as before (compare to
  `search_products` plus `keywords_matched`), none with `filters_failed`;
  existing B11 tests stay green unmodified.

Edge and negative paths (`tests/test_agent.py`, with small fixtures from `CAT`
where the committed data would obscure the point):

- A named product that passes every filter is returned once, with no
  `filters_failed` key (kills "append every named product").
- A brand keyword ("Norvik") and a partial name ("Quiet Pro") add no row
  (kills partial matching).
- Case and hyphen variants: "norvik fold" and "Norvik-Fold" both add P-017
  (go through `keyword_set`). After §32, re-check this test's expectation.
- Two names in one search add two rows, once each; the same name twice adds
  one row.
- No keywords, or blank keywords: no named rows (kills the missing `if words`
  guard); `limit` does not cut or count named rows (`limit: 1` returns one
  filter row plus the named row).
- The tracer receives the same rows as the model, named rows included
  (`RecordingTracer`; extends the existing tracer test pattern at `:281`).
- Description text contains the `filters_failed` sentence (kills dropping
  subtask 3).

Pure helpers (`tests/test_catalogue.py`):

- `failed_filters` returns each filter name alone and in combination, boundary
  prices (equal to min or max passes), and `[]` when all pass. A consistency
  test over the committed catalogue: for several filter combinations,
  `p` is in `search_products(..., keywords=None, limit=10)` exactly when
  `failed_filters(p, ...) == []` (ties the new code to `passes`; kills drift
  between the two).
- `named_products`: exact name only; case and hyphen insensitive; empty and
  blank keywords give `[]`; catalogue order; capped at `MAX_LIMIT`.

Mutation map: dropping the filter in `failed_filters` fails the per-filter
tests; always appending fails "passes every filter returned once"; substring
match fails the brand and partial tests; removing the `not in found` check
fails the once-only tests; counting named rows in `limit` fails the limit
test.

No test calls a model or the network; the fake `ModelClient` only
(`tests/conftest.py`).

## Validation

- `npm run verify` green
- `npm run check:intent` PASS (or ROUTE with a reason recorded in review.md)
- Eval run owed (`agent.py`, `catalogue.py` are in `EVAL_PATHS`): the
  coordinator runs `uv run advisor-eval` on Ollama in the worktree at the
  reviewed commit, then `advisor-analysis hashes` and `compare`. The review
  names which of `out-of-stock-quiet-pro`, `norvik-canvas-school` and
  `norvik-fold-cheap-student` flip, and for `pelagic-studio-back-soon`,
  `norvik-fold-brother-gift` and `aurelis-home-gift-mum` says why not (no
  search, §31; the misspelt "Aurelis"). Flipped-then-failed cases re-run with
  `--only`.
- Live check: none owed by path. `src/advisor/agent.py`,
  `src/advisor/catalogue.py`, `README.md` and `CLAUDE.md` are not in
  `REVIEW-POLICY.md` rule 1; no prompt, hook or adapter changes (rules 2
  and 3 do not apply). If the prompt changes later, this plan stops and is
  re-approved: it becomes Reviewed tier and owes one.

## Assumptions I made

- **Mechanism (within the intent's outcome).** Extra rows appended to the same
  list, not a separate field: `search_tool` returns one list (`Tool.run`'s
  type), and the outcome says the rows that pass the filters still pass them
  all, which holds; the appended rows are marked by `filters_failed`, which is
  how the intent's "must be visible to the model" is met. The coordinator should
  confirm this reading.
- **Name match is exact and full.** A keyword equals the product's whole name
  after the same normalisation as keyword matching. Partial names, brands, and
  a name split into separate keywords ("Norvik", "Fold") do not count; that is
  a known miss, and the misspelt "Aurelis Home 1" is not reached (the intent's
  assumption). A fuzzy match would risk naming the wrong product.
- **Cap.** At most one row per distinct named product, at most 10 rows, not
  counted in `limit`.
- **A named product cut by `limit`** (it passes all filters but ranks below the
  limit) is not added: that case is not "dropped by the filters", and the
  ordering already puts a name match first (a name keyword matches at least
  once, usually more than other rows). A test over the committed data checks a
  full-name search with `limit: 1` returns the product first.
- No new dependency. No change to `search_products`, the schema or the prompt.
- Line numbers above are for `ac69f5b`; §31, §32 and §33 may move them. Parts
  that depend on §32: the normalisation of names (kept independent by going
  through `keyword_set`), and the "Norvik-Fold" test.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-25 — implementation (subtasks 1-5)

Commits: the first commit of the branch (helpers, tool change, description,
docs, tests) and a second that fixes one test and records this entry (hashes
in `git log`). `npm run verify`: 955 passed (kit tests, ruff, mypy green).

Shipped: `failed_filters` and `named_products` in `catalogue.py`
(`search_products.passes` now calls `failed_filters`, one source of the four
tests); `search_tool.run` appends each named product that fails a filter and
is not already in the rows, with `keywords_matched` and `filters_failed`,
outside `limit`; one tool-description sentence; `CLAUDE.md` and `README.md`
lines. New tests: 5 in `tests/test_catalogue.py`, 12 in `tests/test_agent.py`.
No prompt change, no new dependency. No eval run (the coordinator's).

Divergences:
- §32 is on main: `named_products` compares `fold(p.name)` with
  `keyword_set(keywords)` (both folded), not `keyword_set([p.name])`; same
  result. Under fold, "NorvikFold" also matches P-017; the Norvik-Fold test
  covers "norvik fold", "Norvik-Fold", "NORVIK FOLD" and "NorvikFold". The
  result shape, exact-name rule and `limit` handling are as planned.
- The "unchanged search" test: `{"keywords": ["student"], "category":
  "tablet", "max_price": 200}` matches no row, so the expected rows are the
  B11 fallback rows (the plan's "compare to `search_products`" gives `[]` for
  that search); the test compares to the filter-only search.

### 2026-11-25 — rework, review round 1

Owner decision (a): a named product that passes every filter but is cut by
`limit` is not appended (the plan's behaviour). No behaviour change.

Shipped: two tests in `tests/test_agent.py`,
`test_named_product_failing_only_min_price_is_appended` and
`test_named_product_passing_every_filter_but_cut_by_limit_is_not_appended`
(pins the decision: 10 rows, no P-017, no `filters_failed`); a one-line
comment on the defensive `shown` guard in `agent.py`.

Count correction: the earlier entry's "12" is wrong. The first round added 13
tests to `tests/test_agent.py` and 5 to `tests/test_catalogue.py`; this rework
adds 2 more to `tests/test_agent.py` (15 in all). Suite: 957 passed.

Mutants (agent.py backed up by copy, restored by copy):
- `filters["min_price"]` -> `None`: killed by the min_price test (1 failed).
- `if failed and p.id not in shown` -> `if p.id not in shown`: killed by the
  limit test (1 failed).

### 2026-11-25 — merge main (§31, §32)

`git merge main` conflicted only in the import block of `tests/test_agent.py`
(§30 imported `keyword_set`, `keywords_matched`; §31 added `Message`). Kept
both. `agent.py` merged cleanly: the §30 named-row append and §31's
`searched`/`asked` loop are both intact. No test needed adapting. 965 passed.
