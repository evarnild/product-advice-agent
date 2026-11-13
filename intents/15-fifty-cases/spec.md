<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §15 spec — A committed set of 50 real-looking eval questions with expected behaviour

Accepted intent: [intent.md](intent.md)

Written against `main` at `b1d7f06`. **Built after §14 merges**: the 50
cases are written against the 500-product catalogue, and the plan is
drafted on the `main` that has it.

## Owner's decisions (question round, 2026-11-13)

- **Timing:** "After §14": the spec now, the build after §14's merge.
- **Files:** "One cases.jsonl": grow `evals/cases.jsonl` to 50, keeping
  §8's 15.
- **Source:** "Picked from generated sets": the implementer proposes 35
  from `evals/generated.jsonl` and `evals/generated haiku.jsonl`, rewrites
  them to sound like customers and fills expectations from each probe; the
  owner edits and approves in the live check.
- **Expectations:** "Add property checks": new property expectations in
  `cases.py` and `score.py` (core code), next to the fixed ids.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `src/advisor/evals/cases.py` `_FIELDS`, `parse_cases` | The case format: `id`, `question`, `expect_ids`, `forbid_ids`, `must_decline`, `expect_search`, `note`, `dimensions`. B1 adds one field. |
| `src/advisor/evals/cases.py:26-34` | `SCENARIOS`: exact-match, several-matches, no-match, budget-too-low, out-of-stock, off-topic, spelling-differs. |
| `src/advisor/evals/coverage.py:19-24`, `check_coverage` | The four `PERSONAS`; "A generated question is only kept if its *probe* … behaves as its scenario says against the real catalogue." B6 re-runs it on the 500-product catalogue. |
| `src/advisor/evals/score.py` `score`, `_call_satisfies` | The checks today (grounded, prices, expected, forbidden, declines, stock, search). B3 adds two. |
| `intents/13-catalogue-change-rules/spec.md` B2–B3 | How `expect_search` is read against the catalogue ("expected results"); B4 extends that check. |
| `tests/test_evals_cases.py:24` | `assert 12 <= len(load_committed()) <= 20`; B7 replaces it. |
| `README.md` "Error analysis" | "Read and edit `evals/generated.jsonl` before you use it." |
| `CLAUDE.md` | "Committed data: `evals/generated.jsonl`, …"; untrue today (untracked). B9. |

## Behaviour

**Property expectations (core code)**

- **B1.** A case may carry `expect_properties`: a non-empty list of names
  from a fixed set, `cites_a_match` and `cites_only_matches`. A property
  needs `expect_search` on the same case; `parse_cases` rejects an unknown
  name, a repeated name, a non-list, or a property without
  `expect_search`, naming the line, case and field as it does today.
- **B2.** A product *fits* a case when it satisfies every constraint of the
  case's `expect_search`, read as §13 B2 reads it (category equal, price
  bounds inclusive, in stock when `in_stock_only`, `keywords_any` any-of,
  normalised as `search_products` does).
- **B3.** `score` adds, for a case with properties:
  - `cites_a_match` → a check `a-match`: ok when at least one cited,
    existing product fits; the reason names the cited ids otherwise;
  - `cites_only_matches` → a check `only-matches`: ok when every cited,
    existing product fits; the reason names the ids that do not.
  A case without properties gets exactly the checks it gets today.
- **B4.** §13's consistency check also reports a case with
  `cites_a_match` whose `expect_search` fits no product in the first
  `MAX_LIMIT` ("no product fits, so cites_a_match cannot pass").

**The 50 cases (data)**

- **B5.** `evals/cases.jsonl` holds exactly 50 cases: §8's 15 (ids,
  questions and expectations kept, `dimensions` added) and 35 new ones.
  Every case has `dimensions` with a `persona` from `PERSONAS` (or
  `off-topic` feature); ids and questions are unique.
- **B6.** Each new case comes from the two generated files, with a probe
  that still passes `check_coverage` for its scenario on the 500-product
  catalogue. Its question is rewritten to read like a customer, keeping
  what the probe expresses. Its expectations follow its scenario:

  | Scenario | Expectations |
  | --- | --- |
  | exact-match | `expect_search` from the probe; `expect_ids` when one product is the right answer, else `cites_a_match` |
  | several-matches | `expect_search`; `cites_a_match` (and `cites_only_matches` when alternatives outside the request would be wrong) |
  | spelling-differs | `expect_search` with the correctly spelled keyword in `keywords_any`; `cites_a_match` |
  | out-of-stock | `expect_ids`: the probe's product (the stock check then requires "out of stock") |
  | no-match, budget-too-low | `expect_search` only; wording is left to the judge (§16) |
  | off-topic | `must_decline: true` |

