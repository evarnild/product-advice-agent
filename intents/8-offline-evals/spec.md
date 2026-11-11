<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §8 spec — An offline eval suite that scores the advisor's answers against a fixed question set

Accepted intent: [intent.md](intent.md)
Written against `main` at `210e0b1`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Owner's decisions

| Question | Owner's answer | When |
| --- | --- | --- |
| How the suite is started | **`uv run advisor-eval`**: a second console script in `pyproject.toml`, beside `advisor`; `cli.py` untouched | spec round, 2026-11-11 |
| Runs per case | **One run per case** | spec round |
| Tool-call checks | **The answer, plus optional tool checks**: a case may state expected `search_products` arguments, read through a recording `Tracer` | spec round |
| Report | **Printed, plus a JSON file** (gitignored) for comparing runs | spec round |

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/8-offline-evals/intent.md` | Outcome: one command, deterministic checks, a non-zero exit on a failure; the scorers and runner covered by `verify` without a network; the live run not in `verify`. Constraints: through `answer_question` and `make_client`; no provider SDK and no `langfuse` import; synthetic data only; the suite reports and does not gate; leave `prompts/`, `guardrails.py`, `cli.py`, `tracing.py` and the data alone. |
| `src/advisor/prompts/system.md` | "Cite every product you recommend by its name and its id, for example 'Acme One (P-001)', and give its price in euros." "Mention when a recommended product is out of stock." "Stay on the topic … Politely decline other requests." |
| `src/advisor/guardrails.py:14` | `REFUSAL_TEXT = "I can only help with questions about our electronics catalogue."`. Both checks allow everything today, so off-topic declining is the model's job. |
| `src/advisor/agent.py` | `answer_question(question, client, tools, tracer)`, `search_tool(catalogue)`, `MAX_TURNS = 5`, `FALLBACK_ANSWER`. |
| `src/advisor/tracer.py` | The `Tracer` protocol; `tool(name, arguments, result_count, error)` is called once per tool call. |
| `src/advisor/models/__init__.py:17` | `make_client(provider, model, *, api_key=None, base_url=None)`. |
| `src/advisor/config.py` | `load_env`, `load_settings`, `Settings.api_key_variable`, `api_key()`, `ollama_url()`, the defaults (`ollama`/`qwen3:8b`). |
| `src/advisor/data/catalogue.json` | 32 products, 8 categories; prices are floats (all whole euros today). Out of stock: P-004 (headphones, 159), P-010, P-017, P-024, P-032. |
| `CLAUDE.md` → "Architecture" | Pure, tested logic vs I/O; provider SDKs in one module each; `tests/conftest.py` blocks sockets. |

## Behaviour

**Cases**

- **B1.** The cases live in `evals/cases.jsonl` at the repository root, one
  JSON object per line. Each has:
  - `id` (unique short slug) and `question` (string);
  - optional `expect_ids` (ids that must be cited);
  - optional `forbid_ids` (ids that must not be cited);
  - optional `must_decline` (bool);
  - optional `expect_search` (an object of `search_products` argument
    constraints, B9);
  - optional `note` (free text, ignored by scoring).

  Unknown fields are an error.
- **B2.** The case file is validated before any run:
  - every id in `expect_ids` and `forbid_ids` exists in the catalogue;
  - `must_decline` cases have no `expect_ids`;
  - `expect_search` uses only `search_products` argument names.

  A bad file stops the command with exit code 2 and a message naming the
  case and the field. `verify` runs the same validation on the committed
  file.
- **B3.** The committed set has 12 to 20 cases, covering:
  - every category at least once;
  - a budget filter;
  - a case whose honest answer is "nothing matches";
  - an out-of-stock product (P-004 in a headphones-under-200 case);
  - at least two off-topic questions;
  - §7's case: "I need noise-cancelling headphones under 200 euros",
    expecting P-005 and P-001.

**Scoring (pure functions, `src/advisor/evals/score.py`)**

- **B4.** A product is cited when its id appears in the answer as `P-` plus
  three digits (the form the prompt asks for). Names are not matched.
- **B5.** Each answer is scored with these checks, each pass or fail with a
  one-line reason:
  - **grounded:** every cited id exists in the catalogue;
  - **prices:** for every cited id, the product's price appears in the
    answer as a number. A whole price counts in integer form ("189") or
    with two decimals ("189.00" / "189,00"); a price with cents counts only
    with its two decimals;
  - **expected:** every `expect_ids` id is cited;
  - **forbidden:** no `forbid_ids` id is cited;
  - **declines** (only for `must_decline`): the answer cites no id, or
    equals `REFUSAL_TEXT`;
  - **stock:** if a cited product is out of stock, the answer contains "out
    of stock" (case-insensitive);
  - **search** (only with `expect_search`): B9.

  A case passes when all its applicable checks pass.
- **B6.** The scorers read the catalogue they are given; they never load
  files or call a model.

**Running (`src/advisor/evals/`, console script `advisor-eval`)**

- **B7.** `uv run advisor-eval` (the `[project.scripts]` entry
  `advisor-eval`):
  - loads the environment and settings exactly as the `advisor` CLI does
    (`load_env`, `load_settings`; same provider default, key rule and
    `ADVISOR_OLLAMA_URL`);
  - builds one client with `make_client`;
  - runs each case once through `answer_question` with
    `search_tool(load_catalogue())` and a recording tracer (B9);
  - scores the answer.

  Flags:
  - `--cases PATH` (default `evals/cases.jsonl`);
  - `--only ID[,ID…]`;
  - `--report-dir PATH` (default `evals/runs`).
- **B8.** Output and exit codes:
  - one stdout line per case (`PASS`/`FAIL`, case id, the failing checks'
    reasons) and a total line (`N/M passed`, provider, model);
  - exit 0 when all cases pass, 1 when any case fails, 2 for a bad case
    file or bad arguments.
  - A model failure on a case (`ModelError`, including §2's
    unreachable/not-available errors) marks that case `ERROR` with the
    message and counts as a failure. If the very first case fails with
    `ModelUnreachableError` or `ModelNotAvailableError`, the run stops
    there with that message and exit 1. No traceback without `--debug`.
- **B9.** The recording tracer collects each `search_products` call's
  arguments.
  - `expect_search` passes when at least one call satisfies every
    constraint:
    - `category`: equal;
    - `max_price`: the call's `max_price` is set and ≤ the given value;
    - `min_price`: set and ≥;
    - `in_stock_only`: equal;
    - `keywords_any`: at least one of the call's keywords, lower-cased with
      hyphens as spaces (§7's rule), contains one of the given words.
  - Constraint names other than these are a case-file error (B2).
- **B10.** A JSON report is written to
  `<report-dir>/<UTC timestamp>-<provider>.json`. It holds:
  - the provider, the model and the case-file hash;
  - per case: the id, the question, the answer, the search calls, each
    check with pass/fail and reason, and the duration in seconds;
  - the totals.

  `evals/runs/` is gitignored, and nothing else is written.
- **B11.** The suite does not trace to Langfuse: it uses its own recording
  tracer, not `make_tracer`. It imports no provider SDK and not `langfuse`.

**Tests in `verify`**

- **B12.** `npm run verify` covers, with no network and no model:
  - the scorers, against hand-written good and bad answers for each check;
  - the case-file validator, on the committed file and on bad files;
  - the runner, end to end on two or three cases with `ScriptedModelClient`
    (a passing and a failing case, an `ERROR`, the exit codes, the report
    file in a temp dir);
  - the boundary: `advisor.evals` imports neither `langfuse` nor `anthropic`
    nor `httpx` (`tests/test_boundaries.py`).

**Docs**

- **B13.** `README.md` gains "Evaluating answers": the command, the flags,
  what each check means, that a run uses a real model (local by default,
  slow on CPU), and that failures are reported, not gating. `CLAUDE.md`
  names `src/advisor/evals/` (pure scorers vs. the runner's I/O) and the
  command.

## Interpretations

- **"the stated price"** (intent Outcome) is read as: the catalogue price
  appears as a number in the answer. Which product a price sits next to is
  not parsed. Comment site: `score.py` (prices check).
- **"an off-topic case gets the refusal or a decline"** is read as: the
  answer cites no product id, or is the refusal text. Wording is not
  judged, because there is no judge model. Comment site: `score.py`
  (declines).
- **"offline"** is as the intent assumes: no paid API by default, no judge
  model, and no network beyond the configured model server. Comment site:
  the `README.md` section.
- **"a reviewer can run it and read the report"** is read as: the stdout
  summary, with the JSON file as the detail.

## Acceptance criteria

- **AC1** (B1–B3): the committed `evals/cases.jsonl` validates and meets
  the coverage list. Bad files exit 2 naming case and field. *Proof:*
  `tests/test_evals_cases.py`.
- **AC2** (B4–B6, B9): each check passes on a good answer and fails on a
  bad one, including a price with the wrong number, an uncited out-of-stock
  warning, a hyphenated keyword for `keywords_any`, and a `max_price` above
  the limit. *Proof:* `tests/test_evals_score.py`.
- **AC3** (B7, B8, B10): with `ScriptedModelClient`, the runner prints one
  line per case and a total, exits 0/1/2 as specified, marks a `ModelError`
  as `ERROR`, stops on a first-case unreachable error, and writes a JSON
  report with the specified fields. *Proof:* `tests/test_evals_run.py`.
- **AC4** (B11, B12): the boundary test passes, and `verify` is green with
  no model or network. *Proof:* `tests/test_boundaries.py`, `npm run
  verify`.
- **AC5** (B13): the `README.md` and `CLAUDE.md` text. *Proof:* reviewer
  reads.
- **AC6** (live): the owner runs `uv run advisor-eval` once with the local
  model (Ollama, `qwen3:8b`). The run completes, prints a line per case
  and a total, and writes a report under `evals/runs/`. §7's case passes.
  Other failures are findings for later intents, not defects of §8. A
  defect of §8 would be a scorer verdict the owner disagrees with on
  reading the answer. *Proof:* **live check**.

## Non-functional

- **Boundaries:**
  - `src/advisor/evals/score.py` and the case model are pure;
  - `src/advisor/evals/run.py` (or similar) holds the I/O: files, the
    client, the clock, stdout;
  - the console script's entry point is in `src/advisor/evals/`, not in
    `cli.py`;
  - no change to `agent.py`, `catalogue.py`, `guardrails.py`, `prompts/`,
    `tracing.py`, `cli.py` or the data.
- **Data:** synthetic catalogue and invented questions only. Reports stay
  local (gitignored).
- **Model use:**
  - one `answer_question` per case, at most 5 model turns each;
  - local by default: about 15 cases at tens of seconds each is several
    minutes on this machine;
  - Anthropic only when the owner sets the provider, at a cost of cents per
    run.
- **Autonomy:** the suite only reports. No schedule, no gate.

## Out of scope

- LLM-as-judge or semantic scoring.
- Multiple runs per case and pass rates (owner: one run).
- Uploading datasets or scores to Langfuse.
- CI or scheduled runs.
- A cross-model comparison report.
- New guardrail checks.
- Fixing the answers the suite finds wrong.
- Matching products by name.

## Assumptions I made

- **Ids only** (B4), because the prompt mandates the `(P-001)` form. An
  answer that names a product without its id is uncited, and so fails
  `expected`. That also measures the prompt rule.
- **Off-topic** means no id cited, or the refusal text (Interpretations).
- **The price check is presence, not placement** (Interpretations).
- **Cases in `evals/` at the root,** not inside the package. They are data
  for this repository, not shipped code. The runner reads them by path.
- **No Langfuse tracing during evals** (B11). Mixing eval traffic into the
  owner's traces is out of scope. A later intent could add it.
- **First-case abort only for "server unreachable" or "model missing"**
  (B8), so a dead Ollama doesn't produce 15 identical errors.
- **The case count** is 12 to 20; the plan writes the cases.
- **Live check:** none by rule 1 (no `cli.py`, `models/`, `tracing.py`,
  `prompts/` or `infra/` change), but rule 3 applies: a real-model run is
  the point (AC6).
