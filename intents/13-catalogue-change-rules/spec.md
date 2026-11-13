<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §13 spec — Catalogue changes cannot silently break the eval set

Accepted intent: [intent.md](intent.md)

Written against `main` at `e366ed7`.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `src/advisor/evals/cases.py:67` | Today's only catalogue check on a case: `raise fail(key, f"names unknown product id '{i}'")`. Stays. |
| `src/advisor/evals/score.py` `_call_satisfies` | How `expect_search` is read: `category` equal, `max_price` / `min_price` as bounds, `in_stock_only` equal, `keywords_any` satisfied when **any** wanted word appears. B2 reads the filters the same way. |
| `src/advisor/catalogue.py` `search_products` | "Products matching every given filter, cheapest first (ties by id), at most `limit`"; "`limit` is clamped to 1..10" (`MAX_LIMIT = 10`). B2's "visible" is the first `MAX_LIMIT` in that order. |
| `src/advisor/evals/run.py:310-311` | The report already records `"cases_sha256": hashlib.sha256(raw).hexdigest()` and `"prompt_sha256": …`; B5 adds the catalogue the same way. |
| `docs/decisions/0001-stack.md` | "A structured filter tool (`search_products`) over a small committed JSON catalogue". B7's ADR adds rules to it and supersedes nothing. |
| `intents/8-offline-evals` | The case format and code checks; unchanged. |
| `intents/17-evals-every-change/intent.md` | Enforcing owed eval runs belongs there; this spec only writes the rule down (B8). |

## Behaviour

**The consistency check (pure, `cases.py` or a new pure module beside it)**

- **B1.** A pure function takes parsed cases and a catalogue and returns
  one problem per broken expectation, each naming the case id, the product
  id and why. An empty result means the cases are consistent.
- **B2.** For a case with `expect_search`, its *expected results* are the
  catalogue products that satisfy every constraint in `expect_search`, read
  as `score._call_satisfies` reads a model's call: `category` equal,
  `price_eur ≤ max_price`, `price_eur ≥ min_price`, in stock when
  `in_stock_only` is true, and, for `keywords_any`, at least one word
  appearing in the product's name, brand or description, normalised as
  `search_products` does (case and hyphens). They are ordered as
  `search_products` orders them (price, then id).
