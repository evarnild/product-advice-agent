<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §15 review — A committed set of 50 real-looking eval questions with expected behaviour

verdict: attest
tier: attested
reviewed-commit: 5f5ccb0
round: 3
sampled: no
run: auto
live-check: owed

Tier: Attested by the path table: the branch touches
`src/advisor/evals/cases.py` and `score.py` (`src/**`, not in the Reviewed
row), tests, `evals/cases.jsonl`, `README.md`, `CLAUDE.md` and intent
artefacts; the round-2 rework adds no path (`evals/cases.jsonl`,
`tests/test_evals_cases.py`, `spec.md`, `plan.md`). `review_tier` empty. No
CRITICAL or HIGH finding; the eval run is named below.

HEAD 1de93e9 differs from 5f5ccb0 only in `metadata.yml` (`auto_round: 3`,
`auto_stopped` cleared); the reviewed content is 5f5ccb0.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 15` → "nth
attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the rework does the amendment at 8084fe5 and R2-F3's test, nothing more |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | pass; eval run made, no regression |
| 4 | Tests prove the behaviour, not only pass | pass: E1–E4 and the variety mutants killed; E5 survives by design |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): R3-F1 |
| 7 | Documentation | pass (README and CLAUDE.md name no variety minimums) |
| 8 | Guardrails and hygiene | pass (no dependency, secret or user data) |
| 9 | Repository-specific footguns | pass (list empty; round 2's `keywords_any` any-of suggestion stands for the owner) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 15, feature)
  error: A live check is owed and not recorded. Do the steps in intents/15-fifty-cases/review.md → ## Live check, then set live_checked: <date> in intents/15-fifty-cases/metadata.yml.
  note:  10 file(s), 690 line(s) changed outside intents/.
```
The only error is the owed live check (AC6): the owner's, not rework.

## Resolution of round 2
| # | Round 2 | Owner's decision (8084fe5) | At 5f5ccb0 | Status |
| --- | --- | --- | --- | --- |
| R2-F1 cordless | line 47 any-of `["wireless","over-ear"]` | (i) | probe and `keywords_any` `["over-ear"]`; question unchanged ("over ear"); `check_coverage` ok; 8 fit (P-001, P-035, P-043, P-051, P-203, P-211, P-419, P-443), all wireless and over-ear | resolved |
| R2-F1 anc | line 46 any-of `["noise-cancelling","over-ear"]` | (iii) | `["noise-cancelling"]` in probe and `expect_search`, as round 1; note "(over-ear is left to the judge, §16)" in the source segment (`variety:` must stay last for `NOTE_RE`); `check_coverage` ok, 8 fit | resolved |
| R2-F2 | lines 20, 21, 24, 35 without a category word | (a) | "laptop" / "phone" back; `vague` removed; probes pass `check_coverage` (19, 17, 12 fit; 0 in budget for budget-too-low) | resolved |
| R2-F2 vague minimum | B8 5 vague | "vague min 1" | `MIN_VARIETY = {"typo": 5, "multi": 5, "vague": 1, "casual": 5}` (`tests/test_evals_cases.py:214`); counts typo 6, multi 28, vague 1 (`music-gift-150`), casual 10, none 4 | resolved |
| R2-F3 | `expect_search` not tied to the probe | Needs rework | `test_expect_search_is_the_notes_probe_for_every_new_case` (`:443-452`), 28 cases, guard `checked >= 25`; kills E1–E4 | resolved |
| R2-F4 | unscored extras, lines 17, 18, 23 | worth a look | unchanged | the owner's AC6 read |

