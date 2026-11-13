<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §10 plan — Label eval runs in Langfuse annotation queues as an alternative to the custom viewer

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Every trace carries its tool calls' results (spec B1-B3), and eval traces
carry the §9 dimensions as tags (B4), so a run can be judged inside
Langfuse. Two new `advisor-analysis` subcommands close the loop: `queue`
puts a run's traces (all, or filtered) into an annotation queue with a
boolean `pass` score config (B5-B11), and `import` turns the queue's
annotation scores back into §9 label lines (B12-B18), so `taxonomy` and
`counts` work unchanged. `langfuse` stays in `tracing.py`, behind an
SDK-free protocol (B19). No new dependency: `langfuse` 5.2.0 is already
locked.

## Risks

- **Changing what the model sees.** B1 adds an argument to `Tracer.tool`;
  `agent._execute` must still return `json.dumps(results)` to the model
  exactly as today. A test asserts the tool result message is unchanged.
- **A tracer failure reaching a run.** The new results go through the same
  `SafeTracer` and `_FanOutTracer` guards; the error paths in `_execute`
  pass `[]`, never `None`.
- **The eval report changing.** `RecordingTracer` gets the results through
  the new argument; the report's `tools[].results` must stay as today (the
  existing `tests/test_evals_run.py` report tests hold it). `offer_results`
  and `_recording_tool` may then go, but only if every existing report
  test passes unedited.
- **An eager `langfuse` import.** `analysis.py` must import
  `advisor.tracing` inside the `queue` and `import` branches only; `view`,
  `taxonomy` and `counts` must not load it (AC8).
- **Tests that pass whatever the code does.** Fakes return distinct values
  (two configs, two queues, scores with different timestamps, a trace from
  another run) so that taking the first instead of the latest, or skipping
  the run filter, fails a test. Tag tests compare whole lists.
- **SDK shape drift.** The SDK methods are called with keyword arguments as
  in 5.2.0's signatures (below); a test against a fake SDK client asserts
  the exact calls, including `filter` JSON, `fields` and pagination.
- **Leaking a key in an error line.** B11's message prints the exception
  type and message only; a test raises an error whose text carries a fake
  key in the env and asserts the key is not printed.
- **Stale citations.** Lines below are at `f461c3b`; the implementer
  re-checks them.
- **Pass 9 footguns:** the list in `REVIEW-POLICY.md` is empty.

## Verified against the codebase

Re-read on `main` at `f461c3b`.

- `src/advisor/tracer.py:28-30` — `Tracer.tool(self, name, arguments, result_count, error)`; `:51` `NoopTracer.tool`.
- `src/advisor/tracing.py:71-77` — `LangfuseTracer.tool` sends `input=arguments`, `output={"result_count": result_count}`, `level="ERROR" if error else "DEFAULT"`.
- `src/advisor/tracing.py:97-125` — `SafeTracer`, `_guard` swallows and logs at DEBUG; `:118` its `tool`.
- `src/advisor/tracing.py:128-142` — `make_tracer(env, tags)`, `REQUIRED_ENV` at `:27`.
- `src/advisor/agent.py:134-148` — `_execute`: three `tracer.tool(call.name, call.arguments, 0, True)` error calls, then `tracer.tool(call.name, call.arguments, len(results), False)` and `ToolResult(call.id, json.dumps(results), False)`.
- `src/advisor/evals/run.py:60-107` — `RecordingTracer`, `offer_results` at `:76`, `tool` at `:89` (`"results": [] if error or results is None else results`).
- `src/advisor/evals/run.py:109-160` — `_FanOutTracer`, `tool` at `:141`.
- `src/advisor/evals/run.py:163-174` — `_recording_tool`.
- `src/advisor/evals/run.py:276-290` — `stamp` from `started`; per-case `tags` list of five; `_FanOutTracer(tracer, tracer_factory(full_env, tags))`.
- `src/advisor/evals/run.py:369-370` — `record["dimensions"] = dict(case.dimensions)` when present.
- `src/advisor/evals/cases.py:51` — `dimensions: dict[str, str] | None = None`.
- `src/advisor/evals/analysis.py:53-81` — `_parser()` with `generate`, `view`, `taxonomy`, `counts`; `:84` `labels_path_for(report)`; `:94-103` `main(argv, *, env, client_factory, out, err, now, serve)`; `:110` `fail(message, code)`; `:123` `load_settings(load_env(env))`.
- `src/advisor/evals/labels.py:41-61` — `label_line(case_id, label, critique, labelled_at, question, answer)`; `:64` `parse_labels`, last line wins.
- `tests/helpers.py:21-22` — a recording test tracer's `tool(name, arguments, result_count, error)`.
- `tests/test_boundaries.py` — the `langfuse`-only-in-`tracing.py` scan and the subprocess import tests.
- SDK 5.2.0 (`.venv/Lib/site-packages/langfuse/api/`): `annotation_queues/client.py:43` `list_queues(page, limit)`, `:87` `create_queue(name, score_config_ids, description)`, `:177` `list_queue_items(queue_id, …)`, `:282` `create_queue_item(queue_id, object_id, object_type)`; `score_configs/client.py:32` `create(name, data_type, …)`, `:101` `get(page, limit)`; `scores/client.py:120` `get_many(limit, cursor, fields, source, queue_id, name, …)`; `observations/client.py:28` `get_many(fields, limit, cursor, filter, …)`. The client is `Langfuse(...).api`.

