<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §28 review — Two machines can give two intents the same number

verdict: escalate
tier: reviewed
reviewed-commit: 6d2ae42
main: 13f13dd
round: 2
sampled: yes
run: auto
live-check: owed

No finding needs rework. The tier is Reviewed (REVIEW-POLICY.md, the intent
skill, the deliver scripts), so **you read the diff**
(`git diff main...feat/28-reserve-intent-ids`), then run the live check.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the rework matches the D1 b amendment; divergence 7 is now documented |
| 2 | Type check | FAIL only on the owed live check, which is yours to clear |
| 3 | Behaviour against the spec | pass: B1–B24 and AC1–AC21; AC22 is the live check |
| 4 | Tests prove the behaviour | pass: every round-1 rework mutant is killed; M5 is equivalent; S7, S9 and S11 accepted as in round 1 |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass, one count stale again after the merge (LOW) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check
```
type-check: FAIL (intent 28, feature)
  error: A live check is owed and not recorded. Do the steps in intents/28-reserve-intent-ids/review.md → ## Live check, then set live_checked: <date> in intents/28-reserve-intent-ids/metadata.yml.
  note:  24 file(s), 1378 line(s) changed outside intents/.
```

- **Round 1 resolved:**
  - M7 (prompt env) is killed by the new `runGitBounded` env test.
  - M6 (streams) is killed by the harness test.
  - Q6 (symref) is killed by AC7's exact clash lines.
  - S4 is killed by AC14's `could not fetch origin`.
  - S2 is killed by AC15's `no folder intents/40-*`.
  - Your D1 b: `failureReason` is now `lines.find(/^(fatal|error):/) ?? lines[0] ?? "git exited <code>"`, and a timeout is unchanged. AC4 requires `(fatal: …)`. M9, plus two variants (first line only; `error:` not recognised), are killed.
- **M5** (no `finish` on `exit` after a timeout) **is equivalent.** The
  streams are destroyed in the same callback, so `close` follows `exit` at
  once and resolves `null` the same way, with a 2-s fallback behind it.
  Measured on copies outside the repo: original 1996 / 1912 ms, M5 1865 /
  1850 ms. M5 and M6 applied together are killed by both orphan tests.
- **The orphan and harness tests are robust here:** 5 sequential and 4
  concurrent runs passed, and no stray processes were left. They kill only
  pids they started.
- **The merge 3be0ebe is automatic.** `git merge-tree --write-tree` gives
  `b4e327e…`, equal to its tree. §28's policy-text changes against main are
  byte-identical to round 1's, so B19–B24 are still word for word. §29's
  edits to the same files sit in separate hunks.

## Findings
- **LOW** `scripts/remote-io.test.mjs:76-78` — the orphan test needs its
  middle process to exit (800 ms) before the kill (1500 ms), about 0.5 s of
  slack. Under heavy load it could fail falsely, never pass falsely. Worth a
  look. If it flakes, signal the middle's exit through a file.
- **LOW** `plan.md` Progress — "product 880 pass" was true at ebbfaf0; after
  main's merge it is 926. Worth a look.
- **LOW, carried over** — worth a look in your diff read:
  - the skill's exit 2 only reports, while REVIEW-POLICY.md's exception
    says "asks the owner" on "no remote" (both verbatim from the spec, B7
    and B19);
  - `sdlc.md`'s step-1 lines are ragged;
  - divergence 7's `<id>-?` placeholder.

## Not checked
- The POSIX path of `runBounded` (this machine is Windows).
- A real GitHub fetch and push, Git Credential Manager with
  `GCM_INTERACTIVE=never`, a real network outage, and how GitHub shows a
  parentless `intent/<n>` branch. These are the live check (rule 3).
- Whether a real `/intent` session follows the skill's step 5.

