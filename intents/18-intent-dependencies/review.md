<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §18 review — Intent dependencies

verdict: escalate
tier: reviewed
reviewed-commit: 6199bba1d45ae84218fdb73dd7a7d80b33ed7627
round: 3
sampled: no
run: auto
live-check: not-needed

Tier: Reviewed, by the path table (`scripts/intent-check-lib.mjs`,
`scripts/check-intent.mjs`, `.claude/skills/**`). Verdict escalate: no
finding needs rework or a decision; the owner reads the diff because of
the tier.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 18` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Rebase: the branch was rebased onto main 1255175 (the merge-base is main).
`git diff main...HEAD --name-only` contains no `intents/21-*` file.
`git diff 3068ab6 e08b7b7` (round 2's reviewed commit against its rebased
review commit, with `intents/21-*` excluded) touches only §18's review.md.
The code round 2 reviewed is unchanged.

## Resolution of round 2
| # | Finding | Resolution |
| --- | --- | --- |
| F9 MEDIUM | `queue.mjs:96` `--json` branch-only blocker (M27b) | resolved: `queue.test.mjs:189-191` parses `--json`; `blocked_by_open` is `[73]` and no problem says "on no branch". M27b is KILLED by "F3: a blocker that exists only on a branch is open, not an unknown id" |
| F10 LOW | lexical ordering (N10, N07) | resolved: blockers-lib.test "orders ids numerically, not lexically" (direct `['13','9']` → `['9','13']`, further `['100','12']` → `['12','100']`) kills N10-direct and N10-further; spawn-intent.test "names the lowest open blocker numerically across id widths" (blockers 13 and 9 → §9) kills N07 |
| F11 LOW | N08, which unknown blocker is named | unchanged by design; N08 still survives; the spec does not fix which one is named |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (round-3 diff `e08b7b7..HEAD`: three test files, plus plan.md below `## Progress` (line 125) and `auto_round: 3`; spec.md and intent.md unchanged) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (no source change since round 2; openChain probed directly gives `{"direct":["9","13"],"further":["12","100"]}`) |
| 4 | Tests prove the behaviour | pass: 10 mutants, 9 killed, 1 survived (N08, accepted in round 2) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (Progress "Kit tests 296 -> 298" reproduces; "9 and 13; 12 and 100" match the tests) |
| 7 | Documentation | pass (no doc change in round 3; round 2's check stands) |
| 8 | Guardrails and hygiene | pass (tests only, no dependency, no secrets) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 18, feature)
  note:  19 file(s), 696 line(s) changed outside intents/.
