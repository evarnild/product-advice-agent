<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §16 review — An LLM judge for one failure mode, validated against the owner's labels

verdict: rework
tier: reviewed
reviewed-commit: 28aa68c1138c56c2f79d91ba295bf651d26cd8ce
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed (path table: `src/advisor/tracing.py` by meaning;
`review_tier: reviewed`).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 16` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Scope: the rework 6eb1645 and 28aa68c (`auto_round: 2`). The branch was
rebased onto `main` (1687047) before this round, which brought in §13's
merged code; `git range-diff` and a normalised patch comparison show the
§16 `src`/`tests` patches unchanged by the rebase. 699 tests = 624 on
`main` + 70 (round 1) + 5 (rework).

## Round-1 findings: resolution
| Round 1 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| HIGH | M30 undefined TPR could come out trusted | fixed | `test_no_owner_pass_means_undefined_tpr_and_not_trusted` (`tests/test_judge.py:268`); M30, M30b KILLED |
| MEDIUM | few-shot scope not enforced | fixed | `judging.py:133-137` `InputError`; `test_an_out_of_scope_few_shot_case_exits_2_before_any_call`; FS KILLED |
| MEDIUM | G12 partial Langfuse config | fixed | `test_a_partial_langfuse_configuration_writes_the_file_only`; G12 KILLED |
| LOW | M15 `parse_ref` empty parts | fixed | `#c`, `f#` in `test_duplicates_and_bad_refs_are_errors`; M15, M15a, M15b KILLED |
| LOW | stale texts (CLAUDE.md, two tracing.py docstrings) | fixed | all three mention `judge` and the score writes; more of the same class remains (below) |
| worth a look | M10 slot order | taken, partly proved | one `re.sub` pass at `judge.py:94-96`; M10a KILLED, M10b SURVIVED (below) |
| worth a look | `prompt_sha256` per run | taken | README states it |
| worth a look | verdict without `reason` | taken | `judge.py:123-126` → `JudgeError`; consistent with B4 ("anything else is a judge error") and AC3; R1-R3 KILLED |
| worth a look | `CLAUDE.md` prompt path | taken | `src/advisor/evals/prompts/*.md` |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | FAIL on the owed live check only (the owner's) |
| 3 | Behaviour against the spec | pass (B6 scope enforced; B4 reason rule) |
| 4 | Tests prove the behaviour | findings (1): M10b |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (624 + 75 = 699) |
| 7 | Documentation | findings (1): stale docstrings |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 16, feature)
  error: A live check is owed and not recorded. Do the steps in intents/16-llm-judge/review.md → ## Live check, then set live_checked: <date> in intents/16-llm-judge/metadata.yml.
  note:  16 file(s), 1998 line(s) changed outside intents/.
