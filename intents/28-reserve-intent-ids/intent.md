<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §28 — Two machines can give two intents the same number

**Type:** feature
**Originator:** the owner ("So to avoid the number clashing, we should push
the intent early in the cycle", then "yes, draft it with the standing
exception", conversation, 2026-11-24)
**Source:** the §23 collision of 2026-11-24: commits `200092d` (merge of
`origin/main`), `6e272e5` and `40c447d` (the renumber to §27)

## Problem

On 2026-11-23 the owner worked on another machine. It drafted, built,
merged and pushed an intent numbered §23: "Memory caps for the local
Langfuse web and worker containers", in `intents/23-langfuse-web-worker-memory/`.
This machine had used §23 since 2026-11-16 for the typed Anthropic
adapter. That folder was never committed until 2026-11-24, and this
machine never pulled `origin/main`. Neither machine could see the other's
§23.

The clash surfaced only at the end of a full cycle: intent, plan, build,
two review rounds and a live check. `npm run deliver -- 23 --dry-run`
stopped with "origin/main has commits that main lacks"
(`scripts/deliver.mjs:143`). Untangling it took:
- a merge of `origin/main`;
- renaming the folder, `id`, branch and worktree;
- rebuilding the worktree's virtualenv;
- editing §24's references;
- a third review round (the merge counts as unreviewed changes).

The commit subjects before the rename still say "§23:", so `npm run stats`
attributes them to the wrong intent.

Why it can happen:
- `npm run queue -- --next-id` (`scripts/queue.mjs:80-91`,
  `nextId` in `scripts/queue-lib.mjs:167`) takes one more than the highest
  id on local `main`, local branches (`refs/heads` only), the folders on
  this disk and `OVERVIEW.md`. It never fetches or reads `origin`.
- An intent's number is visible to another machine only once its commit
  is pushed, and today that happens at `/deliver`, the last step.
- An agent may push only when the owner asks for that push in the current
  conversation (`REVIEW-POLICY.md` → "Merging"; `CLAUDE.md`, "An agent
  merges, pushes, …"; `AGENTS.md:27`). So no step pushes a draft early.

## Outcome

- A number `/intent` gives a new intent is reserved on `origin` when the
  draft is written, before any spec, plan or code. Another machine's
  `npm run queue -- --next-id` then returns a higher number.
- `npm run queue -- --next-id` counts intents on `origin`, after fetching,
  as well as locally. When the fetch fails (offline, no remote) it says so
  and still prints the local answer.
- The policy has one standing exception to "push only on request": the
  push that reserves a new draft intent's number. It is written in
  `REVIEW-POLICY.md` → "Merging" and mirrored in `CLAUDE.md`, `AGENTS.md`
  and `intents/README.md` → "Who edits what". It covers that push and
  nothing else.
- Re-running the 2026-11-24 situation (two clones, one with an unpushed
  §23 draft, the other pushing its own §23) in a kit test shows the second
  `/intent` getting §24, or the clash reported at `--next-id` time instead
  of at `/deliver`.

## Constraints

- The standing exception is narrow:
  - **What may be pushed:** only what reserves the number (the new draft
    intent's folder). Never code, never another intent's files, never a
    merge, a force push or a branch deletion.
  - **What happens otherwise:** if that push would carry anything else
    (local `main` ahead of `origin/main` with other commits), or would be
    rejected, the agent doesn't push. It says why and asks, as it does
    today.
  - Every other push stays "only when the owner asks".
- Changing `REVIEW-POLICY.md`, `.claude/skills/**` and the kit's enforcement
  scripts is **Reviewed tier**: the owner reads the full diff.
- The kit needs Node ≥ 22 and nothing else. No new dependency.
- `--next-id` must still work with no remote, and offline. The fetch is
  bounded in time, and its failure is a warning, not an error.
- Tests use local bare repositories as the remote (as
  `scripts/deliver.test.mjs` does), never GitHub.
- Out of scope:
  - renumbering existing intents;
  - rewriting the "§23:" commit subjects of §27's history;
  - pulling or merging `origin/main` automatically.

## Type-specific questions

### Feature
- **Users:** the owner, working on more than one machine; the coordinator
  session and `/intent` on each machine.
- **What exists today:**
  - `--next-id` reads local refs and disk only.
  - `/intent` writes the files and leaves committing to the owner (step 4
    of `.claude/skills/intent/SKILL.md`).
  - `/deliver` is the first step that pushes, and so the first to notice.
- **Open design questions for the spec:**
  1. **What carries the reservation.**
     - (a) Push the draft's commit on `main`, possible only when local
       `main` is `origin/main` plus that commit.
     - (b) Push a reservation ref that doesn't touch `main`, e.g. a branch
       or tag per intent such as `refs/heads/intent/28-slug`, holding the
       draft folder.
     - (c) Push the intent's own branch (`feat/28-…`) at draft time.

     (b) and (c) never push `main` and work when local `main` has unpushed
     work, as it did on 2026-11-24. `--next-id` must then read those refs
     on `origin`.
  2. **When `/intent` pushes:** at draft (`status: draft`), or only at
     acceptance. A draft that is later abandoned keeps its number either
     way, as ids are never reused (docs/decisions/0003).
  3. **Whether `--next-id` fetches every time** or reads `origin/*` as last
     fetched, with a `--fetch` flag. The fetch costs a network round trip
     on every queue call.
  4. **Whether `/deliver`'s dry run also reports** an id used on `origin`
     under another folder name, as an earlier and clearer message than
     "origin/main has commits that main lacks".
  5. **Spawn and the reservation ref:** if a reservation ref exists,
     `npm run spawn` should reuse or replace it, not fail on it.

## Assumptions I made

- **Feature, not adjustment:** it changes the kit's scripts, a skill and a
  policy rule, well over the adjustment budget, and the reservation design
  is open.
- **`review_tier: reviewed`:** `REVIEW-POLICY.md` and `.claude/skills/**`
  are on the Reviewed list.
- **The standing exception is the owner's explicit choice in this
  conversation** ("draft it with the standing exception"). The spec still
  has to word it, and the owner accepts that wording with the spec.
- **`OVERVIEW.md`'s §-numbers stay counted** by `--next-id`, as today.
- **Nothing blocks this.** It touches `scripts/queue*.mjs`, the intent skill
  and the policy texts, none of which an open intent changes.
