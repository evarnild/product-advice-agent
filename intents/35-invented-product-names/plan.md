<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §35 plan — Catch an answer that names a product the catalogue does not have

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Add a deterministic check, `invented`, right after `names` in `score()`
(`src/advisor/evals/score.py`), for every case. For each occurrence of a
known cited id it reads the *name slot* (the capitalised run directly before
the id, spec B1) and fails when the run is two to five words that are neither
a catalogue name, nor the cited product's own name or a whole-word tail of
it, nor a near-spelling of it with the same numbers (B2-B4). The reason reads
"P-012 is the Tolvane Chrome 11, cited as Aurelis Home 2" (B5). The helper is
pure (`invented_names(answer, by_id)`, B7). The owner's five defaults are
built as written. The spec's 41-flagged replay becomes a committed test over
a committed fixture, and the 0.85 threshold is pinned by a test pair on each
side. The eval run (AC8) is the coordinator's step at review.

## Risks

- **A false failure on a correct answer.** The rule is tuned on one data set
  (spec "Evidence"). Mitigation: the fixture holds every shape that was a
  false positive in the prototype, plus a whole Haiku report (flags none),
  and the review repeats the full replay.
- **Tests that pass whatever the code does** (REVIEW-POLICY pass 4). Every
  pass test has a fail twin that differs in one thing only (the id, one
  digit, one word), so an always-pass or always-fail helper is caught. Each
  test below names the mutant it kills.
- **The replay fixture rots.** It is scored against the committed catalogue.
  A catalogue change under `docs/decisions/0003-catalogue-changes.md` could
  rename a product and move a verdict. The fixture test names the field it
  stores per answer (expected pairs), so a break is a visible edit, not a
  silent pass.
- **Slot parsing is the whole difficulty.** Markdown (`**`, `[`, quotes),
  list markers, lead-in words and sentence breaks all sit before an id. The
  words are split on whitespace, so a name with punctuation inside a word
  ("Aurelis-Home 2") reads as one word. Covered by the AC3 tests.
- **Stale line citations.** The other open worktrees are not on `main`: §32
  adds `catalogue.fold` and changes `score._call_satisfies`, §31 changes
  `agent.py`, §33 edits `prompts/system.md`. §32 may shift `score.py` lines
  after `_call_satisfies` (`:121`) and add an import near `:10`. This plan
  uses `_norm` as it is at `:10` and depends on none of those lines
  staying put; re-read before launch. If §32 lands first, `_norm` may
  become `fold`; the helper then uses whichever the file imports.
- **Tests listing check names.** Adding `invented` changes the lists at
  `tests/test_evals_score.py:119,122,286,288`. Update, don't delete.
- **Reports from now on carry one more check** (`invented`); old reports
  and labels are not re-scored (decisions/0003), `compare` reads statuses
  only, so it is unaffected.
- REVIEW-POLICY.md pass 9 (repository-specific footguns) names no class
  (REVIEW-POLICY.md:250-252).

## Verified against the codebase

Re-read on `main` at `ec8036d`.

