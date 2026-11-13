<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §18 plan — Record which intents must merge before another can be built

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A `blocked_by:` list in `metadata.yml` (spec B1–B4) that `npm run queue`
displays with chains and problems (B5), that `npm run spawn` and
`check:intent` enforce for direct open blockers (B6–B7), that `/auto` stops
on before spawn (B8), that the drafting skills and docs describe (B9), and
backfilled for §14, §15 and §17 (B10).

## Risks

- **Breaking existing metadata.** Files without the field must parse and
  check exactly as before; the kit tests over existing fixtures stay
  untouched and green.
- **Merge conflicts with the coordinator's own writes.** The coordinator
  edits `auto_*` lines of §14/§15/§17 on `main` while this branch is open.
  The backfill appends `blocked_by:` **at the end of each file, after the
  `links:` items**, far from the `auto_*` lines, so git merges both.
- **Reading "merged" from the wrong side** (B3): only `main`'s `merged:`
  counts; a test gives a branch copy with `merged:` set and `main` without.
- **Tests that pass whatever the code does**: chain and cycle tests use
  literal expected strings; spawn refusal is tested in a temp repo (as
  `spawn-intent.test.mjs` already does) asserting no worktree and no branch
  were created.
- **A gate confusion** (B2): `blocked_by` must not be in `GATE_FIELDS` or
  read by `parseGate`; a test asserts a blocked intent's gates still parse.
- Reviewed tier (`scripts/intent-check-lib.mjs`, `.claude/skills/**`).
  Pass 9's list is empty. Re-check the citations before launch.

## Verified against the codebase

Re-read on `main` at `7a1539b`.

- `scripts/intent-check-lib.mjs:45-68` — `parseMetadata`: `key:` with empty value starts a list; `^\s+-\s+(.*)$` items appended; `stripComment` drops ` #…`.
- `scripts/intent-check-lib.mjs:90` — `GATE_FIELDS = ['intent_accepted', 'spec_accepted', 'plan_approved', 'live_checked']`.
- `scripts/intent-check-lib.mjs:182` — `checkChange({ branch, metadata, intentDir, intentFiles, diff, review = null })` returns `{ errors, routes, notes, … }`.
- `scripts/check-intent.mjs:39-71` — `source` reads `intents/` from the named branch or the working tree; `:93` calls `checkChange`. Blocker state must come from `main` (`git show main:intents/<dir>/metadata.yml`).
- `scripts/queue-lib.mjs:39` `pickSource`; `:62` `queueLine` (parts joined by two spaces); `:75` `formatQueue`; `:87` `queueData` (the `flat` object for `--json`).
- `scripts/queue.mjs:56-77` — `collectEntries()` reads `main:intents/<dir>/metadata.yml` and the branch copy; `:79` `allIntentIds()` (main, every local branch, disk).
- `scripts/session-io.mjs:53` `readIntentMetadataFromBranch(root, id)`; `:80` `readIntentMetadata(root, id)`.
- `scripts/spawn-intent.mjs:114-127` — `spawn()`: reads metadata, then `git worktree add`; the refusal goes before `worktree add`.
- `scripts/*.test.mjs` — `node --test` suites run by `npm run test:kit` (in `verify`).
- `.claude/skills/auto/SKILL.md` — step 4 "Build" (line 144), the resume table (lines ~80-100), step 9 stops.
- `.claude/skills/spawn/SKILL.md:32` — step 4, "add `--base <ref>` only when the intent depends on an unmerged branch, and say so".
- `.claude/skills/intent/SKILL.md`, `.claude/skills/spec/SKILL.md`, `.claude/skills/build-plan/SKILL.md` — the drafting skills (B9).
- `intents/_templates/metadata.yml` — ends with `links:` and a commented example item.
- `intents/README.md` → "Who edits what", and the metadata field list.
- `intents/14-catalogue-500/metadata.yml`, `intents/15-fifty-cases/metadata.yml`, `intents/17-evals-every-change/metadata.yml` — each ends with `links:` items; none has `blocked_by`.

## Subtasks

