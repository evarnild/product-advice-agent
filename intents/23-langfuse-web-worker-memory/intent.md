<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §23 — Memory caps for the local Langfuse web and worker containers

**Type:** adjustment
**Originator:** me (the owner): "we need to reduce the memory footprint of langfuse", then "yes, create an intent to cap web and worker too"
**Source:** intents/21-clickhouse-low-memory (its Constraints put web and worker out of scope)

## Problem

§21 capped ClickHouse, but the two Langfuse application containers have no
limit at all. On 2026-11-23, shortly after `up -d`, `docker stats` showed
`langfuse-web` at 795 MiB and `langfuse-worker` at 712 MiB, each with the
whole Docker VM (7.7 GiB) as its limit, against 321 MiB for the capped
ClickHouse. Together they are now the largest share of `vmmemWSL`, and
nothing stops either from growing over days of uptime: both are Node
processes whose default heap ceiling is sized from the memory they can see,
which is the whole VM.

## Outcome

- After `docker compose -f infra/langfuse/docker-compose.yml up -d`,
  `docker stats` shows a limit of 1 GiB on `langfuse-web` and on
  `langfuse-worker` (today: 7.7 GiB), and each sits under 650 MiB at rest.
- Both Node processes run with a capped V8 heap (`--max-old-space-size=512`),
  so they collect garbage before reaching the container limit instead of
  being OOM-killed by it.
- Langfuse still works: all six containers are up and healthy, an
  `advisor-eval` run is traced, and its traces, scores and annotation
  queues open in the UI (the live check, rule 1, `infra/`).

## Constraints

- No image changes: images stay pinned (ADR 0001, `npm run check:pins`).
  Configuration only, in the compose file.
- No data loss, no volume touched. Local only, localhost-bound as today; no
  secret added.
- Nothing in `src/`, no core code, no new dependency.
- Out of scope: Postgres, Redis and MinIO (together under 180 MiB),
  ClickHouse (§21), and capping WSL itself (`.wslconfig`, a machine
  setting outside the repo).

## Type-specific questions

### Adjustment
- **Exactly what changes:**
  - `infra/langfuse/docker-compose.yml`: `langfuse-web` and
    `langfuse-worker` each gain `mem_limit: 1g` and
    `NODE_OPTIONS: --max-old-space-size=512` in their environment (per
    service, beside the shared `*langfuse-env` anchor, so the two can be
    tuned apart later);
  - `README.md`, the "Memory" note §21 added: one sentence for the web and
    worker caps;
  - `tests/test_compose.py`: one test in the style of §21's, asserting both
    services carry `mem_limit: 1g` and the `NODE_OPTIONS` heap cap.
- **Blast radius:** 3 files, about 20 lines, no core code. `infra/` owes a
  live check (rule 1).

## Assumptions I made

- The values (1 GiB container, 512 MiB V8 old space) suit this repo's load:
  one user, a few thousand traces, eval runs of 50 cases. A heavy UI page or
  a large ingestion batch could need more; the fix would be raising the
  values, not removing them. The live check is where they are proven.
- The Langfuse 4.78.0 images do not set `NODE_OPTIONS` themselves, so
  setting it adds the heap cap rather than replacing a flag they need. The
  build checks this with `docker inspect` on the two images before editing.
- The "under 650 MiB at rest" target is an estimate; much of each
  container's memory may be outside the V8 heap (Next.js and native
  buffers). If the live check shows the target missed while everything
  works and stays under the 1 GiB limit, the owner decides whether that is
  enough.
- Tier: the path table decides (`infra/` is not in the Reviewed list);
  `review_tier` left empty.
- No `blocked_by`: §21 is merged.
- An adjustment needs no spec or plan: `intent_accepted` is its gate.
