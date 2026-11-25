<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §35 — Catch an answer that names a product the catalogue does not have

**Type:** feature
**Originator:** the coordinator's analysis of 10 qwen3:8b eval runs of the
50 cases, for the owner ("write intents")
**Source:** `evals/runs/20261124T215703Z-ollama.json` (latest) and the nine
earlier qwen3:8b runs since `20261121T125003Z`;
`intents/25-cited-id-name-mismatch` (the `names` check)

## Problem

The deterministic checks do not notice an invented product name. In the
latest run two answers present made-up products next to real ids:

- `norvik-fold-brother-gift`: "1. **Acme Foldable (P-004)** - €399.00" and
  "2. **TechFold Pro (P-007)** - €429.00". P-004 is the Sonavo Quiet Pro
  (on-ear headphones, €159); P-007 is the Norvik Slate 14 (a laptop, €899).
- `aurelis-home-gift-mum`: "**Aurelis Home 2 (P-012)** - €299.00 (In
  stock)" and "**Aurelis Home 3 (P-013)** - €349.00 (In stock)". P-012 is
  the Tolvane Chrome 11 (a laptop); P-013 is the Zephra One (a phone).

Both answers ran no search (`searches: []`). Their checks said `grounded`:
"every cited id exists" and `names`: "every cited id sits with its own
name or none". Both cases failed only on `prices` and `expected`.

`grounded` asks only whether a cited id exists. `names` (§25, `misnamed`
in `src/advisor/evals/score.py`) fails an id written next to **another
catalogue product's** name:

```python
near = [shown[n] for a, b, n in mentions if a >= lo and b <= hi]
own = _norm(by_id[pid].name)
if near and own not in {_norm(n) for n in near}:
```

`mentions` are matches of catalogue names only, so a name the catalogue
does not have is never seen, and `near` is empty.

It is not a one-off. A rough scan of the 10 qwen3:8b runs (a name of up to
five words written right before an id, not a catalogue name) finds an
invented name next to a real id in all 10, always in these two
out-of-stock cases (`aurelis-home-gift-mum` in 10, `norvik-fold-brother-gift`
in 8): for example "Eclipse Flex (P-123)", "Norvik Lite
(P-124)", "Aurelis Home 2 (P-002)". Those cases fail on other checks
today, so the run totals hide it. An answer that invents names and states
their prices correctly would pass.

The LLM judge does not cover it. `judge-no-fit` scores only
`no-match` and `budget-too-low` cases (`IN_SCOPE_SCENARIOS` in
`src/advisor/evals/judge.py`). Both cases are `out-of-stock`. Its rule
(a) would fail "a product that no search returned", but it never sees
these answers.

## Outcome

- An answer that presents a product name the catalogue does not have
  next to a cited id fails a deterministic check. The reason names the id,
  that id's real name and the name the answer used (e.g. "P-012 is the
  Tolvane Chrome 11, cited as Aurelis Home 2").
- The four lines quoted above, scored against today's catalogue, fail
  that check. "Auralis Home 1 (P-032)", "Kestrel Calm 46 (P-123)", an id
  with no name near it, and a name in another catalogue-allowed form (case,
  a hyphen read as a space) do not fail it.
- The 50 cases are scored again with a real model (an eval run per
  `REVIEW-POLICY.md` → "Eval runs"), and every case that changes between
  pass and fail against the baseline is explained in the review.

## Constraints

- `score.py` is core code and pure: no model, no files. The check uses
  the answer text and the catalogue it is given (and, if the spec needs it,
  the case's question).
- Deterministic, like the §8 checks; no LLM judge.
- It must not fail ordinary prose: brands, categories, feature words,
  bullet labels and the customer's own words.
- Changing `score.py` owes an eval run, and the baseline may move
  (`EVAL_PATHS` in `src/advisor/evals/baseline.py`). Old run reports and
  labels are not re-scored or edited (docs/decisions/0003, "Old
  records").
- Out of scope: stopping the agent from inventing names (a prompt or
  agent change; §31 covers searching before answering), and the judge's
  scope.

## Type-specific questions

### Feature
- **Users:** the owner, reading eval runs and labelling failures.
- **What exists today:** `grounded` (the id exists) and `names` (the id is
  not next to another catalogue product's name). Nothing reads a name the
  catalogue lacks.
- **Open design questions:**
  - **Scope of a "name".** Only a name next to a cited id that is not that
    id's name (the shape in the evidence), or any product-like name
    anywhere in the answer, with or without an id?
  - **What is a product name.** How to tell "Acme Foldable" from ordinary
    capitalised words ("Both", "Unfortunately", a bold label like
    "**Battery:**"). Options: the words between a list marker or bold mark
    and the id; a capitalised run ending in a model number; a known-brand
    prefix.
  - **Brands.** Is a catalogue brand with an invented model ("Norvik Lite",
    "Aurelis Home 3") invented? Is a brand alone ("a Kestrel model (P-123)")
    fine?
  - **The customer's words.** `aurelis-home-gift-mum` misspells "Auralis
    Home 1" on purpose (variety: typo), and the answer echoes it. Is a name
    taken from the question, or a near miss of a catalogue name, allowed?
  - **Extend `names` or add a check.** One `names` check with a second
    failure kind, or a new check (e.g. `invented`) with its own reason?
    A new name changes the report's check list for every case.
  - **Which cases.** Every case, as `grounded` and `names` are, or only
    cases that ask for it (an `expect_properties` entry)?
  - **Baseline.** If it runs on every case, any committed run re-scored
    could change pass counts. Does the eval run owed by this change stand
    as the new baseline, and is that said in the review?

## Assumptions I made

- **Feature, not fix.** `names` works as §25 specified it ("the window
  names another catalogue product"); catching names outside the catalogue
  is new behaviour with open design choices.
- **The rough scan is evidence, not the rule.** Its pattern (up to five
  words before an id, bold or not) is mine; the spec decides the real one.
  The 10-of-10 count depends on it.
- **No case changes status in the evidence.** Both cases already fail on
  `expected` in every qwen run checked, so on these runs the
  new check adds a reason, not a failure. Other models or a better prompt
  could make it the only failing check.
- **The judge is not the answer here.** Widening `judge-no-fit`'s scope
  would need its own validation (§16) and an Anthropic key per run.
- **`review_tier` left empty.** `score.py` is under `src/**` and not in
  the "by meaning" list, so the path table gives Attested.
- Nothing blocks this. §31 (search before answering) would make these
  answers rarer but does not change what the check must catch.
