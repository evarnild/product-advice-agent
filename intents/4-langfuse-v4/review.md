<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §4 review — Move the local Langfuse stack to v4

verdict: escalate
tier: reviewed
reviewed-commit: 0368e59368d879028e530588ba90ede9ac3642ed
round: 2
sampled: no
run: auto
live-check: owed

The rework resolves round 1's MEDIUM (C6) with one assertion. No finding
needs rework, and the tier is Reviewed, so the verdict is escalate: the
owner reads the diff. The live check is still owed.

Tier: Reviewed, set by input 2 (`review_tier: reviewed`), as in round 1.

Scope: 0e644c0..0368e59 — 18f8829 (the rework: one assertion at
`tests/test_compose.py:89`, plan Progress), e1d1cfb (the round-1 review),
0368e59 (`auto_round: 2`). The diff outside `intents/` and `tests/` is
empty. The Compose file last changed in 3c7f924, before round 1.

## Round-1 findings: resolution
| Round-1 finding | Resolution |
| --- | --- |
| MEDIUM `tests/test_compose.py:89`: major version not asserted (C6 survived) | resolved in 18f8829: `assert version[0] == 4, f"Langfuse must be on major 4, got {version}"`. C6 is killed by `test_langfuse_web_and_worker_share_a_v4_tag`, and T11 shows the new line alone does it |
| LOW `tests/test_compose.py:17`: floating minor-line tags (C19, C20) | open, Worth a look (plan-settled) |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (exactly the round-1 fix; `plan.md` changed only below Progress; spec and intent unchanged) |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear) |
| 3 | Behaviour against the spec | pass (B10's "4.x version ≥ 4.59.0" now asserted; B1–B9, B11, AC1–AC4 unchanged since round 1) |
| 4 | Tests prove the behaviour, not only pass | findings (1): C6 killed; C5, C14 still killed; C19, C20 survive (the plan-settled LOW) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass ("109 passed" and C6's "1 failed, 108 passed" reproduce) |
| 7 | Documentation | pass (no doc changed; nothing the rework touches is documented) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; the "guard that passes whatever the file says" risk re-checked with T11) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 4, feature)
  error: A live check is owed and not recorded. Do the steps in intents/4-langfuse-v4/review.md → ## Live check, then set live_checked: <date> in intents/4-langfuse-v4/metadata.yml.
  note:  4 file(s), 144 line(s) changed outside intents/.
