# §<id> spec — <title>

Accepted intent: [intent.md](intent.md)

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `docs/…` | <a decision or constraint, quoted> |
| `intents/<id>-…` | <a prior decision this builds on> |
| external docs (API, policy) | <the passage that binds this, with a link> |

## Behaviour

<What the system does, as observable behaviour. Number each item (B1, B2, …)
so plan.md and the tests can cite it.>

## Interpretations

<Every place the sources are ambiguous: the reading chosen and why. Each one
becomes a code comment at its implementation site.>

## Acceptance criteria

<Checkable statements, each mapped to a test or a live check. Example: "AC1:
a message with no order number gets the clarifying reply (test:
triage.test.ts)".>

## Non-functional

- **Boundaries:** <which module owns the logic, per CLAUDE.md>
- **Data:** <personal data touched, where it is stored, for how long>
- **Model use:** <which calls, prompt location, cost and latency budget,
  behaviour when the model is down or wrong>
- **Autonomy:** <what the agent may do without a human: answer, act, escalate>

## Out of scope

<What this deliberately does not do.>

## Assumptions I made

<…>
