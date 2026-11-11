<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §9 review — Error analysis on top of the eval suite: synthetic questions by dimension, a trace viewer and pass/fail labels with critiques

verdict: rework
tier: reviewed
reviewed-commit: 35f2762e52e756d0fab986b0d537d0596161db8c
round: 1
sampled: no
run: auto
live-check: owed

Tier: Reviewed, set by input 3 (this report: the HIGH finding on B5/B9).
Input 1 (paths) gives Attested: `src/**` outside the by-meaning list,
tests, build config (`pyproject.toml`, `uv.lock`), `.gitignore`, docs.
Input 2 (`review_tier`) is empty. The viewer is a localhost server whose
reader is the owner (a human in between); `src/advisor/evals/prompts/*.md`
are tooling prompts, not the shipped `src/advisor/prompts/**`; the
`conftest.py` loosening is test-only and sound in substance; the mypy
override sets `ignore_missing_imports` for `fasthtml`/`fasthtml.*` only. So
none of these raised the tier; the HIGH did, and nothing lowers it.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 9` → "nth
attested auto change = 5, every 3, sampled: no".

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (`report.py`, `modeljson.py` are factoring within scope) |
| 2 | Type check | pass (PASS) |
| 3 | Behaviour against the spec | findings (1 HIGH: B5/B9) |
| 4 | Tests prove the behaviour | findings (V12, V13 survive in the viewer; C1, C2, C3 survive in the conftest guard) |
| 5 | Conventions | pass (fasthtml, starlette, uvicorn only in `evals/view.py`; pure modules load no web framework or SDK; sockets blocked; fake model only; the plan's `CORE_CODE` assumption holds) |
| 6 | Numbers in prose | pass (281 at c806886, 464, kit 255, the 17 packages, 60 questions from 30 cells reproduced; release dates not checked) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | findings (MEDIUM `.sesskey` committed; LOW cross-origin POSTs) |
| 9 | Repository-specific footguns | pass (list empty; one entry proposed below) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 9, feature)
  note:  31 file(s), 4120 line(s) changed outside intents/.
```
Exit 0.

