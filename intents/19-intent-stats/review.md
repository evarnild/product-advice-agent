<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §19 review — Time, tokens and owner wait per intent and phase

verdict: rework
tier: reviewed
reviewed-commit: 6b4fba77e01459946f7ab42bcb136da16920b875
round: 5
sampled: no
run: manual
live-check: owed

Tier: Reviewed, never lowered; set by the path table
(`scripts/session-event.mjs`, `.claude/skills/**`, `scripts/ship.mjs` in the
branch diff) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due manual --exclude 19` →
"sample-due manual: nth attested manual change = 1, every 5, sampled: no".

Why this round: the round-4 rework (0d0b3a7 code and tests; 6b4fba7
Progress) applies the owner's "19 1b 2a" (F1 option b, F2 option a).

Scope: `git diff 727e28d..HEAD`: `scripts/stats-lib.mjs` (+12/−9 code),
`scripts/stats-lib.test.mjs` (one test renamed and strengthened, one added,
one assertion added), `plan.md` (Progress, below the marker),
`review.md` (round 4, abc275e). spec.md, intent.md and metadata.yml
unchanged; plan.md has 0 removed lines, all additions after `## Progress`.

Verdict: rework. The rework does what the owner decided, and the code is
right on every probe; one MEDIUM test gap needs a mechanical fix (F1).
Without it, escalate.

## Resolution of round 4
| Item | Decision | Status at 6b4fba7 | Evidence |
| --- | --- | --- | --- |
| F1 agent work double-counted across phases | owner (b): join per intent, an overlap to the earlier-started run's phase | **resolved** | `stats-lib.mjs:397-421`: `agentWork` per intent id, runs sorted by start, each books only the part beyond `covered`. Probe (implement 7.5–8.5 h, review 8–9 h): total 1.5 h, build 1 h, review 0.5 h. Test `stats-lib.test.mjs:524`. Mutant F1 killed |
| F2 a no-commit intent's turn on two lines | owner (a): coord work to the intent's unphased bucket | **resolved** | `stats-lib.mjs:387` `if (a.kind === 'intent')`. Probe: rows [7, 99], §99 unphased coord work 1 h, unattributed 0. Test `:515`. Mutant F2 killed |
| F3 mutant F6, the `--all` total row | Needs rework | **resolved** | `stats-lib.test.mjs:558` asserts `/^total +10h00m +1h00m +1h00m /m`; F6 (`:567`) killed by "prints and serialises both columns" |
| F4 IO1 (`--topo-order`) | worth a look | unchanged (not requested) | IO1 still survives (near-equivalent) |
| F5 docs one-liners | worth a look | unchanged (not requested) | `CLAUDE.md:27` still "elapsed time, owner wait and tokens per phase" |
| Nit F7 cell width | follow-up | unchanged | F7 (`:485`) still survives (cosmetic) |
| Live check (AC7) | — | recorded at 3c8337f, before this rework | see Live check |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: exactly F1 (b), F2 (a), F3; F4, F5 untouched as stated; spec.md and plan.md unchanged above Progress |
| 2 | Type check | pass (PASS) |
| 3 | Behaviour against the spec | pass: B5a "joined, never counted twice" holds (per-phase sum equals the union on 6 synthetic shapes, including reversed input order and a contained run); "attributed to the intent as in B4" holds for a no-commit intent |
| 4 | Tests prove the behaviour | findings (1): 15 mutants, 9 killed, 6 survived; N2, N5, N6 real gaps (F1); N3 a tie-break (F2); IO1, F7 carried |
| 5 | Conventions | pass: kit-only, pure, no model or network, synthetic fixtures |
| 6 | Numbers in prose | pass: Progress figures reproduce; `stats -- 19` agent work 76 min (1h16m) against Progress 1h15m (rounding plus a still-running tagged run) |
| 7 | Documentation | pass; F5 carried |
| 8 | Guardrails and hygiene | pass: no dependency, no secret, synthetic fixtures; no prompt or response text read or printed (real-data runs reduced to minute totals inside a script) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 19, feature)
  note:  25 file(s), 1860 line(s) changed outside intents/.
