<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §6 — A pin-check script for the Langfuse stack's images

**Type:** adjustment
**Originator:** the owner ("make the MinIO pin less fragile. Add a
pin-check script first, then look at SeaweedFS or Garage.")
**Source:** §4's review, rounds 1–2 (Not checked: tag immutability, and
the digest pin); `infra/langfuse/docker-compose.yml:96-97`

## Problem

§4 pins every image exactly. MinIO is the fragile one:
- **Its pin can't be a version.** The free Chainguard image is published
  only as `latest`, so it is pinned by digest
  (`cgr.dev/chainguard/minio@sha256:fb893e36…ab5a`).
- **It can break silently.** Nothing tells the owner when that digest stops
  resolving (Chainguard can stop serving old digests of free images), or
  when `latest` has moved on with security fixes. The first sign would be a
  failed `docker compose up`.
- **Updating it is manual.** The Compose comment at `:97` says to run
  `docker buildx imagetools inspect cgr.dev/chainguard/minio:latest` by hand
  and copy the digest.
- **The other five pins have the same blind spot, less sharply.** Nothing
  checks that they still resolve, or that a newer patch exists on their
  line.

## Outcome

- `npm run check:pins` reads the `image:` lines of
  `infra/langfuse/docker-compose.yml`, resolves each one with `docker buildx
  imagetools inspect` (read-only: no pull, no container), and prints one
  line per image: `ok`, or `UNRESOLVED`.
- For a digest pin (MinIO), it also resolves `:latest` and says whether the
  pin is behind, and prints the new digest to paste.
- It exits non-zero if any pin fails to resolve. It is a hand-run check
  that needs Docker and network access, and `npm run verify` does not run
  it.
- The README's "Updating a pin" paragraph names the command.

## Constraints

- **Blast radius:** at most 5 files and 60 lines, no core code:
  - `scripts/check-pins.mjs` (new, about 40 lines);
  - `package.json` (one script line);
  - `README.md` (one or two lines);
  - `infra/langfuse/docker-compose.yml`, if any (the `:97` comment pointing
    at the command).
- **Node only.** No npm install, in line with the kit's "Node ≥ 22 and
  nothing else". It calls the Docker CLI only through `execFileSync`, with
  arguments read from our own Compose file, never through a shell string.
- **Read-only against registries.** It never pulls, runs or tags an image,
  and never edits the Compose file. Bumping a pin stays a deliberate change.
- **Not in `verify`.** The suite stays offline and Docker-free.
- **Out of scope:**
  - replacing MinIO with SeaweedFS or Garage. That changes the stack's
    storage service (the Compose file, Langfuse's S3 settings, the guard
    test's six services, the live check), is far beyond an adjustment, and
    needs a comparison first;
  - per-image "full tag" rules in `tests/test_compose.py` (the §4 LOW).

## Type-specific questions

### Adjustment
- **Exactly what changes:**
  - a new `scripts/check-pins.mjs`;
  - `"check:pins": "node scripts/check-pins.mjs"` in `package.json`;
  - in `README.md` → "Updating a pin": "run `npm run check:pins` to see
    whether a pin still resolves, and the newer MinIO digest";
  - optionally, the Compose comment at `:97` points to the command.
- **Blast radius:** 3–4 files, about 45–55 lines, no core code
  (`CORE_CODE` is `src/advisor/…`), no runtime path. It touches `scripts/`
  but not the kit's enforcement (`intent-check-lib.mjs`, `check-intent.mjs`,
  `ship*.mjs`), so the path table puts it at Attested.

## Assumptions I made

- **Split the "then look at SeaweedFS or Garage" part off.** An adjustment
  can't hold it. I propose a separate **experiment** (`/intent --exp`):
  - **Question:** can SeaweedFS or Garage stand in for MinIO under Langfuse
    v4 (event and media uploads, path-style S3, a healthcheck), and does
    either publish versioned images?
  - **Containment:** a scratch Compose override on a branch that is never
    merged.
  - **Result:** a note in `docs/`, then a feature intent if one wins.

  Say if you want it drafted now, as §7.
- **No unit test for the script.** Its parsing is three lines of regex over
  our own file, and a test file would push the adjustment past 60 lines. If
  you want one, this becomes a small fix or feature instead of an
  adjustment.
- **`docker buildx imagetools inspect` as the resolver,** as §4's
  implementer and reviewer used it, rather than the registries' HTTP APIs:
  one tool for Docker Hub and `cgr.dev`, and auth handled by Docker.
- **"Behind" is reported only for the digest pin.** For the tagged images,
  finding a newer patch on the same line would mean querying each
  registry's tag list. That is a possible follow-up, not this adjustment.