```

## Findings
- **F11 LOW** (worth a look, carried over) `scripts/spawn-intent.mjs:119`:
  N08 survives. No test covers which of several unknown blockers spawn
  names, and the spec does not fix it. No rework required.

No other findings.

**Mutants** (each run against the full kit suite `node --test scripts/*.test.mjs`;
backed up and restored by copy; `git diff --quiet` confirmed each mutant applied and was then restored):

| Mutant | Target | Result | Killing test |
| --- | --- | --- | --- |
| M27b | `scripts/queue.mjs:96` `queueData(collectEntries(), {})` | KILLED (fail 1) | queue.test "F3: a blocker that exists only on a branch is open, not an unknown id" |
| N07 | `scripts/spawn-intent.mjs:117` lexical sort `(a.id < b.id ? -1 : 1)` | KILLED (fail 1) | spawn-intent.test "names the lowest open blocker numerically across id widths" |
| N10-direct | `scripts/blockers-lib.mjs:60` direct `.sort()` | KILLED (fail 1) | blockers-lib.test "orders ids numerically, not lexically" |
| N10-further | `scripts/blockers-lib.mjs:67` further `.sort()` | KILLED (fail 1) | blockers-lib.test "orders ids numerically, not lexically" |
| N12 (new) | `scripts/blockers-lib.mjs:67` further sorted descending | KILLED (fail 3) | blockers-lib.test "follows chains, each id once", "lists each id once and in ascending order…", "orders ids numerically…" |
| N08 | `scripts/spawn-intent.mjs:119` `blockers.find(unknown)` | SURVIVED (fail 0) | none (F11, accepted) |
| M26 (regression) | `scripts/queue.mjs` `isMerged(picked.metadata)` | KILLED (fail 1) | queue.test "B3: a merged: on the blocker branch copy does not clear it; main decides" |
| M41 (regression) | `scripts/session-io.mjs` mainMetaOf prefers branch metadata | KILLED (fail 1) | spawn-intent.test "B3: a merged: on the blocker branch copy does not clear it" |
| M45 (regression) | `scripts/spawn-intent.mjs:120` `if (false) fail(` | KILLED (fail 1) | spawn-intent.test "refuses a non-digit id and the intents own id as a broken record" |
| N05 (regression) | `scripts/spawn-intent.mjs:117` `blockers.find(open)` | KILLED (fail 2) | spawn-intent.test "names the lowest open blocker" and "…numerically across id widths" |

The round-3 diff changes no source lines, only tests. Its new assertions
each kill at least one mutant above, so they are not vacuous. The tests
prove the behaviour; they do not merely pass.

## Not checked
- A real `/auto` run reaching step 4 on a blocked intent (B8 is prose).
- `npm run queue -- --json` on the live repo with a branch-only blocker
  (proven in a temp repo by queue.test only).
- Rebasing feat/14 and feat/17 onto a main with this change merged.
- Mutants on lines round 3 did not touch, beyond the regression sample
  (round 1 killed 36 at 2574039; round 2 killed 18 at 3068ab6).

## Live check
not needed: no rule-1 path, no `.claude/settings.json`, and no Not-checked
item that only a live run can show.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/18-intent-dependencies` at 6199bba; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 298 tests, 0 fail; "All
  checks passed!"; "152 files already formatted"; mypy "Success: no issues
  found in 27 source files"; "624 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "19 file(s), 696
  line(s)". Matches.
- **Coordinator, re-run:** N08 SURVIVED (fail 0); M27b, N07, N10-direct,
  N10-further each KILLED (fail 1). Matches the reviewer and the
  implementer.

**Reviewer, verified** (in `C:/Users/eric/src/product-advice-agent-wt/18-intent-dependencies` at 6199bba; `git status --short` clean before and after):
- `npm run verify` → exit 0; kit "tests 298 / pass 298 / fail 0"; ruff
  "All checks passed!"; "152 files already formatted"; mypy "Success: no
  issues found in 27 source files"; "624 passed". Matches the
  implementer's 298 and 624.
- `npm run check:intent` → exit 0, PASS, "19 file(s), 696 line(s)".
- The 10 mutants above, one at a time, each against the full kit suite.
- The round-3 diff `e08b7b7..HEAD`, read in full: rework commit 3041c48
  touches only the three test files (+14 lines).
- Rebase: merge-base = main = 1255175; no `intents/21-*` in
  `main...HEAD`; `3068ab6` vs `e08b7b7` differs only in §18 review.md.
- Sampling via `sdlc:scan` (above).
- Nothing pushed: main is at 1255175 and `git ls-remote origin 'refs/heads/feat/18*'` returns nothing.

**Taken on trust:** none of the claims; each was re-run. Round 2's
documentation pass (pass 7) is carried over because round 3 changes no docs.
# Round 2 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 3068ab6dd572524e2c3cb312652050271226f16e
- round: 2
- sampled: no
- run: auto
- live-check: not-needed

Tier: Reviewed, by the path table (`scripts/intent-check-lib.mjs`,
`scripts/check-intent.mjs`, `.claude/skills/**`).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 18` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Every fix is mechanical; no "Needs decision:" finding. Without F9 and F10
the verdict would be escalate (Reviewed tier).

### Resolution of round 1
| # | Finding | Resolution |
| --- | --- | --- |
| F1 HIGH | B3 unproven at queue and spawn | resolved: M26 killed by queue.test "B3: a merged: on the blocker branch copy does not clear it; main decides"; M41 by spawn-intent.test "B3: …" |
| F2 MEDIUM | spawn and a broken record | resolved: M42, M45 killed by spawn-intent.test "refuses a non-digit id and the intents own id as a broken record" |
| F3 MEDIUM | branch-only blocker at the seams | partly: M38 (check-intent.test), M39 (spawn-intent.test), M27a (`queue.mjs:98`, text) killed; M27b (`queue.mjs:96`, `--json`) survives, F9 |
| F4 MEDIUM | B1 note | resolved: `blockers-lib.mjs:28` produces it, `intent-check-lib.mjs:248` pushes it; N01-N04 killed |
| F5 LOW | Progress prose | resolved: 624 and 296 reproduce; the divergence (2) wording matches `npm run queue` today |
| F6 LOW | M04, M10, M12, spawn file order | resolved: M04, M10, M12 killed; spawn names the lowest open blocker (`spawn-intent.mjs:117`, consistent with B8; B6 does not fix which), N05, N06 killed; lexical order survives, F10 |
| F7 LOW | auto skill broken-record list | resolved: `.claude/skills/auto/SKILL.md:154` names the non-digit id |
| F8 LOW | CLAUDE.md, sdlc.md stop lists | out of scope, a follow-up adjustment |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (round-2 diff `255379d..HEAD`: spec.md, intent.md unchanged; plan.md only below Progress) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (B1 note produced; spawn's lowest open blocker agrees with B8) |
| 4 | Tests prove the behaviour | findings (3): 22 mutants, 18 killed, 4 survived (M27b, N07, N08, N10) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (kit 296, pytest 624) |
| 7 | Documentation | pass (`intents/README.md:137-150` still matches) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 18, feature)
  note:  19 file(s), 682 line(s) changed outside intents/.
```

### Findings
- **F9 MEDIUM** `scripts/queue.mjs:96` (round-1 F3, residual): B5's `--json`
  `blocked_by_open` for a branch-only blocker is unproven at the seam; M27b
  (`queueData(collectEntries(), {})`) survives, giving `blocked_by_open: []`
  and a false "on no branch" problem. **Needs rework:** in queue.test "F3:
  a blocker that exists only on a branch is open, not an unknown id", also
  assert `JSON.parse(queue('--json').stdout)`: the in-flight §72 has
  `blocked_by_open` `[73]` and `problems` holds no "on no branch" entry.
- **F10 LOW** `scripts/blockers-lib.mjs:60`, `scripts/spawn-intent.mjs:117`:
  "ascending" and "lowest" are proven only for ids of one width. N10
  (`openChain` direct `.sort()`, lexical: `§13, §9`) and N07 (spawn's
  lexical sort names §13 before §9) survive. **Needs rework:** ids of
  different widths in the openChain ordering test (direct `['13', '9']` →
  `['9', '13']`) and in spawn's "names the lowest open blocker" test
  (blockers 9 and 13 → §9).
- **F11 LOW** (worth a look) `scripts/spawn-intent.mjs:119`: N08 survives;
  which of several unknown blockers is named is untested, and the spec does
  not fix it. No rework required.

**Mutants** (22, full kit suite each; backup and restore by copy): KILLED
M26, M27a, M38, M39, M41, M42, M45, M04, M10, M12, N01-N06, N09, N11.
SURVIVED M27b (`queue.mjs:96`), N07 (`spawn-intent.mjs:117`), N08
(`spawn-intent.mjs:119`), N10 (`blockers-lib.mjs:60`). The rework must kill
M27b, N07 and N10; N08 may stay.

### Not checked
- A real `/auto` run reaching step 4 on a blocked intent (B8 is prose).
- `npm run queue -- --json` on the live repo with a branch-only blocker.
- Rebasing feat/14 and feat/17 onto a main with this change merged.
- Mutants on lines the round-2 diff did not touch (round 1 killed 36 at
  2574039).

### Live check
not needed: no rule-1 path, no `.claude/settings.json`, and no Not-checked
item that only a live run can show.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/18-intent-dependencies` at 3068ab6; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 296 tests, 0 fail; "All
  checks passed!"; "151 files already formatted"; mypy "Success: no issues
  found in 27 source files"; "624 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "19 file(s), 682
  line(s)". Matches.
- **Coordinator, re-run:** survivors M27b, N07, N08, N10 each SURVIVED (fail
  0). Matches the reviewer.
- **Coordinator, re-run:** the kills the rework claims: M26, M27a, M38, M39,
  M41, M42, M45, M04, M10, M12, N03 each KILLED (fail 1), N01 KILLED (fail
  2). Matches the reviewer and the implementer.

**Reviewer, verified:** verify, check:intent, sampling; the round-2 diff
read in full; 22 mutants; `npm run queue` on the branch shows no blocked
lines (divergence 2); nothing pushed (main at 1687047, no remote feat/18).

**Taken on trust:** that spawn's lowest-blocker choice was meant as the B8
alignment (consistent with the spec either way).
# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 25740393d13ab2421fa6ff502b47179341981763
- round: 1
- sampled: no
- run: auto
- live-check: not-needed

Tier: Reviewed, by the path table (`scripts/intent-check-lib.mjs`,
`scripts/check-intent.mjs`, `.claude/skills/**`); `review_tier` is empty.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 18` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Every finding needing rework is mechanical (tests, one note path the plan
fixes, Progress prose). No "Needs decision:" finding.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (divergences a-d weighed below, all acceptable) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): B1 "noted" not implemented |
| 4 | Tests prove the behaviour | findings (4): 47 mutants, 36 killed, 11 survived |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1) |
| 7 | Documentation | findings (1, worth a look) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 18, feature)
  note:  18 file(s), 581 line(s) changed outside intents/.
```

### Findings
- **F1 HIGH** `scripts/queue.mjs:75`, `scripts/session-io.mjs:99`: B3 ("only
  `main`'s `merged:` counts") is unproven at two of three I/O seams. M26
  (queue.mjs `mainMerged: isMerged(picked.metadata)`) and M41
  (`readBlockers` returns the blocker's branch metadata first) survive; the
  plan's Risks name this. **Needs rework:** a `spawn-intent.test.mjs` case
  where the blocker's branch says `merged: x` and `main`'s `merged:` is
  empty, so spawn still refuses; a `queue.test.mjs` temp-repo case where
  the branch copy says merged and main doesn't, so the line still reads
  `blocked by §n`.
- **F2 MEDIUM** `scripts/spawn-intent.mjs:121`, `scripts/session-io.mjs:112`:
  B6 "a broken record also refuses" is proven only for an unknown id. M45
  (`if (problems.length)` → `if (false)`) and M42 (`readBlockers` returns
  `problems: []`) survive. **Needs rework:** a spawn temp-repo test with
  `blocked_by: - x why` (and one with the intent's own id): exit 1, the
  "broken blocked_by record" message, no worktree or branch.
- **F3 MEDIUM** `scripts/check-intent.mjs:111`, `scripts/session-io.mjs:106`,
  `scripts/queue.mjs:96,98`: a blocker that exists only on a local branch is
  untested at the I/O seams. M38 (`onSomeBranch` always false), M39
  (`readBlockers` `exists` always false) and M27 (queue.mjs drops
  `knownIds`) survive; such a blocker is then reported "on no branch"
  instead of open (spawn and check:intent still refuse, with the wrong
  message; queue shows a false Problems line). **Needs rework:** one e2e
  case each in check-intent, spawn and queue where the blocker lives only
  on `feat/<n>-…`: the "not merged" / "blocked by" message, no "on no
  branch".
- **F4 MEDIUM** `scripts/blockers-lib.mjs:12-30`, `scripts/intent-check-lib.mjs:246`:
  B1 "an item without a reason is valid but noted"; no note is produced.
  Plan subtask 1 ("missing reason as a note") and the Tests table
  (plan.md:95, "`- 13` → item + note") fix the shape. **Needs rework:**
  `parseBlockers` returns `notes` (e.g. `blocked_by item "13": no reason
  given.`), `checkChange` pushes them into its `notes`, asserted in the
  blockers-lib and intent-check-lib tests (a mutant dropping the note must
  die).
- **F5 LOW** `intents/18-intent-dependencies/plan.md:135-136` (Progress):
  "pytest unchanged (608)" is 624 after the rebase; divergence (2) "the AC6
  queue lines show only after merge" is wrong (§13 is merged, so after this
  merge the queue shows only `§15 … blocked by §14`). **Needs rework:**
  correct both sentences.
- **F6 LOW** (worth a look) `scripts/blockers-lib.mjs:26,58`,
  `scripts/spawn-intent.mjs:117`: M04 (`013` not normalised), M10 (direct
  duplicates kept: `§13, §13`), M12 (direct list unsorted) survive; spawn
  names the first open blocker in file order, B8 asks for the lowest.
  Add a duplicate-id and an unordered-items case to the openChain test.
- **F7 LOW** (worth a look) `.claude/skills/auto/SKILL.md:153`: the
  broken-record list omits the non-digit id that B4 and README name.
- **F8 LOW** (worth a look) `CLAUDE.md:65`, `sdlc.md:118`: the `/auto` stop
  lists lack the blocked_by stop. Outside the intent's file scope; a
  follow-up adjustment.
- Divergences, all acceptable: (a) the extra stop reason `blocked_by record
  broken` completes B8; (b) AC6 proved by `blockers-backfill.test.mjs`,
  which AC6 allows; (c) `--base` kept for owner-requested stacked branches;
  (d) the additive top-level `problems` in `--json`.

**Mutants** (47, full kit suite each; backup and restore by copy): 36
KILLED, among them M01-M03, M05-M09, M11, M13-M25, M28-M37, M40, M43,
M44, M46, M47. SURVIVED (11): M04, M10, M12 (`blockers-lib.mjs`), M26, M27
(`queue.mjs`), M38 (`check-intent.mjs`), M39, M41, M42 (`session-io.mjs`),
M45 (`spawn-intent.mjs`). The rework must kill M26, M41, M42, M45, M27,
M38, M39 and a new missing-reason-note mutant.

### Not checked
- A real `/auto` run reaching step 4 on a blocked intent (B8 is prose).
- `npm run queue -- --json` on the live repo with a branch-only blocker.
- Rebasing feat/14 and feat/17 onto a post-merge main (inferred
  conflict-free, not tried).
- `findCycles` is exponential on dense graphs (about 22 ms at 18
  fully-connected nodes; irrelevant today).
- Ids with leading zeros end to end; check:intent's working-tree mode with
  blockers.

### Live check
not needed: no rule-1 path, no `.claude/settings.json`, and no Not-checked
item that only a live run can show. The reviewer ran queue and a dry spawn
in a temp clone (below).

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/18-intent-dependencies` at 2574039; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 286 tests, 0 fail; "All
  checks passed!"; "150 files already formatted"; mypy "Success: no issues
  found in 27 source files"; "624 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "18 file(s), 581
  line(s)". Matches.
- **Coordinator, re-run:** M26, M27, M38, M39, M41, M42, M45, M04, M10, M12
  each SURVIVED the kit suite (fail 0). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, sampling; main's kit suite
255 → 286 via `git archive`; 47 mutants; the B10 backfill diff on §14, §15
and §17 (only the spec's items appended, LF); in a temp clone with the
branch merged into main: queue shows `§15 … blocked by §14`, `spawn 15`
refuses with no worktree or branch, `check-intent feat/14-catalogue-500`
PASS; skills' hunks below the frontmatter; nothing pushed.

**Taken on trust:** that the implementer's `isMerged` bug was found by
mutation (behaviour confirmed by M05 killed).
