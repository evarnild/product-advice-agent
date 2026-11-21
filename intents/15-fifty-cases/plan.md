<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §15 plan — A committed set of 50 real-looking eval questions with expected behaviour

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Grow `evals/cases.jsonl` from §8's 15 to 50 cases, each with `dimensions`
and expected behaviour the code checks can score, so that the code checks
(and the §16 judge) run on a varied, catalogue-consistent set of 50. Two
property expectations (`cites_a_match`, `cites_only_matches`) let a case
say "cites a fitting product" without fixing ids, so cases survive catalogue
growth. §13's consistency test keeps all 50 honest, and a test pins the
spread.

## Risks

- **Two definitions of "fits" drifting apart.** §13's `_expected_results`
  already decides which products satisfy an `expect_search`. B2's "fits"
  must be the same rule; a second copy in `score.py` would drift. Mitigation:
  one predicate in `cases.py`, used by both (subtask 1).
- **§22 edits the same code.** §22's spec (B8) changes how
  `_expected_results` ranks keyword matches; §15 extracts its filter. They
  are not blocked on each other; whichever merges second rebases. The
  extraction keeps the filter separate from the ordering, so §22's ordering
  change touches only the `sorted(...)` key.
- **Tests that pass whatever the code does.** The spread test (B7) and the
  probe test (below) read the committed file; a mutant in the data would
  only be caught if the bounds are exact. Each bound gets a boundary test
  on an in-test case list, not only the committed file.
- **Model-written questions that only look rewritten.** The probe test
  re-checks each new case's probe against the 500-product catalogue, and
  for `spelling-differs` that the rewritten question still lacks the
  keyword verbatim (`check_coverage` does both). Real-lookingness is the
  owner's live check (AC6).
- **Generated pool files committed by accident.** They are untracked in the
  main checkout; the coordinator copies them into the worktree for the
  implementer, who never `git add`s them. The coordinator deletes the
  copies before the ship (an untracked file blocks worktree removal).
- **Stale line citations**: every `path:line` below was re-read at
  `17e69a4`; the implementer re-checks before editing.
- **The eval run** (§17): `cases.py` (and `evals/cases.jsonl`) are eval
  paths, so the review makes an Ollama run on the 50, and `/ship` writes
  the baseline from it. The 50-case run is new: `compare` will show 35
  cases "added", which is expected, not a finding.
- **Repository footguns** (`REVIEW-POLICY.md` pass 9): the list is empty.

## Verified against the codebase

Re-read on `main` at `17e69a4`.

