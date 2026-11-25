---
name: build-plan
description: Draft or revise the plan (intents/<id>-<slug>/plan.md) for an accepted product-advice-agent feature, fix or refactor, stamped as made by this skill. Use after spec_accepted (feature) or intent_accepted (fix, refactor) is recorded, or when a review sends its plan back. Invoke as /build-plan <id>.
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/build-plan@0.1.0
---

# /build-plan — draft and validate an intent's plan

Follow `intents/README.md` → "Drafting an artefact" for everything the three
drafting skills share. This file adds only what is the plan's own. It is not
Claude Code's plan mode, and it writes `plan.md` in the intent's folder.

Stamp: `<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->` as the first line
of `plan.md`.

## Who drafts

The coordinator does not read the codebase inline to draft plan.md. It spawns
`product-advice-agent-plan` with the `Agent` tool and a description beginning `§<id> plan`
(that prefix is what `npm run stats` books to the plan phase). The brief is
the intent id, the `main` hash and what is already known (the owner's answers,
prior decisions). The hand-off rules (one file, scratch folder, no commit, no
gate, the reply) are in that agent's definition, `.claude/agents/product-advice-agent-plan.md`;
this file says how to draft. The agent runs on Sonnet; pass a `model` for a plan that must judge a self-contradicting intent.

After the agent returns, run `git status --short` and `git diff --stat`.
Confirm that only `plan.md` changed and that `metadata.yml` is untouched; if
anything else changed, discard it and report. Then read the draft as the steps
below say.

## 1. Check the preconditions, and stop if one fails

Read `intents/<id>-*/metadata.yml`. Stop and say which is missing if:

- `type` is adjustment or experiment (neither has a plan);
- the gate before the plan is not recorded: `spec_accepted` for a feature,
  `intent_accepted` for a fix or refactor.

## 2. Read first

- the intent, and the spec for a feature;
- `intents/_templates/plan.md`;
- `REVIEW-POLICY.md`: tiers, live checks, the review passes;
- every file, symbol and line the plan will rely on, on current `main`.

## 3. No question round

A question at plan time means the spec (or, for a fix or refactor, the
intent) is incomplete. Report it and stop; do not decide a design point
here. When the agent does the drafting, this stop is its `INCOMPLETE:` reply.

## 4. Write `plan.md` from the template

- Goal;
- Risks: the bug classes `REVIEW-POLICY.md` pass 9 names for this repo,
  tests that pass whatever the code does, stale line citations, a lint cap
  once there is one, plus anything specific;
- **Verified against the codebase**: "Re-read on `main` at `<hash>`", then
  `path:line — what is there` for each reliance;
- Subtasks, each committable with `npm run verify` green;
- Tests: for each behavioural line, the test that would fail if it were
  mutated; for a fix, the failing-first test;
- Validation: `npm run verify`, `npm run check:intent`, any end-to-end
  suite the paths call for, and the live-check steps when one is owed by
  path;
- Assumptions I made;
- the `## Progress` marker, left empty.

## 5. Validate

- every spec B and AC (feature), or intent outcome (fix, refactor), maps to
  a subtask and a test or check;
- every `path:line` was read at the recorded commit;
- no subtask needs a gate that is not recorded.

## 6. Report

If the plan found a hard prerequisite (this intent cannot be built correctly
until another is merged), add it to `blocked_by:` in `metadata.yml` as
`<id>    <reason>` (not a gate; related work stays in `links:`) and say so here (the agent reports a prerequisite; the coordinator writes
`blocked_by:`).
Name the folder, the weak points, and the next step: "approve by setting
`plan_approved: <date>` in metadata.yml, or say yes".
