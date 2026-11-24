<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §25 plan — Catch an answer that cites a real id under another product's name

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Add a deterministic check, `names`, to `score()` in
`src/advisor/evals/score.py`. It fails when the text next to a cited id
names a different catalogue product and not the cited product itself. Its
reason names the id, the product the id belongs to, and the name the answer
used: "P-009 is the Pelagic Go 13, cited as Auralis Home 1". Also make the
`prices` reason name each product ("price of P-009 (Pelagic Go 13) not
stated"). Together these cover the intent's first two outcomes. The third,
the eval run, is the coordinator's step at review (Validation).

## Design decisions the intent left to the plan

The intent's assumptions left two choices to the plan: a new check or a
stricter `grounded`, and what "next to" means.

- **A new check, `names`, placed right after `grounded`, not a stricter
  `grounded`.** `grounded` keeps its documented meaning ("every cited id
  is in the catalogue", README.md:158; §8 spec line 71). A separate name
  lets labels, `compare` and the viewer tell an invented id from a
  misattributed one.
- **"Next to" means a window around each occurrence of a cited id:** up to
  80 characters on each side, on the same line, and never past the
  previous or next id in the answer. A product name is found in the window
  case-insensitively, with a hyphen read as a space (`catalogue._norm`),
  and only as a whole name (not inside a longer word). Where two names
  overlap, only the longer one counts: "Zephra One" inside "Zephra One
  Max" is not a separate mention.
- **The rule:** for each occurrence of a known cited id, the occurrence is
  a mismatch when its window names at least one other catalogue product
  and does not name the cited product's own name. A window that names no
  product passes, because the intent says not to fail "an answer that
  cites an id with no product name near it". Unknown ids are left to
  `grounded`. The check fails when any occurrence is a mismatch, and each
  mismatched id is reported once.

**Evidence for the window.** A prototype of this rule was run over every
answer in all 17 reports in `evals/runs/` (587 citations of a known id).
In 575 the product's own name was in the window. In 10 there was no name.
In 2 there was only another product's name, and both are the defects the
intent names: `gen-out-of-stock-6` ("Auralis Home 1 (P-009)") and
`gen-out-of-stock-1` ("Norvik Fold (P-112)", now P-112 is the Ostrel
Cube 86). So the rule gives no false positive on the committed runs.
None of the flagged answers is from a 50-case run, so the baseline is not
expected to move.

## Amendment after review round 1 (owner, 2026-11-24: "25 D1(b) D2(b)")

Two decisions from `review.md` round 1, findings 5 and 6, change the
design above:

- **D1 (b): the window after an id stops at the next id's own name.** When
  a catalogue name is followed, after only whitespace and an opening `(`,
  by the next cited id, that name belongs to the next id. It doesn't count
  in the earlier id's window. Other names after the id still count, as
  before. So "the first one (P-001), or Norvik Slate 14 (P-007)" passes:
  Norvik Slate 14 belongs to P-007, and P-001's window has no other name.
  But "Auralis Home 1 (P-009)" still fails P-009, because that name sits
  before P-009 and belongs to it.
- **D2 (b): fold case without changing the text's length.** Replace the
  "lengths differ: do not guess" guard with a lowercase that keeps every
  character's position. A character whose `lower()` is longer than one
  character is kept as it is. All 500 catalogue names are ASCII, so no
  name match is lost, and an answer containing "İ" is still checked.

Tests for both are part of the rework (below the Progress marker, the
implementer's entry says which). Each must kill the mutant that undoes it:
- D1: dropping the next-id-name rule makes the "first one … Norvik Slate
  14" test fail.
- D2: restoring the fail-open guard makes the "İ Auralis Home 1 (P-009)"
  test fail.

## Risks

- **A false failure** on a correct answer. Possible shapes are a comparison
  ("like the Auralis Home 1, the Pelagic Go 13 (P-009) …") or a table row
  that names a product in another cell. The rule passes both as long as the
  cited product's own name is also in the window. The tests cover these
  shapes, and the eval run shows the real rate.
- **Overlapping names.** "Zephra One" lies inside "Zephra One Max", the only
  such pair among the 500 names (checked). Without longest-match, "Zephra
  One Max (P-x)" could count as also naming Zephra One. That doesn't change
  a pass into a fail, but it would put the wrong name in the reason.
- **A test that passes whatever the code does.** Each test asserts
  `ok` and the reason text, and the pair tests use the same answer with
  only the id changed (P-009 vs P-032), so a check that always passes or
  always fails is caught.
- **Stale line citations.** All lines below were read at `98169fc`. The
  main checkout has uncommitted changes, but none touch `score.py`,
  its tests or README's check list.
- **Tests listing check names.** Adding `names` changes the lists asserted
  in `tests/test_evals_score.py:119,122,286,288`. Update them, don't
  delete them.
- **Speed.** 500 names are searched per occurrence (one combined regex,
  built once per `score()` call). That is negligible next to a model call.
- REVIEW-POLICY.md pass 9 (repository-specific footguns) is empty
  (REVIEW-POLICY.md:237-239), so there is no recorded class to guard against.

## Verified against the codebase

Re-read on `main` at `98169fc`.

- `src/advisor/evals/score.py:10` — `from advisor.catalogue import Product, _norm` (`_norm` already imported).
- `src/advisor/evals/score.py:15` — `_ID_RE = re.compile(r"(?<![A-Za-z0-9])P-\d{3}(?!\d)")`, reused to find id occurrences with positions.
- `src/advisor/evals/score.py:29-31` — `cited_ids`: ids once each, in order of first appearance.
- `src/advisor/evals/score.py:87-92` — `def score(case, answer, searches, catalogue) -> list[Check]`.
- `src/advisor/evals/score.py:98-107` — the `grounded` check: `unknown = [i for i in cited if i not in by_id]`; the new check is appended right after it.
- `src/advisor/evals/score.py:111-124` — the `prices` check; line 123 `f"price of {', '.join(unpriced)} not stated"` is the reason to change.
- `src/advisor/catalogue.py:109-110` — `def _norm(text): return text.lower().replace("-", " ")`.
- `src/advisor/data/catalogue.json:118` — P-009 (Pelagic Go 13, €649, in stock); `:445` — P-032 (Auralis Home 1, €119, out of stock); `:1575` — P-112; `:180`, `:194` — Zephra One and Zephra One Max.
- `tests/test_evals_score.py:7` — `CATALOGUE = load_catalogue()`; `:10-11` `verdicts`; `:92` `GOOD = "The Auralis Calm 300 (P-001) costs 189 euros."`.
- `tests/test_evals_score.py:119,122,286,288` — the asserted check-name lists.
- `tests/test_evals_run.py:223` — asserts a superset of names (`>=`), unaffected.
- `tests/test_analysis_view.py:49,120` — a fixed `grounded` row, unaffected.
- `README.md:155-175` — the check list ("Checks (a product is cited by its id …)").
- `scripts/intent-check-lib.mjs:159` — `score.py` is `CORE_CODE`.
- `REVIEW-POLICY.md` "Eval runs": "`src/advisor/evals/score.py`" is in the list of paths that owe a run.
- 500 product names, no duplicates after `_norm`; one name lies inside another (`zephra one` in `zephra one max`), checked by script at `98169fc`.

## Subtasks

1. **The failing-first tests, then the `names` check.** In
   `tests/test_evals_score.py`, add the tests under "Tests" (1–8) and watch
   them fail. In `score.py`, add a pure helper `misnamed(answer, by_id)`
   that returns `(id, own name, names the window gives)` for each
   mismatched id, once, in order of first occurrence. Add the `names` check
   right after `grounded`, with the reason "P-009 is the Pelagic Go 13,
   cited as Auralis Home 1" (several mismatched ids joined with "; ").
   Update the four name lists (`:119,122,286,288`). `npm run verify` green,
   commit.
2. **The `prices` reason names the product.** Test 9 first, then change line
   123 to "price of P-009 (Pelagic Go 13) not stated" (several joined with
   ", "). Verify, commit.
3. **Docs.** Add a **names** bullet after **grounded** in README.md's check
   list, with the window and the rule in one or two lines. Change the
   **prices** bullet only if its wording no longer holds. If the
   `score.py` paragraph in CLAUDE.md or AGENTS.md names the checks, update
   it too. Verify, commit.
4. **Hand over.** Set `status: in-review`. The eval run is owed and made by
   the coordinator at review (Validation), not by the implementer.

## Tests

All in `tests/test_evals_score.py`, against the committed catalogue, no
model. The failing-first tests are 1 and 2.

1. **The reproduction:** `score(Case("gen-out-of-stock-6", q), "…the product page for the Auralis Home 1 (P-009) for any updates…", [], CATALOGUE)` has `names` not ok, with a reason containing "P-009", "Pelagic Go 13" and "Auralis Home 1". It fails if the check is missing, always passes, or the reason drops a part.
2. **The right id passes:** the same answer with P-032 has `names` ok. It fails if the check fails whenever any name is present.
3. **No name nearby passes:** "P-009 costs 649 euros." has `names` ok, as does `GOOD` (own name). It fails if "no own name" alone fails.
4. **Own name and another name both in the window pass:** "Unlike the Auralis Home 1, the Pelagic Go 13 (P-009) is in stock." has `names` ok. It fails if any other name in the window fails.
5. **Name after the id, case and hyphen:** "P-009 – auralis home 1" fails. "auralis-home 1 (P-032)" passes: no catalogue name has a hyphen (checked at `98169fc`), so the hyphen is tested on the answer side. This fails if matching reads only before the id or is case-sensitive.
6. **The window's bounds:** another product's name more than 80 characters before the id, or on the previous line, or before an earlier id, does not count. Each is its own assertion, and each fails if its bound is removed.
7. **Longest match:** "Zephra One Max (<its id>)" passes. "Zephra One (<Zephra One Max's id>)" fails, and its reason says it was cited as Zephra One. This fails if a name is matched inside a longer word or the reason picks the shorter name.
8. **Unknown ids are left to `grounded`:** "Auralis Home 1 (P-999)" has `names` ok and `grounded` not ok. A mismatched id cited twice is reported once. This fails if unknown ids hit `by_id` or the reason repeats.
9. **`prices` reason:** "The Auralis Home 1 (P-009) is great." has `prices` not ok with the reason "price of P-009 (Pelagic Go 13) not stated". This fails if the line-123 change is reverted.
10. **Order:** the four updated name lists put `names` right after `grounded`. This fails if the check moves or is conditional.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (or ROUTE with a reason recorded in review.md).
- **Eval run (owed: `score.py` is in REVIEW-POLICY.md "Eval runs").** The coordinator runs `uv run advisor-eval` on Ollama in the worktree at the reviewed commit, then `uv run advisor-analysis compare <report>` against `evals/baseline.json`. Every flipped case is re-run with `--only` before it is called a regression. Expected: no case flips. Any case that fails `names` is quoted in the review.
- Live check: none. `score.py` and the tests are not on the live-check path list (`src/advisor/cli.py`, `models/`, `tracing.py`, `prompts/`, `infra/`).

## Assumptions I made

- The check's name is `names`. Its exact reason text is as above.
- The 80-character window, same line, bounded by neighbouring ids: chosen from the prototype. A wider window gains nothing on the committed runs and risks counting a name from the previous product in a list.
- A window that names no product passes, as the intent's constraints say.
- Only the `prices` reason is changed. The reasons of `stock`, `expected` and the others keep their ids only (the intent asked for `prices`).
- No new dependency.
- The old run reports in `evals/runs/` are not re-scored. Only new runs carry `names`.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-24 — implementation (all subtasks)

- Commits: `86b55b3` names check, `5d2ccb8` prices reason, then docs and this entry.
- Shipped: `misnamed()` and the `names` check right after `grounded` in `score.py`; the `prices` reason names each product; README check list gains **names**. CLAUDE.md and AGENTS.md do not name the checks, so unchanged.
- Tests: 11 added or changed in `tests/test_evals_score.py` (tests 1-10; the four name lists updated), plus one reason string in `tests/test_evals_run.py:101`. 868 passed.
- Mutations killed: always-pass (tests 1, 5, 6, 7, 8), no window bounds, no line bound (test 6), shortest-name-first (test 7).
- Divergences: `test_evals_run.py` asserted the old `prices` reason and was updated (not in the plan). `misnamed` returns no mismatches if lowercasing changes the answer's length (rare Unicode), rather than guessing positions. Not run: the eval run (the coordinator's).

### 2026-11-24 — round-1 rework

- Changed: D1 (b) (a name right before the next id, with only space and "(" between, belongs to that id and is out of the earlier id's window) and D2 (b) (length-preserving case fold, replacing the fail-open guard) in `misnamed`; README names bullet mentions D1, prices bullet re-wrapped. Tests added for findings 1-4 and for D1 and D2 (6 tests); 874 passed.
- Mutants, each run against the full suite and restored by copy: next-id bound removed (M13) killed by `test_names_next_id_bound`; lookbehind dropped (M4) by `test_names_needs_a_word_boundary_before_a_name`; `_WINDOW = 100` (M20) and `_WINDOW = 60` (M21) by `test_names_window_width_is_80_characters`; `", "` join (M23) by `test_names_joins_several_mismatches_with_semicolons`; D1 rule dropped by `test_names_a_name_just_before_the_next_id_belongs_to_that_id` (and the join test); D2 guard restored by `test_names_folds_case_without_changing_length`.
- Divergences: the review's example for finding 1 ("P-009 costs 649, the Auralis Home 1 is P-032.") puts the name before the next id, so the bound does not exclude it; I used "P-009 costs 649, and P-032 is the Auralis Home 1." instead. The width test measures a name wholly inside the window (starting exactly 80 before the id, or ending exactly 80 after it).

### 2026-11-24 — round-2 rework

- Changed: tests only. `test_names_fold_keeps_every_position` ("İ P-009" + 66 spaces + "Auralis Home 1": the name ends exactly 80 characters after the id) and `test_names_fold_reads_a_hyphen_as_a_space` ("auralis-home 1 (P-009)"). Corrected "7 tests" to 6 in the round-1 entry. 880 tests passed.
- Mutants, run against the full suite and restored by copy: N9 (`text = _norm(answer)`) killed by `test_names_fold_keeps_every_position`; N11 (`c.lower()` in place of `_norm(c)`) killed by `test_names_fold_reads_a_hyphen_as_a_space`.