## Live check
- owed: rule 3 (the real-origin items above; spec AC22). In the main
  checkout after the merge, or in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/28-reserve-intent-ids` before
  it.
- steps:
  1. Online: `npm run queue -- --next-id`
  2. With Wi-Fi off (or the cable out): `npm run queue -- --next-id`
  3. Network back on. On the first real `/intent` after the merge, let it
     reserve, then look at GitHub.
- you should see:
  - step 1: one number (30 or more), no credential prompt or window, no
    "could not fetch" line, no `§n clash` line, within a few seconds.
  - step 2: within about 10 s, `could not fetch origin (fatal: …): counted
    origin as last fetched` (e.g. "unable to access … Could not resolve
    host"), and still one number on stdout.
  - step 3: "reserved on origin as `intent/<n>`" without being asked. On
    GitHub, `intent/<n>` has no parent and holds exactly
    `intents/<n>-<slug>/intent.md` and `metadata.yml`, and GitHub's `main`
    did not move.
- Steps 1 and 2 can be done before `/deliver 28`. Step 3 needs the merge,
  so record `live_checked` on steps 1–2 and treat step 3 as the first use.

## Eval run
- not owed (no listed path): `uv run advisor-analysis owes-run --base main`
  prints "not owed (no listed path changed)".

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 6d2ae42:
  - `npm run verify`: exit 0; kit 490/490; pytest 926.
  - `npm run check:intent`: FAIL on the live check only.
  - Merge-tree identity, and the md5 of §28's policy-text lines.
  - 10 mutants against the full kit suite.
  - The M5 timing comparison.
  - The flakiness runs and the leftover-process check.
  - No GitHub contact.
- **Coordinator, re-run**, at 6d2ae42:
  - `npm run verify`: kit **490 pass, 0 fail**; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **926 passed**, which matches.
  - `npm run check:intent`: the same FAIL (live check only), which matches.
  - Merge-tree of 3be0ebe's parents: `b4e327eeb61b5756d0c8951005775c4c5e5b3ba9`, equal to its tree, which matches.
  - The surviving mutant and the mutants the rework says it kills, against the full kit suite:
    - M5: **survived** (equivalent).
    - Killed: M6, M7, Q6, S2, S4, M9, M9b, M9c, and M5+M6 together, each by the tests the reviewer named.
    - All match. Restored by byte copy; `git status --short` was clean.
  - `npm run sdlc:scan -- --sample-due auto --exclude 28`: "sampled: yes".
  - No real remote was contacted.
- Taken on trust: the POSIX tree-kill branch.

---

# Round 1

verdict: rework
tier: reviewed
reviewed-commit: 89b665f
main: 47f618f
round: 1
sampled: no
run: auto
live-check: owed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (divergences judged below) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: B1–B24 and AC1–AC21 checked in code and tests; AC22 is the live check |
| 4 | Tests prove the behaviour | findings (10 of 64 mutants survive the full kit suite) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass, one stale count (LOW) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (no new dependency, no secret) |
| 9 | Repo footguns | pass: the test sandboxes strip `GIT_*` and use an empty global config with `GIT_CONFIG_NOSYSTEM`; nothing reaches GitHub |

## Type check
```
type-check: PASS (intent 28, feature)
  note:  24 file(s), 1272 line(s) changed outside intents/.
