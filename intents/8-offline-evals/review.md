<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §8 review — An offline eval suite that scores the advisor's answers against a fixed question set

verdict: escalate
tier: reviewed
reviewed-commit: ee5c24329f69d6ede30b37c1e2d554e5f88adda4
round: 5
sampled: no
run: manual
live-check: owed

Tier: Reviewed. Input 1 sets it (the branch as a whole changes
`scripts/intent-check-lib.mjs`, the kit's enforcement), and `review_tier:
reviewed` agrees. This round's findings do not raise it.

Scope: 76fd919..ee5c243: 2e8f827 (`live_checked` recorded), 365b0da (round
4's review), 7f22550 (the rework) and ee5c243 (Progress entry). Outside
`intents/`, only `tests/test_evals_score.py` (+24) and `README.md` (+2 −1)
changed; `git diff --stat 76fd919..HEAD -- src/ scripts/ infra/ .claude/
CLAUDE.md pyproject.toml uv.lock` is empty, so **nothing under `src/`
changed**. Inside `intents/`: an appended Progress entry and the
`live_checked` line only.

Both round-4 rework findings are closed: R5, R6, R7 and R9 are killed, and
so are 12 more variants; the `stock` and `prices` assertions in the new
tests each carry weight on their own. Two truncations of the phrase survive
(R12, R13): LOW, Worth a look. No finding needs rework, and the tier is
Reviewed, so the verdict is escalate: the owner reads the diff. The live
check is recorded and stands (the scorer is unchanged since the owner's
run).

## Round-4 findings: resolution
| Round 4 | Finding | Resolution | Verified |
| --- | --- | --- | --- |
| MEDIUM | `score.py:57`: R5, R6, R7, R9 survive | `test_near_misses_of_out_of_stock_do_not_count` (3 params) and `test_out_of_stock_phrase_counts_mid_text` (`tests/test_evals_score.py:204-225`) | all four KILLED |
| LOW | `README.md:133-134`: prices bullet omits the exemption | the bullet now ends "; a cited out-of-stock product needs none when the answer says "out of stock"" | read; matches amended B5 |
| LOW | `score.py:111,116`: answer-wide flag; "not out of stock" counts | carried, no defect (spec wording) | probe at HEAD unchanged |
| LOW | `score.py:50`: "1 189", "1 799" | carried | probe at HEAD: both still pass `prices` |
| LOW | `plan.md` N4b/N4c labels | carried | — |
| LOW | `intent-check-lib.mjs:158` K5/K6 | carried (`scripts/` unchanged) | — |
| LOW | `intent-check-lib.mjs:144-147` header, `CLAUDE.md:169` | carried | — |
| LOW (round 1) | M19/M27 equivalent; a first-case abort writes no report | carried | — |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (tests and README only, as round 4 asked) |
| 2 | Type check | pass (PASS) |
| 3 | Behaviour against the spec | pass (code unchanged since round 4; the new tests encode B5's literal "contains 'out of stock'") |
| 4 | Tests prove the behaviour, not only pass | findings (1 LOW: R12, R13 survive on `score.py:57`) |
| 5 | Conventions | pass (real synthetic catalogue; no model or network) |
| 6 | Numbers in prose | pass ("281 passed (277 before)" = 277 + 3 params + 1; P-005 129.0 and P-004 159.0 as the catalogue says; R5/R6/R7/R9 claims reproduced) |
| 7 | Documentation | pass (README prices bullet matches amended B5) |
| 8 | Guardrails and hygiene | pass (ruff, format, mypy green; no dependency change; no secrets) |
| 9 | Repository-specific footguns | pass (list empty). Suggestion carried: "a substring match tested only with inputs that contain it, so loosening it survives" |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 8, feature)
  note:  15 file(s), 1181 line(s) changed outside intents/.
```
Exit 0.

## Findings
- **LOW** `src/advisor/evals/score.py:57` (`says_out_of_stock`) — two
  truncations of the phrase survive: R12 `"of stock"` ("short of stock"
  would count) and R13 `"out of s"` ("out of season" would count). The code
  at HEAD is right (both answers fail `stock` and `prices`); the tests
  don't pin it. Contrived loosenings, not plausible regressions. Worth a
  look: params "… (P-004) is short of stock." and "… is out of season."
  would kill them.
- **LOW** `src/advisor/evals/score.py:111,116` (carried) — the flag is
  answer-wide, "not out of stock" counts, "out-of-stock" does not (now
  pinned). Spec wording. Worth a look: accepting "out-of-stock" would be a
  spec amendment, the owner's call.
- **LOW** `src/advisor/evals/score.py:50` (carried) — "1 189" counts as
  189, "1 799" (P-008) as P-024's 799, against the docstring's "Never
  inside a longer number". Worth a look; the owner's call.
- **LOW** `intents/8-offline-evals/plan.md` (Progress, "Rework round 2";
  carried) — N4b/N4c labels differ from round 2's. Worth a look.
- **LOW** `scripts/intent-check-lib.mjs:158` (carried) — K5, K6 survive
  `test:kit`; practically equivalent. Worth a look.
- **LOW** `scripts/intent-check-lib.mjs:144-147`, `CLAUDE.md:169`
  (carried) — header comment omits evals; long `CLAUDE.md` line. Worth a
  look.
- **LOW** (round 1, carried) — M19, M27 equivalent; a first-case abort
  writes no report. Worth a look.
- **Note:** `main` is at da7d754 (5 behind, 25 ahead); main's side touches
  only `intents/9-*`, `10-*`, `11-*`. Not pushed.

**Mutants** (reviewer's harness outside the repo: backup by copy, target
count 1 asserted, one replacement, `git diff --quiet` non-zero, full
pytest, restore by copy in `finally` with a byte-identical check; `git
status --short` empty after each batch):

| id | target | change | result | killing test(s) |
| --- | --- | --- | --- | --- |
| R5 | `score.py:57` | `"out of"` | KILLED | near_misses[… out of budget.] |
| R6 | `score.py:57` | `"stock"` | KILLED | near_misses[… in stock.], near_misses[… out-of-stock.] |
| R7 | `score.py:57` | also `"out-of-stock"` | KILLED | near_misses[… out-of-stock.] |
| R9 | `score.py:57` | `endswith("out of stock.")` | KILLED | test_out_of_stock_phrase_counts_mid_text |
| R10 | `score.py:57` | `.lower()` dropped | KILLED | test_prices_out_of_stock_exemption_is_case_insensitive, test_stock |
| R11 | `score.py:57` | `startswith("out of stock")` | KILLED | mid_text, test_stock, 3 prices-exemption tests |
| R12 | `score.py:57` | `"of stock"` | **SURVIVED** | none |
| R13 | `score.py:57` | `"out of s"` | **SURVIVED** | none |
| R14 | `score.py:57` | `"out of stock."` | KILLED | mid_text |
| R15 | `score.py:57` | `re.search(r"out\W+of\W+stock")` | KILLED | near_misses[… out-of-stock.] |
| R16 | `score.py:57` | phrase after `.replace("-", " ")` | KILLED | near_misses[… out-of-stock.] |
| R17 | `score.py:57` | `"stock"` and not `"in stock"` | KILLED | near_misses[… out-of-stock.] |
| R18 | `score.py:57` | also `"budget"` | KILLED | near_misses[… out of budget.] |
| R21 | `score.py:57` | phrase and no `;` | KILLED | mid_text |
| R19 | `score.py:116` | prices exemption alone uses `"stock" in` | KILLED | near_misses[… in stock.], near_misses[… out-of-stock.] |
| R20 | `score.py:157` | stock check alone uses `"stock" in` | KILLED | near_misses[… in stock.], near_misses[… out-of-stock.] |
| R22 | `score.py:116` | prices exemption alone uses `endswith` | KILLED | mid_text |
| R23 | `score.py:157` | stock check alone uses `endswith` | KILLED | mid_text |

Survived: R12, R13 (LOW, Worth a look).

## Not checked
- **Real answers that write "out-of-stock" or other stock wording:** the
  owner's runs were not read for wording; the tests pin that
  "out-of-stock" does not count, so such an answer fails both checks.
- **`advisor-eval` against a real Ollama** by the reviewer or coordinator
  (the owner ran it; recorded).
- **Untested paths** (unchanged since round 1): `--debug` traceback
  output; the `--report-dir` write failure; `CatalogueError` → exit 2.
- **Mutants not re-run:** the round 1–4 series on `run.py`, `cases.py`,
  `price_mentioned`, `score.py:111/116` (M1–M4, R1–R4, R8) and the kit;
  unchanged since round 4, tests only grew.
- **`uv lock --check`:** not re-run; no dependency file changed.

## Live check
- owed: rule 3 (AC6). **Done and recorded:** `live_checked: 2026-11-11
  by-agent` (2e8f827, owner: "live check was ok"; run
  `evals/runs/20261111T095353Z-ollama.json`, 11/15, started 09:53:53Z,
  after 82f2b4d at 09:46:44Z).
- The recorded run stands: nothing under `src/` changed between 76fd919
  and ee5c243, so the scorer the owner ran is the scorer at HEAD.
- Steps, if it must be redone: as in round 4's `## Live check` (worktree;
  unset `ADVISOR_MODEL_PROVIDER`, `ADVISOR_MODEL`, `ADVISOR_OLLAMA_URL`;
  `uv run advisor-eval; echo "exit: $LASTEXITCODE"` with Ollama serving
  `qwen3:8b`; expect 15 case lines, `N/15 passed (ollama, qwen3:8b)`, a
  `report:` line and `PASS nc-headphones-under-200`; with Ollama stopped,
  only "cannot reach", exit 1, no report).

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/8-offline-evals` at ee5c243; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `pass 255, fail
  0`; ruff "All checks passed!"; "88 files already formatted"; mypy
  "Success: no issues found in 17 source files"; pytest "281 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0. Matches.
- **Coordinator, re-run:** six mutants with my own harness (backup by
  copy, one replacement, file-changed assertion, full pytest, restore by
  copy): R5 KILLED by near_misses[… out of budget.]; R6 KILLED (2 failed)
  by near_misses[… in stock.]; R7 KILLED by near_misses[… out-of-stock.];
  R9 KILLED by test_out_of_stock_phrase_counts_mid_text; R12 and R13
  SURVIVED (281 passed). Each matches the reviewer and, for R5–R9, the
  implementer.
- **Coordinator, read (round 4):** the owner's run's `started` 09:53:53Z
  is after 82f2b4d's 09:46:44Z.

**Reviewer, verified** (HEAD ee5c243):
- `git diff 76fd919..HEAD` read; the `src/` … `uv.lock` stat empty.
- `npm run verify` exit 0 (255 kit, 281 pytest); `npm run check:intent`
  PASS.
- `npm run sdlc:scan -- --sample-due manual --exclude 8` → "nth attested
  manual change = 1, every 5, sampled: no".
- The catalogue: P-004 Sonavo Quiet Pro 159.0, out of stock; P-005 Kestrel
  Air Plus 129.0, in stock.
- 18 mutants as tabled; `score.py` restored byte-identical; `git status
  --short` empty at the end.
- Five probe answers through HEAD's `score()` ("1 799", "1 189", the
  answer-wide flag, "out of season", "short of stock").
- `main...HEAD` = 5 / 25; not pushed. The reviewer stopped one stray
  `python` process of its own (a hung helper); it never touched the repo.

**Taken on trust:**
- the owner's live-check result ("live check was ok", 2e8f827);
- the round 1–4 mutant results for lines unchanged since round 4.

# Round 4 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: 76fd919b30b707246f103c3166ba6dd1b5b0e5cd
- round: 4
- sampled: no
- run: manual
- live-check: owed

Tier: Reviewed. Input 1 sets it (the branch changes
`scripts/intent-check-lib.mjs`, the kit's enforcement), and `review_tier:
reviewed` agrees. This round's findings do not raise it.

Round 4 is manual: `/auto` used its three rounds (`auto_stopped: out of
rounds, continues by hand`), and the owner typed `/review 8`.

Scope: 01a5eda..76fd919. Outside `intents/`, only `src/advisor/evals/score.py`
(+17 −3) and `tests/test_evals_score.py` (+27) changed, both in 82f2b4d.
Inside `intents/`: 28b47b8, the owner's B5 amendment ("a", after the live
check); 3fa6728 and the resume/stop commits (metadata); 76fd919, a Progress
entry below the marker (`plan.md` unchanged above it).

The code matches the amended B5 exactly, and extracting
`says_out_of_stock` leaves the stock check unchanged. The verdict is rework:
the tests do not pin the phrase itself, so four looser variants of
`says_out_of_stock` survive (R5, R6, R7, R9); for example "P-004 is in
stock" would count as flagged. The gap is as old as round 1, but the prices
check now goes through the same phrase. The fix is tests only, plus a
README line.

### Round-3 findings: resolution
| Round 3 | Finding | Resolution |
| --- | --- | --- |
| LOW | `plan.md` mutant labels N4b/N4c | carried (unchanged) |
| LOW | `score.py:50`: "1 189" counts as 189, "1 799" as P-024's 799 | carried; probe at HEAD gives the same |
| LOW | `intent-check-lib.mjs:158` K5/K6 | carried (`scripts/` unchanged since 01a5eda) |
| LOW | `intent-check-lib.mjs:144-147` header, `CLAUDE.md:169` | carried (unchanged) |
| LOW (round 1) | M19/M27 equivalent; a first-case abort writes no report | carried |
| Live check (AC6) | owner's first run: 9/15; nc-headphones-under-200 and voice-speaker failed `prices` on a flagged out-of-stock id | spec B5 amended (28b47b8); exemption built (82f2b4d); the owner's exact answer now passes `prices`. Owner's second run after 82f2b4d: 11/15, both pass (see Live check) |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (the exemption plus a shared `says_out_of_stock`; the Progress entry names both) |
| 2 | Type check | pass (at 76fd919, FAIL only on the then-owed live check; PASS at 2e8f827 once it was recorded) |
| 3 | Behaviour against the spec | pass (amended B5 met word for word; stock check unchanged, probed against 01a5eda) |
| 4 | Tests prove the behaviour, not only pass | findings (1 MEDIUM: R5, R6, R7, R9 survive on `score.py:57`) |
| 5 | Conventions | pass (pure module, no I/O, no model; CORE_CODE unchanged) |
| 6 | Numbers in prose | pass ("277 passed (273 before)" = 273 + 4 tests, reproduced; M1–M4 as stated in Progress, reproduced) |
| 7 | Documentation | findings (1 LOW: `README.md:133-134`) |
| 8 | Guardrails and hygiene | pass (ruff, format, mypy green; no dependency change; no secrets) |
| 9 | Repository-specific footguns | pass (list empty). Suggestion carried and sharpened: "a substring or regex match tested only with inputs that contain it, so loosening it survives" (N8 in round 2, R5/R6 now) |

### Type check
At the reviewed commit 76fd919 (the reviewer's run):
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 8, feature)
  error: A live check is owed and not recorded. Do the steps in intents/8-offline-evals/review.md → ## Live check, then set live_checked: <date> in intents/8-offline-evals/metadata.yml.
  note:  15 file(s), 1156 line(s) changed outside intents/.
```
At 2e8f827 (`live_checked` recorded on the owner's "live check was ok";
the coordinator's run):
```
type-check: PASS (intent 8, feature)
  note:  15 file(s), 1156 line(s) changed outside intents/.
```

### Pass 3 detail (amended B5)
- **Per id.** `score.py:111-118`: `flagged` is set once per answer; a cited
  id is exempt from `prices` only when `flagged and not
  by_id[i].in_stock`. An in-stock id is never exempt (M2 killed); an
  out-of-stock id needs the phrase (M4 killed).
- **"not out of stock"** counts as flagged ("P-004 is not out of stock."
  passes `stock` and `prices` at HEAD; at 01a5eda it passed `stock` and
  failed `prices`).
- **"out-of-stock"** (hyphen), "out\nof stock", two spaces and U+00A0 do
  not count, for either check, identically before and after.
- **Stock check unchanged:** the old inline `"out of stock" in
  answer.lower()` is the helper's body; 11 probe answers give identical
  `stock` verdicts and reasons at 01a5eda and HEAD.
- **The owner's live answer** fails `prices` at 01a5eda ("price of P-004
  not stated") and passes at HEAD; `stock` passes in both.
- **"1 799"**: unchanged ("P-008 costs 1 799 €. P-024 too." passes
  `prices`; so does "P-001 costs 1 189 €.").

### Findings
- **MEDIUM** `src/advisor/evals/score.py:57` (`says_out_of_stock`) — four
  variants of the phrase match survive the full suite: R6 (`"stock"`: "P-004
  is in stock" counts as flagged), R5 (`"out of"`: "out of budget" counts),
  R9 (phrase only at the end: every test answer ends in "out of stock."),
  R7 (also accepting "out-of-stock": no test pins B5's literal phrase).
  Before 82f2b4d these loosened only `stock`; now they loosen `prices` too.
  Needs rework: in `tests/test_evals_score.py`, add answers citing P-004
  without its price that must fail both `stock` and `prices`: "The Sonavo
  Quiet Pro (P-004) is in stock." (R6), "… is out of budget." (R5), "… is
  out-of-stock." (R7; B5's literal "contains 'out of stock'" decides it);
  and one passing answer with the phrase mid-text, e.g. "The Sonavo Quiet
  Pro (P-004) is out of stock; the Kestrel Air Plus (P-005) costs 129 €."
  (R9).
- **LOW** `README.md:133-134` — the **prices** bullet says "each cited
  product's price appears as a number" and omits the amended exemption, so
  a reader expects §7's case to fail on P-004. Needs rework: add "; a
  cited out-of-stock product needs none when the answer says 'out of
  stock'" (the amended B5 wording).
- **LOW** `src/advisor/evals/score.py:111,116` — the flag is answer-wide,
  as B5 says: one "out of stock" exempts every cited out-of-stock id ("P-004
  is out of stock. P-032 is a speaker." passes `prices` without P-032's 119
  €); "not out of stock" counts; "out-of-stock" does not. This is the
  spec's wording and the stock check's long-standing rule, so no defect.
  Worth a look: if `qwen3:8b` writes "out-of-stock", changing that is a spec
  amendment (the owner's).
- **LOW** `src/advisor/evals/score.py:50` (carried) — "1 189" counts as
  189, and "1 799" (P-008) as P-024's 799, against the docstring's "Never
  inside a longer number". Worth a look; a fix changes the rule below 1000,
  the owner's call.
- **LOW** `intents/8-offline-evals/plan.md` (Progress, "Rework round 2";
  carried) — N4b/N4c labels differ from round 2's. Worth a look.
- **LOW** `scripts/intent-check-lib.mjs:158` (carried) — K5, K6 survive
  `test:kit`; practically equivalent. Worth a look.
- **LOW** `scripts/intent-check-lib.mjs:144-147`, `CLAUDE.md:169`
  (carried) — the header comment doesn't mention evals; the `CLAUDE.md`
  line is long. Worth a look.
- **LOW** (round 1, carried) — M19, M27 equivalent; a first-case abort
  writes no report. Worth a look.
- **Note:** `main` moved to da7d754 (5 behind, 22 ahead); main's new
  commits touch only `intents/9-*`, `10-*`, `11-*`, so no overlap.

**Mutants** (reviewer's harness, outside the repo: backup by copy, one
byte replacement with count 1 asserted, `git diff --quiet` non-zero, full
pytest with the worktree venv, restore by copy in `finally`; `git status
--short` empty after):

| id | target | change | result | killing test(s) |
| --- | --- | --- | --- | --- |
| M1 | `score.py:116` | exemption line removed | KILLED (3) | test_prices_exempts_out_of_stock_cited_id_that_says_so, test_prices_in_stock_cited_id_still_needs_price_when_out_of_stock_said_elsewhere, test_prices_out_of_stock_exemption_is_case_insensitive |
| M2 | `score.py:116` | any id exempt | KILLED (1) | test_prices_in_stock_cited_id_still_needs_price_when_out_of_stock_said_elsewhere |
| M3 | `score.py:57` | `.lower()` dropped | KILLED (2) | test_prices_out_of_stock_exemption_is_case_insensitive, test_stock |
| M4 | `score.py:116` | phrase not required | KILLED (1) | test_prices_out_of_stock_without_saying_so_fails_naming_the_id |
| R1 | `score.py:116` | `flagged and in_stock` | KILLED (3) | test_prices_exempts_…, test_prices_in_stock_cited_…, test_prices_…_case_insensitive |
| R2 | `score.py:116` | `flagged or not in_stock` | KILLED (2) | test_prices_out_of_stock_without_saying_so_…, test_prices_in_stock_cited_… |
| R3 | `score.py:111` | `flagged = False` | KILLED (4) | test_stock, test_prices_exempts_…, test_prices_in_stock_cited_…, test_prices_…_case_insensitive |
| R4 | `score.py:111` | `flagged = True` | KILLED (2) | test_stock, test_prices_out_of_stock_without_saying_so_… |
| R5 | `score.py:57` | `"out of"` | **SURVIVED** | none |
| R6 | `score.py:57` | `"stock"` | **SURVIVED** | none |
| R7 | `score.py:57` | also `"out-of-stock"` | **SURVIVED** | none |
| R8 | `score.py:157` | case-sensitive phrase in the stock check | KILLED (1) | test_stock |
| R9 | `score.py:57` | `endswith("out of stock.")` | **SURVIVED** | none |

Survived: R5, R6, R7, R9, all on `score.py:57`; the MEDIUM rework is
expected to kill all four.

### Not checked
- **Real answers that write "out-of-stock" or other stock wording:** the
  owner's second run had none failing `prices`, but the answers were not
  read for the wording.
- **`advisor-eval` against a real Ollama** by the reviewer or coordinator
  (the owner ran it).
- **Untested paths** (unchanged since round 1): `--debug` traceback
  output; the `--report-dir` write failure; `CatalogueError` → exit 2.
- **Mutants not re-run:** the round 1–3 series on `run.py`, `cases.py`,
  `price_mentioned` and the kit; those files are unchanged since 01a5eda
  and the tests only grew.
- **`uv lock --check`:** not re-run; no dependency file changed.

### Live check
- owed: rule 3 (AC6), re-run because the scorer changed in 82f2b4d.
- **Done:** the owner ran it after 82f2b4d (report
  `evals/runs/20261111T095353Z-ollama.json`, started 09:53:53Z; 82f2b4d is
  09:46:44Z) and said "live check was ok"; recorded as `live_checked:
  2026-11-11 by-agent` in 2e8f827. That run: 11/15,
  `PASS nc-headphones-under-200`, `PASS voice-speaker`; the four FAILs
  (sport-earbuds, video-editing-laptop, tv-sound, out-of-stock-quiet-pro)
  are model behaviour, no `prices` failure.
- The MEDIUM and LOW rework touch tests and `README.md` only, so this run
  stands for the reworked branch unless the rework touches `score.py`.
- Steps, if it must be redone (Windows PowerShell, in the worktree):
  1. Start Ollama; `ollama list` shows `qwen3:8b`.
  2. `cd C:\Users\eric\src\product-advice-agent-wt\8-offline-evals` (no
     `.env`: `ollama`, `qwen3:8b`).
  3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL,
     Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue`
  4. `uv run advisor-eval; echo "exit: $LASTEXITCODE"`
  5. Open the newest `evals\runs\*.json`.
  6. Stop Ollama and run it again.
- You should see: 15 case lines, `N/15 passed (ollama, qwen3:8b)` and a
  `report:` line; `PASS nc-headphones-under-200` (a `prices` FAIL naming an
  out-of-stock id is a §8 defect only if the answer contains "out of
  stock"); after step 6 only the "cannot reach" message, exit 1, no report.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/8-offline-evals` at 2e8f827, which adds only `metadata.yml` to 76fd919; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `pass 255, fail
  0`; ruff "All checks passed!"; "88 files already formatted"; mypy
  "Success: no issues found in 17 source files"; pytest "277 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS. The reviewer's
  FAIL at 76fd919 was the owed live check only, since recorded (2e8f827);
  no other difference.
- **Coordinator, re-run:** the four survivors with my own harness (backup
  by copy, one replacement, file-changed assertion, full pytest, restore
  by copy): R5, R6, R7, R9 each SURVIVED, 277 passed. Matches.
- **Coordinator, read:** the owner's second report's `started`
  (09:53:53Z) is after 82f2b4d's commit time (09:46:44Z), so the recorded
  live check ran the amended scorer; and `README.md:133-134` as quoted.

**Reviewer, verified** (HEAD 76fd919, nothing checked out):
- `git diff --name-only 01a5eda HEAD`; the code, test, spec, plan and
  metadata diffs read; `git show 28b47b8 --stat` (`spec.md` only).
- `npm run verify` exit 0 (255 kit, 277 pytest); `npm run check:intent`
  FAIL, live check only.
- `npm run sdlc:scan -- --sample-due manual --exclude 8` → "nth attested
  manual change = 1, every 5, sampled: no".
- 11 probe answers through HEAD's and 01a5eda's `score.py` against the
  real catalogue (pass 3).
- 13 mutants as tabled; `git status --short` empty after.
- `main...HEAD` = 5 / 22, main's side `intents/9-*`, `10-*`, `11-*` only;
  nothing pushed, nothing touched `main`.

**Taken on trust:**
- the owner's live-check results and their "a" choice (28b47b8);
- the round 1–3 mutant results for files unchanged since 01a5eda;
- that `qwen3:8b` wrote the answer quoted from the first run (the
  reviewer probed that exact text).

# Round 3 (history)

- verdict: escalate
- tier: reviewed
- reviewed-commit: 01a5eda9b5b1f3a88b197ea98037ae2e4c35f761
- round: 3
- sampled: no
- run: auto
- live-check: owed

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

### Round-2 findings: resolution
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

### Passes
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

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 8, feature)
  error: A live check is owed and not recorded. Do the steps in intents/8-offline-evals/review.md → ## Live check, then set live_checked: <date> in intents/8-offline-evals/metadata.yml.
  note:  15 file(s), 1115 line(s) changed outside intents/.
```
The only error is the owed live check (rule 3, AC6): the owner's to clear.

### Findings
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

### Not checked
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

### Live check
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

### Verified myself vs. taken on trust

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
