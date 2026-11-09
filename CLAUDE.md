# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project overview

product-advice-agent: A small product-advice agent for a synthetic electronics catalogue, with evaluation, tracing and guardrails.

So far the repository holds only the
AI-native SDLC kit (from ai-sdlc-kit, first built for heraklios). The
product's stack and architecture are **§1's decision** (intended stack Python + Langfuse (self-hosted), confirmed by §1). Until §1
merges, there is no product code, and no section below describes any.

## Commands

```
npm run verify        # THE check before a change is done (today: the kit's own tests)
npm run check:intent  # does this branch's change match its intent? (intents/README.md)
npm run sdlc:scan     # the evidence behind docs/sdlc-grid.md
npm run queue         # the intent queue, generated from metadata.yml (--next-id, --json); nobody edits it
npm run spawn -- <id> # parallel session for an intent (see "Parallel sessions")
npm run sessions      # what every worktree/session is doing (--json for data, --log for the event tail)
npm run ship -- <id>  # merge a reviewed intent, bookkeep, push, remove worktree and branch (the /ship skill)
npm run test:kit      # node --test over scripts/*.test.mjs
```

The kit needs Node ≥ 22 and nothing else: no `npm install`. §1 extends
`verify` with the product's build, lint and tests, whatever the stack is.
Keep it **one** command.

## How work flows

`sdlc.md` is the step-by-step version for the owner: intent → spec → plan →
build → review → merge, and what each type requires. If it disagrees with the
rules below or with `intents/README.md` and `REVIEW-POLICY.md`, those win.

- The queue is generated, never hand-kept: `npm run queue` lists every
  intent with its status (from its branch while unmerged, else `main`).
  `OVERVIEW.md` is the short, owner-edited snapshot. Each work item's detail
  lives in `intents/<id>-<slug>/`: intent, spec (features), plan, review
  report, metadata. Read `intents/README.md` for the types, the gates and
  branch naming (`feat/2-…`, `fix/2-…`).
- No code before the plan's gate is recorded in `metadata.yml`.
- `/intent` drafts an intent, `/spec` a feature's spec, `/build-plan` a
  plan, `/review` runs `REVIEW-POLICY.md` and writes `review.md`, `/grid`
  refreshes `docs/sdlc-grid.md`, `/spawn` and `/sessions` run parallel work
  (below), and `/ship <id>` merges a reviewed intent when the owner asks
  (`REVIEW-POLICY.md` → "Merging").
- The `product-advice-agent-implementer` agent builds an approved plan, and the
  `product-advice-agent-reviewer` agent does the adversarial passes for `/review`.
