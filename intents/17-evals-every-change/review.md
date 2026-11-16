<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §17 review — Run the evals on every change that can move the answers

verdict: escalate
tier: reviewed
reviewed-commit: 8079a199fb2476b7c134151c1b7d834b3e91db9b
round: 3
sampled: no
run: auto
live-check: owed

## Resolution of round 2

| R2 finding | Resolution | Checked |
| --- | --- | --- |
| MEDIUM auto/SKILL.md:96, the regression row never writes review.md on rework, and has no new-session clause | Row at auto/SKILL.md:96: "write round `auto_round`'s `review.md` on both answers; **no new round** for it. Accepted: name the regressions as accepted, and go on from its verdict. Rework: verdict `rework`, with the regression finding and the owner's answer, then go on as "decision needed" (a **new round** `auto_round` + 1). If the reviewer's report is not in this conversation (a new session), redo the review as the same round, then the re-check and the eval compare" | Resolved. It matches step 5.4 ("every round writes review.md") and the re-check-mismatch row (:95), whose clause it copies and extends to the eval compare |
| LOW, Needs decision: re-run unclear (how, which report, which baseline) | Owner: "yes to the 17 re-run recommendation". Written in REVIEW-POLICY.md:152-160 ("A single run is noisy"), the `## Eval run` template (REVIEW-POLICY.md:286-291), auto/SKILL.md:252-265 (steps 6.4 and 6.5) and review/SKILL.md:84-89 and :123-127. All of them say: only the coordinator re-runs, with `uv run advisor-eval --only <flipped ids>`; a case is a regression only if it fails again; the full run stays the named report and the baseline source; the re-run is evidence only, and its "removed" lines are expected | Resolved, all four places. Order in auto step 6: compare (3), re-run (4), finding and stop (5), run failed (6). review/SKILL.md now says "the coordinator (never a reviewer agent, which calls no model)" |
| LOW, worth a look: `eval regressions, decision needed` contains `decision needed` | Stop renamed `auto_stopped: eval regressions` (auto/SKILL.md:263, row :96) | Resolved. A grep of `.claude/`, CLAUDE.md, REVIEW-POLICY.md, intents/README.md, sdlc.md, scripts/ and docs/ finds no "eval regressions, decision needed" outside this intent's own history. No row name is a substring of another |

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. `git diff main...HEAD -- intents/17-evals-every-change/spec.md` is empty. The round-3 plan.md change is a single hunk `@@ -173,0 +174,21 @@`, below `## Progress` (plan.md:109). Two points the owner sees at the diff read: (a) the stop name `eval regressions` differs from B7's literal parenthetical `(decision needed)`; (b) spec "Out of scope" lists "repeats per case", and the `--only` re-run of flipped cases is a narrow repeat. Both came from owner decisions (round 1 (b), round 2 re-run rule), so neither is a finding (see LOW 1) |
| 2 | Type check | expected FAIL, owed live check only (output below) |
| 3 | Behaviour against the spec | pass. Eval-run check: not owed (below). Skill text is coherent; three wording points are worth a look |
| 4 | Tests prove the behaviour | pass. Round 3 changes no code. The regression sample M18, M19 and M30 is still killed |
| 5 | Conventions | pass. No model, network or Langfuse call; temp git repos only |
| 6 | Numbers in prose | pass. The round-3 Progress entry quotes no counts. The claim "kit 298, pytest 700" is reproduced |
| 7 | Documentation | pass. CLAUDE.md's stop list covers the new stop under "a 'Needs decision:' finding" and has "an eval run that fails". README "Eval runs" is unchanged and still accurate |
| 8 | Guardrails and hygiene | pass. Text only; no secrets |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check

    > product-advice-agent@0.0.0 check:intent
    > node scripts/check-intent.mjs

    type-check: FAIL (intent 17, feature)
      error: A live check is owed and not recorded. Do the steps in intents/17-evals-every-change/review.md → ## Live check, then set live_checked: <date> in intents/17-evals-every-change/metadata.yml.
      note:  11 file(s), 719 line(s) changed outside intents/.
    exit: 1

