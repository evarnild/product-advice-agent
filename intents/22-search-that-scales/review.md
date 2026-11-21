<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §22 review — Product search that still finds the right product in 500

verdict: escalate
tier: reviewed
reviewed-commit: f20551b
round: 3
sampled: no
run: auto
live-check: owed

Tier: Reviewed, never lowered: the path table (`src/advisor/prompts/system.md`)
and `review_tier: reviewed`. No CRITICAL or HIGH finding and none needing
rework: F8 is resolved in the prompt and the eval run shows `voice-speaker`
passing again; F5 and F7 are LOW, carried as worth a look. Verdict
`escalate`: the owner reads the diff.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 22` → "nth
attested auto change = 5, every 3, sampled: no".

HEAD 8a53634 differs from f20551b only in `metadata.yml` (`auto_round: 3`);
the reviewed code is f20551b. `status: in-review`.

**Main moved after this review started:** §15 merged (08e6754, baseline
438b0ec). `git merge-tree --write-tree main feat/22-search-that-scales`
now reports conflicts in `src/advisor/evals/cases.py` and
`tests/test_evals_consistency.py`, so §22 must be rebased (or merged with
main) before `/ship`, and §15's no-match probes `headphones-ldac-balanced-200`
and `smartwatch-gps-apps-minimalist` must be fixed under any-of search
(the plan's rule: the second to merge fixes it). That is a new review round:
the fourth, past `/auto`'s cap, so §22 continues by hand.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the round-2 rework is the B7-amendment sentence (`system.md:12-14`) and its test (`tests/test_agent.py:361-366`); `agent.py` unchanged since round 2 |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | pass for B1–B9 and the B7 amendment; eval run made, no regression |
| 4 | Tests prove the behaviour, not only pass | findings (2), carried: F5, F7 (LOW); 8 mutants, 4 killed, A4 and G2 survive, T1 and T2 survive by design |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: "812 passed", "1 failed, 811 passed", and the amendment's 13/13 vs 6/12 reproduced |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 22, feature)
  error: A live check is owed and not recorded. Do the steps in intents/22-search-that-scales/review.md → ## Live check, then set live_checked: <date> in intents/22-search-that-scales/metadata.yml.
  note:  11 file(s), 346 line(s) changed outside intents/.
```
The only error is the owed live check: the owner's, not rework.