- `src/advisor/evals/cases.py:13` — `SEARCH_CONSTRAINTS = ("category", "max_price", "min_price", "in_stock_only", "keywords_any")`.
- `src/advisor/evals/cases.py:14-23` — `_FIELDS`, the eight case fields; B1 adds `expect_properties`.
- `src/advisor/evals/cases.py:26-34` — `SCENARIOS`, the seven.
- `src/advisor/evals/cases.py:42-51` — `Case`, a frozen dataclass; B1 adds `expect_properties: tuple[str, ...] = ()`.
- `src/advisor/evals/cases.py:114-166` — `parse_cases`; `fail(fld, why)` gives "line N, case 'id': field 'f' …" (`:130-131`); `expect_search` is parsed at `:159`.
- `src/advisor/evals/cases.py:169-191` — `_expected_results`: the filter `ok(p)` (`:172-189`, category equal, bounds inclusive, `in_stock_only`, `keywords_any` any-of over `_norm(name brand description)`), then `sorted` by `(price_eur, id)` (`:191`).
- `src/advisor/evals/cases.py:194-221` — `catalogue_problems`, the §13 check; B4 adds one message here.
- `src/advisor/evals/score.py:11` — imports `Case` from `advisor.evals.cases` (so `score.py` may import the predicate too).
- `src/advisor/evals/score.py:87-180` — `score`: checks `grounded`, `prices`, `expected`, `forbidden`, `declines`, `stock`, `search`; B3 adds `a-match`, `only-matches` after `search`.
- `src/advisor/evals/score.py:29-31` — `cited_ids`.
- `src/advisor/evals/run.py:281, 354` — `checks = score(...)`; the report lists checks generically by name, so B3 needs no `run.py` change.
- `src/advisor/evals/coverage.py:19-24` — `PERSONAS`, four.
- `src/advisor/evals/coverage.py:54-78` — `Probe`; `to_note()` gives `probe: {json}`.
- `src/advisor/evals/coverage.py:85` — `parse_probe(raw)` takes a dict, returns `Probe | None`.
- `src/advisor/evals/coverage.py:123-160` — `check_coverage(scenario, probe, question, catalogue)`.
- `src/advisor/catalogue.py:15-24` — `CATEGORIES`, eight; `:27` `MAX_LIMIT = 10`; `:109` `_norm`.
- `tests/test_evals_cases.py:19-24` — `load_committed`; `test_committed_file_validates_and_has_12_to_20_cases` (`assert 12 <= len(...) <= 20`), replaced by B7.
- `tests/test_evals_cases.py:27-45` — two committed-file tests that keep holding (the 15 keep their ids and expectations).
- `tests/test_evals_cases.py:160-163` — `test_committed_cases_are_consistent_with_the_catalogue` (§13's test on the committed file).
- `tests/test_evals_consistency.py` — §13's unit tests for `catalogue_problems`; AC3 goes here or in `test_evals_cases.py`.
- `tests/test_evals_score.py:117` — `test_checks_only_apply_when_the_case_asks`.
- `evals/cases.jsonl` — 15 lines, no `dimensions`.
- `evals/generated.jsonl` (36 lines) and `evals/generated haiku.jsonl` (51 lines) — untracked in the main checkout; each line has `id`, `question`, `dimensions`, `note: "probe: {…}"`.
- `CLAUDE.md:197` — "Committed data: `evals/generated.jsonl`, …" (B9).
- `README.md:215` — "Read and edit `evals/generated.jsonl` before you use it." (B9: it is a generated pool, not committed.)
- `src/advisor/evals/baseline.py` `EVAL_PATHS` — includes `src/advisor/evals/cases.py`: the review owes an eval run (§17).

## Subtasks

1. **One "fits" predicate (B2).** In `cases.py`, lift `_expected_results`'s
   inner `ok` into a module function `fits(product, search) -> bool` with
   the same body and comments; `_expected_results` filters with it and keeps
   its ordering. No behaviour change: §13's tests stay green. Commit.
2. **`expect_properties` (B1, AC1).** `PROPERTIES = ("cites_a_match",
   "cites_only_matches")`; `_FIELDS` gains `expect_properties`; `Case` gains
   `expect_properties: tuple[str, ...] = ()`; a `_properties(raw, fail)`
   parser rejects a non-list, an empty list, a non-string or unknown name, a
   repeat, and a property on a case without `expect_search` (each through
   `fail`, naming line, case and field). Tests first. Commit.
3. **The two checks (B3, AC2).** In `score.py`, after `search`: for
   `cites_a_match`, check `a-match` (ok when at least one cited id that
   exists in the catalogue `fits`; reason names the cited ids otherwise, or
   "cites no product"); for `cites_only_matches`, check `only-matches` (ok
   when every cited, existing product `fits`; reason names the misfits).
   Cited unknown ids are left to `grounded`. A case without properties gets
   exactly today's checks. Tests first. Commit.
4. **The consistency rule (B4, AC3).** In `catalogue_problems`, a case with
   `cites_a_match` whose `_expected_results` is empty gives "case '<id>': no
   product fits expect_search, so cites_a_match cannot pass". (Reading of
   "fits no product in the first `MAX_LIMIT`": any fitting product is in the
   first `MAX_LIMIT` of the ordered list, so the rule is "the list is
   empty"; comment at the site.) Test first. Commit.
5. **Dimensions on §8's 15 (B5).** Add `dimensions` to each of the 15:
   `feature` from its category (or `off-topic`), `scenario` read from its
   question and expectations, a `persona` from `PERSONAS`. Ids, questions
   and expectations unchanged. List the 15 assignments in Progress. Commit.
6. **The 35 new cases (B5, B6, B8).** From the two generated files (copies
   in the worktree, untracked, never committed):
   - pick candidates whose probe still passes `check_coverage` for its
     scenario on the committed 500-product catalogue;
   - rewrite each question to read like a customer, keeping what the probe
     expresses (for `spelling-differs`, the question still must not contain
     the probe keyword verbatim);
   - fill expectations by B6's table: `expect_search` from the probe
     (`keywords` → `keywords_any`), `expect_ids` / `cites_a_match` /
     `cites_only_matches` / `must_decline` by scenario;
   - id: a short kebab-case slug, unique;
   - `note`: `source: <generated id>; probe: <the probe JSON, as
     Probe.to_note writes it>; variety: <typo|multi|vague|casual, comma
     separated, or none>`, so the review and the tests can read them;
   - meet B7's spread and B8's variety counts.

   `catalogue_problems` on the file must be empty. Commit (more than once
   is fine).
7. **The spread and the probes (B7, AC4).** Replace
   `test_committed_file_validates_and_has_12_to_20_cases` with tests that:
   - the file has exactly 50 cases, all with `dimensions`, unique ids and
     questions, every `persona` in `PERSONAS` (`off-topic` cases too);
   - every scenario is present, off-topic 2–4, every other 5–12;
   - each of the 8 categories is a `feature` at least 4 times;
   - B8: at least 5 cases each of `typo`, `multi`, `vague`, `casual` in the
     `variety:` part of `note`;
   - every case whose `note` has `probe:` passes `check_coverage` for its
     scenario on the committed catalogue (this is B6, enforced);
   - exactly 35 cases carry `source:` in `note`.

   Each bound helper gets a boundary test on an in-test list (4/5 and
   12/13, 1/2 and 4/5 for off-topic, 3/4 per category). Commit.
8. **Docs (B9).** `CLAUDE.md:197` and README "Error analysis": the
   generated files are a generated pool, not committed;
   `evals/cases.jsonl` holds the 50 (with `expect_properties` described
   in README's case format). Commit.
9. **Hand-over.** `npm run verify` green, `npm run check:intent` PASS,
   `status: in-review`, a Progress entry: commits, test counts, the 15
   dimension assignments, the 35 sources (generated id → new id), the
   spread and variety counts.

## Tests

- **B1/AC1** (`tests/test_evals_cases.py`): a valid list parses to a tuple;
  each bad input raises with line, case and field: an unknown name, a
  repeat, a non-list, an empty list, a non-string, a property without
  `expect_search`. Mutants killed: dropping any one rejection branch;
  accepting a third name in `PROPERTIES`.
- **B2** (`tests/test_evals_consistency.py`, existing): §13's tests now go
  through `fits`; plus one direct `fits` test per constraint kind
  (category, `max_price` and `min_price` inclusive at the boundary,
  `in_stock_only` true and false, `keywords_any` any-of and
  hyphen-insensitive, in brand and description). A mutant in any branch of
  `fits` fails at least one.
- **B3/AC2** (`tests/test_evals_score.py`, in-test catalogue): `a-match` ok
  with one fitting cited id among misfits; not ok when none fits (reason
  names the cited ids) and when nothing is cited; `only-matches` ok when all
  fit; not ok naming exactly the misfit; an unknown cited id is ignored by
  both; a case without properties gets the same check names as today
  (extends `test_checks_only_apply_when_the_case_asks`). Mutants: `any` ↔
  `all`, dropping the existence filter, emitting a check without its
  property.
- **B4/AC3**: one problem naming the case when nothing fits a
  `cites_a_match` case; none when one product fits; none for a
  `cites_only_matches`-only case with nothing fitting.
- **B5–B8/AC4**: subtask 7's tests on the committed file, plus the boundary
  tests on in-test lists.
- **§13 on the committed file** (`test_committed_cases_are_consistent_with_the_catalogue`): stays green with 50.
- No model call anywhere; the suite stays offline (`tests/conftest.py`).

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS.
- **Eval run** (§17, owed: `src/advisor/evals/cases.py`): the coordinator
  runs `uv run advisor-eval` on Ollama in the worktree at the reviewed
  commit and compares with `evals/baseline.json` (35 cases "added"
  expected); `/ship` writes the new baseline from it.
- **Live check** (owed, rule 3, AC6): the owner reads all 50 questions and
  expectations in the worktree's `evals/cases.jsonl`, edits any, and runs
  `uv run advisor-eval` once on the default model; the review quotes the
  pass rate. If the owner edits cases, the edits are a commit the next
  review round covers.

## Assumptions I made

- **One predicate:** B2's "fits" is `_expected_results`'s filter, lifted
  out unchanged; §13 B2 and this spec's B2 describe the same rule.
- **B4's "first `MAX_LIMIT`"** reduces to "nothing fits" (see subtask 4).
- **`a-match` with no cited product** is not ok ("cites no product").
- **Cited unknown ids** are ignored by both property checks; `grounded`
  already fails them.
- **The `note` format** (`source: …; probe: …; variety: …`) is mine, so the
  spec's AC5 count and B6's probe check can be tests, not only review
  reading. §8's 15 keep their notes; they get no `source:`.
- **Variety tags:** `typo`, `multi` (two or more constraints), `vague` (no
  category word), `casual` (casual or follow-up register).
- **Scenario of §8's 15** is assigned by the implementer from each case's
  question and expectations, and listed in Progress for the review.
- **The pool copies** sit untracked in the worktree's `evals/` during the
  build and are deleted by the coordinator before the ship.
- **Tier:** the path table decides (`review_tier` empty); `cases.py` and
  `score.py` are core code.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
