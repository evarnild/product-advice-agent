<!-- generated-by: product-advice-agent/review@0.2.0 -->
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