## Resolution of round 2
| Round 2 | Severity | At f20551b | Evidence |
| --- | --- | --- | --- |
| F8 `voice-speaker` regression, `in_stock_only` on every search | MEDIUM (the owner chose c) | resolved: `system.md:12-14` "Set `in_stock_only` only when the customer asks for products in stock; otherwise leave it off, so an out-of-stock match can still be named and flagged." pinned by `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked` (`tests/test_agent.py:361`) | P1–P4 KILLED; eval run: `voice-speaker` PASS, `in_stock_only` on 8 of 13 searches (round 2: 13 of 13; `main`'s old baseline: 6 of 12) |
| F5 tool `description` unpinned | LOW | open (the owner's diff read); `agent.py:131-132` unchanged | A4 SURVIVED |
| F7 `generate.md` no-match clause unpinned, "them" ambiguous | LOW | open; `generate.md:24-26` unchanged | G2 SURVIVED |

The new sentence against the other rules: it narrows "Call it with the …
stock filter that match what the customer asked for" (`:7-8`; redundant,
not contradictory), and is the precondition for "Mention when a recommended
product is out of stock" (`:22`). Grey zone for the live check:
availability questions ("Is the Sonavo Quiet Pro available?",
`out-of-stock-quiet-pro`) may still be read as a stock request.

## Findings
- **F5 LOW** `src/advisor/agent.py:131-132` (carried): the tool
  `description` rewritten outside the plan, unpinned (A4 survives); accurate
  under B2/B3. Worth a look in the diff read; optionally pin it in
  `test_schema_text_says_any_keyword_matches_and_default_ten`
  (`tests/test_agent.py:344`).
- **F7 LOW** `src/advisor/evals/prompts/generate.md:24-26`,
  `tests/test_evals_consistency.py:185-192` (carried): "a no-match probe
  must use words that match none of them" is unpinned (G2 survives) and
  "them" points at "a product's name, brand or description". Worth a look:
  e.g. "…; a no-match probe must use words that no product contains", plus
  an assert.

Nit: `plan.md` subtask 5 and Validation still describe one B7 sentence; the
spec amendment (83cecc9) and Progress record the second. Above Progress is
the owner's.

**Mutants** (copy backup, one-match replace, full `uv run pytest -q`,
restore by copy, `git status --short` clean):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| P1 stock sentence deleted | `system.md:12-14` | KILLED (1 failed, 811 passed) | `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked` |
| P2 "only when" → "when" | `system.md:12` | KILLED | same |
| P3 "otherwise leave it off," dropped | `system.md:13` | KILLED | same |
| P4 "Always set `in_stock_only`;" | `system.md:12` | KILLED | same |
| T1 test weakened to `` "`in_stock_only`" in text `` with P2 | test + prompt | survived, by design (only the full-sentence assert catches wording) | — |
| T2 test made vacuous with P1 | test + prompt | survived, by design (the test is the sentence's only guard) | — |
| A4 old tool description | `agent.py:131-132` | **SURVIVED** | F5 |
| G2 no-match clause dropped | `generate.md:25-26` | **SURVIVED** | F7 |

Round 1's and 2's other killed mutants not re-run: their lines are
unchanged since 6ef5579.

## Not checked
- B10, AC8 and the intent's numbers: the live check (three runs per side).
- How often the model sets `in_stock_only` beyond one run, availability
  questions, and partial (any-of) matches presented as fits: rule 3, the
  live check.
- `advisor-analysis generate` with the reworded `generate.md` (calls a
  model); the token cost of 10 rows instead of 5.
- **The rebase onto `main`** (§15 merged): conflicts in
  `src/advisor/evals/cases.py` (both rewrote `_expected_results`: §15's
  `fits`, §22's ranking) and `tests/test_evals_consistency.py`; §15's two
  no-match probes under any-of search; the 35 new cases under the new
  ranking and the new prompt. None of this is reviewed here.

## Live check
- owed: rule 1 (`src/advisor/prompts/system.md`), AC8/B10 (three-run
  majority), rule 3 (the stock filter's rate; availability questions;
  partial matches presented as fits).
- **Do it after the rebase** (main now has §15's 50 cases): the runs below
  then cover the 50.
- steps:
  1. Start Ollama with the default model (README "Evaluating answers").
  2. On `main`, in `C:/Users/eric/src/product-advice-agent`, run `uv run
     advisor-eval --provider ollama` three times; note the three reports.
  3. In `C:/Users/eric/src/product-advice-agent-wt/22-search-that-scales`,
     run the same three times; copy the reports to the main checkout's
     `evals/runs/`.
  4. Tally per case: `uv run python -c "import json,sys;
     r=json.load(open(sys.argv[1],encoding='utf-8')); print({c['id']:
     c['status'] for c in r['cases']})" <report>`; a case passes on a side
     when PASS in at least 2 of 3.
  5. Count the stock filter per report: `uv run python -c "import json,sys;
     r=json.load(open(sys.argv[1],encoding='utf-8')); a=[t['arguments'] for
     c in r['cases'] for t in c['tools'] if t['name']=='search_products'];
     print(len(a), sum(bool(x.get('in_stock_only')) for x in a))" <report>`.
  6. In the worktree: `uv run advisor "I want in-ear headphones with LDAC
     and a balanced output, under 200 euros"` and read the answer.
- you should see: `student-laptop` and `nc-headphones-under-200` PASS in at
  least 2 of 3 branch runs; no case passing 2 of 3 on `main` fails 2 of 3
  on the branch (watch `voice-speaker`: it cites P-032 and says it is out of
  stock); the stock filter on clearly fewer than all searches; in step 6 the
  answer cites only returned products and claims no feature its text
  lacks. The review then names the six reports, and `live_checked` is
  recorded at your word.

## Eval run
- owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
  touches" `src/advisor/agent.py`, `src/advisor/catalogue.py`,
  `src/advisor/evals/cases.py`, `src/advisor/prompts/system.md`.
- report: `evals/runs/20261121T141005Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at 8a53634 (code = f20551b), copied to
  the main checkout's `evals/runs/`: **11/15**.
- `compare` against `main`'s `evals/baseline.json` (now §15's
  `20261121T125003Z-ollama.json`, 29/50): regressed (1) `waterproof-camera`;
  fixed (3) `nc-headphones-under-200`, `student-laptop`, `tv-sound`; added 0;
  removed 35 (§15's new cases, not on this branch); warnings `cases_sha256`
  and `prompt_sha256` differ (expected).
- `compare` against the pre-§15 baseline (`fd9f7e5:evals/baseline.json`,
  `20261116T093026Z-ollama.json`, 8/15, the one rounds 1–2 used): regressed
  0; fixed (3) the same three.
- re-run: `uv run advisor-eval --only waterproof-camera` →
  `20261121T141235Z-ollama.json`, PASS: not a regression (in the full run
  the model searched `keywords: ["swimming"]` with `in_stock_only` and got
  no rows; the §15 run searched `["waterproof"]`).
- `voice-speaker` (F8): PASS. `in_stock_only` on 8 of 13 searches.
- hashes: the report's `cases_sha256` `2b62108369eb…`, `prompt_sha256`
  `cbf84914b706…`, `catalogue_sha256` `c2e56cb2ffcd…` equal the sha256 of
  the worktree's files (working-tree bytes, autocrlf).
- reading: no regression on one run; the run covers the 15 cases on the
  branch, not §15's 50 (Not checked: the rebase). The six-run majority is
  the live check.

## Verified myself vs. taken on trust

**Coordinator, re-run** (worktree at 8a53634; `git status --short` clean
before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "pass 298",
  "fail 0"; "All checks passed!"; "174 files already formatted"; mypy
  "Success: no issues found in 31 source files"; "812 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "11 file(s), 346 line(s)". Matches.
- **Coordinator, re-run:** P1 KILLED (1 failed, 811 passed); A4, G2
  SURVIVED (812 passed). Matches the reviewer and the implementer.
- **Coordinator, re-run:** the eval run, both compares, the `--only`
  re-run, the stock-filter count and the hash check above.
- **Coordinator, re-run:** `git merge-tree --write-tree --name-only main
  feat/22-search-that-scales` → conflicts in `src/advisor/evals/cases.py`,
  `tests/test_evals_consistency.py` (after §15's merge).

**Reviewer (agent), read-only:** `git diff 6ef5579..f20551b` and the prompt
diff against main; P2–P4, T1, T2; `owes-run`; sampling.

**Taken on trust:** which test kills each mutant (the reviewer's and the
implementer's reports); that the new test failed before the prompt edit
(Progress; P1 shows the equivalent); round 1's and 2's killed mutants on
unchanged lines.

# Round 2 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 6ef5579
- round: 2
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, never lowered: the path table (`src/advisor/prompts/system.md`)
and `review_tier: reviewed`. No CRITICAL or HIGH finding and no finding
needing rework, so the verdict is `escalate` (the owner's diff read, F5
included). The eval run found one regression that failed again on re-run:
F8, "Needs decision", so the run stops at `eval regressions`. The owner
chose rework (F8), so the verdict is `rework`.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 22` → "nth
attested auto change = 5, every 3, sampled: no".

HEAD f4ce400 differs from 6ef5579 only in `metadata.yml` (`auto_round: 2`,
`auto_stopped` cleared); the reviewed code is 6ef5579.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: `generate.md` is outside the plan but is the owner's "22: F4 a", recorded in Progress; F5 left to the diff read |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | pass for B1–B9 (F3 fixed); eval run: findings (1): F8 |
| 4 | Tests prove the behaviour, not only pass | findings (1): F7 (LOW); 8 mutants, 6 killed, A4 and G2 survive |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: F6 corrected; 811 passed reproduced |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; round 1's proposed footgun is the owner's call) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 22, feature)
  error: A live check is owed and not recorded. Do the steps in intents/22-search-that-scales/review.md → ## Live check, then set live_checked: <date> in intents/22-search-that-scales/metadata.yml.
  note:  11 file(s), 335 line(s) changed outside intents/.
```
The only error is the owed live check (set by round 1): the owner's, not
rework. 10 → 11 files with `src/advisor/evals/prompts/generate.md` (F4 a).

### Resolution of round 1
| Round 1 | Severity | At 6ef5579 | Evidence |
| --- | --- | --- | --- |
| F1 brand matching unproven (M13) | HIGH | resolved: `tests/test_catalogue.py:171-172` `keywords=["quiet"]` → `["P-004"]` | M13 KILLED by `test_keywords_case_insensitive_any_may_match` |
| F2 distinct counting unproven (C2, C6) | HIGH | resolved: `tests/test_evals_consistency.py:158-176` `_same_as_search` plus the occurrences and spelling-variant tests | C2 KILLED by `test_expected_results_deduplicates_spelling_variants`; C6 by `test_expected_results_counts_distinct_keywords_not_occurrences` |
| F3 blank-only `keywords_any` excluded everything | MEDIUM | resolved: `cases.py:188` `if words and matched(p) == 0:`; test for `["-"]` and `["-", "alpha"]` | C3 KILLED by `test_expected_results_blank_only_words_match_like_search_products` |
| F4 `generate.md` all-of wording | MEDIUM | resolved per the owner's (a): `generate.md:24-26` "any of which may appear … a no-match probe must use words that match none of them"; `test_generate_prompt_describes_keywords_as_any_of` pins the first clause | G1 KILLED; G2 SURVIVED (F7) |
| F5 tool `description` unpinned (A4) | LOW | open by design, the owner's diff read; text at `agent.py:131-132` accurate | A4 SURVIVES |
| F6 Progress counts | LOW | resolved: "+14 tests (one replaced); 807 passed at 38e0c83", then "811 passed (four added)" | 811 reproduced |

### Findings
- **F8 MEDIUM (eval run)** `voice-speaker` regressed: baseline
  (`20261116T093026Z-ollama.json`) PASS, this run FAIL, and FAIL again on
  the `--only` re-run (`20261121T124544Z-ollama.json`), "does not cite
  P-032". In both branch runs the model searched `{category: speaker,
  keywords: ["voice assistant"], in_stock_only: true}`, got no rows, and
  said nothing is in stock; in the baseline it searched without
  `in_stock_only` and got P-032 (out of stock, which the case expects
  cited and flagged). The search code returns P-032 for the baseline's
  arguments on both sides; the difference is the model's choice of
  `in_stock_only`, possibly nudged by the new prompt sentence or the new
  tool description, possibly run-to-run variance (two runs, qwen3:8b).
  **Needs decision:** accept the regression (the live check's three-run
  majority, AC8, measures it again), or rework (e.g. a prompt or tool
  wording change about stock, a spec change).
  Across the whole run, every search set `in_stock_only` (13 of 13),
  against 6 of 12 on `main`.
  **Owner's decision (2026-11-21): "22 I choose option c"**: rework, a
  prompt line telling the model to set `in_stock_only` only when the
  customer asks for products in stock (spec B7 amendment). Verdict
  `rework`.
- **F5 LOW** `src/advisor/agent.py:131-132` (carried): the tool
  `description` rewritten outside the plan, unpinned (A4 survives); accurate
  under B2/B3. Worth a look in the diff read; optionally pin it in
  `test_schema_text_says_any_keyword_matches_and_default_ten`
  (`tests/test_agent.py:344`).
- **F7 LOW** `src/advisor/evals/prompts/generate.md:25-26`,
  `tests/test_evals_consistency.py:185-192`: the clause "a no-match probe
  must use words that match none of them" is unpinned (G2 survives), and
  "them" grammatically points at "a product's name, brand or description";
  the meaning `check_coverage` enforces is "no product contains any of the
  words". Worth a look: e.g. "…; a no-match probe must use words that no
  product contains", plus an assert on it.

Nit: Progress's first build entry still says blank-only `keywords_any`
"excludes everything"; history, corrected by the rework entry.

**Mutants** (copy backup, one-match replace, full `uv run pytest -q`,
restore by copy, byte-identical):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| M13 brand dropped from the haystack | `catalogue.py:147` | KILLED | `test_keywords_case_insensitive_any_may_match` |
| C2 no dedup | `cases.py:194` | KILLED | `test_expected_results_deduplicates_spelling_variants` |
| C3 no `words and` guard | `cases.py:188` | KILLED | `test_expected_results_blank_only_words_match_like_search_products` |
| C6 count occurrences | `cases.py:199` | KILLED | `test_expected_results_counts_distinct_keywords_not_occurrences` |
| C8 brand dropped from `_expected_results`' haystack | `cases.py:198` | KILLED | `test_keywords_look_in_brand_and_description` |
| A4 old tool description | `agent.py:131-132` | **SURVIVED** | F5 |
| G1 old "must all appear" bullet | `generate.md:24-26` | KILLED | `test_generate_prompt_describes_keywords_as_any_of` |
| G2 no-match clause dropped | `generate.md:25-26` | **SURVIVED** | F7 |

Round 1's 22 killed mutants not re-run: their lines are unchanged since
38e0c83 (only `cases.py:188` changed among source lines).

### Not checked
- B10, AC8 and the intent's numbers: the live check.
- Whether the model now presents partial (any-of) matches as fits, and
  whether it reaches for `in_stock_only` more often (F8): rule 3, the live
  check.
- `advisor-analysis generate` with the reworded `generate.md` (calls a
  model).
- The token cost of 10 rows instead of 5.
- The merged tree under `npm run verify`: `git merge-tree --write-tree main
  HEAD` exits 0, main changed no `src/` or `tests/` since the merge base.
- **Cross-intent, §15** (round 3, attest pending its eval run): it also edits
  `_expected_results`, CLAUDE.md and README, and its no-match probes
  `headphones-ldac-balanced-200` and `smartwatch-gps-apps-minimalist` match
  products under any-of search. Whichever merges second rebases and fixes
  them (the plan's rule); not a §22 finding.

### Live check
- owed: rule 1 (`src/advisor/prompts/system.md`), AC8/B10 (three-run
  majority), rule 3 (partial matches presented as fits; F8's stock filter).
- steps:
  1. Start Ollama with the default model (README "Evaluating answers").
  2. On `main`, in `C:/Users/eric/src/product-advice-agent`, run `uv run
     advisor-eval --provider ollama` three times; note the three
     `evals/runs/<stamp>-ollama.json`.
  3. In `C:/Users/eric/src/product-advice-agent-wt/22-search-that-scales`,
     run the same three times; copy the reports to the main checkout's
     `evals/runs/`.
  4. Tally per case: `uv run python -c "import json,sys;
     r=json.load(open(sys.argv[1],encoding='utf-8')); print({c['id']:
     c['status'] for c in r['cases']})" <report>`. A case passes on a side
     when PASS in at least 2 of 3.
  5. In the worktree: `uv run advisor "I want in-ear headphones with LDAC
     and a balanced output, under 200 euros"` and read the answer.
- you should see: `student-laptop` and `nc-headphones-under-200` PASS in at
  least 2 of 3 branch runs; no case passing 2 of 3 on `main` fails 2 of 3 on
  the branch (watch `voice-speaker`, F8); in step 5 the answer cites only
  returned products and claims no feature its text lacks. The review then
  names the six reports, and `live_checked` is recorded at your word.

### Eval run
- owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
  touches" `src/advisor/agent.py`, `src/advisor/catalogue.py`,
  `src/advisor/evals/cases.py`, `src/advisor/prompts/system.md`.
- report: `evals/runs/20261121T124311Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at f4ce400 (code = 6ef5579), copied to
  the main checkout's `evals/runs/`: **12/15**.
- `uv run advisor-analysis compare` against `evals/baseline.json`
  (`20261116T093026Z-ollama.json`, 8/15): regressed (1) `voice-speaker`;
  fixed (5) `nc-headphones-under-200`, `student-laptop`,
  `video-editing-laptop`, `waterproof-camera`, `tv-sound`; added 0, removed
  0; warning `prompt_sha256` differs (expected: the prompt changed).
- re-run: `uv run advisor-eval --only voice-speaker` →
  `20261121T124544Z-ollama.json`, FAIL again ("does not cite P-032"):
  a regression, F8.
- hashes: the report's `cases_sha256` `2b62108369eb…`, `prompt_sha256`
  `90e19227bea7…`, `catalogue_sha256` `c2e56cb2ffcd…` equal the sha256 of
  the worktree's `evals/cases.jsonl`, `src/advisor/prompts/system.md`,
  `src/advisor/data/catalogue.json` (working-tree bytes, autocrlf).
- reading: the two target cases of B10 pass in this single run; the
  three-run majority is the live check.

### Verified myself vs. taken on trust

**Coordinator, re-run** (worktree at f4ce400; `git status --short` clean
before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "pass 298",
  "fail 0"; "All checks passed!"; "174 files already formatted"; mypy
  "Success: no issues found in 31 source files"; "811 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "11 file(s), 335 line(s)". Matches.
- **Coordinator, re-run:** M13, C2, C3, C6 KILLED (1 failed, 810 passed
  each); A4, G2 SURVIVED (811 passed). Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `owes-run --base main` → owed (4 paths).
- **Coordinator, re-run:** the eval run, compare, `--only` re-run and hash
  check above; the baseline run's `voice-speaker` searched without
  `in_stock_only` and got P-032.

**Reviewer (agent), read-only:** `git diff 38e0c83..6ef5579` and `main...6ef5579`
read in full; C8 and G1 KILLED; `git merge-tree` clean; sampling.

**Taken on trust:** which test kills each mutant (the reviewer's and
implementer's reports; the coordinator's harness records the failure count
only); round 1's 22 killed mutants on unchanged lines; round 1's
measurement of §15's probes under any-of.

# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 38e0c836f3d0a2544ef019125ee9fdd155c5fb49
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, set by the path table (`src/advisor/prompts/system.md`,
Reviewed by meaning) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 22` → "nth
attested auto change = 5, every 3, sampled: no".

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F5 |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): F3; eval run owed |
| 4 | Tests prove the behaviour, not only pass | findings (2): F1, F2; 27 mutants, 22 killed, 5 survived |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): F6 |
| 7 | Documentation | findings (1): F4 |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; one proposed) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 22, feature)
  note:  10 file(s), 291 line(s) changed outside intents/.
