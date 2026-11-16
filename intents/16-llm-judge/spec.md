<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §16 spec — An LLM judge for one failure mode, validated against the owner's labels

Accepted intent: [intent.md](intent.md)

Written against `main` at `5774eeb`. Amended 2026-11-16 after the live
check, against the branch at `403b4b5` (on `main` `89fa3b7`; `main` is now
`b2e2815`).

## Amendment (2026-11-16, after the live check)

The first live check ran the mechanics end to end and came out **not
trusted** (`evals/judge/validation.md` at `403b4b5`: true-positive rate
0.61 (14/23), true-negative rate 0.64 (7/11), 1 judge error, 35 held out).
Reading the 14 disagreements showed three causes in the criterion and the
labels, not the model:

- the owner failed answers for reasons B3 did not name: invented product
  details ("The descriptions do not have this level of details",
  `20261116T094326Z-ollama.jsonl#gen-no-match-2`) and an assumed
  constraint ("price between 200 and 500 was not in the question",
  `20261116T094558Z-ollama.jsonl#gen-no-match-3`);
- several `budget-too-low` conversations had searches that **did** return
  a fitting product (`20261116T094326Z-ollama.jsonl#gen-budget-too-low-6`,
  `-7`, `-8`, `-9`, `-11`, `-15`; `20261116T094558Z-ollama.jsonl#gen-budget-too-low-13`),
  so B1's "by construction nothing in the catalogue fits" did not hold and
  the judge graded them against a precondition that was false;
- labels and few-shot examples disagreed on alternatives of another kind.

Changed: **B1** (scope reason), **B3** (the criterion), **AC2**, **AC7**,
**AC8**, a new **AC9**, the Interpretations on scope and alternatives, and
Assumptions. Unchanged: the score name, the split rules, the trusted bar,
the commands and every Langfuse rule.

Also seen, not decided: 4 of 26 verdicts flipped between two `judge` runs
on the same report. The Anthropic adapter sets no temperature
(`src/advisor/models/anthropic_model.py:73` passes `max_tokens` only), so
the API default applies. See Assumptions.

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

## Owner's decisions (live-check amendment, 2026-11-16)

- **Widen the criterion:** "Invented details, Assumed constraints, Fit
  exists, handled right" (all three proposed additions).
- **Alternatives of another kind:** "Fail unless it fits": fail only when
  the other kind does not serve the customer's need; the prompt spells the
  nuance out.
- **Relabel:** the owner relabels under the widened criterion.
- **Judge model:** stays Haiku ("you used haiku so we are good").

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
  `no-match` or `budget-too-low`: the question was written so that nothing
  fits, but the searches may still return a product that does (amended
  2026-11-16). Other cases and cases without `dimensions` are not judged
  and get no score.

**The judge (pure prompt and parsing, I/O apart)**

- **B2.** The judge gets one conversation: the question, every
  `search_products` call with the products it returned (from the report's
  `tools`), and the final answer. It does not read the catalogue.
- **B3.** The prompt (`src/advisor/evals/prompts/judge-no-fit.md`,
  committed) states the criterion (amended 2026-11-16). The judge first
  decides from the search results which case it is in:
  - **Nothing fits** (no search returned a product that meets the request
    as asked, or no search was run): **pass** when the answer says plainly
    that nothing in the shop fits the request as asked, and offers only
    alternatives that serve the customer's need, or none.
  - **Something fits** (a search returned a product that meets the request
    as asked): **pass** when the answer offers only such products, as the
    results show them.

  In either case the answer **fails** when it:
  - (a) implies a fit the search results do not show (names a product no
    search returned, or one outside the stated budget or requirement, as if
    it met the request), or says nothing fits when a result does;
  - (b) proposes an alternative of another kind that does not serve the
    customer's need. Another kind that does serve it passes (a tablet for
    someone who wants a laptop to take notes on); one that does not fails
    (smartwatches for someone who asked for headphones). The prompt gives
    both examples;
  - (c) states product details the search results do not show (a feature,
    a spec, stock, a price) as facts;
  - (d) assumes a constraint the customer never gave (a budget, a price
    range, a requirement) and answers within it;
  - (e) hides that nothing fits.

  It includes the few-shot examples of B6, each with the owner's label and
  critique.
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
  search (no results) still owes an honest no-fit answer. Amended: the
  scenario says what the question was *written* to test, not what the
  searches found, so the judge reads the results to choose between
  "nothing fits" and "something fits" (B3). A product "fits" when its
  returned row meets every stated requirement, price included.
- **"Serves the same need"** (B3 b) is the customer's purpose as the
  question states it, not the product category: laptop -> tablet can serve
  "something to take notes in lectures"; headphones -> smartwatch serves
  "something to listen to music on" in no reading.
- **"Details the results do not show"** (B3 c): a fact in the answer is
  shown when a returned row holds it (name, price, stock, the fields the
  tool returns). General knowledge about a product kind ("planar headphones
  usually need an amplifier") is not a product detail.
- **The judge does not see the catalogue** (intent question 7): only what
  the model saw, so its verdict survives catalogue changes (§13).

## Acceptance criteria

- **AC1** (B1): scope tests: no-match and budget-too-low in, every other
  scenario and no dimensions out. (test)
- **AC2** (B2, B3, B6): the filled prompt contains the question, each
  tool call with its rows, the answer, and exactly the split's few-shot
  examples with label and critique; nothing from the held-out set. (test)
- **AC9** (B3, amended): the shipped template states both cases ("nothing
  fits", "something fits") and each fail reason (a) to (e), with the two
  alternative examples of (b). (test on the committed file: one assertion
  per rule, so dropping a rule fails it)
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
  `validation.md` is committed with its verdict. Amended: done once on
  2026-11-16 for the mechanics (`403b4b5`); after the relabel and the new
  prompt, `judge` on both 2026-11-16 reports and `judge-validate` run
  again and the new `validation.md` and judgements are committed. The
  verdict may be either; the report must give it with its reason.
- **AC8** (B6): the owner has labelled enough in-scope conversations for
  B7's minimums (today about 12 in scope; labelling more through §10's
  queue is part of the live check), and `split.json` is committed.
  Amended: done at `403b4b5` (35 held out, 11 fails). The owner then
  relabels the 43 conversations in `split.json` (few-shot and held out)
  under the amended B3; the new label lines are committed, and the
  split's few-shot set still has both labels after the relabel (B6),
  else the owner swaps examples.

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
- **Score name stays `judge-no-fit`** (amendment): every in-scope question
  is still written as a no-fit request, so the name still says what is
  judged; renaming would touch the constant, the config, the tests and the
  docs, and leave 26 orphan scores on the live-check traces.
- **No temperature change in this amendment.** Setting it is a change to
  `src/advisor/models/` (a live-check path) and the owner has not decided
  it; the flip rate is reported here instead. If the relabelled run is
  still not trusted, temperature 0 for the judge is the first thing to
  try, as its own decision.
- **How the owner relabels:** the 2026-11-16 runs are traced, so through
  §10's queues and `import`; the 2026-11-13 runs have no traces, so through
  `advisor-analysis view` (a new line per case; the last line wins). No
  command edits a label for the owner.
- **The few-shot examples are relabelled too**, since the judge "follows
  the owner's verdicts and critiques"; an example labelled under the old
  criterion would teach it the old rule.
