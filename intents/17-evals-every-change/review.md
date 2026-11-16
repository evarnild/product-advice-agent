<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §17 review — Run the evals on every change that can move the answers

verdict: rework
tier: reviewed
reviewed-commit: a54cf3f350c846edeefc3a468026a3215310266c
round: 1
sampled: no
run: auto
live-check: owed

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (3) |
| 4 | Tests prove the behaviour, not only pass | findings (2) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1) |
| 7 | Documentation | findings (1) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check

    > product-advice-agent@0.0.0 check:intent
    > node scripts/check-intent.mjs

    type-check: PASS (intent 17, feature)
      note:  11 file(s), 639 line(s) changed outside intents/.
    exit: 0

## Findings

- **HIGH** `src/advisor/evals/baseline.py:87` — the `i in old` guard on "regressed" is not proven. Mutant M18 (`old.get(i, "PASS") == "PASS"`) survives the full suite. With it, a newly added case that FAILs would be reported as "regressed". That turns every new case in §15's set into a false "Needs decision" stop (B6, B7). The test fixtures only add a case that PASSes. Needs rework: in `test_compare_categories_rates_and_no_warnings`, add a case that is new and FAILs, and assert it is in `added` and not in `regressed`.
- **HIGH** `src/advisor/evals/analysis.py:325` — the three-dot `f"{base}...HEAD"` is not proven. Mutant M19 (`..HEAD`) survives. With two dots, once `main` has moved past the branch point, `owes-run` would list `main`'s own changes as this branch's (B1: "its diff touches"). Every `make_repo` test leaves `main` at the branch point. Needs rework: add an `owes-run` test where `main` gains a commit touching a listed path after `work` branches, and assert "not owed".
- **MEDIUM** `.claude/skills/auto/SKILL.md:244-246` — "Read the hash warnings: a run whose `prompt_sha256` … does not match the branch's files is not a run of the reviewed content." `compare` warns when the report differs from the *baseline* (`baseline.py:93-96`). It never compares the report with the *branch's files*. On any prompt or case change the warning always fires, and it cannot tell a stale report from a fresh one. So the spec's Interpretation ("the run's hashes match the branch's files") has no working procedure. The review skill has the same gap at `.claude/skills/review/SKILL.md:80` ("its hashes match"). Needs rework: in both skills, say to compare the report's `cases_sha256`, `prompt_sha256` and `catalogue_sha256` with `sha256sum evals/cases.jsonl src/advisor/prompts/system.md src/advisor/data/catalogue.json` run in the worktree at the reviewed commit. Say that the baseline warnings are expected differences, not this check.
- **MEDIUM** `REVIEW-POLICY.md:145-151`, `.claude/skills/auto/SKILL.md:247-250` — noise. The spec settles it as "report flips, you decide", with tolerance and repeats out of scope. The code follows that: `compare` labels any flip, and I saw no threshold. But neither the policy nor the skills tell the reader that a single run is noisy. The committed baseline shows the risk. Two runs of the same content gave 8/15 (093026Z, the baseline) and 9/15 (093332Z), differing only on `waterproof-camera`. Had 093332Z been chosen, an unchanged re-run would report `waterproof-camera: PASS -> FAIL` and stop `/auto` with "decision needed". Also, the resume table (`auto/SKILL.md:89-101`) sends "decision needed" to the implementer and a new round. It has no path for "owner accepts the regressions" that skips a round. An accepted flake therefore costs one of the three rounds and a fresh, equally noisy run. Needs decision: whether to (a) add a line to the policy and the `## Eval run` reading that single runs vary and a flipped case should be re-run before it is called a regression, and/or (b) add a resume path "regressions accepted → write review.md, no new round". Both go beyond the spec's text.
- **MEDIUM** `intents/17-evals-every-change/metadata.yml:13` — `live_checked: 2026-11-16 by-agent` was recorded on 8b27d7a, before any `review.md` named `## Live check` steps. `intents/README.md:79` defines the gate as "you ran it yourself and saw what `review.md` → `## Live check` said you should". The quoted owner words ("happy so perform the 2 first steps you propose") plausibly cover AC7's "the owner looks at the report". They do not cover the skill procedures below, which have never run with a real model: the `/auto` step 6 eval run, the copy to the main checkout, a compare against a branch and the `/ship` baseline update. With the date set, `check:intent` will not hold the merge for the steps in this report. Needs decision: the owner either confirms the recorded gate covers the `## Live check` steps below, or clears it and records it again after running them.
- **LOW** `.claude/skills/auto/SKILL.md:253` — the new stop `auto_stopped: eval run failed` has no row in the resume table (`:89-101`). It is also missing from the `/auto` stop list in `CLAUDE.md:66-74`. Needs rework: add a row ("eval run failed → once the owner says the cause is cleared, redo the eval-run step for round `auto_round`; no new round", mirroring "re-check mismatch"), and add "an eval run that fails" to CLAUDE.md's list.
- **LOW** `src/advisor/evals/analysis.py:325` — `git diff --name-only` applies rename detection and lists only the destination. Moving a file out of a listed path, such as `src/advisor/prompts/system.md` → `docs/old-prompt.md`, reports "not owed". I reproduced this in a scratch repo; `--no-renames` lists both paths. B1 says "touches any of these paths". Needs rework: pass `--no-renames`, and add a test that moves a file out of a listed path and expects "owed".
- **LOW** `.claude/skills/auto/SKILL.md:247` — "Every case in 'regressed' … is one finding". B7 says "one or more 'regressed' cases make a 'Needs decision …' finding", which is one finding. Needs rework: "One or more cases in 'regressed' make one finding … listing each case".
- **LOW** `intents/17-evals-every-change/plan.md:117-130` (Progress) — the entry names commits 7af1cc0, 240c9a1, 280a2ba, 98f6106 and 84ec629. The branch has 1867933, abf268c, 6e4ef36, 1dcb66f and 358aef1 (it was rebased). It says "evals/baseline.json does not exist" and gives 624→664 tests. I counted 698 pytest and 298 kit tests at a54cf3f (§13/§14/§18 since landed), and subtask 5 has since been done in 03e6f33. Needs rework: append a dated Progress entry (below the marker) with the current SHAs, the baseline commit and the counts. Do not edit the old entry.
- **LOW** `.claude/skills/ship/SKILL.md:67` — the new `## After a complete ship` heading follows a list item with no blank line, and the file ends with an extra blank line. Worth a look.

