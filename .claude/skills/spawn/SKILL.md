---
name: spawn
description: Start a parallel product-advice-agent session for an intent — a worktree on the intent's branch in ../product-advice-agent-wt/, its own dependencies (npm run setup:worktree, when defined), a reserved port and a CLAUDE.local.md brief — or take one down after merge. Use from the main checkout when the owner wants to work on an intent alongside others. Invoke as /spawn <id> [--base <ref>], or /spawn <id> --remove.
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/spawn@0.1.1
---

# /spawn — one intent, one worktree, one session

You are the **coordinator** (the main checkout). This skill wraps
`npm run spawn`; the rules it serves are in `CLAUDE.md` → "Parallel sessions".

## Spawning

1. **Check you are the coordinator.** `git rev-parse --show-toplevel` must be
   the first entry of `git worktree list`. If not, stop and say so.
2. **Find the intent.** `intents/<id>-*/metadata.yml` must exist here. If the
   owner names work that has no intent yet, run `/intent` first and stop.
   Spawning doesn't require gates, because a session can draft the missing
   spec or plan. But say which gates are still empty, because the session
   may not write code before them.
3. **Check the load.** Run `npm run sessions`. If three or more intent
   sessions are already open (anything not `closed`) or implementers you
   launched are still running, say so and ask before adding a fourth.
   Merges are serial and the owner reviews each one, so more sessions
   mostly add waiting.
4. **Spawn.** `npm run spawn -- <id>` (add `--base <ref>` only when the intent
   depends on an unmerged branch, and say so). If the intent folder was
   uncommitted here, the script moves it into the worktree. Tell the owner
   that.
5. **Launch or hand over.** Read the worktree's `metadata.yml`. The gate the
   type needs is `plan_approved` for a feature, fix or refactor, and
   `intent_accepted` for an adjustment or experiment. A bare date and
   `<date> by-agent` both count as recorded; anything else does not.
   - **Recorded:** launch `product-advice-agent-implementer` with the `Agent` tool and
     `run_in_background: true`, working in the spawned worktree (not
     `isolation: "worktree"`). The brief carries the worktree path, branch,
     port and intent folder, and says the branch already exists and is
     checked out there (so skip the agent's "branch from main" step), to use
     absolute paths there and to leave the main checkout alone. Report that it was launched, with path,
     branch, port and gates. Don't poll; you are notified when it ends.
   - **Missing:** don't launch. Report the path, branch, port and gates, say
     which gate is missing, and give the hand-over: `cd "<path>" && claude`,
     or open the folder in the Claude Code desktop app.
6. **On completion.** Report the implementer's result (branch, commits,
   verify output, assumptions) and offer `/review`. Outside an `/auto <id>`
   run (`.claude/skills/auto/SKILL.md`), don't run it unprompted; never
   record a gate or merge; those stay with the owner.

## Removing (`--remove`)

Only after the owner has merged the branch.

1. `npm run spawn -- <id> --remove`. The script refuses when the branch isn't
   merged into `main`, when the worktree has uncommitted files, or when a
   top-level entry is a symlink or junction (a recursive delete would follow
   it into another checkout). Report the refusal as it is. Don't
   reach for `--unmerged` or `--force` unless the owner asks.
2. Mention the `git branch -d <branch>` the script prints. Deleting the
   branch is the owner's call.
