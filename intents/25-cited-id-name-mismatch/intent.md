<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §25 — Catch an answer that cites a real id under another product's name

**Type:** fix
**Originator:** the owner (labelling `gen-out-of-stock-6` on 2026-11-16,
confused by its `prices` message; "fix an answer cites a product id with
another product's name")
**Source:** `evals/runs/20261113T072503Z-ollama.json`, case
`gen-out-of-stock-6`; `intents/8-offline-evals` (the checks)

## Problem

The eval's `grounded` check (`src/advisor/evals/score.py`, `score`) passes
when every cited id **exists** in the catalogue. It never asks whether the
id belongs to the product the answer names next to it.

In `gen-out-of-stock-6` ("I saw the Auralis Home 1 was out of stock…"),
qwen3:8b ran no search and answered "…the product page for the Auralis
Home 1 (P-009)…". P-009 is the Pelagic Go 13 (a €649 laptop, in stock).
The Auralis Home 1 is P-032 (€119 speaker, out of stock). The checks said:

- `grounded`: ok, "every cited id exists" (it is wrong to the customer);
- `prices`: FAIL, "price of P-009 not stated". The failure is right by
  accident and its reason is misleading: it blames a missing price on a
  product the answer never meant, because the out-of-stock exemption does
  not cover the in-stock P-009.

The hole has grown since. In the same run, `gen-out-of-stock-1` cited
"Norvik Fold (P-112)", and `grounded` failed only because the catalogue then
had 32 products. Since §14 it has 500, so P-112 exists and belongs to
another product: the same answer would now pass `grounded`. With ids
`P-001`..`P-500`, almost any id a model invents is a real one.

## Outcome

- An answer that writes a catalogue product's name next to a cited id that
  belongs to a different product fails a check. Its reason names both:
  the id, whose name that id has, and the name the answer gave it (e.g.
  "P-009 is the Pelagic Go 13, cited as Auralis Home 1").
- The `gen-out-of-stock-6` answer above, scored against today's catalogue,
  fails with that reason. An answer that writes "Auralis Home 1 (P-032)"
  does not fail it.
- The 50 committed cases are scored again with a real model (an eval run
  per `REVIEW-POLICY.md` → "Eval runs"), and any case that changes from
  pass to fail or back is explained in the review.

## Constraints

- `score.py` is core code and pure: no model, no files. The check uses only
  the answer text and the catalogue it is given.
- No LLM judge: this is a deterministic check, like the others from §8.
- It must not fail an answer that names a product correctly in another
  form the catalogue allows (case, a hyphen read as a space, the way
  `catalogue._norm` already treats them), nor an answer that cites an id
  with no product name near it.
- Changing `score.py` owes an eval run and possibly a new baseline
  (§17, `REVIEW-POLICY.md` → "Eval runs").
- Out of scope: making the agent itself cite the right id (prompt or tool
  changes); that is a separate intent once this check shows how often it
  happens.

## Type-specific questions

### Fix
- **What broke:** observed: an id cited under another product's name passes
  `grounded`, and another check's reason then points at the wrong product.
  Expected: a failing check that says the id and the name disagree.
- **Since when:** the `grounded` check as specified in §8 ("every cited id
  exists in the catalogue", `intents/8-offline-evals/spec.md:71`). §14 (500 products)
  removed the accidental cover from unknown ids.
- **Impact:** owner-facing, in the evals: a wrong answer can score as
  grounded, and labelling is slowed by misleading reasons. No end user is
  involved (the evals run offline); no data leak.
- **Reproduction:** `score()` on the `gen-out-of-stock-6` question and the
  answer quoted above, with the committed catalogue and no searches.
- **The test that will fail first:** `tests/test_evals_score.py`: a new test
  that scores "the Auralis Home 1 (P-009)" and asserts a failing check whose
  reason names P-009, Pelagic Go 13 and Auralis Home 1; plus one that
  "Auralis Home 1 (P-032)" passes it.

## Assumptions I made

- The fix is a check over the answer, not a change to the agent (see
  out of scope).
- `follows_up: 8`: the gap is in §8's check as specified; §14 made it
  worse but did not cause it.
- Whether this is a new check (e.g. `names-match`) or a stricter `grounded`
  is left to the plan; so is what counts as "next to" (the same parenthesis,
  the same sentence, a window of characters).
- Making the `prices` reason name the product ("price of P-009 (Pelagic Go
  13) not stated") is in scope as a small part of the same fix, since the
  misleading reason is what the owner hit.
