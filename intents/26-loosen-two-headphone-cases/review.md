<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §26 review — Two headphone cases fail correct answers

verdict: attest
tier: attested
reviewed-commit: e65b324
main: 6ebf3c6
round: 2
sampled: no
run: auto
live-check: not-needed

This is a short round. Main was merged into the branch after round 1:
§27 delivered, origin's §23, a new `evals/baseline.json`, and intent
bookkeeping. The branch's own change is byte-identical to round 1's.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent match | pass: same change as round 1 |
| 2 | Type check | pass |
| 3 | Behaviour, plus the eval run | findings (1 MEDIUM, about the eval run's hash) |
| 4 | Tests prove the behaviour | pass, as round 1 (survivors M5, M7 and M9 still stand as LOW) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass |
| 8 | Hygiene | pass |
| 9 | Footguns | finding: a candidate for the list (the MEDIUM) |

## Type check
```
type-check: PASS (intent 26, adjustment)
  note:  2 file(s), 7 line(s) changed outside intents/.
```

- **The change is round 1's.** `git diff main...HEAD` has the same
  `evals/cases.jsonl` blob pair (`14918ef..f804951`, lines 1 and 28) and the
  same test blob pair (`854f1c6..23940ab`, lines 44-45).
- **ccb4793 is the automatic merge.** `git merge-tree --write-tree` on its
  parents gives `34632eed…`, which equals its tree, and `git show --cc` is
  empty.
- **Nothing merged from main touches the cases**, the scorer, the catalogue
  or the prompt.
- **Both cases pass the new baseline's run** (§27's,
  `20261124T183001Z`) under the old and the new definitions. So after the
  merge, a qwen run flips neither case because of this edit.

## Findings
- **MEDIUM** `evals/cases.jsonl` (the worktree's working copy) and the
  run `20261124T195935Z-ollama.json` — `git ls-files --eol` reports `i/lf
  w/mixed`: the two edited lines end in LF and the other 48 in CRLF
  (`core.autocrlf=true`, no `.gitattributes`). The run hashes raw bytes
  (`run.py:310`), so it recorded `cases_sha256` 20ba79fc. `main`'s CRLF
  checkout of the same blob hashes to d5f5e275. A baseline written from
  this run makes later `compare` runs on `main` warn "cases_sha256
  differs" although the cases are the same.
  - Not new: the §22 and §27 baselines differ only by line endings too.
  - The committed blob is right, so no rework on this branch. Worth a
    look: the cure is a separate change (hash normalised text in
    `run.py`, or a `.gitattributes` for `evals/*.jsonl`) and a footgun-list
    entry.
- Round 1's four LOW findings stand unchanged.

## Not checked
- Round 1's mutants, not re-run: the change is byte-identical (same blobs).
- §27's adapter behaviour, which came in through the merge: it was
  reviewed, live-checked and delivered as §27.

## Live check
- not needed: the branch's own diff touches no rule-1 path and not
  `.claude/settings.json`. `anthropic_model.py` arrived only through the
  merge of main (§27, already live-checked).

## Eval run
- Report `evals/runs/20261124T195935Z-ollama.json` (round 1), ollama /
  qwen3:8b, made at c924ad5.
  - The changed files' content is the same at e65b324.
  - `prompt_sha256` c2a38987 and `catalogue_sha256` c2e56cb2 equal the
    files at e65b324.
  - `cases_sha256` 20ba79fc equals the worktree file's bytes. Those are
    mixed line endings (see the MEDIUM).
- `compare` (round 1): 39/50 against 38/50. Regressed 0, fixed 1
  (`gaming-monitor`).

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at e65b324:
  - `npm run verify`: exit 0, 863 passed.
  - `npm run check:intent`: PASS.
  - The diff's blob pairs, the merge-tree reproduction and the empty `--cc`.
  - `git diff --stat 40c447d 6ebf3c6`.
  - Re-scores of four run reports under the old and new definitions.
  - The line-ending hashes.
  - No mutation; clean.
- **Coordinator, re-run**, at e65b324:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **863 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 26, adjustment)`, which matches.
  - `git merge-tree --write-tree` on ccb4793's parents: `34632eed42ed5ce8279b040d6843edea98560785`, equal to `ccb4793^{tree}`, which matches.
  - Content hashes at e65b324: cases 20ba79fc, prompt c2a38987, catalogue c2e56cb2.
  - `npm run sdlc:scan -- --sample-due auto --exclude 26`: "nth attested auto change = 8, every 3, sampled: no".
  - No surviving mutant is new this round, and the change is unchanged, so there are no mutants to re-run.
- Taken on trust: that the run files are unmodified model outputs.

---

# Round 1

verdict: attest
tier: attested
reviewed-commit: c924ad5
main: 40c447d
round: 1
sampled: no
run: auto
live-check: not-needed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent match | pass. Two edits beyond the case lines; both are within the intent (below) |
| 2 | Type check | pass |
| 3 | Behaviour against the intent | pass: every outcome re-derived |
| 4 | Tests prove the behaviour | findings (1 LOW): case 1 is pinned; case 28's values are proven by re-scoring, not by the suite |
| 5 | Conventions | pass: no core code, no model call, no dependency |
| 6 | Numbers in prose | findings (1 LOW) |
| 7 | Documentation | pass |
| 8 | Hygiene | pass |
| 9 | Footguns | pass (list empty) |

## Type check
```
type-check: PASS (intent 26, adjustment)
  note:  2 file(s), 7 line(s) changed outside intents/.