The only error is the owed live check (`live_checked` was cleared in 59cfe99). That is the owner's to clear, not a rework finding. The line count went from 699 to 719. That is the round-3 net change outside intents/: +36 −16 across auto/SKILL.md, review/SKILL.md and REVIEW-POLICY.md.

## Findings

- **LOW, worth a look** `.claude/skills/auto/SKILL.md:261-263` against `:272-275`. Step 7 says "Stop on any 'Needs decision:' finding, with `auto_stopped: decision needed`". Step 6.5 makes the eval regression a "Needs decision:" finding that stops as `eval regressions` instead. Step 7 does not mention the exception, and B7's parenthetical still says `decision needed`. If a round has both kinds of decision, the eval stop comes first, because step 6 runs before review.md. On "accepted", the row then "goes on from its verdict" and stops again as `decision needed`. That works, but nothing says so. Suggested fix: one clause in step 7, "(regressions from the eval run stop as `eval regressions`, step 6)". The owner can also confirm the renamed stop against B7 at the diff read.
- **LOW, worth a look** `.claude/skills/auto/SKILL.md:96`, the new-session clause "then the re-check and the eval compare". It does not say whether step 6.4's `--only` re-run is made again or its earlier report reused. The full report is copied to the main checkout's `evals/runs/`; step 6.2 says nothing about copying the `--only` report. A fresh re-run is another noisy draw and could contradict the answer the owner already gave. Suggested fix: "reuse the `--only` report in the worktree's `evals/runs/`; re-run only if it is gone".
- **LOW, worth a look** `REVIEW-POLICY.md:155`, `auto/SKILL.md:253-254`, `review/SKILL.md:86`: `--only <flipped ids>` does not say how to separate the ids. `run.py:170` takes a "comma-separated" list. With space-separated ids, argparse exits 2 on unrecognised arguments; that is harmless, but it costs a retry. Suggested fix: write `--only <id1>,<id2>`. Also, "fails again" is best read as FAIL or ERROR, matching "regressed" (PASS to FAIL or ERROR).

## Mutants

Each mutant changed one line. A check that `git diff --quiet` returned non-zero came first, then the full pytest suite (700), then a restore by copy. The kit suite was not re-run per mutant: no mutant touched `scripts/`.

| # | Target | Mutation | Result | Killing test |
| --- | --- | --- | --- | --- |
| M18 | baseline.py:85 (the `regressed` comprehension; earlier rounds cited it as :87) | `if i in old and old[i] == "PASS"` → `if old.get(i, "PASS") == "PASS"` | killed (1 failed, 699 passed) | test_evals_baseline::test_compare_categories_rates_and_no_warnings |
| M19 | analysis.py:325 | `f"{base}...HEAD"` → `f"{base}..HEAD"` | killed (1 failed, 699 passed) | test_analysis_baseline_cli::test_owes_run_ignores_changes_main_made_after_branching |
| M30 | analysis.py:325 | drop `"--no-renames"` | killed (1 failed, 699 passed) | test_analysis_baseline_cli::test_owes_run_owed_when_a_file_moves_out_of_a_listed_path |

None survived. Round 3 changed no production line, so no new mutant applies. No rework is expected to kill anything.

**Do the tests prove the behaviour?** For the code, yes: the sample confirms that the round-1 and round-2 kills still hold. Round 3 is skill and policy text that no test exercises. Only the live check, or a real `/auto` regression stop, shows it.

## Not checked

- The `/auto` step 6 eval run, the `--only` re-run, the `eval regressions` stop and both resume branches, the `eval run failed` resume, and the `/ship` baseline update, run end to end with a real Ollama model. That is the live check (rule 3).
- The behaviour of `advisor-eval --only` with a real model, and the shape of its report. I read `run.py:222-227` (it filters the cases) but did not run it. The "removed" claim comes from round 2's trimmed copy, which I did not reproduce in this round.
- M26: `baseline`'s write-error exit is still untested (carried from round 1).
- Mutants M1–M17 and M20–M29: their code has not changed since round 1, and they were not re-run.

