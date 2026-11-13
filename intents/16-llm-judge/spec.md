<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §16 spec — An LLM judge for one failure mode, validated against the owner's labels

Accepted intent: [intent.md](intent.md)

Written against `main` at `5774eeb`.

## Owner's decisions (question round, 2026-11-13)

- **Mode:** one judge for "an honest answer when nothing fits",
  combining `no_product_available` and `irrelevant_alternatives`.
- **Judge model:** "Haiku" (Anthropic, `claude-haiku-5-5`, the
  `DEFAULT_MODELS["anthropic"]` in `src/advisor/config.py:22`).
- **Bar:** "ok with proposal": both agreement rates at least 0.8 on the
  held-out cases; below it the judge is "not trusted" and its verdicts are
  advisory.
- **Output:** "in langfuse score": the verdict is written as a score on
  each eval trace.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `evals/taxonomy.json` | `no_product_available`: "The assistant fails to confirm that no products are available within the specified price range." `irrelevant_alternatives`: "The assistant suggests products that are not relevant to the user's needs." |
| `evals/labels/*.jsonl` (format in `README.md` "Error analysis" item 4) | `case_id`, `label`, `critique`, `labelled_at`, `question`, `answer`; "The last line for a `case_id` is the current label." |
| `intents/9-error-analysis/intent.md` | "an LLM-as-judge with binary output and the owner's critiques as few-shot examples, measured against the owner's labels". |
| `src/advisor/evals/run.py` (report) | Per case: `answer`, `tools` (each call with the products it returned), `dimensions`; top level `started`, `provider`, `model`. |
| `src/advisor/evals/annotate.py:51-77` | The `Annotations` protocol and `run_traces(stamp)`, `case_traces`: how a case is matched to its Langfuse trace (tags `eval`, `run:<stamp>`, `case:<id>`). B9 reuses it. |
| `intents/10-langfuse-annotation/spec.md` | The `queue`/`import` commands read the owner's `pass` scores **by queue**; a judge score outside any queue is not imported as a label. "They never write scores themselves" was §10's limit; this intent lifts it for the judge's own score only. |
| `src/advisor/evals/modeljson.py:12` | `extract_json`: lenient JSON from model output (drops `<think>`), reused for the verdict. |
| `src/advisor/evals/taxonomy.py:41` | The pattern for a prompt built from labels and a committed template in `evals/prompts/`. |
| `CLAUDE.md` | "`langfuse` only in `tracing.py`"; tracing.py is Reviewed tier by meaning and a live-check path. |

## Behaviour

**Which cases are judged**

- **B1.** A case is *in scope* when its `dimensions.scenario` is
  `no-match` or `budget-too-low`: by construction nothing in the
  catalogue fits the request. Other cases and cases without `dimensions`
  are not judged and get no score.

**The judge (pure prompt and parsing, I/O apart)**

- **B2.** The judge gets one conversation: the question, every
  `search_products` call with the products it returned (from the report's
  `tools`), and the final answer. It does not read the catalogue.
- **B3.** The prompt (`evals/prompts/judge-no-fit.md`, committed) states
  the criterion: **pass** when the answer (a) says plainly that nothing
  in the shop fits the request as asked, and (b) offers only alternatives
  that serve the same need, or none; **fail** when it implies a fit that
  the search results do not show, or proposes alternatives of another
  kind. It includes the few-shot examples of B6, each with the owner's
  label and critique.
- **B4.** The model answers JSON `{"pass": true|false, "reason": "<one
  sentence>"}`, read with `extract_json`. Anything else is a judge error
  for that case: recorded, never a pass or fail.

**Running it**

- **B5.** `advisor-analysis judge <report>` judges the report's in-scope
  cases with Haiku (`anthropic`, `claude-haiku-5-5`; `--model` may
  override the model, not the provider), one call per case, and prints
  per case `PASS|FAIL|ERROR <case id>: <reason>` and a total line. It
  writes `evals/judgements/<report name>.jsonl` (committed, like labels):
  one line per case with `case_id`, `pass`, `reason`, `model`,
  `prompt_sha256` (of the filled template), `judged_at` (UTC). It needs
  `ANTHROPIC_API_KEY`; without it, it exits 2 before any call. It never
  edits a label file.
- **B6.** **The split.** `evals/judge/split.json` (committed) names the
  labelled conversations, as `<labels file>#<case_id>`, used as few-shot
  examples (at most 8, both labels represented) and those held out for
  testing. A conversation in one set is never in the other. Only in-scope
  conversations with a current owner label are used.
