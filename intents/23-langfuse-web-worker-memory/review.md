<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §23 review — Memory caps for the local Langfuse web and worker containers

verdict: attest
tier: attested
reviewed-commit: 59da572
main: 63b4f66
round: 1
sampled: yes
run: auto
live-check: owed

**Tier.** The path table decides. `infra/langfuse/docker-compose.yml` is build/infra config (Attested, as in §21); `tests/test_compose.py` is Attested (tests only); `README.md` wording and `intents/**` are Automated. Highest: **Attested**. `review_tier` is empty; no CRITICAL or HIGH finding.

**Adjustment budget.** `git diff --numstat main...HEAD -- . ':!intents'`: 3 files, 20 lines (README +2, compose +6/-1, test +11), within 5 files / 60 lines; no core code, nothing in `src/`.

**Sampling.** `npm run sdlc:scan -- --sample-due auto --exclude 23`: "nth attested auto change = 6, every 3, sampled: yes". A post-merge full diff read is due.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: both services get `mem_limit: 1g` and per-service `NODE_OPTIONS: --max-old-space-size=512`; shared anchor unchanged; one README sentence; one test |
| 2 | Type check | pass (PASS, 3 files / 20 lines) |
| 3 | Behaviour against the intent | pass: rendered config equals main plus the intended changes; eval run not owed |
| 4 | Tests prove the behaviour | findings (1): F1 LOW, 10 of 12 mutants killed; the two survivors both drop the worker's merge key |
| 5 | Conventions | pass: images unchanged, `check:pins` six ok, ports still 127.0.0.1, no `src/`, no dependency, no secret |
| 6 | Numbers in prose | pass for what reproduces offline (860 passed, 3 files / 20 lines, 1g, 512 MiB); the `docker stats` figures go to the live check |
| 7 | Documentation | pass: `README.md:106-107` matches the compose file; CLAUDE.md does not describe container limits |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 23, adjustment)
  note:  3 file(s), 20 line(s) changed outside intents/.