```
FAIL only on the owed live check.

## Findings
- **LOW** `tests/test_judge.py:109-112`: M10b (chained replace,
  conversation first, at `judge.py:96`) survives; the comment at
  `judge.py:95` claims a slot-like string inside the conversation is never
  replaced, but no test puts `[[examples]]` in a conversation. **Needs
  rework:** add `[[examples]]` to the conversation in
  `test_a_slot_inside_a_conversation_is_not_filled_again` and assert the
  text appears exactly once, unchanged.
- **LOW** stale docstrings still naming only `queue` and `import`:
  `src/advisor/evals/analysis.py:5-7`, `:9-12` (Langfuse-error exit codes;
  `judge` exits 2 too), `:65`, and `src/advisor/evals/annotate.py:3` (the
  protocol now has the judge-score methods). **Needs rework:** name
  `judge` and the judge score in those four places.
- **LOW** (worth a look) `judging.py:41`: `LANGFUSE_ENV` is a third copy of
  the variable names with no test against `tracing.REQUIRED_ENV`; reuse
  `analysis._LANGFUSE_ENV` or add it to `tests/test_boundaries.py`.
- **LOW** (worth a look) `judge.py:124-126`: an empty or whitespace
  `reason` is still a verdict.
- **LOW** (worth a look) `plan.md:156`: the Progress entry cites the
  pre-rebase hashes.
- **Coordinator, sequencing.** Needs decision: the live check's step 7
  commits `evals/judge/split.json` (with the new held-out labels),
  `validation.md` and the judgements to the branch, and ship refuses files
  changed after the reviewed commit, so they must be reviewed. Round 3 is
  the last `/auto` round. Either round 3 now reviews only the two LOW
  fixes and the live-check files later need a review by hand, or the
  owner does the live check first and round 3 reviews the LOW fixes and
  the live-check files together.

**Mutants** (one change each, full suite, backup and restore by copy):

| Id | Target | Result | Killed by |
| --- | --- | --- | --- |
| M30 / M30b | `judge.py:239-241` | KILLED | test_no_owner_pass_means_undefined_tpr_and_not_trusted |
| G12 | `judging.py:258` | KILLED | test_a_partial_langfuse_configuration_writes_the_file_only |
| M15 / M15a / M15b | `judge.py:154` | KILLED | test_duplicates_and_bad_refs_are_errors |
| FS | `judging.py:133` | KILLED | test_an_out_of_scope_few_shot_case_exits_2_before_any_call |
| M10a | `judge.py:96` examples first | KILLED | test_a_slot_inside_an_example_is_not_filled_either |
| **M10b** | `judge.py:96` conversation first | **SURVIVED** | (finding) |
| M10c | regex only `[[examples]]` | KILLED | many test_analysis_judge tests |
| M10d | conversation stripped | SURVIVED, equivalent in effect | – |
| R1 / R2 / R3 | `judge.py:124-126` | KILLED | test_anything_else_is_a_judge_error, test_valid_verdicts |

## Not checked
- Real Haiku output (how often a reply lacks `reason`, now an ERROR);
  `system=""`, `tools=[]` with Anthropic.
- The Langfuse batch score `POST`, upsert on `id`, server-side
  `config_id` validation, §10's `import` ignoring judge scores live.
- `validation.md` (not produced; 9 held out, 6 pass / 3 fail).
- `judge` over a few-shot example's own report; non-`ModelError` client
  exceptions; an empty `reason`.
- Round 1's 66 killed mutants not re-run (code unchanged across the
  rebase); §13's code brought in by the rebase (reviewed under §13).

## Live check
- owed: rule 1 (`src/advisor/tracing.py`) and rule 3 (paid model output;
  the Langfuse batch-score endpoint and upsert). Spec AC7, AC8.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge`: `.env`
     with `ANTHROPIC_API_KEY` and the three `LANGFUSE_*`; Langfuse up; pass
     `--runs-dir ../product-advice-agent/evals/runs` (or copy
     `20261113T072503Z-ollama.json` and `20261113T070516Z-anthropic.json`
     into the worktree's `evals/runs/`).
  2. Label more in-scope conversations: `uv run advisor-eval` (Langfuse
     on); `uv run advisor-analysis queue evals/runs/<report>.json --scenario
     no-match`, then `--scenario budget-too-low`; label in Langfuse; `uv run
     advisor-analysis import …`; until `held_out` in `evals/judge/split.json`
     holds ≥30 conversations with ≥10 fails.
  3. `uv run advisor-analysis judge evals/runs/<traced report>.json`.
  4. The same command again.
  5. `uv run advisor-analysis import evals/runs/<that report>.json`.
  6. `uv run advisor-analysis judge-validate`.
  7. Commit `evals/judge/split.json`, `evals/judge/validation.md`,
     `evals/judgements/<report>.jsonl` before the final review round.
- you should see: step 3, one `PASS|FAIL|ERROR <case>: <reason>` line per
  no-match / budget-too-low case (a reply without `reason` shows as an
  ERROR saying the JSON has no string reason; note how many), `wrote N
  verdicts …`, `judge-no-fit: K scored, k no trace`, no key printed; in
  Langfuse one BOOLEAN `judge-no-fit` score per judged trace (source API,
  reason as comment), in no queue, and one `judge-no-fit` config. Step 4:
  still one score per trace. Step 5: no label from a judge score. Step 6:
  the table, both rates `0.xx (a/b)`, errors, model, prompt hash, ≥30
  held out, trusted or not with the reason, every disagreement. A
  score-batch 4xx (`Langfuse score-write failed: …`, keys as `***`) or a
  high ERROR rate is a defect.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge` at 28aa68c; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "158 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "699 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "16 file(s), 1998 line(s)". Matches.
- **Coordinator, re-run:** M30 KILLED by
  test_no_owner_pass_means_undefined_tpr_and_not_trusted; G12 KILLED by
  test_a_partial_langfuse_configuration_writes_the_file_only; M15 KILLED by
  test_duplicates_and_bad_refs_are_errors; FS KILLED by
  test_an_out_of_scope_few_shot_case_exits_2_before_any_call ("1 failed,
  698 passed" each); M10b SURVIVED ("699 passed"). Matches the reviewer
  and the implementer.

**Reviewer, verified:** verify, check:intent, the rebase (range-diff and
patch comparison), the 624 base on `main`, the rework diff in full, the
intent folder edits, 14 mutants, B4/AC3 against the spec and the prompt.

**Taken on trust:** round 1's 66 kills on unchanged code; Anthropic
accepting `system=""`; the Langfuse server upserting on score `id`.

# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 7f4a05313038cda2ec761ed28f4ae3cc0367b3b6
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, by the path table (`src/advisor/tracing.py`, by meaning)
and `review_tier: reviewed`; the HIGH finding would raise it anyway.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 16` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Divergences from the plan, all acceptable (no decision needed): the prompt
sits at `src/advisor/evals/prompts/judge-no-fit.md` beside §9's prompts
(`evals/prompts/` does not exist; the intent says "like §9's"); command
bodies in a new `judging.py` (`judge.py` stays pure, `langfuse` stays in
`tracing.py`); test-seam options `--labels-dir`, `--runs-dir`,
`--judgements-dir` with the repo paths as defaults; B7's minimums count
conversations with a verdict (stricter than the spec's wording).

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (divergences above) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): B6 few-shot scope |
| 4 | Tests prove the behaviour | findings (3 non-equivalent survivors, 1 equivalent) |
| 5 | Conventions | pass (injected client and annotations factories; sockets blocked) |
| 6 | Numbers in prose | pass (608 → 678; split 8 + 9) |
| 7 | Documentation | findings (stale texts) |
| 8 | Guardrails and hygiene | pass (fake keys only; redaction proven) |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 16, feature)
  note:  16 file(s), 1935 line(s) changed outside intents/.
