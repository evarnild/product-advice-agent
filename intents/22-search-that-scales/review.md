<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §22 review — Product search that still finds the right product in 500

verdict: rework
tier: reviewed
reviewed-commit: 38e0c836f3d0a2544ef019125ee9fdd155c5fb49
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, set by the path table (`src/advisor/prompts/system.md`,
Reviewed by meaning) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 22` → "nth
attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): F5 |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): F3; eval run owed |
| 4 | Tests prove the behaviour, not only pass | findings (2): F1, F2; 27 mutants, 22 killed, 5 survived |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): F6 |
| 7 | Documentation | findings (1): F4 |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; one proposed) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 22, feature)
  note:  10 file(s), 291 line(s) changed outside intents/.
```

## Behaviour against the spec
- **B1** met: `passes()` (`catalogue.py:134-143`) keeps category, bounds and
  stock; `test_non_keyword_filters_still_exclude_with_keywords`, M15 killed.
- **B2** met in `search_products` (`hits = [(n, p) for n, p in scored if n >
  0 or not words]`, blanks dropped when `words` is built; hyphen as space,
  M14 killed); brand is searched but no longer tested (F1).
- **B3** met: key `(-t[0], t[1].price_eur, t[1].id)`; a keyword counts once
  (`sum(1 for w in words if w in haystack)`), duplicates collapse after
  `_norm` (`dict.fromkeys`); fixtures disagree on count, price and id; M6–M9
  killed.
- **B4** met: clamp unchanged, function default 5, `[:limit]` cuts the
  ranked list (M10–M12 killed).
- **B5** met: `agent.py:114` `limit = args.get("limit", 10)` with the
  planned comment (A1 killed).
- **B6** met: `keywords` "Any one keyword can match; products matching more
  of the keywords come first."; `limit` "1 to 10 (default 10)"; name,
  property keys and result rows unchanged; the tool `description` also
  rewritten (F5).
- **B7** met: three lines inside the existing search bullet, one sentence
  ("Put the words that distinguish what the customer wants (a use such as
  "student" or "running", a feature such as "noise-cancelling") into
  `keywords`; extra keywords no longer empty a search."); no other line
  changed; the whitespace-normalised test still fails on any word change.
- **B8** partly met: `_expected_results` ranks by `(-matched(p),
  p.price_eur, p.id)` and ADR 0003 is updated; it departs from B2 for
  blank-only `keywords_any` (F3); distinct counting unproven (F2).
- **B9** met: `catalogue_problems` stays empty; old vs new, only
  `drawing-tablet`'s expected rank moves (P-022 5th → 1st); no case edited.
- **B10 / AC8**: the live check.
- **AC4** verified: `search_products(category="laptop", max_price=700,
  keywords=["student"])` → `['P-009']`; the tool default returns 10 with
  P-009 10th (10th cheapest of 11 laptops ≤ 700 €: the default of 10 only
  just includes it).
- **AC7** met, with F2's gap: `test_expected_results_match_search_products_on_every_committed_case`.

## Findings
- **F1 HIGH** `tests/test_catalogue.py:167-174`: brand matching is no longer
  proven; M13 (brand dropped from the haystack, `catalogue.py:147`)
  survives. On `main`, `assert ids(search_products(CAT, keywords=["quiet",
  "noise"])) == ["P-004"]` was the only brand-matched assertion (P-004's
  brand is "Quiet"); the diff deleted it with the all-of assertions. B2:
  "in name, brand or description, as today". **Needs rework:** add `assert
  ids(search_products(CAT, keywords=["quiet"])) == ["P-004"]` (or an
  equivalent brand-only match) to `test_keywords_case_insensitive_any_may_match`.
  Must kill M13.
- **F2 HIGH** `src/advisor/evals/cases.py:193-199`,
  `tests/test_evals_consistency.py:122-133`: `_expected_results`' "distinct
  keywords, each counted once" (B8, spec Interpretations) is unproven; C2
  (no dedup) and C6 (count occurrences) survive (`["alpha", "BETA",
  "beta"]` orders the same either way; no product repeats a keyword).
  **Needs rework:** a consistency test mirroring the catalogue tests,
  asserting ids and equality with `search_products(..., limit=10)`:
  `[prod("P-001", 50, desc="alpha beta"), prod("P-002", 10, desc="alpha
  alpha alpha alpha")]` with `keywords_any ["alpha", "beta"]`; and
  `["in-ear", "in ear", "IN EAR", "beta", "gamma"]` over P-001 "beta gamma"
  and P-002 "in-ear". Must kill C2 (`cases.py:193-195`) and C6 (`:199`).
