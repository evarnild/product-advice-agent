<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §18 spec — Record which intents must merge before another can be built

Accepted intent: [intent.md](intent.md)

Written against `main` at `4013c7f`.

## Owner's decisions (question round, 2026-11-13)

- **Field:** "Block list with reasons": `blocked_by:` as a list like
  `links:`, one blocker per line with its reason.
- **Cleared:** "Merged into main only".
- **Holds back:** "Spawn and build only": spec and plan may be written;
  spawn refuses, `/auto` stops before spawn, `check:intent` FAILs a branch
  with an unmerged blocker.
- **Links:** "Separate; links keeps related only": hard prerequisites
  move to `blocked_by`; `links:` stays for related work; `sdlc:scan`
  counts nothing new.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `scripts/intent-check-lib.mjs:45-68` `parseMetadata` | Lists already parse: a `key:` with an empty value starts a list, `  - item` lines are appended, `#` starts a comment. `blocked_by` needs no parser change. |
| `intents/_templates/metadata.yml` | "Format is flat on purpose — scripts/intent-check-lib.mjs parses it without a YAML dependency"; `links:` written as `  # - intents/1-stack-and-skeleton    related intent`. |
| `scripts/queue-lib.mjs:28-43` `pickSource` | Which metadata speaks for an intent (branch while unmerged, else `main`); B5 reads `blocked_by` from that source and "merged" from `main`. |
| `scripts/spawn-intent.mjs:114-127` `spawn()` | Reads the intent's metadata, then `git worktree add -b <branch> <path> --base`; B6 refuses before this. |
| `scripts/intent-check-lib.mjs:182` `checkChange` | The pure check behind `check:intent`; B7 adds its blocker errors. `ship` already requires `check:intent` PASS, so a dependent cannot ship first. |
| `.claude/skills/auto/SKILL.md` step 4, step 9 | Build is step 4; stops write `auto_stopped`. B8 adds the stop before spawn. |
| `.claude/skills/spawn/SKILL.md` step 4 | "add `--base <ref>` only when the intent depends on an unmerged branch, and say so". |
| `intents/README.md` → "Who edits what" | Gate rules; B2 states the field is not a gate. |
| `intents/15-fifty-cases/spec.md`, `intents/17-evals-every-change/spec.md`, `intents/14-catalogue-500/spec.md` | The dependencies the backfill records (B10). |

## Behaviour

**The record**

- **B1.** `metadata.yml` may carry `blocked_by:` as a list; each item is
  `<id>    <reason>`: an intent id (digits), whitespace, and a reason in
  words. An item without a reason is valid but noted. Absent or empty
  means no blockers.
- **B2.** `blocked_by` is not a gate: any agent drafting or revising an
  intent, spec or plan may write it without the owner's yes; it never
  changes or blocks recording a gate. A hard prerequisite only: "cannot be
  built correctly until that intent is merged". Related work stays in
  `links:`.
- **B3.** A blocker is **cleared** when `main`'s `metadata.yml` for that
  id has a non-empty `merged:`; otherwise it is open (whatever its
  branch says).
- **B4.** A record is **broken** when an item's id has no intent on `main`
  or on any local branch, names the intent itself, or is not digits.

**What reads it**

- **B5.** `npm run queue` marks each intent with open blockers:
  `blocked by §14 (§13)`: the direct open blockers, then in parentheses
  the further open ones reached through them (following chains, each id
  once). `--json` adds `blocked_by` (direct ids with reasons) and
  `blocked_by_open` (every open id, direct and through chains). A cycle
  (17 → 15 → 17) or a broken record is printed as a problem line under the
  list, naming the intents; the queue still prints.
- **B6.** `npm run spawn -- <id>` refuses an intent with an open direct
  blocker, before creating anything: "§<id> is blocked by §<n> (<reason>),
  not merged into main. Ship §<n> first." A broken record also refuses.
  `--remove` is unaffected.
- **B7.** `check:intent` on an intent's branch FAILs when a direct blocker
  is open ("§<id> is blocked by §<n>, which is not merged into main") or
  the record is broken. The blocker state is read from `main`; the pure
  `checkChange` receives it as input.
