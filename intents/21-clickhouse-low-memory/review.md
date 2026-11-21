<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §21 review — ClickHouse low-memory config for the local Langfuse

verdict: escalate
tier: reviewed
reviewed-commit: 907102a
round: 2
sampled: no
run: auto
live-check: owed

Tier: the path table puts `infra/langfuse/*` at Attested and README,
`tests/` and intents at Automated; `review_tier` is empty. Round 1's F1
(HIGH) raised it to **Reviewed** (rule 3), and a tier is never lowered. No
rework findings this round, so on the Reviewed tier the verdict is
`escalate`: the owner reads the diff.

Adjustment budget (`git diff --numstat main...HEAD -- . ':!intents'`): 4
files, 55 lines outside `intents/`, all additions (README.md 9,
low-memory.xml 17, docker-compose.yml 2, tests/test_compose.py 27), within 5
files / 60 lines; no core code. The fourth file was the owner's decision
("21: b and add short test").

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 21` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

## Resolution of round 1
| Finding | Owner's decision | Now (907102a) | Status |
| --- | --- | --- | --- |
| F1 HIGH `background_pool_size` 2 vs MergeTree free-entries defaults | (b) drop it, default, no `merge_tree` block | `low-memory.xml` has neither; `tests/test_compose.py:128` asserts the absence (M7 killed) | resolved; server start is live-check step 2 |
| F2 MEDIUM TRUNCATE expanded `$CLICKHOUSE_PASSWORD` in the host shell | Needs rework | `README.md:101-103` runs `exec clickhouse sh -c '... --password "$CLICKHOUSE_PASSWORD" ...'`; the container's `sh` expands it (`docker-compose.yml:82`) | resolved for bash and Git Bash; see F6 for PowerShell 5.1 |
| F3 MEDIUM no test; M1-M4 survived | short test in `tests/test_compose.py`, fourth file accepted | `tests/test_compose.py:111-118` (compose block: `mem_limit: 1500m`, the `:ro` mount), `:120-128` (XML parses, nine `remove="1"`, no `query_log`, cap 1073741824, no `background_pool_size`) | resolved: M1-M4 killed |
| F4 LOW `processors_profile_log` missing from the README list | worth a look | `README.md:104-105` lists it | resolved |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F5 LOW, the intent's "Exactly what changes" still lists `background_pool_size` and 3 files |
| 2 | Type check | pass apart from the owed live check (FAIL whose only error is the unrecorded live check, the owner's); 4 files, 55 lines |
| 3 | Behaviour against the intent | findings (1): F6 LOW; settings, mount, cap and README match the intent plus round 1's decisions; eval run not owed |
| 4 | Tests prove the behaviour | findings (1): F7 LOW; 9 of 12 mutants killed, the three cache-size mutants survive |
| 5 | Conventions | pass: images untouched, `check:pins` six ok; ports still 127.0.0.1; nothing in `src/`, no core code, no dependency (stdlib `xml.etree`) |
| 6 | Numbers in prose | pass for what reproduces offline (702 passed, 4 files / 55 lines, 1 GiB / 256 MiB / 64 MiB); `docker stats` figures need Docker |
| 7 | Documentation | pass; README describes the round-2 config; CLAUDE.md does not describe the ClickHouse config |
| 8 | Guardrails and hygiene | pass: no secret in the XML, test or README |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 21, adjustment)
  error: A live check is owed and not recorded. Do the steps in intents/21-clickhouse-low-memory/review.md → ## Live check, then set live_checked: <date> in intents/21-clickhouse-low-memory/metadata.yml.
  note:  4 file(s), 55 line(s) changed outside intents/.
```
The only error is the owed live check, the owner's to clear, not a finding.

## Findings
- **F5 LOW** `intents/21-clickhouse-low-memory/intent.md:54,57,65`: "Exactly
  what changes" (the adjustment's plan) still says "sets
  `background_pool_size` to 2" and "3 files, about 35 lines", and the
  Assumptions still place `background_pool_size` at server level. The code
  follows the owner's F1 (b) and F3 decisions (round 1, `## Progress`); the
  text above Progress is the owner's to amend. Worth a look: update those
  bullets to "no `background_pool_size` (default)" and "4 files (adds
  `tests/test_compose.py`), 55 lines".
