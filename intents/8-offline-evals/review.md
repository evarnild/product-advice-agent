<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §8 review — An offline eval suite that scores the advisor's answers against a fixed question set

verdict: escalate
tier: reviewed
reviewed-commit: 01a5eda9b5b1f3a88b197ea98037ae2e4c35f761
round: 3
sampled: no
run: auto
live-check: owed

Tier: Reviewed. It is set by input 1 (the branch changes
`scripts/intent-check-lib.mjs`, the kit's enforcement), and `review_tier:
reviewed` agrees.

Scope: 6e7d305..01a5eda — 278aea1 (round-2 review), bd32a14 (rework),
01a5eda (`auto_round: 3`). `git diff --stat 6e7d305 HEAD -- . ':!intents'`
shows only `tests/test_evals_score.py` (+34 −2); no source changed. Inside
`intents/`, the rework adds a "Rework round 2" entry below the Progress
marker.

The rework is tests only and closes every round-2 rework finding. N12, N8,
N1 and N4b are now killed, and so are N4c and N4d (each no-break space
removed on its own). No new finding needs rework. The tier is Reviewed, so
the verdict is escalate: the owner reads the diff, and the live check (AC6)
is still owed.

## Round-2 findings: resolution
| Round 2 | Finding | Resolution | Verified |
| --- | --- | --- | --- |
| HIGH | N12 (`score.py:48`): wrong later groups not rejected | "1,798", "1.800", "1 899" in `test_price_over_1000_rejects_other_numbers` (`tests/test_evals_score.py:60-79`) | N12 KILLED (3 failed) |
| MEDIUM | N8 (`score.py:19`): any separator accepted | "1-799", "1/799" in the rejects | N8 KILLED |
| MEDIUM | N1 (`score.py:42`): the 1000 boundary untested | `test_price_of_exactly_1000_takes_a_separator` (`:82-84`) | N1 KILLED |
| LOW | N4b (`score.py:19`): U+202F untested; an invisible U+00A0 literal | `"1\u00a0799"` and `"1\u202f799"` written as escapes; the only non-ASCII character left in the test file is `€` | N4b/N4c and N4d KILLED |
| LOW | a digit and a space before the price ("1 189" counts for 189; "1 799" for 799) | carried (the owner's call) | probe: still True for both |
| LOW | `CORE_CODE` anchors (K5, K6) | carried; practically equivalent | — |
| LOW | `CORE_CODE` header comment; `CLAUDE.md:169` long line | carried | — |
| LOW (round 1) | M27, M19 equivalent; a first-case abort writes no report | carried | — |
| Pass 9 suggestion | "test inputs make the code irrelevant" | open (an owner edit to `REVIEW-POLICY.md`) | — |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (tests only; no source, kit or docs change) |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear) |
| 3 | Behaviour against the spec | pass (amended B5 unchanged in code; tests match its wording) |
| 4 | Tests prove the behaviour, not only pass | pass (every round-2 survivor killed, plus N4c and N4d; sampled round-1 resolutions still killed) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1 LOW: mutant naming in `plan.md`); "273 passed (266 before)" reproduced: +5 rejects, +1 accept, +1 test |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (`uv lock --check` exit 0; no secrets) |
| 9 | Repository-specific footguns | pass (list empty; suggestion carried) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 8, feature)
  error: A live check is owed and not recorded. Do the steps in intents/8-offline-evals/review.md → ## Live check, then set live_checked: <date> in intents/8-offline-evals/metadata.yml.
  note:  15 file(s), 1115 line(s) changed outside intents/.
```
The only error is the owed live check (rule 3, AC6): the owner's to clear.

## Findings
- **LOW** `intents/8-offline-evals/plan.md` (Progress, "Rework round 2") —
  the plan calls "U+00A0 removed" N4b and "U+202F removed" N4c, while round
  2's review defines N4b as U+202F removed. All are killed; only the labels
  differ. Worth a look.
- **LOW** `src/advisor/evals/score.py:50` (carried) — a digit and a space
  before the price are not excluded: "1 189" counts as 189, and "1 799"
  (P-008) counts as P-024's 799. This contradicts the docstring's "Never
  inside a longer number". Worth a look in the live check. A fix changes
  the rule for prices below 1000, which is the owner's call.
- **LOW** `scripts/intent-check-lib.mjs:158` (carried) — K5 and K6 (the
  anchors) survive `test:kit`; practically equivalent. Worth a look.
- **LOW** `scripts/intent-check-lib.mjs:144-147`, `CLAUDE.md:169` (carried)
  — the header comment doesn't mention evals, and the `CLAUDE.md` line is
  long and unwrapped. Worth a look.
- **Note:** the branch is 3 commits behind `main`, in `intents/9-*` and
  `intents/10-*` only, so no overlap.

**Mutants** (reviewer's harness `…/scratchpad/mut8r3/mut.py`, ASCII source,
escapes written as text; backup by copy, one match, `git diff --quiet`
non-zero, full pytest, restore by copy in `finally`):

| id | target | change | result | killing test |
| --- | --- | --- | --- | --- |
| N12 | `score.py:48` | later groups `\d{3}` | KILLED (3) | test_price_over_1000_rejects_other_numbers[1,798], [1.800], [1 899] |
| N8 | `score.py:19` | `\D` separator | KILLED (2) | test_price_over_1000_rejects_other_numbers[1-799], [1/799] |
| N1 | `score.py:42` | `> 1000` | KILLED (1) | test_price_of_exactly_1000_takes_a_separator |
| N4b/N4c | `score.py:19` | U+202F removed | KILLED (1) | test_price_over_1000_accepts_thousands_separators[1\u202f799] |
| N4d | `score.py:19` | U+00A0 removed | KILLED (1) | test_price_over_1000_accepts_thousands_separators[1\xa0799] |
| M13 | `run.py` | abort on any `ModelError` | KILLED | test_a_model_error_on_the_first_case_does_not_abort |
| M14, M14b | `score.py` | `_norm` removed | KILLED | test_search_keywords_are_normalised_on_both_sides |
| M43 | `run.py` | `duration_s` 0 | KILLED | test_duration_is_measured_with_the_clock |

Survived: none. Equivalent, carried: N2, N9, M19, M27, and K5/K6
(practically).

## Not checked
- **Real model output and the scorer's verdicts on it** (AC6): the price
  format `qwen3:8b` writes for P-008; `(P-001)` citations; stock wording.
- **`advisor-eval` against a real Ollama.**
- **Untested paths** (unchanged since round 1): `--debug` traceback
  output; the `--report-dir` write failure; `CatalogueError` → exit 2.
- **Prices with cents at 1000 € or more in real answers:** unit-tested
  only.
- **Mutants not re-run this round:** the rest of the N- and K-series and
  the round-1 set. They were killed in round 2, the source and kit are
  unchanged, and added tests cannot revive them.

## Live check
- owed: rule 3 (AC6).
- steps (Windows PowerShell, in the worktree, before the merge):
  1. Start Ollama. `ollama list` must show `qwen3:8b`; otherwise run
     `ollama pull qwen3:8b`.
  2. `cd C:\Users\eric\src\product-advice-agent-wt\8-offline-evals`. There
     is no `.env` here or above, so the defaults apply (`ollama`,
     `qwen3:8b`). No key is needed, and evals don't trace.
  3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL,
     Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue`
  4. `uv run advisor-eval; echo "exit: $LASTEXITCODE"`. It takes several
     minutes on CPU.
  5. `Get-ChildItem evals\runs`; open the newest `.json`.
  6. Stop Ollama, then run `uv run advisor-eval` once more.
- you should see:
  - 15 lines of `PASS`/`FAIL`/`ERROR <id>…`, then `N/15 passed (ollama,
    qwen3:8b)` and `report: evals\runs\<YYYYMMDDTHHMMSSZ>-ollama.json`;
    exit 0 if all pass, else 1;
  - `PASS nc-headphones-under-200`;
  - `git status --short` shows nothing new;
  - read 2–3 answers, including `video-editing-laptop` (P-008, 1799 €).
    "1799", "1,799", "1.799", "1 799", with or without ".00"/",00", all
    count, so a `prices` FAIL there means the price is missing or wrong.
    Read `off-topic-poem` and an out-of-stock case too. A verdict you
    disagree with is a §8 defect (AC6); other FAILs are findings for later
    intents. Note any answer where "1 799" made P-024 (799 €) pass (the
    carried LOW);
  - after step 6, only the "cannot reach" message, exit 1, and no report.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/8-offline-evals` at 01a5eda, `git status --short` empty before and after):
