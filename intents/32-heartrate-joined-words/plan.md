<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §32 plan — Product search treats "heartrate" and "heart-rate" as different words

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Keyword matching drops all spaces and hyphens from both the keyword and the
product text before the substring test ("full fold", the owner's decision
"32 A", 2026-11-25). So `heartrate`, `heart rate` and `heart-rate` find the
same products, in `search_products`, in `keywords_matched` (and so in the
agent tool's rows), in the case checks (`fits`, `_expected_results`,
`catalogue_problems`) and in the eval's `keywords_any` check
(`_call_satisfies`). One new pure function, `catalogue.fold`, is the single
definition of the fold, and all four sites call it. `catalogue._norm` stays
exactly as it is: `score.misnamed` (§25) reads product names through it
character by character and must keep seeing spaces.

Measured on `18a236c` (a scratch copy of the tree with the change applied,
not committed):

- Every product a keyword search finds today is still found (the fold only
  deletes characters from both sides of a substring test).
- Replay of every `search_products` call recorded in `evals/runs/*.json`
  (31 reports, 978 recorded calls; 43 have a mistyped argument and raise in
  both versions, 935 replay): the returned ids differ in 2, both from empty
  to rows: `["50MP"]` (`gen-budget-too-low-2`, report
  `20261113T070516Z-anthropic.json`, 0 to 5 products) and the five-word
  `["optical", "heartrate", "sensor", "continuous", "logging"]`
  (`heartrate-training-zones`, `20261124T165359Z-ollama.json`, 0 to 10).
  The other 933 are identical, in order too. The 2026-11-24 qwen3:8b search
  `["optical heartrate sensor", "continuous logging"]` still matches nothing
  (whole-phrase keywords stay, see Assumptions).
- Committed catalogue (500 products), products matching one keyword, before
  to after: `heartrate` 0 to 31 (equal to `heart rate`, 31); `50mp` 0 to 13;
  `hd` 41 to 100 (59 more, cross-word: "1.2-inch display" folds to
  "...inchdisplay"); `4k` 51 to 55; `gb` 163 to 165; `tb` 40 to 41; `one` 124
  to 129; `ear` 93 to 94. These cross-word matches are accepted (Outcome 3).
- `evals/cases.jsonl` (50 cases, 39 with `expect_search`):
  `catalogue_problems` is `[]` before and after, and `_expected_results` is
  identical for all 39 (same ids, same order).
