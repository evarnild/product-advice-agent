<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §15 review — A committed set of 50 real-looking eval questions with expected behaviour

verdict: rework
tier: attested
reviewed-commit: 37af371
round: 1
sampled: no
run: auto
live-check: owed

Tier: the path table. The diff touches `src/advisor/evals/cases.py` and
`score.py` (`src/**`, not in the Reviewed row), tests, `evals/cases.jsonl`
(data), `README.md`, `CLAUDE.md` and intent artefacts; the highest is
Attested. `review_tier` is empty; no CRITICAL or HIGH finding; no
Not-checked item bears on what a user receives (eval data and scorers).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 15` → "nth
attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F4 |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (2): F1, F7 |
| 4 | Tests prove the behaviour, not only pass | findings (2): F2, F3 |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): F5 |
| 7 | Documentation | findings (1): F6 |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 15, feature)
  note:  10 file(s), 633 line(s) changed outside intents/.
```

## Findings
- **F1 MEDIUM** `evals/cases.jsonl:17,18,21,23,24,46,47`: these questions
  ask for something the expectations don't score, so a wrong answer can
  pass. B6 takes `expect_search` "from the probe", and these probes hold
  only category and price, so `a-match` / `only-matches` accept any product
  in that category and range. Against the 500 catalogue (fitting the
  `expect_search` / naming the extra):
  - `smartwatch-gps-bright-screen-200` (GPS, bright screen): 16 / 4 GPS;
  - `smartwatch-health-100-250` (heart rate, SpO2): 12 / 8;
  - `laptop-uni-backpack-900` ("light enough for a backpack"): 17 / 2; the
    clause was added by the rewrite, not in `haiku:gen-several-matches-2`;
  - `monitor-small-desk-400` (small desk): 16 / 2;
  - `phone-battery-all-day-400` (all-day battery): 12 / 1;
  - `anc-train-rumble-200`, `cordless-over-ear-100-250` (over-ear): 8 / 3
    and 23 / 8.

  E.g. a non-GPS watch under 200 euros passes
  `smartwatch-gps-bright-screen-200`. **Needs decision**, per case: (a) add
  the extra to `keywords_any` where the catalogue supports it (departs from
  B6's "from the probe": a spec amendment); (b) cut the extra from the
  question (for `laptop-uni-backpack-900`, at least the added clause); or
  (c) keep it, leave the extra to §16's judge, and say so in the `note`.
  Can be done as part of the AC6 edit.
- **F2 MEDIUM** `tests/test_evals_cases.py:317-332`
  (`test_new_cases_expect_what_their_scenario_says`): B6's table is not
  enforced, so a wrong expectation (above all the owner's own AC6 edits)
  goes unnoticed. Data mutants D1 (`gift-smartwatch-300`, line 16, loses its
  `expect_properties`: exact-match is lumped with no-match and
  budget-too-low) and D2 (`norvik-canvas-school`, line 41, `expect_ids`
  P-024 → P-004: nothing ties it to the probe's `product_id`) survive. The
  data is right today (all 35 read against B6). **Needs rework**, per B6:
  exact-match → `expect_search` and (`expect_ids` or `cites_a_match`);
  out-of-stock → `expect_ids == [probe.product_id]`; no-match and
  budget-too-low → `expect_search`, no `expect_ids`, no
  `expect_properties`, no `must_decline`. Must kill D1, D2.
- **F3 LOW** `tests/test_evals_cases.py:214, 310-314`: B8's "at least 5"
  has no boundary test; T5 (`MIN_VARIETY = 5` → `4`) survives (the file has
  6 typo and 6 vague, so 4, 5, 6 all pass;
  `test_variety_is_counted_from_the_note_with_a_boundary` tests counting,
  not the threshold). The plan's Risks: "Each bound gets a boundary test on
  an in-test case list". **Needs rework:** move the threshold into a helper
  (e.g. `variety_problems(cases)` using `MIN_VARIETY`) and test 4 fails, 5
  passes on an in-test list. Must kill T5.
- **F4 LOW** `evals/cases.jsonl:37` (`tablet-reading-drawing-80`): a
  disclosed departure from B6. The source `haiku:gen-budget-too-low-11` (a
  son, school, under 120) fails `check_coverage` (one tablet at 119 fits);
  the case moves the probe to `max_price` 80, rewrites the question (a
  cousin, reading and drawing, 80 euros) and changes the persona to gift
  buyer. Only 4 budget-too-low pool items pass on the 500 catalogue (3
  laptops, 1 tablet), and without this case tablet is a `feature` only 3
  times; an unused passing laptop source, `gen-budget-too-low-12`, exists
  but doesn't help the tablet count. **Needs decision:** accept the edited
  source (it now duplicates `tablet-under-100` in substance), or swap in
  another passing tablet source from a different scenario and use
  `gen-budget-too-low-12` for the fifth budget case.
- **F5 LOW** `intents/15-fifty-cases/plan.md:230, 292-298` (Progress)
  overstates: "Four sources had a probe that did not fit as written" holds
  only for the tablet (the three out-of-stock probes pass `check_coverage`
  as written, which ignores category for out-of-stock; their edits correct
  the generator's category: P-017 phone, P-024 tablet, P-032 speaker); a
  fourth feature correction is unmentioned (`gen-out-of-stock-1` →
  `norvik-fold-brother-gift`, monitor → phone); "4 `fits`" tests: there are
  3. **Needs rework:** correct the Progress entry (append a correction
  below it).
- **F6 LOW** `README.md:285-295` ("Changing the catalogue") lists what
  fails `verify` after a catalogue edit but not B4's new message ("no
  product fits expect_search, so cites_a_match cannot pass"). Worth a look.
- **F7 LOW** `evals/cases.jsonl:38-42`: variety tags meet B8 only
  literally. Five of six `vague` are out-of-stock questions naming an exact
  product (Pelagic Studio 15, Norvik Fold ×2, Norvik Canvas 13, "Aurelis"
  Home 1): no category word, but the opposite of vague; `music-gift-150` is
  the only truly vague one. `multi` is uneven (`tablet-reading-drawing-80`
  is multi, `sister-birthday-watch` with category, budget and gift is not).
  Worth a look at the live check.

Nit: AC2 names "an in-test catalogue"; the new score tests use the real
catalogue, as the existing score tests do; the per-constraint checks are
`fits` tests in `tests/test_evals_consistency.py`, covering B2 through the
shared predicate.

**Mutants** (one per changed behavioural line; copy-backup harness
asserting one match and `git diff --quiet` ≠ 0; full product suite `uv run
pytest -q -x`; restored byte-identical): 40 run, 36 killed, 4 survived.
- `cases.py`: C1 (field dropped from `_FIELDS`), C2 (`PROPERTIES` loses a
  name), C3 (empty list accepted), C4 (list check dropped), C6
  (unknown-name check dropped), C7 (duplicate check dropped), C8
  (needs-`expect_search` check dropped), C9 (`_properties` returns `()`),
  C10 (`parse_cases` ignores the field): KILLED. C5 (`isinstance(name, str)`
  dropped): SURVIVED, equivalent (a non-string also fails `name not in
  PROPERTIES` with the same error).
- `fits` F1–F8 (category, `>=`, `<=`, stock, any→all, brand dropped, no
  `_norm`, keyword branch dropped): KILLED. B4a (property condition
  dropped), B4b (inverted), B4c (wrong property name): KILLED.
- `score.py`: S1, S1b (existence filter), S2 (`a-match` ok on any
  citation), S3, S7 (check without its property), S4 (`fits` dropped from
  `a-match`), S5 (`only-matches` always ok), S6 (misfit test inverted), S8,
  S9 (reasons lose the ids): KILLED.
- Test helpers: T1 (scenario high 12→13), T2 (low 5→4), T3a (off-topic low
  2→1), T3b (off-topic high 4→5), T4 (per-feature 4→3): KILLED, both sides
  hit. **T5** (`MIN_VARIETY` 5→4): SURVIVED (F3).
- Data: **D1**, **D2**: SURVIVED (F2).

The rework must kill D1, D2 and T5.

## Not checked
- Whether the 50 read like real customers and the expectations are what the
  owner wants: the owner's AC6 read (live-check rule 3).
- Model output on the 50, including AC6's baseline pass rate (see Eval run).
- The "keeps what the probe expresses" judgement on all 35 is the
  reviewer's, not repeatable by a tool.
- Mutants not run: `PROPERTIES` with a third arbitrary name (only
  `cites_everything` is tested as unknown; low value, a name needs a
  `score.py` check); the `Case` default `expect_properties=()`; the `ok`
  reason strings of `a-match` and `only-matches` (no test reads them).
- Kit mutation behaviour (no kit file changed); `npm run sessions`.

## Live check
- owed: rule 3 (AC6): the questions' real-lookingness and the model's
  output on the 50 show only with an owner read and a real run.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/15-fifty-cases`, open
     `evals/cases.jsonl`. Lines 1–15 are §8's cases (only `dimensions`
     added, verified byte for byte); lines 16–50 are the new 35, each
     `note` naming its source (`haiku:` = `evals/generated haiku.jsonl`),
     probe and variety tags.
  2. Read every question and expectation; decide F1 (lines 17, 18, 21, 23,
     24, 46, 47) and F4; edit anything that doesn't read like a customer or
     isn't the right expectation.
  3. After any edit, `npm run verify` (format, catalogue consistency,
     spread, variety, each probe against `check_coverage`); commit on
     `feat/15-fifty-cases`. The next review round covers the edits.
  4. `uv run advisor-eval` once on the default model (local Ollama, minutes
     on CPU), from the worktree.
- you should see: one PASS / FAIL / ERROR line per case for 50 cases and a
  total; a report `evals/runs/<stamp>-ollama.json` whose `cases_sha256`
  matches the committed `evals/cases.jsonl`; cases with
  `expect_properties` show `a-match` and/or `only-matches`. Quote the pass
  rate as the baseline (AC6). A FAIL is not by itself a defect here (§16's
  judge covers wording).

## Eval run
owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
touches `evals/cases.jsonl`, `src/advisor/evals/cases.py`,
`src/advisor/evals/score.py`". **Not made this round:** the verdict is
rework, and F1 and F4 will change `evals/cases.jsonl`, so a run now would
not be of the content that ships. The coordinator makes it in the first
round whose verdict is not rework, on the reviewed commit (35 cases
"added" in `compare` is expected). Hashes at 37af371 for reference:
`evals/cases.jsonl` `a80b0a1b…8f43`, `src/advisor/prompts/system.md`
`a22c1cbe…0fdc`, `src/advisor/data/catalogue.json` `c2e56cb2…efab`.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 37af371; `git status --short`
shows only the two untracked pool files before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "163 files already formatted"; mypy "Success: no
  issues found in 29 source files"; "739 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "10 file(s), 633
  line(s)". Matches.
- **Coordinator, re-run:** survivors D1, D2, T5 each SURVIVED (739
  passed). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, `owes-run` (owed, 3 paths),
sampling; the data with scratch scripts against the real modules: 50 cases,
unique ids and questions; the scenario, feature, persona and variety counts
above; each typo tag a real misspelling; 35 with `source:`; §8's 15
identical to `main` but for `dimensions`; AC5 on all 35 (every source id in
the pools; every probe passes `check_coverage` by the reviewer's own call;
every `expect_search` equals its probe; every out-of-stock `expect_ids` is
its probe's product, P-010, P-017, P-024, P-032 out of stock;
spelling-differs carry `keywords_any` and `cites_a_match`; no-match and
budget-too-low carry no properties; off-topic `must_decline`); the corrected
probes; budget-too-low pool pass rate 4 of 28; the 40 mutants; `cases.py`
and `score.py` import only `advisor.catalogue` and each other; no
dependency, secret or user data; main unchanged, no upstream.

**Taken on trust:** that the worktree's pool files are the owner's pools
(the coordinator copied them from the main checkout); the kit's own tests
for `check:intent` and `sdlc:scan`.
