<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §8 review — An offline eval suite that scores the advisor's answers against a fixed question set

verdict: rework
tier: reviewed
reviewed-commit: 6a534f60c5bcf187fa2d8c77a3356e8d6bd24c24
round: 1
sampled: no
run: auto
live-check: owed

**Tier:**
- **Input 1 (paths):** Attested. `src/advisor/evals/**` is `src/**`, plus
  tests, build config (`[project.scripts]`), and README/`CLAUDE.md`.
- **Input 2:** `review_tier` is empty.
- **The "by meaning" row doesn't apply:** `advisor-eval` prints to the
  developer and writes a local gitignored file, and its only traffic is to
  the configured model through `make_client`.
- **Input 3 raises it to Reviewed:** the two HIGH findings below are
  behaviour the tests don't prove.
- **Separately,** the owner has decided that `evals/cases.py` and
  `evals/score.py` join `CORE_CODE`. That edits
  `scripts/intent-check-lib.mjs`, the kit's enforcement, which is
  Reviewed by path.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (only the plan's files; `agent.py`, `catalogue.py`, `guardrails.py`, `prompts/`, `tracing.py`, `cli.py`, `models/`, `config.py`, data unchanged; `uv.lock` unchanged) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (2) |
| 4 | Tests prove the behaviour, not only pass | findings (7) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass ("186 before; +55" reproduced) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; suggestion below) |

**Pass 3, confirmed in code:**
- **B1/B2:** unknown fields and ids, decline cases with expected ids, and
  unknown constraints are all rejected, naming the line, case and field;
  exit 2.
- **B3:** coverage met.
- **B4:** `(?<![A-Za-z0-9])P-\d{3}(?!\d)`.
- **B5:** all seven checks, each applied only when it applies.
- **B6:** pure.
- **B7:** env, settings, key and Ollama URL handled as `cli.py` does, then
  one `make_client`.
- **B8:** exit 0/1/2; `ModelError` → ERROR; the first-case abort is limited
  to unreachable or not-available (`run.py:162-168`).
- **B9:** `_norm` (`score.py:59-60`).
- **B10:** the fields and file name were seen in a run.
- **B11:** no `advisor.tracing` import.
- The 15 cases match the plan's table field for field.

**The implementer's stated divergences:**
- **(a)** an `err` stream: fine.
- **(b)** config errors exit 2: the approved plan says 2.
- **(c)** non-`ModelError` → ERROR and continue: reasonable, but untested
  (M34 below).
- **(d)** an aborted run writes no report: the spec is silent; tested.
  Worth a look.
- **(e)** `CORE_CODE`: decided by the owner (see Tier).

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 8, feature)
  note:  13 file(s), 978 line(s) changed outside intents/.
