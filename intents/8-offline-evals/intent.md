<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §8 — An offline eval suite that scores the advisor's answers against a fixed question set

**Type:** feature
**Originator:** the owner ("offline eval suite", picked from the list of
candidate intents on 2026-11-10)
**Source:** `OVERVIEW.md` → "Next": "The evaluation suite and real guardrail
checks, as new intents"; deferred by §1 and §2 (quoted below)

## Problem

Nobody can tell whether the advisor gives good advice, or whether a change
made it better or worse. `npm run verify` proves the plumbing (the tool
loop, the guardrail seam, tracing) with a scripted fake model. It says
nothing about what a real model answers.

The project has deferred this twice. §1: "Out of scope: advice quality, the
evaluation suite, guardrails beyond a placeholder seam, a UI and any
deployment." §2: "Out of scope: the evaluation suite and any scoring". §2's
spec adds "Wrong advice is the eval suite's" to its list of unhandled risks.

The gap has already cost a defect. §7's bug ("noise-cancelling headphones
under 200 euros" answered with "There are no noise-cancelling headphones
available") was found by hand during §2's live check, not by any check that
runs again. The next prompt change, model change or guardrail (the other
half of "Next") has nothing to be measured against, and neither does a
choice between `qwen3:8b` and Claude.

## Outcome

- One command runs a fixed, versioned set of catalogue questions through the
  advisor with a chosen provider (the Ollama default needs no key and no
  paid API). It prints, per case and in total, which checks passed, and
  exits non-zero when a case fails. A reviewer can run it and read the
  report.
- The checks are deterministic, with no judge model. At least these: every
  product id the answer cites exists in the catalogue with the stated price;
  the products a case expects are cited; the products a case forbids are
  not; an off-topic case gets the refusal or a decline; an out-of-stock
  product that is recommended is said to be out of stock. The question
  set includes §7's noise-cancelling case.
- `npm run verify` covers the suite without a network or a model. The
  scorers and the runner are tested against the scripted fake with known
  good and known bad answers, so a broken scorer turns verify red. The live
  run itself is not part of verify.

## Constraints

- Architecture (`CLAUDE.md`): the suite drives the advisor through
  `answer_question` / `run_agent` and the `ModelClient` protocol, and builds
  the provider through `make_client`. It imports no provider SDK and no
  `langfuse` (`tests/test_boundaries.py`). Scorers are pure functions.
- Data: the cases use only the synthetic catalogue (`data/catalogue.json`)
  and invented questions. No real user data, and no captured live
  transcripts committed as fixtures, unless they contain only those.
- Cost: the default run is local (Ollama) and free. A run against Anthropic
  happens only when the owner selects it, with the existing
  `ADVISOR_MODEL_PROVIDER` / key. Tests never call a model
  (`tests/conftest.py` blocks sockets).
- Autonomy: the suite reports. It never changes the prompt, the catalogue or
  the code, and it does not run on a schedule.
- Leave alone: `src/advisor/prompts/`, `guardrails.py`, `cli.py`,
  `tracing.py` and the catalogue data. Improving the answers the suite finds
  wrong is later work (fix or adjustment intents).
- Out of scope: LLM-as-judge or semantic scoring, uploading datasets or
  scores to Langfuse, CI or scheduled runs, a comparison report across
  models (a later experiment), and new guardrail checks.
- No new dependency without a line in `plan.md` saying why.

## Type-specific questions

### Feature
- **Users:** the owner, as developer: before and after a prompt, model or
  guardrail change, and to choose a default model. Reviewers, who can cite
  a run as evidence for a live check.
- **What exists today:** nothing that scores answers. The scripted fake
  (`src/advisor/models/fake.py`: "A scripted fake `ModelClient` for tests
  (and, later, evals)") and the `Tracer` protocol are the seams §1 left for
  it. §2's "repeatable run of a few fixed questions through both providers,
  with results recorded, and no automated scoring" was done by hand.
- **Open design questions:**
  1. Case format and location: JSON or JSONL under `evals/` or
     `src/advisor/evals/`, and which fields a case has (question, expected
     ids, forbidden ids, must refuse, max price, ...).
  2. How a cited product is recognised in free text: the `(P-001)` id form
     the prompt asks for, or also names.
  3. Non-determinism: one run per case, or N runs with a pass rate and a
     threshold.
  4. The command: a `uv run` script, `python -m advisor.evals`, an `npm run`
     alias, or a subcommand of `advisor` (which would touch `cli.py`,
     Reviewed tier).
  5. Whether a case can also check the tool calls (e.g. that the model
     searched `headphones` with `max_price=200`) through a recording
     `Tracer`, or only the final answer.
  6. Whether the report is also written to a file for comparing two runs,
     and its format.
  7. How many cases are enough to start: roughly 10 to 20, covering each
     category, a budget filter, an empty result, out of stock and off-topic.
  8. Whether a run against a real model owes a live check under
     `REVIEW-POLICY.md` rule 1, or only the runner's wiring does.

## Assumptions I made

- **"Offline" means no paid API, no judge model and no network beyond the
  local model.** It does not mean "no model": a suite that only replays the
  fake would test the scorers, not the advisor. So the scored run uses a
  real (by default local) model, and only the scorer tests sit in verify.
  If you meant a fully recorded suite (cassettes replayed in verify), say so:
  that changes the outcome and the data constraint.
- **Deterministic checks only.** Grounding (ids, prices, stock) can be
  checked exactly against the catalogue. Tone and helpfulness need a judge
  model, which is left out.
- **The run reports and does not gate merges.** A failing case shows a
  quality gap; it does not block `verify` or `/ship`. Making it a gate is a
  separate change to `REVIEW-POLICY.md`.
- **§7's case is expected to fail until §7 ships**, and that is fine: it is
  the suite's first regression case. If §7 merges first, it should pass.
- **Tier.** The work is new `src/**` code, tests and data, which the path
  table puts at Attested. It does not touch a "by meaning" path if it stays
  out of `cli.py` and `tracing.py`, so `review_tier` is left empty. A
  subcommand on `advisor` (design question 4) would raise it to Reviewed.
- **Results stay local.** Nothing is sent to Langfuse beyond the traces the
  advisor already writes when tracing is configured.
