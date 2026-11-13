<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §10 review — Label eval runs in Langfuse annotation queues as an alternative to the custom viewer

verdict: escalate
tier: reviewed
reviewed-commit: 9e2ab53bbfc8669046c611e3487aacec0e364142
round: 2
sampled: no
run: auto
live-check: owed

Tier: Reviewed (the path table, `src/advisor/tracing.py` by meaning, and
`review_tier: reviewed`). The reviewer proposed `attest`; the coordinator
writes `escalate`, as for §12, because the Reviewed tier needs the owner's
diff read. No finding needs rework or a decision.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 10` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Scope: the round-2 delta is `git diff fcd5471..HEAD`: d1afd13 (rework:
tests, `CLAUDE.md`, `README.md`, the `analysis.py` module docstring, a
Progress entry below the marker) and 9e2ab53 (`auto_round: 2`). No `src/`
behaviour changed.

## Round-1 findings: resolution
| Round 1 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| HIGH | T30: `make_annotations` redaction wiring unproven | fixed | `test_make_annotations_redacts_both_keys_from_an_sdk_error` (`tests/test_tracing_annotations.py:282`) goes through `make_annotations(ENV)`, raises `RuntimeError("401 sk-test for pk-test")` from `scores.get_many`, asserts `"Langfuse scores failed: RuntimeError: 401 *** for ***"`; T30 KILLED |
| MEDIUM | T6: conflict errors re-wrapped | fixed | both conflict tests assert the full message; T6 KILLED by both |
| MEDIUM | Q15: AC8's `view` leg | fixed | the subprocess test runs `view` with `env={}` and a no-op `serve`, asserts `rc3 == 0`, then no `advisor.tracing`/`langfuse`/`opentelemetry`; Q15 KILLED |
| MEDIUM | Q13: bad-status test passed for the wrong reason | fixed | real report file; exit 2, no factory or fake call, no "No case"; Q13 KILLED |
| LOW | N2: naive `started` | fixed | `report_stamp({"started": "2026-11-12T10:30:05"}) == "20261112T103005Z"`; N2 KILLED (timezone-dependent, LOW below) |
| LOW | `CLAUDE.md:31` Commands line | fixed | `generate\|view\|taxonomy\|counts\|queue\|import`, with the `LANGFUSE_*` note |
| LOW | README exit-2 list, `analysis.py` docstring | fixed | `README.md:240-243` and `analysis.py:8-11` list every `fail(…, 2)` case |
| LOW | no-match exits 2; archived configs; `results` aliasing | carried, worth a look | – |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (tests, docs, a Progress entry below the marker) |
| 2 | Type check | FAIL on the owed live check only (the owner's gate) |
| 3 | Behaviour against the spec | pass (no `src/` behaviour changed; round 1's reading against B1-B19, AC1-AC9 stands) |
| 4 | Tests prove the behaviour | pass (the 5 rework targets killed; 2 equivalent survivors) |
| 5 | Conventions | pass (fake SDK, patched `tracing.Langfuse`, no socket) |
| 6 | Numbers in prose | pass ("608 passed (607 before)") |
| 7 | Documentation | pass (one cosmetic LOW) |
| 8 | Guardrails and hygiene | pass (`pk-test`/`sk-test` are placeholders) |
| 9 | Repository-specific footguns | pass |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 10, feature)
  error: A live check is owed and not recorded. Do the steps in intents/10-langfuse-annotation/review.md → ## Live check, then set live_checked: <date> in intents/10-langfuse-annotation/metadata.yml.
  note:  18 file(s), 2154 line(s) changed outside intents/.
```
Exit 1, only on the owed live check.

## Findings
No finding needs rework or a decision.
- **LOW** (worth a look) `tests/test_analysis_annotate.py:57`: the N2 kill
  depends on the host's timezone; on a UTC host (typical CI) the mutant
  would survive. Hardening: compare a naive stamp with the `+00:00` stamp
  under a pinned non-UTC local zone, or accept as is.
- **LOW** (worth a look) `tests/test_boundaries.py:177`: the comment says
  the subprocess runs `counts` and `taxonomy`; it now runs `view` too.
