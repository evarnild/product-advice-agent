<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §20 review — Bring a branch that is behind main up to date before each review round

verdict: rework
tier: reviewed
reviewed-commit: 2ed67a3
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, by the path table: the branch edits `REVIEW-POLICY.md`,
`scripts/ship-lib.mjs` (merge preconditions), `.claude/agents/**`,
`.codex/agents/**` and `.claude/skills/**`. `review_tier` empty. The policy
applied is `main`'s; the branch's own edits to it do not govern this review.

HEAD e8f77d4 differs from 2ed67a3 only in `metadata.yml` (`auto_round: 1`).
The branch is 0 behind `main` (03a5bdb). `status: in-review`.

Verdict `rework`: F1, F2 and F3 need mechanical rework. Pass 4 is
incomplete (17 of 94 mutants; the reviewer's mutant run was stopped by
memory pressure), so round 2 runs the rest.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 20` → "nth
attested auto change = 6, every 3, sampled: yes"; it applies only to an
`attest` verdict, so `sampled: no` here.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F1; the Progress divergences 1-3 are benign and documented |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): F1 against B14; B1-B23 and A1-A6 otherwise present; eval run not owed |
| 4 | Tests prove the behaviour, not only pass | findings (2): F2, F3; **not run in full**: 17 of 94 mutants, 15 killed, L06 and L08 survive |
| 5 | Conventions | pass (`update-branch-lib.mjs` imports no `child_process` or `fs`, tested; E2E in throwaway sandboxes with `SDLC_UPDATE_BRANCH_VERIFY`) |
| 6 | Numbers in prose | pass: 434 kit tests (382 + 52 new), 859 pytest, check:intent PASS |
| 7 | Documentation | findings (1): F4 (worth a look) |
| 8 | Guardrails and hygiene | pass (no secret, no dependency; git args as arrays; id digits only) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 20, feature)
  note:  23 file(s), 1042 line(s) changed outside intents/.
```

## Findings
- **F1 MEDIUM** `.codex/agents/product-advice-agent-implementer.toml:22`:
  the B14 exception at `:15-20` is followed by the unchanged "…; an
  implementer never merges.", which contradicts it, so a Codex implementer
  may refuse the merge its brief asks for. Needs rework: "an implementer
  never merges into `main`" (the narrowing of A4 and A5).
- **F2 MEDIUM** `scripts/update-branch-lib.mjs:33`: mutant L06 (drop
  `!w.branch &&` from the detached filter) survives, so A1's "and has no
  branch" is unproven: a folder `20-x` holding another id's branch would be
  refused as "HEAD is detached" instead of "no worktree". Needs rework: a
  `findTarget` unit case, worktree `/r/product-advice-agent-wt/20-x` on
  `feat/21-y`, id `20` → reason contains "no worktree".
- **F3 LOW** `scripts/update-branch-lib.mjs:20`: mutant L08 (drop the
  backslash normalisation in `folderName`) survives; no test gives a
  Windows path. Needs rework: a unit case, `C:\r\product-advice-agent-wt\20-x`
  with no branch → "HEAD is detached".
- **F4 LOW** `CLAUDE.md` `/auto` paragraph (its list of stops): does not
  name the new `main merge conflict` and `branch update refused` stops. B23
  does not ask for it and the skill governs. Worth a look.
- **F5 LOW** AC2 "each refusal of B2 → 1": the two-worktrees refusal (A2)
  and the "branch is `main`" guard are unit-tested only, not end to end; the
  approved plan's E2E table omits both and the script refuses before any git
  write. Worth a look.

The implementer's one `git stash` (to run `verify` on subtask 1 alone) was
traced: stash commit 20cf8a6 equals 83b1e5f's content, the stash list is
empty, nothing lost; no rule binding the implementer forbids it. Not a
finding. Note for the owner: `refs/stash` is shared by every worktree, so a
"no stash" rule for implementers may be worth a later intent.