- **B3.** For such a case, a problem is reported when:
  - an `expect_ids` product is not among the expected results ("not
    matched by expect_search");
  - an `expect_ids` product is matched but ranked beyond `MAX_LIMIT`, so no
    call with those filters can show it ("ranked N of M, beyond the 10 a
    search can return");
  - a `forbid_ids` product is among the expected results ("forbidden but
    matched by expect_search").
- **B4.** Cases without `expect_search` (today `out-of-stock-quiet-pro`,
  `voice-speaker`, `off-topic-weather`, `off-topic-poem`) are not checked
  by B3; `parse_cases` still rejects an unknown id in them.

**The test and the report**

- **B5.** A test in the suite parses the committed `evals/cases.jsonl`
  against the shipped catalogue and asserts B1 returns no problem; on
  failure its message lists every problem. Today's 15 cases pass (checked
  by hand at `e366ed7`: every expected id is matched within the first 10,
  no forbidden id is matched), so no case changes in this intent.
- **B6.** The run report (`evals/runs/<stamp>-<provider>.json`) gains
  `"catalogue_sha256"`: the SHA-256 of the bytes of the catalogue file
  `advisor-eval` loaded, next to `cases_sha256` and `prompt_sha256`.
  Nothing else in the report or stdout changes. Readers of reports
  (`advisor-analysis`, the viewer) keep accepting a report without it.

**The written rule**

- **B7.** A new ADR `docs/decisions/0003-catalogue-changes.md` states:
  - ids only grow: a new product takes the next free `P-NNN`; an id is
    never reused or renumbered;
  - a product leaves by being deleted from the file; its id is retired for
    good (no tombstone field);
  - a change to a few products' price, stock, specs or wording is an
    **adjustment**; adding many products, a category or a field is a
    **feature** (a category or field touches core code);
  - the change that breaks a case fixes the case in the same branch (B5
    makes it fail `verify`);
  - old run reports, labels and taxonomies are records of their run and are
    not redone; `catalogue_sha256` says which catalogue they saw;
  - a catalogue change owes an `advisor-eval` run whose report the review
    names; enforcement is §17's.
- **B8.** `README.md` → "Evaluating answers" gets a short "Changing the
  catalogue" paragraph pointing to the ADR, and `CLAUDE.md`'s architecture
  notes mention the consistency test and the new report field in one line
  each.

## Interpretations

- **"A stale case"** (intent Outcome) is read as B3's three conditions:
  the expected search cannot show an expected product, or would show a
  forbidden one. Price and stock assumptions are covered through the
  filters (`max_price`, `in_stock_only`); a case that relies on stock
  without `in_stock_only` is not checked for it.
- **"Returned" for `expect_ids`** is read as within the first `MAX_LIMIT`
  (10), not the tool's default `limit` of 5: the model may ask for up to
  10, and a stricter bar would fail cases (today `video-editing-laptop`,
  P-008 ranked 6 of 6) that a model can still answer.
- **`keywords_any`** is any-of, as `score.py` reads it, not the all-of of
  `search_products(keywords=…)`: the check asks what a search that
  satisfies the case's `expect_search` could show.
- **The hash covers the file's bytes**, like `cases_sha256`, so a
  whitespace-only edit changes it.

## Acceptance criteria

- **AC1** (B2, B3): unit tests over a small in-test catalogue: an expected
  id outside the filters, one ranked 11th of 11, and a matched forbidden id
  each give one problem naming the case and the id; a consistent case
  gives none; `keywords_any` matches on any word, case- and
  hyphen-insensitively. (test)
- **AC2** (B4): a case without `expect_search` gives no problem, whatever
  its ids. (test)
- **AC3** (B5): the committed cases are consistent with the shipped
  catalogue (the new test passes at the branch head); mutating one
  `expect_ids` to an out-of-filter product makes it fail with that case's
  id in the message. (test; mutation in review)
- **AC4** (B6): a run through `run.py` with a fake client writes
  `catalogue_sha256` equal to the SHA-256 of the catalogue file it loaded;
  `advisor-analysis counts` and `view` read a report without the field.
  (tests in `tests/test_evals_run.py`, `tests/test_analysis_*`)
- **AC5** (B7, B8): the ADR, README paragraph and `CLAUDE.md` lines exist
  and match B7's list. (review reads them)

## Non-functional

- **Boundaries:** the check is pure (no file reads), core code, beside
  `cases.py`; the test does the file reads. `run.py` stays the only I/O.
  No change to `catalogue.py`, `score.py`, the catalogue data or the
  cases.
- **Data:** synthetic catalogue and cases only.
- **Model use:** none, in the check or the tests.
- **Autonomy:** not applicable; nothing runs on its own.
- **Live check:** expected `not-needed`: no rule-1 path is touched
  (`run.py` only gains a report field, proven by a test).

## Out of scope

- Checking `evals/generated.jsonl` or other case files (not committed;
  §15 decides); a runtime warning in `advisor-eval` for stale cases.
- Property-style expectations ("cites only in-stock products under the
  budget"): §15.
- A tombstone or `retired` field in the catalogue; a test that ids were
  never reused (needs git history).
- Enforcing owed eval runs (§17); growing the catalogue (§14).

## Assumptions I made

- **Where the "owes an eval run" rule lives** (intent question 1): the ADR
  and README only, not `REVIEW-POLICY.md`, so this stays at the path
  table's tier and §17 owns enforcement.
- **Retirement** (question 2): delete and retire the id, no new field, to
  keep core code and the catalogue format unchanged.
- **Cases without `expect_search`** (question 3): skipped by B3 (B4).
- **Property-style expectations** (question 4): left to §15.
- **Generated probes** (question 5): not checked; only `cases.jsonl`.
- No question round was needed: each open question had a reading that
  keeps the change small and leaves the bigger choice to §15 or §17.