- `src/advisor/evals/score.py:10` — `from advisor.catalogue import Product, _norm`.
- `src/advisor/evals/score.py:15` — `_ID_RE` (`P-` and three digits, not in a longer token).
- `src/advisor/evals/score.py:29-31` — `cited_ids`.
- `src/advisor/evals/score.py:34` — `_WINDOW = 80`.
- `src/advisor/evals/score.py:37-88` — `misnamed`; `:48` ids as `(start, end, id)`; `:53` length-preserving fold; `:54-61` the name regex over `_norm` names, longest first; `:85` the `names` rule.
- `src/advisor/evals/score.py:144-173` — `score()`; `:155-162` the `grounded` check; `:164-173` the `names` check, whose reason is `f"{i} is the {own}, cited as ..."` (the `invented` check copies its shape and goes right after line 173).
- `src/advisor/evals/score.py:175-195` — `prices` follows; `:250-264` the property checks (unchanged).
- `src/advisor/catalogue.py:109-110` — `_norm`: `text.lower().replace("-", " ")`.
- `src/advisor/data/catalogue.json` — checked by script at `ec8036d`: P-004 Sonavo Quiet Pro, P-005 Kestrel Air Plus, P-007 Norvik Slate 14, P-009 Pelagic Go 13, P-012 Tolvane Chrome 11, P-013 Zephra One, P-017 Norvik Fold, P-025 Auralis Tick S, P-032 Auralis Home 1, P-123 Kestrel Calm 46 (all names the spec quotes).
- `difflib.SequenceMatcher(None, a, b).ratio()` on the case-folded names, computed at `ec8036d`: "aurelis home 1" vs "auralis home 1" 0.929; "aurelis hume 1" 0.857 (passes at 0.85, fails at 0.90); "aurelis hum 1" 0.815 (fails at 0.85, passes at 0.80); "aurelis home 2" 0.857 (the digit rule, not the ratio, fails it on P-032).
- `src/advisor/evals/baseline.py:15-26` — `EVAL_PATHS` holds `src/advisor/evals/score.py`: an eval run is owed. `evals/baseline.json` moves after merge (REVIEW-POLICY.md:113-134, "Eval runs").
- `src/advisor/evals/run.py:292-296,369` — `score()` output serialised generically as `{name, ok, reason}`; no list of check names.
- `src/advisor/evals/view.py:218-238` — the viewer renders whatever checks the report has; no list of names. `counts.py`, `labels.py`, `analysis.py`, `baseline.py`: no check-name list (grep for `"grounded"`/`"names"` over `src/` finds `score.py` only).
- `tests/test_evals_score.py:7,11-12` — `CATALOGUE = load_catalogue()`, `verdicts(case, answer)` (name to ok); `:92` `GOOD`; `:119,122,286,288` the four asserted name lists; `:296-297` `names_check` helper; `:300-357` the §25 tests.
- `tests/test_evals_run.py:224` — `>=` on a name set, unaffected. `tests/test_analysis_view.py:49` — a fixed `grounded` row, unaffected.
- `README.md:155-190` — "Checks" list; `:160` grounded, `:161-167` names, `:168` prices.
- `.gitignore:24` — `evals/runs/` is ignored, so a test cannot read the reports.
- `scripts/intent-check-lib.mjs` — `score.py` is `CORE_CODE` (CLAUDE.md "Architecture"); `tests/test_boundaries.py` keeps the pure modules free of langfuse. `difflib` is standard library.
- `intents/25-cited-id-name-mismatch/plan.md` — the precedent: failing-first tests, the helper before the check, name lists updated, the eval run at review.

## Subtasks

1. **Helper and its tests (check not wired).** Add the tests under "Tests"
   T1-T14 in `tests/test_evals_score.py`, calling
   `invented_names(answer, by_id)` and watch them fail. In `score.py` add
   `invented_names(answer, by_id) -> list[tuple[str, str, str]]` (id, own
   name, run as written) beside `misnamed`, once per id, in order of first
   occurrence, plus `_SIMILARITY = 0.85`, `_MAX_SLOT = 5` and the slot logic
   (below). `import difflib`. Verify green, commit.
2. **The check.** Test T15-T17 first. Add the `invented` check right after
   the `names` check (after `:173`) with the B5 reasons, and update the four
   name lists (`:119,122,286,288`) to put `invented` right after `names`.
   Verify, commit.
3. **The replay fixture.** Build `tests/fixtures/invented_replay.json` once
   with a throwaway script in the scratchpad (not committed) from
   `evals/runs/*.json` at `ec8036d`: the 41 flagged answers (report file name,
   case id, answer text, the expected `(id, name)` pairs; 75 pairs in all)
   and every answer of `20261124T192816Z-anthropic.json` plus the PASS
   answers that were the four prototype false positives (expected: no
   pair). Add `test_invented_replay_*` (T18-T19). Everything in the
   fixture is model output over the synthetic catalogue: no secret, no user
   data. Verify, commit.
4. **Docs.** Add an **invented** bullet after **names** in `README.md`'s
   check list (what is read: the capitalised run right before a cited id;
   what passes; what is missed; the reason text). `CLAUDE.md` and `AGENTS.md`
   do not name the checks (grep at `ec8036d`); update them only if that is no
   longer true. Verify, commit.
5. **Hand over.** `status: in-review`. The eval run is the coordinator's at
   review (Validation), not the implementer's.

