---
name: grid
description: Draft or update product-advice-agent's AI-native SDLC grid (docs/sdlc-grid.md): the L0–L4 level per stage (Intent, Design, Build, Test, Deploy, Maintain), the evidence behind each, the outcome measures, and the two stages to move next. Use at the start of a quarter, after a pilot change, or when asked "where does product-advice-agent stand".
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/grid@0.1.2
---

# /grid — where product-advice-agent stands

The kit proposes and the owner decides. You pre-fill the grid from evidence,
and the user confirms it. The scan cannot see deliberate choices (for
example "Maintain is out of scope" or "Design and Build are one step for
features"), so keep any choices the user already recorded.

Stamp: keep or add `<!-- generated-by: product-advice-agent/grid@0.2.0 -->` as the
first line of `docs/sdlc-grid.md`.

## 1. Collect evidence; don't ask for it

```bash
npm run -s sdlc:scan            # readiness, intents, stamps, verdicts, outcome
git log --first-parent main --since=<last grid date> --oneline
```

Also read:
- the existing `docs/sdlc-grid.md`, for the previous levels and the user's
  declared choices;
- the `intents/*/metadata.yml` and `review.md` files;
- `.claude/skills/` and `.claude/agents/`, for what is codified.

## 2. Score each stage by what the level leaves behind

Use the cheat sheet in `docs/sdlc-grid.md` → "What each level means here". A
level counts only when its trace exists:

- **L1:** the artefact exists and is linked. Merged changes reference an
  intent id, `intents/<id>/` holds what the type requires, the context file
  is present, and `npm run verify` ran.
- **L2:** a versioned skill produced it, so the artefact carries a
  `generated-by:` stamp. This is required from the start; no
  self-assessment. Design (and the plan half of Build) count as L2 only for
  the specs (plans) that `npm run sdlc:scan` reports as made by `/spec`
  (`/build-plan`); a hand-written file counts as L1.
- **L3/L4:** a trigger fired, not a person. Show the hook or schedule
  config and its run log. Without that, it is not L3.

Levels can differ by intent type (for example Fix at L2, Feature at L1);
note the type beside the level. Score honestly: a grid that looks better
than the software is worse than none. Score a stage whose underlying
infrastructure is missing (no tests for a module, no way to observe it) at
its real level. Building that infrastructure is a legitimate move.

## 3. Outcome beside progress

Copy the scan's outcome block into the grid's measures table, with the date.
The strategy's rules:
- never report throughput without the revert rate beside it;
- if levels climbed for two quarters with no movement in the outcome, say
  so: the model is wrong for this area.

## 4. Propose the two moves

Pick the two stages where the bottleneck actually is. For each, say whether
to climb (go up a level) or widen (have more changes follow their type's
path). Give one sentence on why, and the concrete first step. Record both in
"The two we move".

## 5. Write and report

Update `docs/sdlc-grid.md` in place:
- the grid table and its evidence column;
- a new dated row in the measures table;
- the two moves;
- a dated changelog line.

Then tell the user:
- what moved since last time;
- what you could not verify;
- which levels you scored lower than they might expect, and why.