```

### Behaviour against the spec
- **B1** met: `passes()` (`catalogue.py:134-143`) keeps category, bounds and
  stock; `test_non_keyword_filters_still_exclude_with_keywords`, M15 killed.
- **B2** met in `search_products` (`hits = [(n, p) for n, p in scored if n >
  0 or not words]`, blanks dropped when `words` is built; hyphen as space,
  M14 killed); brand is searched but no longer tested (F1).
- **B3** met: key `(-t[0], t[1].price_eur, t[1].id)`; a keyword counts once
  (`sum(1 for w in words if w in haystack)`), duplicates collapse after
  `_norm` (`dict.fromkeys`); fixtures disagree on count, price and id; M6–M9
  killed.
- **B4** met: clamp unchanged, function default 5, `[:limit]` cuts the
  ranked list (M10–M12 killed).
- **B5** met: `agent.py:114` `limit = args.get("limit", 10)` with the
  planned comment (A1 killed).
- **B6** met: `keywords` "Any one keyword can match; products matching more
  of the keywords come first."; `limit` "1 to 10 (default 10)"; name,
  property keys and result rows unchanged; the tool `description` also
  rewritten (F5).
- **B7** met: three lines inside the existing search bullet, one sentence
  ("Put the words that distinguish what the customer wants (a use such as
  "student" or "running", a feature such as "noise-cancelling") into
  `keywords`; extra keywords no longer empty a search."); no other line
  changed; the whitespace-normalised test still fails on any word change.
- **B8** partly met: `_expected_results` ranks by `(-matched(p),
  p.price_eur, p.id)` and ADR 0003 is updated; it departs from B2 for
  blank-only `keywords_any` (F3); distinct counting unproven (F2).
- **B9** met: `catalogue_problems` stays empty; old vs new, only
  `drawing-tablet`'s expected rank moves (P-022 5th → 1st); no case edited.
- **B10 / AC8**: the live check.
- **AC4** verified: `search_products(category="laptop", max_price=700,
  keywords=["student"])` → `['P-009']`; the tool default returns 10 with
  P-009 10th (10th cheapest of 11 laptops ≤ 700 €: the default of 10 only
  just includes it).
- **AC7** met, with F2's gap: `test_expected_results_match_search_products_on_every_committed_case`.

### Findings
- **F1 HIGH** `tests/test_catalogue.py:167-174`: brand matching is no longer
  proven; M13 (brand dropped from the haystack, `catalogue.py:147`)
  survives. On `main`, `assert ids(search_products(CAT, keywords=["quiet",
  "noise"])) == ["P-004"]` was the only brand-matched assertion (P-004's
  brand is "Quiet"); the diff deleted it with the all-of assertions. B2:
  "in name, brand or description, as today". **Needs rework:** add `assert
  ids(search_products(CAT, keywords=["quiet"])) == ["P-004"]` (or an
  equivalent brand-only match) to `test_keywords_case_insensitive_any_may_match`.
  Must kill M13.
- **F2 HIGH** `src/advisor/evals/cases.py:193-199`,
  `tests/test_evals_consistency.py:122-133`: `_expected_results`' "distinct
  keywords, each counted once" (B8, spec Interpretations) is unproven; C2
  (no dedup) and C6 (count occurrences) survive (`["alpha", "BETA",
  "beta"]` orders the same either way; no product repeats a keyword).
  **Needs rework:** a consistency test mirroring the catalogue tests,
  asserting ids and equality with `search_products(..., limit=10)`:
  `[prod("P-001", 50, desc="alpha beta"), prod("P-002", 10, desc="alpha
  alpha alpha alpha")]` with `keywords_any ["alpha", "beta"]`; and
  `["in-ear", "in ear", "IN EAR", "beta", "gamma"]` over P-001 "beta gamma"
  and P-002 "in-ear". Must kill C2 (`cases.py:193-195`) and C6 (`:199`).
- **F3 MEDIUM** `src/advisor/evals/cases.py:188`: B8 says `_expected_results`
  ranks "the same way as B2-B3", and B2 says only-blank keywords match
  every product; `_expected_results` excludes everything instead.
  `parse_cases` (`cases.py:87-90`) rejects only `""` and `[]`, so
  `"keywords_any": ["-"]` or `[" "]` parses. On the committed catalogue,
  `{category: laptop, max_price: 700, keywords_any: ["-"]}` gives 0 from
  `_expected_results`, 10 from `search_products` (a case with `expect_ids:
  ["P-009"]` would be reported); `main` matched everything here. No
  committed case is affected; C3 survives. **Needs rework:** `if words and
  matched(p) == 0: return False`, plus a test that
  `_expected_results({"keywords_any": ["-"]}, cat)` and `{"keywords_any":
  ["-", "alpha"]}` each equal `search_products(cat, keywords=…,
  limit=10)`. Must kill C3 (`cases.py:194`). (Rejecting blank-only
  `keywords_any` in `parse_cases` instead would be a spec change.)
- **F4 MEDIUM** `src/advisor/evals/prompts/generate.md:24`: the
  question-generation prompt still says a probe's `"keywords"` are "words
  that must all appear", while `coverage._count` now goes through any-of
  `search_products`. Measured: a no-match probe with several keywords now
  matches when any one appears; reclassified kept → dropped in main's
  untracked pools: 3 of 36 in `evals/generated.jsonl` (`gen-no-match-2`,
  `-4`, `-5`), 2 of 51 in `evals/generated haiku.jsonl` (`gen-no-match-1`,
  `-2`). The plan names the risk, not the prompt; the spec keeps coverage on
  `search_products`. **Needs decision:** (a) update `generate.md` to "any of
  these words; a no-match probe must match none of them" (outside the
  plan); (b) give coverage its own all-of probe rule (contradicts the
  spec's assumption); (c) accept the narrower no-match meaning and leave a
  note.
- **F5 LOW** `src/advisor/agent.py:131-132`: the tool `description` the
  model reads was rewritten (not in the plan; recorded in Progress; no
  conflict with B6; the old "All given filters must match … sorted by price"
  would now be false). No test pins it (A4 survives). Worth a look: accept
  it in the Reviewed diff read, optionally pin it in
  `test_schema_text_says_…`.
- **F6 LOW** `plan.md` Progress ("Tests:"): "grew by about 20 tests" and "804
  passed before the last additions"; measured +14 test functions
  (`test_catalogue` +8 −1, `test_agent` +5, `test_evals_consistency` +2),
  807 passed at 38e0c83. **Needs rework:** append "+14 tests (one
  replaced); 807 passed at <commit>" below the marker.

Proposed footgun (pass 9, the owner's call): "a test edit that replaces
assertions must keep every behaviour the removed lines pinned" (F1).

Nit: "extra keywords no longer empty a search" mentions a change the model
never saw; harmless, and B7's own wording.

**Mutants** (backup by copy, `git diff --quiet` ≠ 0, full `uv run pytest
-q`, byte-identical restore):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| M1 no dedup | `catalogue.py:132` | KILLED | `test_repeated_keyword_is_not_a_bigger_match_than_distinct_ones` |
| M2 no blank filter | `:132` | KILLED | `test_blank_keywords_do_not_match_everything_or_count` |
| M3 count occurrences | `:148` | KILLED | `test_a_keyword_counts_once_however_often_it_appears` |
| M4 any→all | `:154` | KILLED | 8 tests |
| M5 no keywords → nothing | `:154` | KILLED | many |
| M6 drop count key | `:155` | KILLED | 8 tests |
| M7 reverse count | `:155` | KILLED | 8 tests |
| M8 drop price key | `:155` | KILLED | 8 tests |
| M9 drop id key | `:155` | KILLED | 3 tests |
| M10 no lower clamp | `:131` | KILLED | `test_limit_default_and_clamp`, `test_limit_cuts_…` |
| M11 no upper clamp | `:131` | KILLED | 3 tests |
| M12 no `[:limit]` | `:156` | KILLED | 7 tests |
| **M13 brand dropped** | `:147` | **SURVIVED** | F1 |
| M14 no `_norm` | `:147` | KILLED | 3 tests |
| M15 stock filter dropped | `:141-143` | KILLED | 3 tests |
| M16 name dropped | `:147` | KILLED | 3 tests |
| A1 tool default 5 | `agent.py:114` | KILLED | 2 tests |
| A2 old keywords text | `agent.py:60-63` | KILLED | `test_schema_text_says_…` |
| A3 "default 5" | `agent.py:66` | KILLED | `test_schema_text_says_…` |
| **A4 old tool description** | `agent.py:131-132` | **SURVIVED** | F5 |
| C1 drop count key | `cases.py:201` | KILLED | 2 tests |
| **C2 no dedup** | `cases.py:193-195` | **SURVIVED** | F2 |
| **C3 no blank filter** | `cases.py:194` | **SURVIVED** | F3 |
| C4 keyword filter removed | `cases.py:188-189` | KILLED | 3 tests |
| C5 drop id key | `cases.py:201` | KILLED | 2 tests |
| **C6 count occurrences** | `cases.py:199` | **SURVIVED** | F2 |
| C7 reverse count | `cases.py:201` | KILLED | 3 tests |

Not mutated: deleting the prompt sentence (reasoned killed: the test
asserts the full sentence). The rework must kill M13, C2, C3, C6.

### For the coordinator (not findings against §22)
- **§15:** `feat/15-fifty-cases` runs `check_coverage` on its 35 probes;
  under any-of, 2 no-match probes fail: `headphones-ldac-balanced-200`
  (`["ldac", "balanced", "in-ear"]`, max 200) and
  `smartwatch-gps-apps-minimalist` (`["GPS", "third-party apps",
  "minimalist"]`, min 150), each now matching 10. Whichever merges second
  gets a red `verify`. §15's `expect_search` cases still pass a
  `catalogue_problems`-equivalent check (only `drawing-tablet` moves, 5th →
  1st). Related to F4.
- **Product risk of any-of** (for the live check): for a no-match question
  ("LDAC balanced in-ear headphones under 200"), the tool now returns up to
  10 partial matches, and the rows don't say how many keywords each
  matched, so the model may present a partial match as a fit. The owner's
  design choice in the spec; listed for the live check.
- **Behind `main`** by 38 commits (§16, §19); `CLAUDE.md` and `README.md`
  changed on both sides; `git merge-tree --write-tree main HEAD` exits 0.

### Not checked
- B10 and the intent's numbers (11/15 on `main` with 32 products, 9/15 on
  500): need a real model.
- The model's behaviour under the new sentence and description, and whether
  it presents partial matches as fits: the live check.
- Token cost of the default rising from 5 to 10 results.
- `advisor-analysis generate` end to end under the new rule (calls a model);
  F4 measured statically on the existing probe files.
- Mutants beyond the changed lines; the prompt-sentence deletion reasoned.
- `CLAUDE.md` calling `evals/generated.jsonl` committed data (untracked on
  both sides; predates §22; §15 corrects it).

### Live check
- owed: rule 1 (`src/advisor/prompts/system.md`), AC8/B10, and rule 3 for
  "the model presenting partial matches as fits".
- steps:
  1. Start Ollama with the default model (README "Evaluating answers").
  2. On `main`, in `C:/Users/eric/src/product-advice-agent` (no branch
     change), `uv run advisor-eval --provider ollama` three times; note the
     three `evals/runs/<stamp>-ollama.json` paths.
  3. In `C:/Users/eric/src/product-advice-agent-wt/22-search-that-scales`
     at the reviewed commit, the same three times; copy the three reports to
     the main checkout's `evals/runs/`.
  4. Tally per case by majority: for each report, `uv run python -c "import
     json,sys; r=json.load(open(sys.argv[1],encoding='utf-8')); print({c['id']:
     c['status'] for c in r['cases']})" <report>`; a case passes on a side
     when PASS in at least 2 of its 3 runs.
  5. In the worktree, `uv run advisor "I want in-ear headphones with LDAC
     and a balanced output, under 200 euros"` and read the answer.
- you should see: `student-laptop` and `nc-headphones-under-200` PASS in at
  least 2 of 3 branch runs; no case passing on `main` (2 of 3) failing on
  the branch (2 of 3); in step 5, the answer cites only returned products
  and does not claim one has all three features unless its text says so.
  The six report names go in the review; then `live_checked`.

### Eval run
owed: `uv run advisor-analysis owes-run --base main` → `src/advisor/agent.py`,
`src/advisor/catalogue.py`, `src/advisor/evals/cases.py`,
`src/advisor/prompts/system.md`. **Not made this round:** the verdict is
rework and F3 changes `src/advisor/evals/cases.py`, so a run now would not
be of the content that ships. The coordinator makes it, in the worktree,
on the reviewed commit of the first round whose verdict is not rework, and
compares it with `evals/baseline.json`; a flipped case is re-run with
`--only` before it is called a regression.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 38e0c83; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "173 files already formatted"; mypy "Success: no
  issues found in 31 source files"; "807 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "10 file(s), 291
  line(s)". Matches.
- **Coordinator, re-run:** survivors M13, A4, C2, C3, C6 each SURVIVED (807
  passed). Matches the reviewer.

**Reviewer, verified:** verify (kit 298/298, pytest 807), check:intent,
sampling, `owes-run`; 27 mutants; throwaway scripts against the real modules
and committed catalogue: the F3 divergence (0 vs 10), AC4's data, old vs new
expected ranks for the committed and §15 cases, old vs new `check_coverage`
on main's two pools and §15's 35 probes (main's `catalogue.py` via `git
show`), the test delta (+14); `git diff main...HEAD` read in full
(`system.md` adds only the sentence; `metadata.yml` only `status`,
`auto_round`, `auto_stopped`); no remote branch; main checkout untouched.

**Taken on trust:** the Progress entry's commit list (its mutant claims were
re-run, not trusted; they agree except the test counts, F6).
