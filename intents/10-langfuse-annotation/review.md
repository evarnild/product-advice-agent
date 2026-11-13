<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §10 review — Label eval runs in Langfuse annotation queues as an alternative to the custom viewer

verdict: rework
tier: reviewed
reviewed-commit: bf0491e9b7038ed67178d1cbc04a57bed4b36f7e
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, by the path table (`src/advisor/tracing.py`, Reviewed by
meaning: what is sent to Langfuse) and by `review_tier: reviewed` in
`metadata.yml`; the HIGH finding would raise it too.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 10` →
"nth attested auto change = 5, every 3, sampled: no".

Verdict: rework. Five mutants on non-equivalent lines survive; each finding
below that needs work says "Needs rework:" and is mechanical (a test or a
doc line, fixed by the spec or the plan). No "Needs decision:".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (every reported divergence judged against the spec; none is a defect) |
| 2 | Type check | PASS |
| 3 | Behaviour against the spec | 3 LOW, worth a look |
| 4 | Tests prove the behaviour | findings: 73 mutants, 66 killed, 7 survived (2 equivalent) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass ("496 after subtask 1" not reproduced) |
| 7 | Documentation | 2 LOW |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; a candidate below) |

**The implementer's divergences, against the spec:**
- `find_queue(name)` added, `annotation_scores(queue_id)` without
  `config_id`: matches B12 (import never creates a queue) and B13 (filter
  by the name `pass`).
- `fields="core,basic,trace_context"`: harmless; `core` is always included
  per the SDK, and B9's `trace_context` is there.
- `RecordingTracer.offer_results` and `_recording_tool` removed: the report
  tests pass with only fake signatures changed;
  `test_the_report_keeps_turns_tools_with_results_and_guardrails` kills R5,
  so §9's `tools[].results` is still proven.
- Fake-SDK tests in `tests/test_tracing_annotations.py` with
  `tests/fake_langfuse_api.py`: fine.
- Import tests `chdir` to `tmp_path`: `git status --short --ignored evals/`
  empty; `git diff main...HEAD -- evals/` empty; no stray `run.jsonl`.
- Key redaction in SDK error text: in scope (AC7); its wiring is unproven
  (HIGH).
- Open behaviours: no matching case exits 2 before Langfuse (LOW below);
  a missing labels file is empty (B16 "or has none"); archived configs not
  considered (LOW below).

**Checked hard:** `agent._execute` still returns `ToolResult(call.id,
json.dumps(results), False)` (`agent.py:147-148`); error paths pass `[]`
(A1-A3 killed). The cap is in `LangfuseTracer.tool` only (`tracing.py:85`),
`result_count` is `len(results)` (T1-T3 killed). SDK 5.2.0 signatures,
enums (`StrEnum`), the observations filter JSON and pagination to the end
all match (T7, T8, T15-T18 killed). No delete, update or score-write call
(grep; the fake SDK has none). `advisor.tracing` is imported lazily
(`analysis.py:78-82`, Q11 killed); `langfuse` only in `tracing.py`.

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 10, feature)
  note:  18 file(s), 2118 line(s) changed outside intents/.
```
With this report committed (`live-check: owed`), `check:intent` FAILs until
`live_checked` is recorded: the owner's gate, not rework.

## Findings
- **HIGH** `src/advisor/tracing.py:359`: the redaction behind AC7 ("no key
  in the output") is not proven end to end. T30 (`LangfuseAnnotations(client.api)`,
  no secrets) survives: `test_a_secret_in_an_sdk_error_is_redacted` builds
  `LangfuseAnnotations(..., secrets=...)` directly, and the `make_annotations`
  test never raises an SDK error. Needs rework: in a `make_annotations(ENV)`
  test, set `api.error_on["scores.get_many"] = RuntimeError("401 sk-test
  pk-test")`, call `annotation_scores`, assert neither key is in
  `str(error)`. Kills T30.
- **MEDIUM** `src/advisor/tracing.py:192-193`: T6 (no `except
  AnnotationError: raise`) survives; the B6/B7 conflicts would then read
  `Langfuse config failed: AnnotationError: Langfuse config failed: …`.
  Needs rework: assert the exact message of both conflicts (e.g. starts
  with "a score config named 'pass' exists with data type NUMERIC"). Kills
  T6.
