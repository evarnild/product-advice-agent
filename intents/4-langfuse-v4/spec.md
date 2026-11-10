<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §4 spec — Move the local Langfuse stack to v4

Accepted intent: [intent.md](intent.md)
Written against `main` at `08f9b04`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Owner's decisions

| Question | Owner's answer | When |
| --- | --- | --- |
| Image pinning | **Exact versions** for every image | spec round, 2026-11-10 |
| How close to Langfuse's upstream compose | **Minimal edit**: keep our file (localhost ports, required secrets, hex passwords), change what v4 needs, add no `langfuse-ai-gateway` | spec round, 2026-11-10 |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/4-langfuse-v4/intent.md` | Outcome: a fresh `up -d` starts v4 with no deprecation warning; the advisor's trace is the same as §1's live check; README, `.env.example` and the stack decision describe v4. Constraints: localhost only, hex passwords, no data migration ("start fresh" acceptable), suite offline, the SDK stays in `tracing.py`. |
| Langfuse upgrade guide v3→v4 (https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4), read 2026-11-10 | Infrastructure minimums: ClickHouse "25.12 minimum"; PostgreSQL "15 minimum, 16 recommended"; Redis "7.0 minimum, 7.2 recommended"; storage unchanged. New optional variables `LANGFUSE_MIGRATION_V4_WRITE_MODE` (default `events_only`) and others, all with defaults; none required. "Langfuse v3 will receive security patches until end of January 2027." The in-place path (latest v3 first, finished background migrations, backup, then v4) has "no automatic downgrade path back to v3". |
| Langfuse compatibility page (https://langfuse.com/docs/compatibility) | Python SDK v5 needs "self-hosted server ≥ 4.59.0"; OSS v3 is not supported for SDK v5. **We run `langfuse` 5.2.0 (`uv.lock`) against v3 today: unsupported.** |
| Langfuse's `docker-compose.yml` on `main` (read 2026-11-10) | Web `docker.langfuse.com/langfuse/langfuse:${LANGFUSE_IMAGE_TAG:-4}`, worker likewise; ClickHouse `26.3.62.3`; Postgres `${POSTGRES_VERSION:-17}`; Redis `7`; MinIO `cgr.dev/chainguard/minio` untagged; plus `langfuse-ai-gateway` (beta, optional, "newer than 4.75.0"), which the owner left out. |
| Langfuse AI gateway docs (https://langfuse.com/self-hosting/configuration/ai-gateway) | Optional: a proxy that forwards app requests to OpenAI/Anthropic and records them. SDK ingestion and the trace UI do not depend on it. Without it, the UI shows it as not deployed. |
| `infra/langfuse/docker-compose.yml` (main) | `:47` `langfuse-worker:3`, `:63` `langfuse:3`, `:72` `clickhouse-server` (no tag), `:93` `chainguard/minio` (no tag), `:114` `redis:7`, `:128` `postgres:17`. Every port is `127.0.0.1:`. Every secret is `${VAR:?…}`. |
| `infra/langfuse/.env.example` (main) | The secrets list and the hex-only password rule (from §1's live check). |
| `README.md` → "Trace to a local Langfuse (optional)" | The setup steps; `down -v` removes stored traces. |
| `docs/decisions/0001-stack.md:16` | "Tracing \| Langfuse, self-hosted with the v3 docker-compose in `infra/langfuse/` …" |
| `src/advisor/tracing.py` | The SDK use: `Langfuse(public_key, secret_key, host)`, `start_observation`, `update`, `end`, `flush`. All of it sends OpenTelemetry spans. Nothing uses the legacy batch ingestion API that v4 rejects in `events_only` mode. |

## Behaviour

**Images**

- **B1.** Every `image:` in `infra/langfuse/docker-compose.yml` names an
  exact version: a full release tag, or a digest (`@sha256:…`) where the
  registry publishes no fixed tags. No image is untagged or on a major-only
  tag (`:4`, `:7`, `:17`).
- **B2.** Langfuse web and worker run the same v4 release, at least
  `4.59.0` (the SDK v5 minimum). The plan names the newest stable 4.x
  release at plan time.
- **B3.** Versions meet the v4 minimums:
  - ClickHouse ≥ 25.12, on a release line ClickHouse still patches; the
    one Langfuse's compose pins (`26.3.62.3`) unless the plan finds it
    superseded;
  - Postgres 17.x, keeping the major already in use;
  - Redis ≥ 7.2;
  - MinIO pinned per B1.
- **B4.** The Langfuse images come from the registry Langfuse documents for
  v4. If both Docker Hub and `docker.langfuse.com` serve the chosen tag,
  the plan picks one and says why.

**What stays as it is**

- **B5.** Every published port stays bound to `127.0.0.1`. No new service
  is added: no `langfuse-ai-gateway`.
- **B6.** No secret has a default in the Compose file; a missing one stops
  `docker compose` with the `set … in infra/langfuse/.env` message. The
  required secrets are unchanged; passwords stay hex-only.
- **B7.** No new environment variable is required. v4's migration variables
  keep their defaults (`events_only` write mode) and are not set. A fresh
  stack has no legacy data to migrate.
- **B8.** `src/advisor/tracing.py` and the `langfuse` SDK version
  (`uv.lock`) do not change. SDK 5.2 meets v4's requirement (≥ 4.59.0)
  and sends OpenTelemetry spans only.

**Moving from an existing v3 stack**

- **B9.** The README says that a v3 stack is replaced, not upgraded in
  place. Run `docker compose -f infra/langfuse/docker-compose.yml down -v`
  (this deletes the stored v3 traces) before the first `up -d` on v4, then
  create the account, project and keys again. It says why: local test
  traces only; the in-place path needs the latest v3, finished background
  migrations and a backup, and has no way back. It links Langfuse's
  upgrade guide for anyone who has data to keep.

**Guard**

- **B10.** A test reads `infra/langfuse/docker-compose.yml` as text (no
  YAML dependency) and asserts:
  - every `image:` value has an exact tag or digest per B1;
  - web and worker carry the same tag, and it is a 4.x version ≥ 4.59.0;
  - every `ports:` entry starts with `127.0.0.1:`;
  - no service is named `langfuse-ai-gateway`.

  It runs in `npm run verify` and needs no Docker.

**Docs**

- **B11.**
  - The Compose file's header says v4 and links the v4 Compose docs.
  - `README.md` → "Trace to a local Langfuse" gives the v4 setup and
    B9's note.
  - `docs/decisions/0001-stack.md` → the "Tracing" row says v4 with exact
    pins, and adds a dated line: what changed, why (v3 deprecated; SDK v5
    needs ≥ 4.59.0), and the owner's two answers.
  - `CLAUDE.md` changes only where it names the Langfuse version.

## Interpretations

- **"no deprecation warning"** (intent Outcome) is read as: the v3
  deprecation banner the owner saw is gone. Notices about unrelated
  features (for example the AI gateway being "not deployed") are not
  deprecation warnings. Comment site: the Compose file header.
- **"Exact versions"** (owner) is read as: a reference that cannot move. A
  full version tag where the registry publishes one, a digest where it
  doesn't (the free Chainguard MinIO image is published only as `latest`).
  Comment site: next to each digest-pinned image.
- **"Minimal edit"** (owner) is read as: our file stays the base. Only image
  lines, the header and comments change, plus anything without which v4
  does not start. Each such addition is named in the plan with the source
  that requires it. Comment site: the Compose file header.
- **"the same trace as §1's live check"** (intent Outcome) is read as: the
  same observation names, types, order and fields (§1 AC14). Nothing new is
  required on the trace. Comment site: none; the live check carries it.

## Acceptance criteria

- **AC1** (B1–B4, B10): the Compose guard test passes on the new file, and
  fails on `main`'s file (untagged ClickHouse and MinIO, `:3`). *Proof:*
  `tests/test_compose.py`, the reviewer running it against `main`'s file
  by copy.
- **AC2** (B5–B7): the diff of `docker-compose.yml` touches only image
  lines, the header and comments, plus any addition the plan names with its
  source. `docker compose --env-file infra/langfuse/.env.example -f
  infra/langfuse/docker-compose.yml config -q` succeeds. *Proof:* reviewer
  reads the diff and runs the command if Docker is installed; otherwise
  Not checked.
- **AC3** (B8): `git diff main -- src/ uv.lock pyproject.toml` is empty.
  *Proof:* reviewer.
- **AC4** (B9, B11): README, the Compose header, 0001 and CLAUDE.md say
  what B9 and B11 say. *Proof:* reviewer reads.
- **AC5** (all; live): the owner runs the check below. *Proof:* **live
  check**.
  1. `docker compose -f infra/langfuse/docker-compose.yml down -v`, then
     `up -d`.
  2. All six containers are up, and http://localhost:3000 shows no v3
     deprecation warning.
  3. Create the account, project and keys; set them in the root `.env`.
  4. Run `uv run advisor "I need noise-cancelling headphones under 200
     euros"`, and once with an invalid key.
  5. Both traces look as in §1's live check: root `advisor-run`,
     `input-check`, `model-call` generations with model and usage,
     `search_products` with arguments and `result_count`, `output-check`.
     The failed run's root is at level ERROR.

## Non-functional

- **Boundaries:** `infra/langfuse/`, one new test file, and docs. No product
  code changes (B8).
- **Data:** synthetic catalogue and local test traces only. The move deletes
  the v3 traces by design (B9); nothing is migrated.
- **Model use:** unchanged.
- **Autonomy:** unchanged. The stack runs only when the owner starts it.

## Out of scope

- An in-place v3→v4 data migration.
- The AI gateway.
- Langfuse prompt management.
- Recording the model input on traces.
- Changing the SDK.
- §2's trace tags (whether Langfuse shows them is §2's live check, which
  this stack serves).
- Running Langfuse anywhere but this machine.

## Assumptions I made

- **The minimums are the official guide's.** The changelog-era third-party
  numbers that disagreed (§4 intent, question 2) are dropped.
- **No ClickHouse privilege grants are needed.** The guide's "grant extra
  privileges" step applies to upgrading an existing ClickHouse user. A
  fresh stack creates `CLICKHOUSE_USER` through the image's entrypoint, as
  Langfuse's own Compose does. If v4 fails with "Not enough privileges",
  the live check shows it, and the grant becomes an addition the plan
  names (B7/"minimal edit").
- **MinIO stays the Chainguard image, pinned by digest.** Switching
  vendors is not a "minimal edit".
- **No `.env.example` change** beyond comments: B7 adds no variable.
- **The guard test is plain text matching,** so no YAML package arrives.
  It is strict on the patterns in our file. A reformat that breaks it
  means updating the test, not loosening the pinning.