```

**What holds:**
- **The policy texts** (B19 REVIEW-POLICY.md "Merging" and its tier row,
  B20 CLAUDE.md, B21 AGENTS.md, B22 intents/README.md, B23 sdlc.md, B24
  the intent skill 0.3.0) are word for word, whitespace aside. The
  REVIEW-POLICY re-wrap only keeps `npm run reserve-id -- <id>` on one line.
- **The standing exception is narrow:** one parentless commit holding only
  `intent.md` and `metadata.yml`; never `main`, a force push, a merge, a
  deletion, another number or a subagent; on any failure nothing is pushed
  by other means, and the owner is asked.
- **`reserve-id`** pushes exactly `['push','origin','<commit>:refs/heads/intent/<id>']`.
  Its exit codes are 0/1/2/3 as specified. AC9a replays 2026-11-24 with 15
  unpushed commits, and origin's and local `main` stay unchanged.
- **`--next-id`:** a 10-s bounded fetch with a tree kill, `--no-fetch`, and
  warnings rather than errors when offline or with no remote. Clash lines go
  to stderr. The listing and `--json` never fetch.
- **`/deliver`'s** clash stop and reservation note work on both the dry run
  and the real run.

## Findings
- **HIGH** `scripts/remote-io.mjs:96` — B8's `GIT_TERMINAL_PROMPT=0` and
  `GCM_INTERACTIVE=never` are not proven. M7 (`env: { ...env }`) survives,
  because the test sandbox already sets both. Needs rework: a test that
  calls `runGitBounded` with an env lacking both and prints them through a
  git alias, asserting `0 never`. M7 must be killed.
- **MEDIUM** `scripts/remote-io.mjs:80, 86-87` — the fallbacks for a
  descendant that escapes the tree kill are untested: M5 (wait for `close`
  after a timeout) and M6 (streams not destroyed) survive. Needs rework: a
  `runBounded` test where an orphaned grandchild survives the tree kill and
  holds stderr (parent → detached middle → detached grandchild with
  `stdio: 'inherit'`, middle exits). Assert the return comes within the
  bound plus about 2 s, then kill the orphan by pid. M5 and M6 must be
  killed.
- **MEDIUM** `scripts/queue-origin.test.mjs` (AC7) — skipping the
  `origin/HEAD` symref is untested. With Q6, every clash line prints twice.
  Needs rework: in AC7, assert the stderr clash lines are exactly
  `['§23 clash: intents/23-a here, intents/23-b on origin (origin/main)']`.
  Q6 must be killed.
- **MEDIUM** `scripts/reserve-id.mjs:66` (AC14) — B3.3 is not proven apart
  from B3.8: S4 (fetch failure ignored) survives. Needs rework: assert the
  unreachable case's output contains `could not fetch origin`. S4 must be
  killed.
- **MEDIUM** `scripts/remote-io.mjs:104` (`failureReason`) — git's last
  stderr line is boilerplate for common failures, e.g. "could not fetch
  origin (and the repository exists.)". **Decision (owner, 2026-11-24, "28 D1
  b"): use the first `fatal:` or `error:` line, else the first non-empty
  line, else "git exited <code>".** The plan is amended above its Progress
  marker, on the owner's decision. Needs rework: implement it, with a test
  that pins the AC4 reason (it starts with `fatal:`). M9 (the last line)
  must be killed.
- **LOW** `scripts/reserve-id.mjs:55` (AC15) — S2 (the no-folder check
  removed) survives, because Node's crash exit is also 1. Needs rework:
  assert the output contains `no folder intents/40-*`. S2 must be killed.
- **LOW** `scripts/reserve-id-lib.mjs:55` (divergence 7) — a reservation
  branch with no intent folder counts as `taken` (exit 1). The spec doesn't
  cover the case, but it follows from B5 and B10 and changes no outcome
  that matters: nothing is pushed either way. It is tested. The `<id>-?` in
  its message is odd. Worth a look in your diff read.
- **LOW** `.claude/skills/intent/SKILL.md` step 5 against REVIEW-POLICY.md
  "Merging" — the policy (verbatim from B19) says the agent "says why and
  asks the owner" when there is no remote, while the skill (verbatim from
  B7) only reports on exit 2. The spec itself is inconsistent here. Worth a
  look.
- **LOW** `sdlc.md:21-23` — the added `npm run reserve-id` (needed for AC20)
  leaves one line ragged. Cosmetic.
- **LOW** `plan.md` Progress — "product 863 pass" predates main's merge; it
  is 880 at the reviewed commit.
- **Accepted survivors, no rework:**
  - S7 (`hash-object` without `--path`): equivalent without
    `.gitattributes` or autocrlf in the sandbox.
  - S9 (`checkCarried` result ignored): a defence construction never
    trips; `checkCarried` itself is unit-tested.
  - S11 (`update-ref` removed): equivalent, since git's push already
    updates the tracking ref; disclosed by the implementer.

## Not checked
- The POSIX branch of `runBounded` (`detached` plus `process.kill(-pid)`):
  this machine runs Windows.
- A real GitHub fetch and push, Git Credential Manager with
  `GCM_INTERACTIVE=never`, a real network outage, and how GitHub shows a
  parentless `intent/<n>` branch. These go to the live check (rule 3).
- Whether a real `/intent` session follows the new skill step 5.

## Live check
- owed: rule 3 (the Not-checked items above about the real origin). After
  the rework, in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/28-reserve-intent-ids` or in
  the main checkout after the merge.
- steps:
  1. Online: `npm run queue -- --next-id`
  2. With Wi-Fi off (or the cable out): `npm run queue -- --next-id`
  3. Network back on. On the first real `/intent` after the merge, let it
     reserve, then look at GitHub.
- you should see:
  - step 1: one number (30 or more), no credential prompt or window, no
    "could not fetch" line, no `§n clash` line, within a few seconds.
  - step 2: within about 10 s, `could not fetch origin (fatal: …): counted
    origin as last fetched` on stderr, and still one number.
  - step 3: the session says "reserved on origin as `intent/<n>`" without
    asking. On GitHub, `intent/<n>` has no parent and holds exactly
    `intents/<n>-<slug>/intent.md` and `metadata.yml`, and GitHub's `main`
    did not move.

## Eval run
- not owed (no listed path): `uv run advisor-analysis owes-run --base main`
  prints "not owed (no listed path changed)".

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 89b665f:
  - `npm run verify`: exit 0; kit 485/485; pytest 880.
  - `npm run check:intent`: PASS.
  - `owes-run`: not owed.
  - `--next-id --no-fetch` printed 30.
  - The `failureReason` text, against a local origin with a missing path.
  - 64 mutants: 54 killed, 10 survived. Restored by byte copy; clean.
- **Coordinator, re-run**, at 89b665f:
  - `npm run verify`: kit **485 pass, 0 fail**; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **880 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 28, feature)`, which matches.
  - Every mutant the review lists as surviving, against the full kit suite (`node --test scripts/*.test.mjs`): M5, M6, M7, M9, Q6, S2, S4, S7, S9 and S11 all **survived** (fail 0), which matches.
  - Restored by byte copy; `git status --short` was clean.
  - No real remote was contacted.
- Taken on trust: the POSIX tree-kill branch, which was only read.
