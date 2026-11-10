<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §4 plan — Move the local Langfuse stack to v4

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`infra/langfuse/docker-compose.yml` starts Langfuse v4 with every image
pinned to an exact version. A text-only guard test keeps the pins, the
localhost ports and the "no gateway" choice in place. The README, the
Compose header, decision 0001 and `CLAUDE.md` describe v4 and the
start-fresh move from v3. No product code, SDK version or lock file
changes.

## Risks

- **A guard test that passes whatever the file says** (§1's recurring
  class). Its regexes could match too loosely: a tag like `4` or `latest`
  passing as "exact", or a missed `image:` line. The implementer runs the
  test once against `main`'s Compose file, where it must fail on each of
  `:3`, the untagged ClickHouse and the untagged MinIO. The implementer
  also runs it against hand-made bad variants: a major-only tag, web and
  worker on different tags, `0.0.0.0:` ports, a `langfuse-ai-gateway`
  service. Each must fail.
- **Version facts rot.** The tags below were listed from the registries on
  2026-11-10. Re-check before editing that each still exists. Pick no newer
  one without noting it in `## Progress`.
- **A digest pins one platform list.** `cgr.dev/chainguard/minio` is pinned
  by its multi-platform index digest, not a per-platform manifest, so it
  still resolves on amd64 and arm64.
- **ClickHouse privileges** (spec, Assumptions). If v4 fails at the live
  check with "Not enough privileges", that is a live-check defect for a
  rework round, not something to pre-empt here.
- **Overlap.** None in code. §2 and §3 change `src/` and `tests/`, and §4
  only adds `tests/test_compose.py`. §2 adds decision 0002; §4 edits 0001.
  `CLAUDE.md` may need a textual rebase.
- **Stale line citations:** read at `a00823f`.

## Verified against the codebase

Re-read on `main` at `a00823f`.

- `infra/langfuse/docker-compose.yml:1-10` — the header ("Self-hosted Langfuse v3 for local runs, adapted from Langfuse's documented docker-compose …").
- `infra/langfuse/docker-compose.yml:47` — `image: docker.io/langfuse/langfuse-worker:3`
- `infra/langfuse/docker-compose.yml:63` — `image: docker.io/langfuse/langfuse:3`
- `infra/langfuse/docker-compose.yml:72` — `image: docker.io/clickhouse/clickhouse-server` (no tag)
- `infra/langfuse/docker-compose.yml:93` — `image: cgr.dev/chainguard/minio` (no tag)
- `infra/langfuse/docker-compose.yml:114` — `image: docker.io/redis:7`
- `infra/langfuse/docker-compose.yml:128` — `image: docker.io/postgres:17`
- `infra/langfuse/docker-compose.yml:58-59, 66-67, 82-84, 101-103, 119-120, 139-140` — every `ports:` entry is `127.0.0.1:<host>:<container>`.
- `infra/langfuse/docker-compose.yml:12-43` — the shared environment. Every secret is `${VAR:?set VAR in infra/langfuse/.env}`; nothing v4-specific is set.
- `infra/langfuse/.env.example:1-15` — the secrets and the hex-password comment.
- `README.md` → "Trace to a local Langfuse (optional)" (lines 39-54 at `a00823f`).
- `docs/decisions/0001-stack.md:16` — the "Tracing" row naming "the v3 docker-compose"; `:24` "Langfuse hosting: … v3".
- `CLAUDE.md` — names the Langfuse stack (`infra/langfuse/`) but no version. Check with `grep -n "v3\|Langfuse v" CLAUDE.md`; change only a hit.
- `uv.lock` — `langfuse` 5.2.0, which meets the v4 server minimum (≥ 4.59.0).
- `tests/` — no test reads the Compose file today.

