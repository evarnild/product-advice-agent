<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §23 review — Type the Anthropic adapter against the SDK's own types

verdict: rework
tier: attested
reviewed-commit: d6bf4eb
main: 5f7a773
round: 1
sampled: yes
run: auto
live-check: owed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1) |
| 2 | Type check | ROUTE, explained: the refactor holds for the tests |
| 3 | Behaviour against intent | findings (1, the same one) |
| 4 | Tests prove the behaviour | findings (1: no test pins how unknown block types are handled; 1 equivalent survivor) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass |
| 7 | Documentation | pass (nothing user-visible changed) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass (list empty) |

## Type check
```
type-check: ROUTE (intent 23, refactor)
  route: Declared refactor, but existing tests lost lines (tests/test_models.py). Behaviour may have changed — check, or route to feature.
  note:  2 file(s), 88 line(s) changed outside intents/.
```
The ROUTE is explained. Every line `git diff main -- tests/test_models.py`
removes builds the fake (`SimpleNamespace` responses and blocks replaced by
the SDK's `Message`, `TextBlock`, `ToolUseBlock` and `Usage`). No `assert`
line was removed or edited. The one added test is the plan's
characterisation test. The refactor type holds.

## Findings
- **MEDIUM** `src/advisor/models/anthropic_model.py:91,93` — the
  `isinstance` narrowing does not give the old partition for a block type
  that SDK 2.6.0 doesn't know.
  - For the 12 known members of `ContentBlock` the mapping is exact.
  - For an unknown tag, the SDK's `construct_type` falls back to the
    union's first member, `TextBlock`, and keeps the foreign `type`. So
    `[{"type":"text","text":"answer"}, {"type":"futuristic","text":"leak"}]`
    gives the text `'answer'` on `main` and `'answerleak'` on the branch. A
    block with no `text` raises an unwrapped `TypeError` on the branch where
    `main` ignored it.
  - That breaks the intent's "Behaviour is unchanged". The plan's Risks
    claim of "the same partition" was wrong for unknown tags. No plan
    change is needed: the fix keeps the plan's behaviour.
  - **Needs rework:** keep the tag check alongside the narrowing:
    `if isinstance(block, TextBlock) and block.type == "text":` and
    `elif isinstance(block, ToolUseBlock) and block.type == "tool_use":`.
    Add a characterisation test: an unknown-tag block (built with
    `construct_type(type_=Message, value=raw)` or
    `TextBlock.model_construct(type="futuristic", text="x")`) next to a real
    text block gives only the real text. Where possible, also cover an
    unknown block that carries `id`, `name` and `input`. The new test must
    kill a mutant that removes either tag check.
- **LOW** `src/advisor/models/anthropic_model.py:94` — `dict(block.input)`
  copies where the old code aliased. Mutant M4 (drop the `dict(...)`)
  survives, but it is equivalent: `ToolCall.arguments` compares equal and
  nothing depends on identity. Worth a look, no action.

## Not checked
- The real API response path. All responses were built in memory with the
  SDK's own constructors; the live check covers the real API.
- The judge path (`evals/judging.py`) through the adapter against the real
  API. It uses the same `complete`, and no model was called.
- Unknown blocks arriving from the real API. They can't be produced on
  demand, so they are only covered in memory.

## Live check
- owed: rule 1 (`src/advisor/models/`), covering the "real API response
  path" item above. Run it after the rework, in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/23-typed-anthropic-adapter`,
  in PowerShell, with `ANTHROPIC_API_KEY` in `.env`. It costs a few
  Anthropic calls.
- steps:
  1. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"; uv run advisor "Which noise-cancelling headphones under 200 euros do you have?"; echo "exit: $LASTEXITCODE"`
  2. `uv run advisor "Hello, what can you do?"; echo "exit: $LASTEXITCODE"`
  3. Optional, with Langfuse up: open step 1's trace.
  4. `Remove-Item Env:ADVISOR_MODEL_PROVIDER`
- you should see:
  - step 1: an answer citing real ids (P-…) with prices that match `src/advisor/data/catalogue.json`, which shows the tool round trip works; then `exit: 0`, with no traceback and no "model error" line;
  - step 2: a plain-text answer and `exit: 0`;
  - step 3: one generation per model turn with token usage and the served model name, a `search_products` span between them, and no separate Anthropic SDK traces (§5).

## Eval run
- Owed (`uv run advisor-analysis owes-run --base main`: "owed: the diff
  touches src/advisor/models/anthropic_model.py"). It is made at the
  reworked commit in round 2, because this round's verdict changes the
  adapter. The Ollama path doesn't use this adapter, so no flip is expected.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at d6bf4eb:
  - `npm run verify`: exit 0, 860 passed, mypy "Success: no issues found in 31 source files".
  - `npm run check:intent`: ROUTE, shown above.
  - The diff, line by line.
  - Old-versus-new probes over all `ContentBlock` members and unknown tags.
  - Mutants M1–M14. All are killed except M4 (equivalent) and M14 (the proposed fix applied as a probe: 860 passed, which shows no test pins unknown-block handling). Each mutant was restored by copy, and `git status --short` was clean at the end.
- **Coordinator, re-run**, at d6bf4eb:
  - `npm run verify`: kit 438 pass, 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **860 passed**. This matches the reviewer and the implementer.
  - `npm run check:intent`: the same ROUTE text as above, which matches.
  - Surviving mutant M4 (`dict(block.input)` → `block.input`): **860 passed, survived**, which matches the reviewer. Restored by copy; `git status --short` was clean.
  - The MEDIUM finding, confirmed: a `construct_type` probe gives `[('TextBlock', 'text'), ('TextBlock', 'futuristic')]`, and `complete(...).text == 'answerleak'` on the branch.
  - `npm run sdlc:scan -- --sample-due auto --exclude 23`: "nth attested auto change = 6, every 3, sampled: yes".
- Taken on trust: nothing from the implementer's report. Its four mutants match the reviewer's M1, M3, M5 and M6.