## Live check

- **owed:** rule 3. The skill procedures only show in a real model run (spec AC7: "live check owed").
- **steps:**
  1. With Ollama running and `qwen3:8b` pulled, in `C:/Users/eric/src/product-advice-agent-wt/17-evals-every-change`, run `uv run advisor-analysis owes-run --base main`.
  2. In the same worktree, run `uv run advisor-analysis compare evals/runs/20261116T093026Z-ollama.json`, then `uv run advisor-analysis compare evals/runs/20261116T093332Z-ollama.json`.
  3. In a scratch branch or worktree off this branch, change one word of `src/advisor/prompts/system.md` and commit it. Then run `uv run advisor-analysis owes-run --base main`, then `uv run advisor-eval`, then `uv run advisor-analysis compare <new report>`. Compare the report's three `*_sha256` values with `sha256sum evals/cases.jsonl src/advisor/prompts/system.md src/advisor/data/catalogue.json` run there.
  4. If step 3 shows any case under "regressed", re-run those cases with `uv run advisor-eval --only <id1>,<id2>` (comma-separated), then run `compare` on that report too.
  5. Throw the scratch branch or worktree away.
- **you should see:**
  1. "not owed (no listed path changed)", exit 0.
  2. First 8/15 against 8/15, with no flips and no warnings. Then 9/15 with `fixed (1): waterproof-camera: FAIL -> PASS`. Both exit 0.
  3. "owed: the diff touches src/advisor/prompts/system.md", then a new report in `evals/runs/`. `compare` prints both pass rates, any flips and a `prompt_sha256 differs` warning. The report's `prompt_sha256` equals the scratch file's sha256, not the baseline's.
  4. A report holding only the named cases. `compare` shows them, and every other case appears under "removed". Under the rule, that is expected. A case that FAILs or ERRORs again is a regression; one that PASSes is noise. If satisfied, record `live_checked`.

## Eval run

- not owed (no listed path): at 8079a19, `uv run advisor-analysis owes-run --base main` printed "not owed (no listed path changed)", exit 0. The round-3 diff touches only `.claude/skills/auto/SKILL.md`, `.claude/skills/review/SKILL.md`, `REVIEW-POLICY.md` and the intent folder.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/17-evals-every-change` at 8079a19; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 298 tests, 0 fail; "All
  checks passed!"; "160 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "700 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "11 file(s), 719 line(s)". Matches.
- **Coordinator, re-run:** M18, M19, M30 each KILLED ("1 failed, 699
  passed") by the test the reviewer names. Matches.
- **Coordinator, stamp:** the stamp version is copied from
  `.claude/skills/review/SKILL.md` (`review@0.2.0`); the reviewer left a
  placeholder.

**Reviewer:**
- **Verified myself** (in the worktree, at 8079a199fb2476b7c134151c1b7d834b3e91db9b; HEAD was not moved and nothing was checked out):
  - `npm run verify`, exit 0:
    - kit "ℹ tests 298 / pass 298 / fail 0";
    - ruff "All checks passed!" and "160 files already formatted";
    - mypy "Success: no issues found in 29 source files";
    - pytest "700 passed".
    - This matches the implementer's claim.
  - `npm run check:intent`, exit 1. Its only error is the owed live check ("11 file(s), 719 line(s)").
  - The three mutants in the table, each run through a scratch harness: copy backup, assert the change applied, full pytest, restore by copy. `git status --short` was empty after each and at the end.
  - Diffs:
    - read `8698387..HEAD` in full;
    - the spec diff against main is empty;
    - plan.md changes only at +174..194, below `## Progress` (:109);
    - metadata.yml only sets `auto_round: 3`.
  - Read the whole of auto/SKILL.md: the resume table, steps 5 to 9, and the stop rules. Also read REVIEW-POLICY.md "Eval runs", review/SKILL.md steps 3 and 4, CLAUDE.md's /auto stop list and the ship skill's baseline section. Grepped for the old stop name; none left.
  - `run.py:170,222-227`: `--only` is comma-separated, and unknown ids exit 2.
  - `sdlc:scan --sample-due auto --exclude 17` gives "sampled: no".
  - Main and push state:
    - `main` is 59ba1d0; the merge base is b2e2815, and main's own changes since then are only in `intents/22-search-that-scales/`;
    - nothing was pushed: there is no `origin/feat/17-evals-every-change`, and `git branch -r` shows only origin/main.