- `/auto <id>` (coordinator only) carries one accepted intent through the
  steps above: spec (a feature stops once, for the owner's `spec_accepted`),
  plan, spawn, implement, review, and rework, for at most three review
  rounds. The owner's `/auto <id>` is a request to record that intent's
  `plan_approved` and nothing else (`intents/README.md` → "Who edits what").
  It stops for the owner's questions, a "Needs decision:" finding, an
  `escalate` verdict (the owner reads the diff; the next `/auto <id>` goes
  on), a spec or plan amendment, running out of rounds, the live check, a
  CRITICAL finding, any red it cannot trace, a re-check mismatch, a plan
  that exists unapproved, a ship dry-run that is blocked, a worktree held by
  another session, a fourth open session or an agent error, and ends at
  "ready: `/ship <id>`". It never ships, and never records `spec_accepted`
  or `live_checked` without the owner's yes; the `/auto` authorisation
  covers neither. A stop shows in `npm run sessions` as
  `auto · r<n> · <reason>`.
- An agent records a gate (`metadata.yml`) only on the owner's request in
  the current conversation, with `by-agent` after the date; a subagent never
  does (`intents/README.md` → "Who edits what").
- Merges into `main` are local. An agent merges, pushes, deletes a branch
  or removes a worktree only when the owner explicitly asks for that action
  in the current conversation, never on its own initiative, and only after
  the preconditions in `REVIEW-POLICY.md` → "Merging".
- **Never `git checkout` a branch in the main checkout.** It belongs to the
  coordinator session. Implementers and reviewers work in their own
  worktrees.
- A change owes a **live check** when `REVIEW-POLICY.md` → "Live checks"
  says so. The owner runs it; `live_checked: <date>` is recorded, by the
  owner or by an agent on their request, before the merge. An agent's own
  run is evidence, never that gate.

## Parallel sessions

Several intents can run at once, each in its own worktree with its own
Claude Code session. One session, in the main checkout, is the
**coordinator**.

```
npm run spawn -- <id>           # worktree ../product-advice-agent-wt/<id>-<slug> on the intent's branch,
                                # npm run setup:worktree if defined, port 5200+(id mod 100), CLAUDE.local.md brief
npm run spawn -- <id> --remove  # after merge; refuses if unmerged, dirty or holding a link
npm run sessions                # every worktree: status, gates, ±main, dirty, session state
npm run sessions -- --log 30    # the raw event tail
```

- **State lives in three places, each with one owner.** Intent status and
  gates are in `metadata.yml` on the intent's branch; `npm run sessions`
  reads it from each worktree. Git facts (ahead/behind, uncommitted files)
  come from git. What each session is doing is in
  `.git/product-advice-agent-sessions.jsonl`, written by the hooks in
  `.claude/settings.json` on start, prompt, turn end, notification and end.
  That file is never committed, and no agent writes to it by hand. It holds
  **no prompt text**: a prompt is logged by its length only. Events are
  filed under the session's project directory, so a session that `cd`s into
  another worktree still shows as itself. A permission prompt or question
  shows as `needs you`. Claude Code's idle "waiting for your input"
  reminder shows as `idle`, but never hides a prompt still waiting on you:
  only your next prompt, the turn ending or the session ending clears it.
- **Only the coordinator** runs `/spawn`, `/sessions`, `/review` and
  `/auto`, and sends "main moved, rebase" notices. The owner merges (or
  asks the coordinator to, per "Merging"), one branch at a time, running
  `npm run verify` on `main` after each merge.
- **A spawned session** works only on its branch and its intent. Its
  `CLAUDE.local.md` (gitignored, written by spawn) says which intent, branch
  and port it has. It never edits the queue (it is generated), never
  merges, and sets `status: in-review` when done.
- **`/spawn` launches the implementer itself** when `metadata.yml` already
  records the gate the type needs (`plan_approved` for feature/fix/refactor,
  `intent_accepted` for adjustment/experiment): a background
  `product-advice-agent-implementer` agent working in the worktree. With a gate missing
  it hands over instead. On completion the coordinator reports and offers
  `/review`; outside an `/auto <id>` run (`.claude/skills/auto/SKILL.md`) it
  never runs it unprompted, and it never records a gate or merges.
- **A launched implementer is not a session in `npm run sessions`.** Hooks
  run per session and file events under `CLAUDE_PROJECT_DIR`, so the
  implementer files none under the worktree (its row shows `no events`) and
  the coordinator's row reflects only the coordinator's own session.
  Progress shows in the worktree's `status`, `dirty` and `ahead` columns
  (the implementer commits early), and `in-review` means it finished.
- Keep it to about three intent sessions (or launched implementers) at
  once. Merges and reviews are serial, so more sessions mostly add rebases.
- Spawned worktrees live outside the repo on purpose, so the project's
  tools never pick up a nested checkout. Each worktree installs its own
  dependencies: §1 defines `npm run setup:worktree` (for example `npm ci` or
  `uv sync`) once the stack has any, and spawn runs it.

## Architecture

None yet. §1 writes this section: the modules, the boundary between pure,
tested logic and I/O (model calls, channels, storage), and the conventions
worth knowing before editing. When it does, it also:

- narrows `CORE_CODE` in `scripts/intent-check-lib.mjs` to the modules whose
  mistakes cost most;
- names the runtime paths that owe a live check (`REVIEW-POLICY.md` →
  "Live checks", rule 1);
- names the paths behind the Reviewed tier's "by meaning" list (prompts,
  user-facing output, credentials, personal data);
- defines `npm run setup:worktree` if a fresh worktree needs dependencies
  installed before `npm run verify` can pass.

## Conventions that already apply

- Model calls and external APIs are faked or recorded in tests, never called
  live from the suite.
- No secret, token or real user data is committed, including in fixtures
  and logs.
- No new dependency arrives without a line in the intent's `plan.md` saying
  why.
