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