## Subtasks

1. **Tool results through the tracers** (B1-B3, AC1-AC3).
   - `Tracer.tool(name, arguments, results, error)`: `results: list[dict[str, Any]]`
     replaces `result_count` (the count is `len(results)`); update
     `NoopTracer`, `SafeTracer`, `LangfuseTracer`, `RecordingTracer`,
     `_FanOutTracer`, `tests/helpers.py`.
   - `agent._execute` passes `results` on success and `[]` on each error
     path.
   - `LangfuseTracer.tool` output `{"result_count": len(results),
     "results": results[:10]}` (comment: spec I1 and the cap).
   - `RecordingTracer.tool` records `results` from the argument; remove
     `offer_results`/`_recording_tool` only if the report tests pass
     unedited, else keep them.
   - Tests first; commit.
2. **Dimension tags** (B4, AC4). In `run.py`, append `feature:`,
   `scenario:`, `persona:` tags from `case.dimensions` in that order, each
   only when present. Tests first; commit.
3. **The protocol and the pure logic** (B8, B9, B14-B16, B19). A new
   SDK-free `src/advisor/evals/annotate.py`:
   - `Annotations` protocol: `ensure_score_config()`,
     `ensure_queue(name, config_id)`, `run_traces(stamp) -> list[RunTrace]`
     (trace id, tags, start time), `queued_trace_ids(queue_id)`,
     `add_trace(queue_id, trace_id)`, `annotation_scores(queue_id,
     config_id) -> list[Score]` (trace id, value, comment, timestamp), and
     the errors it raises (`AnnotationError(step, message)`).
   - Pure functions: `report_stamp(report)`, `select_cases(report,
     feature, scenario, persona, status)`, `case_traces(run_traces) ->
     (dict case_id → trace_id, duplicates)`, `labels_from_scores(report,
     scores, case_traces, current_labels) -> (lines, counts)`.
   - Tests in `tests/test_analysis_annotate.py`; commit.
4. **The Langfuse side** (B6, B7, B9, B10, B13, AC5-AC7). In `tracing.py`:
   `LangfuseAnnotations(api)` implementing `Annotations` over
   `Langfuse(...).api` with the 5.2.0 calls above (observations filter
   `[{"type": "arrayOptions", "column": "traceTags", "operator": "all of",
   "value": ["eval", "run:<stamp>"]}, {"type": "boolean", "column":
   "isRootObservation", "operator": "=", "value": true}]`, `fields="basic,trace_context"`;
   scores `source="ANNOTATION"`, `queue_id`, `name="pass"`,
   `fields="details,subject"`, `limit=100`, cursor to the end; config and
   queue lists paged to the end), and `make_annotations(env)` that refuses
   (raises `AnnotationError("config", …)`) unless all of `REQUIRED_ENV`
   are set. Every SDK exception becomes `AnnotationError(step, "<type>:
   <message>")`. Tests against a fake `api` object in
   `tests/test_tracing.py`; commit.
