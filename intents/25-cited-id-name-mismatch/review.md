<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §25 review — Catch an answer that cites a real id under another product's name

verdict: rework
tier: attested
reviewed-commit: 703921b
main: 5f7a773
round: 1
sampled: yes
run: auto
live-check: not-needed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass, with two unplanned items (findings 5, 6) and an edit to a file the plan didn't list (finding 9) |
| 2 | Type check | pass |
| 3 | Behaviour against the intent | findings (1 MEDIUM: a false-positive shape the plan doesn't name) |
| 4 | Tests prove behaviour | findings (4 Needs rework; survivors below) |
| 5 | Conventions | pass: `score.py` stays pure, no new imports or dependencies |
| 6 | Numbers in prose | pass: the plan's 587/575/10/2 reproduced; the README's 80 is `_WINDOW` |
| 7 | Documentation | pass: README has a **names** bullet; CLAUDE.md and AGENTS.md name no checks |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass (list empty) |

## Type check
```
type-check: PASS (intent 25, fix)
  note:  4 file(s), 159 line(s) changed outside intents/.
```

Intent outcomes hold:
- `gen-out-of-stock-6`'s real answer (from `evals/runs/20261113T072503Z-ollama.json`) fails `names` with "P-009 is the Pelagic Go 13, cited as Auralis Home 1". Its `prices` reason is "price of P-009 (Pelagic Go 13) not stated".
- The same answer with P-032 passes.
- `gen-out-of-stock-1` fails with "P-112 is the Ostrel Cube 86, cited as Norvik Fold".
- README documents the check (README.md:159-164).

## Findings
1. **HIGH** `tests/test_evals_score.py` (`test_names_window_bounds`) — the
   next-id bound (`score.py:70-71`) is untested. Mutant M13, which deletes
   it, survives the full suite, although plan test 6 says each bound's test
   fails when the bound is removed. Needs rework: add an assertion that
   fails without it, e.g. `"P-009 costs 649, the Auralis Home 1 is
   P-032."` passes `names`.
2. **HIGH** `tests/test_evals_score.py` (`test_names_longest_name_wins`) —
   "a whole name, not inside a longer word" is tested on the right side
   only. Mutant M4, which drops the lookbehind `(?<![a-z0-9])`
   (`score.py:55`), survives. Needs rework: add e.g. `"MegaAuralis Home 1
   (P-009)"` passes `names` (plan test 7).
3. **MEDIUM** `tests/test_evals_score.py` — the 80-character width that the
   plan and README state is not pinned: M20 (`_WINDOW = 100`) and M21
   (`_WINDOW = 60`) survive. Needs rework: add boundary assertions, a name
   ending exactly 80 characters before the id that counts and one at 81
   that doesn't, and the same after the id.
4. **MEDIUM** `tests/test_evals_score.py` — the `"; "` join of several
   mismatched ids (plan subtask 1) is untested, and M23 survives. Needs
   rework: a test with two misnamed ids that asserts the exact reason.
5. **MEDIUM** `src/advisor/evals/score.py:62-71` — a false-positive shape
   the plan's risks don't name. When an id has no name of its own nearby,
   the next product's name, written after it, counts against it.
   - Coordinator probe: `misnamed("the first one (P-001), or Norvik Slate
     14 (P-007)")` returns `P-001 … cited as Norvik Slate 14`.
   - It occurs once in a committed-content run (`20261124T165359Z`,
     qwen3:4b, `laptop-husband-work-1000`, leaked thinking text). That case
     already fails other checks, so it doesn't flip.
   - Needs decision: accept it as a known false positive and record it in
     the plan, or narrow the window (e.g. stop the after-id side at a name
     that directly precedes the next id). Narrowing changes the plan's
     window rule.
6. **MEDIUM** `src/advisor/evals/score.py:49-50` — the Unicode length guard
   is not in the plan and is untested (M2 survives). It never reports at
   wrong offsets, but it fails open for the whole answer: one "İ" (U+0130)
   anywhere makes `names` pass.
   - Coordinator probe: `misnamed("İ Auralis Home 1 (P-009)")` returns
     `[]`; without the "İ" it returns the P-009 mismatch.
   - All 500 catalogue names are ASCII, so a length-preserving fold would
     keep the check working.
   - Needs decision: keep the fail-open guard and pin it with a test, or
     replace it with a length-preserving fold. Either way, record it in the
     plan.
7. **LOW** `src/advisor/evals/score.py:159` — the passing reason ("every
   cited id sits with its own name or none") is not in the plan, and no
   test pins it (M25 survives). The text is accurate. Worth a look.
8. **LOW** `src/advisor/evals/score.py:72,77,158` — M14/M15 (a name
   straddling the 80-character edge), M19 (duplicate names in the reason)
   and M24 (the join of several names) survive. These are small edge and
   reason details. Worth a look.
9. **LOW** `tests/test_evals_run.py:101` — this edit is outside the plan's
   file list but forced by the planned `prices` reason (M26 is killed by
   it). The plan's verified-lines list missed the assertion. Worth a look.

Nit: README.md:165, the reflowed prices bullet runs past the paragraph
width.

## Not checked
- Answers with Unicode hyphens (U+2010, U+2011) or no-break spaces inside
  product names. `_norm` folds only ASCII "-", so "Auralis‑Home 1" would
  not match. Not probed.
- How the label viewer and `compare` show the new check in a live run.
  Their tests are unchanged and green.
- M8 and M9 against the full suite. The reviewer's full-suite rerun was
  stopped for low memory, so it ran them in-process against
  `test_evals_score.py` only; both were killed.
- Mutants M1 (the early return) and M29 (`re.escape`): equivalent on
  today's catalogue. They survive and need no test.

## Live check
- not needed: the diff touches no rule-1 path (`cli.py`, `models/`,
  `tracing.py`, `prompts/`, `infra/`) and not `.claude/settings.json`. How
  the check scores real model output is answered by the eval run below.

## Eval run
- Report `evals/runs/20261124T174837Z-ollama.json` (copied to the main
  checkout). Provider ollama, model qwen3:8b, made in the worktree at
  703921b. It started 17:48:37Z, after the commit at 17:48:05Z.
- Content check: its `cases_sha256` a81f06ad, `prompt_sha256` c2a38987 and
  `catalogue_sha256` c2e56cb2 equal the sha256 of the worktree's
  `evals/cases.jsonl`, `src/advisor/prompts/system.md` and
  `src/advisor/data/catalogue.json`.
- `advisor-analysis compare`: baseline 38/50, this run **40/50**. Regressed
  0. Fixed 2 (`gaming-monitor`, `tv-sound`). Added 0, removed 0.
- Warning: `cases_sha256` differs from the baseline's (b7a88ce6). The
  committed `evals/cases.jsonl` on `main` hashes to b7a88ce6, so the
  difference is the worktree's CRLF checkout of the same content, not a
  changed case.
- The `names` check failed on **no case** in this run. No regression, so no
  `--only` re-run was needed.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 703921b:
  - `npm run verify`: exit 0, 868 passed.
  - `npm run check:intent`: PASS.
  - `owes-run`: owed (`src/advisor/evals/score.py`).
  - Intent outcomes scored against the real run report.
  - The plan's citation counts recomputed.
  - Catalogue facts: 500 distinct names, ASCII only, no hyphens, one nested pair.
  - Mutants M1–M30, results as above. Restored by byte copy; `git status --short` clean.
- **Coordinator, re-run**, at 703921b:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **868 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 25, fix)`, which matches.
  - Every mutant the review lists as surviving, against the full suite (868 tests each): M1, M2, M4, M13, M14, M15, M19, M20, M21, M23, M24, M25 and M29 all **survived**, matching the reviewer. Restored by copy; `cmp` was identical; `git status --short` was clean.
  - Probes for findings 5 and 6, results quoted in the findings.
  - The eval run and `compare`, as above.
  - `npm run sdlc:scan -- --sample-due auto --exclude 25`: "sampled: yes".
- Taken on trust: nothing from the implementer. Its "868 passed" and its killed mutants match.
