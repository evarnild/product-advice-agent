<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §18 review — Intent dependencies

verdict: rework
tier: reviewed
reviewed-commit: 25740393d13ab2421fa6ff502b47179341981763
round: 1
sampled: no
run: auto
live-check: not-needed

Tier: Reviewed, by the path table (`scripts/intent-check-lib.mjs`,
`scripts/check-intent.mjs`, `.claude/skills/**`); `review_tier` is empty.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 18` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Every finding needing rework is mechanical (tests, one note path the plan
fixes, Progress prose). No "Needs decision:" finding.

## Passes
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

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 18, feature)
  note:  18 file(s), 581 line(s) changed outside intents/.
```

## Findings
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

## Not checked
- A real `/auto` run reaching step 4 on a blocked intent (B8 is prose).
- `npm run queue -- --json` on the live repo with a branch-only blocker.
- Rebasing feat/14 and feat/17 onto a post-merge main (inferred
  conflict-free, not tried).
- `findCycles` is exponential on dense graphs (about 22 ms at 18
  fully-connected nodes; irrelevant today).
- Ids with leading zeros end to end; check:intent's working-tree mode with
  blockers.

## Live check
not needed: no rule-1 path, no `.claude/settings.json`, and no Not-checked
item that only a live run can show. The reviewer ran queue and a dry spawn
in a temp clone (below).

## Verified myself vs. taken on trust

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
