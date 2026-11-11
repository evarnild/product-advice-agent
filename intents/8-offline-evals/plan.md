<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §8 plan — An offline eval suite that scores the advisor's answers against a fixed question set

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`uv run advisor-eval` runs 15 fixed catalogue questions through the advisor
once each, with the provider the environment selects (local Ollama by
default).
- It scores each answer with pure, deterministic checks against the
  catalogue: grounding, prices, expected and forbidden ids, declines, stock
  warnings, and optional search-argument checks.
- It prints a line per case and a total, and writes a JSON report to the
  gitignored `evals/runs/`.
- It exits 0, 1 or 2.
- `verify` covers the scorers, the case file and the runner (with the
  scripted fake), and nothing in the suite needs a network.

## Risks

- **Tests that pass whatever the code does** (§1's recurring class). Each
  scorer gets a good answer and a bad one that differ only in what that
  check looks at: a price off by one digit, a missing "out of stock", a
  hyphenated keyword. The runner tests use a scripted fake whose answers
  are known to pass or fail particular checks.
- **The id regex.** `P-\d{3}` must not match inside a longer token
  (`P-0011`, `XP-001`). The test includes both, and boundaries are anchored.
- **Price formats.** Models write "€189", "189 €", "189.00 euros" or
  "189,00 €". A whole price must match in each form, but not as part of a
  longer number ("1189", "189.5"). The test covers each form.
- **Pytest's log handlers and stdout capture.** The runner takes an output
  stream argument, so tests capture it directly, not through `capsys` and
  global state.
- **The clock and file names.** The report file name uses a timestamp. The
  runner takes a `now` function, so the test can predict the name.
- **The boundary.** `advisor.evals` must not pull `langfuse` in (§3's
  subprocess test style), so the runner builds its own recording tracer
  and never imports `advisor.tracing`.
- **`pyproject.toml` and `uv.lock`.** A new `[project.scripts]` entry is
  build config. `uv lock --check` must still pass. If the lock changes,
  commit it, and the reviewer checks that no dependency moved.
- **Overlap:** none in flight. §8 is the only open intent.
- **Stale line citations:** read at `03dde68`.

## Verified against the codebase

Re-read on `main` at `03dde68`.

- `src/advisor/agent.py:22` — `MAX_TURNS = 5`; `:91` `search_tool(catalogue)`; `:151-169` `run_agent`; `:172-200` `answer_question(question, client, tools, tracer)`. It calls `tracer.begin`, `check`, `generation`, `tool`, `finish` and `fail`, and re-raises on failure.
- `src/advisor/tracer.py` — `Tracer` protocol: `begin`, `check`, `generation`, `tool(name, arguments, result_count, error)`, `finish`, `fail`; `NoopTracer`.
- `src/advisor/guardrails.py:14` — `REFUSAL_TEXT`.
- `src/advisor/models/__init__.py:17` — `make_client(provider, model, *, api_key=None, base_url=None)`; `KNOWN_PROVIDERS`.
- `src/advisor/models/base.py` — `ModelError`, `ModelUnreachableError`, `ModelNotAvailableError`.
- `src/advisor/config.py:54,65` — `load_env`, `load_settings`; `Settings.api_key_variable` (`:39`), `ollama_url()` (`:42`), `api_key()` (`:49`); `ConfigError`.
- `src/advisor/cli.py` — the reference for how `advisor` builds the client (key check, `base_url` for ollama). Not edited; `advisor-eval` mirrors its steps.
- `src/advisor/catalogue.py` — `load_catalogue()`, `Product(id, name, brand, category, price_eur, in_stock, …)`, `CATEGORIES`. §7's hyphen rule is in `_norm`.
- `src/advisor/data/catalogue.json` — 32 products. Out of stock: P-004, P-010, P-017, P-024, P-032. Prices are whole euros.
- `pyproject.toml` `[project.scripts]` — `advisor = "advisor.cli:main"`.
- `.gitignore` — no `evals/` entry yet.
- `tests/test_boundaries.py` — the AST importer scan, and §3's subprocess test (the pure modules load no tracing SDK).

## Subtasks

1. **The case model and file** (`src/advisor/evals/cases.py`, `evals/cases.jsonl`).
   - Add `Case` (a frozen dataclass), `CaseFileError(ValueError)` naming
     the line, case id and field, and `load_cases(path, catalogue) ->
     list[Case]`, which validates per B1–B2.
   - Write the 15 cases below.
   - Tests in `tests/test_evals_cases.py`:
     - the committed file loads and covers every category, an off-topic
       pair, P-004 and §7's case;
     - each kind of bad file gives an error naming its case and field:
       unknown field, unknown id, a decline case with expected ids, an
       unknown search constraint, a duplicate id, bad JSON.
2. **The scorers** (`src/advisor/evals/score.py`, pure).
   - Add `cited_ids(answer)`, `price_mentioned(answer, price)`,
     `Check(name, ok, reason)`, and `score(case, answer, searches,
     catalogue) -> list[Check]`. The last runs the B5 checks that apply to
     the case, plus B9's search matching (keywords normalised with
     `advisor.catalogue._norm`).
   - Tests in `tests/test_evals_score.py`: per check, a passing answer and
     a failing one, plus the regex and price edge cases from Risks.
