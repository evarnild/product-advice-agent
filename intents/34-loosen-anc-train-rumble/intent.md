<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §34 — The train-rumble case fails a right answer on its search keyword

**Type:** adjustment
**Originator:** the coordinator's analysis of 10 qwen3:8b eval runs of the
50 cases, for the owner ("write intents")
**Source:** `evals/runs/20261124T215703Z-ollama.json` (latest) and the nine
earlier qwen3:8b runs since `20261121T125003Z`; case 46 of
`evals/cases.jsonl`; `intents/26-loosen-two-headphone-cases` (the
precedent)

## Problem

`anc-train-rumble-200` ("I'm after over ear cans with proper active noise
cancellation, something that kills the train rumble. Under 200 euro, and I
don't need a fancy DAC.") fails on all 10 qwen3:8b runs. In 9 of them the
only failing check is `search`; in the first (`20261121T125003Z`)
`a-match` failed too.

The case expects:

```json
"expect_search": {"category": "headphones", "keywords_any": ["noise-cancelling"], "max_price": 200}
```

In the latest run qwen3:8b searched

```json
{"keywords": ["active noise cancellation", "over ear"], "max_price": 200, "in_stock_only": true, "category": "headphones"}
```

and answered with "**Kestrel Calm 46 (P-123)** … 49.00 …, in stock" and
"**Auralis Calm 83 (P-355)** … 59.00 …, in stock": over-ear headphones with
active noise cancelling under €200, which is right. The `search` check
said: "no search_products call matches {'category': 'headphones',
'keywords_any': ['noise-cancelling'], 'max_price': 200} (1 call(s))".

The keyword test is a substring test after folding case and hyphens
(`score._call_satisfies`):

```python
words = [_norm(k) for k in got if isinstance(k, str)] if isinstance(got, list) else []
wanted = [_norm(w) for w in value]
if not any(w in word for word in words for w in wanted):
```

with `_norm(text) = text.lower().replace("-", " ")`. "noise cancelling" is
not inside "active noise cancellation", so the search fails although it
asks for the same feature. Haiku passes only because it also sent
`noise-cancelling` (`20261124T192816Z-anthropic.json`).

The case's scenario is `spelling-differs`: the customer names the feature
in other words than the catalogue ("noise cancellation" against the
catalogue's "noise cancelling"). Two tests hold that shape, and both bind
`expect_search`:

- `test_new_cases_name_their_source_and_a_probe_that_passes_the_coverage_check`
  runs `check_coverage` on the note's probe, which fails a
  `spelling-differs` probe whose keyword is in the question verbatim
  (`coverage.py`: `if word.lower() in lowered: return False, ...`).
- `test_expect_search_is_the_notes_probe_for_every_new_case` asserts
  `c.expect_search == want`, the note's probe with `keywords` renamed
  `keywords_any`.

So every keyword that would match qwen's phrase ("noise cancel",
"cancellation") is in the question, and cannot be the probe. The case can
pass qwen's search only if `expect_search` may carry more keywords than
the probe.

## Outcome

- `anc-train-rumble-200`'s `search` check passes a headphones search under
  €200 that names noise cancellation in any of its usual spellings
  ("noise-cancelling", "noise cancelling", "noise canceling", "active noise
  cancellation"), and still fails one without it (for example only "over
  ear"), with another category, or without the €200 cap.
- The note's probe stays `{"category": "headphones", "keywords":
  ["noise-cancelling"], "max_price": 200}` and still passes
  `check_coverage` for `spelling-differs`: the question does not contain
  the catalogue's word.
- The products that fit (`cases.fits`, behind `a-match`) stay the same 8
  (P-001, P-004, P-005, P-123, P-355, P-379, P-387, P-403).
- qwen3:8b's answer in `20261124T215703Z-ollama.json`, re-scored against
  the changed case, passes. Haiku's in `20261124T192816Z-anthropic.json`
  still passes.
- `npm run verify` stays green, including the catalogue consistency test.

## Constraints

- No core code: no change to `cases.py`, `score.py` or `coverage.py`
  (`CORE_CODE` in `scripts/intent-check-lib.mjs` is `agent`, `catalogue`,
  `guardrails`, `models/`, and `evals/(cases|score).py`).
  `evals/cases.jsonl` is data and `tests/` is test code; neither is core.
- `evals/cases.jsonl` is in `EVAL_PATHS` (`src/advisor/evals/baseline.py`)
  and REVIEW-POLICY.md → "Eval runs", so an eval run on Ollama is owed and
  the baseline moves after the merge (`cases_sha256` changes).
- Old run reports and labels are records of their run and are not
  re-scored or edited (docs/decisions/0003, "Old records").
- Out of scope: stem- or synonym-aware matching in `search_products` or the
  scorer (core code; a fix or feature), the other 49 cases, and the
  over-ear requirement (left to the judge, as the note says).

## Type-specific questions

### Adjustment
- **Exactly what changes:**
  - `evals/cases.jsonl`, `anc-train-rumble-200`: `keywords_any` becomes
    `["noise-cancelling", "noise cancel"]`. "noise cancel" is a substring of
    the folded "noise cancelling", "noise canceling" and "active noise
    cancellation". Category, `max_price`, `expect_properties:
    ["cites_a_match"]`, the question and the note stay as they are.
  - `tests/test_evals_cases.py`,
    `test_expect_search_is_the_notes_probe_for_every_new_case`: the rule
    becomes "`expect_search` is the probe, except that `keywords_any` may
    add words after the probe's keywords". The probe's keywords must still
    come first and in order, so `check_coverage` keeps testing what the
    case is for. A test that this case's `keywords_any` passes qwen's
    search and fails `["over ear"]` alone.
- **Blast radius:** 2 files (`evals/cases.jsonl`, 1 line;
  `tests/test_evals_cases.py`, about 15 lines), plus the intent folder.
  Within 5 files and 60 lines, and no core code.

## Assumptions I made

- **What the case still guards.** `search`: the agent asked for
  headphones under €200 with noise cancellation in some spelling. `a-match`:
  it cites one of the 8 noise-cancelling headphones under €200. The
  `spelling-differs` part now rests on `a-match`: the customer's
  "cancellation" is not the catalogue's "cancelling", so a plain keyword
  search for the customer's words matches no description. The agent has to
  get to a fitting product anyway. The search check no longer requires
  the catalogue's spelling. That loss is deliberate: the catalogue's
  exact word is a detail of the tool, not of the answer.
- **Superset rule, not a one-case exception.** It is simpler than a list of
  case ids, and the probe still decides what `check_coverage` checks. The
  cost is that a later case could add a verbatim word to `keywords_any`;
  the probe rule still stops it from becoming the probe.
- **Not dropping `keywords_any`.** The scenario test needs it
  (`assert c.expect_search and "keywords_any" in c.expect_search`), and
  without it `a-match` would accept any headphones under €200.
- **Not adding "over-ear".** §15's review (R2-F1) tried it: `keywords_any`
  is any-of, so the fit set grows from 8 to 18 and `a-match` would accept
  headphones without noise cancelling.
- **qwen's answer is partly luck.** "active noise cancellation" matches no
  description. "over ear" matched, and the two cheapest in-stock over-ear
  headphones happen to have ANC. The case does not test that, and this
  intent does not make it.
- **The other choice is to keep the case failing**, as a signal that
  qwen3:8b copies the customer's words into the search. If the owner
  prefers that, abandon this intent.
- **Adjustment, not fix.** No code is wrong: one data expectation is
  stricter than its question.
- **`review_tier` left empty.** Neither file is in the "by meaning" list.
- Nothing blocks this.
