<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §16 plan — An LLM judge for one failure mode, validated against the owner's labels

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A Haiku judge for "an honest answer when nothing fits" (spec B1–B4), run by
`advisor-analysis judge` over a run report with its verdicts in a local
jsonl and as `judge-no-fit` scores on the Langfuse traces (B5, B8–B11), and
validated against the owner's labels by `advisor-analysis judge-validate`
into a committed `evals/judge/validation.md` (B6–B7).

## Risks

- **A key or a real call in the suite.** `make_client("anthropic", …)` and
  `Langfuse(...)` must never run unpatched in a test; tests inject
  `client_factory` and `annotations_factory` (both already parameters of
  `analysis.main`) and use `tests/fake_langfuse_api.py`.
- **Leaking held-out examples into the prompt** (B6): the prompt builder
  takes only the split's few-shot ids; a test asserts no held-out question
  appears in the filled prompt.
- **A judge error counted as a verdict** (B4): parsing returns a distinct
  error value; the agreement maths excludes errors and counts them.
- **Agreement maths that agrees with itself**: rate tests use literal
  counts, including the 0.8 / 30 / 10 boundaries on both sides and an
  owner-fail count of 0 (rate undefined → not trusted).
- **Duplicate scores on rerun** (B9): a deterministic score id; the fake
  API asserts the same ids on a second run.
- **Confusing the judge score with the owner's `pass`** (B10): different
  name, no queue id; `annotation_scores` (§10) filters by queue and name,
  re-read before relying on it.