- **MEDIUM** `tests/test_boundaries.py:176`: AC8 names `view`, `taxonomy`
  and `counts`; the subprocess test covers the last two. Q15 (`import
  advisor.tracing` in the `view` branch) survives. Needs rework: also run
  `main(['view', report, '--labels', labels], env={}, …, serve=lambda app,
  host, port: None)` and assert `advisor.tracing`, `langfuse`,
  `opentelemetry` absent. Kills Q15.
- **MEDIUM** `tests/test_analysis_queue.py:155`:
  `test_a_bad_status_is_a_usage_error` passes for the wrong reason (the
  report path does not exist). Q13 (no `choices`) survives. Needs rework:
  use `report_file(tmp_path)`, assert exit 2, no factory call, no fake call
  and `"No case" not in err`. Kills Q13.
- **LOW** `src/advisor/evals/annotate.py:88-89`: the naive-`started` branch
  is untested; N2 survives. Needs rework: `report_stamp({"started":
  "2026-11-12T10:30:05"}) == "20261112T103005Z"`. Kills N2.
- **LOW** `CLAUDE.md:31`: the Commands line still reads
  `generate|view|taxonomy|counts`. Needs rework: add `queue|import`, noting
  they need the three `LANGFUSE_*` variables.
- **LOW** `README.md:240`: the "Exit 2" list omits a filter matching no
  case, a missing queue and unreadable files; `analysis.py:8` describes exit
  2 as "bad arguments or files". Needs rework: add those cases and "a
  Langfuse error".
- **LOW** `src/advisor/evals/analysis.py:328`: filters matching no case exit
  2 before Langfuse; B8/B11 are silent (literal B11: exit 0 with a
  summary). Fits the module's exit-2 meaning and catches a typo. Worth a
  look (the owner, at the diff read).
- **LOW** `src/advisor/tracing.py:227`: `ensure_score_config` ignores
  `is_archived`. Worth a look.
- **LOW** `src/advisor/agent.py:147-148`: the tracer gets the same `results`
  list before `json.dumps(results)`; a future tracer that mutated it would
  change what the model sees. Worth a look: build the content first.
- **Equivalent survivors:** R3 (`run.py:91`, the agent passes `[]` on every
  error path) and N7 (`annotate.py:129`, a trace has one `case:` tag).
- **Pass 9 candidate:** "a negative test whose input fails for an earlier
  reason proves nothing about the check it names" (Q13).

**Mutants** (73; one per changed behavioural line; full suite with `-x`;
restored by byte copy). Killed: A1-A5 (`agent.py`), T1-T5, T7-T29, T31
(`tracing.py`), N1, N3-N6, N8-N17 (`annotate.py`), Q1-Q12, Q14
(`analysis.py`), R1, R2, R4, R5 (`run.py`), each by the test named in the
reviewer's table. Survived:

| Mutant | Target | Result | Expected killer |
| --- | --- | --- | --- |
| T30 secrets not passed | tracing.py:359 | SURVIVED | make_annotations redaction test (HIGH) |
| T6 AnnotationError re-wrapped | tracing.py:192-193 | SURVIVED | exact conflict messages |
| Q15 `view` loads tracing | analysis.py view branch | SURVIVED | extended boundary subprocess test |
| Q13 `--status` without choices | analysis.py:111 | SURVIVED | fixed bad-status test |
| N2 naive not UTC | annotate.py:88-89 | SURVIVED | naive-started stamp test |
| R3 recording keeps rows on error | run.py:91 | SURVIVED (equivalent) | – |
| N7 last case tag | annotate.py:129 | SURVIVED (equivalent) | – |

**The rework must kill:** T30, T6, Q15, Q13, N2.

## Not checked
- Live Langfuse behaviour: whether v4 accepts the observations filter and
  fills `traceTags`/`isRootObservation` for the root span; whether queue
  scores carry `queueId` and `subject.kind == "trace"` in Scores v3; the
  comment on the score (spec A6); nested tool observations in the queue
  screen (intent question 7); the Scores API delay (I5).
- Whether `Langfuse(...)` in `make_annotations` starts network activity
  before the first call and exits cleanly (patched in tests).
- The Progress entry's "496 after subtask 1".
- ruff and mypy on mutants (pytest decided).

## Live check
Owed by rule 1 (`src/advisor/tracing.py`) and rule 3 (the Not-checked
server items, A6, intent question 7). Covers AC9. In PowerShell:

