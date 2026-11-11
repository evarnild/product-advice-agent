<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §9 plan — Error analysis on top of the eval suite: synthetic questions by dimension, a trace viewer and pass/fail labels with critiques

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

The field guide's first loop runs on top of §8, from questions to counted
failure modes:
- `uv run advisor-analysis generate` writes about 60 synthetic questions,
  tagged by feature, scenario and persona and checked against the
  catalogue, in §8's case format;
- `advisor-eval` keeps each conversation's full context in its report;
- `uv run advisor-analysis view <report>` is a local FastHTML viewer for
  binary labels with critiques, saved as committed JSON lines;
- `taxonomy` drafts failure modes from the critiques, and `counts` tables
  them by mode, by dimension, and against §8's checks.

`verify` covers all of it with the scripted fake and no socket.

## Risks

- **Tests that pass whatever the code does** (§1's and §8's recurring
  class; round 4 of §8 sharpened it to "a substring or regex match tested
  only with inputs that contain it, so loosening it survives"). Every rule
  gets a passing and a failing input that differ only in what the rule
  looks at:
  - each coverage rule (B3), at its threshold (0, 1 and 2 results);
  - each taxonomy rule (B14);
  - each dimension value (B1);
  - the "fail needs a critique" rule (B10).
- **The new dependency.** `python-fasthtml` brings Starlette, uvicorn,
  websockets, python-multipart, beautifulsoup4, fastcore and a package
  named `httpx2`.
  - Check `uv lock` afterwards: if it moves `httpx`, `anthropic` or
    `langfuse`, stop and report rather than accept it.
  - Pin it exactly (§4/§6's style: a known version, not a range).
  - `uv lock --check` must pass.
- **Boundaries.**
  - `advisor.evals.run` must still load no SDK (`tests/test_boundaries.py:64`
    `test_eval_runner_loads_no_sdk`), so the runner never imports the
    viewer. FastHTML is imported in `evals/view.py` only.
  - The static httpx rule (`:48`) scans `src/` imports only, so it is
    unaffected unless our code imports httpx. Starlette's `TestClient`
    uses httpx in tests, which is fine.
  - A new boundary test: only `evals/view.py` imports `fasthtml`,
    `starlette` or `uvicorn`, and the pure modules load none of them.
- **Sockets.** `tests/conftest.py` fails any socket connect.
  - The viewer is tested through Starlette's `TestClient` (in-process, no
    socket).
  - `uvicorn.run` is called only from the `view` subcommand, behind a
    function the test replaces, so the bind address (`127.0.0.1`) and port
    are asserted without serving.
- **§8 must not change meaning.** §8's tests stay green unedited (AC4). The
  new report fields are additions, and `_record`'s existing keys keep their
  names and values.
- **Recording tool results without touching `agent.py`** (B6). Wrap
  `Tool.run` in the runner; the wrapper returns exactly what it got, so
  the agent sees no difference. Test that a wrapped tool's results equal
  the unwrapped one's.
- **Model output parsing** (generation, taxonomy). `qwen3:8b` may wrap JSON
  in prose or `<think>` blocks.
  - Parse leniently: take the first JSON value found.
  - Drop what doesn't validate, and count it.
  - Test with a scripted answer that has prose around the JSON.
- **Determinism.** Cell sampling uses `random.Random(seed)`, never the
  global RNG. `labelled_at` and file names come from an injected clock, as
  in §8.
- **Package data.** The generation and taxonomy prompts live in
  `src/advisor/evals/prompts/*.md`. Hatch packages `src/advisor` whole
  (`pyproject.toml:29-30`), so they ship. Load them by path relative to
  the module, as `agent.load_system_prompt` does.
- **Windows.** File writes are UTF-8 with `\n`; label lines are appended
  with flush per write; paths in printed messages use the OS form (§8's
  live check showed `evals\runs\…`).
- **Stale line citations:** read at `2fa3e69`.
- **Overlap:**
  - §10 (accepted, not started) will write B11's label format, so keep it
    documented in the README.
  - §11 (accepted, not started) touches `run.py`'s argument parser, the
    same file as subtask 3. Whichever merges second rebases.

## Verified against the codebase

Re-read on `main` at `2fa3e69`.

- `src/advisor/evals/cases.py:14` — `_FIELDS = ("id", "question", "expect_ids", "forbid_ids", "must_decline", "expect_search", "note")`; `:22` `Case` (frozen dataclass); `:72` `parse_cases(text, catalogue)`; `:91` unknown fields rejected ("is not a known field"); errors are `CaseFileError` via `fail(fld, why)` naming the line and case.
- `src/advisor/evals/run.py:39-62` — `RecordingTracer` (keeps `search_products` arguments only); `:69` `_parser()`; `:84` `main(argv, *, env, client_factory, out, err, now)`; `:126` `load_settings(load_env(env))`; `:146` `client_factory(...)`; `:149` `tool = search_tool(catalogue)`; `:153-158` per case `RecordingTracer()` and `answer_question(case.question, client, [tool], tracer)`; `:185-196` the report dict; `:209` `_record(...)` and its keys.
- `src/advisor/evals/score.py:87` — `score(case, answer, searches, catalogue)`; `:54` `says_out_of_stock`.
- `src/advisor/agent.py:34` — `Tool(spec, run)` frozen dataclass; `:47` `load_system_prompt()` reads `SYSTEM_PROMPT_PATH`; `:78` `_product_json(p)` (what the model sees); `:91` `search_tool(catalogue)`; `:172` `answer_question(question, client, tools, tracer)`.
- `src/advisor/tracer.py` — `Tracer` protocol (`begin`, `check`, `generation(model, usage, text, tool_names)`, `tool(name, arguments, result_count, error)`, `finish`, `fail`).
- `src/advisor/models/base.py:83` — `ModelClient.complete(system, messages, tools) -> ModelTurn`; `Message(role, text, …)`; `ModelError`, `ModelUnreachableError`, `ModelNotAvailableError`.
- `src/advisor/models/fake.py` — the scripted fake used by the tests.
- `src/advisor/catalogue.py:15` — `CATEGORIES`; `:95` `load_catalogue()`; `:113` `search_products(...)`; `Product(id, name, brand, category, price_eur, in_stock, …)`.
- `pyproject.toml:13-15` — `[project.scripts]` (`advisor`, `advisor-eval`); `:29-30` hatch packages `src/advisor`.
- `tests/test_boundaries.py:26-71` — the import rules and the subprocess check `test_eval_runner_loads_no_sdk`.
- `tests/conftest.py` — sockets blocked.
- `.gitignore:24` — `evals/runs/`.
- `scripts/intent-check-lib.mjs:154-159` — `CORE_CODE` includes `src/advisor/evals/(cases|score).py`; this plan doesn't change it (see Assumptions).

## Subtasks

Each subtask is committed with `npm run verify` green.

1. **Dimensions (B1).** In `cases.py`, add `dimensions` to `_FIELDS` and
   `Case` (default `None`), with `SCENARIOS` and `FEATURES` constants, the
   validation and its error messages. Tests in `tests/test_evals_cases.py`.
2. **Coverage and grid, pure (B2 grid and sampling, B3).** New
   `src/advisor/evals/coverage.py`:
   - `PERSONAS`, `cells()` and `sample_cells(count, seed)`;
   - `Probe` and `check_coverage(scenario, probe, question, catalogue) ->
     (ok, reason)`, using `search_products`.

   Tests: `tests/test_analysis_coverage.py`.
3. **Recording (B5, B6).**
   - In `run.py`, extend `RecordingTracer` to keep turns and guardrails.
   - Add a `_recording_tool(tool, sink)` wrapper that keeps the results.
   - Add the new fields to `_record`, and `prompt_sha256` to the report.

   Tests: in `tests/test_evals_run.py`, add tests; leave existing ones
   unedited.
4. **The generator (B2, B4).**
   - `src/advisor/evals/generate.py`: the prompt formatting, the lenient
     JSON parsing, the case writing and the summary.
   - The prompt: `src/advisor/evals/prompts/generate.md`.

   Tests: `tests/test_analysis_generate.py`, with the scripted fake.
5. **Labels (B11), pure.** New `src/advisor/evals/labels.py`: the label
   line model, `parse_labels(text) -> dict[case_id, Label]` (last line
   wins), and `label_line(...)`. Tests: `tests/test_analysis_labels.py`.
6. **The viewer (B8–B12).**
   - Add `python-fasthtml` to `pyproject.toml`, pinned exactly; run
     `uv lock`; read the diff of `uv.lock` (see Risks).
   - `src/advisor/evals/view.py` holds the FastHTML app factory
     `make_app(report_path, labels_path, now)` and `serve(app, host, port)`.
     The app has the routes for one conversation, the label, the critique
     and the filters, plus inline JS for the hotkeys.

   Tests: `tests/test_analysis_view.py`, with `TestClient`.
7. **Taxonomy (B13, B14).**
   - `src/advisor/evals/taxonomy.py`, pure: `validate(taxonomy, labels)
     -> list[str]` (errors) and `parse_draft(text)`.
   - The prompt: `src/advisor/evals/prompts/taxonomy.md`.

   Tests: `tests/test_analysis_taxonomy.py`.
8. **Counts (B15), pure.** `src/advisor/evals/counts.py` builds the three
   tables as Markdown from the report, labels and taxonomy. Tests:
   `tests/test_analysis_counts.py`.
9. **The command.** `src/advisor/evals/analysis.py`:
   - `main(argv, *, env, client_factory, out, err, now, serve)` with the
     subcommands `generate | view | taxonomy | counts`, and exit codes 0/1/2
     as in the spec;
   - the `advisor-analysis` entry in `pyproject.toml`.

   Tests: `tests/test_analysis_cli.py`. It also covers the "cannot reach"
   exit 1 for `generate` and `taxonomy`.
10. **Boundaries (AC8).** In `tests/test_boundaries.py`:
    - only `evals/view.py` imports `fasthtml`, `starlette` or `uvicorn`;
    - a subprocess check that `advisor.evals.{cases,coverage,labels,taxonomy,counts}`
      load none of them, and no SDK;
    - `test_eval_runner_loads_no_sdk` stays as it is.
11. **Docs.**
    - `README.md` → "Evaluating answers": the loop, the commands, the
      label format (for §10), and what is committed.
    - `CLAUDE.md` → Architecture: the new modules (which are pure, which
      are I/O).
    - `.gitignore`: `evals/taxonomy.draft.json`.

## Tests

For each behavioural line, the test that fails if it is mutated:

- **B1:**
  - each of the three keys missing;
  - an extra key;
  - each scenario value accepted;
  - a value outside the list rejected, with the message naming line, case
    and field;
  - `feature` accepting `off-topic` and each category;
  - §8's `evals/cases.jsonl` still parsing (an existing test).
- **B2:**
  - `sample_cells(60, 9)` is stable (a fixed expected prefix) and differs
    for another seed;
  - only meaningful cells appear (`off-topic` × `off-topic` only);
  - two questions per cell, and `--count` respected;
  - the overwrite refusal and `--force`.
- **B3**, per scenario: a candidate just inside and just outside its
  threshold:
  - `exact-match`: 0 vs 1;
  - `several-matches`: 1 vs 2;
  - `no-match`: 0 vs 1;
  - `budget-too-low`: 0 results and ≥ 1 without `max_price`, vs ≥ 1 with;
  - `out-of-stock`: an out-of-stock id vs an in-stock id vs an unknown id;
  - `spelling-differs`: a keyword present verbatim (in any case) vs absent;
  - an unparsable model answer is dropped and counted.
- **B4:**
  - ids unique and `gen-<scenario>-<n>`;
  - `must_decline` only for `off-topic`;
  - no `expect_ids` for no-match and budget;
  - the probe in `note`;
  - the output parses with `parse_cases`.
- **B5, B6:**
  - `turns`, `tools` with results equal to `search_products`' own output,
    `guardrails` (input and output), `dimensions`, `prompt_sha256` equal to
    the file's SHA-256;
  - the wrapped tool returns identical results;
  - §8's existing tests unedited and green.
- **B8:**
  - `serve` is called with `127.0.0.1` and the default 5209, and with
    `--port`;
  - a missing report exits 2.
- **B9:**
  - the page holds the question, dimensions, each check reason, each turn,
    each tool's products (id, name, price, stock), the answer, the
    guardrails and the position header;
  - one assertion per part, each against a distinct value from the fixture.
- **B10:**
  - pass saves without a critique;
  - fail without a critique is refused (status and no line written);
  - fail with a critique is saved;
  - next and previous.
- **B11:**
  - every change appends one line with all fields;
  - last line wins;
  - a restart reloads the labels.
- **B12:**
  - each filter alone and combined;
  - next and previous stay within the filter.
- **B13:**
  - a scripted draft is written to `evals/taxonomy.draft.json`;
  - an invalid draft writes nothing and exits 1.
- **B14:** one failing example per rule:
  - a duplicate id;
  - an empty id;
  - an unknown mode;
  - a mapped case that is not a fail;
  - a failed case not mapped.
- **B15:**
  - mode counts sorted;
  - per-dimension cells;
  - all four agreement cells, each with its own case;
  - ERROR and unlabelled counted apart;
  - the disagreement ids listed;
  - `--out`.
- **AC8:** the import rules above.

Mutation focus for the review:
- the coverage thresholds (`>=`/`>`, 0/1/2);
- the last-line-wins rule;
- the fail-needs-critique rule;
- the agreement cells;
- the `127.0.0.1` bind;
- the filter AND.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS.
- `uv lock --check` exits 0, and the `uv.lock` diff adds only
  `python-fasthtml` and its dependencies (see Risks).
- **Live check** (owed by rule 3 for AC9; the touched paths are not on rule
  1's list). The owner runs the loop once with Ollama `qwen3:8b`, in the
  worktree:
  1. `uv run advisor-analysis generate`, then read and edit
     `evals/generated.jsonl`;
  2. `uv run advisor-eval --cases evals/generated.jsonl`;
  3. `uv run advisor-analysis view <the new report>`, then label at least 20
     conversations, with critiques for the fails;
  4. `uv run advisor-analysis taxonomy evals/labels/<run>.jsonl`, then edit
     the draft and save it as `evals/taxonomy.json`;
  5. `uv run advisor-analysis counts <the report>`.

  Look at:
  - the generator summary (kept and dropped per scenario);
  - whether a generated "no match" question really has no match;
  - the viewer's speed and hotkeys;
  - whether a reload keeps the labels;
  - whether the counts match what was labelled.

## Assumptions I made

- **`CORE_CODE` is not changed here.** The new pure modules (`coverage`,
  `labels`, `taxonomy`, `counts`) decide what the analysis shows, not
  whether a release passes. Adding them would make §9 a Reviewed-tier kit
  change. The reviewer can raise it as a finding, and the owner decides
  (as in §8).
- **Module layout**: flat files in `src/advisor/evals/`, no sub-package.
- **The viewer's HTML** is FastHTML components with a small inline script
  for the hotkeys; no CSS framework and no CDN (it works offline).
- **Lenient JSON parsing** for model output: the first JSON array or object
  in the text. `<think>…</think>` blocks are stripped first.
- **One commit per subtask** at least; the implementer may split further.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-11 — implementation (all 11 subtasks)

Commits (on `feat/9-error-analysis`, after `c806886`): `8e5ea0a` dimensions
(1), `00caf0d`... see `git log`; in order: dimensions (1), grid and coverage
(2), recording (3), generator (4), labels (5), dependency and viewer (6),
taxonomy (7), counts (8), the `advisor-analysis` command (9), boundaries and
docs (10, 11), and one extra test commit from mutant M6.

What shipped:
- `cases.py` `dimensions` (B1); `coverage.py`, `generate.py`, `modeljson.py`,
  `labels.py`, `report.py`, `taxonomy.py`, `counts.py` (pure); `analysis.py`
  (the `advisor-analysis` command) and `view.py` (the FastHTML viewer, the
  only module that imports `fasthtml`, `starlette` and `uvicorn`);
  `run.py` now records turns, tool results, guardrails, dimensions and
  `prompt_sha256` (B5, B6); prompts in `src/advisor/evals/prompts/`;
  README, CLAUDE.md and `.gitignore` updated.
- Tests: pytest 281 before, 464 after (kit tests 255, unchanged by this
  change). New files: `test_analysis_{coverage,generate,labels,view,taxonomy,counts,cli}.py`,
  additions to `test_evals_cases.py`, `test_evals_run.py`,
  `test_boundaries.py`, `test_no_network.py`. §8's existing tests are
  unedited (only imports at the top of `test_evals_run.py` grew).
- New dependency: `python-fasthtml==0.14.14`, because the owner chose a
  custom FastHTML viewer for labelling (spec, owner answers). `uv.lock`: 17
  packages added, none removed or changed: beautifulsoup4, click, fastcore,
  httptools, itsdangerous, oauthlib, python-dateutil, python-fasthtml,
  python-multipart, pyyaml, soupsieve, starlette, tzdata, uvicorn, uvloop,
  watchfiles, websockets. `httpx`, `anthropic` and `langfuse` did not move.
  `uv lock --check` passes. (`httpx2`, which the plan expected, is already
  in the environment through another dependency and did not change.)

Mutants (each one change, restored by copy; the killing test is the first
failure under `pytest -x`):
- coverage: exact-match `>=1`->`>=2` and several-matches `>=2`->`>=1` and
  no-match `==0`->`<=1` (the three `test_*_threshold` tests in
  `test_analysis_coverage.py`); budget `n!=0`->`n>1` and `<1`->`<0` (budget
  test); spelling `n<1`->`n<0` (needs-a-match test); out-of-stock inverted;
  sample size ceil->floor (`test_generate_count_is_respected`).
- spelling-differs verbatim made case-sensitive on the keyword (M6)
  SURVIVED at first; added
  `test_spelling_differs_compares_a_capitalised_keyword_case_insensitively`,
  which kills it.
- last-line-wins (reversed iteration): `test_last_line_per_case_wins`.
- fail-needs-critique: rule swapped in `check_label` (killed by
  `test_view_labels_default_to_evals_labels_by_report_stem` first; the
  `check_label` tests also cover it); viewer check removed:
  `test_fail_without_a_critique_is_refused_and_writes_nothing`.
- agreement cells: misses swapped, both-pass changed, ERROR not apart,
  unlabelled not apart: `test_counts_prints_the_tables_and_writes_them_with_out`
  and `test_each_agreement_cell_has_its_own_case`.
- bind address: viewer `LOCAL_HOST` and analysis `LOCAL_HOST` set to
  `0.0.0.0`: `test_serve_binds_to_loopback_only` and
  `test_view_serves_on_loopback_and_the_default_port`.
- filter AND: label arm, status arm, dimension arm: the
  `test_*_filter*_alone` tests in `test_analysis_view.py`.
- taxonomy: mapped pass accepted, unmapped fail accepted, duplicate id
  accepted: `test_taxonomy_writes_the_draft_and_sends_the_critiques`,
  `test_a_failed_case_mapped_to_an_empty_list_is_not_mapped`,
  `test_a_duplicate_mode_id_is_an_error`.

Divergences from the plan:
- **Version pin 0.14.14, not 0.14.22.** 0.14.22 is one day old; 0.14.14
  (2026-10-20) is the latest release at least two weeks old on 2026-11-11.
- **`tests/conftest.py` socket guard.** On Windows every asyncio event loop,
  and so Starlette's `TestClient`, builds its self-pipe with
  `socket._fallback_socketpair`, which connects two sockets over loopback;
  the guard blocked it, so the plan's "TestClient, no socket" could not run.
  The guard now lets a connect through only when it is called from
  `_fallback_socketpair` to 127.0.0.1 or ::1. Every other connect stays
  blocked; `test_no_network.py` proves both. The reviewer should look at
  this change.
- **mypy:** FastHTML ships no types, so `pyproject.toml` has a
  `[[tool.mypy.overrides]]` with `ignore_missing_imports` for `fasthtml.*`.
  The viewer wraps the route decorators in a typed `_route` helper.
- **`dimensions` and `Case`:** `Case.dimensions` is `None` without the field.
- **Extra pure modules** not named in the plan: `report.py` (report parsing,
  shared by the viewer and `counts`) and `modeljson.py` (lenient JSON
  extraction, shared by the generator and the taxonomy).
- **`advisor-analysis counts` also checks** that `taxonomy.labels` names the
  same file as the labels it reads (B14's last sentence), exit 2.
- `spelling-differs` also requires at least one probe keyword (the spec
  says "none of the probe's keywords verbatim", which is vacuous with none).
- `generate` considers at most two candidates per cell; a cell that returns
  fewer counts the missing ones as dropped ("missing from the model
  answer"). A first call that finds the model unreachable or missing exits 1;
  a later failed call is only counted as dropped.
- `p` saves a pass and stays on the page; `Enter` in the critique box saves
  and moves on (B10 names only `Enter` as moving).
- `CORE_CODE` is not changed (the plan's assumption).