- `coverage.check_coverage` goes through `search_products` (`coverage.py:112`).
  Over the 36 candidates of the uncommitted `evals/generated.jsonl` the
  verdicts are identical before and after (no probe count crosses its
  scenario's threshold). Its tests are unchanged.
- The existing test suite (926 tests) passes unchanged on the scratch copy.

## Risks

- **A test that passes whatever the code does.** The new tests must fail on
  today's `main`. The implementer runs each once before the fix and notes it
  in Progress. The fixtures must differ from the keyword only by the
  separator (joined keyword against spaced or hyphenated text, and the
  reverse). A fixture where both sides are already joined proves nothing.
- **Breaking §25 `misnamed`.** If `_norm` itself dropped spaces, "Auralis
  Home 1" and "Auralis Home1" would read as one name and positions in
  `misnamed` (which maps characters one for one) would shift. `_norm` is not
  edited; a regression test pins it.
- **The four match sites drifting apart** (§22's lesson, `cases.py:207`). One
  `fold`, imported by all; the agreement tests
  (`test_expected_results_match_search_products_on_every_committed_case`,
  `_same_as_search`) get a joined-word case.
- **Blank keywords.** A keyword of only spaces or hyphens folds to `""`, and
  `"" in haystack` is always true. `keyword_set` must drop `""`, as it
  dropped blanks before (`test_hyphen_only_keyword_is_ignored`,
  `test_blank_keywords_do_not_match_everything_or_count`).
- **Ranking can change for products matching both spellings.** `heart rate`
  and `heartrate` are now one distinct keyword (§22 B3), counted once; a
  keyword list holding both used to count 2 for a product with both forms in
  its text. No recorded call is reordered (replay above), and it follows
  from the owner's rule that they are one word.
- **More cross-word matches** (`hd`: 59 more rows). Accepted by the owner;
  the review should read the numbers above, not rediscover them.
- **Stale line citations.** Read at `18a236c`. §31 edits the loop of
  `agent.py` and §33 edits `prompts/system.md` in other worktrees: lines of
  `agent.py` may drift after a merge of `main`; the symbols will not.
- **Eval run owed, with flaky model runs.** Three of the four edited files
  are in `EVAL_PATHS`. A run on Ollama is not a pass/fail oracle for this
  change (below).

## Verified against the codebase

Re-read on `main` at `18a236c`.

- `src/advisor/catalogue.py:109-110` — `_norm(text)` is `text.lower().replace("-", " ")`; imported privately by `evals/cases.py:10` and `evals/score.py:10`.
- `src/advisor/catalogue.py:113-115` — `keyword_set` returns the distinct `_norm`-ed keywords whose `.strip()` is non-empty.
- `src/advisor/catalogue.py:118-124` — `keywords_matched(product, words)`: `haystack = _norm(f"{name} {brand} {description}")`, counts `w in haystack`.
- `src/advisor/catalogue.py:127-164` — `search_products`: `words = keyword_set(keywords)`, keeps `n > 0 or not words`, sorts by `(-n, price, id)`; docstring `:140-143` says "A hyphen counts as a space" (to update).
- `src/advisor/agent.py:130-138` — the tool uses `keyword_set` and `keywords_matched`, `:136` is the B11 fallback; both go through the changed functions, so the tool needs no edit (the schema text at `:143-146` stays true).
- `src/advisor/evals/cases.py:207-211` — `fits`: `_norm` of the haystack, `any(_norm(w) in haystack ...)`.
- `src/advisor/evals/cases.py:215-236` — `_expected_results`: its own `words` (`:222-224`, `_norm` and `.strip()`) and `matched` (`:227-229`, `_norm`).
- `src/advisor/evals/cases.py:239` — `catalogue_problems` reads only `_expected_results`; no edit.
- `src/advisor/evals/score.py:37-88` — `misnamed`; `:53` and `:55` and `:84-85` use `_norm` per character and per name: these stay on `_norm`.
- `src/advisor/evals/score.py:121-141` — `_call_satisfies`; `:137-138` `_norm` for call keywords and wanted words, then `w in word`.
- `src/advisor/evals/coverage.py:112-119` — `_count` calls `search_products`; `:151-163` the spelling-differs check. No edit.
- `tests/test_catalogue.py:39,133-148` — `_p`, `CAT`, `ids`; `:276-296` the §7 hyphen tests (style to copy); `:299-307` the blank and hyphen-only tests.
- `tests/test_agent.py:389-394` `_rows`; `:427-432` the spelling-variant count test; `:435-440` blank-only keywords.
- `tests/test_evals_score.py:161-169` — `test_search_keywords_are_normalised_on_both_sides`; `:405-419` the `misnamed` fold tests (`names_check`).
- `tests/test_evals_consistency.py:62-67, 124-135, 138-160, 203-208` — hyphen-insensitive `keywords_any`, `_expected_results` vs `search_products`, the committed-cases agreement test, `_same_as_search`.
- `src/advisor/evals/baseline.py:15-26` — `EVAL_PATHS` includes `catalogue.py`, `evals/cases.py`, `evals/score.py` (an eval run is owed); the live-check paths (`CLAUDE.md`) do not include these files.
- `REVIEW-POLICY.md:113` — "Eval runs".
- `CLAUDE.md:164` — "keywords case-insensitive, a hyphen counts as a space" (to update).

## Subtasks

Each ends with `npm run verify` green and its own commit. Tests first
within each subtask: write them, watch them fail, then change the code.

1. **`catalogue.fold` and the search.** Add
   `def fold(text: str) -> str: return "".join(_norm(text).split())`
   (lower case, hyphens read as spaces, then every whitespace character
   dropped; with a docstring that says why `_norm` is kept). `keyword_set`
   folds each keyword and drops `""`. `keywords_matched` folds the haystack.
   Update the `search_products` docstring (separators, §32). Tests below (T1
   to T6).
2. **The case checks and the eval check.** `cases.py`: import `fold`,
   use it in `fits` (haystack and wanted words), in `_expected_results`
   (`words` with `if w`, and `matched`). `score.py`: import `fold` beside
   `_norm`; `_call_satisfies` folds the call's keywords and the wanted words.
   `_norm` use in `misnamed` unchanged. Tests T7 to T11.
3. **Docs.** `CLAUDE.md:164` ("keywords case-insensitive, spaces and hyphens
   ignored (§32)") and the `catalogue.py` bullet for `fold`. Nothing else
   (README does not describe the match rule; checked by `grep -i hyphen`).
4. **Eval run.** Follow `REVIEW-POLICY.md` "Eval runs": `uv run
   advisor-analysis owes-run --base main` (expect owed), then `uv run
   advisor-eval` on Ollama (qwen3:8b), then `compare` against the baseline.
   No paid run unless the owner asks. The run report goes in `evals/runs/`.
   No code change; the review states whether `heartrate-training-zones`
   flipped and why (see Validation).

## Tests

Failing-first (T1, T7 must fail on `18a236c`; all new tests T1 to T11 are
written before the code in their subtask).

- **T1** `test_catalogue.py`: a fixture with "optical heart-rate sensor",
  "heart rate tracking" and "heartrate zones" in three products;
  `["heartrate"]`, `["heart rate"]`, `["heart-rate"]`, `["HEART  RATE"]`
  return the same three ids. Kills: not folding the keyword, not folding the
  haystack (each alone loses one of the three).
- **T2** `test_catalogue.py`, committed catalogue: `category="smartwatch"`,
  `["heartrate"]` and `["heart rate"]` return the same non-empty list.
  Kills: a fold applied to a fixture but not wired into `search_products`.
- **T3** `test_catalogue.py`: no match lost. For every distinct word of
  every committed description (and for each pair of adjacent words joined by
  a space and by a hyphen), the ids that the old rule (`_norm(w) in
  _norm(text)`, written out in the test) matches are a subset of those the
  new search matches, with `limit=10` and the full matched set via
  `keywords_matched`. Kills: any fold that drops a match (e.g. dropping only
  hyphens from the keyword, or stripping other characters).
- **T4** `test_catalogue.py`: the accepted cross-word match, pinned:
  description "a 1.2-inch display" is found by `["hd"]`. Kills: a fold that
  respects word boundaries (which the owner declined).
- **T5** `test_catalogue.py`: `["-", " ", "  - "]` still matches nothing and
  counts nothing (the existing two blank tests, plus a keyword of
  whitespace and hyphens); `keyword_set(["in ear", "in-ear", "inear"])` has
  one element. Kills: not dropping `""` (every product would match), not
  deduplicating after the fold.
- **T6** `test_agent.py`: tool rows for `{"keywords": ["heartrate"]}` against
  a product with "heart-rate": `keywords_matched` is 1; `["heartrate",
  "heart rate", "heart-rate"]` gives 1, not 3; no fallback rows. Kills:
  `keywords_matched` folding only the keyword, a fold that leaves the B11
  fallback firing on a joined word.
- **T7** `test_evals_score.py`: a call with `keywords: ["heartrate"]`
  satisfies `keywords_any: ["heart-rate"]`, and the reverse
  (`["heart rate"]` call, `["heartrate"]` wanted), and
  `["optical heartrate sensor"]` satisfies `["heart-rate"]`; `["noise"]`
  still fails against `["wireless"]`. Kills: `_call_satisfies` still on
  `_norm`, folding only one side.
- **T8** `test_evals_consistency.py`: `fits` with `keywords_any:
  ["heartrate"]` on a product with "heart-rate tracking" is true, and for
  "heart rate" and "HEART-RATE". Kills: `fits` on `_norm`.
- **T9** `test_evals_consistency.py`: `_same_as_search(cat, ["heartrate"])`
  and with a mixed list `["heart rate", "heartrate", "gps"]` on a fixture
  holding the joined, spaced and hyphenated forms: same ids, same order,
  and the distinct-keyword count ranks correctly. Kills: `_expected_results`
  `words` or `matched` on `_norm` (they would disagree with the search).
- **T10** `test_evals_consistency.py`: `catalogue_problems` accepts a case
  with `keywords_any: ["heartrate"]` and `expect_ids` of a "heart-rate"
  product, and still reports one that expects an id with no such text.
- **T11** `test_evals_score.py`, §25 guard: `names_check` is unchanged for a
  name written without its space ("Auralis Home1 (P-009)" is not read as
  the name "Auralis Home 1"), and the existing `test_names_*` tests pass
  unedited. Kills: making `_norm` itself drop spaces.
- Unedited and green: all current tests in `tests/test_catalogue.py`,
  `tests/test_agent.py`, `tests/test_evals_*.py`,
  `tests/test_analysis_coverage.py` (926 tests passed on the scratch copy).
  The committed-cases agreement test
  (`test_expected_results_match_search_products_on_every_committed_case`) is
  the guard that `cases.jsonl` needs no edit.
- No test calls a model or the network (`tests/conftest.py`).

## Validation

- `npm run verify` green
- `npm run check:intent` PASS (or ROUTE with a reason recorded in review.md)
- Eval run (`REVIEW-POLICY.md` "Eval runs"), owed: `catalogue.py`,
  `evals/cases.py` and `evals/score.py` are in `EVAL_PATHS`. Run on Ollama
  after the code subtasks; `advisor-analysis compare` shows the flips. Expect
  `heartrate-training-zones` to flip only if the model searches shorter
  keywords; with qwen3:8b's `["optical heartrate sensor", "continuous
  logging"]` the `search` check passes ("heartrate" is a substring of the
  folded keyword) but `cites_a_match` likely still fails. A case that goes
  from PASS to FAIL is a finding for the review to explain; model variance
  alone is not evidence of a regression, so re-run that case once. The
  review reports the flip or its absence and why.
- Replay check for the review (no model): rerun the recorded
  `search_products` calls of `evals/runs/*.json` on `main` and on the
  branch; the expected difference is the two empty-to-rows calls above.
- Live check: none. The paths touched (`catalogue.py`, `evals/`, `CLAUDE.md`)
  are not among those `REVIEW-POLICY.md` "Live checks" rule 1 names, and no
  CLI, model adapter, tracing, prompt or infra file changes.

## Assumptions I made

- **Whole-phrase keywords stay whole.** A keyword is not split into words;
  this intent's own Assumption left that out. The fold lets "optical
  heartrate sensor" contain "heartrate" for the eval check only; it still
  matches no product text as a search keyword.
- **Which characters fold.** All whitespace (`str.split()`) and hyphens go;
  nothing else (no underscores, slashes, dots or accents). "Spaces and
  hyphens" in the owner's decision is read as this; a keyword of the other
  punctuation is unchanged.
- **The haystack still joins name, brand and description with spaces**
  before folding, so a keyword can now also match across those field
  boundaries (name end + brand start). The replay and the committed-cases
  check show no effect; accepted with the other cross-word matches.
- **`fold` is public** (no underscore) because three modules use it;
  `_norm` stays private and is still imported by `score.py` for `misnamed`.
- **The replay counts are from a scratch copy** (a tree copy outside the
  repo with the change applied, run on `18a236c`); the implementer repeats
  them on the branch and the numbers go in Progress. The earlier attempt
  reported 750 calls; the 31 reports now hold 978 (more runs since), the
  result is the same two changed calls.
- **`follows_up` and tier** as the intent says: empty; the path table puts
  the change in the Attested tier.
- **No new dependency**, no `blocked_by`.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