- **Key redaction** on every new SDK path (§10 round 1's HIGH): errors go
  through `LangfuseAnnotations._call` and `_redact`.
- Reviewed tier and a live check owed (`tracing.py`). Pass 9's list is
  empty. Re-check the line citations below before launch.

## Verified against the codebase

Re-read on `main` at `b211e79`.

- `src/advisor/config.py:22` — `DEFAULT_MODELS = {"ollama": "qwen3:8b", "anthropic": "claude-haiku-5-5"}`.
- `src/advisor/models/__init__.py:17-35` — `make_client(provider, model, *, api_key, base_url)`; never calls the network.
- `src/advisor/models/base.py:74-80` — `ModelTurn(text, tool_calls, usage, model)`; `:83` `ModelClient.complete(system, messages, tools)`.
- `src/advisor/evals/analysis.py:132-141` — `main(argv, *, env, client_factory=make_client, out, err, now, serve, annotations_factory)`.
- `src/advisor/evals/analysis.py:157-180` — `model_client()`: provider from settings, `api_key_variable` check, "Missing {var}: set it in the environment or in .env." exit 2. The judge needs a variant pinned to `anthropic` (B5).
- `src/advisor/evals/analysis.py:69-71` — lazy `from advisor.tracing import make_annotations`.
- `src/advisor/evals/analysis.py:86-115` — subparsers `generate`, `view`, `taxonomy`, `counts`, `queue`, `import`.
- `src/advisor/evals/annotate.py:18` — `SCORE_NAME = "pass"`; `:51-77` the `Annotations` protocol; `:79` `report_stamp`; `:118-140` `case_traces`.
- `src/advisor/evals/modeljson.py:12` — `extract_json(text)`.
- `src/advisor/evals/labels.py:64` — `parse_labels(text) -> dict[str, Label]` (last line wins).
- `src/advisor/evals/report.py:19` — `parse_report(text)`.
- `src/advisor/evals/taxonomy.py:41` — `build_prompt(labels, template)`: the template pattern.
- `src/advisor/tracing.py:176-189` — `LangfuseAnnotations(api, secrets)`, `_call(step, fn)`; `:169` `_redact`; `:221-240` `ensure_score_config` (the pattern for a second config); `:345-359` `make_annotations(env)`.
- Langfuse SDK 5.2.0: `client.api.scores.create(request=[CreateScoreRequest, …])` (synchronous batch, returns results; checked with `inspect.signature`); `client.api.score_configs.get/create` as §10 uses them. Confirm `CreateScoreRequest`'s field names (`id`, `trace_id`, `name`, `value`, `data_type`, `comment`, `config_id`) before relying on them.
- Run report `cases[*].tools`: `[{"name": "search_products", "arguments": {…}, "results": [...], "error": false}]` (e.g. `evals/runs/20261113T072503Z-ollama.json`).
- `tests/fake_langfuse_api.py`, `tests/test_tracing_annotations.py` — §10's fake SDK to extend.

## Subtasks

1. **Pure judge logic** (`src/advisor/evals/judge.py`, new): `in_scope(case)`
   (B1); `conversation(question, tools, answer)` text (B2); `build_prompt(template,
   conversation, examples)` (B3, B6); `parse_verdict(text)` → verdict or error
   (B4); `parse_split(value)` (B6: few-shot ≤ 8, both labels among them, no
   overlap); `agreement(pairs)` → counts, TPR, TNR, errors, trusted and its
   reason (B7); `score_id(stamp, case_id)` (uuid5, B9); `validation_markdown(...)`.
   Tests (AC1–AC3, AC5's maths). Commit.
2. **The prompt** `evals/prompts/judge-no-fit.md`: B3's criterion, the JSON
   answer format, slots for examples and the conversation. Commit.
3. **Langfuse side** (`tracing.py` + the protocol in `annotate.py`):
   `ensure_judge_config()` (BOOLEAN `judge-no-fit`, created if missing, the
   same conflict rule as `pass`) and `write_scores(scores)` via
   `api.scores.create` with the deterministic ids and the config id; every
   call through `_call`. Extend the fake API. Tests (AC6). Commit.
4. **`advisor-analysis judge <report>`** (`analysis.py`): `--split`
   (default `evals/judge/split.json`), `--model`; pinned to `anthropic`
   with the key check before any call; few-shot examples from the split's
   label files and their reports' tools; in-scope cases only; per-case
   stdout lines and a total; writes `evals/judgements/<report name>.jsonl`;
   with Langfuse configured, `run_traces(stamp)` + `case_traces`, config,
   scores, "N scored, k no trace"; without, one line saying only the file
   was written. ERROR lines for model failures; exit 0 when it ran, 2 on
   bad input / missing key / Langfuse error. Tests with fake client and
   fake annotations (AC4, AC6). Commit.
5. **`advisor-analysis judge-validate`**: the held-out set from the split;
   for each, the label file's question and answer plus its report's tools
   (report `evals/runs/<label file stem>.json`; a missing report is a
   reported skip); judge, compare, write `evals/judge/validation.md`
   (B7, `--out` to override). Tests (AC5). Commit.
6. **Initial split** `evals/judge/split.json` from today's in-scope labelled
   conversations (labels whose case is `gen-no-match-*` or
   `gen-budget-too-low-*`, current label): up to 8 few-shot with both labels,
   the rest held out. The live check adds the owner's new labels to
   `held_out`. Commit.
7. **Docs**: README "Error analysis" (the two commands, cost, the score),
   `CLAUDE.md` Commands line and the architecture note (`judge.py` pure;
   the judge score). Commit.
8. **Finish**: verify, check:intent, `status: in-review`, Progress entry.

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1 | each scenario in/out; no dimensions out | widening or narrowing the scope set |
| B2 | conversation text holds question, each call's arguments and rows, answer | dropping results or the answer |
| B3/B6 | filled prompt has exactly the few-shot ids with label and critique; no held-out text | taking all labels; dropping critiques |
| B4 | `{"pass": true}`, `false`, `<think>` + prose, `"pass": "yes"`, missing key, no JSON | treating junk as fail/pass |
| B5 | no `ANTHROPIC_API_KEY` → exit 2, factory never called; provider is `anthropic` even when `ADVISOR_MODEL_PROVIDER=ollama`; `--model` passes through; jsonl fields; label files byte-identical after | provider from settings; key check after the call |
| B6 | split with 9 few-shot, one label only, or overlap → error | dropping a split rule |
| B7 | rates from literal tables; trusted at exactly 0.8/30/10; not at 0.79/29/9; owner-fail 0 → not trusted; errors excluded and counted; disagreements listed | `>=`↔`>`; counting errors as fails |
| B8 | scores sent only for traced cases; "k no trace"; no Langfuse → file only + line | scoring untraced cases |
| B9 | second run sends identical ids | random ids |
| B10 | name `judge-no-fit`, no queue id, config created once, a non-BOOLEAN config of that name → conflict | reusing `pass` |
| B11 | SDK error → exit 2, step named, keys shown as `***` | unredacted error |

All with fakes; no socket, no key.

## Validation

- `npm run verify` green; `npm run check:intent` PASS (FAIL only on the
  owed live check).
- Live check (owed: `tracing.py`, a paid model): with `.env` holding
  `ANTHROPIC_API_KEY` and Langfuse:
  1. label more in-scope conversations through §10's queue (scenarios
     `no-match`, `budget-too-low`) until there are at least 30 held out with
     10 fails; add them to `split.json` `held_out`;
  2. `uv run advisor-analysis judge evals/runs/<report>.json`: stdout lines;
     `judge-no-fit` scores with comments on the traces; run again, no
     duplicate scores;
  3. `uv run advisor-analysis judge-validate`: read `evals/judge/validation.md`
     and its disagreements; commit it.

## Assumptions I made

- `judge.py` is a new pure module but not added to `CORE_CODE` (a kit
  change, Reviewed path); it is tested like core code.
- The judge's Langfuse methods extend the existing `Annotations` protocol
  rather than a sibling protocol (one fake, one factory).
- The validation report's conversations come from the label lines plus
  the matching run report's tool calls; a label file without its report is
  skipped with a line.
- `split.json` is edited by hand (the initial one by the implementer, new
  held-out entries at the live check); no command writes it.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-13: build (subtasks 1-8)

Commits: `5fa5f52` pure judge logic and prompt; `611d990` score config and batch writes in `tracing.py`; `ea6d6a0` `judge` and `judge-validate`; `5e2c032` validate tests; `8b1e194` initial split; docs commit; this entry.

Shipped: `src/advisor/evals/judge.py` (scope, conversation, prompt, verdict, split, agreement, `validation.md`), `src/advisor/evals/judging.py` (the two commands' I/O), `judge-no-fit.md` prompt, `LangfuseAnnotations.ensure_judge_config` / `write_scores` (SDK 5.2.0 `api.scores.create(request=[CreateScoreRequest(id, trace_id, name, value, data_type, comment, config_id, source)])`, `queue_id` left unset), `evals/judge/split.json` (8 few-shot: 4 pass, 4 fail; 9 held out: 6 pass, 3 fail), README and CLAUDE.md. No live call was made; `validation.md` is not committed (the live check produces it).

Tests: 608 before, 678 after (pytest); kit tests 255 unchanged. Mutations checked by backup and restore: `tpr <= MIN_RATE` and a non-Anthropic provider both fail tests.

Divergences from the plan:
- The prompt is `src/advisor/evals/prompts/judge-no-fit.md` (beside `taxonomy.md`), not `evals/prompts/`, which does not exist.
- Prompt written with subtask 1 (the shipped-template test needs it), not as its own commit.
- The `judge` / `judge-validate` bodies are in a new module `judging.py` (analysis.py only parses and dispatches), to keep analysis.py readable.
- `write_scores(scores, config_id)` takes the config id (the command calls `ensure_judge_config` once), and a batch with `rejected > 0` is an `AnnotationError` at step `score-write`.
- `JUDGE_SCORE_NAME` lives in `annotate.py`; `judge` added to the pure-module list in `test_boundaries.py`.
- B7 minimums (30 conversations, 10 fails) count conversations with a verdict (judge errors excluded), and a zero-owner-fail table is "not trusted".
- Extra options `--labels-dir`, `--runs-dir`, `--judgements-dir` (defaults are the repo paths) so tests need no chdir.
- The few-shot examples need their run reports in `evals/runs/` (local, not committed); without one, `judge` exits 2 naming it. `judge-validate` skips a held-out conversation whose report is missing.

### 2026-11-13: review round 1 rework

Commits: this round's single rework commit (hash in `git log`; subject "§16: review round 1 rework"). Tests: 678 before, 683 after (kit 255 unchanged).

Fixes, tests first:
- HIGH (M30): `test_no_owner_pass_means_undefined_tpr_and_not_trusted` (0 owner passes, 30 owner fails: not trusted, "undefined" among the reasons).
- MEDIUM: `_examples` raises `InputError` (exit 2, before any call) for an out-of-scope few-shot case; test `test_an_out_of_scope_few_shot_case_exits_2_before_any_call`.
- MEDIUM (G12): `test_a_partial_langfuse_configuration_writes_the_file_only` (two of three variables: exit 0, "Langfuse is not configured", annotations factory never called).
- LOW (M15): `#c` and `f#` added to `test_duplicates_and_bad_refs_are_errors`.
- LOW stale text: CLAUDE.md (analysis imports `advisor.tracing` for `queue`, `import` and `judge`), the `LangfuseAnnotations` and `make_annotations` docstrings.

Optional items taken: M10 (both slots filled in one `re.sub` pass, with a test); a verdict without a string `reason` is now a judge error (B4: "anything else"), the old `{"pass": true}` case moved to the error tests; the per-run `prompt_sha256` reading is in the README; CLAUDE.md prompt path is `src/advisor/evals/prompts/`.

Mutation checks by backup and restore: M30 (TPR-undefined reason removed), G12 (`all` to `any`) and M15 (`parse_ref` accepting `#c`/`f#`) each fail a test now.

### 2026-11-16: review round 2 rework

Commits: this round's single rework commit (subject "§16: review round 2 rework"). Pre-rebase hashes in the first entry replaced with the post-rebase ones.

- M10b: `test_a_slot_inside_a_conversation_is_not_filled_again` now puts `[[examples]]` and `[[conversation]]` in the conversation and asserts each text appears exactly once, unchanged. Checked by applying the chained-replace mutant (conversation slot filled first) to `judge.py`: the test fails (the `[[examples]]` in the conversation was replaced); file restored by copy.
- Stale docstrings naming only `queue` and `import` now name `judge` (module docstring, exit codes, the `_LANGFUSE_ENV` comment in `analysis.py`; `annotate.py` header).
- `judging.LANGFUSE_ENV` is compared with `tracing.REQUIRED_ENV` in `tests/test_boundaries.py`.
- Left alone, as asked: an empty `reason` still counts as a verdict (owner's call).

### 2026-11-16: live-check amendment

Owner: "accept 16 amendment". Commit: this entry's single commit (subject "§16: live-check amendment: widened judge prompt").

Shipped: `judge-no-fit.md` rewritten to amended B3 (decide "nothing fits" / "something fits" from the results, the pass rule for each, then fail reasons (a) to (e) in either case, with both (b) examples; JSON format, slots and few-shot block unchanged). AC9: `test_the_shipped_template_states_each_rule_of_b3` (12 parametrised assertions). README text on scope updated; no module docstring said "by construction". AC2's test, the data (labels, split, validation, judgements) and `src/advisor/models/` untouched; no temperature change.

Mutation checks (drop each rule from the template by backup and restore): each of the 9 rule lines and the (b) tablet, (b) smartwatch and (a) tail sentences fails its own assertion.

No plan conflict found.

### 2026-11-21: live-check defect: reduced rate counts

Found by the owner's live check: `validation.md` printed the rates as reduced fractions (`0.55 (6/11)` for a 12/22 table, `0.75 (3/4)` for 9/12), because `_rate` printed `Fraction.numerator/denominator`. `_rate(hits, total)` now prints the table's counts; the rates and the trusted decision were already right. Test first: `test_markdown_rates_show_the_table_counts_not_a_reduced_fraction` (failed before the fix); `test_trusted_at_exactly_0_8_30_and_10` had pinned the reduced `4/5` and now asserts `16/20` and `8/10`. Tests: 788 before, 789 after. `validation.md` is regenerated by the owner's next `judge-validate`.

### 2026-11-21: review round 3 rework (manual review, F1 to F5)

Owner's decisions, verbatim: "16 1. accept old files 2. accept current labels 3. update them".

- F1 (AC7, the `20261116T094558Z` judgements): accepted as they are. The owner accepted the pre-amendment judgements of that report and reads AC7 as met. `judge` was not re-run; `evals/judgements/20261116T094558Z-ollama.jsonl` is untouched.
- F2 (AC8, refs without a post-amendment label line): the owner accepts the current labels against AC8. 12 of the 43 refs were relabelled after the amendment; 31 were kept. `evals/labels` is untouched.
- F3: `_RULES` in `tests/test_judge.py` now holds the full sentences of `judge-no-fit.md` lines 10, 13 and 15 (cases and both PASS rules), plus new entries for the line-8 sentence and the line-17 sentence. The prompt is not edited.
- F4: new `test_markdown_rate_is_undefined_with_no_owner_pass` renders `validation_markdown` on a table with no owner pass and asserts `owner pass): undefined`.
- F5: owner-approved hash-only edits. `spec.md` `403b4b5` to `aad9a13` (lines 7, 13, 223, 230; subject "live check data: 26 new held-out labels"); `metadata.yml:9` comment `60635df` to `9f46347` (subject "spec amendment after the live check", no gate value changed); the build entry's hashes in this plan (`a98c115`/`5fa5f52`, `4f16caa`/`611d990`, `8c24a35`/`ea6d6a0`, `8e6fbac`/`5e2c032`, `97f7cf6`/`8b1e194`), each checked by subject in `git log`. Only hashes changed.

Tests: 789 before, 792 after (pytest: 2 new rule entries, 1 F4 test). `npm run verify` green. No change in `src/`.

Mutation checks (backup, apply, `uv run pytest -q`, restore by copy; each fails exactly one test, 791 passed):
- P1 (drop ", or no search was run"): killed by `test_the_shipped_template_states_each_rule_of_b3[case nothing fits]`.
- P2 (drop " and offers only alternatives ... or none"): killed by `[pass when nothing fits]`.
- P4 (drop the line-17 sentence): killed by `[in either case fail]`.
- P5 (drop the line-8 sentence): killed by `[decide the case]`.
- P6 (drop ", as the search results show them"): killed by `[pass when something fits]`.
- E4 (`"undefined"` to `"n/a"` in `judge.py:266`): killed by `test_markdown_rate_is_undefined_with_no_owner_pass`.

### 2026-11-21: review round 4 rework (manual review, F6)

Owner's decision, verbatim: "16 rework".

- F6: in `_RULES` of `tests/test_judge.py`, "case something fits" (line 11), "a implies a fit" (line 19, the whole line; the separate "a says nothing fits when a result does" entry is folded into it and removed), "b other kind" (line 20's first sentence), "c invented details" (line 21) and "d assumed constraint" (line 22) now assert the full text of their line in `judge-no-fit.md`. The prompt is not edited. Test-only change.

Tests: 792 before, 791 after (the folded entry is gone). `npm run verify` green.

Mutation checks (backup by copy, apply, `uv run pytest -q`, restore by copy; each fails exactly one test, 790 passed), all in `test_the_shipped_template_states_each_rule_of_b3`:
- X1 (line 11: drop " as asked"): killed by `[case something fits]`.
- X4 (line 19: drop the parenthesis): killed by `[a implies a fit]`.
- X5 (line 21: drop " (a feature, a spec, stock or a price)"): killed by `[c invented details]`.
- X6 (line 22: drop " and answers within it"): killed by `[d assumed constraint]`.
- P1: `[case nothing fits]`; P2: `[pass when nothing fits]`; P4: `[in either case fail]`; P5: `[decide the case]`; P6: `[pass when something fits]`. All still killed.
