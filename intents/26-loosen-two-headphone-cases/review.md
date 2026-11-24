<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §26 review — Two headphone cases fail correct answers

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
