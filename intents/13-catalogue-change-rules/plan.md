<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §13 plan — Catalogue changes cannot silently break the eval set

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Make a catalogue edit that invalidates a committed eval case fail
`npm run verify` with the case and product named (spec B1–B5), record which
catalogue every eval run used (B6), and write the catalogue-change rules
down (B7–B8), so §14's growth to 500 products is checked by code.

## Risks

- **A check that agrees with itself.** If the consistency function reuses
  a helper that a mutant could break in the same way as the test's
  expectation, the test passes whatever the code does. The unit tests use
  a small in-test catalogue with literal expected ids, not values computed
  by the code under test.
- **Drifting from `score._call_satisfies`.** B2 must read `expect_search`
  as the scorer does. Re-implementing it differently (e.g. all-of
  keywords) would bless cases the scorer fails. The tests pin any-of,
  case- and hyphen-insensitive keywords and both price bounds.
- **The 10-result bar** (spec Interpretations): off-by-one between "ranked
  10 of 11" (fine) and "11 of 11" (problem). Both sides are tested.
- **Hashing the wrong file.** `run.py` calls `load_catalogue()` with the
  default path; the hash must be of the same file. Tested against
  `DEFAULT_CATALOGUE_PATH`'s bytes.
- **Stale line citations** below: re-check before launch.
- Pass 9's footgun list is empty.

## Verified against the codebase

Re-read on `main` at `6ffdbeb`.

- `src/advisor/evals/cases.py:10` — `from advisor.catalogue import CATEGORIES, Product`.
- `src/advisor/evals/cases.py:13` — `SEARCH_CONSTRAINTS = ("category", "max_price", "min_price", "in_stock_only", "keywords_any")`.
- `src/advisor/evals/cases.py:61-68` — `_ids`: `raise fail(key, f"names unknown product id '{i}'")`.
- `src/advisor/evals/cases.py:114` — `def parse_cases(text: str, catalogue: Sequence[Product]) -> list[Case]:`.
- `src/advisor/evals/score.py:64` — `def _call_satisfies(call, want)`: category equal, `max_price` / `min_price` bounds, `in_stock_only` equal, `keywords_any` any-of over `_norm`.
- `src/advisor/catalogue.py:25` — `DEFAULT_CATALOGUE_PATH = Path(__file__).parent / "data" / "catalogue.json"`.
- `src/advisor/catalogue.py:27` — `MAX_LIMIT = 10`.
- `src/advisor/catalogue.py:95` — `def load_catalogue(path: Path | str = DEFAULT_CATALOGUE_PATH)`.
- `src/advisor/catalogue.py:109` — `def _norm(text: str) -> str:` (case and hyphen normalisation).
- `src/advisor/catalogue.py:113` — `def search_products(...)`: cheapest first, ties by id.
- `src/advisor/evals/run.py:212` — `catalogue = load_catalogue()`.
- `src/advisor/evals/run.py:310-311` — `"cases_sha256"`, `"prompt_sha256"` in the report.
- `tests/test_evals_cases.py:9-10` — `COMMITTED = …/"evals"/"cases.jsonl"`, `CATALOGUE = load_catalogue()`.
- `tests/test_evals_run.py:133,216,375` — the existing hash tests to mirror.
- `scripts/intent-check-lib.mjs:154-159` — `CORE_CODE` already covers `src/advisor/evals/(cases|score)\.py`; putting the check in `cases.py` needs no kit change.
- `README.md:111` — `## Evaluating answers`; `CLAUDE.md:168` — the "Offline evals" paragraph.
- `docs/decisions/` — `0001-stack.md`, `0002-local-model.md`; the next is `0003`.

## Subtasks

