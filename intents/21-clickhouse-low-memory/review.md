<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §21 review — ClickHouse low-memory config for the local Langfuse

verdict: rework
tier: reviewed
reviewed-commit: 239fefc
round: 1
sampled: no
run: auto
live-check: owed

Tier: the path table puts `infra/langfuse/*` at Attested (build config, not
in the Reviewed list) and README/intents at Automated; `review_tier` is
empty. F1 (HIGH) raises it to **Reviewed** (rule 3).

Adjustment budget: 3 files / 28 lines outside `intents/` (5 files / 46+3
lines in all), within 5 files / 60 lines; no core code.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 21` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (every listed setting present with the intended value; nothing extra) |
| 2 | Type check | pass (PASS, adjustment, 3 files / 28 lines outside intents/) |
| 3 | Behaviour against the intent | findings (2): F1, F2 |
| 4 | Tests prove the behaviour | findings (1): F3; no test reads a changed line, 4 of 4 mutants survived |
| 5 | Conventions | pass (pinned images untouched, ports still 127.0.0.1, no src/ or core code, no dependency) |
| 6 | Numbers in prose | pass for what reproduces offline (28 lines, 700 tests, 256 MiB / 64 MiB / 1 GiB); the docker-stats figures need Docker (Not checked) |
| 7 | Documentation | findings, counted under pass 3 (F2, F4); CLAUDE.md still accurate |
| 8 | Guardrails and hygiene | pass (no secret in the new file; the README uses a variable, not a password) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 21, adjustment)
  note:  3 file(s), 28 line(s) changed outside intents/.
```

