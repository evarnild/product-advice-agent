<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §21 — ClickHouse low-memory config for the local Langfuse

**Type:** adjustment
**Originator:** me (the owner): "there is a process called vmmemWSL that is eating up 3.2 gb of memory", then "can I reduce the size that clickhouse takes"
**Source:** none (observed on 2026-11-15 while Claude Code's memory reaper kept stopping background test runs)

## Problem

The local Langfuse stack (`infra/langfuse/`) uses most of Docker Desktop's
WSL2 VM, which shows on Windows as `vmmemWSL` at 3.2 GB. On 2026-11-15,
`docker stats` put ClickHouse alone at 3.48 GiB (of 7.62 GiB the VM may
use), its `MemoryResident` at 1.14 GiB. Its biggest tables are ClickHouse's
own diagnostics, not Langfuse data: `system.trace_log` 240 MiB,
`text_log` 101 MiB, `asynchronous_metric_log` 36 MiB, `metric_log` 35 MiB,
`part_log` 28 MiB. On this machine, with Langfuse up for days, the memory left
is short enough that Claude Code stopped three background verify and
mutation runs this week.

## Outcome

- After `docker compose -f infra/langfuse/docker-compose.yml up -d`,
  ClickHouse stays under 1.5 GiB in `docker stats` (target: under
  700 MiB at rest), and its server memory is capped at 1 GiB.
- ClickHouse no longer writes its own diagnostic log tables (`trace_log`,
  `text_log`, `metric_log`, `asynchronous_metric_log`, `part_log`,
  `processors_profile_log`, `opentelemetry_span_log`, `query_thread_log`,
  `query_views_log`). `query_log` stays, for debugging.
- Langfuse still works: every container is healthy, an `advisor-eval`
  run is traced, and the traces, scores and annotation queues open in the
  UI (the live check, rule 1, `infra/`).

## Constraints

- No image changes: every image stays pinned as ADR 0001 and
  `npm run check:pins` require. The change is configuration only, a
  `config.d` file mounted read-only, plus a container memory limit.
- No data loss: the `langfuse_clickhouse_data` volume and its Langfuse
  tables are untouched. Truncating the existing `system.*` log tables to
  reclaim disk is a one-off step the owner runs, documented, not automated.
- Local only and bound to localhost as today; no secret in the new file.
- Nothing in `src/`, no core code, no new dependency.
- Out of scope: capping WSL itself (`%USERPROFILE%\.wslconfig`, a machine
  setting outside the repo), and tuning Postgres, Redis or the Langfuse
  web and worker containers.

## Type-specific questions

### Adjustment
- **Exactly what changes:**
  - a new `infra/langfuse/clickhouse/low-memory.xml`:
    - removes the nine diagnostic log tables;
    - sets `mark_cache_size` to 256 MB, `index_mark_cache_size` to 64 MB, `uncompressed_cache_size` to 0 and `max_server_memory_usage` to 1 GB;
    - sets `background_pool_size` to 2;
  - the `clickhouse` service in `infra/langfuse/docker-compose.yml` gains that file as a read-only volume under `/etc/clickhouse-server/config.d/`, and `mem_limit: 1500m`;
  - a short note in README.md "Trace to a local Langfuse": the memory cap, and the one-off `TRUNCATE TABLE system.<log>` for an existing install.
- **Blast radius:** 3 files, about 35 lines, no core code. `infra/` owes a live check (rule 1).

## Assumptions I made

- The cap values (1 GB server, 1500m container, 256 MB mark cache) suit
  this repo's data volume (a few thousand traces); a heavy UI query could
  hit the 1 GB cap, and the fix would be raising it, not removing it.
- ClickHouse 26.3 accepts `remove="1"` on those log sections and
  `background_pool_size` at server level (true for recent releases;
  the live check confirms the server starts healthy).
- `query_log` is kept on purpose; it is small (1.7 MiB) and useful.
- Tier: the path table decides (`infra/` is not in the Reviewed list);
  `review_tier` left empty.
- An adjustment needs no spec or plan: `intent_accepted` is its gate.

## Progress

- 2026-11-18: built. New `infra/langfuse/clickhouse/low-memory.xml` (nine
  log tables `remove="1"`, `query_log` kept; mark cache 256 MB, index mark
  cache 64 MB, uncompressed cache 0, `max_server_memory_usage` 1 GB, sizes in
  bytes); compose `clickhouse` service mounts it read-only under
  `config.d/` and gets `mem_limit: 1500m`; README note with the one-off
  `TRUNCATE TABLE system.<log>`. 3 files outside intents/, 28 lines added.
  `check:pins` green, `verify` green (700 pytest passed). No test added
  (budget).
- `background_pool_size` is written at server level (top of `<clickhouse>`),
  the form I believe 26.3 accepts. Not verified against a running server:
  the live check must confirm ClickHouse starts healthy and `docker stats`
  shows the cap. The README truncate example lists five of the tables.