- **B8.** `/auto <id>`: spec and plan go ahead as now; before step 4
  (spawn), an open blocker stops the run with
  `auto_stopped: blocked by <n>` (the lowest open direct id), reported with
  every open blocker. A later `/auto <id>` resumes at spawn once they are
  cleared. The skill's stop table lists this reason; the improvised
  "waiting for N to merge" is retired.
- **B9.** The drafting skills: `/intent` asks for, or records, hard
  prerequisites in `blocked_by` (with reasons) and keeps `links:` for
  related work; `/spec` and `/build-plan` add a blocker they discover and
  say so in their report; `/spawn` relays B6's refusal and no longer
  relies on judgement for `--base`. The template gains `blocked_by:` with
  a comment; `intents/README.md` documents the field next to `links:`.

**The backfill**

- **B10.** This change records, on its branch:
  - §14: `- 13    its consistency test checks the growth (spec, "Built after §13 merges")`;
  - §15: `- 13    its consistency check is extended (spec B4)` and
    `- 14    the 50 cases are written against the 500-product catalogue`;
  - §17: `- 13    reads catalogue_sha256 from run reports (spec, Assumptions)`.

  Their `links:` lines for those ids stay (they still describe the
  relation). `auto_stopped` is not touched by the implementer; the
  coordinator rewrites it at the next `/auto` of each.

## Interpretations

- **§17 and §15** (intent Assumptions say §17 is blocked by 13 and 15):
  §17's accepted spec says "Built after §13 merges … not dependent on §15
  or §16", so the backfill records 13 only. The spec wins over the intent's
  assumption; the owner may add 15.
- **"Follows chains"** (intent Outcome) is display (B5); spawn and
  `check:intent` check direct blockers only, since a merged direct blocker
  was itself unblocked to merge.
- **"Related work that doesn't block stays separate"**: `links:` is not
  read by any of B5–B8.

## Acceptance criteria

- **AC1** (B1, B4): parse tests: items with and without reasons; non-digit
  id, self id, unknown id → broken with the reason named. (kit test)
- **AC2** (B3, B5): queue-lib tests over in-memory metadata: open vs
  cleared by `merged:` on main; a branch's `merged:` ignored; chains
  17 → 15 → 14 → 13 printed as `blocked by §15 (§14, §13)`; cleared links
  dropped from the chain; a cycle reported once; JSON fields. (kit test)
- **AC3** (B6): spawn refuses with the message and creates no worktree or
  branch; succeeds once the blocker has `merged:` on main. (kit test, in a
  temp repo as the existing spawn tests do)
- **AC4** (B7): `checkChange` FAILs on an open blocker and on a broken
  record, passes with cleared blockers or none; existing metadata without
  the field passes as before. (kit test)
- **AC5** (B8, B9): the skills and docs say what B8–B9 say. (review reads
  them)
- **AC6** (B10): after the change, `npm run queue` on the branch shows §14
  `blocked by §13`, §15 `blocked by §13, §14`, §17 `blocked by §13`. (kit
  test over the repo's own intents, or the review runs it)

## Non-functional

- **Boundaries:** kit only (`scripts/*.mjs`, `.claude/skills/**`,
  `intents/_templates/`, `intents/README.md`, the three backfilled
  `metadata.yml`). No `src/advisor/` change.
- **Dependencies:** none; Node ≥ 22; the flat format.
- **Model use:** none.
- **Autonomy:** agents write `blocked_by` freely (B2); gates stay the
  owner's.
- **Tier:** Reviewed (`scripts/intent-check-lib.mjs`, `.claude/skills/**`).
  No live check expected beyond the review running `queue` and a dry
  spawn; rule 2 does not apply (no `.claude/settings.json`).

## Out of scope

- Stacked branches (`--base feat/…` counting as cleared); a `ship` change
  beyond the existing `check:intent` precondition; `sdlc:scan` counts;
  `/sessions` showing blockers (it shows `auto_stopped`, which carries
  "blocked by N"); an override flag for spawn.

## Assumptions I made

- **Reason format:** whitespace-separated after the id, like `links:`
  (intent question 1's block form).
- **No override flag** on spawn: editing `blocked_by` is the override.
- **Direct blockers only** for refusals (B6–B8), chains for display (B5).
- **Backfill** as B10, with §17 not blocked by 15 (Interpretations).
- **`/sessions`** gains nothing; the `auto_stopped` reason carries it.