1. **Pure blocker logic** (`scripts/blockers-lib.mjs`, new): `parseBlockers(metadata)`
   → `{ items: [{id, reason}], problems }` (non-digit id, self id, missing
   reason as a note) (B1, B4); `blockerState(id, mainMetaOf)` → open /
   cleared / unknown (B3); `openChain(id, graph)` → direct open ids and the
   further open ones, each once, in order (B5); `findCycles(graph)` (B5).
   Tests in `scripts/blockers-lib.test.mjs` (AC1, AC2's logic). Commit.
2. **Queue** (`queue-lib.mjs`, `queue.mjs`): `queueLine` appends
   `blocked by §14 (§13)` when open; `queueData` adds `blocked_by` and
   `blocked_by_open`; `formatQueue` prints problem lines (cycles, broken
   records, unknown ids) under the groups. `queue.mjs` builds the graph from
   each entry's picked metadata and `main`'s `merged:`. Tests (AC2, AC6 over
   fixtures). Commit.
3. **check:intent** (`intent-check-lib.mjs`, `check-intent.mjs`):
   `checkChange` takes `blockers` (`[{id, reason, state}]`) and adds an
   error per open or unknown blocker and per problem; `check-intent.mjs`
   reads each blocker's `main` metadata (and the local branches for
   "unknown"). Tests (AC4), including metadata without the field. Commit.
4. **Spawn** (`spawn-intent.mjs`): refuse before `worktree add` with B6's
   message; a broken record refuses too. Temp-repo tests (AC3). Commit.
5. **Skills and docs** (B8, B9): `/auto` step 4 gains the blocker check and
   the `blocked by <n>` stop, its resume table the row "blocked by N →
   spawn once cleared"; `/spawn` step 4 relays the refusal; `/intent`,
   `/spec`, `/build-plan` say how to fill `blocked_by`; template
   `metadata.yml` gains `blocked_by:` after `links:` with a comment;
   `intents/README.md` documents the field next to `links:` and in "Who
   edits what" (not a gate). Commit.
6. **Backfill** (B10): append `blocked_by:` with the spec's items at the end
   of §14, §15 and §17's `metadata.yml`; nothing else in those files.
   Commit.
7. **Finish**: `npm run verify`, `npm run check:intent`, `npm run queue`
   (paste the §14/§15/§17 lines), `status: in-review`, Progress entry.

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1 | `- 13    reason` → `{id:'13', reason}`; `- 13` → item + note; no field → `[]` | dropping the reason split; requiring a reason |
| B4 | `- x`, `- 18` on §18, unknown id → problems named | skipping a problem kind |
| B3 | main `merged: abc` → cleared; branch-only `merged:` → open; empty → open | reading the branch copy |
| B5 | 17→15→14→13 all open: `blocked by §15 (§14, §13)`; 14 cleared: `blocked by §15 (§13)`... as the graph gives; a repeat id printed once; JSON fields | stopping at depth 1; duplicates |
| B5 | cycle 17↔15 → one problem line naming both; the queue still prints | infinite loop; aborting |
| B6 | blocked → exit non-zero, message, no worktree, no branch; cleared → spawns | refusing after `worktree add` |
| B7 | open blocker → FAIL with the message; cleared → PASS; no field → as before; unknown → FAIL | ignoring blockers; failing on cleared |
| B2 | gates of a metadata with `blocked_by` parse unchanged | treating it as a gate |
| B10 | the repo's own §14/§15/§17 metadata parse to the spec's items | (data) |

## Validation

- `npm run verify` green (kit tests included); `npm run check:intent`
  PASS.
- `npm run queue` on the branch shows §14 `blocked by §13`, §15
  `blocked by §13, §14`, §17 `blocked by §13`.
- Live check: none expected (no rule-1 path, no `.claude/settings.json`);
  the review runs `queue` and a refused `spawn` in a temp repo.

## Assumptions I made

- A new `scripts/blockers-lib.mjs` rather than growing
  `intent-check-lib.mjs`; it is a kit path the Reviewed row already
  covers via `scripts/`… if the path table names only specific files,
  the tier is still Reviewed through `intent-check-lib.mjs` and the skills.
- `check-intent.mjs` treats an id missing from `main` but present on a
  local branch as **open**, not unknown.
- The backfill goes at the end of each file (merge-friendly), not next to
  `links:`'s header.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