3. **The runner** (`src/advisor/evals/run.py`).
   - Add `main(argv=None, *, env=None, client_factory=make_client,
     out=sys.stdout, now=<UTC clock>) -> int`, with the flags `--cases`,
     `--only`, `--report-dir` and `--debug`.
   - It builds the client exactly as `cli.py` does. On a `ConfigError` or a
     missing key, it prints the same messages and exits 2.
   - A `RecordingTracer` (implementing `Tracer`) keeps each tool call's
     name and arguments.
   - For each case, it calls `answer_question` with
     `search_tool(load_catalogue())`, then `score`, and prints `PASS`,
     `FAIL` or `ERROR`. `ModelError` on a case gives `ERROR`; on the first
     case, `ModelUnreachableError` or `ModelNotAvailableError` aborts with
     exit 1. A traceback is shown only with `--debug`.
   - It writes the B10 JSON report, with a `sha256` of the case file, to
     `<report-dir>/<YYYYMMDDTHHMMSSZ>-<provider>.json`, and prints the
     total.
   - Add `[project.scripts] advisor-eval = "advisor.evals.run:main"`, then
     `uv lock` if needed.
   - Tests in `tests/test_evals_run.py`, using `ScriptedModelClient` and a
     temp dir, covering:
     - all pass → 0;
     - one fail → 1;
     - a `ModelError` → `ERROR`, 1;
     - a first-case `ModelUnreachableError` → abort, 1, the message, and
       later cases not run;
     - a bad case file → 2;
     - `--only` runs only the named cases;
     - the report file's name and fields;
     - an `expect_search` case read through the recording tracer.
4. **Boundary.** In `tests/test_boundaries.py`, add a subprocess test:
   importing `advisor.evals.run` loads none of `langfuse`, `opentelemetry`,
   `anthropic` or `httpx`. The adapters are imported lazily by
   `make_client`, so building no client means importing none.
5. **Ignore and docs.**
   - `.gitignore`: `evals/runs/`.
   - `README.md`: an "Evaluating answers" section (B13).
   - `CLAUDE.md` → "Architecture": `src/advisor/evals/`, with the pure
     `cases.py` and `score.py` and the I/O in `run.py`. Under "Commands":
     `uv run advisor-eval`.
6. **Status.** Set `status: in-review` and append to `## Progress`.

### The 15 cases (`evals/cases.jsonl`)

| id | question | expect_ids | forbid_ids | other |
| --- | --- | --- | --- | --- |
| nc-headphones-under-200 | I need noise-cancelling headphones under 200 euros | P-005, P-001 | P-003 | expect_search: category headphones, max_price 200, keywords_any ["noise"]; note: §7's case. P-004 (out of stock) may be cited if flagged (stock check) |
| sport-earbuds | Cheap wireless earbuds for running? | P-002 | | expect_search: category headphones |
| student-laptop | A laptop for a student, under 700 euros | P-009 | P-008 | expect_search: category laptop, max_price 700 |
| video-editing-laptop | Which laptop is best for video editing? | P-008 | | expect_search: category laptop |
| no-laptop-under-200 | Do you have a laptop under 200 euros? | | | expect_search: category laptop, max_price 200; note: an honest "nothing matches" (no laptop is under 200 €; P-012 at 329 € may be suggested, grounded and priced) |
| basic-phone | A simple phone for calls and maps, under 200 euros | P-016 | P-014 | expect_search: category phone, max_price 200 |
| gaming-monitor | I want a monitor for gaming | P-019 | | expect_search: category monitor |
| drawing-tablet | A tablet for drawing, budget 500 euros | P-022 | P-024 | expect_search: category tablet, max_price 500 |
| gps-watch | A smartwatch with GPS under 250 euros | P-025 | P-026 | expect_search: category smartwatch, max_price 250 |
| waterproof-camera | A camera I can take swimming | P-029 | | expect_search: category camera |
| tv-sound | Something to improve the sound of my TV | P-031 | | expect_search: category speaker |
| out-of-stock-quiet-pro | Is the Sonavo Quiet Pro available? | P-004 | | stock check applies: must say "out of stock" |
| voice-speaker | A smart speaker with a voice assistant | P-032 | | stock check applies (P-032 is out of stock) |
| off-topic-weather | What's the weather in Paris tomorrow? | | | must_decline |
| off-topic-poem | Write me a poem about cats. | | | must_decline |

This covers all 8 categories, budget filters, a nothing-matches case, two
out-of-stock products, two off-topic questions and §7's case.

## Tests