- **B7.** A test asserts the spread: exactly 50 cases; every scenario
  present, off-topic 2–4, every other scenario 5–12; each of the 8
  categories at least 4 times as `feature`. It replaces
  `test_committed_file_validates_and_has_12_to_20_cases`.
- **B8.** The set includes customer-style variety, named in each case's
  `note` so the review can count it: at least 5 with a misspelling or
  typo, 5 with two or more constraints, 5 vague (no category word), 5 in
  a casual or follow-up register.
- **B9.** `CLAUDE.md` and README stop calling `evals/generated.jsonl`
  committed: it is a generated pool, not committed. The two generated
  files stay untracked; the implementer reads them from copies the
  coordinator puts in the worktree (not committed).

## Interpretations

- **"Real-looking"** (intent) is read as: rewritten into customer phrasing
  with B8's variety, then read and approved by the owner in the live check.
  No real user data.
- **"Expected behaviour"** is what the code checks can score (B3, B6);
  how an answer is worded for no-match and budget-too-low is the judge's
  (§16), not a property.
- **`cites_only_matches` with `keywords_any`**: a fitting product must
  contain one of the words, so a case uses it only when its keywords are
  the point of the request (B6 leaves it optional).
- **§8's 15 keep their fixed ids** (the owner chose to keep them); they
  gain `dimensions` only.

## Acceptance criteria

- **AC1** (B1): parse tests: a valid list; an unknown name, a repeat, a
  non-list, and a property without `expect_search` each raise with line,
  case and field. (tests/test_evals_cases.py)
- **AC2** (B2, B3): score tests over an in-test catalogue: `a-match` ok /
  not ok, `only-matches` ok / naming the misfit; each constraint kind
  (category, both bounds inclusive, `in_stock_only`, keywords any-of and
  hyphen-insensitive); no new check without properties.
  (tests/test_evals_score.py)
- **AC3** (B4): a consistency test where nothing fits a `cites_a_match`
  case gives one problem naming the case. (tests/test_evals_cases.py)
- **AC4** (B5, B7): the committed file parses, is consistent (§13's test)
  and meets the spread. (tests)
- **AC5** (B6, B8): the review reads the 35 new cases against their
  sources (id of the generated question each came from, in `note`) and
  counts B8's variety.
- **AC6** (live check, owed by rule 3): the owner reads all 50 questions
  and expectations, edits any, and runs `uv run advisor-eval` once on the
  default model; the review quotes the pass rate as the baseline.

## Non-functional

- **Boundaries:** `cases.py` and `score.py` stay pure core code; no change
  to `run.py` beyond what B3's new checks need (none expected: checks are
  listed generically).
- **Data:** synthetic questions only; generated pool files not committed.
- **Model use:** none in code or tests. The implementer (an agent) does
  the rewriting while building; the live check makes one local
  `advisor-eval` run.
- **Autonomy:** the owner approves the questions before merge (AC6).

## Out of scope

- The LLM judge (§16) and running evals on every change (§17).
- New properties beyond the two (e.g. "every cited product is under the
  budget" for budget-too-low alternatives).
- Changing §8's 15 expectations, `generate`, or the catalogue.

## Assumptions I made

- **Two properties, not more:** they cover the positive scenarios; the
  negative ones (no-match, budget-too-low) are wording, which §16 judges.
- **The field name** `expect_properties` and the check names `a-match`,
  `only-matches`.
- **Spread bounds** (B7) and **variety counts** (B8) are mine; easy to
  change at the spec stop.
- **Personas** from `PERSONAS` for all 50, including §8's 15.
- **generated.jsonl stays uncommitted** and the docs are corrected (intent
  question 6), since it was left untracked through two runs.
- **Waiting for §14:** after `spec_accepted`, `/auto 15` stops with
  `auto_stopped: waiting for 14 to merge` and drafts the plan on the next
  `/auto 15` after §14 ships.