- **Taken on trust:**
  - That the owner's "yes to the 17 re-run recommendation" covers the wording as written, including the rename to `eval regressions`. That rename followed a round-2 "worth a look", not an explicit owner decision.
  - Who made 093026Z and 093332Z, and at which commit (carried over).
# Round 2 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 232900a03b8debb50c6280ef7298a409bc61c4c6
- round: 2
- sampled: no
- run: auto
- live-check: owed

### Resolution of round 1

| R1 finding | Resolution | Checked |
| --- | --- | --- |
| HIGH baseline.py:87 (M18 survived) | `test_compare_categories_rates_and_no_warnings` adds `("newfail","FAIL")` and asserts it is in `added` and not in `regressed` (tests/test_evals_baseline.py:96-111) | M18 killed (KeyError 'newfail'). The variant M18b, which uses `.get` with no KeyError, is killed by the assertion on `regressed` |
| HIGH analysis.py:325 (M19 survived) | new `test_owes_run_ignores_changes_main_made_after_branching` (tests/test_analysis_baseline_cli.py:131) | M19 killed by that test |
| MEDIUM hash-check procedure | auto/SKILL.md:246-251 and review/SKILL.md:80-84 name the three hash fields and the three files, at the reviewed commit; baseline warnings are called "expected differences, not this check" | resolved. REVIEW-POLICY.md:135-140 still says "must match the branch's files". That is consistent: `ship` refuses changes after the reviewed commit, so those files are the reviewed commit's. Not a finding |
| MEDIUM noise and resume path (Needs decision) | owner: "Yes to the 17 recommendations". (a) REVIEW-POLICY.md:152-153, the `## Eval run` template (REVIEW-POLICY.md ~282), auto/SKILL.md:254, review/SKILL.md:84 and :121. (b) the stop is renamed `eval regressions, decision needed`, with a new row at auto/SKILL.md:96 | in place; two new gaps below |
| MEDIUM live_checked recorded early | cleared in 59cfe99; the live check is owed again | metadata.yml `live_checked:` empty |
| LOW `eval run failed` has no resume row or CLAUDE.md entry | row at auto/SKILL.md:97; CLAUDE.md:71 "an eval run that fails" | resolved |
| LOW rename detection | `--no-renames` at analysis.py:325, plus `test_owes_run_owed_when_a_file_moves_out_of_a_listed_path` | M30 killed by that test |
| LOW "Every case … is one finding" | auto/SKILL.md:252-254 "One or more cases … make one finding … listing each case" | resolved; matches B7 |
| LOW stale Progress entry | new dated entry at plan.md:141-173, below the marker; the old entry is untouched | SHAs and counts correct (698→700, kit 298) |
| LOW ship skill blank line | blank line added before the heading; trailing blank removed | resolved |

### Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. spec.md is unchanged against main (0 diff lines). plan.md changed only below the Progress marker. The stop name `eval regressions, decision needed` differs from B7's literal `(decision needed)`, but it is the owner's (b) and still contains the phrase |
| 2 | Type check | expected FAIL, owed live check only (below) |
| 3 | Behaviour against the spec | findings (2), both in the (a)/(b) skill text |
| 4 | Tests prove the behaviour | pass. All three targeted mutants killed; the only changed production line is covered |
| 5 | Conventions | pass. No model or network in the new tests: temp git repos only |
| 6 | Numbers in prose | pass. Progress "kit 298, pytest 698 -> 700" reproduced |
| 7 | Documentation | pass. CLAUDE.md stop list updated |
| 8 | Guardrails and hygiene | pass. No secrets; the git argv is unchanged in shape, with no shell |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check

