<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §22 plan — Product search that still finds the right product in 500

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Make `search_products` match a product when any keyword appears, and rank
by the number of distinct keywords matched, then price, then id, so the
product a customer's distinguishing words point to comes first instead of
being cut by "cheapest five". The tool returns 10 by default, its schema
and the system prompt say how keywords now work, and §13's consistency
check ranks the same way, so `student-laptop` and `nc-headphones-under-200`
pass again on the 500-product catalogue (B10) without new regressions.

## Risks

- **The prompt is the Reviewed tier and owes a live check** (rule 1,
  `src/advisor/prompts/`); B7 is one sentence, and the measured outcome
  (B10) is the owner's three-run majority, not a single run.
- **Two copies of the ranking.** `search_products` and `_expected_results`
  must order identically (B8); a test compares them on every committed
  case (AC7), so they cannot drift.
- **§15 edits the same function** (`_expected_results`, which §15 splits
  into a shared `fits` filter plus the ordering). Neither blocks the other;
  whichever merges second rebases. §22 changes only the ordering key and the
  keyword rule inside the filter.
- **Coverage probes change meaning** (spec Assumptions): `coverage._count`
  calls `search_products`, so a probe with several keywords now matches
  more. A `no-match` or `budget-too-low` probe with two or more keywords may
  stop being one. The committed `evals/generated.jsonl` is not regenerated;
  probe tests are kept green or updated to the new rule. If §15 merges
  first, its probe test (`check_coverage` on each new case) runs under the
  new rule: a §15 case it breaks is reported, and fixed here only if the
  test fails (B9's rule applied to it).
- **Tests that pass whatever the code does.** Every ordering test uses a
  fixture where count order, price order and id order disagree, so a
  mutant that drops one key fails.
- **The eval run** (§17): `catalogue.py`, `agent.py` and the prompt are eval
  paths; the review makes one Ollama run and compares it with the
  baseline; flipped cases are re-run once before being called regressions.
  B10's three-run majority is the owner's live check.
- **Stale line citations**: every `path:line` below was re-read at
  `bbb48a1`; the implementer re-checks before editing.
- **Repository footguns** (`REVIEW-POLICY.md` pass 9): the list is empty.

## Verified against the codebase

Re-read on `main` at `bbb48a1`.

- `src/advisor/catalogue.py:27` — `MAX_LIMIT = 10` (and `MIN_LIMIT = 1` above it).
- `src/advisor/catalogue.py:109-110` — `_norm`: lower case, hyphen to space.
- `src/advisor/catalogue.py:113-143` — `search_products(catalogue, category, min_price, max_price, keywords, in_stock_only, limit=5)`; docstring `:122-127` ("Keywords all have to appear"); `words` at `:129` drops blank keywords; `matches` `:131-141` ends `return all(w in haystack for w in words)`; order `:143` `sorted(..., key=lambda p: (p.price_eur, p.id))[:limit]`.
- `src/advisor/agent.py:51-66` — `_SEARCH_SCHEMA`; `keywords` description `:60` "Words that must all appear in the name, brand or description."; `limit` `:63` "Maximum results, 1 to 10 (default 5).".
- `src/advisor/agent.py:109` — `limit = args.get("limit", 5)`; `:112-120` the `search_products` call.
- `src/advisor/prompts/system.md:6-8` — "Use the `search_products` tool to look products up. Call it with the category, price range, keywords and stock filter that match what the customer asked for. You may call it more than once."
- `src/advisor/evals/cases.py:169-191` — `_expected_results`: `keywords_any` any-of (`:182-188`), ordered `(price_eur, id)` (`:191`); `catalogue_problems` `:194-221` ranks against `MAX_LIMIT`.
- `src/advisor/evals/coverage.py:110-120` — `_count` calls `search_products(..., keywords=list(probe.keywords), limit=10)`.
- `docs/decisions/0003-catalogue-changes.md:22-23` — "An expected product must be matched by the case's filters and rank within the first 10 results".
- `tests/test_catalogue.py:167-172` — `test_keywords_case_insensitive_all_must_match` (`["noise", "alpha"]` → `[]`), replaced by B2/B3 tests; `:199-224` hyphen and blank-keyword tests, kept.
- `tests/test_agent.py:64`, `:204`, `:209` — tool argument and `limit` tests.
- `tests/test_evals_consistency.py` — `test_order_is_by_price_not_by_id`, `test_ties_are_broken_by_id`: still hold for cases without keywords.
- `tests/test_analysis_coverage.py:34, :75-89` — probe counts and spelling-differs tests.
- `src/advisor/evals/baseline.py` `EVAL_PATHS` — includes `src/advisor/prompts/`, `agent.py`, `catalogue.py`: the review owes an eval run.

## Subtasks

1. **Matching and order (B1–B4, AC1–AC3).** In `search_products`: the
   non-keyword filters unchanged; with keywords, a product matches when at
   least one distinct normalised keyword is in its haystack; order by
   (−matched count, price, id); without keywords, price then id; `limit`
   clamped as today, default stays 5. Docstring rewritten. Comments at the
   match ("any keyword: OR, precision comes back through the ranking", the
   tv-sound example) and at the scorer ("a keyword counts once however
   often it appears; duplicates count once after normalising"). Tests
   first; replace `test_keywords_case_insensitive_all_must_match`. Commit.
2. **The tool (B5, B6, AC5).** `limit = args.get("limit", 10)` with a
   comment ("the function keeps 5 for its other callers; the tool defaults
   to 10", spec Interpretations); schema `keywords`: any keyword can match,
   products matching more keywords come first; `limit`: "1 to 10 (default
   10)". Name, arguments and result rows unchanged. Tests first. Commit.
3. **The consistency check (B8, AC7).** `_expected_results` orders like
   `search_products`: (−distinct `keywords_any` matched, price, id); its
   filter unchanged (any-of already). Update ADR 0003's wording ("rank
   within the first 10 results, ordered as `search_products` orders them:
   keywords matched, then price, then id"). Test: for every committed case
   with `expect_search`, `_expected_results(case.expect_search)[:10]`
   equals `search_products` with the same arguments
   (`keywords_any`→`keywords`, `limit=10`). Commit.
4. **Coverage and the committed cases (B9).** Run the full suite; fix any
   probe or coverage test the new rule breaks by updating it to the new
   rule (no change to `coverage.py`'s logic beyond what `search_products`
   now does); `catalogue_problems` on the committed cases stays empty, and
   a case is changed only if the check fails (listed in Progress). Commit.
5. **The prompt (B7, AC6).** One sentence added to the search rule in
   `src/advisor/prompts/system.md`: put the words that distinguish what the
   customer wants (a use such as "student" or "running", a feature such as
   "noise-cancelling") into `keywords`; extra keywords no longer empty a
   search. No other change. A test asserts the sentence is in the committed
   file. Commit.
6. **Real data (AC4).** A fake-free test over the committed catalogue:
   `search_products(category="laptop", max_price=700,
   keywords=["student"])[0].id == "P-009"`; the tool called with
   `{category: laptop, max_price: 700}` and no limit returns 10 products
   including P-009. Commit.
7. **Docs.** `CLAUDE.md` (the `catalogue.py` line: "AND of filters …
   keywords case-insensitive" → any keyword, ranked by keywords matched,
   then price, then id) and README where it describes the search. Commit.
8. **Hand-over.** `npm run verify` green, `npm run check:intent` PASS,
   `status: in-review`, a Progress entry: commits, test counts, any case or
   probe changed in subtask 4 and why.

## Tests

- **B2/AC1** (`tests/test_catalogue.py`): one of two keywords is enough;
  none excludes; blank keywords ignored (`["-"]`, `["--", "noise"]` keep
  their meaning); hyphen as space both ways. Mutants: `any`→`all`, dropping
  the blank filter.
- **B3/AC2**: two keywords, a product matching both ranks above a cheaper
  one matching one; equal counts fall back to price, then id (a fixture
  with a price tie); duplicate and differently-hyphenated keywords count
  once (`["noise", "NOISE"]`, `["in-ear", "in ear"]`); no keywords keeps
  price then id. Mutants: dropping the count key, reversing it, counting
  occurrences instead of distinct words, dropping the id tie-break.
- **B1, B4/AC3**: each non-keyword filter still excludes with keywords
  present; `limit` clamps at 1 and 10 and cuts the ordered list (the
  match-count leader survives a `limit=1`). Existing tests kept.
- **B5, B6/AC5** (`tests/test_agent.py`): a call with no `limit` reaches
  `search_products` with 10 (and returns up to 10); an explicit `limit` is
  passed through; the schema text says any keyword matches and "(default
  10)". Mutant: default 5.
- **B8/AC7** (`tests/test_evals_consistency.py`): a keyword case where
  count order and price order disagree ranks as `search_products` does;
  plus the committed-file comparison of subtask 3. Mutant: dropping the
  count key from `_expected_results`.
- **AC4**: the real-catalogue test of subtask 6.
- **AC6**: the prompt sentence test.
- No model call; the suite stays offline (`tests/conftest.py`).

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (FAIL only on the owed live check until it is
  recorded).
- **Eval run** (§17, owed: `src/advisor/prompts/`, `agent.py`,
  `catalogue.py`): the coordinator's Ollama run in the worktree at the
  reviewed commit, compared with `evals/baseline.json`; a flipped case is
  re-run with `--only` before it is a regression.
- **Live check** (owed, rule 1, the prompt; AC8): before the merge, the
  owner runs `uv run advisor-eval --provider ollama` three times on `main`
  and three times in the worktree, compares per case by majority
  (`student-laptop` and `nc-headphones-under-200` pass in at least 2 of 3;
  no case passing in at least 2 of 3 on `main` fails in at least 2 of 3
  here), and the review names the six reports.

## Assumptions I made

- **Ordering key** `(-matched, price_eur, id)`; "matched" is the number of
  distinct normalised keywords found, blank ones dropped first.
- **Duplicates** are counted after `_norm`, so `"noise-cancelling"` and
  `"noise cancelling"` are one keyword.
- **`_expected_results` uses `keywords_any` as the keyword list** for the
  ranking, so the AC7 comparison maps `keywords_any` → `keywords`.
- **Coverage keeps calling `search_products`** (spec Assumptions); a probe
  whose meaning changes is reported, not re-classified.
- **§15 ordering**: if §15 merges first, the rebase keeps §15's `fits`
  filter and applies this ordering key after it.
- **Tier: Reviewed** (`review_tier: reviewed`, the prompt).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-21 — build (subtasks 1-8)

Commits: e3410f5 (matching and order), 669023c (tool default 10, schema),
3353f83 (`_expected_results`, ADR 0003), 04baa3e (prompt sentence, AC4 test),
07bc3f9 (README, CLAUDE.md), e9a9170, 7e16fee, 8e1bd49 (format, one more
mutant-killing test, lint), plus the hand-over commit.

Shipped: `search_products` matches any keyword and orders by (distinct
keywords matched desc, price, id), default limit still 5; the tool defaults to
10 and its keywords/limit schema text and its description changed;
`_expected_results` orders the same way; ADR 0003 wording; one sentence in the
prompt's search rule; AC4 real-catalogue test; docs.

Tests: 804 passed in the full pytest run before the last additions; the suite
grew by about 20 tests (catalogue, agent, consistency); `npm run verify` and
`check:intent` outputs are in the hand-over report.

Cases and probes changed: none. The full suite was green after subtask 1-3
with no change to any coverage probe test, `coverage.py`, or
`evals/cases.jsonl`; `catalogue_problems` on the committed cases is empty.

Mutants (all restored by copy; the killing tests):
- drop the count key / reverse it: `test_more_keywords_matched_ranks_first_then_price_then_id`, `test_a_keyword_counts_once_however_often_it_appears`, `test_limit_cuts_the_ranked_list_and_keeps_the_leader`, the tool ranking test.
- any -> all: `test_keywords_case_insensitive_any_may_match` and the ranking tests.
- drop the id tie-break: `test_no_filters_sorted_price_then_id`, the ranking test, the consistency ranking test.
- count occurrences: `test_a_keyword_counts_once_however_often_it_appears`.
- drop the blank filter: `test_blank_keywords_do_not_match_everything_or_count`.
- tool default 5: `test_tool_default_limit_is_ten_...`, `test_committed_catalogue_student_laptop_under_700_finds_p009`.
- `_expected_results` without the count key: the consistency ranking test and the committed-case comparison.
- no de-duplication of keywords: first SURVIVED; `test_repeated_keyword_is_not_a_bigger_match_than_distinct_ones` was added and kills it.

Divergences: the tool's `description` text ("All given filters must match.
Sorted by price") was stale under the new rule, so it was updated too. No
other divergence.

Assumptions: ordering key and de-duplication as in the plan; blank-only
`keywords_any` is not specially handled in `_expected_results` (an empty or
blank list excludes everything there, where `search_products` would match all;
no committed case has one); the prompt test compares whitespace-normalised
text; live check and eval runs are the coordinator's and owner's.

### 2026-11-21 — rework after review round 1

Commits: the `§22: round-1 rework tests (F1-F3), F4 prompt wording` commit, then this Progress entry.

- F1: brand-only assertion (`keywords=["quiet"]` gives `["P-004"]`) in `test_keywords_case_insensitive_any_may_match`.
- F2: two consistency tests in `tests/test_evals_consistency.py` (distinct count not occurrences; spelling variants de-duplicated), each comparing ids and equality with `search_products(..., limit=10)`.
- F3: `_expected_results` now `if words and matched(p) == 0: return False`; test with `["-"]` and `["-", "alpha"]` against `search_products`.
- F4 (a), the owner's decision "22: F4 a", outside the plan's subtasks: `src/advisor/evals/prompts/generate.md` now describes a probe's `"keywords"` as any-of, and a no-match probe must match none; a new test pins the sentence (no test pinned the old one).
- F5: no change (owner's diff read).
- F6 correction: +14 tests (one replaced); 807 passed at 38e0c83.

Mutants (each run on the full suite, restored by copy, tree clean after):
- M13 (brand dropped from the haystack): killed by `test_keywords_case_insensitive_any_may_match`.
- C2 (no dedup in `_expected_results`): killed by `test_expected_results_deduplicates_spelling_variants`.
- C6 (count occurrences): killed by `test_expected_results_counts_distinct_keywords_not_occurrences`.
- C3 (no `words and` guard): killed by `test_expected_results_blank_only_words_match_like_search_products`.

Tests: 811 passed in the full pytest run (four added by this rework).

### Round 2 rework (F8, owner's option c), 2026-11-21

Commit 2e5a794. Added to the search rule in `src/advisor/prompts/system.md`: "Set `in_stock_only` only when the customer asks for products in stock; otherwise leave it off, so an out-of-stock match can still be named and flagged." Tool description in `agent.py` unchanged. Test first: `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked` failed before the edit, passed after. Mutant (sentence deleted): killed by that test (1 failed, 811 passed); restored by copy. Tests: 812 passed in verify. No eval run (no model calls); the owed re-run is the coordinator's.
