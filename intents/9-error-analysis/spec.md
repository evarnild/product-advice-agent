<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §9 spec — Error analysis on top of the eval suite: synthetic questions by dimension, a trace viewer and pass/fail labels with critiques

Accepted intent: [intent.md](intent.md)

Written against `main` at `03a77b7` (§8 merged in 31bd1b7).

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/9-error-analysis/intent.md` | The first loop of the field guide, end to end: questions by dimension, runs that keep everything, a viewer with binary labels and critiques, failure modes counted. Constraints: extend §8, don't fork it; leave `prompts/`, `guardrails.py`, `cli.py`, `tracing.py` and the catalogue alone; local model by default; the owner labels every conversation, no model grades; viewer local only. Owner on 2026-11-11: "go with a custom viewer". |
| Owner, spec questions (2026-11-11) | Viewer: **FastHTML**. Generation: **local model, about 60 questions**. Committed: **questions, taxonomy, labels and critiques** (runs stay local). Taxonomy: **the model drafts, the owner edits**. |
| Hamel Husain, "A Field Guide to Rapidly Improving AI Products" | "Generate user inputs, not outputs"; "Verify scenario coverage"; "One-click correct/incorrect buttons beat lengthy forms."; "Favor Binary Decisions Over Arbitrary Scales". |
| `intents/8-offline-evals/spec.md` | The case format (B1–B4), the checks (B5, amended), the runner and report (B7–B10). §8's checks and their meaning are unchanged here. |
| `src/advisor/evals/cases.py` | `_FIELDS = ("id", "question", "expect_ids", "forbid_ids", "must_decline", "expect_search", "note")`; an unknown field is an error ("is not a known field"). |
| `src/advisor/evals/run.py` | `RecordingTracer` keeps only `search_products` arguments; `_record` writes `id, question, status, answer, error, searches, checks, duration_s`; the report has `provider, model, cases_sha256, started, cases, totals`. |
| `src/advisor/tracer.py` | `Tracer`: `begin`, `check(stage, allowed, reason)`, `generation(model, usage, text, tool_names)`, `tool(name, arguments, result_count, error)`, `finish`, `fail`. Tool *results* are not in the protocol. |
| `src/advisor/agent.py` | `Tool(spec, run)`; `answer_question(question, client, tools, tracer)`; `search_tool(catalogue)`. |
| `src/advisor/models/base.py` | `ModelClient.complete(system, messages, tools) -> ModelTurn`. |
| `src/advisor/data/catalogue.json` | 8 categories: camera, headphones, laptop, monitor, phone, smartwatch, speaker, tablet. Out of stock: P-004, P-010, P-017, P-024, P-032. |
| `CLAUDE.md` → "Conventions" | Provider/tracing libraries in one module each, enforced by `tests/test_boundaries.py`; tests drive a fake `ModelClient`; sockets blocked in tests. |
| python-fasthtml on PyPI (0.14.22 at writing) | Requires starlette, uvicorn, fastcore, python-multipart, beautifulsoup4 and others; Python ≥ 3.10. |

## Behaviour

### Questions by dimension

- **B1. Dimensions on a case.** §8's case format gains one optional field,
  `dimensions`: an object with the string keys `feature`, `scenario` and
  `persona`, all three required when the field is present.
  - `feature` is a catalogue category or `off-topic`.
  - `scenario` is one of `exact-match`, `several-matches`, `no-match`,
    `budget-too-low`, `out-of-stock`, `off-topic`, `spelling-differs`.
  - `persona` is a non-empty string.
  - Any other key, or a value outside those lists, is a case-file error
    naming the line, the case and the field, as §8's errors do. Cases
    without `dimensions` (all of §8's) parse exactly as before.
- **B2. The generator.** `uv run advisor-analysis generate` writes candidate
  questions to a new case file (default `evals/generated.jsonl`; it
  refuses to overwrite an existing file unless `--force`).
  - **The grid:** features × scenarios × personas, where personas are a
    fixed list of four: a student on a tight budget, a non-technical buyer,
    an enthusiast who knows the specs, someone buying a gift. Only
    meaningful cells are used (the `off-topic` scenario pairs only with the
    `off-topic` feature, and back).
  - **Sampling:** `--count` (default 60) questions from cells drawn by a
    seeded shuffle (`--seed`, default 9), two questions per cell, so a run
    with the same seed asks for the same cells.
  - **One model call per cell** through `make_client` and
    `ModelClient.complete` with no tools, using a generation prompt stored
    under `src/advisor/evals/prompts/`. The prompt gives the cell, the
    catalogue's categories and price range per category, and the
    out-of-stock products (id and name), and asks for questions only (no
    answers), each with a structured *probe*: the `search_products`
    arguments that express it (category, min/max price, keywords), plus,
    for `out-of-stock`, the product id it is about.
  - Provider and model come from the environment as in §8 (`ollama`,
    `qwen3:8b` by default); `--provider` / `--model` follow §11 once it is
    merged, and are not part of §9.
- **B3. Coverage check.** Each candidate is verified against the catalogue
  with `search_products`, by its probe, before it is written:
  - `exact-match`: the probe returns at least 1 product;
  - `several-matches`: at least 2;
  - `no-match` and `budget-too-low`: 0 (and for `budget-too-low`, the same
    probe without `max_price` returns at least 1);
  - `out-of-stock`: the named product exists and is out of stock;
  - `off-topic`: no probe needed;
  - `spelling-differs`: at least 1, and the question contains none of the
    probe's keywords verbatim (case-insensitive).
  A candidate that fails its check, or whose model output cannot be
  parsed, is dropped. The command prints, per scenario, how many were
  asked for, kept and dropped (with the reason), and exits 0 when at
  least one question was kept, 1 when none were, 2 for bad arguments.
- **B4. Generated cases.** Each kept question is written in §8's format with
  `id` (`gen-<scenario>-<n>`, unique), `question`, `dimensions`, and a
  `note` holding the probe. `off-topic` cases get `must_decline: true`;
  `no-match` and `budget-too-low` cases get none of `expect_ids` /
  `forbid_ids`; `out-of-stock` cases get nothing that would force citing
  the product. The file parses with §8's `parse_cases` (with B1). The owner
  reads and edits it before committing it.

### Runs that keep everything

- **B5. Full context in the report.** `advisor-eval` (§8's runner) records,
  per case, in addition to §8's fields:
  - `dimensions` (when the case has them);
  - `turns`: per model turn, the text and the names of the tools called;
  - `tools`: per tool call, the name, the arguments, the **results** (the
    products returned, as the model saw them) and whether it was an error;
  - `guardrails`: the input and output checks (stage, allowed, reason).
  The report gains `prompt_sha256` (the SHA-256 of
  `src/advisor/prompts/system.md` as loaded). §8's existing fields, the
  checks and the exit codes are unchanged.
- **B6. How it is recorded.** Turns and guardrails come from a recording
  `Tracer` (an extension of §8's `RecordingTracer`); tool results come from
  wrapping each `Tool.run` in the runner. The `Tracer` protocol, `agent.py`
  and `tracing.py` are not changed.
- **B7. Repeats.** One answer per question per run, as in §8.

### The viewer

- **B8. Starting it.** `uv run advisor-analysis view <report.json>` serves a
  FastHTML app on `127.0.0.1` only, port `--port` (default 5209), and
  prints its URL. A missing or unreadable report exits 2 with a one-line
  message.
- **B9. One conversation per screen**, all context visible without
  scrolling sideways: the question and its dimensions; §8's status and each
  check with its reason; each model turn in order with its tool calls, the
  arguments and the returned products (id, name, price, stock); the answer;
  the guardrail verdicts; the current label and critique. A header shows
  the position (`12 / 60`), and the counts labelled, passed and failed.
- **B10. Labelling.** `p` labels the conversation **pass**; `f` labels it
  **fail** and focuses the critique box. A critique is required for a fail
  and optional for a pass. `Enter` in the critique box saves it and moves
  to the next conversation; `j` / `k` (and buttons) move next / previous.
  Every label or critique change is saved at once (B11): closing the
  browser loses nothing that was shown as saved.
- **B11. Label storage.** Labels go to `evals/labels/<report-stem>.jsonl`,
  one JSON line per change: `case_id`, `label` (`pass` / `fail`),
  `critique`, `labelled_at` (UTC), plus `question` and `answer` copied from
  the report so each line stands alone as a future few-shot example. The
  last line per `case_id` is the current label. The viewer reloads them on
  start, so labelling resumes where it stopped. These files are committed
  (owner's decision).
- **B12. Filters.** By each dimension's value, by label (unlabelled, pass,
  fail) and by §8 status (PASS, FAIL, ERROR), combined with AND. Next and
  previous move within the filtered list.

### Failure modes

- **B13. Drafting the taxonomy.** `uv run advisor-analysis taxonomy
  <labels.jsonl>` sends the failed conversations' critiques (with the
  question and answer) to the model in one call, through `make_client`,
  with a prompt under `src/advisor/evals/prompts/`, and writes
  `evals/taxonomy.draft.json`: a list of modes (`id`, `name`,
  `description`) and a proposed mapping of each failed `case_id` to one or
  more mode ids. Model output that does not validate (B14) is reported and
  nothing is written (exit 1).
- **B14. The accepted taxonomy.** The owner edits the draft and saves it as
  `evals/taxonomy.json` (committed). It is valid when: mode ids are unique
  and non-empty; every mapped mode id exists; every mapped case is a fail
  in the labels it names; every failed case is mapped to at least one mode.
  The file names the labels file it maps (`labels`), so `counts` can check
  it.
- **B15. Counts.** `uv run advisor-analysis counts <report.json>` reads the
  report, its labels file and `evals/taxonomy.json`, validates them (B14;
  any error is printed and exits 2), and prints Markdown tables:
  1. per mode: the number of failed conversations, sorted descending;
  2. per mode × each dimension (feature, scenario, persona);
  3. **agreement** between §8's status and the owner's label: both pass,
     both fail, owner fail but §8 PASS (*a check misses it*), owner pass
     but §8 FAIL (*a check is too strict*), with the case ids in the two
     disagreement cells; ERROR cases and unlabelled ones are counted
     apart.
  `--out <file>` also writes the tables to a file. Disagreements are
  reported only; nothing opens an intent or changes a check.

## Interpretations

- **"adds them to §8's question set"** (intent, Outcome) is read as: the
  same format and runner, in a separate file (`evals/generated.jsonl`), run
  with `advisor-eval --cases evals/generated.jsonl`. §8's 15 hand-written
  cases stay as they are, so §8's suite keeps its meaning.
- **"Verify scenario coverage"** is read as: a deterministic check of each
  candidate's probe against the real catalogue (B3), not a model judgement.
- **"every model turn"** (intent) is read as what the `Tracer` sees: each
  turn's text and tool names (B5); token usage is left out.
- **"the prompt version"** is read as the hash of the shipped system prompt
  (B5); the prompt has no version number.
- **"in one keystroke plus typing"** is read as `p` / `f` plus the critique
  box (B10).
- **Ports:** the intent's "the worktree's port (5200 + id mod 100)" is read
  as the default 5209 for §9, overridable with `--port`, since the viewer
  is also run from the main checkout.

## Acceptance criteria

- **AC1** (B1): `dimensions` validates as specified; §8's case file still
  parses unchanged. *Proof:* `tests/test_evals_cases.py`.
- **AC2** (B2, B4): with a scripted fake client, `generate` asks for the
  seeded cells, writes §8-format cases with dimensions, unique ids and the
  probe in `note`, refuses to overwrite without `--force`, and prints the
  per-scenario summary. *Proof:* new `tests/test_analysis_generate.py`.
- **AC3** (B3): each scenario's coverage rule keeps a valid candidate and
  drops an invalid one, against the real catalogue. *Proof:* new
  `tests/test_analysis_coverage.py`.
- **AC4** (B5, B6): a run with the fake client writes `turns`, `tools` with
  results, `guardrails`, `dimensions` and `prompt_sha256`; §8's fields,
  checks and exit codes are unchanged (§8's tests stay green unedited).
  *Proof:* `tests/test_evals_run.py`.
- **AC5** (B8–B12): the viewer, through Starlette's test client (no
  socket): renders one conversation with all B9 parts; `p`/`f`/critique
  requests save B11 lines; a fail without a critique is refused; labels
  reload; filters and next/previous respect each other; it binds to
  127.0.0.1. *Proof:* new `tests/test_analysis_view.py`.
- **AC6** (B13, B14): the taxonomy draft is written from a scripted model
  answer and refused when it doesn't validate; each B14 rule has a failing
  example. *Proof:* new `tests/test_analysis_taxonomy.py`.
- **AC7** (B15): counts, the per-dimension tables and the agreement table
  from a fixed report, labels file and taxonomy, including the
  disagreement case ids. *Proof:* new `tests/test_analysis_counts.py`.
- **AC8** (non-functional): `fasthtml`, `starlette` and `uvicorn` are
  imported only in the viewer module; the pure modules load none of them;
  no test opens a socket. *Proof:* `tests/test_boundaries.py`.
- **AC9** (live): the owner runs the loop once with the local model:
  `generate` (about 60 questions, reads and edits them), `advisor-eval
  --cases evals/generated.jsonl`, labels at least 20 conversations in the
  viewer with critiques, `taxonomy`, edits and saves it, `counts`. The
  viewer feels fast enough to label one conversation in a few seconds, and
  the counts table matches what they labelled. *Proof:* **live check**.

## Non-functional

- **Boundaries:** pure modules (no I/O, no model, no web framework):
  dimensions validation (`cases.py`), the coverage check, label-file
  parsing, taxonomy validation and the counts. I/O and wiring: the
  `advisor-analysis` command (generate, taxonomy, counts), the runner's
  recording, and the viewer module, the only one that imports FastHTML.
  All under `src/advisor/evals/`. Nothing in `prompts/`, `guardrails.py`,
  `cli.py`, `tracing.py`, `agent.py` or the catalogue changes.
- **Data:** synthetic catalogue and generated questions only. Committed:
  `evals/generated.jsonl`, `evals/labels/*.jsonl` (labels, critiques and
  the copied question and answer), `evals/taxonomy.json`. Not committed:
  `evals/runs/` (already gitignored) and `evals/taxonomy.draft.json`.
- **Model use:** `generate` (one call per cell, about 30) and `taxonomy`
  (one call) through `make_client`; the local model by default, so no cost.
  Anthropic only when the owner selects it. A model that is down gives §8's
  "cannot reach" message and exit 1. Tests use the scripted fake; no
  socket is opened.
- **Autonomy:** the tools propose; the owner reviews the generated
  questions, labels every conversation and accepts the taxonomy. No model
  labels or grades an answer. Nothing runs on a schedule.
- **Dependency:** `python-fasthtml` (owner's choice), pinned in `uv.lock`,
  with its own line in `plan.md`.

## Out of scope

- New code checks for the failure modes found; an LLM-as-judge; prompt or
  guardrail fixes; a model comparison (each a later intent, per the intent).
- Several answers per question (B7).
- Langfuse datasets, scores or annotation queues (§10, which will write the
  B11 label format).
- `--provider` / `--model` flags on these commands (§11 for `advisor-eval`;
  `advisor-analysis` reads the environment).
- Editing the taxonomy in the viewer; deployment, authentication, remote
  access.

## Assumptions I made

- **One command with subcommands**, `advisor-analysis generate | view |
  taxonomy | counts`, a new script in `pyproject.toml`, rather than four
  scripts.
- **Personas** are a fixed list of four (B2); the owner can edit the list in
  code later.
- **Probe in `note`:** the generated case keeps its probe as text in §8's
  `note`, so §8's format needs only the one new field (B1).
- **Recording without changing the protocol** (B6): wrapping `Tool.run` gets
  the results the model saw, and leaves `Tracer`, `agent.py` and
  `tracing.py` untouched, as the intent requires.
- **Disagreement is reported only** (B15), per the intent's open question 7;
  acting on it is the owner's.
- **One taxonomy file** for the first loop, naming the labels file it maps
  (B14); several runs' taxonomies are a follow-up.
- **A fail needs a critique, a pass doesn't** (B10): the critique is what
  the taxonomy is built from.
- **Default port 5209**, not 5200 + id mod 100 from the worktree, because
  the viewer is used from the main checkout after the merge.
- **Tier:** the path table decides (`review_tier` empty). A new dependency
  and a web server bound to localhost may lead the review to raise it.
