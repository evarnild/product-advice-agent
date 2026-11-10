<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §7 — Product search misses matches when a keyword and the catalogue differ only by a hyphen

**Type:** fix
**Originator:** the owner, during §2's live check (step 3)
**Source:** `intents/2-local-model/review.md` → "Live check", step 3;
`intents/1-stack-and-skeleton/spec.md` B4

## Problem

Asked "I need noise-cancelling headphones under 200 euros", the advisor
answers "There are no noise-cancelling headphones available under 200
euros", although the catalogue has three: P-001 (189 €, in stock), P-004
(159 €, out of stock) and P-005 (129 €, in stock).

The model's tool call is sensible and the same every time:
`search_products(category="headphones", max_price=200,
keywords=["noise-cancelling"])` (`qwen3:8b`, 3 runs out of 3). It gets `[]`
back, because a keyword matches only when it appears exactly in the name,
brand or description, and the catalogue says "noise cancelling" without a
hyphen. The same question written without the hyphen gives
`keywords=["noise cancelling"]` and a correct answer naming P-005 and P-001.

The user is told, wrongly, that nothing matches. A keyword written with a
hyphen fails against text written with a space, and the other way round
(`"in ear"` against "in-ear", `"two day"` against "two-day").

## Outcome

- `search_products` treats a hyphen the same as a space, in both the
  keywords and the product text. `keywords=["noise-cancelling"]` with
  `category="headphones", max_price=200` returns P-005, P-004 and P-001,
  and `keywords=["in ear"]` matches "in-ear".
- Every keyword search that works today returns the same results as before.
  The existing tests in `tests/test_catalogue.py` stay green, unchanged.
- §1's spec B4 says how hyphens are treated, so the documented behaviour
  matches the code.

## Constraints

- Only `src/advisor/catalogue.py` (core code: `search_products` stays a
  pure function), its tests, and the B4 wording. Leave the tool schema and
  argument checks in `agent.py`, the prompt and the catalogue data as they are.
- No new dependency. No fuzzy or semantic matching, stemming or
  embeddings: matching stays exact and case-insensitive.
- Out of scope: telling the model to search again with broader keywords
  after an empty result. That is a prompt change (`src/advisor/prompts/`,
  Reviewed tier), and a possible separate adjustment.
- Tests stay offline with the catalogue fixtures. The live run that found
  this is evidence, not a test.

## Type-specific questions

### Fix
- **What broke:** a keyword that differs from the catalogue text only by a
  hyphen matches nothing (observed: `[]` and "no headphones available").
  Expected: the noise-cancelling headphones under 200 €.
- **Since when:** since keyword search was added in §1
  (3d4f3ac, "§1: synthetic catalogue, validation and search"). It has
  always matched exactly. §2's local default made it visible, because
  `qwen3:8b` copies the user's spelling into the keyword.
- **Impact:** any user who writes a hyphenated term the catalogue spells
  with a space, or the other way round, is told that nothing matches. The
  answer is wrong, but it is shown with confidence. No data leaks. Any
  provider is affected whenever its keyword keeps the user's spelling.
- **Reproduction:** `search_products(load_catalogue(),
  category="headphones", max_price=200, keywords=["noise-cancelling"])`
  returns `[]`. End to end: `uv run advisor "I need noise-cancelling
  headphones under 200 euros"` with the Ollama default.
- **The test that will fail first:** in `tests/test_catalogue.py`, a test
  that searches the test catalogue (whose fixture already contains "noise
  cancelling and light") with `keywords=["noise-cancelling"]`. It asserts
  the same result as `keywords=["noise cancelling"]`, and the reverse case
  for a hyphenated description.

## Assumptions I made

- **Hyphens only.** The fix covers the ASCII hyphen `-`. Other dashes
  (`–`, `—`), slashes, and words run together ("noisecancelling") are left
  out. Widen it if you want those too.
- **Both sides are normalised.** The keyword and the product text are both
  normalised, so the fix works in both directions, not only for hyphenated
  keywords.
- **`follows_up: 1`.** The exact matching was §1's decision (B4). This is a
  gap in that decision, not a regression.
- **Tier.** `catalogue.py` is `src/**` and not on the Reviewed list, so the
  path table gives Attested, and `review_tier` is left empty.
- **B4 wording.** The spec B4 wording is updated in §1's folder as part of
  this fix, so the spec stays true.
