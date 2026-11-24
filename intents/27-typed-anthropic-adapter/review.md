<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §27 review — Type the Anthropic adapter against the SDK's own types

verdict: attest
tier: attested
reviewed-commit: 192ccc2
main: 40c447d
round: 3
sampled: no
run: auto
live-check: owed

This round exists because main was merged into the branch since round 2.
That merge brought origin's §23 (Langfuse memory caps) and the renumber
of this intent from §23 to §27. The deliver preconditions count a merge of
main as unreviewed change. The branch's own code is unchanged since round 2.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | ROUTE, reason stated: only the fake's construction lines in tests/test_models.py were replaced, no assertion changed (as in rounds 1 and 2) |
| 3 | Behaviour against intent | pass (unchanged since round 2) |
| 4 | Tests prove the behaviour | pass |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1 LOW) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass (list empty) |

## Type check
```
type-check: ROUTE (intent 27, refactor)
  route: Declared refactor, but existing tests lost lines (tests/test_models.py). Behaviour may have changed — check, or route to feature.
  note:  2 file(s), 106 line(s) changed outside intents/.
```
The ROUTE is round 1's, explained there: only the fake's construction
lines were removed, and no assertion changed. The live-check error is gone,
because the check is recorded.

- **The branch's own change is unchanged.** `git diff 5f7a773...8fddf12 --
  src tests` (round 2) and `git diff main...HEAD -- src tests` (now) are
  byte-identical.
- **The merge (bc795e2) is the automatic one.** `git merge-tree
  --write-tree 6e272e5 40c447d` gives exactly its tree, and `git show --cc
  bc795e2` is empty.
- **The renumber is complete.** The only §23 leftovers are on purpose: the
  pasted check:intent output in the rounds below, and the owner's quotes
  in `metadata.yml`.

## Findings
- **LOW** `intents/27-typed-anthropic-adapter/plan.md:206-207` — the
  renumber rewrote the quoted commit subjects in the Progress entry to
  "§27: …". The commits (994e273, 1cb69f2, 30ffd4a) still say "§23: …".
  Worth a look; it doesn't block.

## Not checked
- The real Anthropic API response path, and the judge path through the
  adapter. The recorded live check covers the first; no model was called.
- main's merged content beyond its tests passing. §23 (memory caps) was
  reviewed and live-checked on its own branch on the other machine.

## Live check
- owed: rule 1 (`src/advisor/models/`). **Recorded:** `live_checked:
  2026-11-24 by-agent    # owner: "23 live checked"` (b992942). It was given
  while this intent was still §23 on this machine. The code is unchanged
  since, so the check still covers it.

## Eval run
- Report `evals/runs/20261124T183001Z-ollama.json` (round 2, in the main
  checkout), ollama / qwen3:8b. It still covers this commit's content: its
  `cases_sha256` a81f06ad, `prompt_sha256` c2a38987 and `catalogue_sha256`
  c2e56cb2 equal the sha256 of the files at 192ccc2.
- Comparison as in round 2: 38/50 against 38/50.
  `headphones-ldac-balanced-200` flipped and passed again on its `--only`
  re-run, so it isn't a regression. Fixed 1: `gaming-monitor`.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 192ccc2:
  - `npm run verify`: exit 0, 863 passed.
  - `npm run check:intent`: ROUTE only.
  - Merge-tree recomputation, `--cc` and the byte-identical diff, as above.
  - Renumber diffs, file by file.
  - Mutants M1, M3, M15 and M16 all killed. Restored by copy; `git status --short` was clean.
- **Coordinator, re-run**, at 192ccc2:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **863 passed**, which matches.
  - `npm run check:intent`: `type-check: ROUTE (intent 27, refactor)`, which matches.
  - No mutant survives this round, and the code is unchanged, so there are no mutants to re-run.
  - Content hashes of `evals/cases.jsonl`, `src/advisor/prompts/system.md` and `src/advisor/data/catalogue.json` at 192ccc2: a81f06ad, c2a38987, c2e56cb2. These match the eval report.
  - `npm run sdlc:scan -- --sample-due auto --exclude 27`: "nth attested auto change = 7, every 3, sampled: no".
- Taken on trust: nothing.

---

# Round 2

verdict: attest
tier: attested
reviewed-commit: 8fddf12
main: 5f7a773
round: 2
sampled: yes
run: auto
live-check: owed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | FAIL only on the owed live check; the ROUTE is the same as round 1's, explained there |
| 3 | Behaviour against intent | pass: round 1's MEDIUM is resolved |
| 4 | Tests prove the behaviour | pass (M4 from round 1 is an equivalent survivor; no action) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (862 passed, reproduced) |
| 7 | Documentation | findings (1 LOW) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass (list empty) |

## Type check
```
type-check: FAIL (intent 23, refactor)
  error: A live check is owed and not recorded. Do the steps in intents/27-typed-anthropic-adapter/review.md → ## Live check, then set live_checked: <date> in intents/27-typed-anthropic-adapter/metadata.yml.
  route: Declared refactor, but existing tests lost lines (tests/test_models.py). Behaviour may have changed — check, or route to feature.
  note:  2 file(s), 106 line(s) changed outside intents/.
```
- The only error is the owed live check, which is the owner's to clear.
- The ROUTE is round 1's. The rework (2ec8c95..8fddf12) removed no test line; it only added two tests.

