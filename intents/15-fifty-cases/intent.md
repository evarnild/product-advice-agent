<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §15 — A committed set of 50 real-looking eval questions with expected behaviour

**Type:** feature
**Originator:** the owner, 2026-11-13: "/intent 50 real looking questions"
**Source:** the week's objective "Test set and evaluation: 50 real-looking
questions with expected behaviour; code-based checks first, then one
LLM-as-judge that you validate against your own labels on 30 cases; run on
every change"; the coordinator's gap list in the same conversation; §8
(cases and code checks), §9 (generated questions), §13 and §14 (catalogue)

## Problem

The eval set the code checks run on is too small and the larger sets carry
no expected behaviour:

- `evals/cases.jsonl` (committed, §8) has **15** hand-written cases with
  expected behaviour (`expect_ids`, `forbid_ids`, `expect_search`,
  `must_decline`) but no `dimensions`, so §9's counts cannot slice them.
  `tests/test_evals_cases.py` pins its size:
  `test_committed_file_validates_and_has_12_to_20_cases`.
- §9's `advisor-analysis generate` wrote `evals/generated.jsonl` (36) and
  the owner has a second set, `evals/generated haiku.jsonl` (51). Both have
  `dimensions` and a probe `note` but **no expected behaviour**, are
  model-written rather than real-looking, and are **untracked** in the main
  checkout, although `CLAUDE.md` lists `evals/generated.jsonl` as committed
  data. README says to "Read and edit `evals/generated.jsonl` before you
  use it."
- The scenario spread is uneven (generated: budget-too-low 13,
  out-of-stock 8, several-matches 6, no-match 5, exact-match 2, off-topic 2;
  `spelling-differs` kept 0 of 10 in the first run).

So the code checks cover 15 questions, and the LLM judge planned next has
no 50-question set to run on.

## Outcome

- **50 committed cases** in one file `advisor-eval` runs by default, each
  with an id, a question, `dimensions` (feature, scenario, persona) and
  expected behaviour that the §8 code checks can score: `expect_search`
  plus `expect_ids` / `forbid_ids`, or `must_decline`.
- **Real-looking:** the owner has read and edited every question, and the
  set includes the ways customers actually write (vague, several
  constraints, typos and spelling variants, follow-up-style phrasing,
  off-topic).
- **Spread:** every catalogue category and every §9 scenario appears, with
  no scenario above a share the spec sets.
- **Checked against the catalogue:** all 50 pass §13's consistency test,
  so a later catalogue change that breaks one fails `verify`.
- **A baseline:** one `advisor-eval` run on the 50 with the default model,
  its pass rate quoted in the review.

## Constraints

- Synthetic only: no real customer data; questions may be drafted by a
  model, but each is owner-edited before it is committed.
- No model call in the suite; the code checks stay deterministic.
- The case format (`cases.py`, core code) changes only if the spec decides
  a new expectation is needed.
- Order: after §13 (consistency test), and after §14 if the 50 are written
  against the 500-product catalogue.
- Out of scope: the LLM judge and its 30-label validation, running evals on
  every change, the catalogue itself.

## Type-specific questions

### Feature
- **Users:** the owner, who runs and labels evals; the coming LLM judge,
  which runs on this set.
- **What exists today:** 15 cases with expectations; 36 + 51 generated
  questions without; §9's `generate` and coverage check, which already
  confirm a question's probe against the catalogue.
- **Open design questions:**
  1. One file of 50 (grow `cases.jsonl`, keep the §8 15 as part of it) or
     two files (the 15 plus a new 35).
  2. Where the 35+ come from: picked and edited from the two generated
     files, freshly written by the owner, or a new `generate` run against
     the 500-product catalogue.
  3. How expected behaviour is filled for model-written questions: by
     hand, or derived from the §9 probe (`note: probe: {…}`) and then
     confirmed by the owner.
  4. Property-style expectations (e.g. "cites only in-stock products under
     the budget") instead of fixed id lists, so cases survive catalogue
     growth (§13 question 4).
  5. The size bound in `test_committed_file_validates_and_has_12_to_20_cases`
     and the per-scenario share.
  6. Whether `evals/generated.jsonl` gets committed (as `CLAUDE.md` says)
     or the claim is corrected.

## Assumptions I made

- It is a **feature**: it changes committed eval data, a test bound and
  possibly the case format (core code), and needs a spec on the open
  questions. No question round was asked; the open points above go to the
  spec.
- "Real-looking" means owner-edited, varied customer phrasing, not data
  from real users (there are none).
- The 50 are written after §14, against the 500-product catalogue, so the
  expected ids are not redone right after.
- §8's 15 cases are kept and count toward the 50.
- `review_tier` is left to the path table (eval data and tests).
