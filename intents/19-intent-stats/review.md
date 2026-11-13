<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §19 review — Time, tokens and owner wait per intent and phase

verdict: rework
tier: reviewed
reviewed-commit: 1fb88e2e13af4e365d2313accfb12208210494c4
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, by the path table (`scripts/session-event.mjs`'s logic,
`.claude/skills/**`, `scripts/ship.mjs`) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 19` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Findings F2, F3 and F4 need the owner's decision, so the run stops; the
mechanical items wait for the same rework.

## Passes
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

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 19, feature)
  note:  23 file(s), 1505 line(s) changed outside intents/.
```

## Findings
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

## Not checked
- The hook in a live Claude Code session (the live check), including
  whether a background-agent completion fires `UserPromptSubmit`.
- The figures against what actually happened (owner memory, AC7).
- `projectSlug` for paths with dots or underscores; Codex sessions.
- Ship's `stats.md` on the real repo; the resumed-ship path with stats.

## Live check
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

## Verified myself vs. taken on trust

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
