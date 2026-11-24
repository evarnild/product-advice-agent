<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §24 review — Constrain the LLM judge's reply to its verdict schema

verdict: rework
tier: reviewed
reviewed-commit: 63211c5
main: 49a3dfe
round: 1
sampled: no
run: auto
live-check: owed

**Tier.** The paths give Attested. `src/advisor/evals/prompts/` is not the
shipped `src/advisor/prompts/`. But the HIGH finding below raises it to
Reviewed (REVIEW-POLICY.md → "Tiers", rule 3), so you read the diff before
the merge.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: subtasks 1–5 built as planned; subtask 6 (the re-validation) is the owner's live check, not done by design |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass for B1–B10 and AC1–AC10; AC11 is the live check; AC12 is the eval run below |
| 4 | Tests prove the behaviour | findings (1 HIGH, 1 LOW) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (863 → 884, 21 new cases) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass: no `type: ignore`, `noqa` or `cast(` added; no new dependency |
| 9 | Repo footguns | pass |

## Type check
```
type-check: PASS (intent 24, feature)
  note:  16 file(s), 327 line(s) changed outside intents/.
```

What the code does, checked against the installed SDK (anthropic 2.6.0):
- **Without a schema,** `messages.create` gets exactly `{model, max_tokens,
  system, messages, tools}`, with no `output_config`. The agent,
  `generate` and `taxonomy` pass no schema.
- **With a schema,** it sends `output_config = {"format": {"type":
  "json_schema", "schema": dict(schema)}}`, typed `OutputConfigParam`.
  Its `stop_reason` is read only then: `refusal` and `max_tokens` become a
  `ModelError` naming them.
- **Ollama** refuses a schema with `ModelError` before any request.
- **The verdict is read strictly** with `json.loads`: prose-wrapped, fenced
  and `<think>`-prefixed replies are now "the model answer is not a JSON
  object". `judge.agreement` is untouched. `extract_json` serves only
  `generate` and `taxonomy`.
- **Boundaries** hold: `anthropic` and `httpx` stay in their one module
  each, and mypy --strict is clean.

## Findings
- **HIGH** `tests/test_models.py`
  (`test_adapter_sends_the_schema_as_output_config_format`) — the
  `max_tokens` value sent in the schema branch is never asserted. Spec B3
  and AC3 say "every other argument is as today", and B4's cut-off message
  quotes the 1024.
  - Mutant A5 (`max_tokens=2048` in the schema call,
    `anthropic_model.py:105`) survives the full suite.
  - So does A16, the same at `:91` in the no-schema call, a gap inherited
    from §27.
  - Needs rework: assert `sent["max_tokens"] == MAX_TOKENS` (import it from
    `advisor.models.anthropic_model`) in that test and in
    `test_adapter_without_a_schema_sends_exactly_todays_arguments`. A5 and
    A16 must be killed.
- **LOW** `tests/test_judge.py` (`test_anything_else_is_a_judge_error`) —
  the only fenced case has a ```` ```json ```` tag. Mutant J8
  (`json.loads(text.strip().strip('`'))`, `judge.py:130`) lets a bare
  fence through and survives, although B8 makes any fence an error.
  Needs rework: add the case `('```\n{"reason": "r", "pass": true}\n```',
  _NOT_OBJECT)`. J8 must be killed.

## Not checked
- Whether `claude-haiku-5-5` accepts `output_config.format` (with `tools=[]`
  beside it), and whether the API generates the properties in schema
  order. Only the live check shows this (rule 1, and rule 3 for this item).
- The real `stop_reason` the API returns for a structured-output refusal;
  it is faked here.
- `base.py` was not mutated: its change is the protocol signature, which
  mypy covers.

## Live check
- owed: rule 1 (`src/advisor/models/`), and the two Not-checked items above
  about the real API. Run it after the rework, in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/24-judge-structured-output`,
  with `ANTHROPIC_API_KEY` set. It costs about 35 Haiku calls plus one
  `advisor` run.
- steps:
  1. `uv run advisor-analysis judge-validate --runs-dir C:/Users/eric/src/product-advice-agent/evals/runs`
  2. Open `evals/judge/validation.md`.
  3. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"; uv run advisor "A cheap phone that is in stock"; echo "exit: $LASTEXITCODE"; Remove-Item Env:ADVISOR_MODEL_PROVIDER`
  4. Commit the new `evals/judge/validation.md` on the branch (or ask me
     to), **before the next review round**: it must be part of that
     round's reviewed commit.
- you should see:
  - step 1 completes over the 35 held-out conversations. Failure looks like
    `ERROR <ref>: Anthropic call failed: BadRequestError` on every one,
    which means the model rejected the schema.
  - in `validation.md`: no judge error reading "the model answer is not a
    JSON object", "the JSON has no boolean 'pass'" or "the JSON has no
    string 'reason'". A refusal, a cut-off or an API error is allowed
    (spec I4). The prompt sha256 differs from a6cff797…. The old rates for
    comparison: true-positive rate 0.52 (11/21), true-negative rate 0.75
    (9/12), 2 judge errors.
  - step 3: a normal answer citing real ids with prices, then `exit: 0`.

## Eval run
- Report `evals/runs/20261124T204309Z-ollama.json` (copied to the main
  checkout). Provider ollama, model qwen3:8b, made in the worktree at
  63211c5. It started 20:43:09Z, after the commit at 20:42:41Z.
- Content check: its `cases_sha256` d5f5e275, `prompt_sha256` c2a38987 and
  `catalogue_sha256` c2e56cb2 equal the worktree's files.
- `compare` against `evals/baseline.json` (§26's run): baseline 39/50, this
  run **38/50**. Regressed 1: `basic-phone`, which passed when re-run alone
  (`advisor-eval --only basic-phone`, `20261124T205326Z-ollama.json`), so it
  is not a regression. Fixed 0, added 0, removed 0.
- The `cases_sha256` warning against the baseline is the line-ending
  artefact that §29 fixes (the baseline hashed a mixed-ending copy of the
  same cases).

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 63211c5:
  - `npm run verify`: exit 0, 884 passed.
  - `npm run check:intent`: PASS.
  - `owes-run`: owed.
  - The whole src, test and doc diff, read against B1–B12 and AC1–AC12.
  - The SDK types in 2.6.0.
  - The boundary greps.
  - 34 mutants: 31 killed; A5, A16 and J8 survived. Restored by copy; clean.
- **Coordinator, re-run**, at 63211c5:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **884 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 24, feature)`, which matches.
  - Surviving mutants against the full suite: A5, A16 and J8 each **survived** (884 passed), which matches. Restored by copy; `git status --short` was clean.
  - The eval run, `compare` and the `--only` re-run, as above.
- Taken on trust: the implementer's per-commit "verify green"; HEAD alone was verified.