**The slot logic** (the spec's B1-B4, no new design). For each id occurrence
at `start` in `ids = _ID_RE.finditer(answer)` with `pid in by_id`: take the
text from `max(previous id end, last newline before start + 1)` to `start`;
strip the trailing characters in ` (`, `[`, `*`, quotes (and spaces); split
on whitespace; walk the words backwards taking a word only if, after
stripping leading `*`, `(`, `[`, `_` and quotes, it starts with an uppercase
letter or a digit and does not end with `. ! ? : ;` or `,` (a word that does
end so, such as "GPS." or "1." or "**Price:**", ends the walk and is not
taken); stop at five words. Drop a leading "The", "A" or "An" and a leading
pure-number list marker; strip `*`, brackets and quotes from each word; the
run is the rest. Pass when: fewer than two words; or `_norm(run)` is a
catalogue name; or `_norm(run)` equals the cited name or a whole-word suffix
of it; or `ratio(_norm(run), _norm(own)) >= _SIMILARITY` and
`re.findall(r"\d+", run) == re.findall(r"\d+", own)`. Else it is invented.
A bare id word (another `P-123`) ends the walk.

## Tests

All in `tests/test_evals_score.py` (new section "invented", after the §25
tests) against the committed catalogue and no model, except T18-T19 (fixture).
`inv(answer)` is a small helper over `invented_names` or, from T15 on, the
`invented` check. "M:" is the mutation each test kills; the implementer runs
each against the full suite and restores by copy, as in §25.

- **T1 (B4, AC1) the four intent lines fail.** "1. **Acme Foldable (P-004)**
  - 399.00", "2. **TechFold Pro (P-007)**", "- **Aurelis Home 2 (P-012)**",
  "- **Aurelis Home 3 (P-013)**" each give the pair (id, real name, run).
  M: helper always returns `[]`; M: reads after the id.
- **T2 (B5, AC1) reasons.** The check reason is exactly "P-004 is the Sonavo
  Quiet Pro, cited as Acme Foldable"; several joined with "; ", each id once
  in order of first occurrence (an id cited twice with two invented names
  reports the first). M: `", "` join; M: no dedupe; M: own name swapped for
  the run.
- **T3 (B4) brand with invented model and another maker's product fail.**
  "Norvik Flex (P-123)" and "Dell XPS 15 (P-009)" fail. M: pass when the
  first word is a catalogue brand.
- **T4 (B2, AC2) passes.** "Auralis Home 1 (P-032)", "Kestrel Calm 46
  (P-123)", "auralis-home 1 (P-032)" (case, hyphen), "Go 13 (P-009)", "a
  Kestrel model (P-123)" (brand alone is one word), "P-009 costs 649." (no
  name), "Zephra (P-013)" (one word). M: drop the one-word rule; M: drop the
  tail rule; M: case-sensitive compare; M: no hyphen fold.