5. **The subcommands** (B5, B7, B8, B11, B12, B17, AC5-AC8). In
   `analysis.py`: `queue <report> [--queue] [--feature] [--scenario]
   [--persona] [--status]` and `import <report> [--queue] [--labels]`,
   with an injectable `annotations_factory` on `main` (default imports
   `advisor.tracing.make_annotations` lazily); missing variables checked
   before any Langfuse call; summary lines; exit codes. Tests in
   `tests/test_analysis_queue.py` and `tests/test_analysis_import.py`;
   a boundary test for the lazy import; commit.
6. **Docs.** `README.md` "Error analysis": the two commands, the queue
   name, the score, the delay note (spec I5), the round trip; the tracing
   section: tool results and dimension tags. `CLAUDE.md` "Error analysis"
   and "Conventions": `annotate.py`, `make_annotations` in `tracing.py`.
   Commit.

## Tests

| Behaviour | Test that fails if it is mutated |
| --- | --- |
| B1 `_execute` passes results / `[]` | `test_agent.py`: a recording tracer sees the rows on success and `[]` for an unknown tool, a `ToolError` and a raising tool; the `ToolResult` content equals `json.dumps(rows)` |
| B2 trace output, cap 10 | `test_tracing.py`: fake client receives `{"result_count": 2, "results": rows}`; 12 rows → 10 sent, `result_count` 12; error → `[]`, level `ERROR` |
| B3 a raising tracer changes nothing | existing `SafeTracer` and `_FanOutTracer` tests, updated to the new signature |
| §9 report unchanged | existing `test_evals_run.py` report tests, unedited apart from the signature in fakes |
| B4 tags | `test_evals_run.py`: two cases, one with all three dimensions, one without; whole tag lists compared |
| B6 config | create when missing; reuse the `BOOLEAN` `pass` and not a `NUMERIC` `pass` listed first; wrong type only → exit 2 |
| B7 queue | create with the config id; reuse by name on page 2; existing queue without the config → exit 2 |
| B8 filters | each filter alone and two combined, on a report with distinct values |
| B9 matching | traces of another run ignored (filter asserted on the fake); duplicate case tag → latest start wins, duplicate count printed |
| B10 skip queued | an already queued trace is not added again; no delete/update method is called (the fake has none) |
| B11/B17 summary and errors | exact summary lines; an `AnnotationError` mid-way exits 2 after earlier adds; a fake key in env not in output |
| B13 scores read | the fake asserts `source`, `queue_id`, `name`, `fields`, and two pages followed |
| B14 latest score wins; outside run skipped | two scores for one trace, the later one is written; a score on a foreign trace is counted |
| B15 mapping | true → pass with comment; false with comment → fail; false without → not written, case id printed |
| B16 idempotent | second import appends nothing; a viewer label then a different import label → appended |
| B18 | the imported file parses with `parse_labels` and `counts` runs on it |
| B5/B12 env | missing variables → exit 2 naming them; the factory is never called |
| B19/AC8 boundaries | `langfuse` only in `tracing.py` (existing scan); subprocess: `advisor-analysis counts` on a fixture loads no `advisor.tracing` |

All Langfuse access in tests is through fakes; `tests/conftest.py` blocks
sockets.

## Validation