- **F6 LOW** `README.md:101-103`: the TRUNCATE command works as written in
  bash, Git Bash and PowerShell 7.3+. Windows PowerShell 5.1 does not escape
  embedded double quotes when passing arguments to a native program, so the
  single-quoted `sh -c` argument would reach `docker` split and fail
  visibly (harmless). Reasoned from PowerShell's documented behaviour, not
  run. Worth a look: label the command "in bash or Git Bash". Live-check
  step 7 shows whether it bites.
- **F7 LOW** `infra/langfuse/clickhouse/low-memory.xml:13-15`: no test reads
  `mark_cache_size`, `index_mark_cache_size` or `uncompressed_cache_size`;
  M8-M10 survive. Within the owner's "short test"; the 1 GiB and 1500m caps
  still bound memory and live-check step 4 checks the values. Worth a look:
  three `root.find(...).text ==` lines would kill them (55 of 60 lines).

**Mutants** (full product suite, 702 tests, plus `check-pins`; backup and
restore by copy; a `git diff --quiet` guard proves each applied):
- M1 `docker-compose.yml:78` delete `mem_limit: 1500m`: KILLED (`test_clickhouse_is_capped_and_mounts_the_low_memory_config`)
- M2 `docker-compose.yml:86` delete the mount line: KILLED (same test)
- M3 `docker-compose.yml:86` drop `:ro`: KILLED (same test)
- M4 `low-memory.xml:16` `max_server_memory_usage` → 0: KILLED (`test_low_memory_config_trims_logs_and_caps_memory`)
- M5 `low-memory.xml:8` delete `processors_profile_log remove="1"`: KILLED (XML test)
- M6 add `<query_log remove="1"/>`: KILLED (XML test)
- M7 re-add `<background_pool_size>2</background_pool_size>`: KILLED (XML test)
- M11 `low-memory.xml:4` `text_log remove="1"` → `remove="0"`: KILLED (XML test)
- M12 `docker-compose.yml:78` `mem_limit` → 15000m: KILLED (compose test)
- M8 `low-memory.xml:13` `mark_cache_size` → 5368709120: SURVIVED (F7)
- M9 `low-memory.xml:15` `uncompressed_cache_size` → 8589934592: SURVIVED (F7)
- M10 `low-memory.xml:14` `index_mark_cache_size` → 5368709120: SURVIVED (F7)

The tests prove the repository side (cap, read-only mount, nine removed
logs, `query_log` kept, 1 GiB cap, no `background_pool_size`); ClickHouse's
behaviour is the live check's.

## Not checked
- Whether ClickHouse 26.3.62.3 starts healthy with this config (`remove="1"`
  on each section, the default background pool). Needs Docker.
- Whether the settings take effect, and whether the removed logs stop growing
  while `query_log` grows.