```

## Findings
- **F1 MEDIUM** `scripts/stats-lib.mjs:416-419`, `scripts/stats-lib.test.mjs:524-538`:
  no test pins the run ordering or contained runs, though real data depends
  on both: `stats-io.mjs:62` lists `agent-*.jsonl` in directory order
  (random agent ids), not start order. Probes on mutated copies outside the
  repo:
  - N2 (no `sort`): the reviewer's case in reverse order gives total 1 h
    against a union of 1.5 h (review 1 h, build 0);
  - N5 (drop `if (part > 0)`): implement 7–10, review 8–9, rework 9.5–11
    gives build 3 h, review 0, total 3 h (correct: build 3 h, review 1 h,
    total 4 h): a negative part is booked to review;
  - N6 (`covered = to`): the same runs give review 1.5 h, total 4.5 h.

  All three survive the full kit suite (every fixture is in start order,
  none has a contained run). The code is right on every probe: fragility,
  not wrong output. **Needs rework:** add two cases to the B5a test at
  `:524`: (i) `[agentRun('§7 review round 1', 8, 9), agentRun('§7 implement',
  7.5, 8.5)]` → build 1 h, review 0.5 h, total 1.5 h (kills N2); (ii)
  `[agentRun('§7 implement', 7, 10), agentRun('§7 review round 1', 8, 9),
  agentRun('§7 rework', 9.5, 11)]` → build 3 h, review 1 h, total 4 h (kills
  N5, N6).
- **F2 LOW** `scripts/stats-lib.mjs:416`: the tie-break `|| x.span[1] -
  y.span[1]` (N3) is pinned by no test, and the owner's rule ("the
  earlier-started run's phase") doesn't cover equal starts; today the
  shorter run books first (review 8–9 with implement 8–10 → build 1 h,
  review 1 h); without it, directory order decides (build 2 h). Equal starts
  to the millisecond are unlikely. Worth a look: pin it, or leave it.
- Carried, worth a look: round-4 F4 (IO1, `stats-io.mjs:97`), F5
  (`CLAUDE.md:27`, `README.md:276`, `sdlc.md:151`); nit F7
  (`stats-lib.mjs:485`), the owner's display follow-up.

**Mutants** (full kit suite each; exact-string replace, asserted unique and
applied; backed up and restored by copy):

| # | Line | Mutation | Result | Killing test |
| --- | --- | --- | --- | --- |
| F1 | stats-lib.mjs:414-421 | back to a per-(intent, phase) union | KILLED | "joins agent work per intent: an overlap goes to the earlier run's phase…" |
| F2 | :387 | `&& byIntent.has(a.id)` restored | KILLED | "books a turn for an intent with no commits to that intent's unphased bucket…" |
| F6 | :567 | `--all` total with the old 4 keys | KILLED | "prints and serialises both columns" |
| IO1 | stats-io.mjs:97 | drop `--topo-order` | SURVIVED (near-equivalent; round-4 F4) | — |
| F7 | :485 | cell width 11 → 10 | SURVIVED (cosmetic) | — |
| N1 | :415 | `covered = Infinity` | KILLED | "joins…", "books agent work by tag…", "prints and serialises both columns" |
| N2 | :416 | no `sort` | **SURVIVED** (F1) | — |
| N3 | :416 | no end tie-break | SURVIVED (F2) | — |
| N4 | :417 | `part = to - from` | KILLED | "joins…", "books agent work by tag…" |
| N5 | :418 | drop `if (part > 0)` | **SURVIVED** (F1) | — |
| N6 | :419 | `covered = to` | **SURVIVED** (F1) | — |
| N7 | :418 | always book to `build` | KILLED | "joins…", "books agent work by tag…" |
| N8 | :404 | run's phase always `review` | KILLED | "joins…", "books agent work by tag…", "prints and serialises…" |
| N11 | :403 | a new array per run | KILLED | "joins…", "books agent work by tag…" |

The rework must kill N2 (`:416`), N5 (`:418`), N6 (`:419`). Not run:
comment-only lines (`:388`, `:397`, `:412-413`); `:390` (unchanged, killed
in round 4 as W6); `covered = -Infinity` → `0` (equivalent, timestamps > 0).

## Not checked
- Whether §14's real figures are right: the rework changes them (Live
  check); only the owner's memory can say whether a §14 review run
  overlapped an implement run by about half an hour.
- Equal-start tie-breaking on real transcripts (F2).
- `owes-run` (absent on this branch, which predates §17); main's
  `EVAL_PATHS` applied by hand.
- The transcript format's stability (as in rounds 1–4).
- The display nits the owner left for a follow-up.

## Live check
- owed: rule 3 (AC7, stats over real transcripts). Rules 1 and 2 don't
  apply.
- recorded: `live_checked: 2026-11-21 by-agent` (3c8337f), on the code
  before this rework.
- **A re-check is owed before the merge** (`check:intent` doesn't enforce
  it, since the date is set): the rework changes how agent work is booked,
  and on real data that changes a figure. §14 agent work drops from 98 min
  to 66 min (review 43 → 10 min; build 56 min unchanged); §17 and §19, the
  intents the recorded check covered, are unchanged; no other intent's coord
  or agent work changed (22 compared, old code against new).
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats`: `npm
     run stats -- 19`, then `npm run stats -- 14`.
  2. §19: compare the coord work and agent work columns with what the
     recorded check saw.
  3. §14: check against your memory that a review (or rework) run
     overlapped its implement run, so the overlap now counts once, in build.
