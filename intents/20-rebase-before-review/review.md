<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §20 review — Bring a branch that is behind main up to date before each review round

verdict: rework
tier: reviewed
reviewed-commit: 68cc7dc
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed, by the path table (`REVIEW-POLICY.md`, `scripts/ship-lib.mjs`,
`.claude/agents/**`, `.codex/agents/**`, `.claude/skills/**`; the rework
itself touches `.codex/agents/product-advice-agent-implementer.toml`). Never
lowered. `main`'s policy and review skill applied.

HEAD b8ea50a differs from 68cc7dc only in `metadata.yml` (`auto_round: 2`).
The branch is 0 behind `main` (03a5bdb). `status: in-review`.

Round 1's F1-F3 are resolved. The reviewer's verdict was `escalate`,
conditional on the 77 mutants round 1 could not run. The coordinator ran
them this round: 13 survive. Two are test gaps on behaviour the spec names
(F6, F7: Needs rework), so the verdict is `rework`. The others are
equivalent, unreachable by design, or proven by reading (below).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 20` → "nth
attested auto change = 6, every 3, sampled: yes"; applies only to `attest`,
so `sampled: no`.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the rework does F1-F3 and nothing more; `plan.md` changes only below Progress (4 lines) |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | pass: B14/A5 hold in both implementers; eval run not owed |
| 4 | Tests prove the behaviour, not only pass | findings (2): F6, F7; 94 + 1 mutants now run in all, 13 survive (classified below) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: 437 kit tests (434 + 3), check:intent "23 file(s), 1059 line(s)" (1042 + 17) |
| 7 | Documentation | findings (1): F4 carried (worth a look) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 20, feature)
  error: A live check is owed and not recorded. Do the steps in intents/20-rebase-before-review/review.md → ## Live check, then set live_checked: <date> in intents/20-rebase-before-review/metadata.yml.
  note:  23 file(s), 1059 line(s) changed outside intents/.
```
The only error is the owed live check: the owner's, not rework.