1. Start the stack if needed: `cd C:\Users\eric\src\product-advice-agent;
   docker compose -f infra/langfuse/docker-compose.yml up -d`; open
   `http://localhost:3000`.
2. `cd C:\Users\eric\src\product-advice-agent-wt\10-langfuse-annotation`;
   `Copy-Item ..\..\product-advice-agent\.env .env` (gitignored; it holds
   `LANGFUSE_HOST`, the two keys and the model settings).
3. `uv run advisor-eval --cases ..\..\product-advice-agent\evals\generated.jsonl
   --only gen-out-of-stock-1,gen-out-of-stock-2,gen-out-of-stock-3,gen-out-of-stock-4,gen-out-of-stock-5,gen-out-of-stock-6,gen-out-of-stock-7,gen-out-of-stock-8,gen-budget-too-low-1,gen-budget-too-low-2`;
   note `evals\runs\<stamp>-<provider>.json`.
4. Langfuse → Tracing, filter tag `scenario:out-of-stock`: 8 traces. One
   trace: tags `eval`, `provider:…`, `model:…`, `run:<stamp>`,
   `case:gen-out-of-stock-N`, `feature:<v>`, `scenario:out-of-stock`,
   `persona:<v>` in that order; the `search_products` output is
   `{"result_count": n, "results": [...]}` with full rows.
5. `uv run advisor-analysis queue evals\runs\<stamp>-<provider>.json
   --scenario out-of-stock` → `queue advisor-eval <stamp>: 8 added, 0
   already queued, 0 no trace` (on "no trace", wait a minute and rerun).
   Again → `0 added, 8 already queued`. Langfuse has a Boolean `pass`
   config and the queue with 8 items. No key in any output.
6. In the queue UI label at least five traces: at least one `true`, at
   least one `false` with a comment typed on the score (A6); optionally a
   `false` without comment. Note whether the nested tool observation and
   its rows read clearly (intent question 7).
7. `uv run advisor-analysis import evals\runs\<stamp>-<provider>.json` →
   `import: N labels written, 0 unchanged, k fail without critique, 0
   outside the run`. Fewer than labelled: wait a few minutes, rerun (I5).
   `Get-Content evals\labels\<stamp>-<provider>.jsonl`: label, critique,
   UTC `labelled_at` as entered. Once more → `0 labels written, N
   unchanged`.
8. `uv run advisor-analysis taxonomy evals\labels\<stamp>-<provider>.jsonl`
   (one model call; writes `evals\taxonomy.draft.json`), then `uv run
   advisor-analysis counts evals\runs\<stamp>-<provider>.json --taxonomy
   evals\taxonomy.draft.json`: the tables print. Do not overwrite
   `evals\taxonomy.json`.
9. `uv run advisor "I need noise-cancelling headphones under 200 euros."`
   answers; its trace (`provider:`/`model:` only) shows `results` rows.
10. Before `/ship`: commit or delete the new `evals\labels\<stamp>-<provider>.jsonl`
    (a dirty worktree blocks the removal; `evals\runs\` and `.env` are
    gitignored).

You should see every line above, the comment on the `pass` score, readable
tool rows in the queue screen, an idempotent import, and no key printed. If
A6 fails, the spec goes back to the owner.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/10-langfuse-annotation` at bf0491e; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; ruff
  "All checks passed!"; "125 files already formatted"; mypy "Success: no
  issues found in 27 source files"; pytest "607 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → "type-check: PASS
  (intent 10, feature)", "18 file(s), 2118 line(s)". Matches.
- **Coordinator, re-run:** every surviving mutant with my own harness
  (backup by copy, replacement asserted once, CRLF-aware, full pytest,
  restore by copy): T30, T6, Q15, Q13, N2, R3, N7 all SURVIVED ("607
  passed"). Matches the reviewer.

**Reviewer, verified:** HEAD bf0491e on its branch, `main` 543f932, nothing
pushed; verify; check:intent; the sampling line; `git diff main...HEAD`
read in full against B1-B19 and AC1-AC9; SDK 5.2.0 signatures, models,
enums, pagination and filter docs; 73 mutants; no tracked file edited.

**Taken on trust:** the Progress entry's "496 after subtask 1"; that the
self-hosted Langfuse v4 server behaves as the SDK 5.2.0 docstrings say (the
live check); the case ids in the main checkout's untracked
`evals/generated.jsonl`.
