<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §32 — Product search treats "heartrate" and "heart-rate" as different words

**Type:** fix
**Originator:** the coordinator's error analysis of the qwen3:8b eval runs
of 2026-11-24, turned into an intent on the owner's "write intents"
**Source:** `evals/runs/20261124T215703Z-ollama.json`, case
`heartrate-training-zones`; `intents/7-search-hyphens` (a hyphen counts as
a space)

## Problem

The case `heartrate-training-zones` ("Which smartwatches have an optical
heartrate sensor with continuous logging? I want the data for my training
zones.") fails in every qwen3:8b run. In the latest run the model searched
`{"category": "smartwatch", "keywords": ["optical heartrate sensor",
"continuous logging"], "in_stock_only": true}`. It answered "None of the
recommended products have an optical heart rate sensor with continuous
logging", and cited nothing. Yet 31 of the 62 smartwatches say
"heart-rate tracking" in their description (e.g. P-025, "Sporty
smartwatch with GPS and heart-rate tracking.").

Keyword matching is a substring test after `catalogue._norm`, which is
`text.lower().replace("-", " ")` (`src/advisor/catalogue.py:109`). It
only turns a hyphen into a space, so a word written joined never matches
the same word written apart or hyphenated. On the committed catalogue:

- `{"category": "smartwatch", "keywords": ["heart rate"]}` matches
  (P-102, P-222, …, `keywords_matched` 1);
- `{"category": "smartwatch", "keywords": ["heartrate"]}` matches nothing,
  and the §22 B11 fallback returns ten rows with `keywords_matched` 0.

Each keyword is matched as a whole phrase. "optical heartrate sensor" is
looked up as one string and is not a substring of any product text, and
neither is "continuous logging". No smartwatch text contains "optical" or
"continuous" at all.

The eval's own check has the same blind spot. The case expects
`"expect_search": {"category": "smartwatch", "keywords_any":
["heart-rate"]}`. `score._call_satisfies` (`src/advisor/evals/score.py:136`)
passes when a normalised wanted word is a substring of a normalised
searched keyword. "heart rate" is not in "optical heartrate sensor", so
`search` fails ("no search_products call matches …").

## Outcome

- Keyword matching ignores separators (space and hyphen): `heartrate`,
  `heart rate` and `heart-rate` match each other, in the keywords and the
  product text alike.
  `{"category": "smartwatch", "keywords": ["heartrate"]}` returns the same
  smartwatches as `["heart rate"]`, with `keywords_matched` 1.
- The eval's `keywords_any` check, and the case checks in
  `src/advisor/evals/cases.py` that mirror the search (`fits`,
  `_expected_results`, `catalogue_problems`), fold separators the same way
  as the search does. A search for `["heartrate"]` satisfies
  `keywords_any: ["heart-rate"]`.
- No match is lost: every product a keyword search matches today is still
  matched, whatever the limit. The existing tests in
  `tests/test_catalogue.py` and `tests/test_agent.py` stay green,
  unchanged. Folding may add matches across word boundaries (owner's
  decision, 2026-11-25, "32 A": full fold, both sides; for example `hd`
  also matches "1.2-inch display" folded). At the result limit of 10 a new
  cheaper match can displace an old one from the returned rows (owner's
  decision after round 1, "32 A": 9 of 11,043 probe searches on the
  committed catalogue); the ranking is not changed to prevent it.
- An eval run is made on the change (`REVIEW-POLICY.md` → "Eval runs"),
  and the review says whether `heartrate-training-zones` flipped and why.

## Constraints

- `catalogue.py`, `evals/cases.py` and `evals/score.py` are core code
  (`CORE_CODE` in `scripts/intent-check-lib.mjs`): pure and tested. No new
  dependency, no stemming or fuzzy-matching library.
- All three files are in `EVAL_PATHS`, so the change owes an eval run.
  Evals run on Ollama; a paid run only on the owner's request.
- `score.misnamed` (§25) also uses `_norm`, character by character
  (`score.py:53`), to find product names in an answer. Separator folding
  for keywords must not change how that check reads names. The plan must
  not simply make `_norm` drop spaces.
- The search, the eval check and the case checks must keep agreeing on
  what matches, as §22 made them (`cases.py:207`, "as
  search_products(keywords=...) matches too").
- `evals/cases.jsonl` is not edited to make the case pass.

## Type-specific questions

### Fix
- **What broke:** observed: `heartrate` finds no smartwatch, and the model
  says none fits. Expected: it finds the smartwatches with "heart-rate
  tracking".
- **Since when:** since §1. Search has always been a substring match.
  §7 (d5f4cc1) made a hyphen equal a space, but not the joined form.
- **Impact:** an end user who writes a compound word joined is told that
  nothing fits, although products fit. This is 1 of the 50 cases, failing
  on every run. There is no data leak.
- **Reproduction:** `search_products(load_catalogue(),
  category="smartwatch", keywords=["heartrate"])` returns `[]`, while
  `keywords=["heart rate"]` returns smartwatches. And `score` on a
  `search_products` call with `{"category": "smartwatch", "keywords":
  ["heartrate"]}`, against the case's `expect_search`, fails `search`.
- **The test that will fail first:** `tests/test_catalogue.py`. A new test
  asserts that `search_products` with `keywords=["heartrate"]`,
  `["heart rate"]` and `["heart-rate"]` returns the same products, in
  the style of the existing §7 hyphen tests. There is also one in
  `tests/test_evals_score.py`: a call with `keywords: ["heartrate"]`
  satisfies `keywords_any: ["heart-rate"]`.

## Assumptions I made

- **Multi-word keywords stay whole phrases.** This fix does not split a
  keyword into words. With the fix alone, the model's actual search
  `["optical heartrate sensor", "continuous logging"]` still matches no
  product: "opticalheartratesensor" is not in any product's folded text.
  The search returns the fallback rows with `keywords_matched` 0, so
  `cites_a_match` most likely still fails. The `search` check would pass,
  though, because "heartrate" is a substring of the folded
  "opticalheartratesensor". The case flips only if the model searches
  shorter keywords, as gpt-oss:20b did (`["optical", "heartrate",
  "continuous"]`). **Open point for the owner:** should a multi-word
  keyword also match when all (or any) of its words match? That would
  change §22's ranking. I left it out and expect at most 1 case to flip,
  and possibly none.
- **Cross-word matches.** Folding can create a few new matches across word
  boundaries (e.g. "in ear" as "inear" inside "within earshot"). I assume
  that is acceptable as long as no current match is lost. The plan should
  check the catalogue for such matches.
- **`follows_up` is empty.** The gap is in §1's substring matching as
  specified, and §7 narrowed it on purpose to hyphens. Neither introduced
  a regression. `follows_up: 7` would also be defensible.
- **Tier.** The path table decides (Attested, `src/**`), so `review_tier`
  is empty. No prompt change is planned.