- `npm run verify` green
- `npm run check:intent` PASS (it FAILs until `live_checked` is recorded)
- Live check (owed: `src/advisor/tracing.py`, rule 1), in PowerShell with
  the local Langfuse up and the root `.env` keys:
  1. `uv run advisor-eval --cases evals\generated.jsonl` (or `--only` a
     handful of ids); note the report path.
  2. In Langfuse, open one trace: the `search_products` tool observation
     shows `results` rows; the trace has `feature:`/`scenario:`/`persona:`
     tags; the Tracing table filters on a `scenario:` tag.
  3. `uv run advisor-analysis queue <report> --scenario out-of-stock`:
     the summary line; the queue `advisor-eval <stamp>` exists with the
     `pass` score.
  4. In the queue UI, label at least five traces, at least one `false` with
     a comment on the score. Note whether the nested tool observations read
     clearly (intent question 7) and whether the comment sits on the score
     (spec A6).
  5. `uv run advisor-analysis import <report>` (rerun after a few minutes if
     scores are missing, spec I5); then a second time: nothing appended.
  6. `uv run advisor-analysis counts <report>` runs on the labels.
  7. `uv run advisor "I need noise-cancelling headphones under 200 euros."`
     still answers; its trace shows tool results.

## Assumptions I made

- `result_count` leaves the `Tracer.tool` signature (derived from
  `results`) but stays in the Langfuse output (spec A4).
- The stamp a queue and an import use comes from the report's `started`
  field, formatted as `run.py` does, so it equals the `run:` tag.
- `annotate.py` stays out of `CORE_CODE` (`scripts/intent-check-lib.mjs:154-159`),
  as §9's pure modules (`labels.py`, `taxonomy.py`, `counts.py`) did; the
  kit's scripts are not edited.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-13: implementation (all six subtasks)

Commits: `d85477d` (1, tool results), `73537c2` (2, dimension tags),
`f700453` (3, `annotate.py`), `e144869` (4, `LangfuseAnnotations`),
`ed847c4` (5, `queue` and `import`, boundary tests), `62268b2` (6, docs), plus
the final commit with this entry, the `in-review` status and a test-isolation
fixture.

Shipped: B1-B19 as specified. `Tracer.tool(name, arguments, results, error)`
everywhere; the Langfuse tool observation carries `{"result_count", "results"}`
(cap 10); eval traces carry the three dimension tags; new SDK-free
`src/advisor/evals/annotate.py`; `LangfuseAnnotations` and `make_annotations`
in `tracing.py`; `queue` and `import` in `analysis.py` with an injectable
`annotations_factory` (lazy `advisor.tracing` import); README and CLAUDE.md.

Tests: 607 passed at the end (496 after subtask 1; new files
`tests/test_analysis_annotate.py`, `test_analysis_queue.py`,
`test_analysis_import.py`, `test_tracing_annotations.py`,
`tests/fake_langfuse_api.py`). `npm run verify` green.

Mutants run on behavioural lines (each restored by copy; full suite, `-x`):
M1 agent passes `[]` on success: `test_agent.py::test_tracer_sees_generations_and_tools_in_order`.
M2 no cap of 10: `test_tracing.py::test_tool_output_is_cut_to_ten_rows_but_counts_all`.
M3 `result_count` constant: `test_tracing.py::test_langfuse_tracer_with_real_sdk_and_in_memory_exporter`.
M4 dimension tag order: `test_evals_run.py::test_dimensions_become_three_more_tags_in_order`.
M5 earliest trace wins: `test_analysis_annotate.py::test_a_repeated_case_tag_takes_the_latest_start_and_counts_the_repeat`.
M6 earliest score wins: `test_analysis_annotate.py::test_the_latest_score_per_trace_wins_whatever_the_order`.
M7 filter "any of": `test_tracing_annotations.py::test_run_traces_filters_on_tags_root_and_follows_the_cursor`.
M8 first named config accepted: `test_tracing_annotations.py::test_the_boolean_pass_config_is_reused_not_a_numeric_one_listed_first`.
M9 queued traces re-added: `test_analysis_annotate.py::test_plan_separates_new_queued_and_without_trace`.
M10 critique ignored in the unchanged test: `test_analysis_annotate.py::test_a_different_label_or_critique_is_appended`.
M11 no env check: `test_analysis_import.py::test_a_missing_variable_exits_2_without_calling_langfuse`.
M12 fail without critique written: `test_analysis_annotate.py::test_a_fail_without_a_comment_is_not_written_but_listed`.
M13 outside-run scores not skipped: `test_analysis_annotate.py::test_scores_on_traces_outside_the_run_are_counted_and_skipped`.
M14 score source not ANNOTATION: `test_tracing_annotations.py::test_annotation_scores_ask_for_the_queue_and_follow_the_cursor`.
M15 queue without config accepted: `test_tracing_annotations.py::test_an_existing_queue_without_the_pass_config_is_a_conflict`.
M16 secrets not redacted: `test_tracing_annotations.py::test_a_secret_in_an_sdk_error_is_redacted`.
M17 error path hands rows to the tracer: `test_agent.py::test_tracer_gets_an_empty_list_on_every_error_path`.
M18 filters OR instead of AND: `test_analysis_annotate.py::test_filters_combine_with_and`.
M19 no newline repair before an append: `test_analysis_import.py::test_a_file_without_a_final_newline_gets_one_before_the_append`.
M20 stamp not converted to UTC: `test_analysis_annotate.py::test_stamp_is_the_started_time_in_utc_as_run_py_formats_it`.
All 20 killed.

