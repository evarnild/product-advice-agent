<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §26 — Two headphone cases fail correct answers

**Type:** adjustment
**Originator:** the owner ("draft an intent to loosen those two cases", after
the Haiku run on 2026-11-24)
**Source:** `evals/runs/20261124T192816Z-anthropic.json` (claude-haiku-5-5,
48/50); cases 1 and 28 of `evals/cases.jsonl`

## Problem

Haiku failed two of the 50 cases with answers a reader would accept.
In both, what failed is the case's expectation, not the answer.

- **`nc-headphones-under-200`** ("I need noise-cancelling headphones under
  200 euros", `evals/cases.jsonl:1`) expects both P-005 and P-001
  (`"expect_ids": ["P-005", "P-001"]`). Haiku searched for
  `noise-cancelling` under €200 and listed four in-stock matches: P-001,
  P-403, P-355 and P-123. It flagged three more as out of stock. It left
  out P-005 (Kestrel Air Plus, €129, in-ear), and `expected` failed:
  "does not cite P-005". The case dates from §7, when the catalogue had 32
  products and P-005 and P-001 were the only fits. With 500 products
  (§14) there are many fits, and naming any of them answers the question.
- **`headphones-hifi-transparent-200`** (a no-match case, `:28`) expects a
  search with `keywords_any: ["noise cancellation", "transparent mode"]`.
  The search check passes when a wanted phrase appears *inside* a keyword
  the agent sent (`score._call_satisfies`). Haiku searched twice, with
  `["noise-cancelling", "transparent", "high-fidelity"]` and then
  `["transparency", "ambient", "hi-fi", "hifi"]`. Neither contains "noise
  cancellation" or "transparent mode", so `search` failed. Its answer was
  right: nothing lists a transparency mode, said plainly, with the in-stock
  noise-cancelling options as alternatives. qwen3:8b passes only because
  it sends the literal phrase `transparent mode`.

A case that fails a good answer makes the eval read worse than it is. It
also hides the comparison between models: Haiku's 48/50 is really 50/50 on
these two.

## Outcome

- `nc-headphones-under-200` passes an answer that cites any in-stock
  noise-cancelling headphones under €200, and still fails one that cites
  P-003 (forbidden), cites a product that doesn't fit, or cites nothing.
- `headphones-hifi-transparent-200` passes a search for the
  transparency feature in any of its usual words ("transparent",
  "transparency", "ambient"), and still fails a search without it.
- Haiku's two answers in `20261124T192816Z-anthropic.json`, re-scored
  against the changed cases, pass. qwen3:8b's committed baseline answers
  for both cases still pass.
- `npm run verify` stays green, including the catalogue consistency test
  (`tests/test_evals_cases.py::test_committed_cases_are_consistent_with_the_catalogue`).

## Constraints

- Data only: two lines of `evals/cases.jsonl`. No change to `cases.py` or
  `score.py` (core code), so it stays an adjustment.
- `evals/cases.jsonl` is in REVIEW-POLICY.md's "Eval runs" list, so an eval
  run is owed on Ollama, and the baseline moves after the merge.
  `cases_sha256` changes, so later `compare` output warns against the old
  baseline until then.
- Old run reports and labels are records of their run and are not
  re-scored or edited (docs/decisions/0003, "Old records").
- Out of scope: the other 48 cases, and whether the search check should
  test keywords at all.

## Type-specific questions

### Adjustment
- **Exactly what changes:**
  - `nc-headphones-under-200`: drop `expect_ids` and add
    `"expect_properties": ["cites_a_match", "cites_only_matches"]` against
    the existing `expect_search` (`category: headphones`, `max_price: 200`,
    `keywords_any: ["noise"]`). Keep `forbid_ids: ["P-003"]`. Update the
    `note` to say why.
  - `headphones-hifi-transparent-200`: `keywords_any` becomes
    `["transparen", "ambient"]`, matched as a substring of a sent keyword.
    Category and `max_price` stay. Update the `note`.
- **Blast radius:** 1 file (`evals/cases.jsonl`), 2 lines, plus the intent
  folder. Within 5 files and 60 lines, and no core code.

## Assumptions I made

- **`cites_only_matches` too, not only `cites_a_match`.** The question asks
  for noise-cancelling headphones under €200, so an answer that also cites
  something that doesn't fit should fail. But Haiku flagged out-of-stock
  fits (P-004, P-387, P-379), and they fit `expect_search`, which has no
  `in_stock_only`. So they pass `cites_only_matches`, and the `stock`
  check still demands that they are flagged.
- **`"noise"` stays the keyword for case 1.** `fits` matches it against
  name, brand and description, as `search_products` does. Whether every
  noise-cancelling product says "noise" there is checked by the
  consistency test once the case has properties. If some fit doesn't,
  that is a catalogue question, not this intent's.
- **The stem `"transparen"`** covers "transparent" and "transparency" as a
  substring. `"ambient"` covers "ambient mode" / "ambient sound". "Noise"
  is dropped from case 2's keywords because it would let a search without
  the distinguishing feature pass. The case is about the transparency
  mode that nothing has.
- **Adjustment, not fix.** Nothing in the code is wrong; two data
  expectations were written for a 32-product catalogue and one model's
  wording.
- **`review_tier` left empty.** `evals/cases.jsonl` is not in the "by
  meaning" list.
- Nothing blocks this.
