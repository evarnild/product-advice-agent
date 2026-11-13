<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §13 review — Catalogue changes cannot silently break the eval set

verdict: escalate
tier: reviewed
reviewed-commit: d822fa763aa96de6b92f2f3bae163a43f6563f29
round: 2
sampled: no
run: auto
live-check: not-needed

Tier: Reviewed, set in round 1 by input 3 (two HIGH findings) and never
lowered; the path table alone gives Attested and `review_tier` is empty.
The reviewer's verdict is `escalate`: no finding needs rework, and the
Reviewed tier needs the owner's diff read.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 13` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Scope: `git diff 338baf8..HEAD`: 525794c (rework: `cases.py:180`, two
tests, a Progress entry) and d822fa7 (`auto_round: 2`). `review.md`,
`spec.md`, `intent.md` untouched; `plan.md` only below Progress.

## Round-1 findings: resolution
| Round 1 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| HIGH | `cases.py:179` `in_stock_only: false` read as "out of stock only" | fixed | `cases.py:180` `if search.get("in_stock_only") and not p.in_stock:` (spec B2; `catalogue.py:138`); `test_in_stock_only_false_does_not_filter_on_stock` covers both halves; R1 (old `!=` form) KILLED |
| HIGH | price-then-id order not proven | fixed | `test_order_is_by_price_not_by_id` (11 products, P-001 dearest); R2 (`key=lambda p: p.id`) KILLED |
| LOW | `run.py:313` catalogue read twice | carried, worth a look | sharing the bytes needs a new `load_catalogue` signature; the reads differ only if the file changes mid-run |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (exactly the two fixes) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass |
| 4 | Tests prove the behaviour | pass (9 of 9 mutants killed) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (624 = 622 + 2) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 13, feature)
  note:  9 file(s), 254 line(s) changed outside intents/.
```

## Findings
No new finding. Carried: **LOW** (worth a look) `src/advisor/evals/run.py:313`,
`catalogue_sha256` hashes a second read of `DEFAULT_CATALOGUE_PATH`.

**Mutants** (`cases.py`; one change each, full suite, backup and restore by copy):

| # | Line | Mutation | Result | Killed by |
| --- | --- | --- | --- | --- |
| R1 | :180 | back to `bool(p.in_stock) != search["in_stock_only"]` | KILLED | test_in_stock_only_false_does_not_filter_on_stock |
| R2 | :190 | `key=lambda p: p.id` | KILLED | test_order_is_by_price_not_by_id |
| R3 | :180 | key present means filter | KILLED | test_in_stock_only_false_does_not_filter_on_stock |
| R4 | :180 | `not` dropped | KILLED | test_in_stock_only |
| R5 | :180 | `if False:` | KILLED | test_in_stock_only |
| R6 | :180 | `if not p.in_stock:` | KILLED | test_in_stock_only, test_in_stock_only_false_does_not_filter_on_stock |
| R7 | :190 | `p.price_eur` only | KILLED | test_ties_are_broken_by_id |
| R8 | :190 | `(-p.price_eur, p.id)` | KILLED | three ranking tests |
| R9 | :190 | `(p.id, p.price_eur)` | KILLED | test_order_is_by_price_not_by_id |

## Not checked
- Round 1's 26 code mutants on lines the rework did not touch (not re-run).
- A real `advisor-eval` run writing `catalogue_sha256`; `view` over HTTP.
- Whether the branch merges cleanly into current `main` (only
  `intents/**` commits on `main` since its base).
- ADR 0003's adjustment/feature line on a real catalogue edit (§14).

## Live check
Not needed: the round-2 diff touches `cases.py` (pure) and tests; no
rule-1 path, no `.claude/settings.json`.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/13-catalogue-change-rules` at d822fa7; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "136 files already formatted"; mypy "Success: no issues
  found in 27 source files"; "624 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "9 file(s), 254
  line(s)". Matches.
- **Coordinator, re-run:** R1 KILLED by
  test_in_stock_only_false_does_not_filter_on_stock, R2 KILLED by
  test_order_is_by_price_not_by_id ("1 failed, 623 passed" each). Matches
  the reviewer and the implementer.

**Reviewer, verified:** verify, check:intent, the round-2 diff in full, 9
mutants, the sampling line; nothing pushed.

**Taken on trust:** round 1's results for untouched lines; the 622
baseline.

# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 8914cc1d590e87d92365e3ea455e79bb8f44ab11
- round: 1
- sampled: no
- run: auto
- live-check: not-needed

Tier: the path table gives Attested (`src/advisor/evals/cases.py`,
`run.py`, tests, docs); `review_tier` is empty; this run's two HIGH
findings raise it to **Reviewed** (input 3).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 13` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 13, feature)
  note:  9 file(s), 233 line(s) changed outside intents/.
```

### Findings
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

### Not checked
- A real `advisor-eval` run writing `catalogue_sha256` (only the
  fake-client run covers it; the field does not depend on the model).
- `advisor-analysis view` serving a report without the field over HTTP
  (`serve` is stubbed).
- ADR 0003's adjustment/feature line against the kit's adjustment limit
  on a real catalogue edit.
- Whether the branch (based on 17f5e32) merges cleanly into current
  `main` (every later commit touches `intents/**` only).

### Live check
Not needed: no rule-1 path, no `.claude/settings.json`; the one runtime
change (`catalogue_sha256`) is proven in-process with the fake client.

### Verified myself vs. taken on trust

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
