<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §6 review — A pin-check script for the Langfuse stack's images

verdict: attest
tier: attested
reviewed-commit: e1d81ddc10bf241959d5ddacf9b2586ae049f44b
round: 1
sampled: no
run: auto
live-check: owed

Tier: Attested, set by the path table (input 1).
- `scripts/check-pins.mjs` is under `scripts/**` but is not one of the
  listed enforcement scripts.
- `package.json` is build config, and the `README.md` change is wording.
- The Compose file is not on the Reviewed row, and its change is the
  comment at `:97` only (`# Update: npm run check:pins (prints the newest
  digest to paste)`). No image, environment or service line changed, and
  `tests/test_compose.py` still passes (5/5).

`review_tier` is empty, and no CRITICAL or HIGH finding raises the tier.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (adjustment, no plan; exactly the four files the intent names, plus metadata) |
| 2 | Type check | pass (adjustment, 4 files, 47 lines: within 5 and 60) |
| 3 | Behaviour against the intent's Outcome | pass (each bullet exercised by hand) |
| 4 | Tests prove the behaviour, not only pass | findings (1): no test covers the script, by the intent's design; every behavioural line exercised by hand instead |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass |
| 7 | Documentation | findings (1) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 6, adjustment)
  note:  4 file(s), 47 line(s) changed outside intents/.
```

## Findings
- **LOW** `scripts/check-pins.mjs` (whole file) — `npm run verify` neither
  runs nor tests it, so every script mutant survives the suite: `:9`
  regex, `:13` argv, `:15-17` exit 2, `:19` stderr line, `:22` digestOf,
  `:28` `failed++`, `:34`, `:37-39`, `:42` exit code. The accepted intent
  waives the test ("No unit test for the script… If you want one, this
  becomes a small fix or feature"), so this is not rework. Worth a look.
- **LOW** `scripts/check-pins.mjs:9,41-42` — if no `image:` line matches
  (a reformatted Compose file, or a future `image: >-` style), the script
  prints nothing and exits 0, which reads as a silent pass. Reproduced with
  `services: {}`. Worth a look: `if (!refs.length) { console.error('no
  image: lines found'); process.exit(1); }`.
- **LOW** `scripts/check-pins.mjs:33,35` — a `name:tag@sha256:…` reference
  makes it look up `name:tag:latest`, an invalid reference; it prints
  "could not resolve … invalid reference format" and exits 0. No current
  line has this form. Worth a look.
- **LOW** `CLAUDE.md` "Commands" — `npm run check:pins` is not listed
  there, though `README.md:67` names it. Adding it would be a fifth file,
  still within the adjustment limit. Worth a look.

Checked against the intent's constraints, with no finding:
- **Read-only:**
  - the only Docker call is `docker buildx imagetools inspect <ref>`;
  - after the runs, `docker image ls` holds no `redis:latest` and no
    `*:0.0.0-nope`, so inspect did not pull;
  - `readFileSync` is the only file I/O.
- **No shell:** `execFileSync('docker', [..., ref])` takes an argument
  array with no `shell` option, and `docker` resolves to `docker.exe`. Image
  lines with shell metacharacters (`;echo…&&calc`, `$(touch…)`,
  backticks, `|whoami`) came back `UNRESOLVED … invalid reference format`,
  exit 1, and no side-effect files appeared.
- **Node only:** `node:child_process` and `node:fs`; no dependency added.
- **Not in verify:** `verify` is unchanged; `README.md:67` says so.
- **Exit codes:**
  - any UNRESOLVED exits 1;
  - a missing Docker exits 2, which is non-zero and distinct;
  - an unresolvable `:latest` is not a pin, so it is printed but not
    counted as a failure. That is consistent with the intent.
- **Blast radius:** 4 files and 47 lines; no core code.

## Not checked
- **Docker present but buildx missing, or the daemon or builder stopped.**
  By reading the code, each reference would print UNRESOLVED and exit 1,
  rather than take the exit-2 path. The message may not make clear that
  Docker is the problem.
- **Private registries, authentication, and Docker Hub rate limits.**
- **A "newer patch on the same line" check for the five tagged pins:** out
  of scope by the intent's assumption.
- **The owner's own machine and network:** the reviewer's run is evidence,
  not the owner's check.
- **`docker compose config` on the changed file:** not run, because the
  worktree has no `infra/langfuse/.env`. The YAML is checked only through
  `tests/test_compose.py`, which passes.
- **Output on macOS or Linux:** not tested; this is a Windows host.

## Live check
- owed: rule 1. The diff touches `infra/` (`infra/langfuse/docker-compose.yml:97`).
  The change is a comment with no runtime effect, but rule 1 is path-based,
  and nothing waives it automatically. It is a ten-second check, which also
  covers the owner's own Docker and network.
- steps:
  1. With Docker Desktop running, open a terminal in
     `C:\Users\eric\src\product-advice-agent-wt\6-pin-check-script`.
  2. `npm run check:pins`
  3. Optional: `git diff main...adjust/6-pin-check-script -- infra/`. Only
     the `# Update:` comment line changed.
- you should see: six `ok` lines (langfuse-worker 4.78.0, langfuse 4.78.0,
  clickhouse-server 26.3.62.3, the minio digest, redis 7.4.12, postgres
  17.11). Under minio: `pin is current (cgr.dev/chainguard/minio:latest)`,
  or `pin is BEHIND … to update paste: …` if Chainguard has published since.
  Exit 0.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/6-pin-check-script` at e1d81dd, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "67 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "116 passed".
  Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0. Matches.
- **Coordinator, re-run:** `npm run check:pins` → the same six `ok` lines,
  "pin is current", exit 0. Matches.
- **Coordinator, re-run:** survivor sample `:28` `failed++` → `failed += 0`
  (backup by copy, file-changed check, restore by copy): kit 255 pass,
  pytest "116 passed". It survives, as the review says it does by design.
- **Coordinator, re-run:** a copy of the script against a scratch Compose
  file `services: {}` → no output, exit 0. Matches the silent-pass LOW.

**Reviewer, verified:**
- `verify`, `check:intent` and `check:pins`, as above.
- `sdlc:scan --sample-due auto --exclude 6` → "nth attested auto change =
  1, every 3, sampled: no".
- Path exercises with a byte-identical script copy and scratch Compose files
  (scratchpad `rev6/`):
  - a non-existent tag → UNRESOLVED, exit 1;
  - a zero digest → UNRESOLVED, exit 1;
  - a behind digest pin → "pin is BEHIND … to update paste: …", exit 0;
  - Docker hidden from `PATH` → the message, exit 2;
  - a mixed file → 2 UNRESOLVED, exit 1, with the commented line skipped;
  - shell metacharacters → inert;
  - `services: {}` → silent, exit 0;
  - a tag+digest reference → exit 0.
- `docker image ls` showed no pulled images.
- Clean state, and no tracked file edited.

**Taken on trust:** that `docker buildx imagetools inspect` never pulls, in
any configuration (Docker's documented behaviour, backed by `image ls`).