## Mutants

Each mutant changed one line (M1 removed one list entry), and the full pytest suite ran (698 tests) for each. The kit suite was not re-run per mutant: no mutant touched `scripts/`.

| # | Target | Mutation | Result | Killing test |
| --- | --- | --- | --- | --- |
| M1 | baseline.py:24 | drop `evals/cases.jsonl` from `EVAL_PATHS` | killed | test_evals_baseline::test_policy_path_list_equals_eval_paths |
| M2 | baseline.py:39 | no `\\`→`/` normalisation | killed | test_files_under_listed_directories_owe[src\\advisor\\agent.py] |
| M3 | baseline.py:40 | prefix entries matched exactly | killed | test_files_under_listed_directories_owe (prompts, data, models) |
| M4 | baseline.py:40 | exact entries matched as prefix | killed | test_near_misses_do_not_owe[agent.pyc], [cases.jsonl.bak] |
| M5 | baseline.py:41 | append the raw path | killed | test_files_under_listed_directories_owe[backslash] |
| M6 | baseline.py:50-51 | copy non-string (None) fields | killed | test_baseline_without_catalogue_hash_has_none; cli test_baseline_without_catalogue_hash_writes_none |
| M7 | baseline.py:47 | no `source` | killed | test_baseline_copies_fields; cli test_baseline_writes_fields |
| M8 | baseline.py:58-59 | no dict check | killed | test_check_baseline_rejects_bad_shapes |
| M9 | baseline.py:62 | any status accepted | killed | test_check_baseline_rejects_bad_shapes |
| M10 | baseline.py:87 | regressed only to FAIL (drops ERROR) | killed | test_compare_categories_rates_and_no_warnings |
| M11 | baseline.py:90 | fixed only from FAIL | killed | test_compare_categories_rates_and_no_warnings |
| M12 | baseline.py:95 | never warn | killed | test_compare_warns_once_per_differing_field; cli test_compare_prints_flips_and_exits_0 |
| M13 | baseline.py:99 | new_passed = total | killed | test_compare_categories_rates_and_no_warnings |
| M14 | baseline.py:101 | old_passed = total | killed | test_compare_categories_rates_and_no_warnings |
| M15 | baseline.py:105-106 | added/removed swapped | killed | test_compare_categories_rates_and_no_warnings |
| M16 | baseline.py:125 | warnings not printed | killed | cli test_compare_prints_flips_and_exits_0 |
| M17 | baseline.py:122 | fixed block not printed | killed | cli test_compare_prints_flips_and_exits_0 |
| **M18** | baseline.py:87 | `i in old and old[i] == "PASS"` → `old.get(i, "PASS") == "PASS"` | **SURVIVED** | none (finding 1) |
| **M19** | analysis.py:325 | `...HEAD` → `..HEAD` | **SURVIVED** | none (finding 2) |
| M20 | analysis.py:331 | ignore git's exit code | killed | cli test_owes_run_unknown_base_exits_2 |
| M21 | analysis.py owes-run | exit 1 when owed | killed | cli test_owes_run_owed_lists_matching_paths |
| M22 | analysis.py compare | exit 1 after printing | killed | cli test_compare_prints_flips_and_exits_0 |
| M23 | analysis.py baseline | source = full path | killed | cli test_baseline_writes_fields |
| M24 | analysis.py compare | BaselineError not caught | killed | cli test_compare_missing_or_invalid_file_exits_2_naming_it |
| M25 | analysis.py report read | ReportError not caught | killed | cli test_baseline_invalid_or_missing_report_exits_2 |
| M26 | analysis.py baseline | write-error exit 1 → 0 | not run | the patch text matched 4 places; the write-error path is untested |
| M27 | analysis.py compare | skip check_baseline | killed | cli test_compare_missing_or_invalid_file_exits_2_naming_it |
| M28 | REVIEW-POLICY.md report format | rename `## Eval run` | killed | test_report_format_has_eval_run_after_live_check |
| M29 | analysis.py:332 | git failure → empty list | killed | cli test_owes_run_unknown_base_exits_2 |