- **T5 (B2) whole catalogue name passes `invented`.** "Zephra One Max
  (<P-012's id>)": a run that is another product's whole name is not
  invented (it is `names`' business, T14). M: drop the whole-name rule.
- **T6 (B2) the tail is whole words.** "Go 13 (P-009)" passes; "o 13
  (P-009)" is one word and passes by T4, so use "Pelagic Go (P-009)": a
  prefix, not a tail, fails; "Slate 14 (P-007)" passes (spec's "Slate 14").
  M: tail by character suffix or by prefix.
- **T7 (B3, AC2) misspelling next to its own id.** "Aurelis Home 1 (P-032)"
  passes; the same text with "(P-012)" fails. M: ignore the cited id (compare
  with any catalogue name); M: drop the similarity rule.
- **T8 (B3) digits must be equal.** "Aurelis Home 2 (P-032)" fails (ratio
  0.857 passes alone, so only the digit rule fails it); "Aurelis Home 1
  (P-032)" passes. M: drop the digit rule.
- **T9 (B3, pins the 0.85) threshold on both sides.** "Aurelis Hume 1
  (P-032)" (0.857) passes; "Aurelis Hum 1 (P-032)" (0.815) fails. M:
  `_SIMILARITY = 0.90` fails the first; M: `0.80` fails the second. The test
  also asserts `score._SIMILARITY == 0.85` so a change is a deliberate edit
  with the fixture re-run.
- **T10 (B1, AC3) slot edges, one test per shape.** "I recommend the Kestrel
  Air Plus (P-005)" passes (lead-in is lowercase; run is the own name);
  "I recommend the Acme Foldable (P-004)" fails with run "Acme Foldable" (not
  "I recommend ..."); "The Norvik Fold (P-017)" passes (article dropped);
  "The Acme Foldable (P-004)" fails with run "Acme Foldable";
  "... GPS. The Auralis Tick S (P-025)" passes (sentence break ends the run);
  "1. Acme Foldable (P-004)" fails with run "Acme Foldable" (list marker
  dropped); "**Price:** (P-004)" passes; a run of six capitalised words
  before an id reports the last five. M: no sentence stop (the GPS case
  fails); M: keep the article; M: keep the list number; M: cap 6.
- **T11 (B1, AC3) what is not read.** A name after the id ("P-004 - Acme
  Foldable"), a table cell ("| Acme Foldable | P-004 |"), a name on the
  previous line, and a name before an earlier id ("Acme Foldable P-007 then
  P-004") pass. M: read after the id; M: read across a newline; M: read
  across another id.
- **T12 (B1) markdown and punctuation.** "[Acme Foldable](P-004)" is not a
  slot match (`](` is not in the allowed run); "**Acme Foldable** (P-004)"
  and "\"Acme Foldable\" (P-004)" fail with run "Acme Foldable". M: strip
  fewer trailing characters.
- **T13 (B6, AC4) unknown id and no id.** "Acme Foldable (P-999)" has
  `invented` ok and `grounded` not ok; an answer with no id has `invented`
  ok. M: look the id up without `by_id`.
- **T14 (B6, AC4) independent of `names`.** "Auralis Home 1 (P-009)"
  (another catalogue name): `names` not ok, `invented` ok. "Acme Foldable
  (P-004), not the Auralis Home 1": both fail (the slot is invented even
  though `names` also fires). M: skip when `names` fails (second half); M:
  fail on whole catalogue names (first half).
- **T15 (B5, AC5) order for every case.** The four updated lists at
  `:119,122,286,288` put `invented` right after `names`; a case with
  `expect_ids`, `must_decline` and `expect_properties` also has it (a new
  assertion on the full list). M: append at the end; M: add it only when
  `expect_properties` or `expect_search` is set.
- **T16 (B5) ok reason.** "no invented product name next to a cited id" for
  `GOOD`. M: change the string.
- **T17 (B7) purity and determinism.** Same inputs, same output twice; the
  helper's signature has no question or case parameter
  (`inspect.signature` is exactly `(answer, by_id)`). `tests/test_boundaries.py`
  already covers no new import (`difflib` is stdlib). M: add a parameter.
- **T18 (AC6, replay) the fixture.** For each of the 41 flagged answers,
  `invented_names` returns exactly the recorded `(id, run)` pairs (75 in
  all); the total counts are asserted (41 answers, 75 pairs). M: any slot or
  rule change that flips a verdict. Also asserts that every recorded run is
  not a catalogue name in `catalogue.json`.
- **T19 (AC6, replay) the clean side.** Every clean answer in the fixture
  (a whole Haiku report and the four prototype false-positive answers)
  returns `[]`. M: drop the lead-in, article, own-name-tail or sentence-break
  rule (each turns a fixture answer into a flag).
- **T20 (AC6 literal) one correct, one invented answer** quoted in the test
  file itself, so the pass/fail pair is readable without the fixture.
- **AC7** (README bullet) is a manual check at review. **AC8** is the eval
  run (Validation). AC1 maps to T1-T2, AC2 to T4, T7-T9, AC3 to T10-T12, AC4
  to T13-T14, AC5 to T15, AC6 to T18-T20, B7 to T17, B8 to T15 and the
  README line (`PROPERTIES`, `cases.py` and the judge are untouched: a
  `git diff --stat` at review shows it).

The replay over `evals/runs/` is not a test (the directory is gitignored).
The review repeats it with the same one-off script over all reports and
reports the flagged count against the spec's 41 answers / 75 pairs; the
script is not committed, the fixture test is the standing proof. This is
how the 0.85 is pinned: T9 on both sides, the `_SIMILARITY` constant assert,
and T18-T19.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (or ROUTE with a reason recorded in review.md).
- **Eval run (owed: `score.py` is in `EVAL_PATHS`).** The coordinator runs
  `uv run advisor-eval` on Ollama in the worktree at the reviewed commit,
  then `uv run advisor-analysis compare <report>` against
  `evals/baseline.json`. Every flipped case is re-run with `--only` before it
  is called a regression. Expected: none flips on qwen3:8b (all 41 flagged
  answers already fail on other checks); a PASS to FAIL because an answer
  really invents a product is a "Needs decision". Any case that fails
  `invented` is quoted in the review. The baseline moves after the merge.
- Live check: none. `score.py`, its tests, the fixture and the README are
  not on the live-check path list (`src/advisor/cli.py`, `models/`,
  `tracing.py`, `prompts/`, `infra/`).

## Assumptions I made

- The `invented` check's reasons are the spec's B5 text; the ok reason is
  the spec's string.
- "At most 5 words" is read as the last five words before the id; the
  article and list number are dropped after, so a run is at most five words.
- A word ends the walk if it ends in `. ! ? : ; ,` (after stripping trailing
  `*`), so "**Price:**" and "GPS." both end it.
- An id cited twice with different invented names is reported with the first
  name only (the spec's "each id once, in order of first occurrence").
- The fixture is built from `evals/runs/` as it stands at `ec8036d` and
  stores answer text and expected pairs; it is the standing replay, the full
  replay stays a review step.
- No new dependency: `difflib` is standard library.
- `review_tier` stays empty (spec: `score.py` is not in the "by meaning" list).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-25 - build (subtasks 1-5)

Commits: see `git log` (97b0076 helper, check, tests, fixture; then the README, simplification and hand-over commit).

Shipped: `invented_names` and `_SIMILARITY`/`_MAX_SLOT` in `score.py`, the `invented` check right after `names`, the four name lists updated, T1-T20 in `tests/test_evals_score.py`, `tests/fixtures/invented_replay.json`, the README bullet. `npm run verify` green: 972 pytest, 490 kit tests. Mutants killed by the tests: similarity 0.90 and 0.80, cap 6, no digit rule, no own-name tail. No eval run (the coordinator's).

Divergences:
- Subtasks 1 and 2 were committed together (the check is wired in the same commit as the helper).
- `fold` from §32 exists, but `_norm` is unchanged and the helper uses `_norm` as the plan said. Line numbers shifted; no effect.
- The word-stop set `. ! ? : ; ,` is subsumed by "a word must end in a letter or digit", which also handles `](`. The set was dropped (no behaviour change; the mutant that removed it survived for that reason).
- Replay counts differ from the spec's 41 answers / 75 pairs. On the 35 reports now in the main checkout (4 are newer than the spec's) the helper flags 64 answers / 113 pairs in 16 reports. All 112 pairs but one are names no catalogue has (granite3.3 run `20261124T175356Z` gives 32 answers). The fixture holds 63 answers / 112 pairs. The one left out is a false positive: `20261124T165359Z-ollama.json`, `voice-speaker`, leaked reasoning text "So: Recommend Auralis Home 1 (P-032)" gives the run "Recommend Auralis Home 1" (a capitalised sentence-initial verb joins the own name). The spec's B1/B2 do not drop a capitalised lead-in verb; fixing it needs a decision. The fixture counts (63, 112, 50 clean) are asserted in T18-T19.

### 2026-11-25 - rework, round 1

Commit: see `git log` (the commit after 81e5689).

Owner decision on review finding 1, option (a): in B2 a run that ends in the cited id's own name in whole words (`shown.endswith(" " + own)`) is not invented, so "Recommend Auralis Home 1 (P-032)" passes. Added to `invented_names`, its docstring and the README bullet. "So: Recommend Auralis Home 1 (P-032)" is in `clean` in the fixture (51 clean answers; flagged stay 63 / 112); the fixture note now says what `clean` holds (all of `20261124T192816Z-anthropic.json` plus that one answer, shortened). Literal tests: it passes; "So: Recommend Acme Home 1 (P-032)" is still invented.

Mechanical items: findings 2 to 5 as tests (`test_invented_more_slot_edges`), the section sign restored in both places in `score.py` (no U+FFFD left in the diff), the "word must end in a letter or digit" rule stated in the docstring and the README (finding 7).

Correction to the earlier entry: "all 112 pairs but one" should read: the helper flags 113 pairs on 35 reports, of which 112 are real inventions.

Mutants (copy-backup, apply, full suite with `-x`, restore by copy; each fails a test): remove the new ends-with-own-name clause (fails); `prev_id_bound_off` (fails); `listnum_off` (fails); own-tail by character suffix (fails); `_SLOT_TRAIL` without `[` (fails); without `*` (fails); without the quotes (fails).

Divergence: the review's `assert inv("1 Kestrel Air Plus (P-005)") == []` no longer kills `listnum_off` once the ends-with-own-name rule exists (the run passes either way). I kept it and added `runs("1 Acme Foldable (P-004)") == [("P-004", "Acme Foldable")]`, which does.

### 2026-11-25 - rework, round 2

Commit: see `git log` (the commit after 99bd414). Tests, the fixture note, the README and this entry only; `score.py` is unchanged.

- Two tests in `test_invented_lead_in_before_the_own_name_passes`: "Recommend Xauralis Home 1 (P-032)" (whole words) and "Recommend Auralis Home 1 Max (P-032)" (ends in). Mutants by copy-backup, full suite, restored by copy: `shown.endswith(own)` fails a test; `(" " + own) in shown` fails a test.
- README: the limitation that a word put before the real name ("Norvik Auralis Home 1 (P-032)") passes (owner's decision a); the non-alphanumeric ending characters now listed as in the docstring (`)`, `+`, `%`, `-`).
- Fixture note: the clean answer was shortened and the euro sign written as "euros"; the original is quoted.
- Correction to the round 1 entry: I said the README lines were rewrapped. They are not: README.md:175 is still about 152 characters. The kit test that was red in my first round 1 verify was not reproduced (the reviewer got 490/490 in 4 runs) and I did not keep its output.