```

## Findings
- **HIGH** `tests/test_evals_score.py` (`test_search_max_price_category_and_keywords`),
  target `src/advisor/evals/score.py:59-60` — AC2 requires proof with a
  hyphenated keyword for `keywords_any`, but `["noise"]` against
  `["noise-cancelling"]` matches by plain substring. So removing `_norm`
  on either side survives (M14, M14b). Needs rework: assertions whose
  outcome depends on `_norm`, e.g. `keywords_any ["noise cancelling"]`
  matches `keywords ["Noise-Cancelling"]`, and `["noise"]` matches
  `["NOISE"]`.
- **HIGH** `tests/test_evals_run.py`, target `src/advisor/evals/run.py:169-172`
  — B8 aborts only on `ModelUnreachableError`/`ModelNotAvailableError`.
  No test puts a plain `ModelError` first, so widening the abort survives
  (M13). Needs rework: the script's first entry is `ModelError("boom")`;
  expect `ERROR hp: boom`, the later cases run, exit 1, and a report
  written.
- **MEDIUM** `tests/test_evals_run.py`, target `run.py:170-174` — an
  unexpected exception becomes `ERROR <id>: unexpected <Type>` and the run
  continues. Making it re-raise, which gives a traceback and breaks B8,
  survives (M34). Needs rework: `RuntimeError("x")` on the second case;
  expect `ERROR lap: unexpected RuntimeError`, the third case runs, exit 1,
  and no traceback in `err`.
- **MEDIUM** `tests/test_evals_run.py:156`, targets `run.py:183` and `:190` —
  `cases_sha256` is checked only by length (M32: hashing `b""` survives),
  and `failed` is only ever asserted as 0 (M38: hard-coding it survives).
  Needs rework: assert `cases_sha256 ==
  hashlib.sha256(cases_path.read_bytes()).hexdigest()`, and `totals ==
  {"total": 3, "passed": 2, "failed": 1, "errors": 0}` in the failing-case
  test.
- **MEDIUM** `tests/test_evals_run.py:156`, target `run.py:228` — the clock
  is constant, so `duration_s == 0` holds even when the duration is never
  computed (M43). Needs rework: an advancing clock, and a non-zero
  `duration_s`.
- **MEDIUM** `tests/test_evals_cases.py:57` (bad-file parametrize), targets
  `cases.py:59` (category), `:63` (`in_stock_only` type), `:65-68`
  (`keywords_any`) and `:104` (`must_decline` type). Each validation can be
  removed with the suite green (M23, M24, M25, M42). Needs rework: one row
  each: `expect_search={"category": "toaster"}`, `{"in_stock_only":
  "yes"}`, `{"keywords_any": []}` and `must_decline="yes"`, each expecting
  `case 'c1'` and the field name.
- **MEDIUM** `src/advisor/evals/score.py:31-36` (`price_mentioned`), with
  case `video-editing-laptop`. Spec B5 accepts a whole price only as
  "1799", "1799.00" or "1799,00". The scripted answer "The Norvik Forge 16
  (P-008) costs EUR 1,799." scored `prices` FAIL. Five products cost
  1000 € or more (P-008, P-010, P-011, P-017; P-014 at 999 is at the
  edge), and `video-editing-laptop` expects P-008. A real model writing
  "€1,799" or "1.799 €" would get a FAIL the owner would disagree with,
  which AC6 counts as a §8 defect. The code follows the spec. **Needs
  decision:** either accept thousands separators ("1,799", "1.799", "1
  799") for prices of 1000 or more, or keep B5 and let the live check show
  what `qwen3:8b` writes.
- **LOW** `src/advisor/evals/run.py:55` — `RecordingTracer.tool` filters on
  `name == "search_products"`. Recording every tool survives (M27), but
  only one tool exists, so they are equivalent today. Calls the tool
  rejected (`error=True`) are recorded and can satisfy `expect_search`;
  the spec is silent. Worth a look.
- **LOW** `src/advisor/evals/score.py:117` — M19, equivalent:
  `REFUSAL_TEXT` holds no id, so "cites no id" already passes it. Worth a
  look.
- **LOW** `src/advisor/evals/run.py:162-168` — a first-case abort writes no
  report (divergence (d)). Worth a look.
- **Owner decision, to apply in the rework:** `evals/cases.py` and
  `evals/score.py` join `CORE_CODE` (`scripts/intent-check-lib.mjs:154`,
  with its kit test). This amends the plan, which kept `scripts/` out of
  scope; the amendment is recorded in `plan.md` with the owner's words.
- **Pass 9 suggestion:** "a test pair whose inputs make the code under test
  irrelevant (`noise` ⊂ `noise-cancelling` without normalisation)": §1's
  class again. An owner edit to `REVIEW-POLICY.md`.

**Mutants, from the reviewer's harness** (`…/scratchpad/mut8r/mut.py`, 44
mutants; backup by copy, one match, `git diff --quiet` non-zero, full
pytest, restore by copy):
- **The plan's six, all killed:** M1 (price regex), M2 (`cited_ids`
  boundaries), M3 (stock check), M4a/M4b (`max_price`), M5 (exit 0), M6
  (ERROR as pass).
- **Also killed:** M7 (declines), M8 (forbidden inverted), M9 (expected
  subset), M10 (unknown field), M11 (report not written), M12 (`--only`
  ignored), M15–M18, M20–M22, M26, M28–M31, M33, M35–M37, M39–M41, M44.
- **Survived:**
  - M13 `run.py:169`, abort on a first-case plain `ModelError`;
  - M14 `score.py:59` and M14b `score.py:60`, `_norm` removed;
  - M23 `cases.py:59`, category validation removed;
  - M24 `cases.py:63`, `in_stock_only` type check removed;
  - M25 `cases.py:65`, `keywords_any` validation removed;
  - M32 `run.py:183`, sha256 of `b""`;
  - M34 `run.py:174`, re-raise instead of ERROR;
  - M38 `run.py:190`, `failed` hard-coded to 0;
  - M42 `cases.py:104`, `must_decline` type check removed;
  - M43 `run.py:228`, `duration_s` hard-coded to 0;
  - M27 `run.py:55` and M19 `score.py:117`: equivalent; no rework.

## Not checked
- **Real model output and the scorer's verdicts on it** (AC6): price
  formats above 1000 €; whether `qwen3:8b` cites ids in the `(P-001)` form;
  the stock wording in `voice-speaker` and `out-of-stock-quiet-pro`.
- **`advisor-eval` against a real Ollama:** no network was used.
- **`--debug` traceback output:** not tested or run.
- **The `--report-dir` write-failure path** (`run.py:196`) and the
  `CatalogueError` → exit 2 path (`run.py:110`): untested, not mutated.

## Live check
- owed: rule 3 (real model output and the scorer's verdicts on it; AC6).
  Run it after the rework.
- steps (Windows PowerShell, in the worktree, before the merge):
  1. Start Ollama. `ollama list` must show `qwen3:8b`; otherwise run
     `ollama pull qwen3:8b`.
  2. `cd C:\Users\eric\src\product-advice-agent-wt\8-offline-evals`. The
     worktree and its parent folders have no `.env`, so the defaults apply
     (`ollama`, `qwen3:8b`). No key is needed, and evals don't trace.
  3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL,
     Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue`
  4. `uv run advisor-eval; echo "exit: $LASTEXITCODE"`. It takes several
     minutes on CPU.
  5. `Get-ChildItem evals\runs`; open the newest `.json`.
