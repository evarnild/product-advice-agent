<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §17 spec — Run the evals on every change that can move the answers

Accepted intent: [intent.md](intent.md)

Written against `main` at `d7303ec`.

## Owner's decisions (question round, 2026-11-13)

- **Enforcement:** "Review pass only": `REVIEW-POLICY.md` gains the rule;
  a missing run is a review finding. Nothing blocks mechanically (no
  change to `ship-lib.mjs` or `check:intent`).
- **Baseline:** "Committed baseline": `evals/baseline.json`, updated after
  each merge whose review made a run; the branch's run is compared with it.
- **Regression:** "Report flips, you decide": the review lists every case
  that flipped and the pass-rate change; no threshold blocks.
- **Who runs:** "The coordinator, on Ollama": during `/auto` (and
  `/review` in the coordinator session) the coordinator runs
  `advisor-eval` on the local model; a paid run only on the owner's
  request.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `REVIEW-POLICY.md` → "Live checks" (line 70 on) | The pattern: a path list that makes a check owed, `/review` deciding owed / not-needed, steps in the report. B1–B2 mirror it. |
| `REVIEW-POLICY.md` → "The report" (line 189 on) | The report's sections; header `live-check: owed \| not-needed` (ship accepts only those two). B3 adds a section, not a header field. |
| `scripts/ship-lib.mjs:104` | "changed since the reviewed commit besides review.md and metadata.yml": why the baseline is committed on `main` after the merge (B7), not on the branch. |
| `src/advisor/evals/run.py` report | `provider`, `model`, `cases_sha256`, `prompt_sha256`, `started`, per-case `id` and `status` (`PASS`/`FAIL`/`ERROR`); §13 adds `catalogue_sha256`. |
| `README.md` "Evaluating answers" | "A run uses a real model: the local one by default (slow on CPU, minutes for the 15 cases)". |
| `docs/decisions/0003-catalogue-changes.md` (§13, on its branch) | "a catalogue change owes an `advisor-eval` run whose report the review names; enforcement is §17's". |
| `.claude/skills/auto/SKILL.md` §6, `.claude/skills/review/SKILL.md`, `.claude/skills/ship/SKILL.md` | Where the coordinator's run (B4) and the baseline update (B7) are written. |

## Behaviour

**When a run is owed**

- **B1.** `REVIEW-POLICY.md` gains a section "Eval runs": a change owes an
  eval run when its diff touches any of `src/advisor/prompts/`,
  `src/advisor/agent.py`, `src/advisor/models/`,
  `src/advisor/guardrails.py`, `src/advisor/catalogue.py`,
  `src/advisor/data/`, `src/advisor/config.py` (the default models),
  `src/advisor/evals/cases.py`, `src/advisor/evals/score.py`, or
  `evals/cases.jsonl`. Otherwise none is owed.
- **B2.** A review of a change that owes a run and names no run report,
  or names one not made on the reviewed commit's content, has a HIGH
  finding "Needs rework: make the eval run" (a new pass-1/pass-4-style
  check listed in "Passes"). The verdict rules are otherwise unchanged.

**The report section**

- **B3.** `review.md` gains `## Eval run` (after `## Live check`): either
  "not owed (no listed path)", or the run report's name, provider and
  model, the comparison of B6, and the coordinator's reading. No new
  header field.

**Who runs it**

- **B4.** In an `/auto` round (and a `/review` run by the coordinator), when
  a run is owed, the coordinator runs `uv run advisor-eval` in the
  worktree at the reviewed commit, on the default provider (Ollama),
  after the reviewer's report and with the re-check, then copies the
  report into the main checkout's `evals/runs/` (gitignored), so it
  survives the worktree's removal. A paid run happens only on the owner's
  request in the conversation. If the run cannot complete (Ollama down, an
  ERROR on every case), `/auto` stops with `auto_stopped: eval run failed`
  and says why.

**Comparing with the baseline**

- **B5.** `evals/baseline.json` (committed) holds: the source report's
  name, `provider`, `model`, `cases_sha256`, `prompt_sha256`,
  `catalogue_sha256` (absent if the source report has none), and per case
  `id` → `status`. `advisor-analysis baseline <report>` writes it from a
  run report, nothing else.
- **B6.** `advisor-analysis compare <report> [--baseline <path>]` prints:
  both pass rates (passed / total), every case that went PASS→FAIL or
  PASS→ERROR ("regressed"), every FAIL/ERROR→PASS ("fixed"), cases only
  in one of the two ("added" / "removed"), and a warning line for each
  differing `provider`, `model`, `cases_sha256`, `prompt_sha256` or
  `catalogue_sha256`. Exit 0 whatever it finds (the owner decides);
  exit 2 for a missing or invalid file.