```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 17, feature)
  error: A live check is owed and not recorded. Do the steps in intents/17-evals-every-change/review.md → ## Live check, then set live_checked: <date> in intents/17-evals-every-change/metadata.yml.
  note:  11 file(s), 699 line(s) changed outside intents/.
exit: 1
```

The only error is the owed live check, which follows from the owner clearing `live_checked` (59cfe99). Clearing it is the owner's job; it is not a rework finding.

### Findings

- **MEDIUM** `.claude/skills/auto/SKILL.md:96`: the "eval regressions, decision needed" row never writes the round's `review.md` when the owner picks rework.
  - **Why it happens:** step 6, the eval run, comes after the re-check and "before writing `review.md`" (auto/SKILL.md:234). Step 6.4 then stops, so round n has no `review.md` at the stop. The row's Accepted branch writes it. The Rework branch says only `as "decision needed" (a **new round**)`. The decision-needed row (:94) assumes the round's `review.md` already exists, because step 5.4 writes it before step 5.5 acts on a verdict.
  - **Effect:** round n's report, and any "Needs rework:" findings from the reviewer in that round, never reach `review.md` or the implementer. Round n+1 then starts with a gap in the history.
  - **Second gap:** unlike the "re-check mismatch" row (:95), this row does not say what to do when the reviewer's report is not in the conversation (a new session). In that case the Accepted branch cannot write `review.md` either.
  - **Needs rework:** in that row, write round `auto_round`'s `review.md` on both branches: the regression finding with the owner's answer, and verdict `rework` on the Rework branch. Then go on as "decision needed". Add the re-check-mismatch clause: "If the reviewer's report is not in this conversation, redo the review as the same round, then the re-check and the eval compare." Step 5.4 ("every round writes `review.md`") and row :95 determine this fix.
- **LOW** `.claude/skills/auto/SKILL.md:252-256`, `.claude/skills/review/SKILL.md:84`, `REVIEW-POLICY.md:152-153`: "re-run a case that flipped before calling it a regression" leaves several things open.
  - **What is unclear:**
    - It does not say how to re-run. `advisor-eval --only <id>` exists (run.py:170).
    - It does not say which report the `## Eval run` section names after a re-run.
    - It does not say what `/ship` writes as the baseline when the re-run disagrees with the full run.
  - **Why it matters:** a re-run with `--only` does not compare cleanly. I trimmed 093332Z to the one case `waterproof-camera` and ran `compare` on it. It printed "this run: 1/1 passed", `fixed (1)` and `removed (14)`, listing every other case. A coordinator could misread that as 14 removals, or `/ship` could commit it as the baseline.
  - **Smaller points:**
    - In auto/SKILL.md the sentences run finding → re-run → stop. The re-run should come before the finding.
    - In review/SKILL.md the sentence sits right after "A reviewer agent only checks…", which leaves it unclear who re-runs. Only the coordinator may call a model.
  - **Needs decision:** which report counts after a re-run, both for `## Eval run` and for the baseline written at ship. One option: re-run with `--only <flipped ids>`, call it a regression only if it fails again, and keep naming the full run, which stays the baseline source. The fix chooses behaviour beyond the spec, so it is the owner's call.
- **LOW, worth a look** `.claude/skills/auto/SKILL.md:94-96`: the new reason `eval regressions, decision needed` contains the earlier row's reason `decision needed` (:94). A coordinator that matches the reason by substring hits row :94 first, a new round, and skips the "accepted, no new round" path. A distinct name, such as `eval regressions`, would remove the ambiguity. Not blocking.

### Mutants

Each mutant changed one line and ran the full pytest suite (700). Kit tests were not re-run per mutant because no mutant touched `scripts/`. The harness checked that the diff was non-empty before running.