## Resolution of round 1
| # | Round 1 | At 68cc7dc | Evidence |
| --- | --- | --- | --- |
| F1 MEDIUM | Codex "never merges." contradicts B14 | resolved: `.codex/agents/product-advice-agent-implementer.toml:22` "…; an implementer never merges into `main`."; `scripts/kit-texts.test.mjs:40-44` | F1M KILLED |
| F2 MEDIUM | L06 survived | resolved: `scripts/update-branch-lib.test.mjs:55-59` | L06 KILLED |
| F3 LOW | L08 survived | resolved: `scripts/update-branch-lib.test.mjs:60-64` | L08 KILLED |
| F4 LOW | CLAUDE.md `/auto` stop list | open, worth a look (the owner's) | — |
| F5 LOW | A2 and "branch is main" unit-only | open, worth a look (the owner's) | — |

`plan.md`: c69c759 wrote it with CRLF and garbled backslashes; 68cc7dc
restored LF (0 CR in the blob, as at 2ed67a3) and the text. Net change: 4
lines appended under Progress.

## Findings
- **F6 LOW** `scripts/update-branch-lib.mjs:61`, `classifyMerge`: mutant
  L19 (`if (mergeHead && unmerged.length > 0)` → `if (unmerged.length > 0)`)
  survives, so "a conflict needs `MERGE_HEAD`" (B7, reading facts only) is
  unproven: unmerged paths without `MERGE_HEAD` would be called a conflict
  (exit 2) instead of unexpected (exit 1). Needs rework: one assert in
  "reads the facts, not the message"
  (`scripts/update-branch-lib.test.mjs:106-113`):
  `classifyMerge({ ...h, status: 1, unmerged: ['f'] })` is `'unexpected'`.
- **F7 LOW** `scripts/update-branch.mjs:54`: mutant U04 (drop the
  `rebase-apply` check) survives; the E2E "a rebase in progress" case
  (`scripts/update-branch.test.mjs:276-284`) uses the default (merge)
  backend only, so B2's refusal of a rebase in progress is unproven for
  `git rebase --apply` (and `git am`). Needs rework: a second E2E case, the
  same conflicting setup with `git rebase --apply main`, asserting exit 1,
  "rebase is in progress", nothing changed.
- **F4 LOW** (carried) `CLAUDE.md` `/auto` paragraph: does not name the
  `main merge conflict` and `branch update refused` stops. Worth a look.
- **F5 LOW** (carried) AC2: the two-worktrees refusal and the "branch is
  `main`" guard are unit-tested only. Worth a look.
- **F8 LOW** `scripts/update-branch.mjs:99-109`: the dispatch for an
  `unexpected` merge result is untested end to end: U33 (no abort for
  `unexpected`, which would then run `verify` and report a merge), U21 and
  U20 survive. The plan says this path cannot be reached in a real repo
  (Assumptions); `classifyMerge` and `classifyAbort` are unit-tested. Worth
  a look: the owner reads `:99-109` in the diff.
- **F9 LOW** `.claude/skills/auto/SKILL.md:202`: mutant K10 (the step-5 stop
  renamed `update refused`) survives because the required phrase also occurs
  at `:104` and `:325`, so `kit-texts.test.mjs` does not pin the stop itself.
  Worth a look.

**Mutants.** Round 1's harness (`mut20/run.mjs`: copy backup, one replace,
`git diff --quiet` check, full `npm run test:kit`, restore, `git diff
--quiet` check). The reviewer ran L06, L08, F1M; the coordinator re-ran
those three and ran the 77 round 1 left. All 94 apply exactly once.

| Mutants | Result |
| --- | --- |
| L06, L08, F1M | KILLED (by the rework's three new cases) |
| L18, L20-L38 | KILLED (`classifyMerge` "reads the facts, not the message", `classifyAbort` "lists each fault alone", `outputTail` "keeps the last 25 lines of 30", the `formatReport` cases per outcome) |
| L19 | **SURVIVED**: F6 |
| U02, U03, U05-U12, U14-U19, U22-U28, U30-U32 | KILLED (E2E: "a merge in progress", "a rebase in progress", "a cherry-pick in progress", "an untracked file in the way of main…", "the id is checked out in the main checkout", "up to date…", "behind with no commits of its own: a fast-forward…", "behind with own commits and green verify…", "red verify…", "conflict…", "no worktree for the id", "usage: no id", "a modified tracked file") |
| U04 | **SURVIVED**: F7 |
| U01 (relative `--git-path` joined to the worktree) | SURVIVED: equivalent here: git prints an absolute path for a linked worktree's git dir |
| U13 (drop `--no-edit`) | SURVIVED: equivalent without a terminal (git does not open an editor) |
| U20, U21, U33 (`unexpected` / abort-left dispatch) | SURVIVED: unreachable end to end by the plan's design; F8 |
| U29 (`status ?? 1` → `?? 0`) | SURVIVED: only a signal-killed git has a null status; not testable here |
| S01, S02 | KILLED (ship-lib "says why a rewrite and a merge of main since the review each mean a new round") |
| SL1-SL6 | KILLED (`behindLine` cases; kit-texts "no file uses an old wording") |
| SS1, SS2 (`sessions.mjs` call site) | SURVIVED: no test runs `sessions.mjs`; AC5 allows a read, and the reviewer read it correct |
| K01-K09, K12 | KILLED (kit-texts "no file uses an old wording", "names npm run update-branch where it is used", "both implementer definitions carry…", "the reviewers and the review skill name the three-dot diff", "the policy has the main: header line", "covers the files it should") |
| K10 | SURVIVED: F9 |
| K11, K13 (a new rebase instruction in other words) | SURVIVED by design (A3: the grep test rejects old wordings only) |

## Not checked
- `update-branch` against a real worktree with the real `npm run verify`
  (the live check).
- The coordinator flow in `/auto` and `/review` (agent instructions; read
  only; the live check).
- A merge of `main` that changes `uv.lock`, leaving the worktree's
  environment stale (carried).
- The script runs git with the inherited environment (carried).
- The `unexpected` merge path end to end (F8).
- Round 2's reviewer did not re-read the round-1 diff beyond confirming
  nothing outside the rework changed since 2ed67a3.

## Live check
- owed: rule 3 (AC9), unchanged from round 1.
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

**Coordinator, re-run** (worktree at b8ea50a; `git status --short` clean
before and after):
- **Coordinator, re-run:** `npm run verify` → "tests 437", "pass 437",
  "fail 0"; "All checks passed!"; "181 files already formatted"; mypy
  "Success: no issues found in 31 source files"; "859 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "23 file(s), 1059 line(s)". Matches the reviewer.
- **Coordinator, re-run:** L06, L08, F1M KILLED, each by the test the
  reviewer named. Matches the reviewer and the implementer.
- **Coordinator, run:** the 77 mutants round 1 did not run, results above;
  every restore checked by `git diff --quiet`; no restore failure.
- **Coordinator, read:** `classifyMerge` (`update-branch-lib.mjs:58-63`) and
  its test (`update-branch-lib.test.mjs:105-114`); `inProgressOps` and the
  merge dispatch (`update-branch.mjs:44-110`); the `branch update refused`
  occurrences in `auto/SKILL.md` (`:104`, `:202`, `:325`).

**Reviewer (agent), read-only:** the rework diff `2ed67a3..68cc7dc`;
`git diff --name-only 2ed67a3..b8ea50a`; the `plan.md` CR counts and
`git ls-files --eol`; verify, check:intent; L06, L08, F1M; `owes-run`;
sampling; nothing pushed (`git branch -r`).

**Taken on trust:** round 1's L01-L17 and its AC6 grep classification (code
and texts unchanged since, except the F1 line); the equivalence readings of
U01, U13 and U29 are the coordinator's, not tested.

# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 2ed67a3
- round: 1
- sampled: no
- run: auto
- live-check: owed

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

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 20, feature)
  note:  23 file(s), 1042 line(s) changed outside intents/.
```

### Findings
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

### Not checked
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

### Live check
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

### Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

### Verified myself vs. taken on trust

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
