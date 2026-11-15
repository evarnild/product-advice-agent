<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §14 review — Grow the catalogue to 500 products

verdict: escalate
tier: reviewed
reviewed-commit: 46efe59f4280dcc6532308436fa3aeb8bbb46c6e
round: 2
sampled: no
run: auto
live-check: owed

Verdict: escalate. Every round-1 finding that needed rework (F1, F2, F3,
F6) or was worth a look (F4, F7) is resolved; 17 of 17 mutants are killed;
no finding needs rework. The tier is Reviewed, so the owner reads the diff.

Tier: Reviewed, carried from round 1 (input 3: the owed live check concerns
what users receive). Nothing lowers a tier.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 14` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

## Resolution of round 1
| Round 1 | Resolution | Evidence |
| --- | --- | --- |
| F1 MEDIUM the 32 unpinned | resolved | `tests/test_catalogue_build.py:46` `FIRST_32_SHA256`, test at `:58-61`; sha of main's 32 recomputed = `7b19c278…f21f4`; D02, M09b killed |
| F2 MEDIUM oracle reads the module | resolved | `BANDS`, `KEYS` literals at `:25-44`, match spec B4/B5; M03d killed by the band test and the totals pin, M03e by the totals pin only (F8) |
| F3 MEDIUM command untested | resolved | `main(argv, path=DATA_PATH)` at `catalogue_build.py:292-310`, tmp-copy tests at `:211-238`; M12-M17 killed |
| F4 LOW description values | resolved | `PRINTED` at `:152-174`; M08c-M08h killed with regeneration |
| F5 MEDIUM sport-earbuds, student-laptop | open, as intended | left to the live check; no case changed |
| F6 LOW Progress hashes | resolved | f56d7bb, 06af3a1, acbd3c4, c181170, 74f9cfe, 2569766 on the branch |
| F7 LOW CLAUDE.md line | resolved | `CLAUDE.md:156-158` says not in `CORE_CODE`, `main` is I/O |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (round-2 diff: CLAUDE.md, metadata, plan.md below Progress, `catalogue_build.py` path parameter, the test file) |
| 2 | Type check | pass (FAIL only on the owed live check) |
| 3 | Behaviour against the spec | pass (data and cases unchanged since round 1; AC5 is the live check) |
| 4 | Tests prove the behaviour | pass (17/17 killed; F8 on how M03e is guarded) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (653 → 658, the sha, the eight totals reproduce) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (no dependency, no secret) |
| 9 | Repository-specific footguns | pass (list empty; round 1's "self-referential test oracle" candidate not added, the owner's call) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 14, feature)
  error: A live check is owed and not recorded. Do the steps in intents/14-catalogue-500/review.md → ## Live check, then set live_checked: <date> in intents/14-catalogue-500/metadata.yml.
  note:  13 file(s), 7290 line(s) changed outside intents/.
```
The only error is the owed live check; clearing it is the owner's.

## Findings
- **F8 LOW** (worth a look) `tests/test_catalogue_build.py:241-260`
  (`NEW_PRICE_TOTALS`): a snapshot, not a B5 guard. M03e (camera 99-2999)
  still yields B5-valid data (149-2959, all thirds used), so only an
  implementation pin can kill it; the totals do, but every intended
  regeneration that moves a price must update eight numbers. Alternative:
  `assert PRICE_BANDS == BANDS` (and `SPEC_KEYS == KEYS`), which kills
  M03d and M03e and survives a regeneration. Either is acceptable.
- **F5 MEDIUM** (carried, worth a look, for the live check)
  `evals/cases.jsonl`: `sport-earbuds` (P-002 ranks 10 of 63) and
  `student-laptop` (P-009 ranks 10 of 11) sit beyond the default search
  `limit` of 5; `no-laptop-under-200`'s note ("P-012 at 329") is stale.
  The owner decides after the eval run.
- Nits: Progress names the rework commit as "see `git log`" rather than
  `ae937db`; "a APS-C sensor"; camera "1 in" vs "inch"; 175 KB vs "about
  150 KB".

**Mutants** (17, full suite each; "regen" = generator re-run): KILLED all:
D02, M09b, M03d, M03e (totals pin only), M12, M13, M13b, M08c-M08h, M14
(`main` ignores `path`), M15 (`check = False`), M16 (`newline` → None),
M17 (`--check` difference returns 0). Survivors: none.

## Not checked
- Model answers on 500 products (AC5): pass rate, the five tightened
  cases' keywords, F5's two cases.
- Langfuse traces of those runs; the `generate` prompt growth (77
  out-of-stock products).
- Whether the four brands are registered anywhere.
- "Specs scale with price" has no test of its own.
- The `argv is None` branch of `main` by test (`--check` from the shell
  exited 0).

## Live check
- owed: rule 3 (model output on the new catalogue; spec AC5, ADR 0003's
  eval run).