- Whether MergeTree mutations (Langfuse's deletes) still run (probe, step 6).
- The memory outcome: under 1.5 GiB, the 700 MiB target at rest, the 1 GiB
  cap holding under a heavy UI query.
- The bind mount readable by uid 101 on Docker Desktop for Windows;
  `mem_limit` honoured by the owner's compose version.
- The README's TRUNCATE in the owner's shell (F6), and TRUNCATE working once
  the section is removed from config.
- Langfuse end to end: traces, scores and annotation queues.
- ClickHouse's parser reading the CRLF working-tree XML (step 2).

## Live check
- owed: rule 1 (`infra/`); also covers every Not-checked item. Run it **in
  the worktree `C:/Users/eric/src/product-advice-agent-wt/21-clickhouse-low-memory`,
  before the merge**. The stack shares ports and volumes with main's: first
  `docker compose -f infra/langfuse/docker-compose.yml down` in the main
  checkout (**without** `-v`), then copy the main checkout's
  `infra/langfuse/.env` into the worktree's `infra/langfuse/`.
- steps (in the worktree, in Git Bash unless a step says otherwise):
  1. `docker compose -f infra/langfuse/docker-compose.yml up -d`.
  2. `docker compose -f infra/langfuse/docker-compose.yml ps`: every container
     healthy or running, clickhouse healthy (not restarting). If it restarts:
     `docker compose -f infra/langfuse/docker-compose.yml logs clickhouse |
     grep -iE "BAD_ARGUMENTS|Exception|remove"` and stop.
  3. `docker stats --no-stream`: clickhouse under 1.5 GiB, LIMIT ~1.465 GiB;
     again after ~5 minutes at rest, target under 700 MiB.
  4. Settings took: `docker compose -f infra/langfuse/docker-compose.yml exec
     clickhouse sh -c 'clickhouse-client --user clickhouse --password
     "$CLICKHOUSE_PASSWORD" -q "SELECT name, value FROM system.server_settings
     WHERE name IN ('"'"'max_server_memory_usage'"'"','"'"'mark_cache_size'"'"','"'"'index_mark_cache_size'"'"','"'"'uncompressed_cache_size'"'"')"'`:
     1073741824, 268435456, 67108864, 0. No `background_pool_size`
     expectation: it stays at the server default.
  5. Logs off: in the same `exec ... sh -c` form, `SELECT count()` on
     `system.trace_log`, `text_log`, `metric_log`, `asynchronous_metric_log`,
     twice a minute apart: no growth, or "unknown table".
     `system.query_log` still grows after clicking around the UI.
  6. MergeTree and mutations: `CREATE DATABASE probe21; CREATE TABLE
     probe21.t (x UInt8) ENGINE=MergeTree ORDER BY x; INSERT INTO probe21.t
     VALUES (1),(2); ALTER TABLE probe21.t DELETE WHERE x=1 SETTINGS
     mutations_sync=1; SELECT count() FROM probe21.t; DROP DATABASE
     probe21;` (`clickhouse-client --multiquery`, or one at a time): no
     error, count 1.
  7. The README's one-off step, **exactly as written** (`README.md:101-103`,
     as one line) in Git Bash; if you normally use PowerShell, try it there
     too and note the version (F6). Exit 0; then `SELECT sum(bytes_on_disk)
     FROM system.parts WHERE database='system' AND table='trace_log' AND
     active` is about 0.
  8. With the three `LANGFUSE_*` variables in the root `.env` and Ollama up:
     `uv run advisor-eval --provider ollama --only <one or two case ids>`
     finishes and prints its pass line.
  9. http://localhost:3000: the run's traces (tagged `eval`) open with spans,
     a trace's scores show, Annotation Queues lists and opens the queues.
- you should see: every container healthy; ClickHouse under 1.5 GiB with a
  ~1.465 GiB limit; the four settings as configured; removed logs not
  growing while `query_log` grows; the probe mutation at count 1; the README
  command working as written; the eval's traces, scores and queues in the
  UI. Then bring this stack down (without `-v`) and restart main's.

## Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 907102a; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → "All checks passed!", "162
  files already formatted", mypy "Success: no issues found in 29 source
  files", "702 passed". Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "4 file(s), 55 line(s)". Matches.
- **Coordinator, re-run:** the kills the rework claims: M1, M2, M3 KILLED
  (the compose test, 1 failed), M4 KILLED (the XML test, 1 failed). Matches
  the reviewer and the implementer.
- **Coordinator, re-run:** survivors M8, M9, M10 each SURVIVED (702 passed,
  `check:pins` exit 0). Matches the reviewer.

**Reviewer, verified:** verify (kit 298, pytest 702), check:intent,
sampling, `check:pins` (six ok), `owes-run`; the round-2 diff
(`6e8b428..HEAD`) read in full; mutants M1-M12; nothing pushed (no remote
branch); Docker not started, no model called.

**Taken on trust:** ClickHouse 26.3.62.3's behaviour with this config
(start-up, `remove="1"`, the default pool passing the MergeTree sanity
check, the cap holding); PowerShell 5.1's argument passing (F6); everything
under Not checked.
# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 239fefc
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: the path table puts `infra/langfuse/*` at Attested (build config, not
in the Reviewed list) and README/intents at Automated; `review_tier` is
empty. F1 (HIGH) raises it to **Reviewed** (rule 3).

Adjustment budget: 3 files / 28 lines outside `intents/` (5 files / 46+3
lines in all), within 5 files / 60 lines; no core code.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 21` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 21, adjustment)
  note:  3 file(s), 28 line(s) changed outside intents/.
```

### Findings
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

### Not checked
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

### Live check
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

### Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

### Verified myself vs. taken on trust

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
