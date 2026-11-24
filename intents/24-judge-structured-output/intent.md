<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §24 — Constrain the LLM judge's reply to its verdict schema

**Type:** feature
**Originator:** the owner ("what would be the advantage of structured
output?", then "draft an intent for structured output on the judge",
conversation, 2026-11-23)
**Source:** `intents/16-llm-judge` (the judge), `evals/judge/validation.md`

## Problem

The judge (`advisor-analysis judge` / `judge-validate`, §16) gets its
verdict by asking for it in prose and parsing it afterwards. The prompt ends
"Reply with one JSON object and nothing else: `{"pass": true or false,
"reason": "<one sentence>"}`" (`src/advisor/evals/prompts/judge-no-fit.md`),
the call passes no format to the model (`judging._ask`,
`src/advisor/evals/judging.py:143-148`: `client.complete("", [...], [])`),
and `judge.parse_verdict` (`src/advisor/evals/judge.py:115`) digs the first
JSON object out of whatever came back with the lenient `extract_json`.

When the model strays from the format, the conversation gets a
`JudgeError`: neither a pass nor a fail, counted and left out of the rates
(`judge.agreement`, `judge.py:216`). The committed validation has **2 judge
errors out of 35 held-out conversations** (`evals/judge/validation.md:8`).
So the agreement numbers the owner relies on to trust the judge are partly
about the format, not the judgement, and every error is a conversation the
judge does not score. The `ModelClient` protocol
(`src/advisor/models/base.py`) has no way to ask a provider for a reply in
a given shape, so nothing today can prevent this.

## Outcome

- A judge call asks the model, through the provider's own structured-output
  mechanism, for a reply that fits the verdict schema (a one-sentence
  reason and a boolean pass). A test with the scripted fake asserts the
  schema the client received; a test on the adapter asserts the request it
  sends to the SDK (faked).
- A reply in that shape is read without the lenient scan; a reply the
  provider still could not complete (a refusal, a cut-off at the token
  limit, an API error) is a `JudgeError` with a reason that says which, as
  today. `extract_json` stays for `generate` and `taxonomy`.
- A `judge-validate` run on the committed split, made at the owner's
  request, reports 0 judge errors that are format errors, and its
  `validation.md` is committed with the new agreement rates (whatever they
  are) beside the old ones in the review.

## Constraints

- `anthropic` stays imported only in `models/anthropic_model.py`
  (`tests/test_boundaries.py`). The judge stays pinned to Anthropic
  (`judging.py` docstring); this intent does not add a provider to it.
- The agent's own calls (`agent.run_agent`) do not change: the advisor's
  answer stays free text, and a call without a schema behaves exactly as
  today in both adapters and the fake.
- No new dependency and no SDK version bump (`anthropic` 2.6.0 per
  `uv.lock`), unless the spec finds 2.6.0 lacks the mechanism; then a plan
  line says why.
- Tests never call a model (`tests/conftest.py` blocks sockets). Real judge
  runs cost Anthropic tokens on the owner's key and run only on the owner's
  request.
- Touches `src/advisor/models/`: a live check is owed (`REVIEW-POLICY.md` →
  "Live checks", rule 1), and `owes-run` will likely say an eval run is
  owed (Ollama, the default provider).
- Privacy (§19): judged conversations and judge reasons are eval data, not
  user data, but nothing in logs or the review quotes session transcripts.
- Out of scope: structured output for `generate` and `taxonomy` (a later
  intent if this one works), and for the agent's tool calls.

## Type-specific questions

### Feature
- **Users:** the owner, who runs `judge` and `judge-validate` and decides
  from `validation.md` whether to trust the judge.
- **What exists today:** prompt instructions plus `extract_json` plus a
  hand check in `parse_verdict`; 2 of 35 held-out conversations end as
  judge errors.
- **Open design questions:**
  - How a schema reaches the provider: an optional parameter on
    `ModelClient.complete` (every adapter and the fake accept it; Ollama
    maps it to `format` or refuses it), or a narrower judge-only path. The
    protocol change touches every adapter.
  - Field order: `reason` before `pass`, so the model writes its reasoning
    before the verdict. That changes the prompt's example and the prompt
    hash, so the judge is re-validated anyway.
  - Which Anthropic mechanism (a structured-output format, or a forced
    single tool call whose input is the verdict), and whether
    `claude-haiku-5-5` and SDK 2.6.0 support it.
  - Whether the prompt keeps its "Reply with one JSON object" line.
  - What happens to old `evals/judgements/*.jsonl` and the committed
    `validation.md`: replaced by the new run, or kept beside it.

## Assumptions I made

- **Feature, not adjustment.** It changes the model interface and owes a
  spec; well over an adjustment's 5 files and 60 lines.
- **The 2 judge errors are format errors.** I read only the count in
  `validation.md`, not the reasons (which may quote conversations). The
  spec should confirm their reasons before promising "0 format errors".
- **Not blocked by §23** (typed Anthropic adapter, accepted, not built).
  Both edit `models/anthropic_model.py`; whichever merges second rebases.
  Recorded as a link, not `blocked_by`. If you'd rather type the adapter
  first, say so and I'll add `23` to `blocked_by`.
- **`review_tier` left empty.** `src/advisor/evals/prompts/` and
  `models/` are not in the "by meaning" list, so the path table decides.
- **The owner runs `judge-validate`** for the outcome's third bullet; an
  agent never calls Anthropic on its own.