For the rework round, the coordinator should re-run M18 (baseline.py:87) and M19 (analysis.py:325); the reworks for findings 1 and 2 should kill them. The rename fix (LOW) needs a new mutant: drop `--no-renames` at analysis.py:325.

**Do the tests prove the behaviour?** Mostly. 26 of 28 mutants that ran were killed. The policy-list test keeps `EVAL_PATHS` and the policy in step. The two survivors are real gaps: an added failing case is unguarded (M18), and so is a `main` that moved (M19).

## Not checked

- The `/auto` step 6 eval-run procedure, the copy to the main checkout's `evals/runs/`, and the `/ship` baseline update, run end to end with a real Ollama model. These are skill text, and only a real coordinator run shows them (live check, rule 3).
- `baseline`'s write-error exit 1 (M26 not run).
- Whether 093026Z, and not 093332Z, was the right baseline to commit. The owner chose it; see the noise finding.

## Live check

- owed: rule 3. The Not-checked item is the skill procedures (`/auto` step 6 eval run, compare, the regression stop, `/ship` baseline update), which only a real model run shows. Spec AC7 also states "live check owed". Rule 1 does not apply (no listed runtime path).
- steps:
  1. In the main checkout on `main` (Ollama running, `qwen3:8b` pulled), check out nothing. In this worktree run `uv run advisor-analysis owes-run --base main`.
  2. Run `uv run advisor-analysis compare evals/runs/20261116T093026Z-ollama.json`, then `uv run advisor-analysis compare evals/runs/20261116T093332Z-ollama.json`.
  3. In a scratch branch or worktree that touches `src/advisor/prompts/system.md` (one word), run `uv run advisor-analysis owes-run --base main`, then `uv run advisor-eval`, then `compare` on the new report.
- you should see:
  1. "not owed (no listed path changed)".
  2. 8/15 against 8/15 with no flips and no warnings, then 9/15 with `fixed (1): waterproof-camera: FAIL -> PASS`. Both exit 0.
  3. "owed: the diff touches src/advisor/prompts/system.md", a report in `evals/runs/`, and `compare` printing both pass rates, any flips, and a `prompt_sha256 differs` warning. Then confirm the existing `live_checked` covers this, or record it again (finding 5).

## Eval run

- not owed (no listed path): `uv run advisor-analysis owes-run --base main` at a54cf3f printed "not owed (no listed path changed)". The diff touches `src/advisor/evals/analysis.py` and `baseline.py`, neither listed.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/17-evals-every-change` at a54cf3f; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 298 tests, 0 fail; "All
  checks passed!"; "159 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "698 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "11 file(s), 639
  line(s)". Matches.
- **Coordinator, re-run:** M18 (`baseline.py:87`) SURVIVED ("698 passed");
  M19 (`analysis.py:325`) SURVIVED ("698 passed"). Matches the reviewer.
- **Coordinator, correction:** the reviewer's prose said "400 pytest" in two
  places; its own verify line and the re-run give 698, corrected above.

**Reviewer:**
- Verified myself: `npm run verify` exit 0 (kit 298/298, ruff "All checks passed!", 159 files formatted, mypy "no issues found in 29 source files", pytest 698 passed). `npm run check:intent` exit 0, PASS.
- Verified myself: `evals/baseline.json` hashes equal `sha256` of the branch's `evals/cases.jsonl` (2b6210…), `src/advisor/prompts/system.md` (a22c1c…) and `src/advisor/data/catalogue.json` (c2e56cb2…). `baseline` regenerated from `20261116T093026Z-ollama.json` into a scratch path is byte-identical to the committed file, apart from line endings. `compare` of 093026Z → 8/15, no flips, no warnings, exit 0. `compare` of 093332Z → 9/15, fixed `waterproof-camera`, exit 0. A missing report, a missing baseline and an invalid baseline each exit 2 naming the file. A non-report `baseline` input exits 2.
- Verified myself: 29 mutants (table above); the git rename behaviour, in a scratch repo; `sdlc:scan --sample-due auto --exclude 17` → "sampled: no". `intents/17-…/spec.md` and the plan above the Progress marker are unchanged against main: only metadata.yml and the Progress entry differ.
- Verified myself: no secret or user data in the diff. `baseline.json` holds case ids and statuses only. The git subprocess takes the `--base` argument as an argv element; no shell is involved.
- Taken on trust: that 093026Z and 093332Z were made by `advisor-eval` on Ollama `qwen3:8b` at this content (their hashes match, but who ran them and at which commit is not recorded). Also the owner's words behind `live_checked` and `auto_authorized`.
