<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §13 — Catalogue changes cannot silently break the eval set

**Type:** feature
**Originator:** the owner, 2026-11-13: "how should we deal with catalog
changes in general?", then "draft both intents" (this one and §14)
**Source:** the coordinator's answer in that conversation (stable ids, a
catalogue hash on every run, a consistency test in `verify`, a written rule
for edits); the week's objective "Test set and evaluation: 50 real-looking
questions with expected behaviour … run on every change"

## Problem

The catalogue (`src/advisor/data/catalogue.json`, 32 products) is an input
to every eval, but nothing ties the two together beyond product ids:

- `evals/cases.jsonl` names products in `expect_ids` and `forbid_ids`, and
  those lists assume prices and stock ("P-005 is under 200 and in stock").
  `parse_cases` only checks that an id exists (`src/advisor/evals/cases.py:67`:
  `raise fail(key, f"names unknown product id '{i}'")`). A price or stock
  edit that makes a case's expected answer wrong passes `verify` and shows
  up later as a model "failure" that is really a stale case.
- The run report records `cases_sha256` and `prompt_sha256`
  (`src/advisor/evals/run.py:310-311`) but nothing about the catalogue. A
  run, its labels (`evals/labels/*.jsonl`) and its taxonomy counts cannot
  say which catalogue the answers were given against.
- There is no written rule for catalogue edits: whether ids may be reused
  or renumbered, how a product leaves, which edits are small and which need
  a spec, and whether an edit owes an eval run. `docs/decisions/0001-stack.md`
  only says "a small committed JSON catalogue".
- §14 (grow the catalogue to 500 products) would change dozens of correct
  answers at once with no way to see which.

## Outcome

- **A stale case fails `verify`.** For every case in the committed
  `evals/cases.jsonl` with `expect_search`, a test runs those filters
  through `search_products` on the shipped catalogue and fails, naming the
  case and the id, when an `expect_ids` product is not returned or a
  `forbid_ids` product is. Any case the test finds broken today is fixed in
  this change.
- **Every run says which catalogue it used.** The run report gains
  `catalogue_sha256` next to `cases_sha256` and `prompt_sha256`.
- **The rule is written down** (an ADR `docs/decisions/0003-…` and a short
  README section): ids only grow and are never reused or renumbered; how a
  product is retired; which catalogue edits are an adjustment and which a
  feature; that a catalogue change owes an `advisor-eval` run whose report
  the review cites; that old labels stay valid as records of their run and
  are not redone.

## Constraints

- No model call in the suite; the new test is deterministic over the
  shipped files. No new dependency.
- `cases.py` and `score.py` are core code (`CORE_CODE`); if the spec puts
  logic there it is tested like the rest of it.
- Existing run reports and label files are not rewritten: a report without
  `catalogue_sha256` stays readable by `advisor-analysis`.
- An edit to `REVIEW-POLICY.md` (if the spec puts the "owes an eval run"
  rule there) makes this intent Reviewed tier.
- Out of scope: growing the catalogue (§14), new categories or fields, the
  LLM judge, CI.

## Type-specific questions

### Feature
- **Users:** the owner, who writes cases, labels runs and edits the
  catalogue; the reviewer, who needs to know whether a catalogue change
  broke cases.
- **What exists today:** id-existence validation in `parse_cases`; a test
  that the committed cases parse and cover every category
  (`tests/test_evals_cases.py`); hashes of the cases and the prompt in the
  run report.
- **Open design questions:**
  1. Where the "owes an eval run" rule lives: `REVIEW-POLICY.md` (enforced
     by review, Reviewed tier) or the ADR and README only.
  2. Retirement: keep the product with a flag (a new field, core code) or
     delete it and leave the id as a permanent hole.
  3. Cases without `expect_search` (declines, `must_decline`): skipped by
     the test, or checked another way.
  4. Whether to add property-style expectations now ("cites only in-stock
     products under the budget") so cases survive catalogue growth, or
     leave that to the 50-case intent.
  5. Whether §9's coverage probes (`evals/generated.jsonl` notes) are
     checked too, or only `cases.jsonl`.

## Assumptions I made

- It is a **feature**, not an adjustment: it adds a test, a report field,
  an ADR and README text, and may touch core code (`cases.py`), which an
  adjustment may not.
- The test covers `evals/cases.jsonl` only; `evals/generated.jsonl` is not
  committed today (it is untracked in the main checkout, although
  `CLAUDE.md` calls it committed data).
- `catalogue_sha256` hashes the file's bytes, like the two existing hashes.
- `review_tier` is left to the path table; it rises to Reviewed if the spec
  edits `REVIEW-POLICY.md`.
- It ships before §14, so §14's growth is checked by it.