| # | Target | Mutation | Result | Killing test |
| --- | --- | --- | --- | --- |
| M18 | baseline.py:87 | `i in old and old[i] == "PASS"` → `old.get(i, "PASS") == "PASS"` | killed (KeyError 'newfail') | test_evals_baseline::test_compare_categories_rates_and_no_warnings |
| M18b | baseline.py:87 | as M18, with `old.get(i,"PASS")` in the tuple too (no KeyError) | killed (regressed list has an extra ('newfail','PASS','FAIL')) | same |
| M19 | analysis.py:325 | `{base}...HEAD` → `{base}..HEAD` | killed | test_analysis_baseline_cli::test_owes_run_ignores_changes_main_made_after_branching |
| M30 | analysis.py:325 | drop `"--no-renames"` | killed | test_analysis_baseline_cli::test_owes_run_owed_when_a_file_moves_out_of_a_listed_path |

There are no survivors. analysis.py:325 is the only production line changed in round 2. M1–M17 and M20–M29 (round 1) target code unchanged since then and were not re-run. A rework of the findings above changes skill text only, so it is expected to kill no new mutant.

**Do the tests prove the behaviour?** Yes, for the code. Both round-1 survivors and the rename gap are now proven: each fails for the intended reason and not only by accident (M18b confirms M18 does not die only on the KeyError). The (a)/(b) changes are skill and policy prose that no test exercises. Only the live check or a real `/auto` regression stop shows them.

### Not checked

- The `/auto` step 6 eval run, the regression stop and its two resume branches, the `eval run failed` resume, and the `/ship` baseline update, run end to end with a real Ollama model. Live check, rule 3.
- M26, `baseline`'s write-error exit, which is still untested (carried from round 1).
- Whether a re-run with `--only` is the intended re-run (LOW finding).

### Live check

- **owed:** rule 3. The skill procedures are only shown by a real model run (spec AC7: "live check owed").
- **steps:**
  1. With Ollama running and `qwen3:8b` pulled, in `C:/Users/eric/src/product-advice-agent-wt/17-evals-every-change`, run `uv run advisor-analysis owes-run --base main`.
  2. In the same worktree, run `uv run advisor-analysis compare evals/runs/20261116T093026Z-ollama.json`, then `uv run advisor-analysis compare evals/runs/20261116T093332Z-ollama.json`.
  3. In a scratch branch or worktree off this branch that changes one word of `src/advisor/prompts/system.md` and commits it, run `uv run advisor-analysis owes-run --base main`, then `uv run advisor-eval`, then `uv run advisor-analysis compare <new report>`. Compare the report's three `*_sha256` with `sha256sum evals/cases.jsonl src/advisor/prompts/system.md src/advisor/data/catalogue.json` there.
  4. If step 3 shows a case under "regressed", re-run it with `uv run advisor-eval --only <id>` and `compare` that report.
- **you should see:**
  1. "not owed (no listed path changed)", exit 0.
  2. First 8/15 against 8/15, with no flips and no warnings. Then 9/15 with `fixed (1): waterproof-camera: FAIL -> PASS`. Both exit 0.
  3. "owed: the diff touches src/advisor/prompts/system.md", then a report in `evals/runs/`. `compare` prints both pass rates, any flips and a `prompt_sha256 differs` warning. The report's `prompt_sha256` equals the scratch file's sha256, not the baseline's.
  4. 1/N passed with every other case under "removed". Decide whether this is the re-run you want the skills to describe (LOW finding). Then record `live_checked` if satisfied.

### Eval run

- not owed (no listed path): `uv run advisor-analysis owes-run --base main` at 232900a printed "not owed (no listed path changed)", exit 0. The changed paths are skills, CLAUDE.md, README.md, REVIEW-POLICY.md, `evals/baseline.json`, the intent folder, `src/advisor/evals/analysis.py`, `src/advisor/evals/baseline.py` and two tests. None of them is in the policy's list.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/17-evals-every-change` at 232900a; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 298 tests, 0 fail; "All
  checks passed!"; "160 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "700 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "11 file(s), 699 line(s)". Matches.
- **Coordinator, re-run:** M18 KILLED by `test_compare_categories_rates_and_no_warnings`;
  M19 KILLED by `test_owes_run_ignores_changes_main_made_after_branching`;
  M30 KILLED by `test_owes_run_owed_when_a_file_moves_out_of_a_listed_path`
  (each "1 failed, 699 passed"). Matches the reviewer and the implementer.

