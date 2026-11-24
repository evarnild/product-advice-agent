<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §24 review — Constrain the LLM judge's reply to its verdict schema

verdict: escalate
tier: reviewed
reviewed-commit: 4ec3673
main: 40b3da7
round: 3
sampled: yes
run: auto
live-check: owed

The live check is recorded. No finding needs rework on the branch. The tier
stays Reviewed, so you read the diff again. Since your last read, only
`evals/judge/validation.md` and metadata changed, plus main's merge.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: since round 2 the branch adds only the committed re-validation (subtask 6) and metadata |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: AC11 met for the 9 conversations that could be judged; AC12 is the fresh eval run below |
| 4 | Tests prove the behaviour | pass: the branch's src and tests are unchanged since round 2, where all 34 mutants were killed |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: `validation.md` re-rendered byte-identical |
| 7 | Documentation | pass (this report states the shortfall; see below) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check
```
type-check: PASS (intent 24, feature)
  note:  17 file(s), 408 line(s) changed outside intents/.
```

- **The merge 7f5a3d9 is automatic.** `git merge-tree --write-tree` of its
  parents gives `9a2a4d0c…`, equal to its tree.
- `git diff 04292f4 HEAD -- src tests` is exactly main's §25 patch.
  `src/advisor/models`, `judge.py`, `judging.py` and the judge prompt are
  unchanged since 63211c5.

## The re-validation (`evals/judge/validation.md`, committed at 8d64656)
- **Only 9 of the 35 held-out conversations were judged.** The other 26
  were skipped because their run reports are not in `evals/runs/` on this
  machine (the folder is gitignored):
  - `20261116T094326Z-ollama.json`, 20 conversations;
  - `20261116T094558Z-ollama.json`, 6 conversations.

  So the file's rates are on 9 conversations, **not comparable** with the
  old 35-conversation rates.
- **Full-set figures, for the record:**
  - old: true-positive rate 0.52 (11/21), true-negative rate 0.75 (9/12),
    2 judge errors, on 35;
  - new: 0.60 (3/5), 1.00 (4/4), 0 judge errors, on 9.

  The file says "not trusted": 9 is below the 30 it needs.
- **Like-for-like on the same 9 conversations** (old verdicts from the
  round-2 `validation.md`):

  | | old judge, prompt a6cff797 | new judge, prompt d007ff8c |
  | --- | --- | --- |
  | true-positive rate | 2/4 | 3/5 |
  | true-negative rate | 4/4 | 4/4 |
  | judge errors | 1 | 0 |

  - The old error `20261113T070516Z-anthropic.jsonl#gen-budget-too-low-3`
    ("holds no JSON object") is now a verdict that agrees with your label.
  - The other old error (`gen-no-match-4`) is among the skipped, so it is
    untested.
- **Faithful:** the reviewer re-rendered the file offline from `split.json`,
  the labels, the run reports and the judge's verdicts, and got it
  byte-identical. The prompt sha256 `d007ff8c…` reproduces from the
  template and the 8 few-shot examples.

## Findings
None open. Round 3 raised three, all resolved in this report:
- **The eval run** was compared against a moved baseline. A fresh run was
  made (below).
- **The skipped conversations:** this report states them, above.
- **Who ran the live check:** this report says it, below.

## Not checked
- The judge on the 26 skipped conversations. A full 35-conversation
  re-validation needs those two run reports restored or regenerated: a
  possible follow-up, not a finding against this branch.
- The judge's verdicts and reasons themselves (model output).

## Live check
- owed: rule 1 (`src/advisor/models/`). **Recorded:** `live_checked:
  2026-11-24 by-agent    # owner: "24 live checked, accept the
  9-conversation validation"`.
- **The coordinator made the run, with your key and at your request, and
  you accepted it.** REVIEW-POLICY.md "Live checks" says an agent's own run
  is evidence, not the gate. You gave the gate after reading the evidence.
- What it covered:
  - `judge-validate` on `claude-haiku-5-5` completed with the verdict
    schema: 9 judged, 0 judge errors. So Haiku accepted `output_config` with
    `tools=[]`.
  - One `ADVISOR_MODEL_PROVIDER=anthropic uv run advisor "A cheap phone that
    is in stock"` run answered with 5 in-stock phones (P-489, P-016, P-226,
    P-466, P-015), whose names, prices (€129–€249) and stock match the
    catalogue, then `exit: 0`.

## Eval run
- Report `evals/runs/20261124T215703Z-ollama.json` (copied to the main
  checkout). Provider ollama, model qwen3:8b, made in the worktree at
  4ec3673. It started 21:57:03Z, after the commit at 21:52:13Z.
- Content check: its `cases_sha256` d5f5e275, `prompt_sha256` c2a38987 and
  `catalogue_sha256` c2e56cb2 equal the worktree's files.
