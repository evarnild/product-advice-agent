<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §18 — Record which intents must merge before another can be built

**Type:** feature
**Originator:** me (owner), in the coordinator session: "should we include in
the SDLC an explicit record of dependencies between intents so that we know
which intent cannot be built before another one"
**Source:** `auto_stopped` in `intents/15-fifty-cases/metadata.yml` and
`intents/17-evals-every-change/metadata.yml`; `.claude/skills/spawn/SKILL.md`
step 4

## Problem

Intents depend on each other, but the kit has no field for that, so the
build order is worked out again by whoever reads the intent next and is
recorded only as free text.

- `links:` holds both hard prerequisites and related work, and nothing tells
  them apart. §17 lists `intents/8-offline-evals    the runner and report it
  requires` (it can't be built without it) next to `intents/16-llm-judge
  its verdicts join the comparison once it exists` (it can go ahead without
  it).
- `/auto` worked out the order on the spot and wrote it into a field meant
  for something else: `auto_stopped: waiting for 13 to merge` (§17) and
  `auto_stopped: waiting for 14 to merge` (§15). The documented stop reasons
  in `.claude/skills/auto/SKILL.md` don't include this one.
- That free text is already incomplete. §17's links say it needs §15's case
  set (`the set an owed run uses`), and §15 is waiting on §14. So §17 is
  blocked by 13, 14 and 15, but its metadata names only 13. When §13
  merges, nothing will show that §17 still can't start.
- `/spawn` relies on judgement: "add `--base <ref>` only when the intent
  depends on an unmerged branch, and say so". Nothing checks that judgement,
  and `npm run queue` lists §15 and §17 as accepted, the same as an intent
  that is ready to build.

With up to three parallel sessions, a wrong order costs a worktree built on
the wrong base, a rebase, or a plan written against code that doesn't exist
yet.

## Outcome

- Each intent's metadata can say which other intents must be merged before
  it can be built. The tools read that, not free text. Related work that
  doesn't block stays separate.
- `npm run queue` shows which intents are blocked and by what, following
  chains (17 → 15 → 14). It reports a cycle or an id that doesn't exist.
- `npm run spawn`, `/auto` and `check:intent` act on the record: a blocked
  intent isn't spawned or carried forward by accident, and a broken record
  fails the check. §15 and §17 are backfilled, so the queue shows their
  real blockers.

## Constraints

- Kit code only: `scripts/*.mjs`, `.claude/skills/**`, the templates and
  `intents/README.md`. No change to `src/advisor/`.
- No new dependency. The kit needs "Node ≥ 22 and nothing else", and
  `metadata.yml` stays flat ("scripts/intent-check-lib.mjs parses it without
  a YAML dependency").
- The record is not a gate. An agent may write or change it while drafting
  (`/intent`, `/spec`, `/build-plan`) without the owner's yes. It must never
  stand in for, or block the recording of, a gate the owner gives.
- It is for hard prerequisites only ("can't be built correctly until it is
  merged"), so a related intent must not end up blocking the queue.
- Existing `metadata.yml` files without the field stay valid and mean "no
  blockers".
- Reviewed tier: the change touches `scripts/intent-check-lib.mjs` and
  `.claude/skills/**` (REVIEW-POLICY.md path table).

## Type-specific questions

### Feature
- **Users:** the owner reading the queue, the coordinator session running
  `/spawn` and `/auto`, and the skills that draft intents, specs and plans.
- **What exists today:** free-text `links:`, `/auto` improvising
  `auto_stopped` reasons, and `spawn --base` used on judgement.
- **Open design questions:**
  1. Field name and shape: `blocked_by: [13, 15]` (inline list of ids), or a
     block list with a reason per line, like `links:`?
  2. What "unblocked" means: merged into `main` only, or also "built on top
     of the blocker's branch" when `spawn --base feat/<n>-…` is given? If the
     second, how does `/ship` stop the dependent intent from merging before
     its blocker?
  3. Which gate a blocker holds back: `plan_approved` (a plan written against
     code that isn't there yet), spawn and implementation only, or both?
  4. Does `/auto` stop at the start of a run when an intent is blocked, or
     carry it through spec and plan and stop only before spawn? (Spec and
     plan can often be written against a blocker's accepted spec.)
  5. Should `npm run queue` list ids that appear in `blocked_by` but not in
     `links:`, or should `blocked_by` replace those `links:` lines?
  6. Does the `sdlc:scan` grid count anything from this (blocked time, say),
     or nothing for now?

## Assumptions I made

- **Feature, not adjustment:** it changes the metadata format, three scripts
  and at least three skills, which is well over the adjustment limit of 5
  files and 60 lines.
- **The backfill belongs to this intent:** §15 blocked by 14 (and 13, via
  its link "its consistency test checks the 50"); §17 blocked by 13 and 15
  (14 then follows through §15). Whether 13 really blocks 15 is for the
  spec to confirm.
- **`review_tier` is left empty**, because the path table already makes it
  Reviewed.
- **The field drafted in the earlier conversation (`blocked_by:`)** is a
  working name, not a decision; open question 1 settles it.