- **Carried** (worth a look, for the owner's diff read): filters matching no
  case exit 2 before Langfuse (`analysis.py:328`); archived configs not
  considered (`tracing.py:227`); the tracer and `json.dumps` share the
  `results` list (`agent.py:147-148`).

**Mutants** (round-1 survivors; backup by copy, one CRLF-aware replacement
asserted once, full pytest, restore by copy):

| Mutant | Target | Result | Killed by |
| --- | --- | --- | --- |
| T30 secrets not passed | tracing.py:359 | KILLED | test_make_annotations_redacts_both_keys_from_an_sdk_error |
| T6 no `except AnnotationError: raise` | tracing.py:191-192 | KILLED | test_a_pass_config_of_another_type_only_is_a_conflict_naming_the_type, test_an_existing_queue_without_the_pass_config_is_a_conflict |
| Q15 `view` loads tracing | analysis.py:220 | KILLED | test_view_counts_and_taxonomy_load_neither_tracing_nor_langfuse |
| Q13 `--status` without `choices` | analysis.py:113 | KILLED | test_a_bad_status_is_a_usage_error |
| N2 naive time not UTC | annotate.py:88-89 | KILLED | test_stamp_is_the_started_time_in_utc_as_run_py_formats_it |
| R3 recording keeps rows on error | run.py:91 | SURVIVED (equivalent) | – |
| N7 last case tag | annotate.py:129 | SURVIVED (equivalent) | – |

Round 1's 66 kills were not re-run: no `src/` behaviour changed and no
assertion was removed.

## Not checked
- Live Langfuse v4 behaviour: the observations filter, `traceTags` and
  `isRootObservation` on the root span; `queueId` and `subject.kind` on
  queue scores; the comment on the score (A6); nested tool observations in
  the queue screen (intent question 7); the Scores API delay (I5); whether
  `Langfuse(...)` starts network activity on construction.
- ruff and mypy on mutants; the N2 kill on a UTC host.

## Live check
Owed by rule 1 (`src/advisor/tracing.py`) and rule 3. Covers AC9, A6 and
intent question 7. In PowerShell:

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
   config and the queue with 8 items. No key in any output; an SDK error,
   if any, shows `***` for the keys.
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

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/10-langfuse-annotation` at 9e2ab53; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; ruff
  "All checks passed!"; "126 files already formatted"; mypy "Success: no
  issues found in 27 source files"; pytest "608 passed". Matches the
  reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL on the owed live
  check only, "18 file(s), 2154 line(s)". Matches.
- **Coordinator, re-run:** T30, T6, Q15, Q13, N2 KILLED, each by the test in
  the table ("1 failed, 607 passed"; T6 "2 failed, 606 passed"); R3 and N7
  SURVIVED ("608 passed"). Matches the reviewer and the implementer.

**Reviewer, verified:** HEAD 9e2ab53, `main` 543f932, nothing pushed;
`git diff fcd5471..HEAD` read in full (under `src/` only the `analysis.py`
docstring); verify; check:intent; the sampling line; the 7 mutants; every
exit-2 claim against `fail(…, 2)` in `analysis.py`; no tracked file edited.

**Taken on trust:** round 1's 66 kills and its reading of the spec
(unchanged code); the Langfuse v4 server's behaviour (the live check); the
case ids in the main checkout's untracked `evals/generated.jsonl`.

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: bf0491e9b7038ed67178d1cbc04a57bed4b36f7e
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, by the path table (`src/advisor/tracing.py`, Reviewed by
meaning: what is sent to Langfuse) and by `review_tier: reviewed` in
`metadata.yml`; the HIGH finding would raise it too.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 10` →
"nth attested auto change = 5, every 3, sampled: no".

Verdict: rework. Five mutants on non-equivalent lines survive; each finding
below that needs work says "Needs rework:" and is mechanical (a test or a
doc line, fixed by the spec or the plan). No "Needs decision:".

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 10, feature)
  note:  18 file(s), 2118 line(s) changed outside intents/.
```
With this report committed (`live-check: owed`), `check:intent` FAILs until
`live_checked` is recorded: the owner's gate, not rework.

### Findings
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

### Not checked
- Live Langfuse behaviour: whether v4 accepts the observations filter and
  fills `traceTags`/`isRootObservation` for the root span; whether queue
  scores carry `queueId` and `subject.kind == "trace"` in Scores v3; the
  comment on the score (spec A6); nested tool observations in the queue
  screen (intent question 7); the Scores API delay (I5).
- Whether `Langfuse(...)` in `make_annotations` starts network activity
  before the first call and exits cleanly (patched in tests).
- The Progress entry's "496 after subtask 1".
- ruff and mypy on mutants (pytest decided).

### Live check
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

### Verified myself vs. taken on trust

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