- **F3 MEDIUM** `src/advisor/evals/cases.py:188`: B8 says `_expected_results`
  ranks "the same way as B2-B3", and B2 says only-blank keywords match
  every product; `_expected_results` excludes everything instead.
  `parse_cases` (`cases.py:87-90`) rejects only `""` and `[]`, so
  `"keywords_any": ["-"]` or `[" "]` parses. On the committed catalogue,
  `{category: laptop, max_price: 700, keywords_any: ["-"]}` gives 0 from
  `_expected_results`, 10 from `search_products` (a case with `expect_ids:
  ["P-009"]` would be reported); `main` matched everything here. No
  committed case is affected; C3 survives. **Needs rework:** `if words and
  matched(p) == 0: return False`, plus a test that
  `_expected_results({"keywords_any": ["-"]}, cat)` and `{"keywords_any":
  ["-", "alpha"]}` each equal `search_products(cat, keywords=…,
  limit=10)`. Must kill C3 (`cases.py:194`). (Rejecting blank-only
  `keywords_any` in `parse_cases` instead would be a spec change.)
- **F4 MEDIUM** `src/advisor/evals/prompts/generate.md:24`: the
  question-generation prompt still says a probe's `"keywords"` are "words
  that must all appear", while `coverage._count` now goes through any-of
  `search_products`. Measured: a no-match probe with several keywords now
  matches when any one appears; reclassified kept → dropped in main's
  untracked pools: 3 of 36 in `evals/generated.jsonl` (`gen-no-match-2`,
  `-4`, `-5`), 2 of 51 in `evals/generated haiku.jsonl` (`gen-no-match-1`,
  `-2`). The plan names the risk, not the prompt; the spec keeps coverage on
  `search_products`. **Needs decision:** (a) update `generate.md` to "any of
  these words; a no-match probe must match none of them" (outside the
  plan); (b) give coverage its own all-of probe rule (contradicts the
  spec's assumption); (c) accept the narrower no-match meaning and leave a
  note.
- **F5 LOW** `src/advisor/agent.py:131-132`: the tool `description` the
  model reads was rewritten (not in the plan; recorded in Progress; no
  conflict with B6; the old "All given filters must match … sorted by price"
  would now be false). No test pins it (A4 survives). Worth a look: accept
  it in the Reviewed diff read, optionally pin it in
  `test_schema_text_says_…`.
- **F6 LOW** `plan.md` Progress ("Tests:"): "grew by about 20 tests" and "804
  passed before the last additions"; measured +14 test functions
  (`test_catalogue` +8 −1, `test_agent` +5, `test_evals_consistency` +2),
  807 passed at 38e0c83. **Needs rework:** append "+14 tests (one
  replaced); 807 passed at <commit>" below the marker.

Proposed footgun (pass 9, the owner's call): "a test edit that replaces
assertions must keep every behaviour the removed lines pinned" (F1).

Nit: "extra keywords no longer empty a search" mentions a change the model
never saw; harmless, and B7's own wording.

**Mutants** (backup by copy, `git diff --quiet` ≠ 0, full `uv run pytest
-q`, byte-identical restore):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| M1 no dedup | `catalogue.py:132` | KILLED | `test_repeated_keyword_is_not_a_bigger_match_than_distinct_ones` |
| M2 no blank filter | `:132` | KILLED | `test_blank_keywords_do_not_match_everything_or_count` |
| M3 count occurrences | `:148` | KILLED | `test_a_keyword_counts_once_however_often_it_appears` |
| M4 any→all | `:154` | KILLED | 8 tests |
| M5 no keywords → nothing | `:154` | KILLED | many |
| M6 drop count key | `:155` | KILLED | 8 tests |
| M7 reverse count | `:155` | KILLED | 8 tests |
| M8 drop price key | `:155` | KILLED | 8 tests |
| M9 drop id key | `:155` | KILLED | 3 tests |
| M10 no lower clamp | `:131` | KILLED | `test_limit_default_and_clamp`, `test_limit_cuts_…` |
| M11 no upper clamp | `:131` | KILLED | 3 tests |
| M12 no `[:limit]` | `:156` | KILLED | 7 tests |
| **M13 brand dropped** | `:147` | **SURVIVED** | F1 |
| M14 no `_norm` | `:147` | KILLED | 3 tests |
| M15 stock filter dropped | `:141-143` | KILLED | 3 tests |
| M16 name dropped | `:147` | KILLED | 3 tests |
| A1 tool default 5 | `agent.py:114` | KILLED | 2 tests |
| A2 old keywords text | `agent.py:60-63` | KILLED | `test_schema_text_says_…` |
| A3 "default 5" | `agent.py:66` | KILLED | `test_schema_text_says_…` |
| **A4 old tool description** | `agent.py:131-132` | **SURVIVED** | F5 |
| C1 drop count key | `cases.py:201` | KILLED | 2 tests |
| **C2 no dedup** | `cases.py:193-195` | **SURVIVED** | F2 |
| **C3 no blank filter** | `cases.py:194` | **SURVIVED** | F3 |
| C4 keyword filter removed | `cases.py:188-189` | KILLED | 3 tests |
| C5 drop id key | `cases.py:201` | KILLED | 2 tests |
| **C6 count occurrences** | `cases.py:199` | **SURVIVED** | F2 |
| C7 reverse count | `cases.py:201` | KILLED | 3 tests |

Not mutated: deleting the prompt sentence (reasoned killed: the test
asserts the full sentence). The rework must kill M13, C2, C3, C6.

## For the coordinator (not findings against §22)
- **§15:** `feat/15-fifty-cases` runs `check_coverage` on its 35 probes;
  under any-of, 2 no-match probes fail: `headphones-ldac-balanced-200`
  (`["ldac", "balanced", "in-ear"]`, max 200) and
  `smartwatch-gps-apps-minimalist` (`["GPS", "third-party apps",
  "minimalist"]`, min 150), each now matching 10. Whichever merges second
  gets a red `verify`. §15's `expect_search` cases still pass a
  `catalogue_problems`-equivalent check (only `drawing-tablet` moves, 5th →
  1st). Related to F4.
- **Product risk of any-of** (for the live check): for a no-match question
  ("LDAC balanced in-ear headphones under 200"), the tool now returns up to
  10 partial matches, and the rows don't say how many keywords each
  matched, so the model may present a partial match as a fit. The owner's
  design choice in the spec; listed for the live check.
- **Behind `main`** by 38 commits (§16, §19); `CLAUDE.md` and `README.md`
  changed on both sides; `git merge-tree --write-tree main HEAD` exits 0.

## Not checked
- B10 and the intent's numbers (11/15 on `main` with 32 products, 9/15 on
  500): need a real model.
