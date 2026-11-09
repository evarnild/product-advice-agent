---
name: sessions
description: The coordinator's read of all parallel product-advice-agent work — every worktree's intent status, gates, ahead/behind main, uncommitted files and what its Claude Code session is doing — turned into what needs the owner now, what can be reviewed, and in what order to merge. Use when the owner asks "where are we", "what's waiting on me", "what can I merge", or after a merge into main. Invoke as /sessions [--log N].
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/sessions@0.1.1
---

# /sessions — what is everyone doing

Run from the main checkout. This skill reads; it changes nothing.

## 1. Gather

- `npm run queue` — every intent by status (In flight, Queued, Shipped,
  Stopped), read from `metadata.yml` and the intents' branches. It is
  generated; there is nothing to keep in step with it.
- `npm run sessions` — the table (needs-you first), the rows behind `main`
  and the rows ready for review.
- `npm run sessions -- --log 30` (or the N the owner gave) when the table
  alone does not explain a row, e.g. a session that went `idle` hours ago.

## 2. Report, in this order

1. **Waiting on you.** Every `needs you` row, with its message. These
   sessions are blocked until the owner switches to them.
2. **Ready for review.** `status: in-review` rows. Suggest `/review <branch>`
   for each. When several are ready, suggest merging in this order: fewest
   files touched first, then the lower review tier. Each merge makes the
   others rebase, so the cheap ones go first.
3. **Behind main.** Rows with `-N` in `±main` and an open session. Write the
   rebase notice: *"main moved (§<merged id> merged). Rebase `<branch>` on
   main and re-run `npm run verify`."* If your harness can message other
   local sessions (ListAgents / SendMessage), send it to that session.
   Otherwise give the owner the text to paste.
4. **Stale.** Sessions idle or closed for more than a day with work not
   `in-review`, and worktrees whose branch is merged (suggest
   `/spawn <id> --remove`).

Keep it short: one line per session unless something is wrong.

## After a merge

When the owner says they merged §N: run step 1, send or draft the rebase
notice for every open session now behind `main`, and suggest
`/spawn N --remove`.