- you should see: §19 totals coord work ~11m, agent work ~1h16m (build ~20m,
  review ~56m); §14 totals coord work ~18m, agent work ~1h06m (build ~56m,
  review ~10m), the phase agent-work cells summing to the total. If it
  passes, keep `live_checked` or re-date it at your word; if §14 looks
  wrong, clear it and send the change back to rework.

## Eval run
not owed: `owes-run` is absent on this branch, so main's `EVAL_PATHS` (10
entries, `git show main:src/advisor/evals/baseline.py`) were applied by hand
to `git diff --name-only main...HEAD` (merge-base b2e2815); nothing matches
(kit scripts, fixtures, skills, docs, `package.json`, intents).

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 6b4fba7; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 379", "fail 0";
  "All checks passed!"; "157 files already formatted"; mypy "Success: no
  issues found in 28 source files"; "658 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "25 file(s), 1860
  line(s)". Matches.
- **Coordinator, re-run:** the kills the rework claims: F2 and F6 KILLED
  (full kit suite). F1 (a multi-line revert) not re-run by me; the reviewer
  and the implementer both report it killed.
- **Coordinator, re-run:** survivors N2, N3, N5, N6, IO1, F7 each SURVIVED
  the full kit suite. Matches the reviewer.

**Reviewer, verified:** verify (kit 379, pytest 658), check:intent,
sampling; spec, intent and metadata unchanged and plan.md additions below
Progress; main untouched, no remote branch; synthetic probes against the
real `stats-lib.mjs` (six shapes summing to the union; the F2 case;
`formatAll` with no NaN); mutated copies outside the repo for N2, N3, N5,
N6; the 15 mutants; real data numbers only (`node scripts/stats.mjs 19
--json`, `14 --json`, `--all --json`, reduced to minute totals in a script,
also with the 727e28d stats scripts): §19 coord 11, agent 76 (build 20,
review 56) both versions; §14 agent work 98 → 66. No prompt or response text
read, printed or kept.

**Taken on trust:** the owner's "19 1b 2a" as quoted in Progress; the
content of the recorded live check (3c8337f); round 4's results for
untouched lines.
# Round 4 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 727e28db7b469b40132dd217f15c3cf80caa4e50
- round: 4
- sampled: no
- run: manual
- live-check: owed

