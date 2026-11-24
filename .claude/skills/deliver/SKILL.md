---
name: deliver
description: Merge a reviewed product-advice-agent intent into main, do the bookkeeping, push, and remove its worktree and branch, stopping at the first step that fails. Use only when the owner asks to ship or merge a named intent, or asks whether it can ship. Invoke as /deliver <id>.
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/ship@0.1.0
---

# /deliver — merge a reviewed intent and clean up

You are the **coordinator** (the main checkout, on `main`). This skill wraps
`npm run deliver`, which does the steps as tested code. The rules it applies are
`REVIEW-POLICY.md` → "Merging" (preconditions, `--no-ff`, `verify`,
bookkeeping); read that section rather than relying on this file. The
queue is generated, so the bookkeeping commit holds `metadata.yml` and the
generated `stats.md` of the intent (§19); if the stats cannot be collected
the report says so and the ship goes on without that file.

## The request

`/deliver <id>` is the owner's explicit request, for intent §id only and in this
conversation, to record the live check (below), merge, push, and remove the
worktree and branch. Run nothing without that request, and never for an id
the owner didn't name. If no id was given, ask for it; don't guess one from
`npm run queue` or the sessions list. A request for one id doesn't carry over to
another.

## Run it

1. **The live check.** Add `--live-checked "<the owner's words>"` only when
   the owner's message invoking `/deliver` says they ran the live check (for
   example "live checked, /deliver 4"), quoting their words as they wrote them.
   Never add it from your own reading of the state, from `review.md`, or from
   your own run of the product. Without it, a live check that is owed and not
   recorded stops the run, which is the right outcome.
2. **Attribution.** Pass each attribution line your session was given for
   commits as `--trailer "<line>"` (repeat the flag). The script adds none of
   its own.
3. **Run:** `npm run deliver -- <id> [--live-checked "…"] [--trailer "…"]…`
4. **`/deliver <id> --dry-run`, or "can §N ship?"** or any question about
   readiness: run `npm run deliver -- <id> --dry-run` instead. It changes
   nothing (it does not even fetch) and prints every step as done, to do, or
   the first thing that would stop it.
5. **Where:** the script runs only from the main checkout, on `main`. From
   a worktree it stops at `start` with "run from the main checkout"; relay
   that, don't work around it.

## Relay the report

Give the owner the script's report as it is: one line per step (commit
hashes, the push range, removed paths), or the step it stopped at and why.
Then:

- **Stopped:** say which step and what the script advises. Don't work around
  it: no `--force`, no reset, no `branch -D`, no hand-editing to get past a
  check, and don't commit another session's uncommitted intent folder as your
  own. A red `verify` after the merge is reported, not undone; whether to
  revert is the owner's call.
- **"Left for you":** the worktree folder is held open by a session or an
  editor. Tell the owner to close it, then run
  `npm run deliver -- <id> --cleanup`. Don't stop processes.
- **Re-running** `/deliver <id>` after fixing what stopped a run resumes where
  it stopped; only on the owner's request.
- **Complete:** say so.

## After a complete ship: the eval baseline

When the shipped intent's `review.md` names an eval run (its `## Eval run`
section is not "not owed"), and only after the script reports complete, in
the main checkout on `main`:

1. Run `uv run advisor-analysis baseline evals/runs/<that report>`.
2. Commit `evals/baseline.json` alone, as `§<id>: eval baseline from
   <report>`, with the attribution lines you were given.
3. Do not push it unless the owner says so. If the report file is gone, say
   so and leave the baseline as it is.

This is part of the owner's `/deliver <id>` request. It cannot be done on the
branch: `deliver` refuses files changed after the reviewed commit.