1. **The check (B1–B4).** In `src/advisor/evals/cases.py`, a pure
   `catalogue_problems(cases, catalogue) -> list[str]` (name may differ;
   report it) and a helper for the expected results in price-then-id
   order. Read `keywords_any` with `catalogue._norm`, as `score.py` does.
   Use `catalogue.MAX_LIMIT` for the bar. Each problem string names the
   case id, the product id and the reason (spec B3 wording). Code
   comments at the implementation sites for the spec's Interpretations
   ("within MAX_LIMIT, not the default 5"; "keywords any-of, as
   score._call_satisfies"). Unit tests (AC1, AC2). Commit.
2. **The committed-cases test (B5, AC3).** In `tests/test_evals_cases.py`,
   `test_committed_cases_are_consistent_with_the_catalogue`: parse the
   committed file against `load_catalogue()`, assert the problem list is
   empty, and put the list in the assert message. Commit.
3. **The report field (B6, AC4).** In `run.py`, add
   `"catalogue_sha256": hashlib.sha256(DEFAULT_CATALOGUE_PATH.read_bytes()).hexdigest()`
   next to the other two hashes (read the bytes once, from the same path
   `load_catalogue()` used). Tests in `tests/test_evals_run.py`; confirm
   `advisor-analysis counts` and `view` accept a report without the field
   (an existing fixture without it, or a new one). Commit.
4. **The rule (B7, B8, AC5).** `docs/decisions/0003-catalogue-changes.md`
   with B7's six points, linking 0001 and §13/§17; the README paragraph
   "Changing the catalogue" under "Evaluating answers"; one `CLAUDE.md`
   line each for the consistency test and `catalogue_sha256`. Commit.
5. **Finish.** `npm run verify`, `npm run check:intent`; `status:
   in-review`; a `## Progress` entry. Commit.

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B2 category | an expected id in another category → one problem | dropping the category filter |
| B2 max/min price | expected id at 201 with `max_price: 200` → problem; at exactly 200 → none; same for `min_price` | `>` ↔ `>=`, dropping a bound |
| B2 in_stock_only | an out-of-stock expected id with `in_stock_only: true` → problem; with it absent → none | ignoring `in_stock_only` |
| B2 keywords_any | matches on the second of two words; "Noise-Cancelling" matches "noise cancelling" | any→all; no `_norm` |
| B3 ranking | 11 matches, expected id 11th → problem naming "11 of 11"; 10th of 11 → none | `>` ↔ `>=` on `MAX_LIMIT`; ordering by id only |
| B3 order ties | two products at the same price, expected one sorted by id | dropping the id tie-break |
| B3 forbidden | a forbidden id that matches → problem; one outside the filters → none | dropping the forbid check |
| B1 message | each problem string contains the case id and the product id | a message without ids |
| B4 | a case without `expect_search` and an unmatched `expect_ids` → no problem | checking cases without `expect_search` |
| B5 / AC3 | the committed file → `[]` | (guards the data) |
| B6 / AC4 | report's `catalogue_sha256` == SHA-256 of `DEFAULT_CATALOGUE_PATH` bytes, 64 hex chars | hashing the cases or prompt file; omitting the key |
| B6 readers | `advisor-analysis counts` on a report without `catalogue_sha256` exits 0 | a reader requiring the key |

All in-process, no model, no socket.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS.
- Live check: none expected. No rule-1 path is touched; `run.py` gains
  one report field, proven by a test. The review decides.

## Assumptions I made

- The check lives in `cases.py` (already core code), not a new module, so
  `CORE_CODE` in the kit needs no change.
- The problems are plain strings, not a new dataclass; the test asserts on
  their content.
- `run.py` hashes `DEFAULT_CATALOGUE_PATH` because it always loads the
  default catalogue (`run.py:212`); there is no catalogue option to honour.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-13 — build (subtasks 1-5)

Commits: d9ec739 (check), 6755a73 (committed-cases test), the
`catalogue_sha256` commit, the rules commit (ADR 0003, README, CLAUDE.md),
and this finish commit.

Shipped: `catalogue_problems(cases, catalogue) -> list[str]` in
`src/advisor/evals/cases.py` (with a private `_expected_results`), unit tests
in the new `tests/test_evals_consistency.py`, the committed-cases test in
`tests/test_evals_cases.py`, `catalogue_sha256` in the run report plus a test,
a test that `advisor-analysis counts` and `view` accept a report without it,
ADR 0003, the README "Changing the catalogue" section and two CLAUDE.md lines.

Tests: 608 -> 622 passed. No committed case needed fixing.

Divergences: `cases.py` imports the private `_norm` and `MAX_LIMIT` from
`advisor.catalogue` (as `score.py` already uses a `_norm`), rather than a
copy. The README section is a `###` under "Evaluating answers" (placed after
the error-analysis text, before "Check"). Subtasks 1 and 2 were run as one
verify cycle, committed separately.

### 2026-11-13 — review round 1 rework

Commit: see the `§13: rework` commit after 338baf8. Tests 622 -> 624.

- `in_stock_only: false` no longer filters (it was read as "out of stock
  only"); the condition is now `search.get("in_stock_only") and not
  p.in_stock`, as spec B2 and `search_products` read it. New test
  `test_in_stock_only_false_does_not_filter_on_stock`.
- New `test_order_is_by_price_not_by_id` (id order and price order disagree)
  pins price-then-id ordering. Mutation-checked by copy and restore: ordering
  by id only, and the old `!=` stock form, each fail exactly one new test.
- The optional LOW (hash the catalogue bytes once) is left: `load_catalogue`
  takes a path, so sharing the bytes would change its signature.
