<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §4 — Move the local Langfuse stack to v4

**Type:** feature
**Originator:** the owner ("move to langfuse v4"), after the Langfuse UI
said v3 is deprecated during §1's live check
**Source:** §1's live check (2026-11-10); `infra/langfuse/docker-compose.yml`

## Problem

The self-hosted Langfuse stack that §1 ships
(`infra/langfuse/docker-compose.yml`) runs Langfuse v3 (`langfuse/langfuse:3`,
`langfuse/langfuse-worker:3`), and the Langfuse web UI warns that v3 is
deprecated. As of 2026-11-10, per Langfuse's changelog and upgrade guide:
- v4 is generally available for self-hosting;
- v3 gets security patches only until January 2027;
- Langfuse Cloud becomes v4-only on 16 November 2026.

Every trace the project will rely on for evaluation goes through this stack.
Staying on v3 means a deprecated server under the tracing, and a forced
move later, when there is real trace data to carry over.

## Outcome

- `docker compose -f infra/langfuse/docker-compose.yml up -d` on a fresh
  checkout starts Langfuse v4 with every container up, and the UI shows no
  deprecation warning.
- A run of `uv run advisor "<question>"` against it gives the same trace as
  §1's live check: root `advisor-run` with input and output, `input-check`,
  `model-call` generations with model and token usage, `search_products`
  with arguments and `result_count`, and `output-check`. A failed run gives
  an ERROR-level root.
- `README.md`, `infra/langfuse/.env.example` and
  `docs/decisions/0001-stack.md` describe v4: versions, any new settings,
  and how to start fresh from a v3 stack.

## Constraints

- **Local only:**
  - the stack stays bound to `127.0.0.1`;
  - secrets stay in the gitignored `infra/langfuse/.env`, and only
    placeholders are committed;
  - passwords stay hex, since they are interpolated into URLs (§1's live
    check).
- **No trace data to migrate.** The stack holds only test traces, so
  "start fresh" (`down -v`) is acceptable. A data-preserving v3→v4
  migration is out of scope unless the spec says otherwise.
- **The suite stays offline.** Model calls and Langfuse are faked; nothing in
  `npm run verify` needs Docker or a running Langfuse.
- **Dependencies:** a Langfuse Python SDK upgrade, if v4 needs one, is a
  dependency change with its line in `plan.md`. `langfuse` stays imported
  only in `src/advisor/tracing.py`.
- **Tracing never changes a run** (spec §1 B17); the 5 s flush bound stays.
- **Out of scope:**
  - recording the model input (system prompt, tool definitions) on traces;
  - Langfuse prompt management;
  - evaluation features.

  Each is its own intent.

## Type-specific questions

### Feature
- **Users:** the owner, who runs the stack locally and reads traces; every
  later evaluation intent, which reads them.
- **What exists today:** Langfuse v3 via Docker Compose (web, worker,
  Postgres 17, ClickHouse unpinned, Redis 7, MinIO), Python SDK `langfuse`
  5.2 sending over OpenTelemetry. §1's live check passed on it.
- **Open design questions:**
  1. Image pinning: a major tag (`:4`), or an exact version for every image
     (Langfuse, ClickHouse, Postgres, Redis, MinIO)? Today ClickHouse and
     MinIO are unpinned.
  2. Which minimum versions v4 needs: the sources disagree on ClickHouse
     (≥ 25.12 or 26.4 recommended), Postgres (15 or 16) and Redis (7.0 or
     7.2). The spec takes them from the official upgrade guide.
  3. Does `langfuse` 5.2 on the client work against a v4 server as it is?
     v4 rejects the legacy batch ingestion API in events-only mode and
     expects client-side propagation of attributes like user and session.
     If the SDK needs a newer major, does `tracing.py` change, and do its
     tests?
  4. An existing v3 stack: does the README tell the owner to `down -v` and
     start fresh, or document the official v3→v4 upgrade path?
  5. Which new v4 settings, if any, belong in `.env.example`?

## Assumptions I made

- **Type feature, not adjustment.** The change may stay within the Compose
  file and docs, but it has open design questions (pinning, minimum
  versions, SDK compatibility), and it may touch `tracing.py` and the
  dependencies. When in doubt, a feature.
- **No v3 data needs keeping:** only §1's live-check traces exist, and the
  worktree that held them is gone.
- **A live check is owed** (rule 1: `infra/`, and `tracing.py` if touched).
  It is §1's steps 2–9 against v4.
- **Order with §3:** §3 touches `tracing.py`. Whichever merges second
  rebases; the two don't need each other.