## Findings
- **HIGH** `src/advisor/evals/run.py:71-91` (`_recording_tool`) and
  `src/advisor/evals/view.py:204-213` (`_turns`) — a call to an unknown
  tool is missing from `tools`, and the viewer then attributes later tool
  calls to the wrong turn. B5 asks for "per tool call, the name, the
  arguments, the results … and whether it was an error", but calls are
  recorded only by wrapping `Tool.run`, and `agent._execute` answers an
  unknown tool name without calling any `run` (`agent.py:135-137`). The
  turn still lists the name, and `_turns` slices `tools[:len(names)]`, so
  every later call shifts one turn earlier. Reproduced: turn 1 calls
  `get_product`, turn 2 `search_products {"category":"laptop",
  "max_price":700}` → `tools` holds only the search, the page shows the
  laptop search under **Model turn 1**, and `get_product` appears nowhere.
  A hallucinated tool name is a realistic `qwen3:8b` failure, and exactly
  what error analysis should show (B9: "each model turn in order with its
  tool calls"). V12 survives because the B9 fixture has one call in turn 1.
  Needs rework: record every call from `RecordingTracer.tool` (called for
  unknown tools, bad arguments and successes alike), in call order, and
  fill `results` from the wrapper (so B6 still holds); add a
  `test_evals_run.py` test (an unknown-tool turn, then a search turn:
  `tools` has both, the first `error: true`) and a `test_analysis_view.py`
  fixture with calls in two turns, asserting each renders under its own
  turn (kills V12).
- **MEDIUM** `.sesskey:1` (committed in 8b70983), from
  `src/advisor/evals/view.py:277` — `FastHTML(...)` is built without
  `secret_key`, so FastHTML's `get_key` reads or writes `.sesskey` in the
  current directory: the tests created it at the repo root and it was
  committed; every `view` run writes one where it starts. The app reads no
  session and is localhost-only, but a signing secret in git breaks pass
  8's "no secret, token … committed". Needs rework: pass an ephemeral
  `secret_key=secrets.token_hex(32)`; `git rm .sesskey`; add `.sesskey` to
  `.gitignore`; add a test that `make_app` writes no file
  (`monkeypatch.chdir(tmp_path)`, directory stays empty).
- **MEDIUM** `src/advisor/evals/view.py:240` — B9's guardrail verdicts are
  proven only for "allowed": V13 (always "allowed") survives, since every
  fixture guardrail is allowed. Needs rework: a fixture case with a
  guardrail `allowed: False` and a reason, asserting `input: BLOCKED (…)`.
- **MEDIUM** `tests/conftest.py:26-31`, `tests/test_no_network.py:23-34` —
  the socket-guard exemption is sound in substance (only a caller code
  object named `_fallback_socketpair` in a file ending `socket.py`,
  connecting to 127.0.0.1 or ::1; `_fallback_socketpair` connects only to
  its own listener; `connect_ex` and `create_connection` stay blocked; C5
  shows the exemption is needed). But the only test fails all three
  conditions at once, so dropping any one survives (C1, C2, C3); and
  `endswith("socket.py")` also matches `websocket.py`. Needs rework:
  compare `caller.co_filename` with `socket.__file__`; add three tests
  that each fail exactly one condition, with code compiled via
  `compile(src, <filename>, "exec")`: `_fallback_socketpair` defined in the
  test file to loopback (C2); another function name compiled with
  `socket.__file__` (C1); `_fallback_socketpair` compiled with
  `socket.__file__` to `("10.255.255.1", 9)` (C3); each must raise
  `NetworkBlockedError`.
- **LOW** `src/advisor/evals/view.py:447` (`save_label`) — the viewer
  accepts cross-origin POSTs and any `Host` header (verified: a POST with
  `Origin: http://evil.example` returned 303 and appended a label; a GET
  with `Host: evil.example` returned 200). While it runs, any page in the
  owner's browser could append labels, which are committed and meant as
  few-shot examples. Synthetic data, and the spec says "no
  authentication", so no defect against the spec. Worth a look: reject a
  POST whose `Origin` (when present) isn't `http://127.0.0.1:<port>`, and
  a request whose `Host` isn't `127.0.0.1:<port>`.
- **Implementer's choices on open points:** each a reasonable reading, no
  decision needed: `spelling-differs` needs a keyword (tested, M6); at most
  2 candidates per cell (B2, tested, G3); the first unreachable call exits
  1, later ones are drops (non-functional; G1, G2); `p` stays on the page
  (B10 names only `Enter` as moving; judge in the live check: a pass costs
  `p` then `j`); `counts` checks `taxonomy.labels` (B14; A1); a refused
  label is 422 with the critique kept.
- **`CORE_CODE`:** no finding; `coverage`, `labels`, `taxonomy`, `counts`,
  `report`, `modeljson` shape what the owner sees, not what a user
  receives or whether a check passes.
- **Proposed pass-9 footgun** (an owner edit to `REVIEW-POLICY.md`): "A
  per-call record built by wrapping `Tool.run` misses calls the agent
  rejects before `run` (unknown tool names); the Tracer's `tool()` callback
  is the complete list."
- **Note — `main` moved:** §11 (75f9ecc, 5fade27) changed `run.py`,
  `tests/test_evals_run.py` and `README.md`. `git merge-tree` conflicts in
  `tests/test_evals_run.py` only (both branches append tests after
  `test_the_suite_does_not_write_outside_the_report_dir`; keep both).
  `run.py` and `README.md` auto-merge, with no semantic interplay (§11
  picks provider and model; §9 adds per-case and report fields). A rebase
  needs the owner's word and a new review round.

**Mutants** (reviewer's harness outside the repo: byte-exact single
replacement, `git diff --quiet` non-zero, full `pytest -q -p
no:cacheprovider -x`, restore by copy in `finally`; `git status --short`
clean after each batch). 48 run:

| id | target | mutation | result | killed by |
| --- | --- | --- | --- | --- |
| C1 | conftest.py:27 | co_name condition → True | **SURVIVED** | – |
| C2 | conftest.py:28 | filename condition → True | **SURVIVED** | – |
| C3 | conftest.py:30 | address condition → True | **SURVIVED** | – |
| C4 | conftest.py:26 | allow every connect | KILLED | test_socket_connect_is_blocked |
| C5 | conftest.py:32 | exemption removed | KILLED | test_view_labels_default_to_evals_labels_by_report_stem |
| M1 | coverage.py:140 | exact `>=1`→`>=0` | KILLED | test_exact_match_threshold |
| M2 | coverage.py:142 | several `>=2`→`>2` | KILLED | test_several_matches_threshold |
| M3 | coverage.py:144 | no-match `==0`→`<=1` | KILLED | test_no_match_threshold |
| M4 | coverage.py:146 | budget `!=0`→`>1` | KILLED | test_budget_too_low_needs_zero_within_budget_and_some_without |
| M5 | coverage.py:148 | without-max `<1`→`<0` | KILLED | same |
| M6 | coverage.py:152 | no-keywords check removed | KILLED | test_spelling_differs_needs_a_match_and_keywords |
| M7 | coverage.py:158 | case-sensitive both sides | KILLED | test_spelling_differs_keyword_must_not_appear_verbatim |
| M8 | coverage.py:135 | in-stock check removed | KILLED | test_out_of_stock_needs_a_real_out_of_stock_product |
| M9 | coverage.py:39 | off-topic pairing one-way | KILLED | test_generate_writes_valid_cases_and_prints_the_summary |
| M10 | coverage.py:49 | global RNG | KILLED | test_generate_asks_for_the_seeded_cells_in_order_and_writes_cases |
| M11 | labels.py:81 | first line wins | KILLED | test_last_line_per_case_wins |
| M12 | labels.py:31 | whitespace critique for a fail | KILLED | test_a_fail_needs_a_critique_and_a_pass_does_not |
| M14 | labels.py:52 | timestamp not UTC | KILLED | test_the_timestamp_is_utc |
| V1 | view.py:157 | persona filter ignored | KILLED | test_each_dimension_filter_alone |
| V2 | view.py:165 | status filter ignored | KILLED | test_label_and_status_filters_alone |
| V3 | view.py:162 | label filter can't tell pass from fail | KILLED | test_label_and_status_filters_alone |
| V4 | view.py:285 | previous goes to first | KILLED | test_without_a_filter_next_and_previous_walk_every_conversation |
| V5 | view.py:286 | next/previous ignore filter | KILLED | test_each_dimension_filter_alone |
| V6 | view.py:463 | Enter with no label saves a pass | KILLED | test_a_refused_fail_keeps_the_typed_critique_in_the_box |
| V7 | view.py:480 | `p` also moves on | KILLED | test_pass_saves_without_a_critique_as_a_full_line |
| V8 | view.py:479 | in-memory labels not updated | KILLED | same |
| V9 | view.py:490 | `serve` any host | KILLED | test_serve_binds_to_loopback_only |
| V10 | view.py:370 | critique not shown | KILLED | test_a_refused_fail_keeps_the_typed_critique_in_the_box |
| V11 | view.py:177 | stock always in stock | KILLED | test_one_conversation_shows_every_part |
| V12 | view.py:208 | all calls under turn 1 | **SURVIVED** | – (HIGH) |
| V13 | view.py:240 | guardrail always allowed | **SURVIVED** | – (MEDIUM) |
| V14 | view.py:290 | pass count `!= "fail"` | equivalent | – |
| V15 | view.py:476 | labels opened `"w"` | KILLED | test_enter_saves_the_pending_label_and_moves_to_the_next_conversation |
| R1 | run.py:88 | error flag stays True | KILLED | test_the_report_keeps_turns_tools_with_results_and_guardrails |
| R2 | run.py:55 | guardrail allowed always True | KILLED | test_recording_tracer_keeps_searches_turns_and_guardrails |
| R3 | run.py:223 | hash of empty bytes | KILLED | test_prompt_sha256_is_the_hash_of_the_shipped_system_prompt |
| R4 | run.py:58 | turn text dropped | KILLED | test_the_report_keeps_turns_tools_with_results_and_guardrails |
| K1 | counts.py:66 | ERROR in agreement cells | KILLED | test_each_agreement_cell_has_its_own_case |
| K2 | counts.py:50 | modes ascending | KILLED | test_modes_are_counted_and_sorted_descending |
| K3 | counts.py:108 | dimension cell ignores value | KILLED | test_the_per_dimension_tables_have_a_cell_per_mode_and_value |
| K4 | counts.py:72 | both-fail reworded | equivalent | – |
| T1 | taxonomy.py:91 | whitespace mode id | KILLED | test_an_empty_mode_id_is_an_error |
| T2 | taxonomy.py:107 | mapped non-fail | KILLED | test_an_invalid_draft_writes_nothing_and_exits_1[text3] |
| T3 | taxonomy.py:102 | unknown mode | KILLED | test_an_invalid_draft_writes_nothing_and_exits_1[text2] |
| T4 | taxonomy.py:59 | `labels_ref` ignored | KILLED | test_taxonomy_writes_the_draft_and_sends_the_critiques |
| A1 | analysis.py:238 | labels-file check off | KILLED | test_counts_checks_that_the_taxonomy_names_this_labels_file |
| A2 | analysis.py:149 | overwrite without `--force` | KILLED | test_generate_refuses_to_overwrite_without_force |
| A3 | analysis.py:147 | `--count 0` allowed | KILLED | test_generate_bad_arguments_and_config_exit_2 |
| G1 | generate.py:134 | first unreachable swallowed | KILLED | test_generate_model_unreachable_exits_1_and_writes_nothing |
| G2 | generate.py:134 | later unreachable raises | KILLED | test_the_first_unreachable_call_raises_but_a_later_one_is_a_drop |
| G3 | generate.py:145 | no cap per cell | KILLED | test_missing_candidates_and_extra_candidates |
| G4 | generate.py:152 | duplicates kept | KILLED | test_a_repeated_question_is_dropped |
| G5 | generate.py:178 | off-topic loses `must_decline` | KILLED | test_generate_writes_valid_cases_and_prints_the_summary |
| D1 | cases.py:99 | extra dimension key | KILLED | test_bad_dimensions_name_line_case_and_field[dims0] |
| D2 | cases.py:109 | whitespace persona | KILLED | test_bad_dimensions_name_line_case_and_field[dims4] |

Survived: V12, V13 (`view.py:208`, `:240`), C1, C2, C3
(`tests/conftest.py:27-30`); the rework is expected to kill all five, and
the HIGH's new `test_evals_run.py` test must fail on today's `run.py:71-91`.

## Not checked
- **Live model behaviour (AC9):** what `qwen3:8b` generates, how many
  candidates survive coverage, whether no-match questions read naturally;
  the taxonomy draft's quality and whether qwen's output parses beyond the
  scripted cases.
- **The hotkeys in a real browser:** the inline script is only
  string-checked; `p`/`f`/`Enter`/`j`/`k`, the critique focus, and
  "closing the browser loses nothing" are the live check's.
- **B9's "visible without scrolling sideways":** the CSS looks right; not
  rendered.
- **Package release dates:** `python-fasthtml 0.14.14` (2026-10-20, the
  implementer's date) and the 16 transitive versions (e.g. `starlette
  1.10.0`, `tzdata 2026.6`) not checked against PyPI. A `[tool.uv]
  exclude-newer` would enforce the two-week rule; the owner's choice.
- **`uvicorn.run` serving for real:** replaced in every test.
- **The rebase onto `main`:** not run (see the Note).

## Live check
- owed: rule 3 (AC9; the Not-checked items above are runtime behaviour
  only a live run shows). Rule 1 does not apply.
- **When:** after the rework and the rebase onto `main` (so `advisor-eval
  --provider` exists). Ollama running with `qwen3:8b` pulled. Windows
  PowerShell, in the worktree.
- steps:
  1. `cd C:\Users\eric\src\product-advice-agent-wt\9-error-analysis`;
     `$env:ADVISOR_MODEL_PROVIDER = "ollama"; $env:ADVISOR_MODEL =
     "qwen3:8b"`.
  2. `uv run advisor-analysis generate` — about 30 model calls, then per
     scenario `<scenario>: asked N, kept K, dropped D (…)`, ending `wrote K
     questions to evals\generated.jsonl`; exit 0. Note scenarios with most
     questions dropped, and the reasons.
  3. `notepad evals\generated.jsonl` — each line: `id` `gen-<scenario>-<n>`,
     `dimensions` with three keys, `note` with `probe: {…}`, off-topic
     lines `"must_decline": true`. Spot-check two `no-match` questions (run
     one with `uv run advisor "<question>"`: nothing should be found) and a
     `spelling-differs` one (its probe keywords not in the question).
     Delete or reword anything unnatural; save.
  4. `uv run advisor-eval --cases evals\generated.jsonl` — a line per
     case and a report path; open the report: each case has `dimensions`,
     `turns`, `tools` (with `results`), `guardrails`; the report has
     `prompt_sha256`.
  5. `uv run advisor-analysis view evals\runs\<stamp>.json` — prints
     `serving http://127.0.0.1:5209 …`; open it. `http://<your LAN
     IP>:5209` must **not** answer. One screen shows question, dimensions,
     status and checks, each model turn with its tool calls, arguments and
     products, the answer, the guardrails, and `1 / N  labelled 0, pass 0,
     fail 0`, with no sideways scroll. An unknown-tool call shows as an
     error under its own turn.
  6. Label at least 20 with the keyboard: `p` saves a pass (stays; `j`
     moves on); `f` focuses the critique, `Enter` saves the fail and moves
     on; `k` goes back; `f` then `Enter` with an empty box is refused ("A
     fail needs a critique."). Use the filters; `j`/`k` stay inside them.
     Ctrl+C, run `view` again: labels and counts are still there.
     `Get-Content evals\labels\<stamp>.jsonl`: one line per change with
     `case_id, label, critique, labelled_at` (UTC, `Z`), `question`,
     `answer`. Judge whether a conversation takes a few seconds.
  7. `uv run advisor-analysis taxonomy evals\labels\<stamp>.jsonl` —
     `wrote K failure modes to evals\taxonomy.draft.json; …`. On "Draft
     rejected: …" (exit 1), note why and rerun.
  8. Edit `evals\taxonomy.draft.json` (rename or merge modes; every failed
     case maps to a mode; keep `"labels"`), save as `evals\taxonomy.json`.
  9. `uv run advisor-analysis counts evals\runs\<stamp>.json --out
     $env:TEMP\counts.md` — four tables: fails per mode (highest first);
     per mode by feature, scenario, persona; the agreement table (both
     pass, both fail, owner fail / status PASS with ids, owner pass /
     status FAIL with ids, ERROR, unlabelled). Check them against your
     labels. Change one mapping to an unknown mode: `Taxonomy error: …`,
     exit 2; undo it.
  10. `git status`: only `evals/generated.jsonl`, `evals/labels/*.jsonl`,
      `evals/taxonomy.json` new; no `.sesskey`, no
      `evals/taxonomy.draft.json`.
- you should see: each command exits 0 on the happy path, the viewer
  answers only on 127.0.0.1, labels survive a restart, and the counts match
  your labels.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/9-error-analysis` at 35f2762; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `pass 255, fail
  0`; ruff "All checks passed!"; "111 files already formatted"; mypy
  "Success: no issues found in 26 source files"; pytest "464 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0, "31
  file(s), 4120 line(s)". Matches.
- **Coordinator, re-run:** the five survivors with my own harness (backup
  by copy, one replacement, file-changed assertion, full pytest, restore
  by copy): V12 (`mine, tools = tools, []`), V13 (`'allowed'` always), C1
  (co_name condition → True), C2 (filename condition → True), C3 (address
  condition → True): each SURVIVED, 464 passed. Matches.
- **Coordinator, read:** `git ls-files .sesskey` lists it;
  `tests/conftest.py:20-33` and `view.py:204-213`, `:238-242` as quoted.

**Reviewer, verified** (worktree at 35f2762, read-only):
- `npm run verify` exit 0 (464 passed, 26 source files); `check:intent`
  PASS; `sdlc:scan` sampling as above.
- `uv lock --check --offline` "Resolved 66 packages", exit 0; the
  `uv.lock` diff adds 17 packages and moves nothing (`httpx`, `anthropic`,
  `langfuse` unmoved).
- "281 before" reproduced by collecting tests from `git archive c806886`.
- AC4: `git diff main...HEAD -- tests/test_evals_*.py` changes only two
  import lines; §8's test bodies are unedited.
- HTML escaping: `<script>` in question, answer, persona, check reason,
  turn text, tool arguments, product id and name, guardrail reason, and a
  `</textarea>` critique → 0 raw, 12 escaped; only `_CSS` and `_SCRIPT` are
  raw constants.
- Label path: `labels_path_for` uses `report.stem` under `evals/labels/`.
- Viewer POST probe (422 / 303 / 200, as in the LOW); `.sesskey` written
  in a scratch directory by `get_key`; the unknown-tool reproduction.
- 48 mutants as tabled; `git status --short` empty after each batch;
  `main` unchanged at 5fade27.
- The overlap with §11 from `git merge-tree --write-tree --name-only main
  HEAD`.
- No `noqa`, `type: ignore` or `pragma` added in `src/`; `mypy --strict
  src/advisor/evals/view.py` passes.

**Taken on trust:**
- `python-fasthtml 0.14.14`'s release date (2026-10-20) and that 0.14.22
  is a day old; the transitive packages' dates;
- that `httpx2` is already in the environment through another dependency
  (it is not in the lock diff).