- steps:
  1. Before: in `C:/Users/eric/src/product-advice-agent` on `main` (Ollama
     up, same `.env`), `uv run advisor-eval --provider ollama`; note the
     report, pass rate, failed ids, `catalogue_sha256`.
  2. After: in `C:/Users/eric/src/product-advice-agent-wt/14-catalogue-500`,
     the same command; `catalogue_sha256` differs.
  3. Compare by hand: pass rates and failed cases; for the five changed
     cases (`video-editing-laptop`, `gaming-monitor`, `drawing-tablet`,
     `gps-watch`, `tv-sound`), did the search include the keyword and is
     the expected id cited; for `sport-earbuds` and `student-laptop`, did
     the search show P-002 / P-009.
  4. Spot-check three answers (`nc-headphones-under-200`, `gps-watch`,
     `tv-sound`) in Langfuse (tag `eval`) or the report.
  5. Name both reports in the next `review.md`, then record `live_checked`.
- you should see: the after pass rate equal to before, or lower only by
  cases you can explain (likely F5); no ungrounded ids; cited prices match
  the catalogue; out-of-stock products flagged; answers naming fitting
  in-category products, some of them P-033+.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/14-catalogue-500` at 46efe59; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "153 files already formatted"; mypy "Success: no issues
  found in 28 source files"; "658 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "13 file(s), 7290 line(s)". Matches.
- **Coordinator, re-run:** the kills round 1's resolutions claim: D02
  KILLED (1 failed; `--check` exit 0, as expected), M12 KILLED (2 failed),
  M13 KILLED (1 failed), M03d laptop 249-3499 regenerated KILLED (2
  failed), M03e camera 99-2999 regenerated KILLED (1 failed). Matches the
  reviewer.

**Reviewer, verified:** verify, check:intent, sampling; the sha of main's
32 and the eight totals by a scratch script; M03d and M03e in memory
(camera 99-2999 still meets B5, laptop 249-3499 does not); 17 mutants;
`--check` from the shell; data and cases unchanged since round 1;
plan.md edits only under Progress; nothing pushed.

**Taken on trust:** the four brand names not being real electronics
brands; the commit order's reason (unchanged since round 1).
# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: f2426b930d0889d4747d462f2bcc38fd6c936587
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: the path table gives Attested (`src/advisor/catalogue_build.py`,
`src/advisor/data/catalogue.json`, tests, `evals/cases.jsonl`, docs);
`review_tier` is empty; input 3 raises it to **Reviewed**: the owed live
check concerns what users receive (model answers on 500 products), with a
concrete reason to expect change (F5).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 14` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (generator not in `CORE_CODE`, declared) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (B1-B10 and AC1-AC4 checked in the data; AC5 is the live check) |
| 4 | Tests prove the behaviour | findings (4): F1-F4 |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): F6 |
| 7 | Documentation | findings (1): F7 |
| 8 | Guardrails and hygiene | pass (no dependency, no secret) |
| 9 | Repository-specific footguns | pass (list empty; candidate below) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 14, feature)
  note:  13 file(s), 7178 line(s) changed outside intents/.
