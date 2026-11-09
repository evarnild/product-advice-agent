# product-advice-agent overview

A short orientation, edited rarely and by the owner. Nothing here tracks
status.

- **The queue** (what is in flight, queued, shipped or stopped, with type,
  status, gates and merge hash) is generated: `npm run queue`. It reads
  each `intents/<id>-<slug>/metadata.yml` (from the intent's branch while
  that branch is unmerged, else from `main`). `npm run queue -- --next-id`
  prints the id a new intent takes. Nobody edits a queue by hand.
- **Work items** live in `intents/<id>-<slug>/`; see
  [`intents/README.md`](intents/README.md). A new idea is a draft intent
  (`/intent`), which the queue lists under Queued once it is committed.
- **How a change moves** from intent to merge: [`sdlc.md`](sdlc.md).

## Snapshot

- 2026-11-09: repository created with the AI-native SDLC kit (ai-sdlc-kit).
  Stack: Python + uv + Langfuse (self-hosted), decided in
  [`docs/decisions/0001-stack.md`](docs/decisions/0001-stack.md) (§1).

## Next

- The evaluation suite and real guardrail checks, as new intents
  (`npm run queue -- --next-id`).
