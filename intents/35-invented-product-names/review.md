<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §35 review — Catch an answer that names a product the catalogue does not have

verdict: attest
tier: attested
reviewed-commit: 8360831f1fb197da58ac253fead47e5881396b26
main: bab8ec8
round: 3
sampled: no
run: auto
live-check: not-needed

The reviewer examined `3ad7dee`. The branch has since been merged with `main`
(bab8ec8, which includes §30) at `8360831`; `git diff 3ad7dee HEAD --
src/advisor/evals` is empty, so the reviewed code is unchanged (the merge
brought §30's `agent.py`, `catalogue.py` and tests, which do not touch
`score.py`, `_norm` or `fold`).

Rounds: round 1 (rework: the owner decided the "Recommend Auralis Home 1"
false positive as option (a); five test gaps; a corrupted section sign) and
round 2 (rework: two surviving mutants on the new own-name clause, README,
fixture note and Progress corrections), both fixed (commits `99bd414`,
`d86c8a5`). Round 1's report is below; round 2's findings and their
resolution are summarised in "Round 2" under the findings.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: `git diff d86c8a5~1 HEAD -- src` is empty before the merge; `git diff main...HEAD --stat` lists only `README.md`, `src/advisor/evals/score.py`, `tests/test_evals_score.py`, `tests/fixtures/invented_replay.json` and `intents/35-...` |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: the owner's decision (a) is `shown.endswith(" " + own)` at `score.py:156`; spec.md B2 does not record it yet (see "For the owner") |
| 4 | Tests prove the behaviour | pass: every mutant in the set is killed |
| 5 | Conventions | pass: pure, `difflib` (standard library) is the only new import, no model call |
| 6 | Numbers in prose | pass after round 2 |
| 7 | Documentation | pass: the README bullet is true, and now says a word put before the real name passes |
| 8 | Guardrails and hygiene | pass: the fixture holds synthetic catalogue output only |
| 9 | Repo-specific footguns | none |

Tier: Attested (`score.py` is core code, `review_tier` is empty). No CRITICAL
or HIGH finding in any round, so rule 3 never raised it.

## Type check

```
type-check: PASS (intent 35, feature)
  note:  4 file(s), 1461 line(s) changed outside intents/.
```

## Findings

None that need rework. Round 2's findings were fixed in `d86c8a5`:
1. LOW: `new_clause_charsuffix` (`shown.endswith(own)`) survived: now
   killed by `runs("Recommend Xauralis Home 1 (P-032)") == [("P-032",
   "Recommend Xauralis Home 1")]`.
2. LOW: `new_clause_contains` (`(" " + own) in shown`) survived: now killed by
   `runs("Recommend Auralis Home 1 Max (P-032)") == [("P-032", "Recommend
   Auralis Home 1 Max")]`.