```

### Findings
- **HIGH** `src/advisor/evals/judge.py:236-237`: M30 survives. Without the
  "true-positive rate is undefined" reason, a held-out set with ≥30 owner
  fails and no owner pass comes out **trusted**. **Needs rework:** add to
  `tests/test_judge.py` an agreement over 30 owner fails and 0 owner passes
  that asserts not trusted and "undefined" among the reasons.
- **MEDIUM** `src/advisor/evals/judging.py:123-135`: B6 "Only in-scope
  conversations with a current owner label are used", but `_examples` never
  checks scope for a few-shot entry, so an out-of-scope entry in the
  hand-edited `split.json` enters the prompt silently. **Needs rework:** in
  `_examples`, an out-of-scope few-shot case is an `InputError` (exit 2),
  like a missing report; add a test.
- **MEDIUM** `src/advisor/evals/judging.py:253`: G12 (`all` → `any` over the
  three `LANGFUSE_*` variables) survives. With a partial configuration B8
  wants the file only and the "not configured" line. **Needs rework:** a
  judge test with two of the three variables set: exit 0, the "Langfuse is
  not configured" line, annotations factory never called.
- **LOW** `src/advisor/evals/judge.py:151`: M15 (`parse_ref` accepting `#c`
  or `f#`) survives. **Needs rework:** `#c` and `f#` → `SplitError` in
  `test_duplicates_and_bad_refs_are_errors`.