```
The only error is the owed live check: the owner's to clear (review skill,
step 1). The 1-line rise from 143 is the new assertion.

## Findings
- **LOW** `tests/test_compose.py:17` — carried from round 1. `TAG` accepts
  any tag with two or more numeric parts, so floating minor-line tags pass:
  C19 (`redis:7.4`) and C20 (`clickhouse-server:26.3`) survive. Spec B1
  says "a full release tag", but the approved plan defined "exact" as "at
  least two dot-separated numeric parts", and the guard does what the plan
  says. The shipped pins are full release tags. Worth a look: tightening
  means per-image rules, and changes the plan, so the owner raises it.

Mutants this round (backup by copy, exact single-occurrence replacements,
file-changed and `git diff --quiet` asserted, full pytest, restore by copy
with a SHA-256 match):

| id | change | result | killing test |
| --- | --- | --- | --- |
| C5 | both Langfuse → `4.58.0` | killed (1 failed, 108 passed) | share_a_v4_tag (`>= MIN_LANGFUSE`) |
| **C6** | **both Langfuse → `5.0.0`** | **killed** (1 failed, 108 passed) | share_a_v4_tag: "Langfuse must be on major 4, got (5, 0, 0)" |
| C14 | both Langfuse → `3.227.1` | killed (1 failed, 108 passed) | share_a_v4_tag: "… got (3, 227, 1)" |
| C19 | redis `7.4.12` → `7.4` | survived (109 passed) | — (plan-settled LOW) |
| C20 | clickhouse `26.3.62.3` → `26.3` | survived (109 passed) | — (plan-settled LOW) |
| T11 + C6 | drop the new `version[0] == 4` line, with the 5.0.0 file | survived (109 passed) | — (the new line alone kills C6) |

Round 1's other Compose and test-logic mutants were not re-run. The rework
adds an assertion and removes none, so nothing round 1 killed can newly
survive.

## Not checked
- **Whether Langfuse 4.78.0 starts on this file** with these versions and
  no added variables (B7), including the "no ClickHouse privilege grant on a
  fresh stack" assumption. Live check (AC5).
- **The v4 UI and traces:** no deprecation warning; SDK 5.2 traces arrive
  with §1's shape. Live check.
- **The two links** (header, README): Langfuse was not contacted.
- **Whether the Docker Hub tags are immutable** (`postgres:17.11`,
  `redis:7.4.12` get rebuilt for base-OS updates); no digest baseline.
- **Pulling or running any image:** not allowed. The registry manifests and
  `docker compose config -q` were not re-run this round: the Compose file is
  unchanged since round 1 verified both.

## Live check
- owed: rule 1 (`infra/langfuse/docker-compose.yml`). This is spec AC5, and
  it also covers the first two Not-checked items. The rework is done, so it
  can be run now.
- **before you start:**
  - `down -v` deletes the v3 stack's volumes: every stored v3 trace, and the
    v3 account and API keys. The Compose project name is `langfuse` from
    both the main checkout and the worktree, so running it from the
    worktree removes the same stack.
  - The worktree has no `.env` files (both are gitignored), and the Compose
    file refuses to start without `infra/langfuse/.env`.
- steps (Windows PowerShell):
  1. `cd C:\Users\eric\src\product-advice-agent-wt\4-langfuse-v4`
  2. `Copy-Item ..\..\product-advice-agent\infra\langfuse\.env
     infra\langfuse\.env`. Every password must be hex (`openssl rand -hex
     24`), as in §1. Or make a fresh one from `infra\langfuse\.env.example`.
  3. `Copy-Item ..\..\product-advice-agent\.env .env` (your
     `ANTHROPIC_API_KEY`; the `LANGFUSE_*` keys get replaced below). If the
     main checkout has no `.env`, create one from `.env.example`.
  4. `docker compose -f infra/langfuse/docker-compose.yml down -v`. This
     deletes the v3 traces.
  5. `docker compose -f infra/langfuse/docker-compose.yml up -d`
  6. `docker compose -f infra/langfuse/docker-compose.yml ps`
  7. Open http://localhost:3000. Sign up again, and create an organisation,
     a project and API keys.
  8. In the worktree's `.env`, set `LANGFUSE_HOST=http://localhost:3000`
     and the new `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`. Update the
     main checkout's `.env` later too.
  9. `uv run advisor "I need noise-cancelling headphones under 200 euros"`
  10. Run the same with a bad key: `$env:ANTHROPIC_API_KEY =
      "sk-ant-invalid"`, the command, then `Remove-Item
      Env:ANTHROPIC_API_KEY`.
