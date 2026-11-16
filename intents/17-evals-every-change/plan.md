<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §17 plan — Run the evals on every change that can move the answers

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A written rule for which changes owe an eval run (spec B1–B3), the
coordinator running it on Ollama during the review (B4), a committed
baseline and a comparison that reports flips without blocking (B5–B7), and
the baseline refreshed on `main` after a ship (B8), starting from a first
baseline this intent commits (B9).

## Risks

- **A model call in the suite**: `baseline`, `compare` and `owes-run` read
  files and git only; tests use fixture reports; `tests/conftest.py`
  blocks sockets anyway.
- **Merge overlap**: §16 adds `judge`/`judge-validate` subparsers to
  `analysis.py` and §18/§19 edit the auto, review and ship skills. Keep the
  new subparsers and skill paragraphs self-contained; the coordinator
  resolves conflicts at rebase.
- **Policy drift**: the path list exists in two places (B1's prose in
  `REVIEW-POLICY.md` and `owes_run`'s constant). A test reads the policy
  section and asserts both list the same paths.
- **A report not tied to the reviewed content** (Interpretations): the
  comparison prints each hash; the skill tells the coordinator to state the
  commit the run was made at.
- **Baseline committed on the branch**: forbidden by ship's
  "changed since the reviewed commit" rule; the first baseline (B9) is
  committed before review, as part of the build, not after.
- Reviewed tier (`REVIEW-POLICY.md`, `.claude/skills/**`); live check owed.

## Verified against the codebase

Re-read on `main` at `3d04fd5` (§13 merged).

- `REVIEW-POLICY.md:70` "## Live checks" (the pattern), `:113` "## Merging", `:145` "## Passes", `:189-235` "## The report" with sections Passes, Type check, Findings, Not checked, Live check, Verified myself.
- `src/advisor/evals/run.py:310-313` — report hashes `cases_sha256`, `prompt_sha256`, `catalogue_sha256`; per case `id`, `status`.
- `src/advisor/evals/report.py:19` — `parse_report(text)` (validation of report files).
- `src/advisor/evals/analysis.py:86-115` — subparsers `generate` … `import`; `main(argv, *, env, client_factory, out, err, now, serve, annotations_factory)`.
- `scripts/ship-lib.mjs:104` — "changed since the reviewed commit besides review.md and metadata.yml".
- `.claude/skills/auto/SKILL.md` §6 "The coordinator's re-check" (line ~193), §7 stops, §9; `.claude/skills/review/SKILL.md` §3 passes, §4 report; `.claude/skills/ship/SKILL.md` "Relay the report".
- `.gitignore` — `evals/runs/` ignored (reports stay local).

## Subtasks

1. **Pure module** `src/advisor/evals/baseline.py`: `EVAL_PATHS` and
   `owes_run(paths)` (B1); `baseline_from(report)` (B5);
   `compare(report, baseline)` → rates, regressed, fixed, added, removed,
   warnings (B6); `format_comparison`. Tests (AC1–AC3 logic). Commit.
2. **Commands** in `analysis.py`: `baseline <report> [--out evals/baseline.json]`,
   `compare <report> [--baseline …]` (exit 0 always when files are valid,
   2 otherwise), `owes-run [--base main]` (prints "owed" with the matching
   paths, or "not owed"; uses `git diff --name-only <base>...HEAD`). Tests
   with fixtures and a temp git repo for `owes-run`. Commit.
3. **Policy** `REVIEW-POLICY.md`: "## Eval runs" after "## Live checks"
   (B1 path list, B2 HIGH finding, who runs it, regressions reported not
   blocking); "The report" gains `## Eval run` after `## Live check` (B3).
   A test that the policy's path list equals `EVAL_PATHS`. Commit.
4. **Skills**: `/review` passes mention the eval-run check and the
   section; `/auto` §6 runs `owes-run`, then `advisor-eval` in the worktree
   when owed, copies the report to the main checkout's `evals/runs/`, runs
   `compare` against `evals/baseline.json`, adds the regressed cases as a
   "Needs decision" finding (B7) and stops with `eval run failed` when the
   run cannot complete (B4); `/ship` adds the post-ship baseline step (B8).
   Commit.
5. **First baseline (B9)**: the implementer cannot run a model; it writes
   the commands into Progress and stops short of the baseline. The
   coordinator runs `advisor-eval` on Ollama at the branch head (the cases
   and catalogue on `main`), the owner looks at it in the live check, and
   the coordinator commits `evals/baseline.json` **before the review round**
   on the owner's word.
6. **Docs**: README "Evaluating answers" (`baseline`, `compare`,
   `owes-run`), `CLAUDE.md` Commands line. Commit.
7. **Finish**: verify, check:intent, `status: in-review`, Progress.

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1 | each listed path owes; `src/advisor/tracing.py`, `README.md`, `scripts/x.mjs` don't; prefix vs exact (`src/advisor/data/x.json` owes, `src/advisor/database.py` doesn't) | prefix too loose; a path dropped |
| B1 policy | the policy section's list == `EVAL_PATHS` | drift |
| B5 | fields copied; no `catalogue_sha256` → absent; invalid report → exit 2 | wrong field |
| B6 | regressed (PASS→FAIL, PASS→ERROR), fixed, added, removed; both rates; one warning per differing hash/model/provider; exit 0 | missing a category; exit non-zero on regressions |
| B6 | missing baseline file → exit 2 with the path | silent pass |
| owes-run | temp repo diff with a listed path → "owed" + path; none → "not owed" | inverted |