- you should see:
  - 15 lines of `PASS`/`FAIL`/`ERROR <id>…`, then `N/15 passed (ollama,
    qwen3:8b)` and `report: evals\runs\<YYYYMMDDTHHMMSSZ>-ollama.json`;
    exit 0 if all pass, else 1;
  - `PASS nc-headphones-under-200` (§7 is on this branch);
  - `git status --short` shows nothing new;
  - read 2–3 answers, including `video-editing-laptop` (P-008, 1799 €;
    watch for "1,799"), `off-topic-poem` and an out-of-stock case. A
    verdict you disagree with is a §8 defect (AC6); other FAILs are
    findings for later intents;
  - with Ollama off: only the "cannot reach" message, exit 1, and no
    report.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/8-offline-evals` at 6a534f6, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "87 files already formatted";
  mypy "Success: no issues found in 17 source files"; pytest "241 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS. Matches.
- **Coordinator, re-run:** all 13 listed survivors, from the reviewer's
  `muts.txt` definitions, with my own harness (backup by copy, one
  replacement, file-changed assertion, full pytest, restore by copy).
  M13, M14, M14b, M23, M24, M25, M32, M34, M38, M42, M43, M27 and M19 each
  SURVIVED ("241 passed"). Matches the reviewer on all 13.

**Reviewer, verified:**
- `uv lock --check` exit 0, and `uv.lock` not in the diff.
- `sdlc:scan --sample-due auto --exclude 8` → "nth attested auto change =
  4, every 3, sampled: no".
- `main` collects 186 tests.
- `advisor-eval --help` and `--bogus` (exit 2).
- An end-to-end scratch run with `ScriptedModelClient` on three real
  cases:
  - the factory was called with `ollama qwen3:8b None
    http://localhost:11434`;
  - output `PASS nc-headphones-under-200`, `FAIL video-editing-laptop`
    (price "1,799", no laptop search), `FAIL off-topic-weather`, `1/3
    passed`, exit 1;
  - the report had the B10 keys;
  - a first-case unreachable gave exit 1, the message on stderr, and no
    report.
- 44 mutants, as above.
- No secrets; model text reaches only `json.dumps` and stdout.

**Taken on trust:** that `ScriptedModelClient` behaves like a real adapter
at the `ModelClient` boundary.