- you should see:
  - **Step 6:** six containers, all running, with no restart loop. The
    images are `langfuse:4.78.0` and `langfuse-worker:4.78.0`.
    - If not: `docker compose -f infra/langfuse/docker-compose.yml logs
      langfuse-worker langfuse-web`. Look especially for ClickHouse "Not
      enough privileges", which would be a rework defect.
  - **Step 7:** no v3 deprecation banner. An "AI gateway not deployed"
    notice is expected, and is not a deprecation warning.
  - **Step 9:** an answer, exit 0.
  - **Step 10:** "The advisor is unavailable right now.", exit 1.
  - **In Langfuse → Traces:** two traces.
    - The good one: root `advisor-run` with input and output; then
      `input-check`, `model-call` generations with model and token usage,
      `search_products` with arguments and `result_count`, and
      `output-check`.
    - The failed one: an `advisor-run` root at level ERROR.
  - If a step fails, leave `live_checked:` empty, and the change goes back
    to rework.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/4-langfuse-v4` at 0368e59, `git status --short` empty before and after):
- **Coordinator, re-run:** `git diff 0e644c0 HEAD -- . ':!intents' ':!tests'`
  → empty; `--stat` → `plan.md`, `review.md`, `tests/test_compose.py` (+1),
  plus `metadata.yml`. Matches.
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "61 files already formatted";
  mypy "Success: no issues found in 11 source files"; pytest "109 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL, exit 1, with only
  the owed-live-check error. Matches.
- **Coordinator, re-run:** mutants with my round-1 harness:
  - C6 KILLED by test_langfuse_web_and_worker_share_a_v4_tag (1 failed, 108
    passed);
  - C5 and C14 KILLED by the same test;
  - C19 and C20 SURVIVED (109 passed).

  Matches the reviewer and the implementer.

**Reviewer, verified:**
- HEAD 0368e59, merge base 82bb545 (= local `main`); nothing pushed.
- The scope diffs as above.
- `verify` and `check:intent`.
- `sdlc:scan --sample-due auto --exclude 4` → "nth attested auto change =
  1, every 3, sampled: no".
- Seven mutant runs (harness `…/scratchpad/mut4r2/run.py`), restored with a
  SHA-256 match.
- The Progress numbers.

**Taken on trust:**
- the Langfuse-docs facts the spec quotes;
- that `tracing.py` uses no legacy batch ingestion;
- that the v4 server accepts SDK 5.2's spans (the live check);
- round 1's registry-manifest and `config -q` results (the file is
  unchanged).

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: 0e644c086113ea7396dcfdb2bd02dc823986c78f
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, set by input 2: `metadata.yml` has `review_tier:
reviewed`. On paths alone it would be Attested (`tests/**`, the Compose
file as build config, `README.md`, `docs/**`). The diff does not touch
`infra/langfuse/.env.example`. No CRITICAL or HIGH finding; nothing lowers a
tier.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (exactly subtasks 1–7; nothing above the Progress marker changed) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): B10's "4.x" not asserted. B1–B9, B11 and AC1–AC4 met |
| 4 | Tests prove the behaviour, not only pass | findings (2): 21 Compose-file mutants, 18 killed, 3 survived (C6, C19, C20) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; §1's "guard that passes whatever the file says" checked under pass 4) |

**Pass 3, item by item.**
- **B1.** All six images are exact (`docker-compose.yml:50,66,75,98,119,133`):
  `langfuse-worker:4.78.0`, `langfuse:4.78.0`, `clickhouse-server:26.3.62.3`,
  `minio@sha256:fb893e36…ab5a` (commented at `:96-97`), `redis:7.4.12`,
  `postgres:17.11`.
- **B2.** Web and worker are both on 4.78.0 (≥ 4.59.0), the newest 4.x on
  Docker Hub.
- **B3.**
  - ClickHouse 26.3.62.3: ≥ 25.12, and the newest 26.3.x.
  - Postgres 17.11: the newest 17.x.
  - Redis 7.4.12: ≥ 7.2, and the newest 7.4.x.
  - MinIO: a multi-platform index digest (amd64 and arm64), equal to
    today's `latest`.
- **B4.** Docker Hub, with the reason in plan subtask 2.
- **B5.** All 8 ports are `127.0.0.1:`; six services; no gateway.
- **B6, B7.** The env block and the `${VAR:?}` secrets are untouched; no
  variable was added.
- **B8 / AC3.** `git diff main...HEAD -- src/ uv.lock pyproject.toml` is
  empty.
- **B9.** `README.md:57-63` covers it in full:
  - the v3 stack is replaced, not upgraded;
  - `down -v` deletes the v3 traces;
  - then `up -d`, and create the account, project and keys again;
  - the reason, and the upgrade-guide link.
- **B10.** The test is text-only, needs no YAML or Docker, and runs in
  `verify`. It does not assert "4.x" (finding 1).
- **B11.** The header says v4 and links the v4 Compose docs. The README,
  the 0001 row and the dated line (what changed, why, both owner answers)
  are present. `CLAUDE.md` has no version mention.
- **AC1.** On `main`'s Compose file the guard fails: "2 failed, 107 passed"
  (`test_every_image_is_exact` on `langfuse-worker:3`;
  `test_langfuse_web_and_worker_share_a_v4_tag`). The untagged ClickHouse
  and MinIO each fail independently (C7, C3).
- **AC2.** The diff is only image lines, the header and comments. `docker
  compose --env-file infra/langfuse/.env.example -f
  infra/langfuse/docker-compose.yml config -q` exits 0 (parse only; Docker
  29.8.2, Compose v5.5.1).
- **AC4.** All four documents read.

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 4, feature)
  note:  4 file(s), 143 line(s) changed outside intents/.
```

### Findings
- **MEDIUM** `tests/test_compose.py:89` — the guard does not assert the
  major version, so web and worker both on `5.0.0` pass (mutant C6
  survived). Spec B10 requires "a 4.x version ≥ 4.59.0", and plan subtask 1
  says "`4.x.y` with `(4, x, y) >= (4, 59, 0)`". The shipped file is right
  (4.78.0); only the guard is weaker than the spec. Needs rework: add
  `assert version[0] == 4` next to `:89`. Kills C6.
- **LOW** `tests/test_compose.py:17` — `TAG` accepts any tag with two or
  more numeric parts, so floating minor-line tags pass: C19 (`redis:7.4`)
  and C20 (`clickhouse-server:26.3`) survived, and Docker Hub's floating
  `clickhouse-server:26.3.62` would pass too. Spec B1 says "a full release
  tag", but the approved plan defined "exact" as "at least two dot-separated
  numeric parts", and the guard does what the plan says. The shipped pins
  are full release tags. Worth a look: tightening means per-image rules (for
  example four parts for ClickHouse, three for Redis); the owner can raise
  it.

Compose-file mutants (backup by copy, `git diff --quiet` asserted, full
pytest without `-x`, restore by copy with a hash check):

| id | change | result | killing test(s) |
| --- | --- | --- | --- |
| C1 | worker `4.78.0` → `4` | killed | every_image_is_exact, share_a_v4_tag |
| C2 | `127.0.0.1:3000:3000` → `3000:3000` | killed | ports_are_localhost_only |
| C3 | MinIO digest removed | killed | every_image_is_exact |
| C4 | seventh service `extra` (busybox:1.37.0) | killed | collects_what_it_guards, exactly_the_six_services |
| C5 | both Langfuse → `4.58.0` | killed | share_a_v4_tag |
| **C6** | **both Langfuse → `5.0.0`** | **survived** | — |
| C7 | ClickHouse untagged | killed | every_image_is_exact |
| C8 | web `:latest` | killed | every_image_is_exact, share_a_v4_tag |
| C9 | `127.0.0.1:5432` → `0.0.0.0:5432` | killed | ports_are_localhost_only |
| C10 | `minio` renamed `langfuse-ai-gateway` | killed | exactly_the_six_services |
| C11 | web `4.77.0`, worker `4.78.0` | killed | share_a_v4_tag |
| C12 | redis `:7` | killed | every_image_is_exact |
| C13 | postgres `:17` | killed | every_image_is_exact |
| C14 | both Langfuse → `3.227.1` | killed | share_a_v4_tag |
| C15 | web `:${LANGFUSE_IMAGE_TAG:-4.78.0}` | killed | every_image_is_exact, share_a_v4_tag |
| C16 | MinIO digest truncated to 8 hex | killed | every_image_is_exact |
| C17 | web ports in flow form `["3000:3000"]` | killed | collects_what_it_guards |
| C18 | extra port `3001:3001` on web | killed | collects_what_it_guards, ports_are_localhost_only |
| **C19** | **redis `7.4.12` → `7.4`** | **survived** | — |
| **C20** | **clickhouse `26.3.62.3` → `26.3`** | **survived** | — |
| C21 | both Langfuse → `4.78` | killed | share_a_v4_tag (`len == 3`) |

**Test-logic mutants of `tests/test_compose.py`.** Each was paired with the
bad Compose variant it exists to catch.
- **Load-bearing:** the mutated guard then passes the bad file.
  - T1: TAG loosened to `:(\d+(?:\.\d+)*)$`, with C12;
  - T2: `>= MIN_LANGFUSE` → `True`, with C5;
  - T3: port assert → `True`, with C2;
  - T4: drop `len(version) == 3`, with C21;
  - T6: drop the service-name check, with a seventh service that has no
    image;
  - T8: drop web == worker, with C11;
  - T9: drop `len(_ports()) == 8`, with C17.
- **Redundant and harmless:** another check still catches the bad file.
  - T5: drop the gateway assert;
  - T7: drop the `:latest` assert;
  - T10: drop `len(_images()) == 6`.

### Not checked
- **Whether Langfuse 4.78.0 starts on this file** with these ClickHouse,
  Postgres, Redis and MinIO versions and no added variables (B7). This
  includes the spec's assumption that a fresh stack needs no ClickHouse
  privilege grant. Live check (AC5).
- **The v4 UI and traces:** that the UI shows no deprecation warning, and
  that SDK 5.2 traces arrive with §1's shape. Live check.
- **The two links** (header, README): Langfuse was not contacted. The spec's
  Langfuse-docs facts were not re-read.
- **Whether the Docker Hub tags are immutable.** `postgres:17.11` and
  `redis:7.4.12` are official-image tags that get rebuilt for base-OS
  updates: the version is fixed, but the content can change. That is within
  the spec's "full version tag". No digest baseline was recorded.
- **Pulling or running any image:** not allowed. Existence was checked by
  registry manifest only.

### Live check
- owed: rule 1 (`infra/langfuse/docker-compose.yml`). This is spec AC5, and
  it also covers the first two Not-checked items. Run it after the rework.
- **before you start:**
  - `down -v` deletes the v3 stack's volumes: every stored v3 trace, and the
    v3 account and API keys. The Compose project name is `langfuse` from
    both the main checkout and the worktree, so running it from the
    worktree removes the same stack.
  - The worktree has no `.env` files (both are gitignored), and the Compose
    file refuses to start without `infra/langfuse/.env`.
- steps (Windows PowerShell):
  1. `cd C:\Users\eric\src\product-advice-agent-wt\4-langfuse-v4`
  2. `Copy-Item ..\..\product-advice-agent\infra\langfuse\.env
     infra\langfuse\.env`. Every password must be hex (`openssl rand -hex
     24`), as in §1. Or make a fresh one from `infra\langfuse\.env.example`.
  3. `Copy-Item ..\..\product-advice-agent\.env .env` (your
     `ANTHROPIC_API_KEY`; the `LANGFUSE_*` keys get replaced below). If the
     main checkout has no `.env`, create one from `.env.example`.
  4. `docker compose -f infra/langfuse/docker-compose.yml down -v`. This
     deletes the v3 traces.
  5. `docker compose -f infra/langfuse/docker-compose.yml up -d`
  6. `docker compose -f infra/langfuse/docker-compose.yml ps`
  7. Open http://localhost:3000. Sign up again, and create an organisation,
     a project and API keys.
  8. In the worktree's `.env`, set `LANGFUSE_HOST=http://localhost:3000`
     and the new `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`. Update the
     main checkout's `.env` later too: its v3 keys are gone.
  9. `uv run advisor "I need noise-cancelling headphones under 200 euros"`
  10. Run the same with a bad key: `$env:ANTHROPIC_API_KEY =
      "sk-ant-invalid"`, the command, then `Remove-Item
      Env:ANTHROPIC_API_KEY`. The real environment overrides `.env`.
- you should see:
  - **Step 6:** six containers (langfuse-web, langfuse-worker, clickhouse,
    minio, redis, postgres), all running, with no restart loop. The images
    are `langfuse:4.78.0` and `langfuse-worker:4.78.0`.
    - If not: `docker compose -f infra/langfuse/docker-compose.yml logs
      langfuse-worker langfuse-web`. Look especially for ClickHouse "Not
      enough privileges", which would be a rework defect.
  - **Step 7:** no v3 deprecation banner. An "AI gateway not deployed"
    notice is expected, and is not a deprecation warning.
  - **Step 9:** an answer, exit 0.
  - **Step 10:** "The advisor is unavailable right now.", exit 1.
  - **In Langfuse → Traces:** two traces.
    - The good one: root `advisor-run` with input and output; then
      `input-check`, `model-call` generations with model and token usage,
      `search_products` with arguments and `result_count`, and
      `output-check`.
    - The failed one: an `advisor-run` root at level ERROR.
    - Both have §1's shape.
  - If a step fails, leave `live_checked:` empty, and the change goes back
    to rework.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/4-langfuse-v4` at 0e644c0, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "60 files already formatted";
  mypy "Success: no issues found in 11 source files"; pytest "109 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0. Matches.
- **Coordinator, re-run:** `git diff main...HEAD -- src uv.lock
  pyproject.toml` → 0 bytes. Matches.
- **Coordinator, re-run:** Compose mutants with my own harness (backup by
  copy, exact replacements, file-changed assertion, full pytest, restore by
  copy):
  - C6 (both Langfuse → `5.0.0`) SURVIVED;
  - C19 (`redis:7.4`) SURVIVED;
  - C20 (`clickhouse-server:26.3`) SURVIVED;
  - C1 (worker `:4`) KILLED by test_every_image_is_exact and
    test_langfuse_web_and_worker_share_a_v4_tag;
  - C2 (`3000:3000`) KILLED by test_ports_are_localhost_only.

  Each matches the reviewer.

**Reviewer, verified:**
- HEAD 0e644c0, merge base 82bb545 (= local `main`).
- `verify`, `check:intent` and AC3 as above.
- AC2: `docker compose … config -q` exits 0 (project `langfuse`, six pinned
  images).
- `docker buildx imagetools inspect` resolves all six (manifests only).
- The Docker Hub tags API confirms each pin is the newest on its line.
- AC1, and 39 mutant runs (harness `…/scratchpad/mut4r/`), each restored by
  copy with a SHA-256 match.
- `sdlc:scan --sample-due auto --exclude 4` → "nth attested auto change =
  1, every 3, sampled: no".
- Nothing pushed.

**Taken on trust:**
- the Langfuse-docs facts the spec quotes (v4 minimums, SDK v5 needing ≥
  4.59.0, `events_only` default, the end of v3 patches);
- that `tracing.py` uses no legacy batch ingestion;
- that the v4 server accepts SDK 5.2's spans. The live check decides that.