- **Coordinator, re-run:** `git diff --name-only 6e7d305 HEAD -- .
  ':!intents'` → `tests/test_evals_score.py` only. Matches.
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "88 files already formatted";
  mypy "Success: no issues found in 17 source files"; pytest "273 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL with only the
  owed-live-check error. Matches.
- **Coordinator, re-run:** the four mutants the rework says it now kills,
  with my own harness (backup by copy, one replacement, file-changed
  assertion, full pytest, restore by copy):
  - N12 KILLED by test_evals_score::test_price_over_1000_rejects_other_numbers[1,798] (3 failed);
  - N8 KILLED by ::test_price_over_1000_rejects_other_numbers[1-799] (2 failed);
  - N1 KILLED by ::test_price_of_exactly_1000_takes_a_separator;
  - N4b KILLED by ::test_price_over_1000_accepts_thousands_separators[1\u202f799].

  Each matches the reviewer and the implementer.

**Reviewer, verified:**
- `uv lock --check` exit 0.
- `sdlc:scan --sample-due auto --exclude 8` → "nth attested auto change =
  4, every 3, sampled: no".
- The rework diff and the intent diffs read.
- A non-ASCII scan of the test file (only `€`).
- 10 mutants, as above.
- A `price_mentioned` probe at HEAD.
- Nothing touched `main`; nothing pushed.

