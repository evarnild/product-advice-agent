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