```

### Findings
- **F1 MEDIUM** `tests/test_catalogue_build.py:19-35`: nothing pins
  P-001…P-032 to their original content; `FIRST_32` comes from the
  committed file, so the "unchanged" test compares the file with itself.
  D02 (a hand edit to P-006's description) passes all 653 tests and
  `--check` (exit 0); M09b (the generator edits the 32, then regenerate)
  passes too. The data itself equals `main`'s today. **Needs rework:** pin
  the 32, e.g. `sha256(json.dumps(COMMITTED[:32], sort_keys=True,
  ensure_ascii=False))` == `7b19c2785849fb227c1a9647c442ed2260ca275e0a5e4a83c46c1178f89f21f4`
  (main's 32), or a frozen copy.
- **F2 MEDIUM** `tests/test_catalogue_build.py:9-16, 66-85`: the band and
  spec-key tests import `PRICE_BANDS` and `SPEC_KEYS` from the module under
  test. M03d (laptop 249-3499) and M03e (camera 99-2999), each regenerated,
  pass. **Needs rework:** write B5's eight bands and B4's eight key tuples
  as literals in the test, as `test_counts_per_category` does.
- **F3 MEDIUM** `src/advisor/catalogue_build.py:286-302` (`main`): the
  command is untested; M12 (`--check` never differs) and M13 (indent 4,
  ASCII escapes) survive. **Needs rework:** a path parameter (default the
  data file), tested on a tmp copy: `--check` 0 on an unedited copy, 1
  after an edit; a rewrite equals `json.dumps(built, indent=2,
  ensure_ascii=False)`.
- **F4 LOW** (worth a look) `tests/test_catalogue_build.py:122-146`: the
  description test checks B8's four features but not every printed value
  (M08c-M08f survive with regeneration).
- **F5 MEDIUM** (worth a look, for the live check) `evals/cases.jsonl`:
  `sport-earbuds` (P-002 ranks 10 of 63) and `student-laptop` (P-009 ranks
  10 of 11) pass §13's check (≤ `MAX_LIMIT` 10) but sit beyond the tool's
  default `limit` of 5 (`agent.py:109`); expect them to fail in
  `advisor-eval` unless the model asks for more. `no-laptop-under-200`'s
  note ("P-012 at 329") is stale: the cheapest laptop is now P-241 at 259.
  B9 only requires the cases §13 reports; changing these is a decision
  after the live check.
- **F6 LOW** `plan.md` Progress: pre-rebase hashes (fcb8d7e … 57c884d); the
  branch has f56d7bb, 06af3a1, acbd3c4, c181170, 74f9cfe, 2569766.
  **Needs rework:** update them.
- **F7 LOW** (worth a look) `CLAUDE.md:156-158`: the generator sits under
  "Pure, tested logic (the `CORE_CODE` modules…)" but is not in
  `CORE_CODE` and its `main()` does I/O.
- Not findings: the red commit acbd3c4 (declared; `--no-ff` keeps `main`'s
  first-parent history green); generic line names behind invented brands
  (the 32 already use them). Nits: "a APS-C sensor"; camera "1 in" vs
  "inch"; 175 KB vs "about 150 KB".
- Pass-9 candidate: "Self-referential test oracle: a test that imports its
  expected values from the module it tests proves nothing about the
  spec's values."

**Mutants** (31 generator, 2 data; mode A = mutate and run the suite, mode B
= mutate, regenerate, run): SURVIVED: M12, M13 (A and B); D02 (A); M09b,
M03d, M03e, M08c-M08f (B). KILLED: unseeded RNG (M01), dropped spec key
(M02), band and price-ending mutants (M03a-c, M04, M04b), stock share
(M05a-b), brands (M06, M06b), name retry (M07), description phrases
(M08a-b), first 32 reordered or restocked (M09a, M09c), target counts
(M10, M10b), spec scaling (M11, by data pins), D01 (a price edit in the
file, by the rebuild test; `--check` exit 1).

### Not checked
- Model answers on 500 products (AC5): pass-rate change, the keywords of
  the five tightened cases, F5's two cases.
- Langfuse traces of those runs; the `generate` prompt growth (77
  out-of-stock products); whether the four brands are registered anywhere.
- "Specs scale with price" by test (checked by correlation and reading
  only).

### Live check
- owed: rule 3 (model output on the new catalogue; spec AC5, ADR 0003's
  eval run).
- steps:
  1. Before: in `C:/Users/eric/src/product-advice-agent` on `main` (Ollama
     up, same `.env`), `uv run advisor-eval --provider ollama`; note the
     report, pass rate, failed ids, `catalogue_sha256`.
  2. After: in `C:/Users/eric/src/product-advice-agent-wt/14-catalogue-500`,
     the same command; `catalogue_sha256` differs.
  3. Compare by hand: pass rates and failed cases; for the five changed
     cases, did the search include the keyword and is the expected id
     cited; for `sport-earbuds` and `student-laptop`, did the search show
     P-002 / P-009.
  4. Spot-check three answers (`nc-headphones-under-200`, `gps-watch`,
     `tv-sound`) in Langfuse (tag `eval`) or the report.
  5. Name both reports in the next `review.md`, then record `live_checked`.
- you should see: the after pass rate equal to before, or lower only by
  cases you can explain (likely F5); no ungrounded ids; cited prices match
  the catalogue; out-of-stock products flagged; answers naming fitting
  in-category products, some of them P-033+.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/14-catalogue-500` at f2426b9; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "152 files already formatted"; mypy "Success: no issues
  found in 28 source files"; "653 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "13 file(s), 7178
  line(s)". Matches.
- **Coordinator, re-run:** D02 SURVIVED ("653 passed", `--check` exit 0);
  M12 SURVIVED (`--check` exit 0); M13 SURVIVED; M03e (camera 99-2999,
  regenerated) SURVIVED. Matches the reviewer.

**Reviewer, verified:** verify and check:intent; `--check` (0 committed,
1 with D01); the data by script (the 32 equal `main`'s parsed JSON, ids
contiguous, counts 63×4 / 62×4, 72 of 468 new out of stock with 9 per
category, 12 brands in every category, B4 keys, B5 prices, unique names,
layout); the cases (§13 check `[]`, five problems on `main`'s cases
reproduced, only `expect_search` and `note` changed, keyword reach);
every B10 test change against the data; 33 mutants; the red commit
from an extract; nothing pushed.

**Taken on trust:** the four brands not being registered electronics
brands; why the commit order put the file before the tests.
