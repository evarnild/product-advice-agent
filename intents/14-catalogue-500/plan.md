<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §14 plan — Grow the catalogue to 500 products

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A pure, seeded generator (`src/advisor/catalogue_build.py`, spec B1–B2)
that keeps P-001…P-032 and appends 468 products to reach 500 (B3) with
fixed spec keys, price bands, stock share, brands, unique names and
searchable descriptions (B4–B8); the committed catalogue is its exact
output; every §8 case §13's test flags is fixed with a note (B9); tests
that depended on the 32-product catalogue are updated (B10).

## Risks

- **Not reproducible**: anything outside the seeded `random.Random`
  (set iteration order, `hash()`, dict order from unordered sources)
  makes the committed file differ from a rebuild. AC2 compares the parsed
  committed file with a fresh build on every `verify`.
- **Changing the 32**: a test compares the first 32 with the file at
  `main` (`git show` is not available to tests; instead a frozen copy of
  the 32 as the generator's input is the file's first 32, and AC1 asserts
  they come back unchanged).
- **Breaking §9's generate prompt**: `generate.py`'s `catalogue_summary`
  lists every out-of-stock product; with ~75 out of stock the prompt grows.
  Out of scope to change; the test that pins today's list
  (`tests/test_analysis_generate.py:40-47`) is updated to the new
  catalogue, and the growth is noted in Progress.
- **Weakening cases to make them pass** (B9): a case is tightened, never
  deleted; each changed case's `note` says "§14: …"; the review reads them.
- **Real brand names** (B7): the 4 new brands are invented; the review
  checks them.
- **Line endings**: the committed JSON is CRLF in the working tree with no
  final newline; the generator writes `\n` and lets git normalise; tests
  compare parsed JSON, never bytes.
- Pass 9's list is empty. No live-check path is touched, but AC5's live
  check is owed (rule 3).

## Verified against the codebase

Re-read on `main` at `3d04fd5` (§13 merged).

- `src/advisor/catalogue.py:15-24` `CATEGORIES`; `:25` `DEFAULT_CATALOGUE_PATH`; `:28` `_ID_RE = ^P-\d{3}$`; `:29` `_FIELDS`; `:95` `load_catalogue`; `:113` `search_products` (keywords in name, brand, description).
- `src/advisor/data/catalogue.json` — a JSON list, 2-space indent, 32 products, 458 lines.
- `src/advisor/evals/cases.py:169` `_expected_results`, `:194` `catalogue_problems` (§13).
- `tests/test_evals_cases.py:160` `test_committed_cases_are_consistent_with_the_catalogue`; `:37-46` pins `nc-headphones-under-200` → `{"P-005", "P-001"}` and `"P-004"` in some case.
- `tests/test_analysis_generate.py:40-47` pins `"- headphones: 6 products, 59.0 to 249.0"` and the five out-of-stock ids.
- Tests calling `load_catalogue()` on the shipped file: `test_analysis_cli.py`, `test_analysis_coverage.py` (`CAT`, counts via `search_products(CAT, limit=10, …)`), `test_analysis_generate.py`, `test_catalogue.py`, `test_evals_cases.py`, `test_evals_run.py`, `test_evals_score.py`.
- `evals/cases.jsonl` — 15 cases; §13 found all consistent with 32 products.

## Subtasks

1. **Generator, pure (B1, B4–B8)**: `catalogue_build.py` with per-category
   tables (spec keys and value ladders, price bands, line names),
   `NEW_BRANDS` (4 invented), `SEED`, `TARGET_COUNTS`, and
   `build_products(existing, seed)`. Tests first (AC1, AC3) over the
   generated part. Commit.
2. **Command (B2)**: `python -m advisor.catalogue_build` rewrites
   `src/advisor/data/catalogue.json` from its first 32; `--check` exits 1
   when the file differs from a rebuild. Commit the generator only.
3. **Regenerate and the reproducibility test (B3, AC2)**: run it, commit the
   500-product file; a test asserts the parsed file equals
   `build_products(file[:32], SEED)`, 500 ids P-001…P-500, the per-category
   counts. Commit.
4. **Fix the cases (B9, AC4)**: run §13's test; for each problem, tighten
   the case (a price bound or keyword in `expect_search`, or its ids) and
   add "§14: …" to its `note`. Commit.
5. **Other tests (B10)**: update every test that pinned the 32-product
   contents (e.g. `test_analysis_generate.py:40-47`, coverage counts);
   in-test catalogues untouched. Commit.
6. **Docs**: README (catalogue size, how to regenerate), `CLAUDE.md`
   (the generator, "pure, not imported at runtime"), ADR 0003's example if
   any. Commit.
7. **Finish**: verify, check:intent, `status: in-review`, Progress entry
   (counts per category, out-of-stock share, the new brand names, each
   changed case and why).

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1 | same seed twice equal; other seed differs; first 32 unchanged and first | unseeded random; reordering; editing the 32 |
| B3 | 500 products; ids contiguous P-001…P-500; counts 63/63/63/63/62/62/62/62 | wrong targets; id gap |
| B4 | each new product's spec keys = the category's set | a missing key |
| B5 | price whole, ends in 9, inside band; at least one product in each band third | band off; clustering |
| B6 | out-of-stock share 12–18% of new; ≥ 5 per category | wrong rate |
| B7 | 12 brands; ≥ 4 per category | fewer brands |
| B8 | names unique; description contains the category word and each feature phrase its specs imply | template missing a phrase |
| B2/AC2 | committed file == rebuild | hand edit; nondeterminism |
| B9 | §13's consistency test passes | (data) |

## Validation

- `npm run verify` green; `npm run check:intent` PASS (FAIL only on the
  owed live check).
- Live check (owed, rule 3; spec AC5): `uv run advisor-eval` on `main`
  before and on the branch after (Ollama), compare pass rates and failed
  cases by hand; spot-check three answers for sensible products.

## Assumptions I made

- `--check` on the command (not in the spec) so a reviewer can confirm
  reproducibility from the shell; it writes nothing.
- The 4 new brands and line names are chosen by the implementer and listed
  in Progress.
- A changed case keeps its id and question; only expectations and `note`
  change.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