| Spec | Test | Fails if |
| --- | --- | --- |
| B1–B3, AC1 | `test_evals_cases.py`: the committed file loads and covers; six bad files give errors naming case and field | validation loosened; a field ignored |
| B4 | `test_evals_score.py`: `cited_ids` finds `P-001` in "Acme (P-001)" and "P-001,", and not in `P-0011` or `XP-001` | regex unanchored |
| B5 grounded | a cited `P-099` fails; real ids pass | check skipped |
| B5 prices | "€189", "189 €", "189.00", "189,00" pass for 189.0; "1189", "18.9", "190" fail | presence check loosened or tightened |
| B5 expected / forbidden | missing expected id fails; forbidden id present fails | inverted |
| B5 declines | no id → pass; the refusal text → pass; any cited id → fail | check skipped |
| B5 stock | P-004 cited without "out of stock" fails; with it, passes; in-stock cited without the phrase passes | case-sensitivity, wrong product |
| B9 search | `max_price` 250 vs limit 200 fails, 180 passes, unset fails; category mismatch fails; `keywords_any ["noise"]` matches `["noise-cancelling"]` | normalisation removed; comparison flipped |
| B7, B8, AC3 | `test_evals_run.py`: exit 0/1/2; `ERROR`; first-case abort; `--only` | exit-code or flow mutants |
| B10 | the report file name from the injected clock, and its fields | file not written; fields missing |
| B11, B12 | `test_boundaries.py`: subprocess import of `advisor.evals.run` loads no SDK | an eager import added |

The implementer runs these mutants once each and records the killing test:
- the price regex accepting any digits;
- `cited_ids` without boundaries;
- the stock check dropped;
- `max_price` compared with `>=`;
- the exit code always 0;
- `ERROR` counted as a pass.

It backs up and restores by copy, and finishes with `git status --short`
clean.

## Validation

- `npm run verify` green, with no model or network.
- `npm run check:intent` PASS (feature).
- `uv lock --check` passes.
- Live check (spec AC6, rule 3), run by the owner:
  1. Ollama running with `qwen3:8b`, and the main checkout's `.env` without
     `ADVISOR_MODEL_PROVIDER`/`ADVISOR_MODEL`. Run `uv run advisor-eval`.
  2. You should see one line per case and a total, a report file under
     `evals/runs/`, and `nc-headphones-under-200` passing.
  3. Open the report and read two or three answers. Do the scorer's
     verdicts match your own reading?

## Assumptions I made

- **15 cases** (the spec allows 12–20); the case table is the plan's
  choice.
- **`advisor-eval` mirrors `cli.py`'s client building** rather than sharing
  a helper. Refactoring `cli.py` would touch a Reviewed path. A little
  duplication is the price; a later refactor could share it.
- **`_norm` is imported from `advisor.catalogue`** for `keywords_any`,
  to reuse §7's rule. It is a private name; a test pins the behaviour.
- **The report's timestamp is the run's start, in UTC.**
- **No `--provider` flag:** the environment selects the provider, as for
  `advisor`. `$env:ADVISOR_MODEL_PROVIDER = "anthropic"` switches one run.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-11: build (subtasks 1-6)

Commits: `9ab314f` (cases file, validator, scorers and their tests),
`aa4060b` (runner, `advisor-eval` entry, boundary test, `.gitignore`,
README, CLAUDE.md), plus the status commit.

Shipped: `src/advisor/evals/{cases,score,run}.py`, `evals/cases.jsonl` (15
cases as in the plan table), `tests/test_evals_{cases,score,run}.py`, the
subprocess boundary test, `[project.scripts] advisor-eval`. Tests: 241 pass
in `npm run verify` (was 187; +54: cases 14, score 27, run 13, boundary 1
minus none). `uv lock --check` passes with no lock change (a script entry
adds no dependency).

Mutants (each run once against the full suite, restored by copy, `git status
--short` clean afterwards), all killed:
- price regex accepting any digits: `test_price_mentioned_*` (accepts/rejects/cents), `test_a_failing_case_exits_1_and_names_the_reason`;
- `cited_ids` without boundaries: `test_cited_ids_ignores_longer_or_malformed_tokens` (`P-0011`, `XP-001`, `AP-123x`);
- stock check dropped: `test_stock`;
- `max_price` compared with `>=`: `test_search_max_price_category_and_keywords` and three runner tests;
- exit code always 0: `test_a_failing_case_exits_1_and_names_the_reason` and three more;
- `ERROR` counted as a pass: `test_a_model_error_marks_error_counts_as_failure_and_run_continues`, `test_later_unreachable_is_an_error_not_an_abort`.

Divergences and choices:
- Tests were written right after each module, in the same commit, not
  strictly before it; the mutant run is the check that they bite.
- `main` also takes an `err` stream (errors and the abort message go to it,
  per-case lines and the total to `out`). Config errors (missing key,
  unknown provider, bad Ollama URL) exit 2 as the plan says, where `cli.py`
  uses 1. A catalogue load error also exits 2.
- Any non-`ModelError` exception on a case is recorded as `ERROR unexpected
  <Type>` and the run goes on (tracebacks with `--debug`).
- A first-case unreachable/not-available abort writes no report.
- `keywords_any` reads the call's `keywords` argument (the tool's name for
  it). `in_stock_only` absent in a call counts as false.
- `scripts/intent-check-lib.mjs` `CORE_CODE` was not touched (outside the
  plan's file list); `evals/` pure modules are not listed there.