**Taken on trust:**
- the owner's words as recorded in 14a9e8d;
- `ScriptedModelClient` at the `ModelClient` boundary;
- round 2's kills of the mutants not re-run.

# Round 2 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: 6e7d305bb5300d830bf2f78fc0dc2a555b3fc1ae
- round: 2
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed. It is set by input 1 (`scripts/intent-check-lib.mjs` is the
kit's enforcement), and input 2 (`review_tier: reviewed`) agrees.

Scope: 6a534f6..6e7d305:
- 6f724aa, 7263a8a: the round-1 review and stop;
- 14a9e8d: the owner's amendments to `spec.md` B5 and `plan.md` →
  "## Amendments";
- 630b551: the rework;
- 6e7d305: `auto_round: 2`.

The rework edits `plan.md` only below the Progress marker.

**Round 1 is resolved:** all 11 survivors are now killed, and the
`CORE_CODE` change matches the owner's amendment exactly. The new
thousands-separator code behaves as amended B5 says, but its reject tests
don't vary the parts the code computes. Four mutants on it survive. All the
fixes are tests: mechanical.

### Round-1 findings: resolution
| Round 1 | Finding | Resolution | Verified |
| --- | --- | --- | --- |
| HIGH | `_norm` unproven (M14, M14b) | `test_search_keywords_are_normalised_on_both_sides` (`tests/test_evals_score.py:126`) | M14, M14b killed |
| HIGH | a first-case plain `ModelError` must not abort (M13) | `test_a_model_error_on_the_first_case_does_not_abort` (`tests/test_evals_run.py:106`) | M13 killed |
| MEDIUM | an unexpected exception becomes ERROR, the run goes on (M34) | `test_an_unexpected_exception_is_an_error_and_the_run_goes_on` (`:115`) | killed |
| MEDIUM | `cases_sha256`, `failed` (M32, M38) | `test_a_failing_case_totals_and_case_file_hash_in_the_report` (`:123`) | killed |
| MEDIUM | `duration_s` (M43) | `test_duration_is_measured_with_the_clock` (`:132`) | killed |
| MEDIUM | four validations (M23, M24, M25, M42) | four rows in `test_bad_files_name_the_case_and_field` (`tests/test_evals_cases.py:70-79`) | killed |
| MEDIUM, Needs decision | thousands separators for prices ≥ 1000 | owner chose "a"; spec B5 amended; `price_mentioned` accepts them, with tests | behaviour correct; test gaps below |
| Owner decision | `cases.py`, `score.py` join `CORE_CODE` | done as amended: regex and comment (`scripts/intent-check-lib.mjs:157-158`), kit test (`scripts/intent-check-lib.test.mjs:394,397`), `CLAUDE.md:169` | K1–K4 killed by the kit test |
| LOW | M27, M19 (equivalent); a first-case abort writes no report | unchanged | — |
| Pass 9 suggestion | the "test inputs make the code irrelevant" class | open (an owner edit to `REVIEW-POLICY.md`); N12 and N8 are the same class again | — |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (only `score.py`, the eval tests, the `CORE_CODE` entry and its kit test, `CLAUDE.md`) |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear; no ROUTE, so the core change with tests is handled correctly) |
| 3 | Behaviour against the spec | pass (two LOW notes) |
| 4 | Tests prove the behaviour, not only pass | findings (4) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass ("266 … +25", "kit 255" reproduced) |
| 7 | Documentation | pass (one LOW) |
| 8 | Guardrails and hygiene | pass (no new dependency; `uv lock --check` exit 0) |
| 9 | Repository-specific footguns | pass (list empty; suggestion repeated) |