```

The two edits beyond the case lines are within the intent:
1. **`tests/test_evals_cases.py:44-45`.** The old assertion pinned
   `nc.expect_ids == {"P-005","P-001"}`, exactly what the intent removes, so
   `verify` would be red without the change. The new lines pin the intent's
   change: no `expect_ids`, plus both properties. This is not core code.
2. **Case 28's `note`.** The intent says "update the note", and
   `test_expect_search_is_the_notes_probe_for_every_new_case` requires the
   note's probe to equal `expect_search`. The new probe still passes the
   coverage check for no-match: no product contains "transparen" or
   "ambient".

Intent outcomes, re-scored against the branch's cases:
- Haiku (`20261124T192816Z-anthropic.json`) and qwen3:8b
  (`20261121T165658Z-ollama.json`, the baseline's source) pass both cases.
- `nc-headphones-under-200` still fails an answer that cites P-003, a
  product that doesn't fit (P-007 over €200, P-002 without noise
  cancelling), or nothing. All 8 fitting products say "noise cancel…".
- Case 28 still fails a search without a transparency word, a right
  keyword above €200, a right keyword in the wrong category, and no
  search.

## Findings
- **LOW** `evals/cases.jsonl:28` — nothing in the suite pins case 28's new
  keywords: M5 (the whole edit reverted), M7 (`"ambient"` dropped) and M9
  (`"hi fi"` added) survive. Re-scoring proves them, as for the other 48
  data cases. Worth a look.
- **LOW** `evals/cases.jsonl:28` — `"ambient"` and the stem `"transparen"`
  also pass searches that don't ask for the feature:
  `["ambient noise cancelling"]` and `["transparent case"]` both pass.
  The intent chose these words deliberately. Worth a look.
- **LOW** `intents/26-loosen-two-headphone-cases/intent.md:78` — "Blast
  radius: 1 file … 2 lines" is stale. It's 2 files and 7 lines outside
  `intents/`, still well within an adjustment. Worth a look.
- **LOW** `evals/cases.jsonl:28` — the note's parenthetical now sits inside
  `NOTE_RE`'s `source` group. Only a truthiness check reads it today. Worth
  a look.

## Not checked
- How later models word their searches, beyond the synonyms tried
  ("pass-through", "hear-through", "awareness" and "see-through" fail, as
  the intent's word list implies).
- Old run reports and labels: left untouched on purpose (docs/decisions/0003).

## Live check
- not needed: the diff touches no rule-1 path and not
  `.claude/settings.json`. It changes eval data and one test assertion;
  the eval run below shows how the cases score real output.

## Eval run
- Report `evals/runs/20261124T195935Z-ollama.json` (copied to the main
  checkout). Provider ollama, model qwen3:8b, made in the worktree at
  c924ad5.
- Content check: its `cases_sha256` 20ba79fc, `prompt_sha256` c2a38987 and
  `catalogue_sha256` c2e56cb2 equal the sha256 of the worktree's files.
- `advisor-analysis compare`: baseline 38/50, this run **39/50**. Regressed
  0. Fixed 1 (`gaming-monitor`). Added 0, removed 0.
- The `cases_sha256` warning is expected: this change edits the cases. The
  baseline moves after the merge.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at c924ad5:
  - `npm run verify`: exit 0, 860 passed.
  - `npm run check:intent`: PASS.
  - `owes-run`: owed (`evals/cases.jsonl`).
  - Re-scores as above.
  - Mutants: M1–M4 and M6 killed; M5, M7 and M9 survived; M8 equivalent.
  - `git diff main...HEAD -- evals/cases.jsonl` has hunks at lines 1 and 28 only.
  - Clean worktree at the end.
- **Coordinator, re-run**, at c924ad5:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **860 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 26, adjustment)`, which matches.
  - Surviving mutants against the full suite: M5, M7 and M9 each **survived**, 860 passed, which matches. Restored by copy; `cmp` was identical; `git status --short` was clean.
  - The eval run and `compare`, as above.
  - `npm run sdlc:scan -- --sample-due auto --exclude 26`: "nth attested auto change = 7, every 3, sampled: no".
- Taken on trust: that the two run files are the unmodified outputs of the named models.