## Findings
- **F1 HIGH** `infra/langfuse/clickhouse/low-memory.xml:17`:
  `<background_pool_size>2</background_pool_size>` without matching
  `<merge_tree>` overrides. With the default
  `background_merges_mutations_concurrency_ratio` 2 the merge/mutate pool
  has 4 slots, while the MergeTree defaults
  `number_of_free_entries_in_pool_to_execute_mutation` (20),
  `..._to_execute_optimize_entire_partition` (25) and
  `..._to_lower_max_size_of_merge` (8) exceed it; ClickHouse's
  `MergeTreeSettings::sanityCheck` rejects that with BAD_ARGUMENTS, at
  server start or at MergeTree table creation (Langfuse's migrations), and
  otherwise mutations (Langfuse's deletes) never get free slots. From the
  ClickHouse source as remembered, not observed: Docker was not started.
  **Needs decision:** (a) keep 2 and add a `<merge_tree>` block setting the
  three `number_of_free_entries_in_pool_*` to ≤ 4 (the usual low-memory
  recipe; beyond the intent's "exactly what changes"); (b) drop
  `background_pool_size` (default 16) and rely on the 1 GiB cap; or (c)
  raise it so the pool (×2) is ≥ 25. Live-check step 6 must pass either way.
- **F2 MEDIUM** `README.md:102`: the one-off TRUNCATE passes
  `--password "$CLICKHOUSE_PASSWORD"`, which the host shell expands;
  `CLICKHOUSE_PASSWORD` is set only in `infra/langfuse/.env` and inside the
  container (`docker-compose.yml:82`), so the command authenticates with an
  empty password and fails. **Needs rework:** let the container expand it,
  e.g. `docker compose -f infra/langfuse/docker-compose.yml exec clickhouse
  sh -c 'clickhouse-client --user clickhouse --password "$CLICKHOUSE_PASSWORD"
  -q "TRUNCATE TABLE system.trace_log"'`, keeping the "repeat for" list.
- **F3 MEDIUM** `tests/test_compose.py` (nothing added): no test reads
  `mem_limit`, the `config.d` mount, `:ro` or `low-memory.xml`; M1-M4 all
  survive. The budget has room (3 of 5 files, 28 of 60 lines). **Needs
  decision:** add a text guard to `tests/test_compose.py` (clickhouse has
  `mem_limit: 1500m` and mounts `./clickhouse/low-memory.xml` read-only under
  `/etc/clickhouse-server/config.d/`; the XML parses, removes the nine logs,
  keeps `query_log`, sets `max_server_memory_usage` 1073741824), a fourth
  file the intent did not list; or accept the live check as the only proof
  for an infra-only change.
- **F4 LOW** (worth a look) `README.md:104`: the "repeat for" list names the
  five tables measured in the intent; on an existing 26.x install
  `processors_profile_log` (on by default) has likely grown too. Add it, or
  say "and any other `system.*_log` you see in `system.parts`".

**Mutants** (full product suite, 700 tests, plus `npm run check:pins`, the
only kit script that reads the compose file; backup and restore by copy):
- M1 `docker-compose.yml:78` delete `mem_limit: 1500m`: SURVIVED.
- M2 `docker-compose.yml:86` delete the `low-memory.xml` mount: SURVIVED.
- M3 `docker-compose.yml:86` drop `:ro`: SURVIVED.
- M4 `low-memory.xml:16` `max_server_memory_usage` → 0: SURVIVED.
- Not run (no test or script references `low-memory.xml`, so they survive
  trivially): each `remove="1"` line (xml:3-11), the cache sizes (xml:13-15),
  `background_pool_size` (xml:17).

## Not checked
- Whether ClickHouse 26.3.62.3 starts with this config: the F1 sanity check,
  `remove="1"` on each of the nine log sections, a top-level
  `background_pool_size`. Needs Docker.
- Whether the settings take effect (`system.server_settings`), and whether
  `trace_log` and the others stop growing.
- The memory outcome: under 1.5 GiB in `docker stats`, the 700 MiB target at
  rest, the 1 GiB cap holding under a UI query.
- The bind mount readable by uid 101 on Docker Desktop for Windows;
  `mem_limit` honoured by the owner's compose version.
- `TRUNCATE TABLE system.trace_log` once the section is removed from config.
- Langfuse end to end: traces, scores and annotation queues after the change.

## Live check
- owed: rule 1 (`infra/`); also covers every Not-checked item. Run it **in
  the worktree `C:/Users/eric/src/product-advice-agent-wt/21-clickhouse-low-memory`,
  before the merge**, after F1 is resolved. The stack shares ports and
  volumes with main's: bring main's down first (`docker compose -f
  infra/langfuse/docker-compose.yml down` in the main checkout, **without**
  `-v`), and copy the main checkout's `infra/langfuse/.env` into the worktree.
- steps:
  1. `docker compose -f infra/langfuse/docker-compose.yml up -d`.
  2. `docker compose -f infra/langfuse/docker-compose.yml ps`: every
     container healthy or running, clickhouse healthy. If clickhouse
     restarts: `docker compose -f infra/langfuse/docker-compose.yml logs
     clickhouse | grep -iE "number_of_free_entries|BAD_ARGUMENTS|Exception"`
     and stop (F1).
  3. `docker stats --no-stream`: clickhouse under 1.5 GiB, LIMIT ~1.465 GiB;
     again after ~5 minutes at rest, target under 700 MiB.
  4. Settings took: in `clickhouse-client` (run through `exec clickhouse sh
     -c '... --password "$CLICKHOUSE_PASSWORD" ...'`), `SELECT name, value
     FROM system.server_settings WHERE name IN ('max_server_memory_usage',
     'mark_cache_size', 'index_mark_cache_size', 'uncompressed_cache_size',
     'background_pool_size')`: 1073741824, 268435456, 67108864, 0, and the
     pool size F1's decision chose.
  5. Logs off: `SELECT count()` on `system.trace_log`, `text_log`,
     `metric_log`, `asynchronous_metric_log`, twice a minute apart: no
     growth (or the table is gone); `system.query_log` still grows after
     clicking around the UI.
  6. MergeTree and mutations: `CREATE DATABASE probe21; CREATE TABLE
     probe21.t (x UInt8) ENGINE=MergeTree ORDER BY x; INSERT INTO probe21.t
     VALUES (1),(2); ALTER TABLE probe21.t DELETE WHERE x=1 SETTINGS
     mutations_sync=1; SELECT count() FROM probe21.t; DROP DATABASE
     probe21;`: no error, count 1.
  7. The README's one-off step, exactly as written after rework:
     `TRUNCATE TABLE system.trace_log` succeeds; its `system.parts` size
     drops to ~0.
  8. With the three `LANGFUSE_*` variables in the root `.env` and Ollama up:
     `uv run advisor-eval --provider ollama --only <one or two case ids>`
     finishes and prints its pass line.
  9. http://localhost:3000: the run's traces (tagged `eval`) open with spans,
     a trace's scores show, Annotation Queues lists and opens the queues.
- you should see: every container healthy, ClickHouse under 1.5 GiB, the
  five settings as configured, the removed logs not growing while
  `query_log` grows, the probe mutation finishing, the README command
  working, and the eval's traces, scores and queues in the UI. Then bring
  this stack down (without `-v`) and restart main's.

## Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 239fefc; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → "All checks passed!", "161
  files already formatted", mypy "Success: no issues found in 29 source
  files", "700 passed". Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "3 file(s), 28
  line(s)". Matches.
- **Coordinator, re-run:** M1, M2, M3, M4 each SURVIVED (pytest 700 passed,
  `check:pins` exit 0). Matches the reviewer.
- **Coordinator, re-run:** no `.py` or `.mjs` under `tests/` or `scripts/`
  mentions `low-memory`, `mem_limit` or `config.d`. Matches the reviewer.
- **Coordinator, read:** `README.md:99-104` passes `"$CLICKHOUSE_PASSWORD"`
  to the host shell (F2).

**Reviewer, verified:** verify, check:intent, `check:pins` (six images ok),
sampling, `owes-run`; the diff read in full against the intent's list; M1-M4;
nothing pushed or merged; Docker not started, no model called.

**Taken on trust:** ClickHouse's behaviour with these settings, in
particular the F1 sanity check (from the reviewer's knowledge of the
ClickHouse source, not observed on 26.3.62.3), and everything under Not
checked.
