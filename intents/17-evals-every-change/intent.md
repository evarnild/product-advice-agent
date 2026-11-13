<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §17 — Run the evals on every change that can move the answers

**Type:** feature
**Originator:** the owner, 2026-11-13: "/intent run evals on every change"
**Source:** the week's objective "Test set and evaluation: 50 real-looking
questions … code-based checks first, then one LLM-as-judge … run on every
change"; §15 (the 50 cases), §16 (the judge), §13 (catalogue changes owe an
eval run)

## Problem

Nothing makes an eval run happen when the advisor changes. `CLAUDE.md`
lists `uv run advisor-eval` as "not part of verify", README says "A run
uses a real model", and neither `REVIEW-POLICY.md` nor the ship
preconditions (`scripts/ship-lib.mjs`) mention evals. A change to the
system prompt, the agent loop, a model adapter, the default model or the
catalogue can merge with `verify` green and no idea whether the answers got
better or worse. The owner runs evals by hand when they think of it.

What makes this harder than adding a step to `verify`:

- **A run calls a real model.** The local Ollama run takes minutes (36
  cases: about 3.5 min in `evals/runs/20261113T072503Z-ollama.json`; 50
  will be about 5); an Anthropic run costs money and needs a key. The suite
  must stay offline (`tests/conftest.py` blocks sockets).
- **Results vary run to run.** The same 15 cases on Ollama passed 6 and
  then 9 (`20261111T114440Z-ollama.json`, `20261111T120859Z-ollama.json`),
  so "the pass rate dropped" needs a baseline and a tolerance, not a single
  number.
- **There is no CI.** The repo has a GitHub remote but no
  `.github/workflows/`, and a hosted runner cannot reach the owner's local
  Ollama.

## Outcome

- **A rule says which changes owe an eval run**, the way rule 1 says which
  owe a live check: at least `src/advisor/prompts/`, `agent.py`,
  `models/`, `guardrails.py`, the catalogue data and the eval cases. Other
  changes owe none.
- **An owed run is evidence in the review.** The review names the run
  report (`evals/runs/<stamp>-<provider>.json`) made on the branch's
  content, and compares it with a baseline from `main`: pass rate, and the
  cases that flipped pass↔fail (code checks, and the judge's verdict once
  §16 exists).
- **It is enforced, not remembered.** A branch whose change owes a run
  cannot be shipped (or cannot get a green review) without one made on
  the commit being reviewed; the spec decides where the check lives.
- **The cost is known up front**: the default run is the local model;
  a paid run happens only when the owner asks for one.

## Constraints

- No model call in `verify` or the test suite.
- Paid model runs only on the owner's explicit request; the default is
  the local Ollama.
- `REVIEW-POLICY.md`, `scripts/ship-lib.mjs` and the skills are Reviewed
  tier, so this intent is too.
- Run reports stay gitignored unless the spec decides a baseline is
  committed.
- No new dependency without a plan line.
- Out of scope: hosted CI with a paid model, the judge itself (§16), the
  case set itself (§15), fixing the answers a run flags.

## Type-specific questions

### Feature
- **Users:** the owner, who reads reviews and ships; the reviewer and
  `/auto`, which would cite the run.
- **What exists today:** `advisor-eval` writes a report with the
  `cases_sha256` and `prompt_sha256` it ran against and per-case
  `duration_s`; the live-check rule and gate as a pattern for an owed,
  owner-side step; no CI.
- **Open design questions:**
  1. The path list that owes a run.
  2. Where it is enforced: `check:intent`, a ship precondition, the
     `/review` passes, or a git hook; and how a report is tied to a commit
     (the report would need the commit or a content hash).
  3. Who runs it: the owner (like a live check), the reviewer or the
     implementer agent (the run needs the local Ollama, so it runs on the
     owner's machine either way).
  4. The baseline: a fresh run on `main` each time, or a committed
     baseline report updated at each merge.
  5. The tolerance: how many flipped cases or what pass-rate drop counts
     as a regression, given the run-to-run variance; repeats per case.
  6. Whether a regression blocks the merge or is reported for the
     owner's decision.
  7. Whether a later GitHub Actions job (code checks only, a fake model)
     is worth it at all.

## Assumptions I made

- It is a **feature**: it adds a policy rule, enforcement in the kit and
  a comparison, and needs a spec. No question round was asked.
- "Every change" means every change that can move the answers, not
  documentation or kit-only changes.
- The runs happen on the owner's machine with Ollama by default; hosted
  CI is out of scope.
- `review_tier: reviewed`: it likely edits `REVIEW-POLICY.md` and the
  kit's enforcement, both on the Reviewed path list.
- Best done after §15 (the 50 cases) and before or alongside §16; it does
  not need §16 to start.