- The model's behaviour under the new sentence and description, and whether
  it presents partial matches as fits: the live check.
- Token cost of the default rising from 5 to 10 results.
- `advisor-analysis generate` end to end under the new rule (calls a model);
  F4 measured statically on the existing probe files.
- Mutants beyond the changed lines; the prompt-sentence deletion reasoned.
- `CLAUDE.md` calling `evals/generated.jsonl` committed data (untracked on
  both sides; predates §22; §15 corrects it).

## Live check
- owed: rule 1 (`src/advisor/prompts/system.md`), AC8/B10, and rule 3 for
  "the model presenting partial matches as fits".
- steps:
  1. Start Ollama with the default model (README "Evaluating answers").
  2. On `main`, in `C:/Users/eric/src/product-advice-agent` (no branch
     change), `uv run advisor-eval --provider ollama` three times; note the
     three `evals/runs/<stamp>-ollama.json` paths.
  3. In `C:/Users/eric/src/product-advice-agent-wt/22-search-that-scales`
     at the reviewed commit, the same three times; copy the three reports to
     the main checkout's `evals/runs/`.
  4. Tally per case by majority: for each report, `uv run python -c "import
     json,sys; r=json.load(open(sys.argv[1],encoding='utf-8')); print({c['id']:
     c['status'] for c in r['cases']})" <report>`; a case passes on a side
     when PASS in at least 2 of its 3 runs.
  5. In the worktree, `uv run advisor "I want in-ear headphones with LDAC
     and a balanced output, under 200 euros"` and read the answer.
- you should see: `student-laptop` and `nc-headphones-under-200` PASS in at
  least 2 of 3 branch runs; no case passing on `main` (2 of 3) failing on
  the branch (2 of 3); in step 5, the answer cites only returned products
  and does not claim one has all three features unless its text says so.
  The six report names go in the review; then `live_checked`.

## Eval run
owed: `uv run advisor-analysis owes-run --base main` → `src/advisor/agent.py`,
`src/advisor/catalogue.py`, `src/advisor/evals/cases.py`,
`src/advisor/prompts/system.md`. **Not made this round:** the verdict is
rework and F3 changes `src/advisor/evals/cases.py`, so a run now would not
be of the content that ships. The coordinator makes it, in the worktree,
on the reviewed commit of the first round whose verdict is not rework, and
compares it with `evals/baseline.json`; a flipped case is re-run with
`--only` before it is called a regression.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 38e0c83; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "173 files already formatted"; mypy "Success: no
  issues found in 31 source files"; "807 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "10 file(s), 291
  line(s)". Matches.
- **Coordinator, re-run:** survivors M13, A4, C2, C3, C6 each SURVIVED (807
  passed). Matches the reviewer.

**Reviewer, verified:** verify (kit 298/298, pytest 807), check:intent,
sampling, `owes-run`; 27 mutants; throwaway scripts against the real modules
and committed catalogue: the F3 divergence (0 vs 10), AC4's data, old vs new
expected ranks for the committed and §15 cases, old vs new `check_coverage`
on main's two pools and §15's 35 probes (main's `catalogue.py` via `git
show`), the test delta (+14); `git diff main...HEAD` read in full
(`system.md` adds only the sentence; `metadata.yml` only `status`,
`auto_round`, `auto_stopped`); no remote branch; main checkout untouched.

**Taken on trust:** the Progress entry's commit list (its mutant claims were
re-run, not trusted; they agree except the test counts, F6).
