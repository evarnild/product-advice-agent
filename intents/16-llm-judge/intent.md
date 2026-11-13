<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §16 — An LLM judge for one failure mode, validated against the owner's labels

**Type:** feature
**Originator:** the owner, 2026-11-13: "/intent LLM as a judge"
**Source:** the week's objective "code-based checks first, then one
LLM-as-judge that you validate against your own labels on 30 cases";
`intents/9-error-analysis/intent.md` (out of scope there: "an LLM-as-judge
with binary output and the owner's critiques as few-shot examples, measured
against the owner's labels"); `intents/10-langfuse-annotation/intent.md`
(out of scope there: "Langfuse LLM-as-a-judge evaluators and the agreement
view (the later judge intent)"); §15 (the 50 cases)

## Problem

The advisor's answers are scored only by §8's deterministic checks (search
arguments, cited ids, stock, forbidden ids, refusal), and `score.py` says
so: "Wording is not judged (no judge model)". The owner's labels show
failures those checks cannot see. `evals/taxonomy.json` (drafted from
`evals/labels/20261113T072503Z-ollama.jsonl`) has four modes, and
`counts.md` counts them:

| mode | failed |
| --- | --- |
| `irrelevant_alternatives`: "suggests products that are not relevant to the user's needs" | 4 |
| `no_product_available`: "fails to confirm that no products are available within the specified price range" | 4 |
| `incorrect_price_range` | 2 |
| `no_search_performed` | 2 |

The last two are code-checkable (a price comparison, a missing tool call).
The first two are about what the answer says, so today only the owner,
reading every conversation, finds them. That does not scale to 50 cases
on every change, and nobody knows how far an automatic verdict on them
could be trusted.

## Outcome

- **One judge, one failure mode.** A judge that reads a conversation (the
  question, the tool results the model got, the answer) and returns pass or
  fail with a one-line reason, for a single mode from the taxonomy (the
  spec picks it; `no_product_available` or `irrelevant_alternatives`).
- **Validated on at least 30 of the owner's labels.** The owner's labelled
  conversations are split into few-shot examples and a held-out test set;
  on the test set the judge's agreement with the owner is reported as the
  true-positive rate (owner pass, judge pass) and the true-negative rate
  (owner fail, judge fail), with the counts, in a committed report. The
  spec sets the bar for "trusted".
- **Runs with the evals.** `advisor-eval` (or an `advisor-analysis`
  command over a run report) can add the judge's verdict per case next to
  the code checks, clearly marked as the judge's, without changing the code
  checks' result.

## Constraints

- **Cost and autonomy.** The judge calls a real model only when the owner
  runs it; the suite fakes it (`tests/conftest.py` blocks sockets). A paid
  judge model needs the owner's go; the local Ollama costs nothing.
- **Labels are the owner's.** The judge never writes or changes a label,
  and never writes scores to Langfuse unless the spec decides so.
- **Data.** Synthetic conversations only; the judge prompt is committed
  (`evals/prompts/`, like §9's), with the few-shot examples taken from the
  owner's critiques.
- The code checks stay first and unchanged; the judge adds a verdict, it
  does not override one.
- No new dependency without a plan line. `langfuse` stays in `tracing.py`
  only.
- Out of scope: judges for more than one mode, Langfuse's built-in
  evaluators, running evals on every change, prompt fixes the judge points
  to.

## Type-specific questions

### Feature
- **Users:** the owner, who wants to stop reading every conversation for
  the failure modes code cannot check.
- **What exists today:** §8's code checks; 34 labels on 23 distinct cases
  (21 pass, 13 fail) across three runs and two models; §10's queue and
  import to label more quickly; the taxonomy and counts; `run.py` records
  each case's turns and tool results.
- **Open design questions:**
  1. Which mode is judged first.
  2. The judge model: Anthropic (paid, stronger) or Ollama `qwen3:8b`
     (free, weaker); and whether it may be the same model as the advisor.
  3. The 30 labelled cases: which run and model, how many fails are
     needed for a meaningful true-negative rate, and the split (few-shot /
     dev / test).
  4. Whether labels from different runs of the same case count once or
     separately.
  5. Where the verdict lives: a new field in the run report, a separate
     judge report, or a Langfuse score.
  6. The bar for trusting the judge (e.g. both rates at least 0.8) and
     what happens below it.
  7. Whether the judge reads §14's catalogue or only the tool results in
     the conversation (the latter keeps it independent of catalogue
     changes, §13).

## Assumptions I made

- It is a **feature**: a new prompt, a model call path, a report and a
  validation procedure, with a spec needed on the questions above. No
  question round was asked.
- One mode only, binary output, critiques as few-shot examples, as §9's
  intent framed it.
- The validation labels come from the owner, via §10's queue or §9's
  viewer, and labelling up to 30 is part of the work (today: 23 distinct
  cases).
- It runs on §15's 50 cases once they exist; the validation does not wait
  for them.
- `review_tier` is left to the path table: the judge prompt is an eval
  prompt, not one the product ships to users.
