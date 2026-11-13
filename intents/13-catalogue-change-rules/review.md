<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §13 review — Catalogue changes cannot silently break the eval set

verdict: rework
tier: reviewed
reviewed-commit: 8914cc1d590e87d92365e3ea455e79bb8f44ab11
round: 1
sampled: no
run: auto
live-check: not-needed

Tier: the path table gives Attested (`src/advisor/evals/cases.py`,
`run.py`, tests, docs); `review_tier` is empty; this run's two HIGH
findings raise it to **Reviewed** (input 3).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 13` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (subtasks 1–5, no unplanned scope; plan.md only appended below Progress) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): B2 `in_stock_only: false` |
| 4 | Tests prove the behaviour | findings (1): M14 (order by id only) survives |
| 5 | Conventions | pass (pure check in a CORE_CODE module; `_norm` imported as `score.py` does) |
| 6 | Numbers in prose | pass (622 = 608 + 14) |
| 7 | Documentation | pass (ADR 0003 has B7's six points; README "Changing the catalogue"; CLAUDE.md lines) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 13, feature)
  note:  9 file(s), 233 line(s) changed outside intents/.
```

## Findings
- **HIGH** `src/advisor/evals/cases.py:179`: `in_stock_only: false` is
  read as "out of stock only" (`bool(p.in_stock) != search["in_stock_only"]`).
  Spec B2: "in stock when `in_stock_only` is true"; `search_products(in_stock_only=False)`
  returns in-stock products too. With `{"in_stock_only": false}` an
  in-stock expected id is wrongly reported as not matched and an
  out-of-stock forbidden id is wrongly reported as matched. Latent (no
  committed case uses it), but §14 and §15 edit cases against this check.
  No test covers `false`; the spec-correct form (M23) survives.
  **Needs rework:** `if search.get("in_stock_only") and not p.in_stock: return False`,
  plus a case in `tests/test_evals_consistency.py::test_in_stock_only`:
  `{"in_stock_only": False}` with an in-stock expected id gives no problem
  (and an out-of-stock one is matched).
- **HIGH** `tests/test_evals_consistency.py:64,73`: price-then-id ordering
  is not proven. M14 (`key=lambda p: p.id` at `cases.py:189`) passes all
  622 tests because id order equals price order in both ranking tests; the
  plan's Tests table (B3 ranking row) says the test kills "ordering by id
  only". **Needs rework:** a ranking test where id order and price order
  disagree (e.g. 11 products, P-001 the most expensive: expecting P-001
  gives "11 of 11"; expecting the cheapest, highest id gives none).
- **LOW** (worth a look) `src/advisor/evals/run.py:313`: the catalogue
  file is read a second time for the hash instead of hashing the bytes
  `load_catalogue()` parsed (plan: "read the bytes once"); they differ only
  if the file changes mid-run.

**Mutants** (26 code, 1 data; one change each, full suite, backup and
restore by copy):

| # | Mutation | Result |
| --- | --- | --- |
| M1 | category filter dropped (cases.py:174) | KILLED |
| M2 / M3 | max `>`→`>=` / min `<`→`<=` | KILLED (boundary tests) |
| M4 / M5 | max / min bound dropped | KILLED |
| M6 | in_stock_only ignored (:179) | KILLED (test_in_stock_only) |
| M7 | keywords any → all (:185) | KILLED |
| M8 / M9 | no `_norm` / lower only | KILLED |
| M10 / M11 | haystack drops description / brand | KILLED |
| M12 / M13 | MAX_LIMIT `>`→`>=` / +1 (:211) | KILLED |
| **M14** | **order by id only (:189)** | **SURVIVED** (finding 2) |
| M15 | tie-break dropped (:189) | KILLED (test_ties_are_broken_by_id) |
| M16 | ranks from 0 (:204) | KILLED |
| M17 / M18 / M19 | not-matched / rank / forbid problem dropped | KILLED |
| M20 | B4 skip removed (:201-202) | KILLED |
| M21 / M22 | message without case id / product id | KILLED |
| **M23** | in_stock_only truthy-only, the spec's reading (:179) | **SURVIVED** (finding 1: it is the fix) |
| M24 / M25 / M26 | hash of prompt / cases bytes / key omitted (run.py:313) | KILLED (test_report_records_the_sha256_of_the_catalogue_file_it_loaded) |
| AC3 | data: `student-laptop` expect P-009 → P-001 | KILLED ("case 'student-laptop': P-001 is not matched by expect_search") |

## Not checked
- A real `advisor-eval` run writing `catalogue_sha256` (only the
  fake-client run covers it; the field does not depend on the model).
- `advisor-analysis view` serving a report without the field over HTTP
  (`serve` is stubbed).
- ADR 0003's adjustment/feature line against the kit's adjustment limit
  on a real catalogue edit.
- Whether the branch (based on 17f5e32) merges cleanly into current
  `main` (every later commit touches `intents/**` only).

## Live check
Not needed: no rule-1 path, no `.claude/settings.json`; the one runtime
change (`catalogue_sha256`) is proven in-process with the fake client.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/13-catalogue-change-rules` at 8914cc1; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "135 files already formatted"; mypy "Success: no
  issues found in 27 source files"; "622 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → "type-check: PASS
  (intent 13, feature)", "9 file(s), 233 line(s)". Matches.
- **Coordinator, re-run:** M14 SURVIVED ("622 passed"), M23 SURVIVED
  ("622 passed"). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, the sampling line, 26 code
mutants and one data mutant, every number in prose by script, the docs
against B7; nothing pushed; HEAD unchanged.

**Taken on trust:** the 608 baseline (622 minus the 14 new tests, not run
on `main`).