## Validation

- `npm run verify` green; `npm run check:intent` PASS (FAIL only on the
  owed live check).
- Live check (owed: the skills, a real model run): the coordinator's
  `advisor-eval` on Ollama, `baseline` from it, `compare` of the report
  with itself (no flips); the owner reads the report and says the
  baseline may be committed.

## Assumptions I made

- `owes-run` lives in `advisor-analysis` (Python, beside `compare`) rather
  than a node script, since the skills already call `uv run`.
- The first baseline is committed on the branch before the review round
  (subtask 5), so it is part of the reviewed content.
- A path entry ending in `/` is a prefix; any other is an exact file.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-13 - subtasks 1-4, 6 built; 5 left to the coordinator

Commits: 7af1cc0 (baseline.py), 240c9a1 (commands), 280a2ba (policy),
98f6106 (skills), 84ec629 (README, CLAUDE.md). Tests 624 -> 664 (+40:
30 in `tests/test_evals_baseline.py` incl. the policy-list == `EVAL_PATHS`
test, 10 in `tests/test_analysis_baseline_cli.py` with a temp git repo for
`owes-run`). No model call, no new dependency.

Divergences: the eval-run check is a paragraph under pass 3 in
`REVIEW-POLICY.md` and the review skill, not a tenth pass, so "nine passes"
stays true in the reviewer agent and skill. `baseline.py` is not added to
`CORE_CODE` (the spec says no kit change). `owes-run` prints "owed: the diff
touches" plus the paths, or "not owed (no listed path changed)".

Subtask 5 (first baseline, B9) is NOT done: the implementer cannot run a
model, and `evals/baseline.json` does not exist. Coordinator commands, in the
worktree at the branch head (Ollama running, qwen3:8b pulled):

    uv run advisor-eval
    cp evals/runs/<stamp>-ollama.json <main checkout>/evals/runs/
    uv run advisor-analysis baseline evals/runs/<stamp>-ollama.json
    uv run advisor-analysis compare evals/runs/<stamp>-ollama.json   # same report: no flips, no warnings

The owner reads the report, then the coordinator commits `evals/baseline.json`
on the branch before the review round (`§17: first eval baseline from <report>`).

### 2026-11-16 - rework after review round 1

Commits now on the branch (the 2026-11-13 entry's SHAs are from before the
rebase): 1867933, abf268c, 6e4ef36, 1dcb66f, 358aef1 (subtasks 1-4, 6),
03e6f33 (subtask 5: `evals/baseline.json` from
`20261116T093026Z-ollama.json`), then the review and gate commits, and this
rework: a1efc36 and the format commit after it. Subtask 5 is done; the old
entry's "does not exist" is superseded.

Rework (review.md round 1): a new-and-failing case in the compare test (kills
M18); `owes-run` tests for a moved `main` (M19) and for a file moved out of a
listed path, with `--no-renames` on the `git diff`; the hash check in the auto
and review skills now names the three files to hash, and says the baseline
warnings are not that check; the "One or more cases ... one finding" wording;
a resume row and a CLAUDE.md stop-list entry for `eval run failed`; blank
line in the ship skill.

Owner decisions ("Yes to the 17 recommendations"):
- (a) Noise: one sentence in `REVIEW-POLICY.md` "Eval runs" and in the
  `## Eval run` report guidance, mirrored in the auto and review skills: a
  single run varies, re-run a flipped case before calling it a regression.
- (b) Resume path: the regression stop is now
  `auto_stopped: eval regressions, decision needed` (the smallest change that
  a row can match), with a resume-table row: accepted means write that
  round's `review.md` with no new round and go on from its verdict; a rework
  choice behaves as "decision needed" (new round).

Counts: kit 298 (unchanged), pytest 698 -> 700 (+2 owes-run tests; the
compare test gained a case). Mutants: M18 killed by
`test_compare_categories_rates_and_no_warnings`; M19 by
`test_owes_run_ignores_changes_main_made_after_branching`; dropping
`--no-renames` by `test_owes_run_owed_when_a_file_moves_out_of_a_listed_path`.
`check:intent` fails only on the cleared `live_checked` gate (coordinator's).