- `compare` against `evals/baseline.json` (§25's run, 39/50): this run
  **38/50**.
  - Regressed 1: `tv-sound`. It passed when re-run alone (`advisor-eval
    --only tv-sound`, `20261124T220941Z-ollama.json`), so it is not a
    regression.
  - Fixed 0, added 0, removed 0.
- No hash warning: the baseline and this run both hash this machine's CRLF
  checkout.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 4ec3673:
  - `npm run verify`: exit 0, 902 passed.
  - `npm run check:intent`: PASS.
  - The merge-tree identity.
  - The `src`/`tests` diff equals main's §25 patch.
  - The offline re-render of `validation.md`.
  - The like-for-like table.
  - The eval hashes, and the round-1 report re-scored with the merged
    scorer (identical statuses).
  - No mutation; clean.
- **Coordinator, re-run**, at 4ec3673:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **902 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 24, feature)`, which matches.
  - Merge-tree of 7f5a3d9's parents: `9a2a4d0c1d7eace687ba692772e9503d3128f1e1`, equal to its tree, which matches.
  - The fresh eval run, `compare` and the `--only` re-run, as above.
  - `npm run sdlc:scan -- --sample-due auto --exclude 24`: "nth attested auto change = 9, every 3, sampled: yes".
- Taken on trust: the judge's verdicts and reasons.

---

# Round 2

verdict: escalate
tier: reviewed
reviewed-commit: 04292f4
main: c98c879
round: 2
sampled: no
run: auto
live-check: owed

The tier stays Reviewed (round 1's HIGH, rule 3). No finding needs rework.
**You read the diff** (`git diff main...feat/24-judge-structured-output`),
then run the live check below.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the rework (6775d96) changes tests only, plus a Progress entry |
| 2 | Type check | FAIL only on the owed live check, which is yours to clear |
| 3 | Behaviour against the spec | pass: same code as round 1; AC11 owed; AC12 covered by round 1's run |
| 4 | Tests prove the behaviour | pass: all 34 round-1 mutants are now killed |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (885) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check
```
type-check: FAIL (intent 24, feature)
  error: A live check is owed and not recorded. Do the steps in intents/24-judge-structured-output/review.md → ## Live check, then set live_checked: <date> in intents/24-judge-structured-output/metadata.yml.
  note:  16 file(s), 332 line(s) changed outside intents/.
```

- **Round 1 resolved:**
  - A5 and A16 are killed by the two `max_tokens` assertions
    (`tests/test_models.py:187`, `:199`);
  - J8 is killed by the bare-fence case.
- `git diff 63211c5 HEAD -- src` is empty.
- **The merge ffae26b is automatic** (merge-tree equals its tree). It
  brings only §28's metadata and plan from main.

## Findings
None open.

## Not checked
- Whether `claude-haiku-5-5` accepts `output_config.format` with `tools=[]`,
  the property order the API generates, and the real `stop_reason` for a
  structured refusal. Only the live check shows these (rule 1; rule 3 for
  this item).

## Live check
- owed: rule 1 (`src/advisor/models/`), and the Not-checked item above. In
  the worktree `C:/Users/eric/src/product-advice-agent-wt/24-judge-structured-output`,
  with `ANTHROPIC_API_KEY` set. It costs about 35 Haiku calls plus one
  `advisor` run.
- steps:
  1. `uv run advisor-analysis judge-validate --runs-dir C:/Users/eric/src/product-advice-agent/evals/runs`
  2. Open `evals/judge/validation.md`.
  3. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"; uv run advisor "A cheap phone that is in stock"; echo "exit: $LASTEXITCODE"; Remove-Item Env:ADVISOR_MODEL_PROVIDER`
  4. Commit the new `evals/judge/validation.md` on the branch (or ask me
     to). A further review round then covers it: it must be inside that
     round's reviewed commit.
- you should see:
  - step 1 completes over the 35 held-out conversations. Failure looks like
    `ERROR <ref>: Anthropic call failed: BadRequestError` on every one.
  - in `validation.md`:
    - no judge error reading "the model answer is not a JSON object", "the
      JSON has no boolean 'pass'" or "the JSON has no string 'reason'";
    - a named refusal, cut-off or API error is allowed;
    - the prompt sha256 differs from a6cff797…;
    - the old rates for comparison: true-positive rate 0.52 (11/21),
      true-negative rate 0.75 (9/12), 2 judge errors.
  - step 3: a normal answer citing real ids with prices, then `exit: 0`.

## Eval run
- Round 1's report `evals/runs/20261124T204309Z-ollama.json` (qwen3:8b,
  made at 63211c5) still covers this commit. `src` is unchanged, and its
  hashes (cases d5f5e275, prompt c2a38987, catalogue c2e56cb2) equal the
  files at 04292f4.
- `compare`: 38/50 against 39/50. The one flip, `basic-phone`, passed on
  its `--only` re-run (`20261124T205326Z-ollama.json`), so it is not a
  regression.

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 04292f4:
  - `npm run verify`: exit 0, 885 passed.
  - `npm run check:intent`: FAIL on the live check only.
  - The empty `src` diff, merge-tree identity and the three hashes.
  - A5, A16 and J8 killed.
  - Clean worktree at the end.
- **Coordinator, re-run**, at 04292f4:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **885 passed**, which matches.
  - `npm run check:intent`: the same FAIL (live check only), which matches.
  - Mutants the rework says it kills:
    - A5 (`anthropic_model.py:105`): **killed**, 1 failed.
    - A16 (`:91`): **killed**, 1 failed.
    - J8 (`judge.py:130`): **killed**, 1 failed.
    - All match. Restored by copy; `git status --short` was clean.
- Taken on trust: round 1's 31 other killed mutants (`src` unchanged since).

---

# Round 1

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