3. LOW: the README now says a word put before the real name ("Norvik
   Auralis Home 1 (P-032)") passes, because the run then ends in the id's
   own name.
4. LOW: the fixture note says the clean answer was shortened and the euro
   sign written as "euros", quoting the original.
5. LOW: the Progress entry says the README lines are not rewrapped, and that
   the kit test red in the implementer's first run was not reproduced (it
   did not recur in 3 more runs of 490 of 490 by the round 3 reviewer, plus
   the two runs inside the coordinator's `update-branch`) and its output was
   not kept. No kit test reads the root README; the likely cause is timing
   under machine load.

## Mutations

Round 3 reviewer, 17 mutants, each on a private `git archive HEAD` copy and
the full suite (974 tests), all killed: the new clause in both wrong forms
and removed; `prev_id_bound_off`; `listnum_off`; `own_tail_charsuffix`;
`_SLOT_TRAIL` without `[`, `*`, all quotes, or the double quote only;
`_SIMILARITY` 0.80 and 0.90; `_MAX_SLOT` 4 and 6; the check wired always ok,
before `names` or at the end. Round 1 and 2 killed the rest (the digit guard,
the tail rules, the article drop, the stops, the dedupe, the fixture counts).
The equivalent or near-equivalent ones (`own_eq_off`, `sim_ge_to_gt`,
`digit_regex_single`) stay. The coordinator re-ran the two new-clause
mutants itself: each fails
`test_invented_lead_in_before_the_own_name_passes`.

## Not checked

- Answer styles from other providers beyond the 38 stored reports.
- Which kit test failed in the implementer's first run (no log).

## Live check

not-needed: `score.py`, its tests, the fixture and the README are not on a
rule-1 path.

## Replay (reviewer, read-only, all 38 reports in `evals/runs/`, 1,439 answers)

Flagged: 65 answers and 116 (id, run) pairs in 17 reports; the fixture's 63
answers and 112 pairs match, plus the 4 pairs of `20261125T095700Z` (all
real inventions). False positives: 0. Flagged answers in a PASS case: none.
Baseline: the baseline's source run has 0 flagged answers, so no case in
`evals/baseline.json` changes status.

## Eval run

- Report: `evals/runs/20261125T115807Z-ollama.json` (ollama, qwen3:8b), made by
  the coordinator in the worktree at 8360831, the merged content (`main` with
  §30 included). `advisor-analysis hashes` exits 0.
- `compare` against `evals/baseline.json` (§30's run, 43/50): 41/50.
  Regressed (2): `tv-sound` and `norvik-fold-brother-gift`. Fixed: none.
- The new `invented` check failed in exactly one case of the 50, and that one
  answer does name products the catalogue does not have:
  `norvik-fold-brother-gift`, "P-123 is the Kestrel Calm 46, cited as EcoFold
  Pro". The case also fails `expected` ("does not cite P-017") on the same
  run.
- Re-runs with `--only tv-sound,norvik-fold-brother-gift`, three times:
  `tv-sound` FAIL, FAIL, PASS (it fails at random on code without this
  change: 4 of its last 6 runs before §31, and again in §30 and §33's
  runs); `norvik-fold-brother-gift` FAIL in 3 of 3, each time on `expected`
  (the answer does not cite P-017) and in 2 of the 3 also on `invented`
  ("P-123 ... cited as Norvik Slim; P-124 ... cited as Norvik Lite", "P-004
  ... cited as Acme Foldable; P-007 ... cited as TechFold Pro"): invented
  names, correctly named by the new check. The case passed once in
  §30's baseline run and failed in that branch's earlier runs, so the
  flip is the case's variation, and the new check only adds a true reason
  to a failure it already had. Not a regression of this change.
- Status flips caused by the check: none (the check never changed a PASS to
  FAIL by itself in any stored report or here).

## For the owner

- `spec.md` B2 does not record your option (a) (a run that ends in the
  cited id's own name, in whole words, is not invented); the decision is in
  round 1's review and the plan's Progress. Amending the spec above its
  marker is yours; it does not block.
- Because of option (a), an invented word put before a real name ("Norvik
  Auralis Home 1 (P-032)") passes. It occurs zero times in the stored data;
  the README says so.
- The replay fixture `tests/fixtures/invented_replay.json` holds answers
  from the eval reports: synthetic catalogue output, no personal data.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run), in the worktree at 8360831: the
  branch update (`merged main`, `verify` green at the merge: 490 kit tests,
  974 pytest) and `npm run check:intent` PASS; the two new-clause mutants
  (each killed); the full eval run, `hashes`, `compare`, the `invented`
  outcome per case, and the three `--only` re-runs above. No mutant of this
  round survives, so none to re-run.
- Verified by the reviewer: `verify` exit 0 and `check:intent` PASS at
  3ad7dee; the 17 mutants; the replay and its false-positive scan; the
  README example and the fixture quote against the original report; two extra
  kit runs; `sdlc:scan --sample-due auto --exclude 35`: "nth attested auto
  change = 10, every 3, sampled: no".
- Taken on trust: none.

---

# Round 1 (history)

# §35 review — Catch an answer that names a product the catalogue does not have

verdict: rework
tier: attested
reviewed-commit: 23688a9
main: b370233
round: 1
sampled: no
run: auto
live-check: not-needed

The verdict is `rework` for two reasons: one finding needs the owner's
decision (finding 1, it adds a spec rule), and the others are mechanical (five
test gaps and a corrupted character). Nothing is CRITICAL or HIGH, so rule 3
does not raise the tier.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the diff is `score.py`, its tests, the fixture, the README and intent files; `cases.py`, `run.py`, the judge and `tracing.py` are untouched |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | one finding (1); one small difference from B1 on stop characters (finding 7, LOW) |
| 4 | Tests prove the behaviour | findings (2 to 5): 6 non-equivalent mutants survive, plus 2 to 3 equivalent ones |
| 5 | Conventions | pass: pure; only `difflib` is new (standard library); no model, no I/O |
| 6 | Numbers in prose | one LOW finding (8) |
| 7 | Documentation | pass: the README bullet is accurate |
| 8 | Guardrails and hygiene | one LOW finding (6) |
| 9 | Repo-specific footguns | none |

## Type check

```
type-check: PASS (intent 35, feature)
  note:  4 file(s), 1433 line(s) changed outside intents/.
```

## Findings

1. **MEDIUM, Needs decision (owner)** `src/advisor/evals/score.py:100-118`
   (`_slot_run`, B1/B2): a real false positive of the rule as specified. In
   `20261124T165359Z-ollama.json`, case `voice-speaker` (status PASS), the
   answer leaks reasoning: "So: Recommend Auralis Home 1 (P-032) at 119
   euros". "So:" ends the walk, "Recommend" is capitalised, so the run is
   "Recommend Auralis Home 1": not the id's own name, not a tail, digits equal,
   but the edit ratio is too low. It is the only false positive across all
   1,239 stored answers and the only flagged answer whose case passed. A real
   run would flip that case PASS to FAIL. Under the spec it is a correct flag
   (B1 drops only The/A/An and list numbers), so removing it adds a spec rule.
   Options: (a, recommended, minimal) in B2 a run that ends in the cited id's
   own name, in whole words (`shown.endswith(" " + own)`), is not invented:
   capitalised lead-ins such as "Recommend", "Consider", "Buy" pass. Replayed
   over all 36 reports it removes exactly this flag and changes nothing else;
   add the answer to `clean` in the fixture (counts stay) and literal tests
   "So: Recommend Auralis Home 1 (P-032)" (passes) and its twin "So:
   Recommend Acme Home 1 (P-032)" (still invented). (b) a stop-list of
   capitalised verbs: brittle, not advised. (c) accept it as a known false
   positive on leaked reasoning text and document it in the README. (d) do
   not read text inside `<think>...</think>`: wider, new scope.
2. **LOW, Needs rework** (T11 vs `score.py:146-147`): mutant
   `prev_id_bound_off` (deleting `if k > 0: lo = max(lo, ids[k - 1].end())`)
   survives; B1 says another cited id is never part of a slot. Add
   `assert [i for i, _ in runs("Acme Foldable P-007 Zorp P-004")] == ["P-007"]`.
3. **LOW, Needs rework** (T10 vs `score.py:115-116`): mutant `listnum_off`
   (the leading-digit pop) survives. Add
   `assert inv("1 Kestrel Air Plus (P-005)") == []`.
4. **LOW, Needs rework** (T6 vs `score.py:154`): mutant `own_tail_charsuffix`
   (`own.endswith(" " + shown)` to `own.endswith(shown)`) survives; the plan
   says T6 kills it and it does not. Add
   `assert runs("Ic Go 13 (P-009)") == [("P-009", "Ic Go 13")]`.
5. **LOW, Needs rework** (T12 vs `score.py:96` `_SLOT_TRAIL`): three mutants
   survive (drop `[`, drop `*`, drop the quotes). Add failing tests for an
   opening mark glued to the id, each with run "Acme Foldable":
   `Acme Foldable [P-004]`, `Acme Foldable **P-004**`, `Acme Foldable "P-004"`.
6. **LOW, Needs rework** `src/advisor/evals/score.py:92` and `:124`: the
   section sign in "(§35)" was written as U+FFFD (bytes EF BF BD). Restore it
   in both places.
7. **LOW** `score.py:106`: the implementer's "a word must end in a letter or
   digit" stop replaces B1's `. ! ? : ; ,` list. The equivalence claim holds
   for the removed set (all non-alphanumeric: dead code), but the rule is
   wider: names ending in `)`, `+`, a trademark sign, `%` or `-` now end the
   walk. Harmless apart from a false negative below; one line in the
   docstring or README would make it explicit. Worth a look.
8. **LOW** `tests/fixtures/invented_replay.json` "note" and the plan: the note
   says `clean` also holds answers that were false positives of earlier
   drafts; `clean` is exactly the 50 answers of `20261124T192816Z-anthropic.json`
   (no own-name-tail and no sentence-break shapes; those are covered by the
   literal tests). The plan's claim that T6 kills the character-suffix mutant
   is wrong (finding 4). Progress says "all 112 pairs but one"; the helper
   flags 113 pairs on 35 reports (112 real). Worth a look.

## Replay (reviewer, over `evals/runs/*.json`, 36 reports, 1,239 answers)

- Flagged: 66 answers and 117 (id, run) pairs in 17 reports. 63 answers /
  112 pairs match the fixture exactly and no fixture entry goes unflagged.
  New report `20261125T095700Z`: 2 answers / 4 pairs, all real inventions
  ("Norvik Slim (P-102)", "Norvik Lite (P-103)", "Aurelis Home 2 (P-002)",
  "Aurelis Home 3 (P-003)"). Plus the one false positive (finding 1).
- True positives: 116 of 117 pairs name a product the catalogue does not have,
  each checked against the normalised catalogue names.
- False negatives found: 2, both in answers that already fail ("HP Envy x360
  (P-025)": the lowercase "x360" ends the walk, by spec; "Budget Laptop
  (L-001)** (P-001)": a parenthetical between name and id).
- Baseline: the baseline's source `20261125T085756Z-ollama.json` has 0 flagged
  answers, so no case in `evals/baseline.json` changes status.
- Performance: all 1,339 case records in 0.12 s; the cost grows with the
  square of a single line of ids (20,000 ids on one 660 KB line: 2.2 s). No
  action needed.

## Mutations

Reviewer: every mutant on a `git archive HEAD` copy, never the worktree, the
full suite each time. Killed: the similarity threshold 0.90 and 0.80 and off,
`_MAX_SLOT` 6, 4 and no cap, the digit guard, own-name tail off and tail by
prefix, the whole-catalogue-name rule, the one-word rule, the article drop
(and case-sensitive), the stops (non-alphanumeric off, spec-set-only, capital
rule, digit start), stripping, the newline bound, dedupe and first-occurrence,
the check wiring (always ok, join, swapped, reason, placed before `names` or at
the end), and three fixture mutations. Survived: the six of findings 2 to 5
(reworks expected to kill them) and equivalent or nearly equivalent ones
(`own_eq_off`, `sim_ge_to_gt` at a ratio of exactly 0.85,
`digit_regex_single`).

## Not checked

- Behaviour on other providers' answer styles beyond the 36 stored reports.
- The eval run (below).

## Live check

not-needed: `score.py`, its tests, the fixture and the README are not on a
rule-1 path.

## Eval run

Owed (`score.py` is in `EVAL_PATHS`). It is made in round 2, after the
rework, on the content that will be merged. The reviewer's offline
prediction: no flip against the baseline on qwen3:8b (the baseline's source
run has no flagged answer). A PASS to FAIL in the new run whose only failing
check is `invented` is read against finding 1.

## Verified myself vs. taken on trust

- Verified myself (Coordinator): `npm run update-branch` merged `main` and
  `verify` was green at the merge (490 kit tests, 972 pytest); this round's
  re-check of the survivors happens after the rework (round 2).
- Verified by the reviewer: `verify` exit 0 (ruff, format, mypy, 972 passed),
  `check:intent` PASS, the full replay, the false-negative scans, the
  mutants and timings above, the equivalence of the dead stop-set removal,
  and the U+FFFD bytes.
- Taken on trust: none.
