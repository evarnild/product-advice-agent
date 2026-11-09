<!-- generated-by: product-advice-agent/grid@0.1.0 -->
# product-advice-agent — AI-native SDLC grid

One area: the whole repository. Owner: eric.varnild. Refresh with `/grid` at
the start of each quarter or after a pilot change. The numbers come from
`npm run sdlc:scan`, not from memory.

Model and levels: six stages (Intent, Design, Build, Test, Deploy,
Maintain) and five levels (L0–L4). Each stage ends in an artefact the next
one reads, with humans at the gates. The kit was first built for heraklios
(github.com/evarnild/heraklios), whose `docs/sdlc-grid.md` is a worked
example.

## The grid — 2026-11-09 (first fill, before any product code)

| Stage | Level | Evidence | Gap to next level |
| --- | --- | --- | --- |
| **Intent** | L1 (kit only) | `intents/`, templates, types and the `/intent` skill exist. No intent has been written yet | L2: §1 drafted by `/intent` and accepted through its gate |
| **Design** | L0 | No spec yet; the `/spec` skill exists | L1: §1's `spec.md`, accepted at its gate (L2 when `/spec` produced it) |
| **Build** | L1 (kit only) | `CLAUDE.md`; plans are approved before code (enforced by `check:intent`); versioned implementer agent (Claude + Codex); `/build-plan`, `/spawn` + `/sessions` (worktree per intent, session hooks), `/auto` | L2: hooks that block unsafe actions (push, `git checkout` in the main checkout) |
| **Test** | L0 for product, L1 for kit | `npm run verify` runs the kit's 254 tests; there is no product suite | L1: §1 adds the product's tests to `verify`, plus a dependency and secret check |
| **Deploy** | L1 (policy only) | Written `REVIEW-POLICY.md` with tiers; `/review` and the reviewer agent; `/ship` checks the merge preconditions as tested code | L2: every merge goes through `/review` with a stamped `review.md` |
| **Maintain** | L0 | Nothing runs, so there is nothing to observe | L1: findings written as fix intents once the agent handles real conversations |

**Production release stays human by design**: any deployment and any push
stay manual gates at every level.

**Declared choices** (the scan can't see these, so keep them on refresh):
- Merges are local. The review report is a committed `review.md`, not a PR
  comment.
- The kit is stack-agnostic until §1 (intended stack Python + Langfuse (self-hosted), confirmed by §1). Its scripts need only Node.

## The two we move — Q4 2026

1. **Intent → L2 (climb).** Run `/intent --feature` for §1 (stack and
   skeleton) and take it through every gate.
2. **Test → L1 (climb).** §1 makes `npm run verify` run the product's build,
   lint and tests. Until then, nothing in `src/` can be attested.

## Measures

Report progress and outcome together, never one without the other. Never
read throughput without the revert rate beside it.

| Date | Window | Changes on main | Per week | Reference an intent/§ | Reverts | Intents (stamped) | Attested / reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-09 | repo start | 1 (the kit scaffold) | — | — | 0 | 0 (0) | — |

## What each level means here

| Stage | L1 · by hand | L2 · codified | L3 · triggered | L4 · closed loop |
| --- | --- | --- | --- | --- |
| Intent | `intents/<id>/intent.md` written with an assistant, type declared, accepted in metadata | `/intent` drafted and validated it (stamp) | a user report or a monitor drafts the intent itself | intents drafted, deduplicated and ranked unattended |
| Design | `spec.md` written by hand for features | a `/spec` skill loads conventions and prior decisions | accepting an intent fires the spec pass | specs produced unattended; only flagged concerns reach you |
| Build | context file; plan approved before code | shared skills and agents for plan, implement, verify; hooks block unsafe actions | an accepted spec fires plan generation | approved plans implemented unattended where the checks carry it |
| Test | `npm run verify` with a fresh context; failing test first for fixes; security check | test files protected during fixes; a verification skill; an eval suite where the product uses a model | a new change fires verification automatically | verification repairs its own failures within limits |
| Deploy | written review policy; agentic review on every change | tiers applied automatically from the policy; gates enforced as hooks | a verified change fires review; you act on the report | everything up to the release gate unattended (ceiling) |
| Maintain | findings written as fix intents | scheduled evals or soak runs; deterministic checks | a failure fires diagnosis; you triage | findings written back as intents unattended |

Don't skip L1, and don't automate a stage past the point where its output
can be checked.

## Changelog

- 2026-11-09: first fill, alongside the kit scaffold.