**Pass 3, amended B5** (`score.py:34-51`, plus a probe against the real
module):
- **Accepted for 1799:** "1,799", "1.799", "1 799", "1,799.00",
  "1.799,00".
- **Rejected:** "1,79", "11,799", "1,7990", "21 799".
- **Below 1000:** unchanged ("1,189" and "1.189" rejected for 189).
- **U+00A0 and U+202F:** both accepted. This is within the amendment's
  intent (a typeset "1 799"), but U+202F is untested.

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 8, feature)
  error: A live check is owed and not recorded. Do the steps in intents/8-offline-evals/review.md → ## Live check, then set live_checked: <date> in intents/8-offline-evals/metadata.yml.
  note:  15 file(s), 1083 line(s) changed outside intents/.
```
The only error is the owed live check (round 1, rule 3): the owner's to
clear.

### Findings
- **HIGH** `tests/test_evals_score.py:49`
  (`test_price_over_1000_rejects_other_numbers`), target
  `src/advisor/evals/score.py:48`. No test rejects a grouped number whose
  later groups are the wrong digits. N12 (later groups replaced by `\d{3}`)
  survives, so "1,800" or "1.000" would count as the price of a 1799 €
  product. AC2 requires "a price with the wrong number". Needs rework: add
  "1,798", "1.800" and "1 899" to the rejects for 1799.0.
- **MEDIUM** `tests/test_evals_score.py:49`, target `score.py:19`
  (`_GROUP_SEP`). No test rejects a separator outside the spec's list. N8
  (`_GROUP_SEP = "\D"`) survives, so "1-799" or "1/799" would count. Needs
  rework: add "1-799" and "1/799" to the rejects.
- **MEDIUM** `score.py:42` (`if whole >= 1000:`). The spec's boundary
  ("1000 or more") is untested: N1 (`> 1000`) survives. N2 (`if True:`) is
  equivalent. Needs rework: `assert price_mentioned("1,000", 1000.0)` and
  `assert price_mentioned("1.000,00", 1000.0)`.
- **LOW** `tests/test_evals_score.py:43`, target `score.py:19`. The accepts
  parametrize has a literal, invisible U+00A0 in `"1 799"`, which reads like
  a plain space. U+202F, which the code accepts, is untested: N4b (dropping
  `\u202f`) survives. Needs rework: write it `"1\u00a0799"` and add
  `"1\u202f799"`.
- **LOW** `score.py:50` — the lookbehinds exclude a digit, or a digit
  followed by `.` or `,`, before the price, but not a digit followed by a
  space. So "1 189" counts for 189, and "1 799" (P-008) also counts as
  P-024's 799 €. This follows the amendment ("below 1000 unchanged") but
  contradicts the docstring's "Never inside a longer number". Low risk
  with the current cases. Worth a look: watch for it in the live check. A
  fix changes the rule for prices below 1000, which is the owner's call.
- **LOW** `scripts/intent-check-lib.mjs:158` — dropping the new entry's `$`
  or `^` survives `npm run test:kit` (K5, K6). The existing entries'
  anchors are unpinned too, and paths are repo-relative, so this is
  practically equivalent. Worth a look.
- **LOW** documentation — the header comment above `CORE_CODE`
  (`scripts/intent-check-lib.mjs:144-147`) still lists only the agent loop,
  the search, the guardrails and the model interface (the inline comment
  covers evals); `CLAUDE.md:169` is a long unwrapped line. Worth a look.
- **Note:** the branch is 3 commits behind `main`, in `intents/9-*` and
  `intents/10-*` only, so no overlap.

**Mutants** (reviewer's harness `…/scratchpad/mut8r2/mut.py`; backup by copy,
one match, `git diff --quiet` non-zero, full pytest or `npm run test:kit`,
restore by copy):
- **Round-1 survivors, all KILLED:**
  - M13: test_a_model_error_on_the_first_case_does_not_abort;
  - M14, M14b: test_search_keywords_are_normalised_on_both_sides;
  - M23, M24, M25, M42: the `test_bad_files_name_the_case_and_field` rows;
  - M32, M38: test_a_failing_case_totals_and_case_file_hash_in_the_report;
  - M34: test_an_unexpected_exception_is_an_error_and_the_run_goes_on;
  - M43: test_duration_is_measured_with_the_clock.
- **New thousands-separator code, KILLED:** N3 (branch off), N4 (both
  no-break spaces removed), N5–N7 (space, dot or comma removed), N10–N11
  (groups of 2 or 4), N13–N14 (plain or grouped form dropped), N15–N17
  (cents), N18–N21 (lookbehinds and lookaheads).
- **Survived:**
  - N12 `score.py:48`: later groups `\d{3}`;
  - N8 `score.py:19`: `\D` separator;
  - N1 `score.py:42`: `> 1000`;
  - N4b `score.py:19`: `\u202f` removed.

  A rework is expected to kill all four.
- **Equivalent:** N2 (`if True:`), N9 (separator optional).
- **`CORE_CODE`:** K1 (`score` dropped), K2 (`cases` dropped), K3 (widened
  to all of `evals/`) and K4 (line removed) are KILLED by "narrowed
  CORE_CODE: wiring and I/O modules are not core, the model interface is".
  K5 and K6 (anchors) SURVIVED, practically equivalent.

### Not checked
- **Real model output and the scorer's verdicts on it** (AC6): which price
  format `qwen3:8b` writes for P-008; `(P-001)` citations; stock wording.
- **`advisor-eval` against a real Ollama.**
- **Untested paths** (unchanged since round 1, not mutated): `--debug`
  traceback output; the `--report-dir` write failure; `CatalogueError` →
  exit 2.
- **Prices with cents at 1000 € or more in real answers:** the catalogue
  has none; unit-tested only.

### Live check
- owed: rule 3 (AC6). Run it after the rework.
- steps (Windows PowerShell, in the worktree, before the merge):
  1. Start Ollama. `ollama list` must show `qwen3:8b`; otherwise run
     `ollama pull qwen3:8b`.
  2. `cd C:\Users\eric\src\product-advice-agent-wt\8-offline-evals`. There
     is no `.env` here or above, so the defaults apply (`ollama`,
     `qwen3:8b`). No key is needed, and evals don't trace.
  3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL,
     Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue`
  4. `uv run advisor-eval; echo "exit: $LASTEXITCODE"`. It takes several
     minutes on CPU.
  5. `Get-ChildItem evals\runs`; open the newest `.json`.
  6. Stop Ollama, then run `uv run advisor-eval` once more.