- **B7.** `advisor-analysis judge-validate` runs the judge on every
  held-out conversation (from its label file's question and answer and its
  report's tool calls), compares with the owner's label, and writes
  `evals/judge/validation.md` (committed): the counts table (owner
  pass/fail × judge pass/fail), the true-positive rate (owner pass, judge
  pass ÷ owner pass), the true-negative rate (owner fail, judge fail ÷
  owner fail), judge errors, the model, the prompt hash, and the verdict
  **trusted** when both rates are at least 0.8 and the held-out set has at
  least 30 conversations with at least 10 fails, else **not trusted** with
  the reason. It also lists each disagreement with both reasons.

**The Langfuse score**

- **B8.** With Langfuse configured (the three `LANGFUSE_*` variables),
  `judge` also writes each verdict as a BOOLEAN score named
  `judge-no-fit` on that case's trace, with the reason as the score's
  comment. The trace is found as §10 finds it (`run:<stamp>` and
  `case:<id>` tags). A case with no trace is counted and skipped. Without
  Langfuse, only the local file is written and a line says so.
- **B9.** Re-running `judge` on the same report replaces, not duplicates,
  each case's `judge-no-fit` score (a deterministic score id from the run
  stamp and case id) and rewrites the local file.
- **B10.** The judge score is never written into an annotation queue and
  never named `pass`, so §10's `import` cannot take it for an owner label.
  The score config `judge-no-fit` (BOOLEAN) is created if missing, like
  §10's `pass` config.
- **B11.** Every Langfuse call goes through `tracing.py` behind the
  `Annotations` protocol (extended) or a sibling protocol; an SDK error
  exits 2 with the step named and keys redacted, as §10 does.

## Interpretations

- **"One failure mode"** (intent) is the owner's combined mode: the two
  taxonomy modes co-occur in the critiques ("Proposing smartwatches as a
  replacement for headphones. Also, there are no objects for less than 40
  euros").
- **"Validated on 30 cases"** is read as 30 held-out labelled
  *conversations* (a case in a given run), since the same case answered
  by different runs or models is a different conversation to judge.
- **"In scope by scenario"** rather than by the search results: the
  scenario is fixed by the probe check (§9), and a model that did not
  search (no results) still owes an honest no-fit answer.
- **The judge does not see the catalogue** (intent question 7): only what
  the model saw, so its verdict survives catalogue changes (§13).

## Acceptance criteria

- **AC1** (B1): scope tests: no-match and budget-too-low in, every other
  scenario and no dimensions out. (test)
- **AC2** (B2, B3, B6): the filled prompt contains the question, each
  tool call with its rows, the answer, and exactly the split's few-shot
  examples with label and critique; nothing from the held-out set. (test)
- **AC3** (B4): verdict parsing: valid JSON both ways, `<think>` blocks,
  prose around JSON, a missing or non-boolean `pass` → error. (test)
- **AC4** (B5): `judge` over a fake model client writes the jsonl lines
  and the stdout lines; without `ANTHROPIC_API_KEY` it exits 2 with no
  call; labels untouched. (test)
- **AC5** (B7): `judge-validate` over a fake client and fixture labels:
  the table, both rates, the trusted / not trusted rule at the 0.8, 30
  and 10 boundaries, the disagreement list. (test)
- **AC6** (B8–B11): a fake Langfuse API receives one BOOLEAN
  `judge-no-fit` score per traced case with the reason as comment and a
  deterministic id; a second run sends the same ids; no queue call; the
  config is created once; SDK errors exit 2 with keys redacted. (test)
- **AC7** (live check, owed: `tracing.py`, a paid model): the owner runs
  `judge` on a real report with Langfuse on, sees the scores and comments
  on the traces, reruns without duplicates, and runs `judge-validate`;
  `validation.md` is committed with its verdict.
- **AC8** (B6): the owner has labelled enough in-scope conversations for
  B7's minimums (today about 12 in scope; labelling more through §10's
  queue is part of the live check), and `split.json` is committed.

## Non-functional

- **Boundaries:** prompt building, scope, split handling, verdict parsing
  and the agreement maths are pure (new module `src/advisor/evals/judge.py`);
  `analysis.py` does the I/O; `langfuse` stays in `tracing.py`; the model
  call goes through the existing `ModelClient` (`make_client`).
- **Data:** synthetic conversations; the owner's critiques go into the
  committed prompt as few-shot examples (no personal data).
- **Model use:** Haiku, only on the owner's command; one call per in-scope
  case (about 20 per 50-case run, cents). The suite fakes it. If the model
  is down or answers badly, that case is an ERROR, never a verdict.
- **Autonomy:** the judge writes only its own score and files; it never
  changes a label, a queue, or the code checks' result.
- **Tier:** Reviewed (`tracing.py`); live check owed.

## Out of scope

- Judges for other modes; using the judge's verdict in pass/fail of
  `advisor-eval`; Langfuse's built-in LLM-as-a-judge evaluators; prompt
  fixes the judge points to; running evals on every change (§17).

## Assumptions I made

- **The local jsonl and `validation.md` exist besides the Langfuse score**:
  validation needs the verdicts next to the owner's labels, and the files
  make the result reviewable in git. The score is the place to look at
  them per trace, as the owner asked.
- **Scope by scenario** (B1), and the conversation as the unit (B7).
- **At most 8 few-shot examples**, chosen by the owner or the implementer
  and committed in `split.json`; the held-out minimums are 30 and 10
  fails.
- **Score name** `judge-no-fit`, **files** under `evals/judgements/` and
  `evals/judge/`, **commands** `judge` and `judge-validate`.
- `review_tier` rises to **reviewed** (tracing.py).