Tier: Reviewed, never lowered; set by the path table
(`scripts/session-event.mjs`, `.claude/skills/**`, `scripts/ship.mjs` in the
branch diff) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due manual --exclude 19` →
"sample-due manual: nth attested manual change = 1, every 5, sampled: no".

Why this round: `/auto 19` was out of rounds after round 3 (escalate at
1ca5315). The owner's live check found defects, fixed in another session
(3ba38c7, 1870007) under a spec amendment the owner accepted (cf9f831,
0c175dd); `live_checked` followed (3c8337f). `npm run ship -- 19 --dry-run`
stopped on these unreviewed changes. The owner asked for `/review 19`.

Verdict: rework. One LOW finding needs a mechanical fix (F6); two LOW
findings are spec deviations that need the owner's decision. Without them,
escalate.

Scope: `git diff 1ca5315..727e28d`: `scripts/stats-io.mjs` (1 line),
`scripts/stats-lib.mjs` (+75/−18), `scripts/stats-lib.test.mjs` (+85),
`scripts/stats.test.mjs` (+11), `spec.md` (the 2026-11-18 amendment: W1–W3,
B5a, B6, B8, AC4a, AC7), `plan.md` (subtask 7, two Progress entries),
metadata and review.md, against the amended spec and plan subtask 7.

### Resolution of round 3
| Item | Status at 727e28d | Evidence |
| --- | --- | --- |
| F2g gate-side `clipToLife` (documented guard) | holds | comment still at `stats-lib.mjs:419`; code unchanged |
| F8m `-m` (equivalent mutant) | holds | the `statsCutover` line is not in this diff; the only stats-io hunk is :93–97 |
| Carried LOWs (live-check milestone wording, F3 owner-wait stops, I2, C5, C6, R1) | unchanged, as decided | — |
| Live check owed (AC7) | recorded: `live_checked: 2026-11-21 by-agent` (3c8337f) | see Live check |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: plan subtask 7 plus the same-second fix (3ba38c7), which amended AC4a covers; amendment proposed cf9f831, accepted 0c175dd, code 1870007; edits above Progress come under the owner's acceptance |
| 2 | Type check | pass (PASS) |
| 3 | Behaviour against the spec | findings (2): agent work counted twice across phases; work for an intent with no commits |
| 4 | Tests prove the behaviour | findings (1): F6. 25 mutants: 22 killed, 3 survived (F6 a real gap; IO1 near-equivalent, F7 cosmetic) |
| 5 | Conventions | pass: kit-only and pure, no model or network, synthetic fixtures, throwaway repo under tmpdir |
| 6 | Numbers in prose | pass: kit 378, pytest 658; 369 + 9 = 378; the "7 200 000 ms" before the fix; §13 2m coord work, 0 agent work, 40m gate wait reproduced. §16–§19 agent work reads 12m/46m/1h38m/1h16m against Progress 11m/45m/1h37m/1h15m (rounding plus later runs) |
| 7 | Documentation | pass; one LOW worth a look (CLAUDE.md:27) |
| 8 | Guardrails and hygiene | pass: no new dependency, no secret, synthetic fixtures, no prompt or response text read or printed |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 19, feature)
  note:  25 file(s), 1839 line(s) changed outside intents/.
```

### Findings
- **F1 LOW** `scripts/stats-lib.mjs:396-412`: agent work is joined per
  (intent, phase), not per intent. Overlapping `§N implement` and `§N review`
  runs count the overlap once in build and again in review, so totals count
  it twice. Spec B5a: "the runs of one intent are joined, never counted
  twice"; plan subtask 7: "the union … in the tag's phase". Synthetic probe:
  implement 7.5–8.5 h plus review 8–9 h gives `totals.agentWorkMs` 2 h
  against a union of 1.5 h. Rare (runs are sequential). **Needs decision:**
  (a) keep the per-phase union and amend B5a's wording, or (b) join per
  intent and book each overlap to one phase.
- **F2 LOW** `scripts/stats-lib.mjs:387,391` against `:374`: a turn
  attributed by `skillId` to an intent with no commits yet books its coord
  work to `unattributed` but its coordinator tokens to an intent row
  (`phase(id, UNPHASED)`). Probe: rows `[7, 99]`, §99 coord work 0, the
  turn's hour on the unattributed line, so one turn lands on two lines. B5a:
  the turn is "attributed to the intent as in B4"; Progress and the test
  "books a turn for an intent with no commits as unattributed" deliberately
  do otherwise. **Needs decision:** (a) book the work to the intent's
  unphased bucket as the tokens are, (b) send the tokens to unattributed
  too, or (c) keep it and amend B5a.