- you should see:
  - 15 lines of `PASS`/`FAIL`/`ERROR <id>…`, then `N/15 passed (ollama,
    qwen3:8b)` and `report: evals\runs\<YYYYMMDDTHHMMSSZ>-ollama.json`;
    exit 0 if all pass, else 1;
  - `PASS nc-headphones-under-200`;
  - `git status --short` shows nothing new;
  - read 2–3 answers, including `video-editing-laptop` (P-008, 1799 €):
    "1799", "1,799", "1.799", "1 799" and any of these followed by
    ".00"/",00" **now count**, so a `prices` FAIL there means the price is
    really missing or wrong. Read `off-topic-poem` and an out-of-stock case
    too. A verdict you disagree with is a §8 defect (AC6); other FAILs are
    findings for later intents;
  - after step 6, only the "cannot reach" message, exit 1, and no report.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/8-offline-evals` at 6e7d305, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "88 files already formatted";
  mypy "Success: no issues found in 17 source files"; pytest "266 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL with only the
  owed-live-check error. Matches.
- **Coordinator, re-run:** the four survivors with my own harness (backup
  by copy, one replacement, file-changed assertion, full pytest, restore by
  copy): N1, N4b, N8 and N12 each SURVIVED ("266 passed"). Matches.
  - My first attempt at N4b found no match, and nothing was changed: my
    harness file had saved `\u00a0` as the literal character. I fixed the
    harness and re-ran N4b, N8 and N12.
- **Coordinator, re-run:** sampled round-1 survivors, now killed:
  - M13 by test_evals_run::test_a_model_error_on_the_first_case_does_not_abort;
  - M14 by test_evals_score::test_search_keywords_are_normalised_on_both_sides;
  - M43 by test_evals_run::test_duration_is_measured_with_the_clock.

  Each matches the reviewer.

**Reviewer, verified:**
- `uv lock --check` exit 0.
- `sdlc:scan --sample-due auto --exclude 8` → "nth attested auto change =
  4, every 3, sampled: no".
- 33 Python mutants and 6 kit mutants, as above.
- A probe of `price_mentioned` (`…/mut8r2/edge.py`).
- The catalogue scan: ≥ 1000 € are P-008, P-010, P-011, P-017; P-024 is
  799.
- The diffs read; nothing touched `main`; nothing pushed.

**Taken on trust:**
- the owner's words as recorded in 14a9e8d;
- `ScriptedModelClient` at the `ModelClient` boundary.

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: 6a534f60c5bcf187fa2d8c77a3356e8d6bd24c24
- round: 1
- sampled: no
- run: auto
- live-check: owed

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

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 8, feature)
  note:  13 file(s), 978 line(s) changed outside intents/.
```

### Findings
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

### Not checked
- **Real model output and the scorer's verdicts on it** (AC6): price
  formats above 1000 €; whether `qwen3:8b` cites ids in the `(P-001)` form;
  the stock wording in `voice-speaker` and `out-of-stock-quiet-pro`.
- **`advisor-eval` against a real Ollama:** no network was used.
- **`--debug` traceback output:** not tested or run.
- **The `--report-dir` write-failure path** (`run.py:196`) and the
  `CatalogueError` → exit 2 path (`run.py:110`): untested, not mutated.

### Live check
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

### Verified myself vs. taken on trust

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
