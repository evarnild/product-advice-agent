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
  There is no product code yet. Stack: intended stack Python + Langfuse (self-hosted), confirmed by §1.

## Next

- The first intent (id 1, the one `npm run queue -- --next-id` prints):
  confirm the Python + Langfuse (self-hosted) stack and build the project skeleton. Extend `npm run verify`
  with build, lint and test. Write `CLAUDE.md` → "Architecture". Narrow
  `CORE_CODE`. Name the live-check and Reviewed-tier paths. Define
  `npm run setup:worktree` if a fresh worktree needs dependencies. Start it
  with `/intent --feature`.