- **LOW** stale texts: `CLAUDE.md:182-183` (analysis imports
  `advisor.tracing` "only inside `queue` and `import`", now also `judge`);
  `tracing.py:195-197` `LangfuseAnnotations` docstring ("never updates or
  deletes anything"; it now writes scores, replaced by id on rerun);
  `tracing.py:402` `make_annotations` docstring ("`queue` and `import`").
  **Needs rework:** mention `judge` and the score writes in all three.
- **LOW** (worth a look) `judge.py:93-95`: the comment says the slot order
  keeps a slot-like string in a conversation from being replaced, but a
  few-shot example containing `[[conversation]]` would be (M10 equivalent
  for the tests). Fill both slots in one pass or reword the comment.
- **LOW** (worth a look) `judging.py:146-149`: `prompt_sha256` hashes the
  template with the examples and an open conversation slot (one hash per
  run), not B5's per-case filled template; sensible for B7, but not listed
  as a divergence or in README.
- **LOW** (worth a look) `judge.py:122-123`: `{"pass": true}` without a
  `reason` is a verdict with an empty reason; B4 reads "anything else is a
  judge error".
- **LOW** (worth a look, pre-existing) `CLAUDE.md:186` says the prompts are
  `evals/prompts/*.md`; they are under `src/advisor/evals/prompts/`.

**Mutants** (70; one change each, full suite, backup and restore by copy):
66 KILLED, 4 SURVIVED. Survivors: M30 `judge.py:237` (HIGH), G12
`judging.py:253` (MEDIUM), M15 `judge.py:151` (LOW), M10 `judge.py:95`
(equivalent for the tests). Killed, among others: scope widened/narrowed
(M01-M03); conversation rows/answer/failed call/no search (M04-M07);
critique and label in examples (M08-M09); verdict non-boolean/non-object
(M11-M12); random or stamp-less score id (M13-M14, T04); split rules
(M16-M21); error counted as fail (M22, G09, G18); every 0.8/30/10 boundary
(M23-M29); undefined TNR (M31); provider not pinned, key check moved or
dropped, `--model` ignored (G01-G04); few-shot leaking held-out (G07);
`ModelError` uncaught (G08); untraced or errored cases scored (G10-G11);
jsonl appended (G13); validate inversions (G15-G17); dispatch (A01-A02);
tracing score fields, name, `queue_id`, data type, source, config, batch
size, rejected>0, `_call` and redaction (T01-T16).

### Not checked
- Real Haiku output on the prompt; `system=""` and `tools=[]` with
  Anthropic (the same call shape as `generate`/`taxonomy`).
- Whether self-hosted Langfuse accepts the SDK 5.2.0 batch score `POST`
  and upserts on a repeated `id` (B9); server-side `config_id` validation.
- Whether §10's `import` ignores `judge-no-fit` scores on a live server
  (reasoned from the code: no queue, another name).
- `validation.md` (not yet produced); the held-out set is 9 conversations
  (6 pass, 3 fail), so "trusted" needs ~21 more labels with ≥7 fails (AC8).
- `judge` over the report a few-shot example came from (the judge sees its
  own example); non-`ModelError` exceptions from a client.

### Live check
- owed: rule 1 (`src/advisor/tracing.py`) and rule 3 (paid model output;
  the Langfuse batch-score endpoint and upsert). Spec AC7, AC8.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge`, `.env`
     with `ANTHROPIC_API_KEY` and the three `LANGFUSE_*`; Langfuse up. Use
     `--runs-dir ../product-advice-agent/evals/runs` (the few-shot reports
     `20261113T072503Z-ollama.json` and `20261113T070516Z-anthropic.json`
     are there) or copy them into the worktree's `evals/runs/`.
  2. Label more in-scope conversations: `uv run advisor-eval` (Langfuse
     on), `uv run advisor-analysis queue evals/runs/<report>.json --scenario
     no-match` and `--scenario budget-too-low`, label in Langfuse, `uv run
     advisor-analysis import …`; repeat until `held_out` in
     `evals/judge/split.json` holds ≥30 conversations with ≥10 fails
     (`<labels file>#<case id>` entries).
  3. `uv run advisor-analysis judge evals/runs/<traced report>.json`.
  4. The same command again.
  5. `uv run advisor-analysis import evals/runs/<that report>.json`.
  6. `uv run advisor-analysis judge-validate`.
  7. Commit `evals/judge/split.json`, `evals/judge/validation.md`,
     `evals/judgements/<report>.jsonl` (before the final round, so they are
     reviewed content).
- you should see: step 3, one `PASS|FAIL|ERROR <case>: <reason>` line per
  no-match / budget-too-low case, `wrote N verdicts …`, `judge-no-fit: K
  scored, k no trace`, no key printed; in Langfuse one BOOLEAN
  `judge-no-fit` score (source API, reason as comment) per judged trace,
  in no queue, and one `judge-no-fit` config. Step 4: still one score per
  trace, same `K scored`. Step 5: no label line from a judge score. Step
  6: the table, both rates as `0.xx (a/b)`, errors, model, prompt hash,
  ≥30 held out, trusted or not trusted with the reason, every
  disagreement. A score-batch 4xx shows as `Langfuse score-write failed:
  …` with `***` for keys, and is a defect.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge` at 7f4a053; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "144 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "678 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "16 file(s), 1935
  line(s)". Matches.
- **Coordinator, re-run:** M30, G12, M15 and M10 each SURVIVED ("678
  passed"). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, 70 mutants, the SDK 5.2.0
`CreateScoreRequest` fields and `ScoresClient.create` return types, the
split (17 in-scope conversations, 8 + 9, no shared question text), the
608 baseline on `main` by `pytest --collect-only`, no real client in any
test, plan.md edits below Progress only.

**Taken on trust:** Anthropic accepting `system=""` live; the Langfuse
server upserting on score `id`.
