<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §19 review — Time, tokens and owner wait per intent and phase

verdict: rework
tier: reviewed
reviewed-commit: 23ebd8f48f2e5fe79d494acae79b8c6f8bec630e
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed (path table: `scripts/session-event.mjs`'s logic,
`.claude/skills/**`, `scripts/ship.mjs`; `review_tier: reviewed`).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 19` →
"sampled: no".

The reviewer's own mutation batch was stopped by Claude Code for low memory
(only M4 ran); the owner asked for the rerun ("rerun the 19 mutants") and
the coordinator ran all 28 mutants in the foreground. The Mutants table
below is that run, not a prediction.

## Resolution of round 1
| Finding | Resolution | Evidence |
| --- | --- | --- |
| F1 HIGH live-check stop never ends | resolved: `GATE_END` gains `live check` | F1 KILLED by "ends a live-check stop at the commit recording the answer, in any wording (F1, F3)" |
| F2 waits outside the life (owner: clip) | resolved for in-session waits: `clipToLife` (`stats-lib.mjs:282-287`) | F2, F2s, C2, C3, C3m KILLED; the gate-side clip is unproven (F9), C1 and C4 survive (F9, F10) |
| F3 which stops count (owner: dependency stops only) | resolved: `NOT_THE_OWNER` anchored; `merged (` ends a gap | F3, F3m, R2, S10c KILLED; R3 survives (F11) |
| F4 author time (owner) | resolved for phases (`stats-io.mjs:96`); the cutover is wrong for intents merged while §19 was in flight (F8) | F4log, F4cut KILLED |
| F5 idle prompt (S12) | resolved | S12 KILLED by "opens no gap at an idle prompt on its own" |
| F6 hook wiring (M6) | resolved: process test against a temp repo | M6 KILLED by "reads the repo skill list from .claude/skills … (B1 wiring)" |
| F7 S10, S2c, S16, I5, I4, M4 | resolved: a test each | all KILLED (table below) |
| LOW unplanned `stats-io.mjs`, Progress divergences | unchanged; for the owner at the diff read | — |
| LOW Progress hashes and figures | resolved: note on pre-rebase hashes; figures marked a snapshot | read |
| LOW README / sdlc.md, auto skill colon | resolved (README.md:276, sdlc.md:151-153, auto SKILL.md:301-303) | read |
| LOW `stats -- <id>` buckets; `skillId` first integer | unchanged by choice (B1's literal text) | worth a look |
| I2 `projectSlug` | unchanged; survives by construction | worth a look |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (spec.md changed only in fb54597, plan.md only in 990cf51 and the Progress entry in 2626762) |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | findings (1): F8 |
| 4 | Tests prove the behaviour | findings (3): F9, F10, F11; 28 mutants, 20 killed, 8 survived |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (kit 366, pytest 658 reproduced; "352 after the rebase" not reproduced) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (synthetic fixtures; the hook test asserts its sentinel never reaches the log, empty stdout and stderr) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 19, feature)
  error: A live check is owed and not recorded. Do the steps in intents/19-intent-stats/review.md → ## Live check, then set live_checked: <date> in intents/19-intent-stats/metadata.yml.
  note:  25 file(s), 1665 line(s) changed outside intents/.
```
The only error is the owed live check; clearing it is the owner's.

## Findings
- **F8 HIGH** `scripts/stats-io.mjs:81` (`statsCutover`): with
  `--format=%at`, the cutover is the author time of the commit that added
  `stats-lib.mjs` (4415b20, 2026-11-13 18:04:59), not when it reached
  `main`, so every intent merged while §19 was in flight reads as not
  partial (B8). Reproduced in a scratch clone with `main` merged `--no-ff`
  with feat/19: `stats --all --json` gives §1-§13 partial, §14 and §18 not,
  though both merged on 2026-11-16 before §19 and lack the B1 hook fields.
  **Needs rework:** add `--first-parent -m` to `statsCutover`'s `git log`
  (it keeps author time, per F4, and yields the merge commit's), with a
  `stats.test.mjs` case: an intent merged on `main` between the adding
  commit's author time and a `--no-ff` merge of the stats branch is
  `partial`. A mutant dropping `--first-parent` must die.
- **F9 MEDIUM** `scripts/stats-lib.test.mjs` (F2 block, "clips a gate wait
  that runs on past the merge, and lets an unmerged intent wait up to
  now"): neither half proves its name. (a) The gate gap ends at the
  `merged (` commit, so clipping changes nothing; with `merged \(` in
  `GATE_END` the gate-side clip (`stats-lib.mjs:394`) is near-unreachable:
  F2g SURVIVES. (b) The unmerged case asserts only `sessionWaitMs === 2h`,
  which the 2 h cap gives with or without the clip at `now`: C1 (`mergedAt
  ?? Infinity`) SURVIVES. **Needs rework:** in (b) also assert `idleMs ===
  0` (kills C1); rename (a), or replace it with a case that clips, or say
  in a code comment that the gate-side clip is a guard.
- **F10 LOW** `scripts/stats-lib.mjs:283`: `if (it.startedAt === null)
  return null` (interpretation 3, "an intent with no commits gets no wait")
  is untested: C4 SURVIVES. **Needs rework:** a `computeStats` case where a
  session turn has the `skillId` of an intent with no commits, asserting no
  wait is booked.
- **F11 LOW** `scripts/stats-lib.mjs:297` (`NOT_THE_OWNER`): R3
  (`(?:blocked|waiting for …)`, "blocked" without "by N") SURVIVES. It
  would also drop `auto stopped: blocked_by record broken` (§18's stop, now
  in the `/auto` skill), which the owner must fix, so by the F3 decision it
  is owner wait. **Needs rework:** a `gateGaps` case where `auto stopped:
  blocked_by record broken` counts as gate wait.
- **LOW** (worth a look) `stats-lib.mjs:59` vs `:296`: the phase milestone
  is still `^live check recorded` while `GATE_END` accepts any `live
  check`; older intents (four `live check passed` commits) get no
  live-check phase. Consistent with B3's literal text; those intents are
  partial.
- **LOW** (worth a look) per F3, `auto stopped: build waits for the round 3
  review of 9` (1) and `too many sessions` (5) count as owner wait, as
  decided.
- **LOW** (carried) I2; `stats -- <id>` prints buckets not involving the id;
  `skillId` is the first free-standing integer. Equivalent survivors: C5
  (`>` → `>=`, a zero-length gap), C6 (`Math.max(now, startedAt)` → `now`,
  differs only when `now` precedes the first commit), R1 (anchor dropped;
  only `auto stopped:` subjects open a gap anyway).

## Mutants
Coordinator's foreground run, one mutant at a time, full kit suite each,
backup and restore by copy with diff guards; `git status --short` clean
after each batch.

| Mutant | Target | Result | Killing test |
| --- | --- | --- | --- |
| M4 | `session-lib.mjs:180` id regex unguarded | KILLED | "logs the skill and the first integer argument of a slash prompt" |
| M6 | `session-event.mjs` hook gets no skill list | KILLED | "reads the repo skill list from .claude/skills … (B1 wiring)" |
| S2c | gate wait ignores agent overlap | KILLED | "leaves agent time of the intent out of a gate wait, and another intent agent in (S2c)" |
| S10 | `auto run resumed` dropped from `GATE_END` | KILLED (3) | "ends an escalate stop at the resumed run", F3 and S2c tests |
| S10c | `blocked by` dropped from `NOT_THE_OWNER` | KILLED | "does not count a dependency stop (F3)" |
| S12 | any Notification opens a gap | KILLED | "opens no gap at an idle prompt on its own" |
| S16 | build ends at the last auto round | KILLED | "ends build at the first of several auto rounds …" |
| I2 | `projectSlug` regex | SURVIVED | (carried, equivalent on this repo) |
| I4 | `statsCutover` returns null | KILLED | "marks partial only the intent merged before stats-lib.mjs arrived on main …" |
| I5 | no pending-merge commit | KILLED | "gives an intent without a merged commit a ship phase ending at the pending merge (I5)" |
| F1 | `live check` dropped from `GATE_END` | KILLED | "ends a live-check stop … in any wording (F1, F3)" |
| F2 | no clip (gate and session) | KILLED (2) | "books no in-session wait from before the first commit or after the merge", "cuts a wait that straddles …" |
| F2g | no clip, gate side only | **SURVIVED** | F9 |
| F2s | no clip, session side only | KILLED (2) | as F2 |
| F3 | `NOT_THE_OWNER` back to `/…\|blocked/` | KILLED | "counts a blocked ship dry-run and ready-for-ship (until merged) as owner wait (F3)" |
| F3m | `merged (` dropped from `GATE_END` | KILLED (2) | F3 test, "clips a gate wait …" |
| F4log | log format `%ct` | KILLED (2) | "keeps distinct phases for a rebased intent …" |
| F4cut | cutover format `%ct` | KILLED | "marks partial only the intent merged before …" |
| C1 | `mergedAt ?? Infinity` | **SURVIVED** | F9 |
| C2 | no clip at the start | KILLED (2) | F2 tests |
| C3 | no clip at the end | KILLED (2) | F2 tests |
| C3m | end clip ignores `mergedAt` | KILLED (2) | F2 tests |
| C4 | no null guard for an intent without commits | **SURVIVED** | F10 |
| C5 | `>` → `>=` | SURVIVED | equivalent |
| C6 | clip at `now` without `startedAt` | SURVIVED | near-equivalent |
| R1 | anchor dropped from `NOT_THE_OWNER` | SURVIVED | equivalent |
| R2 | `waiting for N to merge` dropped | KILLED (2) | "pairs a stop or drafted commit with the owner's answer", "does not count a dependency stop (F3)" |
| R3 | `blocked` without "by N" | **SURVIVED** | F11 |
| G1 | `GATE_END` only `live check recorded` | KILLED | "ends a live-check stop … in any wording (F1, F3)" |

The rework must kill C1, C4, F2g (or document the guard), R3, and a
cutover mutant dropping `--first-parent` once F8 lands.

## Not checked
- "kit 352 after the rebase" (Progress): not reproduced.
- `npm run stats -- --all` on real transcripts this round (memory); round
  1's run was clean and no output path changed.
- From round 1: the hook in a live session, the figures against owner
  memory, `projectSlug` for unusual paths.

## Live check
- owed: rule 3 (the hook in real sessions; stats over real transcripts),
  AC7.
- steps: after the merge, in the main checkout: `npm run stats -- 13` (or
  the latest shipped intent), compare per-phase elapsed, gate wait,
  in-session wait and tokens (coordinator vs agents) with your memory of
  the run; `npm run stats -- --all`; then type `/sessions`, `/spec 19` and
  `yes to 16`, and read the last lines of
  `.git/product-advice-agent-sessions.jsonl`.
- you should see: no prompt or response text anywhere; §1-§18 marked
  `partial` (§14 and §18 included, once F8 is fixed); `/sessions` →
  `"skill":"sessions"`, no `skillId`; `/spec 19` →
  `"skill":"spec","skillId":19`; the plain prompt with neither; no hook
  output or error.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats` at 23ebd8f; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 366 tests, 0 fail; "All
  checks passed!"; "157 files already formatted"; mypy "Success: no issues
  found in 28 source files"; "658 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "25 file(s), 1665 line(s)". Matches.
- **Coordinator, re-run:** the 28 mutants in the table, in the foreground
  (the reviewer's batch had been stopped for memory). Against the
  reviewer: M4 KILLED, as it ran. Against its predictions (not results):
  C3m was predicted to survive and is KILLED; R3 was predicted killed and
  SURVIVES (added as F11); every other prediction holds. Against the
  implementer: every kill it claims (F1, S10, S12, M6, S2c, S16, I5, I4,
  M4, F2, F3, F4) holds.

**Reviewer, verified:** verify and check:intent at 23ebd8f; the round-2
diff read in full, spec.md and plan.md provenance per commit; F8 reproduced
in a scratch clone (ids and partial flags only), deleted after; history
subjects for stop and live-check wordings as counts only; M4 run and
killed; after its batch was stopped mid-S10c, `stats-lib.mjs` restored by
copy and checked clean.

**Taken on trust:** none of the mutant results (all re-run here); the
transcript format's stability, as in round 1.
# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 1fb88e2e13af4e365d2313accfb12208210494c4
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, by the path table (`scripts/session-event.mjs`'s logic,
`.claude/skills/**`, `scripts/ship.mjs`) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 19` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Findings F2, F3 and F4 need the owner's decision, so the run stops; the
mechanical items wait for the same rework.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): unplanned `stats-io.mjs` and Progress-only divergences |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (4): F1-F4 |
| 4 | Tests prove the behaviour | findings (3); 49 mutants, 39 killed, 10 survived |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): Progress hashes and snapshot figures |
| 7 | Documentation | findings (1) |
| 8 | Guardrails and hygiene | pass (prompt-text privacy proven; hook silent and total) |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 19, feature)
  note:  23 file(s), 1505 line(s) changed outside intents/.
```

### Findings
- **F1 HIGH** `scripts/stats-lib.mjs:284` (`GATE_END`): the owner's wait at a
  live-check stop is never counted; `auto stopped: live check owed` →
  `live check recorded` gives no gate gap (spec B6: the gap ends at "the
  next commit that records the owner's answer (a gate, …)"). Six real
  stops (§2, §4, §5, §6, §8, §9). **Needs rework:** add `live check
  recorded` to `GATE_END`, with a `gateGaps` test. (Accepting older
  wordings such as `live check passed` for the backfill is part of F4's
  decision list below.)
- **F2 HIGH** `scripts/stats-lib.mjs:390-400`: in-session waits outside the
  intent's lifetime are booked to it (`spread` clamps into the last phase):
  after the merging turn, an overnight gap goes to that intent (real: §7
  elapsed 26m, in-session 2h00m, idle 5h29m; §9 idle 54h06m on 49h20m
  elapsed). **Needs decision:** clip gate and session waits to the
  intent's [first commit, merge or now] span, or keep B6's literal rule.
- **F3 MEDIUM** `scripts/stats-lib.mjs:285` (`NOT_THE_OWNER`): `/…|blocked/`
  also drops `auto stopped: ship dry-run blocked, changes after the
  reviewed commit` (§1, §3, §10), which the owner must act on; `ready for
  /ship` → `merged` is not gate wait either. B6 says every `auto stopped:`
  starts gate wait. **Needs decision:** which stops count as the owner's
  wait (only dependency stops excluded, or also ready-for-ship counted),
  and whether older live-check wordings close a gap.
- **F4 MEDIUM** `scripts/stats-lib.mjs:26,42`: phases use committer time
  (`%ct`, spec B3 "by committer time"), which every rebase rewrites; all
  eight §19 commits carry 18:18:13-14 while their author times run
  18:00:55 → 18:18:14, so a rebased intent's build and review collapse.
  `statsCutover` has the same issue. **Needs decision:** switch to author
  time (`%at`), amending B3.
- **F5 MEDIUM** `scripts/stats-lib.test.mjs:190`: "idle prompts do not
  count" is not proven (S12 survives). **Needs rework:** an `idle_prompt`
  with no permission prompt before it gives no gap.
- **F6 MEDIUM** `scripts/session-event.mjs:27`: the hook's skill-list wiring
  is untested (M6 survives: B1 would be dead in production). **Needs
  rework:** a process test against a temp repo with `.claude/skills/spec/`
  asserting `skill: "spec", skillId: 17`, no sentinel, empty output,
  exit 0.
- **F7 MEDIUM** survivors whose fix the spec or plan fixes. **Needs
  rework:** one test each: S10 (`auto stopped: escalate…` → `auto run
  resumed`), S2c (gate gap with a tagged agent inside), S16 (two `auto
  round` commits), I5 (pending merge on an intent without `merged`: a ship
  phase), I4 (cutover: earlier merge `partial`, later not), M4
  (`/review feat/19-x` → no `skillId`).
- **LOW** (worth a look, owner to ratify at the diff read) the unplanned
  `scripts/stats-io.mjs` and divergences 1, 2, 4, 6, 8 stated only in
  Progress; the reviewer judges each acceptable (a Stop restarting a
  permission wait means those waits are rarely measured;
  `SDLC_STATS_TRANSCRIPTS` is read by production code).
- **LOW** `plan.md` Progress: pre-rebase hashes; live figures drifted
  (now 177h39m elapsed …). **Needs rework:** current hashes, figures
  marked a snapshot.
- **LOW** (worth a look) README and `sdlc.md` don't mention `npm run
  stats`; `.claude/skills/auto/SKILL.md:287-291` leaves a colon that now
  introduces the safety rules, and two blank lines.
- **LOW** (worth a look) `stats-lib.mjs:494-495`: `stats -- <id>` prints
  shared and unattributed buckets that don't involve the id; idle sums
  gate and session idle over the same wall-clock; `skillId` takes the
  first integer (`/review … round 2` → 2).
- **I2** (worth a look) `projectSlug` (`/[^A-Za-z0-9]/` vs `/[\\/:]/`)
  survives; both sides use the same function and the real slug was
  confirmed on disk.

**Mutants** (49, kit suite each; scratch exports, originals restored): 39
KILLED, among them every privacy mutant (M1-M3, M7), the cap and idle
(S1, S1b), agent time in session gaps (S2, S2b), dedupe (S3), shared and
guessed turns (S4, S5), tag parsing (S6-S6c), worktree id and skillId
(S14, S17), missing milestones (S7, S7b), partial (S8-S8c), skipped lines
(S9-S9d, S15), I/O (I1, I3, I6-I8), ship never blocked and stats.md in
bookkeeping (H1-H4). SURVIVED (10): M4 `session-lib.mjs:180`, M6
`session-event.mjs:27`, S2c `stats-lib.mjs:382`, S10 and S10c
`stats-lib.mjs:284-285`, S12 `:209`, S16 `:77`, I2, I4, I5 (`stats-io.mjs`).

### Not checked
- The hook in a live Claude Code session (the live check), including
  whether a background-agent completion fires `UserPromptSubmit`.
- The figures against what actually happened (owner memory, AC7).
- `projectSlug` for paths with dots or underscores; Codex sessions.
- Ship's `stats.md` on the real repo; the resumed-ship path with stats.

### Live check
- owed: rule 3 (the hook in real sessions; stats over real transcripts),
  spec AC7.
- steps: after the merge, in the main checkout: `npm run stats -- 13` (or
  the latest shipped intent), compare per-phase elapsed, gate wait,
  in-session wait and tokens (coordinator vs agents) with your memory of
  the run; `npm run stats -- --all` (§1-§18 marked `partial`, a total line,
  shared/unattributed blocks, `skipped lines: N`); then type `/sessions`,
  `/spec 19` and `yes to 16`, and read the last lines of
  `.git/product-advice-agent-sessions.jsonl`.
- you should see: no prompt or response text in any stats output;
  `/sessions` → `"skill":"sessions"`, no `skillId`; `/spec 19` →
  `"skill":"spec","skillId":19`; the plain prompt with neither; otherwise
  only `ts, worktree, branch, id, event, session, promptChars, detail`
  (`detail` = `"<n> chars"`); no hook output or error in the session.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats` at 1fb88e2; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 309 tests, 0 fail; "All
  checks passed!"; "150 files already formatted"; mypy "Success: no issues
  found in 27 source files"; "624 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "23 file(s), 1505
  line(s)". Matches.
- **Coordinator, re-run:** M4, M6, S2c, S10, S10c, S12, S16, I2, I4, I5 each
  SURVIVED the kit suite (M6 confirmed directly: "tests 309, pass 309, fail
  0"). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, sampling, 49 mutants, a
17-input hook fuzz against a temp repo (exit 0, empty output, sentinel
never logged), `stats -- --all` on real data checked line by line for
shape only, scenario probes for F1-F4, committer vs author times, skill
hunks only in the named paragraphs, nothing pushed.

**Taken on trust:** the transcript format's stability; Claude Code's
project-folder naming beyond this repo's path.