**Reviewer:**
- **Verified myself:**
  - `npm run verify` exit 0: kit 298 tests, 298 pass, 0 fail; ruff "All checks passed!"; "160 files already formatted"; mypy "Success: no issues found in 29 source files"; pytest "700 passed". This matches the implementer's claim.
  - `npm run check:intent` exit 1. Its only error is the owed live check (output above).
  - Four mutants (table above), each followed by `git status --short` clean.
  - Diffs:
    - Read the round-2 diff `0ce42a3..232900a` in full.
    - `git diff main...HEAD -- spec.md` is empty.
    - The plan.md diff is entirely below the Progress marker.
    - metadata.yml: `live_checked` cleared and `auto_round: 2`.
  - The hashes in `evals/baseline.json` equal the sha256 of the branch's `evals/cases.jsonl` (2b6210…), `system.md` (a22c1c…) and `catalogue.json` (c2e56c…).
  - `compare` of 093026Z gives 8/15 with no flips; 093332Z gives 9/15 with `waterproof-camera` fixed. Both exit 0.
  - A one-case trimmed copy of 093332Z, written in scratch (not committed), compares as 1/1 with 14 "removed".
  - `sdlc:scan --sample-due auto --exclude 17` gives "sampled: no".
  - Nothing was pushed (no origin ref); `main` is at b2e2815.
- **Taken on trust:**
  - That the owner's words "Yes to the 17 recommendations" cover (a) and (b) as written.
  - Who made 093026Z and 093332Z, and at which commit. Their hashes match the content.
```
# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: a54cf3f350c846edeefc3a468026a3215310266c
- round: 1
- sampled: no
- run: auto
- live-check: owed

### Passes

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

### Type check

    > product-advice-agent@0.0.0 check:intent
    > node scripts/check-intent.mjs

    type-check: PASS (intent 17, feature)
      note:  11 file(s), 639 line(s) changed outside intents/.
    exit: 0

### Findings

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

### Mutants

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

### Not checked

- The `/auto` step 6 eval-run procedure, the copy to the main checkout's `evals/runs/`, and the `/ship` baseline update, run end to end with a real Ollama model. These are skill text, and only a real coordinator run shows them (live check, rule 3).
- `baseline`'s write-error exit 1 (M26 not run).
- Whether 093026Z, and not 093332Z, was the right baseline to commit. The owner chose it; see the noise finding.

### Live check

- owed: rule 3. The Not-checked item is the skill procedures (`/auto` step 6 eval run, compare, the regression stop, `/ship` baseline update), which only a real model run shows. Spec AC7 also states "live check owed". Rule 1 does not apply (no listed runtime path).
- steps:
  1. In the main checkout on `main` (Ollama running, `qwen3:8b` pulled), check out nothing. In this worktree run `uv run advisor-analysis owes-run --base main`.
  2. Run `uv run advisor-analysis compare evals/runs/20261116T093026Z-ollama.json`, then `uv run advisor-analysis compare evals/runs/20261116T093332Z-ollama.json`.
  3. In a scratch branch or worktree that touches `src/advisor/prompts/system.md` (one word), run `uv run advisor-analysis owes-run --base main`, then `uv run advisor-eval`, then `compare` on the new report.
- you should see:
  1. "not owed (no listed path changed)".
  2. 8/15 against 8/15 with no flips and no warnings, then 9/15 with `fixed (1): waterproof-camera: FAIL -> PASS`. Both exit 0.
  3. "owed: the diff touches src/advisor/prompts/system.md", a report in `evals/runs/`, and `compare` printing both pass rates, any flips, and a `prompt_sha256 differs` warning. Then confirm the existing `live_checked` covers this, or record it again (finding 5).

### Eval run

- not owed (no listed path): `uv run advisor-analysis owes-run --base main` at a54cf3f printed "not owed (no listed path changed)". The diff touches `src/advisor/evals/analysis.py` and `baseline.py`, neither listed.

### Verified myself vs. taken on trust

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