- **B7.** A regression is reported, never blocking: in `/auto`, one or
  more "regressed" cases make a "Needs decision: accept the regressions
  or rework" finding, so the run stops for the owner (`decision needed`);
  none, and the run goes on.

**Updating the baseline**

- **B8.** After `/ship <id>` completes for a change whose review names an
  eval run, the coordinator runs `advisor-analysis baseline
  evals/runs/<that report>` in the main checkout and commits
  `evals/baseline.json` on `main` (`§<id>: eval baseline from <report>`),
  as part of the `/ship` request. It is not pushed unless the owner says
  so. `.claude/skills/ship/SKILL.md` says this.
- **B9.** This intent commits the first `evals/baseline.json`, from a run
  of the current `main` (its live check, AC7).

## Interpretations

- **"Every change"** (intent) is B1's path list: changes that can move an
  answer or a verdict. Docs, kit, tracing and analysis-only changes owe
  none.
- **"On the reviewed commit's content"** is read through the hashes: the
  run's `prompt_sha256`, `cases_sha256` and `catalogue_sha256` match the
  branch's files; code changes in `agent.py` or `models/` are trusted to
  the run being made in the worktree at that commit, which the coordinator
  states in "Verified myself".
- **"Review pass only"** keeps `ship` and `check:intent` unchanged; the
  skills (auto, review, ship) carry the procedure.

## Acceptance criteria

- **AC1** (B5): `baseline` writes the fields from a fixture report; a
  report without `catalogue_sha256` writes none; invalid input exits 2.
  (test)
- **AC2** (B6): `compare` on fixtures: regressed, fixed, added, removed,
  each hash/model warning, both pass rates, exit 0; missing file exits 2.
  (test)
- **AC3** (B1): a pure function that says whether a list of changed paths
  owes a run, tested on each listed path, a near miss
  (`src/advisor/tracing.py`, `README.md`) and an empty list; the review
  skill uses it via a small command (`advisor-analysis owes-run --base main`
  or a `node` script, the plan decides). (test)
- **AC4** (B1, B2, B3): `REVIEW-POLICY.md` has the section and the report
  format has `## Eval run`; the review skill's passes mention it. (review
  reads them)
- **AC5** (B4, B7): `.claude/skills/auto/SKILL.md` has the run in step 6,
  the copy to the main checkout, the `eval run failed` stop and the
  regression decision. (review reads it)
- **AC6** (B8): `.claude/skills/ship/SKILL.md` has the baseline update
  after a complete ship. (review reads it)
- **AC7** (B9, live check owed: the skills and a real model run): the
  coordinator runs `advisor-eval` on `main` (Ollama), the owner looks at
  the report, `baseline` writes `evals/baseline.json`, it is committed on
  the branch; `compare` of that report with itself prints no flips.

## Non-functional

- **Boundaries:** `owes_run` and the comparison are pure (a new
  `src/advisor/evals/baseline.py`); `analysis.py` does the files and exit
  codes. No change to `run.py`, `ship-lib.mjs` or `check-intent.mjs`.
- **Data:** run reports stay gitignored; only `evals/baseline.json` (ids
  and statuses) is committed.
- **Model use:** none in code or tests. The coordinator's run uses the
  local Ollama (about 5 min for 50 cases); paid only on request.
- **Autonomy:** the coordinator may run the local eval and commit the
  baseline on `main` after a ship the owner asked for; it never decides a
  regression is acceptable.
- **Tier:** Reviewed (`REVIEW-POLICY.md`, `.claude/skills/**`).

## Out of scope

- Mechanical blocking in `ship` or `check:intent`; hosted CI; repeats per
  case; the judge's verdicts in the comparison (a later change once §16
  lands); tolerance thresholds.

## Assumptions I made

- **The path list** (B1), including `config.py` (default models),
  `cases.py`/`score.py` (verdicts) and `evals/cases.jsonl`.
- **A HIGH "Needs rework" for a missing run** (B2): mechanical, since the
  rule says the run is owed.
- **The baseline is committed on `main` after the merge** (B8), because
  `ship` refuses files changed after the reviewed commit; the skill, not
  `ship.mjs`, does it.
- **Command names** `baseline`, `compare`, `owes-run`, and the new module
  `baseline.py`.
- **Regressions stop `/auto` as a decision** (B7), which is how "you
  decide" works inside a run.
- Built after §13 merges (it reads `catalogue_sha256`); not dependent on
  §15 or §16.