Round 1's finding is resolved. `anthropic_model.py:91,93` now pair the
`isinstance` with the tag check (`and block.type == "text"` / `"tool_use"`).
The unknown-tag probes now give `'answer'` for both shapes, the same as
`main`. Two new tests pin this:
- `test_adapter_ignores_text_shaped_blocks_with_an_unknown_tag` (tests/test_models.py:239);
- `test_adapter_ignores_tool_shaped_blocks_with_an_unknown_tag` (tests/test_models.py:247). It is defensive: SDK 2.6.0 builds unknown blocks as `TextBlock`, but the test keeps the tool-side tag check.

## Findings
- **LOW** `intents/27-typed-anthropic-adapter/plan.md` (round-1 rework
  Progress entry) — it says the SDK "falls back to
  `TextBlock`/`ToolUseBlock`". In 2.6.0 it falls back only to `TextBlock`.
  A wording slip in the implementer's own section. Worth a look; no rework.

## Not checked
- The real Anthropic API response path. Responses are built in memory
  with the SDK's constructors; the live check covers the real API.
- The judge path (`evals/judging.py`) through this adapter against the
  real API. No model was called.

## Live check
- owed: rule 1 (`src/advisor/models/`), covering the "real API response
  path" item. Run it in the worktree
  `C:/Users/eric/src/product-advice-agent-wt/27-typed-anthropic-adapter`,
  in PowerShell, with `ANTHROPIC_API_KEY` in `.env`. It costs a few
  Anthropic calls.
- steps:
  1. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"; uv run advisor "Which noise-cancelling headphones under 200 euros do you have?"; echo "exit: $LASTEXITCODE"`
  2. `uv run advisor "Hello, what can you do?"; echo "exit: $LASTEXITCODE"`
  3. Optional, with Langfuse up: open step 1's trace.
  4. `Remove-Item Env:ADVISOR_MODEL_PROVIDER`
- you should see:
  - step 1: an answer citing real ids (P-…) with prices that match `src/advisor/data/catalogue.json` (the tool round trip works), then `exit: 0`, with no traceback and no "model error" line;
  - step 2: a plain-text answer and `exit: 0`;
  - step 3: one generation per model turn with token usage and the served model name, a `search_products` span between them, and no separate Anthropic SDK traces (§5).

## Eval run
- Report `evals/runs/20261124T183001Z-ollama.json` (copied to the main
  checkout). Provider ollama, model qwen3:8b, made in the worktree at
  33276bc.
  - That commit differs from the reviewed 8fddf12 only in
    `metadata.yml` (`auto_stopped`), so the content is the same.
  - Its `cases_sha256` a81f06ad, `prompt_sha256` c2a38987 and
    `catalogue_sha256` c2e56cb2 equal the worktree's files.
- `advisor-analysis compare`: baseline 38/50, this run **38/50**.
  - Regressed 1: `headphones-ldac-balanced-200`. Re-run with
    `advisor-eval --only headphones-ldac-balanced-200`
    (`20261124T185936Z-ollama.json`): **PASS**. Not a regression: a single
    run varies.
  - Fixed 1: `gaming-monitor`. Added 0, removed 0.
- The `cases_sha256` warning against the baseline is the CRLF checkout of
  the same file. `main`'s committed `evals/cases.jsonl` hashes to the
  baseline's b7a88ce6.
- As expected: the Ollama path does not use this adapter.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 8fddf12:
  - `npm run verify`: exit 0, 862 passed.
  - `npm run check:intent`: FAIL on the live check only.
  - The rework diff, read line by line.
  - Unknown-tag probes.
  - Mutants M1, M2, M3, M5, M6, M15 and M16 all killed.
- **Coordinator, re-run**, at 8fddf12:
  - `npm run verify`: kit 438 pass, 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **862 passed**, which matches.
  - `npm run check:intent`: the same FAIL (live check) and ROUTE, which matches.
  - Mutants the rework says it kills:
    - M15 (drop `and block.type == "text"`): **killed** by `test_adapter_ignores_text_shaped_blocks_with_an_unknown_tag`.
    - M16 (drop `and block.type == "tool_use"`): **killed** by `test_adapter_ignores_tool_shaped_blocks_with_an_unknown_tag`.
    - Both match the reviewer and the implementer. Restored by copy; `git status --short` was clean.
  - The eval run, `compare` and the `--only` re-run, as above.
- Taken on trust: nothing.

---

# Round 1

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
  `C:/Users/eric/src/product-advice-agent-wt/27-typed-anthropic-adapter`,
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
  - `npm run sdlc:scan -- --sample-due auto --exclude 27`: "nth attested auto change = 6, every 3, sampled: yes".
- Taken on trust: nothing from the implementer's report. Its four mutants match the reviewer's M1, M3, M5 and M6.