- **F3 LOW** `scripts/stats-lib.test.mjs:546`, `scripts/stats-lib.mjs:558`:
  mutant F6 survives; if `formatAll`'s total row keeps the old 4 keys, the
  coord and agent work columns print `NaNhNaNm` and no test fails. **Needs
  rework:** in "prints and serialises both columns", add
  `expect(formatAll(s)).toMatch(/^total +10h00m +1h00m +1h00m /m);` (or the
  suite's equivalent assertion).
- **F4 LOW** `scripts/stats-io.mjs:97`: mutant IO1 (drop `--topo-order`)
  survives; on linear history git's default walk already lists a child
  before its parent, so `--reverse` alone fixes the same-second case;
  `--topo-order` only guards clock skew. Worth a look (near-equivalent).
- **F5 LOW** `CLAUDE.md:27` (and `README.md:276`, `sdlc.md:151`): the stats
  one-liners don't mention coord work or agent work. Worth a look.
- Nit: `stats-lib.mjs:476` cell width is pinned by no test (F7); the owner's
  "misaligned row" follow-up covers it.

**Mutants** (full kit suite each; exact-string replace, asserted applied,
restored by copy):

| # | Line | Mutation | Result | Killing test |
| --- | --- | --- | --- | --- |
| IO1 | stats-io.mjs:97 | drop `--topo-order` | SURVIVED (near-equivalent) | — |
| IO2 | stats-io.mjs:97 | drop `--reverse` | KILLED | "keeps commit order for commits in the same second…" |
| S1 | stats-lib.mjs:204 | `stopped: true` at start | KILLED | "closes a turn at the next prompt…"; "caps a turn with no Stop at 2 h…" |
| S2 | :209 | drop `turn.stopped = true` | KILLED | same two |
| W1 | :384 | open turn ends at `t.start` | KILLED | "caps a turn with no Stop at 2 h…" |
| W2 | :385 | no 2 h cap | KILLED | same |
| W3 | :385 | always capped | KILLED | same (the 3 h case) |
| W4 | :387 | drop `byIntent.has` | KILLED | "books a turn for an intent with no commits as unattributed" |
| W5 | :388 | no `coordSpans.set` | KILLED | "takes the intent's coordinator turns out of a gate wait… (W2)"; "counts gate wait and in-session wait separately…" |
| W6 | :389 | `+= len` (no share) | KILLED | "books coord work from attributed turns, spread…"; "prints and serialises both columns" |
| W8 | :390 | shared `+= 0` | KILLED | "shows shared and unattributed turn time on those lines…" |
| W9 | :391 | drop unattributed work | KILLED | same; "books a turn for an intent with no commits…" |
| A1 | :412 | no `unionMs` | KILLED | "books agent work by tag… joining overlapping runs…" |
| A2 | :402 | key per intent only | KILLED | same |
| A3 | :404 | no span push | KILLED | same; "prints and serialises both columns" |
| G1 | :417 | coord spans not in `mine` | KILLED | the two gate-wait tests |
| U1 | :354 | unattributed without `workMs: 0` | KILLED | "shows shared and unattributed…"; "prints and serialises both columns" |
| U2 | :357 | shared without `workMs: 0` | KILLED | "shows shared and unattributed…" |
| F1m | :468 | drop the coord work column | KILLED | "books coord work…"; "prints and serialises both columns" |
| F2m | :481 | `totalsOf` with the old 4 keys | KILLED | four working-time tests |
| F3m | :534 | no side-line coord work | KILLED | "shows shared and unattributed…" |
| F4m | :534 | side-line coord work always shown | KILLED | "prints the phases, tokens per model…" (stats.test.mjs) |
| F5m | :573 | JSON without `workMs` | KILLED | "prints and serialises both columns" |
| F6 | :558 | `--all` total with the old 4 keys | SURVIVED (F3: Needs rework) | — |
| F7 | :476 | cell width 10 instead of 11 | SURVIVED (cosmetic) | — |

The rework must kill F6. Not run: the `firstTs !== null` half of `:401`
(equivalent), `:412` `+=` → `=` (keys unique, equivalent), comment-only
lines (:38, :96, :380–382, :419).

### Not checked
- Whether 1870007's code was written before the amendment was accepted: the
  commits are in order, four minutes apart; git can't tell when code was
  written.
- Agent work on real transcripts with overlapping implement and review runs
  of one intent (probed on synthetic data only).
- The display nits the owner left for a follow-up (shared blocks, a
  misaligned row, the `<synthetic>` row, uncounted review time): the owner's
  recorded choice, not assessed as findings.
- `uv run advisor-analysis owes-run --base main`: the branch predates §17 and
  has no `owes-run` (exit 2); main's `EVAL_PATHS` applied by hand instead.
- The transcript format's stability (as in rounds 1–3).

### Live check
- owed: rule 3 (AC7: stats over real transcripts and the hook in real
  sessions). Already **recorded**: `live_checked: 2026-11-21 by-agent`
  (3c8337f).
- Ordering: 3c8337f (2026-11-21 09:14) descends from 1870007 (2026-11-18
  14:06); only `metadata.yml` changes in 3c8337f and 727e28d. The recorded
  check ran on the code reviewed here (the metadata note: `npm run stats --
  17 / 19` in session). Rules 1 and 2 don't apply.
- The post-round-3 code (`git diff 1ca5315..727e28d -- scripts/`, ~170
  lines) still needs the owner's **diff read** (Reviewed tier), not another
  live check, unless a decision on F1 or F2 changes how agent or coord work
  is booked: then re-run `npm run stats -- 19` in the worktree and compare
  the coord work and agent work columns with the previous figures.

### Eval run
not owed: `owes-run` is absent on this branch, so main's `EVAL_PATHS`
(`src/advisor/evals/baseline.py` at main) were applied by hand to `git diff
--name-only main...HEAD` (merge-base b2e2815); nothing matches (kit
scripts, skills, docs and intents only).

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 727e28d; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → "All checks passed!", "157
  files already formatted", mypy "Success: no issues found in 28 source
  files", "658 passed"; `npm run test:kit` → "tests 378, pass 378, fail 0".
  Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "25 file(s), 1839
  line(s)". Matches.
- **Coordinator, re-run:** survivors F6 (`stats-lib.mjs:558`), IO1
  (`stats-io.mjs:97`), F7 (`stats-lib.mjs:476`) each SURVIVED the full kit
  suite. Matches the reviewer.

**Reviewer, verified:** verify (kit 378, pytest 658), check:intent,
sampling, `owes-run` (absent; checked by hand), the 25 mutants above, two
synthetic probes against the real `stats-lib.mjs` (the double count and the
no-commit split), one numbers-only `node scripts/stats.mjs --all --json`
reduced to minute totals (output deleted; no prompt or response text read or
printed), the round-4 diff read in full with the amendment and subtask 7,
commit order; no remote branch for feat/19.

**Taken on trust:** the owner's acceptance of the amendment and the content
of the live check, as recorded in commits and metadata; round 3's results
for code this round did not change.
# Round 3 (history)


- verdict: escalate
- tier: reviewed
- reviewed-commit: 1ca5315424f554da63118c924309942a89943ed4
- round: 3
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed (the paths `scripts/session-event.mjs`, `.claude/skills/**` and `scripts/ship.mjs`; `review_tier: reviewed`). The owner reads the diff.

Verdict: escalate. The reviewer proposed `attest`; no finding needs rework or a
decision, but the tier is Reviewed, so the verdict is `escalate` (the
owner's diff read), as in this intent's earlier rounds and REVIEW-POLICY.

Round 3 diff (440321a..1ca5315): `scripts/stats-io.mjs` (1 line), `scripts/stats-lib.mjs` (1 comment line), `scripts/stats-lib.test.mjs` (+3 tests or assertions), `scripts/stats.test.mjs` (+1 test), the plan.md Progress entry and `auto_round: 3`. spec.md is unchanged this round. plan.md is changed only by an appended Progress entry, below the marker.

### Resolution of round 2
| Finding | Resolution | Evidence |
| --- | --- | --- |
| F8 HIGH cutover took the author time of the commit that added the file | resolved: `stats-io.mjs:81` runs `git log main --first-parent -m --diff-filter=A --format=%at` | F8 (both flags dropped) and F8fp (`--first-parent` dropped) are KILLED by "uses the merge commit, not the author time of the commit that added the file" (stats.test.mjs, a throwaway repo with a `--no-ff` merge). F8m (`-m` dropped) survives as an equivalent mutant; see LOW below |
| F9 MEDIUM F2 test did not prove its name | resolved: renamed to "caps a gate wait that ends at the merge, and lets an unmerged intent wait up to now, none of it idle"; it asserts `idleMs` 17 h and 0; the gate-side clip is commented as a guard (`stats-lib.mjs:394`) | C1 KILLED; F2g SURVIVES as a documented guard, which is acceptable (see Findings) |
| F10 LOW intent with no commits | resolved: "books no wait to a skill id with no commits" | C4 KILLED |
| F11 LOW `blocked_by record broken` | resolved: a `gateGaps` case, `[1,5]` booked as gate wait | R3 KILLED |
| LOW live-check milestone vs `GATE_END` wording; F3 owner-wait stops; I2, C5, C6, R1 carried | unchanged, by choice and as decided | — |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (the round-3 diff is exactly the four round-2 fixes plus the Progress entry; spec.md untouched) |
| 2 | Type check | pass (FAIL only on the owed live check, which is the owner's to clear) |
| 3 | Behaviour against the spec | pass (B8 partial now uses the cutover at the merge commit; F4 author time kept) |
| 4 | Tests prove the behaviour | pass: 14 mutants run this round, 12 killed, 2 survive (F2g a documented guard, F8m equivalent) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (kit 369, pytest 658 reproduced; "366 before" matches round 2) |
| 7 | Documentation | pass (no doc change needed this round) |
| 8 | Guardrails and hygiene | pass (synthetic throwaway repo, removed in `finally`; no transcript or session-log text read) |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 19, feature)
  error: A live check is owed and not recorded. Do the steps in intents/19-intent-stats/review.md → ## Live check
- owed: rule 3 (the hook in real sessions; stats over real transcripts),
  AC7. Run it in the worktree **before** the merge (`ship` requires
  `live_checked` first); until §19 merges, `stats-lib.mjs` is not on
  `main`, so there is no cutover and every merged intent reads `partial`.
- steps, in `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats`:
  1. `npm run stats -- 13` (or the latest shipped intent): compare
     per-phase elapsed, gate wait, in-session wait and tokens (coordinator
     vs agents) with your memory of the run.
  2. `npm run stats -- --all`.
  3. Open a Claude Code session in this worktree (its hooks run this
     branch's `scripts/session-event.mjs`); type `/sessions`, `/spec 19`
     and a plain prompt such as `yes to 16`; then read the last lines of
     `.git/product-advice-agent-sessions.jsonl` in the main checkout.
- you should see: no prompt or response text anywhere; every merged
  intent marked `partial` (no cutover before the merge; after it, only
  those merged before §19's merge commit); `/sessions` →
  `"skill":"sessions"`, no `skillId`; `/spec 19` →
  `"skill":"spec","skillId":19`; the plain prompt with neither; no hook
  output or error.

### Verified myself vs. taken on trust
**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats` at 1ca5315; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 369 tests, 0 fail; "All
  checks passed!"; "157 files already formatted"; mypy "Success: no issues
  found in 28 source files"; "658 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "25 file(s), 1707 line(s)". Matches.
- **Coordinator, re-run:** F8, F8fp, C1, C4, R3 each KILLED by the test the
  reviewer names; F2g and F8m SURVIVED. Matches the reviewer and the
  implementer.
- **Coordinator, change:** the reviewer's live-check steps said "after the
  merge"; `ship` needs `live_checked` before the merge, so the steps run in
  the worktree (no cutover there, every merged intent `partial`, from
  `computeStats`'s `cutover = null` branch, `stats-lib.mjs:337`).

**Verified (round-3 reviewer, worktree `C:/Users/eric/src/product-advice-agent-wt/19-intent-stats` at 1ca5315, already its HEAD; nothing checked out):**
- `npm run verify` → exit 0: kit "tests 369, pass 369, fail 0"; "All checks passed!"; "157 files already formatted"; mypy "Success: no issues found in 28 source files"; "658 passed".
- `npm run check:intent` → exit 1, live check only, "25 file(s), 1707 line(s)".
- Round-3 diff read in full. `ship.mjs:227` merges `--no-ff`, so the cutover reads a first-parent merge commit in practice.
- The 14 mutants above.
- Branch not pushed: no remote branch. `main` was not touched by this branch. Main has since moved b2e2815 → 59ba1d0 with §22 bookkeeping commits only.

**Taken on trust:** the transcript format's stability (as in rounds 1–2), and round 2's coordinator results for mutants not re-run.
# Round 2 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 23ebd8f48f2e5fe79d494acae79b8c6f8bec630e
- round: 2
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed (path table: `scripts/session-event.mjs`'s logic,
`.claude/skills/**`, `scripts/ship.mjs`; `review_tier: reviewed`).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 19` →
"sampled: no".

The reviewer's own mutation batch was stopped by Claude Code for low memory
(only M4 ran); the owner asked for the rerun ("rerun the 19 mutants") and
the coordinator ran all 28 mutants in the foreground. The Mutants table
below is that run, not a prediction.

### Resolution of round 1
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

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 19, feature)
  error: A live check is owed and not recorded. Do the steps in intents/19-intent-stats/review.md → ## Live check, then set live_checked: <date> in intents/19-intent-stats/metadata.yml.
  note:  25 file(s), 1665 line(s) changed outside intents/.
```
The only error is the owed live check; clearing it is the owner's.

### Findings
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

### Mutants
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

### Not checked
- "kit 352 after the rebase" (Progress): not reproduced.
- `npm run stats -- --all` on real transcripts this round (memory); round
  1's run was clean and no output path changed.
- From round 1: the hook in a live session, the figures against owner
  memory, `projectSlug` for unusual paths.

### Live check
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

### Verified myself vs. taken on trust

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