```
With `live-check: owed` committed, `check:intent` FAILs until `live_checked:` is recorded: the owner's to clear, not rework.

## Behaviour checked against the intent
- **Rendered config.** No `infra/langfuse/.env` in the worktree and the real one was not read. main's and the branch's compose files were rendered with dummy env values (`docker compose --env-file <dummy> -f … config --format json`), both exit 0. `langfuse-web` and `langfuse-worker`: environment 31 → 32 keys, the only added key `NODE_OPTIONS=--max-old-space-size=512`, none removed or changed; `mem_limit` absent → 1073741824 on both; every other field identical. minio, redis, postgres identical; clickhouse differs only in the absolute host path of its bind mount (rendered from another directory). The worker's move to `<<: *langfuse-env` gives the old environment plus `NODE_OPTIONS`.
- **No image change.** Both langfuse tags still 4.78.0; `check:pins` ok for all six; the test asserts `NODE_OPTIONS` is not in `x-langfuse-env`.
- **Images.** `docker image inspect` on `langfuse/langfuse:4.78.0` and `langfuse/langfuse-worker:4.78.0`: neither sets `NODE_OPTIONS` in `Config.Env` (only `NODE_ENV=production`). Both start through `dumb-init -- ./{web,worker}/entrypoint.sh`, not read (Not checked).

## Mutants (infra/langfuse/docker-compose.yml)
Each applied by script, `git diff --quiet` asserted non-zero first, full `uv run pytest` (860), restored from a byte copy. Killing test in every killed case: `tests/test_compose.py::test_langfuse_web_and_worker_are_capped_per_service`.

| Mutant | Target | Result |
| --- | --- | --- |
| M1 worker `mem_limit` removed | :63 | killed |
| M2 worker `<<: *langfuse-env` removed | :65 | **survived** |
| M3 worker `NODE_OPTIONS` removed | :66 | killed |
| M4 worker `NODE_OPTIONS` 512→1024 | :66 | killed |
| M5 worker `mem_limit` 1g→2g | :63 | killed |
| M6 web `mem_limit` removed | :74 | killed |
| M7 web `NODE_OPTIONS` removed | :77 | killed |
| M8 web `NODE_OPTIONS` 512→1024 | :77 | killed |
| M9 web `mem_limit` 1g→2g | :74 | killed |
| M10 `NODE_OPTIONS` also in the shared anchor | x-langfuse-env | killed |
| M11 worker env reverted to `environment: *langfuse-env` | :64-66 | killed |
| M12 worker `<<: *langfuse-env` replaced by one explicit var | :65 | **survived** |

## Findings
- **F1 LOW** `tests/test_compose.py:136-138`, `infra/langfuse/docker-compose.yml:65`. Nothing checks that the worker still merges the shared environment: M2 and M12 drop `<<: *langfuse-env` and all 860 tests pass. Such a worker would lose `DATABASE_URL` and the ClickHouse, Redis and S3 settings and fail at start. The intent's test (both services carry the two caps) is what was built, the web service's merge key was untested on main too, the render shows the environment correct today, and the live check would show a broken worker at once, so not raised to rework. Worth a look: `assert "      <<: *langfuse-env" in block` at `tests/test_compose.py:138` would kill M2 and M12.
- **LOW (observation, no action)** Commits 09bc69e and b393f13 lack the `Co-Authored-By` trailer; 59da572 has it. No repo rule requires it (CLAUDE.md, intents/README.md, REVIEW-POLICY.md, `.claude/agents`), and adding it would rewrite commits under the reviewed commit, which `ship`'s ancestry check forbids. Left as is.

No "Needs rework:" or "Needs decision:" findings. No CRITICAL.

## Not checked
- **Whether `NODE_OPTIONS` reaches the Node process.** The images' `entrypoint.sh` was not read (it needs a container). If it exported its own `NODE_OPTIONS`, the heap cap would be overridden. Live-check step 3 covers it.
- **The runtime outcome.** The 1 GiB limit in `docker stats`, under 650 MiB at rest, six healthy containers, tracing, scores and queues in the UI: need the running stack (rule 1, `infra/`).
- **Load.** Whether 512 MiB of old space suffices for a heavy UI page or a large ingestion batch.
- **The real `infra/langfuse/.env`.** Not used; the render used dummy values.
- **The kit half of verify** (`node --test`) ran inside `npm run verify`; only its exit 0 was inspected.

## Live check
- **owed:** rule 1, the diff touches `infra/` (`infra/langfuse/docker-compose.yml`). It also covers "whether `NODE_OPTIONS` reaches the Node process".
- **steps:**
  1. In the worktree (or the main checkout after merge), with the real `infra/langfuse/.env` in place: `docker compose -f infra/langfuse/docker-compose.yml up -d`. Only `langfuse-web` and `langfuse-worker` are recreated; no volume is touched. Wait about a minute.
  2. `docker compose -f infra/langfuse/docker-compose.yml ps`.
  3. `docker compose -f infra/langfuse/docker-compose.yml exec langfuse-web sh -c 'for p in /proc/[0-9]*; do grep -q node $p/cmdline 2>/dev/null && tr "\0" "\n" < $p/environ | grep NODE_OPTIONS; done'`, then the same with `langfuse-worker`.
  4. After a few minutes at rest: `docker stats --no-stream`.
  5. With the root `.env` holding the Langfuse keys: `uv run advisor-eval`; then open http://localhost:3000, a new trace, the project's scores and an annotation queue.
- **you should see:**
  - Step 2: all six services Up, `(healthy)` where a healthcheck exists.
  - Step 3: `NODE_OPTIONS=--max-old-space-size=512` at least once per container.
  - Step 4: LIMIT `1GiB` for `langfuse-web` and `langfuse-worker` (today 7.7 GiB), each MEM USAGE under about 650 MiB. Missing that target while working and under 1 GiB is the owner's call (intent).
  - Step 5: the run is traced; traces, scores and queues open without errors; no container restarts.

## Eval run
- not owed (no listed path). `uv run advisor-analysis owes-run --base main`: "not owed (no listed path changed)".

## Verified myself vs. taken on trust
- **Coordinator, re-run** (worktree, HEAD 59da572): `npm run verify` exit 0, ruff "All checks passed!", 860 passed. Matches the reviewer and the implementer.
- **Coordinator, re-run**: `npm run check:intent` → `type-check: PASS (intent 23, adjustment)`, 3 files / 20 lines. Matches.
- **Coordinator, re-run**: M2 (worker `<<: *langfuse-env` deleted) → survived, 860 passed. Matches the reviewer.
- **Coordinator, re-run**: M12 (worker `<<: *langfuse-env` → `REDIS_PORT: "6379"`) → survived, 860 passed. Matches the reviewer. Restored by copy; `git status --short` clean.
- **Reviewer, ran** (worktree, HEAD 59da572): branch contains main 63b4f66; `npm run verify` exit 0, 860 passed; `npm run check:intent` PASS; `npm run check:pins` six ok (minio behind latest, informational); `owes-run` not owed; `sdlc:scan --sample-due` sampled: yes; `git diff --numstat` budget; `docker compose config` render diff with dummy env; `docker image inspect` on both langfuse images; the 12 mutants above with the full suite, restored by byte copy, `git status --short` clean.
- **Not touched**: no up, down, restart or exec against the running stack; the real `.env` not read; nothing pushed or merged.
- **Taken on trust**: the implementer's Progress was not relied on; its mutant list matches except M2 and M12, which it did not run. The intent's `docker stats` figures (795/712/321 MiB, 7.7 GiB) are taken on trust; the live check covers them.