**Mutants** (reviewer's harness `mut20/run.mjs`: copy backup, replace,
full `npm run test:kit`, restore, `git diff --quiet` check):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| L01 | `update-branch-lib.mjs:16` one id → `>= 1` | KILLED | parseUpdateArgs "rejects no id, two ids, a flag and a non-numeric id" |
| L02 | `:16` `/^\d+$/` → `/^\d+/` | KILLED | same |
| L03 | `:28` id match → `startsWith` | KILLED | findTarget "finds by the branch id, with or without codex/, not by prefix" |
| L04 | `:29` `> 1` → `> 2` | KILLED | findTarget "refuses two worktrees for one id, naming both" |
| L05 | `:32` `=== 1` → `=== 2` | KILLED | findTarget, E2E |
| L06 | `:33` drop `!w.branch &&` | **SURVIVED** | F2 |
| L07 | `:33` drop the `-` after the id | KILLED | findTarget "reports a detached worktree whose folder is <id>-…" |
| L08 | `:20` drop backslash normalisation | **SURVIVED** | F3 |
| L09 | `:34` drop `detachedPath` | KILLED | findTarget detached, E2E "a rebase in progress" |
| L10 | `:45` in-progress `> 1` | KILLED | preflight cases, E2E |
| L11 | `:46` `pathKey` → raw compare | KILLED | preflight "names each reason" |
| L12 | `:47` `'main'` → `'master'` | KILLED | same |
| L13 | `:48` detached → `false` | KILLED | same |
| L14 | `:49` dirty → `false` | KILLED | preflight, E2E modified/staged |
| L15 | `:55` `> 0` → `>= 0` | KILLED | planUpdate, E2E up to date |
| L16 | `:55` `> 0` → `> 1` | KILLED | planUpdate, E2E behind |
| L17 | `:60` `status === 0` → `<= 1` | KILLED | classifyMerge "reads the facts, not the message", E2E |

Not run (memory pressure stopped the run): L18-L38 (classify conditions,
classifyAbort, the tail, exit codes and lines), U01-U33 (all of
`update-branch.mjs`), S01-S02 (`ship-lib` messages), SL1-SL6
(`session-lib`), SS1-SS2 (`sessions.mjs`), K01-K13 (the kit texts). Defined
in the coordinator's scratchpad `mut20/mutants.mjs`; round 2 runs them.

## Not checked
- 77 of 94 mutants, listed above: every mutant of `update-branch.mjs`, the
  ship and session message mutants and the kit-text mutants.
- `update-branch` against a real worktree with the real `npm run verify`
  (the live check).
- The coordinator flow in `/auto` and `/review` (agent instructions; read
  only; the live check).
- A merge of `main` that changes `uv.lock`, leaving the worktree's
  environment stale, so `verify` goes red for an environment reason.
- The script runs git with the inherited environment (as `ship.mjs`); only
  matters if run from a hook.

## Live check
- owed: rule 3 (AC9): `update-branch` against a real worktree and the
  `/review` flow are runtime behaviour only a live run shows. Rules 1 and 2
  do not apply (no runtime path, no `.claude/settings.json`).
- steps (Git Bash, in the main checkout `C:/Users/eric/src/product-advice-agent`):
  1. With a spawned worktree behind `main` (`npm run sessions` shows
     "Behind main (update before review): §n (-N)"), run
     `npm run update-branch -- <id>; echo $?`.
  2. Run it again.
  3. Commit anything on `main`, then run `/review <branch>` in the
     coordinator.
  4. Optional, in a scratch intent whose branch and `main` edit the same
     line: `npm run update-branch -- <id>; echo $?`, then
     `git -C <worktree> status --porcelain --untracked-files=no` and
     `git -C <worktree> rev-parse -q --verify MERGE_HEAD`.
- you should see: (1) one block after `verify` finishes: "behind main by N;
  merged main (now <head>, main <main>)", "verify green", exit 0;
  `git -C <worktree> rev-parse HEAD^2` equals `git rev-parse main`. (2)
  "branch contains main at <short main>", no verify, exit 0. (3)
  `npm run update-branch` runs before any pass and the new `review.md`
  header has `main: <hash>` equal to `git rev-parse --short main`. (4) exit
  2, the file under "conflicted files:", both git commands print nothing.

## Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

## Verified myself vs. taken on trust

**Coordinator, re-run** (worktree at e8f77d4; `git status --short` clean
before and after):
- **Coordinator, re-run:** `npm run verify` → "tests 434", "pass 434",
  "fail 0"; "All checks passed!"; "180 files already formatted"; mypy
  "Success: no issues found in 31 source files"; "859 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "23 file(s), 1042
  line(s)". Matches.
- **Coordinator, re-run:** L06 SURVIVED, L08 SURVIVED (kit 434 pass each).
  Matches the reviewer.
- **Coordinator, read:** F1's two sentences at
  `.codex/agents/product-advice-agent-implementer.toml:15-22`; F2's filter
  at `update-branch-lib.mjs:33`; F3's `folderName` at `:20`.

**Reviewer (agent), read-only:** `git diff main...HEAD` (25 files); verify,
check:intent, `test:kit`; L01-L17; the AC6 grep (no remaining instruction to
rebase: prohibitions, the ship message and its policy rule, descriptive
comments and test files only); `owes-run`; sampling; the stash trace
(reflog, `git fsck --unreachable`); `git branch -r` (nothing pushed).

**Taken on trust:** which test kills L01-L17 (the reviewer's harness log);
the AC6 grep classification beyond F1.