Divergences from the plan:
- `Annotations` has `find_queue(name)` (import must not create a queue) and
  `annotation_scores(queue_id)` without `config_id` (the SDK filter is by
  score name, not config).
- The observations call uses `fields="core,basic,trace_context"`, not
  `"basic,trace_context"`: the trace id and start time are in `core`, and the
  SDK says unspecified fields default to `core` and `basic`.
- `offer_results` and `_recording_tool` were removed; their two direct tests
  were replaced by one `RecordingTracer` test (the report tests pass
  unedited apart from tracer signatures in fakes).
- Fake-SDK tests are in `tests/test_tracing_annotations.py` (plan: `test_tracing.py`),
  sharing `tests/fake_langfuse_api.py`.
- `LangfuseAnnotations` removes the secret and public key from SDK error text
  (not in the plan; it backs AC7's "no key in the output").
- `queue` with filters that match no case exits 2 before touching Langfuse
  (no empty queue is created); the spec does not cover it.
- `plan_additions` and `ImportResult` helpers in `annotate.py` carry the
  queue plan and the import counts (pure, tested).
- Tests that exercise `import` change the working directory to a temp dir, so
  a default `evals/labels/` path can never reach the repository.
- Nothing was run against a live Langfuse; the live check (AC9) is owed.

### 2026-11-13: rework after review round 1

Commit: the one following `fcd5471` (subject "§10: rework after review round 1").
Tests: 608 passed (607 before). `npm run verify` green.

Fixed every "Needs rework:" finding, tests and docs only (no behaviour change):
- `make_annotations(ENV)` redaction: `test_make_annotations_redacts_both_keys_from_an_sdk_error`.
- Exact messages of the B6 and B7 conflicts in `test_tracing_annotations.py`.
- `test_boundaries.py`: the subprocess test also runs `view` (with a no-op `serve`).
- `test_a_bad_status_is_a_usage_error` uses a real report and asserts no fake call and no "No case".
- `report_stamp` of a time without an offset.
- CLAUDE.md Commands line; README exit-2 list; `analysis.py` module docstring.

Mutants run on the rework (restored by copy; all killed):
T30 `LangfuseAnnotations(client.api)` without secrets: `test_tracing_annotations.py::test_make_annotations_redacts_both_keys_from_an_sdk_error`.
T6 no `except AnnotationError: raise`: `test_tracing_annotations.py::test_a_pass_config_of_another_type_only_is_a_conflict_naming_the_type`.
Q15 `import advisor.tracing` in the `view` branch: `test_boundaries.py::test_view_counts_and_taxonomy_load_neither_tracing_nor_langfuse`.
Q13 no `choices=STATUSES`: `test_analysis_queue.py::test_a_bad_status_is_a_usage_error`.
N2 naive `started` not read as UTC: `test_analysis_annotate.py::test_stamp_is_the_started_time_in_utc_as_run_py_formats_it`.

Left alone as instructed: the "Worth a look" LOWs.