Wording of the four restored questions: `laptop-husband-work-1000`
byte-identical to round 1; `laptop-uni-backpack-900` round 1 minus the
backpack clause (round 1's (b)); `phone-battery-all-day-400` "My old phone
is flat by lunchtime and I just want a new one. Nothing fancy, up to 400
euros." (follows the source, keeps (b)'s cut);
`laptop-student-way-over-budget` "a laptop to write my essays on" ("essays"
is left from round 2's rewrite, not in `gen-budget-too-low-13`; harmless,
nit). All read like customers.

## Findings
- **R3-F1 LOW** `intents/15-fifty-cases/plan.md:135`: the plan body still
  says "B8: at least 5 cases each of `typo`, `multi`, `vague`, `casual`";
  the amended B8 and the test say vague ≥ 1. The amendment governs and
  Progress (`plan.md:374`) records it. Worth a look: the owner may add a
  pointer (above Progress is the owner's).

Nits: `test_variety_needs_five_of_each_not_four` is now misnamed (vague's
boundary is 1/0); `anc-train-rumble-200` keeps "over ear" (no longer forced,
reads naturally); `assert MIN_VARIETY == {…}` (`:438`) restates line 214.

**Mutants** (copy backup, one-match replace, full product suite, restore by
copy; `git status --short` shows only the two untracked pool files):

| Mutant | Target | Result | Killing test |
| --- | --- | --- | --- |
| E1 | `:17` `smartwatch-gps-bright-screen-200` drops `["GPS"]` from `expect_search` | KILLED | `test_expect_search_is_the_notes_probe_for_every_new_case` |
| E2 | `:46` anc `expect_search` → `["noise-cancelling","over-ear"]` | KILLED | same |
| E3 | `:18` `smartwatch-health-100-250` drops `["heart rate"]` | KILLED | same |
| E4 | `:47` cordless `expect_search` → `["wireless"]` (probe stays) | KILLED | same |
| E5 | `:47` cordless probe and `expect_search` both → `["wireless"]` | **SURVIVED** | none, by design: a coherent B6-valid edit; the owner's AC6 read confirms data values |
| E6 | `:25` `music-gift-150` loses `vague` | KILLED | `test_the_committed_file_has_the_customer_style_variety` |
| M1 | vague minimum 1 → 0 | KILLED | `test_variety_needs_five_of_each_not_four` |
| M2 | typo minimum 5 → 4 | KILLED | same |
| M3 | `counts[v] < MIN_VARIETY[v]` → `< 1` | KILLED | same |
| T1 | probe test skips everything | KILLED (the `checked >= 25` guard) | `test_expect_search_is_the_notes_probe_for_every_new_case` |
| T3 | probe test drops the `keywords` → `keywords_any` rename | KILLED | same |

No rework is open.

## Not checked
- The AC6 read (rule 3): whether the 50 read like customers and expect what
  the owner wants, including R2-F4 (lines 17, 18, 23), `music-gift-150` (the
  one vague case: expects `speaker` with `cites_only_matches`, so a
  headphones answer fails), and `cordless-over-ear-100-250` (its
  spelling-differs content is now only "over ear" against "over-ear").
- **Cross-intent, §22** (round 2, stopped at an eval regression): any-of
  search makes the no-match probes `headphones-ldac-balanced-200` and
  `smartwatch-gps-apps-minimalist` match products and fail
  `check_coverage`; both branches edit `_expected_results`, CLAUDE.md and
  README. Whichever merges second rebases and fixes it (§22's plan).
- The merged tree under `npm run verify`: `git merge-tree --write-tree main
  HEAD` exits 0; main changed no eval input since the merge base. A rebase
  before `/ship` means a new review round.
- Mutants not run: the coherent anc revert (like E5); fixture internals;
  round 1's code mutants (`cases.py`, `score.py` unchanged since round 1);
  kit behaviour (no kit file changed).

## Live check
- owed: rule 3 (AC6).
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/15-fifty-cases`, open
     `evals/cases.jsonl`: lines 1–15 are §8's (only `dimensions` added),
     16–50 the new 35, each `note` naming its source (`haiku:` = `evals/generated
     haiku.jsonl`), probe and variety.
  2. Read all 50 questions and expectations; look closely at lines 20, 21,
     24, 35 (category words restored), 46, 47 (over-ear), 25 (the one
     vague case) and 17, 18, 23 (unscored extras). Edit anything wrong.
  3. After any edit: `npm run verify`, commit on `feat/15-fifty-cases` (an
     edit means a new review round).
  4. The model run is already made (Eval run below: 29/50 on qwen3:8b);
     re-run `uv run advisor-eval` from the worktree only if you edit.
- you should see: questions that read like customers with expectations you
  agree with; the report's 29/50 is the baseline pass rate (AC6). A FAIL on
  no-match or budget-too-low wording is not by itself a defect (§16's
  judge). Then say "15 live checked" and `live_checked` is recorded at your
  word.

## Eval run
- owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
  touches" `evals/cases.jsonl`, `src/advisor/evals/cases.py`,
  `src/advisor/evals/score.py`.
- report: `evals/runs/20261121T125003Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at 1de93e9 (content = 5f5ccb0), copied
  to the main checkout's `evals/runs/`: **29/50**.
- `uv run advisor-analysis compare` against `evals/baseline.json`
  (`20261116T093026Z-ollama.json`, 8/15): regressed (0); fixed (1)
  `waterproof-camera`; added (35); removed (0); warning `cases_sha256`
  differs (expected: the cases changed).
- hashes: the report's `cases_sha256` `a965c9f099f7…`, `prompt_sha256`
  `a22c1cbe4f5d…`, `catalogue_sha256` `c2e56cb2ffcd…` equal the sha256 of
  the worktree's `evals/cases.jsonl`, `src/advisor/prompts/system.md`,
  `src/advisor/data/catalogue.json`.
- reading: no regression, so no `--only` re-run. Of the 35 new cases 14
  fail, most "cites no product" on several-matches and exact-match cases,
  and the three Norvik/Pelagic out-of-stock cases miss their product; these
  are the new cases' first measurement (the baseline /ship writes), not
  regressions.

## Verified myself vs. taken on trust

**Coordinator, re-run** (worktree at 1de93e9; `git status --short` only the
two untracked pool files before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "pass 298",
  "fail 0"; "All checks passed!"; "164 files already formatted"; mypy
  "Success: no issues found in 29 source files"; "741 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "10 file(s), 690 line(s)". Matches.
- **Coordinator, re-run:** E1, E2, E3 KILLED (1 failed, 740 passed each);
  E5 SURVIVED (741 passed). Matches the reviewer and the implementer.
- **Coordinator, re-run:** `owes-run`, the eval run, compare and the hash
  check above.

**Reviewer (agent), read-only:** `git diff 27d5428..5f5ccb0`; scratch checks
with `parse_cases`, `fits`, `catalogue_problems`, `check_coverage` (50
cases, problems empty, variety counts, fit counts, the 8 cordless fits);
E4, E6, M1–M3, T1, T3; `git merge-tree`; sampling.

**Taken on trust:** which test kills each mutant (the reviewer's and the
implementer's reports; the coordinator's harness records the failure count
only); that the pool files are the owner's pools; round 1's code mutants.

# Round 2 (history)


- verdict: rework
- tier: attested
- reviewed-commit: 27d5428
- round: 2
- sampled: no
- run: auto
- live-check: owed

Tier: Attested by the path table, unchanged from round 1 (the rework
touches `evals/cases.jsonl`, `tests/test_evals_cases.py`, `README.md` and
intent artefacts; no new path); `review_tier` empty; no CRITICAL or HIGH
finding.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 15` → "nth
attested auto change = 5, every 3, sampled: no".

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): R2-F2 |
| 2 | Type check | pass (FAIL only on the owed live check, the owner's) |
| 3 | Behaviour against the spec | findings (2): R2-F1, R2-F4; eval run owed |
| 4 | Tests prove the behaviour, not only pass | findings (1): R2-F3 |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; suggestion below) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 15, feature)
  error: A live check is owed and not recorded. Do the steps in intents/15-fifty-cases/review.md → ## Live check, then set live_checked: <date> in intents/15-fifty-cases/metadata.yml.
  note:  10 file(s), 673 line(s) changed outside intents/.
```
The only error is the owed live check (AC6), not a rework finding.

### Resolution of round 1
| # | Round 1 | Owner's decision | At 27d5428 | Status |
| --- | --- | --- | --- | --- |
| F1 (a) | `smartwatch-gps-bright-screen-200` (17) | (a) | `keywords_any: ["GPS"]` in probe and `expect_search`; fits 16 → 4 (P-025, P-110, P-206, P-366); "bright screen" unscored (R2-F4) | resolved |
| F1 (a) | `smartwatch-health-100-250` (18) | (a) | `["heart rate"]`; fits 12 → 8; SpO2 appears in no product, rightly not added | resolved |
| F1 (a) | `anc-train-rumble-200` (46) | (a) | `["noise-cancelling", "over-ear"]` any-of: fits widen 8 → 18 | **not achieved**: R2-F1 |
| F1 (a) | `cordless-over-ear-100-250` (47) | (a) | `["wireless", "over-ear"]` any-of: fits stay 23 | **not achieved**: R2-F1 |
| F1 (b) | `laptop-uni-backpack-900` (21) | (b) | backpack clause cut; "a laptop" also changed to "something" (not asked) | resolved; see R2-F2 |
| F1 (b) | `monitor-small-desk-400` (23) | (b) | "small desk" cut; "for studying at home" added (not in the source) | resolved; R2-F4 |
| F1 (b) | `phone-battery-all-day-400` (24) | (b) | "lasts the whole day" cut; "phone" also removed (not asked) | resolved; see R2-F2 |
| F2 | B6 table not enforced | rework | `test_new_cases_expect_what_their_scenario_says` (`tests/test_evals_cases.py:324`) checks each branch; D1, D2 and 9 branch mutants KILLED | resolved; the probe-to-`expect_search` link still untested (R2-F3) |
| F3 | T5 survived | rework | `variety_problems` (`:267`), `test_variety_needs_five_of_each_not_four` (`:422`); T5, V1–V3 KILLED | resolved |
| F4 | `tablet-reading-drawing-80` | accept | note: "source edited: max_price 120 to 80, see spec B6 amendment"; the source probe fails `check_coverage` as written (re-checked) | resolved |
| F5 | Progress overstated | rework | correction appended (`plan.md:306`), verified | resolved |
| F6 | README missing B4 message | worth a look | `README.md:292-295` quotes it, matching `cases.py:236` | resolved |
| F7 | `vague` tags literal | worth a look | out-of-stock cases re-tagged; five `vague` reached by rewriting three questions to drop their category word | acted on beyond the owner's decisions: R2-F2 |

### Findings
- **R2-F1 MEDIUM** `evals/cases.jsonl:46,47` (`anc-train-rumble-200`,
  `cordless-over-ear-100-250`): F1 (a) is not achieved for the two over-ear
  cases. `keywords_any` is any-of (`fits`, `cases.py:206-212`; the `search`
  check, `_call_satisfies`, `score.py:79-83`), so adding the word widened
  them:
  - ANC: fits 8 → 18; ten of the 18 have no noise cancelling (P-006, P-035,
    P-043, P-051, P-203, P-211, P-275, P-419, P-443, P-459), five are not
    over-ear.
  - Cordless: fits stay 23; 15 are not over-ear.
  - The `search` check got weaker than round 1: a search with only
    `keywords: ["over-ear"]` now satisfies both (`_call_satisfies` True);
    before, it had to carry "noise-cancelling" / "wireless", the
    spelling-differs point of the case.
  - The note's probe (all-of in `search_products`, `catalogue.py:141`)
    counts 3 and 8 for `check_coverage`, while `expect_search` accepts 18
    and 23.
  - "over ear" in the questions: both cases are spelling-differs for their
    original keyword, not for over-ear; the verbatim rule
    (`coverage.py:155-158`) forced "over-ear" to be respelled, which search
    normalises anyway, so it adds no spelling-differs content (it reads
    naturally).

  **Needs decision**, per case (fits on the 500 catalogue, ANC under 200 /
  cordless 100–250):

  | Option | ANC | cordless | Meaning |
  | --- | --- | --- | --- |
  | today: any-of `[old, "over-ear"]` | 18 | 23 | widens or does nothing; `search` passes on "over-ear" alone |
  | (i) replace the old keyword with `"over-ear"` | 13 | 8 | over-ear scored; spelling-differs content lost; `search` no longer asks for noise-cancelling / wireless; ANC's 13 include 10 over-ear without ANC |
  | (ii) an all-of constraint (case format, `fits`, `_call_satisfies`; amends B1/B2, a spec change) | 3 (P-001, P-123, P-355) | 8 | scores both words; matches what the note's probe counts; for cordless, (i) and (ii) give the same 8 |
  | (iii) revert to the round-1 keyword; note "over-ear left to §16's judge" | 8 | 23 | as round 1; the question may say "over-ear" again |

- **R2-F2 MEDIUM** `evals/cases.jsonl:20,21,24,35`
  (`laptop-husband-work-1000`, `laptop-uni-backpack-900`,
  `phone-battery-all-day-400`, `laptop-student-way-over-budget`): to keep
  B8's 5 `vague` after F7's re-tagging, the rework rewrote these to drop
  their category word: outside the owner's decisions (F7 was worth a look;
  (b) said "cut the extra"), and against B6 ("keeping what the probe
  expresses": every source names the category). The cases now expect a
  category the customer never named. On the 500 catalogue: "something to
  get his work done on… up to 1000" fits 41 tablets as well as 19 laptops;
  "something for essays and streaming lectures… 900" 37 tablets and 17
  laptops; with `cites_only_matches` a sensible tablet fails
  `only-matches` and `search`. `laptop-student-way-over-budget` is
  budget-too-low, yet "something to write my essays on… about 200 euros"
  has 5 tablets under 200, so its premise is false as written.
  `phone-battery-all-day-400` still reads as a phone, but 32 smartwatches
  are under 400. `music-gift-150` (round 1, unchanged) has the same shape
  (headphones fail `only-matches`). **Needs decision:** (a) put the category
  word back in the four (vague drops to 1: B8 needs other vague cases or a
  spec change to "5 vague (no category word)"); (b) keep them vague and drop
  `category` from `expect_search` (`cites_only_matches` then means little:
  344 products under 1000, 326 under 900, 177 under 400;
  `laptop-student-way-over-budget` stops being budget-too-low, 82 under
  200); or (c) keep them and note that each tests inferring the category,
  accepting that a tablet answer fails.
- **R2-F3 MEDIUM** `tests/test_evals_cases.py:306-336`: no test ties a new
  case's `expect_search` to its note's probe (B6 "from the probe"; the
  amendment "the case's probe and `keywords_any`"), so the F1 (a) data is
  unguarded. E1 (`smartwatch-gps-bright-screen-200` loses `"keywords_any":
  ["GPS"]`, keeps it in the probe), E2 (`anc-train-rumble-200` back to
  `["noise-cancelling"]`), E3 (`smartwatch-health-100-250` loses `["heart
  rate"]`) SURVIVE (740 passed). **Needs rework:** assert that for every
  new case except out-of-stock, `expect_search` equals the probe with
  `keywords` renamed `keywords_any` (adjusted to R2-F1's decision, e.g. an
  all-of field). Must kill E1, E2, E3.
- **R2-F4 LOW** `evals/cases.jsonl:17,18,23`: extras still unscored:
  `monitor-small-desk-400` gained "for studying at home" (not in
  `gen-several-matches-6`; the owner's (b) was a cut); line 17 "a bright
  screen" (one smartwatch says "bright"); line 18 SpO2 (none). Left to the
  judge. Worth a look at the AC6 read.

Footgun suggestion (pass 9, the owner's edit of `REVIEW-POLICY.md`):
"`keywords_any` is any-of in `fits` and `_call_satisfies`, while a probe's
`keywords` are all-of in `search_products`: adding a word to `keywords_any`
widens a case, never narrows it." (Two rounds running.) Note: §22, in
review, makes `search_products` any-of too, which closes the probe side of
this gap but not the narrowing problem.

**Mutants** (copy backup, one-match bytes replace, `git diff --quiet` ≠ 0,
full product suite, restored byte-identical): 17 run, 14 KILLED, 3
SURVIVED.
- Round-1 survivors: D1 KILLED (`test_new_cases_expect_what_their_scenario_says`),
  D2 KILLED (same), T5 KILLED (`test_variety_needs_five_of_each_not_four`).
- F2's scenario test, one data mutant per branch, all KILLED by
  `test_new_cases_expect_what_their_scenario_says`: B-off
  (`off-topic-sourdough` `must_decline` false), B-nm-decline
  (`camera-wildlife-zoom` gains `must_decline`), B-btl-props
  (`laptop-uni-250` gains `cites_only_matches`), B-em-only-matches
  (`gift-smartwatch-300` keeps only `cites_only_matches`), B-oos-ids-extra
  (`norvik-canvas-school` second id P-017), B-sm (`monitor-room-500` loses
  `cites_a_match`), B-sd-kw (`shower-speaker-water-proof` loses
  `keywords_any`), B-sd-props (`beach-speaker-waterprof` loses
  `cites_a_match`). The out-of-stock "no properties" assertion is
  unreachable (`parse_cases` rejects properties without `expect_search`):
  equivalent.
- `variety_problems`: V1 (`<` → `<=`), V2 (unknown-variety line dropped),
  V3 (`VARIETIES[:3]`) KILLED.
- **E1, E2, E3 SURVIVED** (R2-F3).

### Not checked
- Whether the 50 read like customers and the expectations are what the
  owner wants: the owner's AC6 read (rule 3), including R2-F2's fairness
  question and R2-F4.
- Model output on the 50, including AC6's baseline (Eval run).
- `main` has moved (§16, §19 merged, §22 planned): `git merge-tree
  --write-tree main HEAD` reports no conflict; `CLAUDE.md` and `README.md`
  changed on both sides; main touched none of the eval-run inputs. A rebase
  before `/ship` means a new review round. **§22** (in review) changes
  `search_products` and therefore `check_coverage` for multi-keyword
  probes; whichever of §15 and §22 merges second re-checks the probe test.
- Mutants not run: weakenings of the scenario test (covered by data
  mutants); the unreachable out-of-stock assertion; round 1's code mutants
  (`cases.py`, `score.py` unchanged).

### Live check
- owed: rule 3 (AC6).
- steps:
  1. Decide R2-F1 (lines 46, 47: i, ii or iii) and R2-F2 (lines 20, 21, 24,
     35: a, b or c); the rework follows and the next round reviews it.
  2. After the rework, in
     `C:/Users/eric/src/product-advice-agent-wt/15-fifty-cases`, open
     `evals/cases.jsonl`: lines 1–15 are §8's (only `dimensions` added),
     16–50 the new 35, each `note` naming its source (`haiku:` = `evals/generated
     haiku.jsonl`), probe and variety.
  3. Read every question and expectation; check R2-F4 (lines 17, 18, 23) and
     the `vague` cases (20, 21, 24, 25, 35) with care; edit anything wrong.
  4. After any edit, `npm run verify` and commit on `feat/15-fifty-cases`.
  5. `uv run advisor-eval` once on the default model (Ollama) from the
     worktree.
- you should see: 50 PASS / FAIL / ERROR lines and a total; a report
  `evals/runs/<stamp>-ollama.json` whose `cases_sha256` equals the sha256
  of the committed `evals/cases.jsonl`; `a-match` / `only-matches` on cases
  with properties. Quote the pass rate as the baseline (AC6).

### Eval run
owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
touches `evals/cases.jsonl`, `src/advisor/evals/cases.py`,
`src/advisor/evals/score.py`". **Not made this round** (verdict rework;
R2-F1 and R2-F2 will change `evals/cases.jsonl`): the coordinator makes it
on the reviewed commit of the first round whose verdict is not rework.
Hashes at 27d5428: `evals/cases.jsonl` `3c72d16c…2db7`, prompt
`a22c1cbe…0fdc`, catalogue `c2e56cb2…efab` (prompt and catalogue equal the
baseline's).

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 27d5428; `git status --short`
only the two untracked pool files before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "164 files already formatted"; mypy "Success: no
  issues found in 29 source files"; "740 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "10 file(s), 673 line(s)". Matches.
- **Coordinator, re-run:** the kills the rework claims: D1, D2, T5 each
  KILLED (1 failed, 739 passed). Matches.
- **Coordinator, re-run:** survivors E1, E2, E3 each SURVIVED (740
  passed). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, sampling, `owes-run`; scratch
scripts against the real modules: 50 unique cases, `catalogue_problems`
empty, all 35 sources in the pools, all 35 probes pass `check_coverage`,
every `expect_search` equals its probe, the spread and variety counts, every
fit count in this report, SpO2 absent from the catalogue, `_call_satisfies`
passing "over-ear" alone for both cases, round 1's F5 claims; the 17
mutants; no remote branch; `main` moved only by the owner's merges.

**Taken on trust:** that the pool files are the owner's pools; the owner's
decision text as quoted in the B6 amendment (db3c3af); round 1's code
mutants (`cases.py`, `score.py` unchanged).
# Round 1 (history)


- verdict: rework
- tier: attested
- reviewed-commit: 37af371
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: the path table. The diff touches `src/advisor/evals/cases.py` and
`score.py` (`src/**`, not in the Reviewed row), tests, `evals/cases.jsonl`
(data), `README.md`, `CLAUDE.md` and intent artefacts; the highest is
Attested. `review_tier` is empty; no CRITICAL or HIGH finding; no
Not-checked item bears on what a user receives (eval data and scorers).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 15` → "nth
attested auto change = 5, every 3, sampled: no".

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F4 |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (2): F1, F7 |
| 4 | Tests prove the behaviour, not only pass | findings (2): F2, F3 |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): F5 |
| 7 | Documentation | findings (1): F6 |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 15, feature)
  note:  10 file(s), 633 line(s) changed outside intents/.
```

### Findings
- **F1 MEDIUM** `evals/cases.jsonl:17,18,21,23,24,46,47`: these questions
  ask for something the expectations don't score, so a wrong answer can
  pass. B6 takes `expect_search` "from the probe", and these probes hold
  only category and price, so `a-match` / `only-matches` accept any product
  in that category and range. Against the 500 catalogue (fitting the
  `expect_search` / naming the extra):
  - `smartwatch-gps-bright-screen-200` (GPS, bright screen): 16 / 4 GPS;
  - `smartwatch-health-100-250` (heart rate, SpO2): 12 / 8;
  - `laptop-uni-backpack-900` ("light enough for a backpack"): 17 / 2; the
    clause was added by the rewrite, not in `haiku:gen-several-matches-2`;
  - `monitor-small-desk-400` (small desk): 16 / 2;
  - `phone-battery-all-day-400` (all-day battery): 12 / 1;
  - `anc-train-rumble-200`, `cordless-over-ear-100-250` (over-ear): 8 / 3
    and 23 / 8.

  E.g. a non-GPS watch under 200 euros passes
  `smartwatch-gps-bright-screen-200`. **Needs decision**, per case: (a) add
  the extra to `keywords_any` where the catalogue supports it (departs from
  B6's "from the probe": a spec amendment); (b) cut the extra from the
  question (for `laptop-uni-backpack-900`, at least the added clause); or
  (c) keep it, leave the extra to §16's judge, and say so in the `note`.
  Can be done as part of the AC6 edit.
- **F2 MEDIUM** `tests/test_evals_cases.py:317-332`
  (`test_new_cases_expect_what_their_scenario_says`): B6's table is not
  enforced, so a wrong expectation (above all the owner's own AC6 edits)
  goes unnoticed. Data mutants D1 (`gift-smartwatch-300`, line 16, loses its
  `expect_properties`: exact-match is lumped with no-match and
  budget-too-low) and D2 (`norvik-canvas-school`, line 41, `expect_ids`
  P-024 → P-004: nothing ties it to the probe's `product_id`) survive. The
  data is right today (all 35 read against B6). **Needs rework**, per B6:
  exact-match → `expect_search` and (`expect_ids` or `cites_a_match`);
  out-of-stock → `expect_ids == [probe.product_id]`; no-match and
  budget-too-low → `expect_search`, no `expect_ids`, no
  `expect_properties`, no `must_decline`. Must kill D1, D2.
- **F3 LOW** `tests/test_evals_cases.py:214, 310-314`: B8's "at least 5"
  has no boundary test; T5 (`MIN_VARIETY = 5` → `4`) survives (the file has
  6 typo and 6 vague, so 4, 5, 6 all pass;
  `test_variety_is_counted_from_the_note_with_a_boundary` tests counting,
  not the threshold). The plan's Risks: "Each bound gets a boundary test on
  an in-test case list". **Needs rework:** move the threshold into a helper
  (e.g. `variety_problems(cases)` using `MIN_VARIETY`) and test 4 fails, 5
  passes on an in-test list. Must kill T5.
- **F4 LOW** `evals/cases.jsonl:37` (`tablet-reading-drawing-80`): a
  disclosed departure from B6. The source `haiku:gen-budget-too-low-11` (a
  son, school, under 120) fails `check_coverage` (one tablet at 119 fits);
  the case moves the probe to `max_price` 80, rewrites the question (a
  cousin, reading and drawing, 80 euros) and changes the persona to gift
  buyer. Only 4 budget-too-low pool items pass on the 500 catalogue (3
  laptops, 1 tablet), and without this case tablet is a `feature` only 3
  times; an unused passing laptop source, `gen-budget-too-low-12`, exists
  but doesn't help the tablet count. **Needs decision:** accept the edited
  source (it now duplicates `tablet-under-100` in substance), or swap in
  another passing tablet source from a different scenario and use
  `gen-budget-too-low-12` for the fifth budget case.
- **F5 LOW** `intents/15-fifty-cases/plan.md:230, 292-298` (Progress)
  overstates: "Four sources had a probe that did not fit as written" holds
  only for the tablet (the three out-of-stock probes pass `check_coverage`
  as written, which ignores category for out-of-stock; their edits correct
  the generator's category: P-017 phone, P-024 tablet, P-032 speaker); a
  fourth feature correction is unmentioned (`gen-out-of-stock-1` →
  `norvik-fold-brother-gift`, monitor → phone); "4 `fits`" tests: there are
  3. **Needs rework:** correct the Progress entry (append a correction
  below it).
- **F6 LOW** `README.md:285-295` ("Changing the catalogue") lists what
  fails `verify` after a catalogue edit but not B4's new message ("no
  product fits expect_search, so cites_a_match cannot pass"). Worth a look.
- **F7 LOW** `evals/cases.jsonl:38-42`: variety tags meet B8 only
  literally. Five of six `vague` are out-of-stock questions naming an exact
  product (Pelagic Studio 15, Norvik Fold ×2, Norvik Canvas 13, "Aurelis"
  Home 1): no category word, but the opposite of vague; `music-gift-150` is
  the only truly vague one. `multi` is uneven (`tablet-reading-drawing-80`
  is multi, `sister-birthday-watch` with category, budget and gift is not).
  Worth a look at the live check.

Nit: AC2 names "an in-test catalogue"; the new score tests use the real
catalogue, as the existing score tests do; the per-constraint checks are
`fits` tests in `tests/test_evals_consistency.py`, covering B2 through the
shared predicate.

**Mutants** (one per changed behavioural line; copy-backup harness
asserting one match and `git diff --quiet` ≠ 0; full product suite `uv run
pytest -q -x`; restored byte-identical): 40 run, 36 killed, 4 survived.
- `cases.py`: C1 (field dropped from `_FIELDS`), C2 (`PROPERTIES` loses a
  name), C3 (empty list accepted), C4 (list check dropped), C6
  (unknown-name check dropped), C7 (duplicate check dropped), C8
  (needs-`expect_search` check dropped), C9 (`_properties` returns `()`),
  C10 (`parse_cases` ignores the field): KILLED. C5 (`isinstance(name, str)`
  dropped): SURVIVED, equivalent (a non-string also fails `name not in
  PROPERTIES` with the same error).
- `fits` F1–F8 (category, `>=`, `<=`, stock, any→all, brand dropped, no
  `_norm`, keyword branch dropped): KILLED. B4a (property condition
  dropped), B4b (inverted), B4c (wrong property name): KILLED.
- `score.py`: S1, S1b (existence filter), S2 (`a-match` ok on any
  citation), S3, S7 (check without its property), S4 (`fits` dropped from
  `a-match`), S5 (`only-matches` always ok), S6 (misfit test inverted), S8,
  S9 (reasons lose the ids): KILLED.
- Test helpers: T1 (scenario high 12→13), T2 (low 5→4), T3a (off-topic low
  2→1), T3b (off-topic high 4→5), T4 (per-feature 4→3): KILLED, both sides
  hit. **T5** (`MIN_VARIETY` 5→4): SURVIVED (F3).
- Data: **D1**, **D2**: SURVIVED (F2).

The rework must kill D1, D2 and T5.

### Not checked
- Whether the 50 read like real customers and the expectations are what the
  owner wants: the owner's AC6 read (live-check rule 3).
- Model output on the 50, including AC6's baseline pass rate (see Eval run).
- The "keeps what the probe expresses" judgement on all 35 is the
  reviewer's, not repeatable by a tool.
- Mutants not run: `PROPERTIES` with a third arbitrary name (only
  `cites_everything` is tested as unknown; low value, a name needs a
  `score.py` check); the `Case` default `expect_properties=()`; the `ok`
  reason strings of `a-match` and `only-matches` (no test reads them).
- Kit mutation behaviour (no kit file changed); `npm run sessions`.

### Live check
- owed: rule 3 (AC6): the questions' real-lookingness and the model's
  output on the 50 show only with an owner read and a real run.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/15-fifty-cases`, open
     `evals/cases.jsonl`. Lines 1–15 are §8's cases (only `dimensions`
     added, verified byte for byte); lines 16–50 are the new 35, each
     `note` naming its source (`haiku:` = `evals/generated haiku.jsonl`),
     probe and variety tags.
  2. Read every question and expectation; decide F1 (lines 17, 18, 21, 23,
     24, 46, 47) and F4; edit anything that doesn't read like a customer or
     isn't the right expectation.
  3. After any edit, `npm run verify` (format, catalogue consistency,
     spread, variety, each probe against `check_coverage`); commit on
     `feat/15-fifty-cases`. The next review round covers the edits.
  4. `uv run advisor-eval` once on the default model (local Ollama, minutes
     on CPU), from the worktree.
- you should see: one PASS / FAIL / ERROR line per case for 50 cases and a
  total; a report `evals/runs/<stamp>-ollama.json` whose `cases_sha256`
  matches the committed `evals/cases.jsonl`; cases with
  `expect_properties` show `a-match` and/or `only-matches`. Quote the pass
  rate as the baseline (AC6). A FAIL is not by itself a defect here (§16's
  judge covers wording).

### Eval run
owed: `uv run advisor-analysis owes-run --base main` → "owed: the diff
touches `evals/cases.jsonl`, `src/advisor/evals/cases.py`,
`src/advisor/evals/score.py`". **Not made this round:** the verdict is
rework, and F1 and F4 will change `evals/cases.jsonl`, so a run now would
not be of the content that ships. The coordinator makes it in the first
round whose verdict is not rework, on the reviewed commit (35 cases
"added" in `compare` is expected). Hashes at 37af371 for reference:
`evals/cases.jsonl` `a80b0a1b…8f43`, `src/advisor/prompts/system.md`
`a22c1cbe…0fdc`, `src/advisor/data/catalogue.json` `c2e56cb2…efab`.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 37af371; `git status --short`
shows only the two untracked pool files before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "163 files already formatted"; mypy "Success: no
  issues found in 29 source files"; "739 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "10 file(s), 633
  line(s)". Matches.
- **Coordinator, re-run:** survivors D1, D2, T5 each SURVIVED (739
  passed). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, `owes-run` (owed, 3 paths),
sampling; the data with scratch scripts against the real modules: 50 cases,
unique ids and questions; the scenario, feature, persona and variety counts
above; each typo tag a real misspelling; 35 with `source:`; §8's 15
identical to `main` but for `dimensions`; AC5 on all 35 (every source id in
the pools; every probe passes `check_coverage` by the reviewer's own call;
every `expect_search` equals its probe; every out-of-stock `expect_ids` is
its probe's product, P-010, P-017, P-024, P-032 out of stock;
spelling-differs carry `keywords_any` and `cites_a_match`; no-match and
budget-too-low carry no properties; off-topic `must_decline`); the corrected
probes; budget-too-low pool pass rate 4 of 28; the 40 mutants; `cases.py`
and `score.py` import only `advisor.catalogue` and each other; no
dependency, secret or user data; main unchanged, no upstream.

**Taken on trust:** that the worktree's pool files are the owner's pools
(the coordinator copied them from the main checkout); the kit's own tests
for `check:intent` and `sdlc:scan`.
