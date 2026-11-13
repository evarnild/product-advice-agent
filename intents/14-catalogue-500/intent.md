<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §14 — Grow the catalogue to 500 products

**Type:** feature
**Originator:** the owner, 2026-11-13: "/intent generate a 500 objects
catalog", then "draft both intents"
**Source:** the week's objective "50 real-looking questions with expected
behaviour"; §13 (catalogue change rules), which this depends on

## Problem

The synthetic catalogue (`src/advisor/data/catalogue.json`) has 32
products: headphones 6, laptop 6, phone 5, monitor 4, tablet 3, smartwatch
3, speaker 3, camera 2; 5 out of stock. That is too thin for the week's
objective of 50 realistic questions with expected behaviour:

- most categories have two to six products, so a question quickly has one
  obvious answer or none, and trade-offs (budget vs. features, an
  alternative when the first choice is out of stock) cannot be asked;
- `search_products` clamps results to 10 (`MAX_LIMIT = 10` in
  `src/advisor/catalogue.py`), but no category has more than 6 products, so
  the cap and the price ordering are never exercised;
- the advisor does not feel like a real shop in a demo.

## Outcome

- **The shipped catalogue has 500 products**, valid under `load_catalogue`
  (ids `P-001` … `P-500`, which `^P-\d{3}$` already allows), spread across
  the categories so each has enough to choose from, with a spread of price
  bands, brands and stock.
- **P-001 to P-032 are unchanged**, so §8's cases, §9's labels and old
  traces keep meaning what they meant.
- **The eval set follows.** §13's consistency test passes; every §8 case
  whose correct answer the growth changes is updated in the same change,
  each with a one-line reason. An `advisor-eval` run before and after is
  compared in the review.
- Everything stays synthetic: no real brand, product name or trademark.

## Constraints

- Synthetic data only; brands and names invented (today's style:
  "Auralis Calm 300"). No real user data.
- If a model drafts the products, it is a one-off run whose output is
  committed and checked by deterministic code; the suite makes no model
  call. A paid API run needs the owner's go; the local Ollama costs nothing.
- No new dependency without a plan line.
- The search tool's contract (filters, the 10-result cap, price-then-id
  order) does not change. The system prompt changes only if the spec says
  so (Reviewed tier).
- Depends on §13 being merged first.
- Out of scope: new categories or new product fields (unless the spec
  decides otherwise), the 50-case set itself, the LLM judge.

## Type-specific questions

### Feature
- **Users:** the owner (evals, demos); the advisor's users, who get more
  choice.
- **What exists today:** 32 hand-written products, the loader's
  validation, §9's coverage check that counts catalogue matches per
  question probe.
- **Open design questions:**
  1. How the products are made: a model drafts them and a script checks
     them; a seeded script with no model; or a committed generator command
     that can be rerun.
  2. Categories: the same 8 at about 60 each, or new ones (which change
     `CATEGORIES`, core code, and likely the prompt).
  3. The spec keys per category (today `specs` is free-form strings) and
     whether they are made consistent within a category.
  4. Price bands per category, the out-of-stock share (today about 15%),
     and the number of brands.
  5. Whether the generator, if any, is committed, and where it lives.
  6. Load and token cost: 500 products in memory is small, but whether any
     path sends the whole catalogue to the model (none does today).

## Assumptions I made

- It is a **feature**: bulk data, likely a generator, case updates and a
  review of what the growth changes.
- P-001 to P-032 stay as they are and new products are appended (the
  coordinator's recommendation; the owner has not answered it yet).
- The same 8 categories, deepened, unless the spec decides otherwise.
- "500 objects" means 500 products in `catalogue.json`.
- `review_tier` is left to the path table; it rises to Reviewed if the
  prompt changes.
