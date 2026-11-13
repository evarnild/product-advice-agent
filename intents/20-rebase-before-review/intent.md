<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §20 — Rebase a branch that is behind main before each review round

**Type:** feature
**Originator:** me (owner), in the coordinator session: "Should we always
rebase (if needed) before we launch a review round"
**Source:** none (raised while §13 merged with §14, §15 and §17 open)

## Problem

A review round can start on a branch that is behind `main`, and nothing in
the kit notices. That costs in two ways.

1. **A rebase after a review throws the review away.** `REVIEW-POLICY.md`
   → "Merging": "Its `reviewed-commit` is an ancestor of the branch (`git
   merge-base --is-ancestor`). A rebase since the review means a new round."
   (enforced in `scripts/ship-lib.mjs`). A branch that has to rebase after
   its last review pays for a whole extra round.
2. **The review tests a combination that will never merge.** `verify` and
   the mutants run on the branch without `main`'s newer commits. Branch plus
   `main` is first tested by `verify` on `main` after the merge, when it's
   too late for review. Right now §13 has merged a test in `verify` that
   checks the eval cases against the catalogue, while §14 changes the
   catalogue and §15 adds 50 cases. A clash between them would be missed by
   every review round and caught only after a merge.

Today the only defence is advice:

- `/sessions` drafts a notice, "main moved (§<merged id> merged). Rebase
  `<branch>` on main and re-run `npm run verify`." (`.claude/skills/sessions/SKILL.md`)
  It runs only when someone thinks to use it.
- `/auto` is explicitly kept from acting on it: "never merge, push, rebase
  or delete a branch or worktree" (`.claude/skills/auto/SKILL.md`).
- `/review` doesn't check whether the branch is behind `main`.

## Outcome

- No review round (`/review` or `/auto`) starts on a branch that is behind
  `main` without either rebasing it first or saying it is behind and by how
  much.
- Under `/auto`, a branch that is behind is rebased and re-verified in its
  worktree before the reviewer is launched. A conflict or a red `verify`
  after the rebase stops the run with a reason of its own.
- The review report records the `main` commit it was checked against, so it
  shows whether the branch was current.

## Constraints

- **The coordinator never rebases in the main checkout.** CLAUDE.md:
  "**Never `git checkout` a branch in the main checkout.**" The rebase
  happens in the intent's worktree, done by the implementer or by a command
  run there.
- **No agent resolves a conflict by choosing behaviour.** A conflict whose
  resolution isn't mechanical is a stop, like "Needs decision:". The
  owner's answer then goes to the implementer.
- **The merge preconditions keep their meaning.** A rebase before a round
  never makes an earlier round's report count. Only the report of the round
  after the rebase can satisfy `/ship`.
- **Never push or force-push.** The rebase is local, as all branches here
  are until `/ship`.
- **No new dependency.** Kit only, Node ≥ 22.
- **Review tier:** Reviewed (`REVIEW-POLICY.md`, `.claude/skills/**`,
  `.claude/agents/**` and `.codex/agents/**` are all in the path table's
  Reviewed row).

## Type-specific questions

### Feature
- **Users:** the coordinator running `/auto` and `/review`, the implementer
  agent, and the owner (fewer wasted rounds, merges already tested against
  current `main`).
- **What exists today:** a rebase notice drafted by `/sessions`, sent by
  hand. `/auto` is forbidden to rebase. `/review` doesn't check.
- **Open design questions:**
  1. **Who rebases under `/auto`:** relaunch or resume the implementer with
     "rebase on main, run verify, report", or a small kit script the
     coordinator runs against the worktree path (`git -C <worktree> rebase
     main`), which aborts on conflict?
  2. **Manual `/review`:** rebase it as well, or only report "behind main by
     N" and ask?
  3. **`main` moves after the final review:** keep today's rule (`/ship`
     merges, then `verify` on `main`), or make `/ship` refuse a branch that
     is behind `main`? The second guarantees every merge was reviewed as it
     lands, but with parallel intents nearly every merge causes another
     round.
  4. **Rebase or merge `main` into the branch:** rebase keeps the reviewed
     diff clean but rewrites commits. Merging keeps the commits but puts
     `main`'s changes into the diff the reviewer reads.
  5. **Does a rebase before round 1 count against `/auto`'s three rounds?**
     (Presumably not: it's not a review.)
  6. **Should `check:intent` or `npm run sessions` warn about a behind
     branch in `in-review`,** so the manual path is covered too?

## Assumptions I made

- **Feature, not adjustment.** It would touch about five Reviewed-tier files
  (`.claude/skills/auto/SKILL.md`, `.claude/skills/review/SKILL.md`, both
  implementer definitions, `REVIEW-POLICY.md`), probably a script, and
  it has open design questions. The README says to use a feature for
  "anything with a design question".
- **The `/sessions` rebase notice stays** for sessions that are not under
  `/auto`.
- **"Behind" means `git rev-list --count <branch>..main` > 0,** measured
  against local `main`, since merges here are local.
- **I'd answer question 3 with "keep today's rule"** and question 4 with
  "rebase", as I recommended in the conversation. The spec decides.