Registry tags, listed 2026-11-10:
- Docker Hub `langfuse/langfuse` and `langfuse/langfuse-worker`: newest `4.78.0` (also `4.77.0`, `4.76.0`, …; v3's last is `3.227.1`).
- Docker Hub `clickhouse/clickhouse-server`: `26.3.62.3`, the newest on the 26.3 line, and the one Langfuse's own Compose pins.
- Docker Hub `postgres`: `17.11`, the newest 17.x.
- Docker Hub `redis`: `7.4.12`, the newest 7.4.x (≥ 7.2).
- `cgr.dev/chainguard/minio:latest`: index digest `sha256:fb893e36fc369d41e92f678b17ec27378fa5bf0576aeef7ac15460c13629ab5a`. The free tier publishes only `latest`.

## Subtasks

1. **Guard test first** (B10, AC1). Add `tests/test_compose.py`, reading
   the file as UTF-8 text with no YAML import.
   - **Collect** every `image:` value and every `ports:` list item (lines
     matching `^\s+- ` under a `ports:` key), plus the service names
     (two-space-indented keys under `services:`).
   - **Assert:**
     - each image ends in `@sha256:<64 hex>`, or in a tag with at least two
       dot-separated numeric parts (`\d+\.\d+(\.\d+)*`), never `latest` and
       never a bare major;
     - `langfuse/langfuse` and `langfuse/langfuse-worker` share one tag;
     - that tag is `4.x.y` with `(4, x, y) >= (4, 59, 0)`;
     - every port item starts with `127.0.0.1:`;
     - no service is `langfuse-ai-gateway`;
     - the file has exactly six services (`langfuse-worker`,
       `langfuse-web`, `clickhouse`, `minio`, `redis`, `postgres`).
   - **Show it fails on `main`:** run it once against `main`'s file and
     against the bad variants under Risks, via copy-backup, apply, run,
     restore. Record the results in `## Progress`.

   Commit the test together with step 2, so every commit stays green.
2. **Pin the images** (B1–B4).
   - `langfuse-worker`: `docker.io/langfuse/langfuse-worker:4.78.0`
   - `langfuse-web`: `docker.io/langfuse/langfuse:4.78.0`
   - `clickhouse`: `docker.io/clickhouse/clickhouse-server:26.3.62.3`
   - `minio`: `cgr.dev/chainguard/minio@sha256:fb893e36fc369d41e92f678b17ec27378fa5bf0576aeef7ac15460c13629ab5a`,
     with a comment: digest, because the free Chainguard image is published
     only as `latest` (spec, Interpretations); update by `docker buildx
     imagetools inspect cgr.dev/chainguard/minio:latest`.
   - `redis`: `docker.io/redis:7.4.12`
   - `postgres`: `docker.io/postgres:17.11`

   Langfuse stays on Docker Hub (B4). Both registries serve `4.78.0`;
   Docker Hub is already where every other image comes from, and adds no
   registry to trust. Nothing else in the file changes, apart from the
   header (step 3).
3. **Header and comments** (B11, Interpretations).
   - The header says "Self-hosted Langfuse v4" and links
     https://langfuse.com/self-hosting/deployment/docker-compose.
   - One line says every image is pinned exactly (update deliberately; see
     the README), and another that there is no AI gateway (optional, beta,
     not used by the advisor).
4. **README** (B9, B11). In "Trace to a local Langfuse (optional)":
   - say v4;
   - add "Coming from the v3 stack": `docker compose -f
     infra/langfuse/docker-compose.yml down -v` deletes the v3 traces; then
     `up -d`, and create the account, project and keys again. It gives the
     reason in one sentence and links
     https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4
     for anyone with data to keep;
   - add one line on updating a pin: change the tag, then `npm run verify`
     (the guard test).
5. **Decision 0001** (B11).
   - The "Tracing" row says v4, with exact pins.
   - Under "Consequences", a dated line (2026-11-10, §4): v3 is
     deprecated, and Python SDK v5 needs a server ≥ 4.59.0; images pinned
     exactly; no AI gateway; the owner's answers ("Exact versions",
     "Minimal edit").
   - The 2026-11-09 answers section stays as written (history).
6. **`CLAUDE.md`**: only if `grep` finds a v3 mention. "Live checks" already
   lists `infra/`.
7. **Status.** Set `status: in-review` and append to `## Progress`.

## Tests

