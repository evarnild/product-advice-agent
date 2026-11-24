<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §29 — An eval run's content hashes depend on the checkout's line endings

**Type:** fix
**Originator:** the §26 review, round 2 (MEDIUM finding), and the owner
("write the follow-up intent of 26", 2026-11-24)
**Source:** `intents/26-loosen-two-headphone-cases/review.md` (round 2,
Findings); `evals/baseline.json` as committed at `4a50ff6`

## Problem

An eval run report records three content hashes, and `compare` warns when
they differ from the baseline's. They are computed over the files' raw bytes
(`src/advisor/evals/run.py:310`, `:313`, `:314`):
- `cases_sha256` over `evals/cases.jsonl`;
- `catalogue_sha256` over `src/advisor/data/catalogue.json`;
- `prompt_sha256` over `src/advisor/prompts/system.md`.

The repository has no `.gitattributes`, and this machine has
`core.autocrlf=true`. So the same committed content hashes differently
depending on how it was checked out:

| `evals/cases.jsonl` at `main` | sha256 |
| --- | --- |
| the committed blob (LF) | 90a614f9… |
| this machine's checkout (CRLF) | d5f5e275… |
| §26's worktree after its edit (2 lines LF, 48 CRLF) | 20ba79fc… |

What this has already caused:
- **A warning on every compare.** The baseline written after §26 (`4a50ff6`,
  from `20261124T195935Z-ollama.json`) records `cases_sha256` 20ba79fc,
  from a working copy with mixed line endings. Every `advisor-analysis
  compare` on `main` now warns "cases_sha256 differs" although the cases
  are identical. A warning that is always on hides the one that matters: a
  run made against other cases.
- **Earlier baselines too.** The §22 baseline (b7a88ce6, LF bytes) and the
  §27 baseline (a81f06ad, CRLF bytes) differ only by line endings.
- **The review's content check is checkout-dependent.** REVIEW-POLICY.md →
  "Eval runs" and `/auto` step 6 compare a report's hashes with the sha256
  of the worktree's files. That passed in §26 only because both were
  computed over the same mixed bytes; on a fresh checkout it would fail.
- **Machines disagree.** A machine with other line-ending settings (the
  owner works on two) gets other hashes for the same content.

The judge's own `prompt_sha256` (`src/advisor/evals/judging.py:154`) hashes
text read in Python's text mode, so it is already free of line endings.
The fix should make the three report hashes behave the same way.

## Outcome

- A run's `cases_sha256`, `catalogue_sha256` and `prompt_sha256` are the same
  for every checkout of the same committed content (LF, CRLF or mixed). A
  test hashes one content in all three forms and gets one value.
- `advisor-analysis compare` of a new run on `main` against the committed
  baseline prints no hash warning when cases, prompt and catalogue are
  unchanged. It still warns when any of them really changed (a test).
- The committed `evals/baseline.json` carries hashes in the new form, so
  the warning stops without waiting for the next baseline.
- The content check in REVIEW-POLICY.md → "Eval runs" and in `/auto` step 6
  hashes the files the same way the run does: one command, or one stated
  rule, not "sha256 of the file".

## Constraints

- `run.py` is I/O (not `CORE_CODE`). Put any hashing helper in a pure
  module, with its tests, so `run.py` and the content check share one
  definition.
- Old run reports stay as they are (docs/decisions/0003, "Old records").
  `compare` must keep working against a baseline or report written before
  the fix. Comparing an old-form hash with a new-form one is the one place
  a warning may remain, and the warning should say so.
- `evals/baseline.json` is regenerated only from content that equals
  `main`'s: the same source run, with its three hashes recomputed in the new
  form from the files it was made on. It is not hand-edited to silence a
  warning.
- Does this owe an eval run? `run.py` and `baseline.py` are not in
  `EVAL_PATHS`, so not by path (REVIEW-POLICY.md → "Eval runs"). The answers
  don't change, only how their inputs are fingerprinted.
- Changing `.claude/skills/auto/SKILL.md` or `REVIEW-POLICY.md` is Reviewed
  tier. If the plan can state the content check without editing them (for
  example a command the skill already calls prints the hashes), that's
  preferable. Otherwise the tier is Reviewed.
- Out of scope:
  - renormalising the repository's line endings (`git add --renormalize`,
    a repository-wide `.gitattributes`);
  - the judge's `prompt_sha256`;
  - rewriting old run reports.

## Type-specific questions

### Fix
- **What broke:** observed: `compare` warns "cases_sha256 differs" for
  identical cases, and a report's hash matches a worktree only when both
  have the same line endings. Expected: the hash identifies the content,
  not the checkout.
- **Since when:** `cases_sha256` since §8 (`aa4060b`, raw bytes from the
  start), `catalogue_sha256` since §13 (`636a88b`). It became visible
  through §17's `compare` (`1867933`) and is now on every run since §26's
  baseline (`4a50ff6`).
- **Impact:** owner-facing, in the evals: a permanent false warning, and a
  review check that depends on the machine. No end user is involved; no
  data leak.
- **Reproduction:** on `main` (4a50ff6 or later), take any run made in the
  main checkout, e.g. `evals/runs/20261124T183001Z-ollama.json`, and run
  `uv run advisor-analysis compare evals/runs/20261124T183001Z-ollama.json`.
  It warns "cases_sha256 differs: baseline 20ba79fc…, report a81f06ad…"
  for the same cases.
- **The test that will fail first:** a new test for the hashing helper.
  The same bytes with LF, CRLF and mixed line endings must give one hash.
  It fails against today's raw-bytes hashing in `run.py`.

## Assumptions I made

- **Normalise in the hash, don't change the files.** I read "the hash
  identifies the content" as hashing the text with `\r\n` read as `\n`,
  rather than forcing LF checkouts with `.gitattributes`. The latter would
  touch every file's checkout on Windows and is a wider change. The plan
  may add `.gitattributes` for `evals/*.jsonl` too, if it gives a reason.
- **`follows_up: 8`.** The raw-bytes hash dates from §8's runner. §26
  only exposed it, by writing two LF lines into a CRLF working copy.
- **Fix, not adjustment.** It changes how `run.py` and `compare` behave,
  needs a failing-first test, and may touch the policy text.
- **`review_tier` left empty.** The path table decides: Reviewed if the
  skill or the policy changes, Attested otherwise.
- **Nothing blocks this.** It touches `run.py`, `baseline.py`, possibly
  `analysis.py`, and `evals/baseline.json`. §25 (in review) changes
  `score.py` and README.md and will merge cleanly beside it.
