# §<id> plan — <title>

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

<One paragraph: what the change achieves, in terms of the intent's outcome.>

## Risks

<What could go wrong: the classes of bug this project has hit before (see
REVIEW-POLICY.md pass 9), tests that pass without proving the behaviour,
stale line citations, plus anything specific to this change.>

## Verified against the codebase

<Every file, symbol and line this plan relies on, re-read on current main.
`path:line — what is there`. Line numbers rot; re-check before launch.>

## Subtasks

1. <Small, ordered, each independently committable.>

## Tests

<The test contract: edge cases, negative paths, error handling, async code,
integration boundaries (model calls, external APIs: faked or recorded, never
live in the suite). For a fix, the failing-first test. For each behavioural
line, which test would fail if it were mutated.>

## Validation

- `npm run verify` green
- `npm run check:intent` PASS (or ROUTE with a reason recorded in review.md)
- Live check: <what the owner will run and look at, or "none, and why">

## Assumptions I made

<…>

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