| Spec | Test | Fails if |
| --- | --- | --- |
| B1 | `test_compose.py`: every image exact | any image is untagged, `:latest`, or a bare major (`main`'s file fails on three images) |
| B2 | `test_compose.py`: web and worker share a tag of at least 4.59.0 | the two diverge, or either is on `3.x` or below 4.59.0 |
| B3 | reviewer checks the chosen versions against the spec minimums (ClickHouse ≥ 25.12, Postgres 17.x, Redis ≥ 7.2) | — (versions are data; the guard doesn't hard-code them) |
| B5 | `test_compose.py`: ports localhost-only; no gateway; exactly six services | a port is opened to `0.0.0.0`, or a service is added |
| B6, B7 | reviewer: the Compose diff touches only image lines, header and comments; `docker compose --env-file infra/langfuse/.env.example -f infra/langfuse/docker-compose.yml config -q` passes, when Docker is available | — |
| B8 | reviewer: `git diff main -- src/ uv.lock pyproject.toml` empty | — |
| B9, B11 | reviewer reads README, header, 0001, CLAUDE.md | — |

Mutants for pass 4 sit in the test's own logic, since the Compose file is
data. The reviewer applies each one-line mutant to the Compose file and
checks that a test fails:
- `4.78.0` → `4` on the worker only;
- `127.0.0.1:3000:3000` → `3000:3000`;
- remove the MinIO digest;
- add a seventh service.

## Validation

- `npm run verify` green (kit tests, ruff, mypy, pytest including
  `test_compose.py`).
- `npm run check:intent` PASS. The change has no core code; ROUTE is
  possible only if the kit counts `infra/` specially, in which case the
  reason goes in `review.md`.
- `docker compose --env-file infra/langfuse/.env.example -f
  infra/langfuse/docker-compose.yml config -q` passes (implementer and
  reviewer, if Docker is on the machine; the CLI parse needs no daemon).
- Live check (owed by rule 1: `infra/`), run by the owner; spec AC5:
  1. `docker compose -f infra/langfuse/docker-compose.yml down -v`.
  2. `docker compose -f infra/langfuse/docker-compose.yml up -d`.
  3. All six containers up; http://localhost:3000 with no v3 deprecation
     warning.
  4. Create the account, project and keys; put them in the root `.env`.
  5. `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
     then the same with an invalid key.
  6. Both traces as in §1's live check, with the failed one's root at
     ERROR.

## Assumptions I made

- **Docker Hub for the Langfuse images** (B4's choice, reason in subtask 2).
- **Newest-at-plan-time versions:** Langfuse `4.78.0`, ClickHouse
  `26.3.62.3`, Postgres `17.11`, Redis `7.4.12`, MinIO the `latest` digest
  of 2026-11-10. They are pinned once; later bumps are their own small
  changes.
- **Six services exactly** in the guard. It encodes "minimal edit", so
  adding a service means changing the test on purpose.
- **ROUTE reasons**, if any, go in `review.md` (see Validation).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-10 — build (subtasks 1-7)

Commits: 3c7f924 (guard test, pins, header, README, decision 0001); the
status/Progress commit follows it.

Shipped: `tests/test_compose.py` (5 tests: collection sanity, exact images,
web/worker share a 4.x tag >= 4.59.0, localhost-only ports, exactly six
services and no gateway). Pins as in subtask 2. Header, README (v4, "Coming
from the v3 stack", "Updating a pin"), decision 0001 row and dated line.
`CLAUDE.md`: grep found no v3 mention, so unchanged.

Tags re-checked read-only with `docker buildx imagetools inspect` on
2026-11-10: langfuse/langfuse 4.78.0, langfuse-worker 4.78.0,
clickhouse-server 26.3.62.3, redis 7.4.12, postgres 17.11, and the MinIO
index digest all resolve. No newer version picked.

Guard test against `main`'s Compose file: 2 failed, 3 passed (exact-images
fails on `langfuse-worker:3`; the v4-tag test fails). Bad variants, each
applied to the finished file by copy, run, restore-by-copy (helper scripts
in the session scratchpad; file verified identical afterwards): worker `:4`,
web/worker diverge, web on 3.227.1, 4.58.0 (below minimum), web `:latest`,
ClickHouse untagged, MinIO without digest, MinIO `:latest`, Redis `:7`,
Postgres `:17`, port `3000:3000`, port `0.0.0.0:3000:3000`, added
`langfuse-ai-gateway`, added seventh service: every one fails (1 or 2
tests failed each).

`npm run verify`: kit tests green; pytest 109 passed (104 before + 5).
`docker compose --env-file infra/langfuse/.env.example -f
infra/langfuse/docker-compose.yml config -q`: exit 0 (parse only; no daemon
use, no containers started or pulled).

Divergences: none. Compose diff is image lines, header and two comment
lines for the MinIO digest. AC5 (live check) is the owner's.

### 2026-11-10 — Rework round 1

Review item 1 (MEDIUM, mutant C6): `test_langfuse_web_and_worker_share_a_v4_tag`
now asserts `version[0] == 4` with a message, before the `>= (4, 59, 0)`
check. C6 (web and worker both `5.0.0`, applied by copy, change asserted,
full suite, restored by copy and compared identical) is killed by that test
("Langfuse must be on major 4, got (5, 0, 0)"): 1 failed, 108 passed. With
the real file: `npm run verify` green, 109 passed. The LOW (floating minor
tags) is untouched, as instructed. Commit: see the next `§4:` commit after
e1d1cfb.
