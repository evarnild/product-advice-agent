<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §14 spec — Grow the catalogue to 500 products

Accepted intent: [intent.md](intent.md)

Written against `main` at `ddc1d01`. **Built after §13 merges**: its
consistency test and ADR 0003 are what this change is checked against.

## Owner's decisions (question round, 2026-11-13)

- **Generation:** "Seeded script, committed": a deterministic generator,
  no model.
- **Categories:** "Same 8, ~60 each": no change to `CATEGORIES` or the
  prompt.
- **Specs:** "Fixed keys per category" for the new products, enforced by a
  test.
- **Mix:** "~15% out of stock, ~12 brands", each category spanning cheap
  to premium.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `src/advisor/catalogue.py` | `CATEGORIES` (8); `_FIELDS = ("id", "name", "brand", "category", "price_eur", "in_stock", "specs", "description")`; `_ID_RE = ^P-\d{3}$`; `specs` is `dict[str, str]`; `load_catalogue` validates every product. |
| `src/advisor/data/catalogue.json` at `ddc1d01` | 32 products: headphones 6, laptop 6, phone 5, monitor 4, tablet 3, smartwatch 3, speaker 3, camera 2; 5 out of stock; brands Auralis, Kestrel, Sonavo, Norvik, Pelagic, Tolvane, Lumino, Zephra; whole-euro prices. |
| `docs/decisions/0003-catalogue-changes.md` (§13) | ids only grow, never reused; "adding many products … is a feature"; "the change that breaks a case fixes the case in the same branch"; "a catalogue change owes an `advisor-eval` run whose report the review names". |
| `intents/13-catalogue-change-rules/spec.md` B2–B3 | The consistency test this change must pass: expected ids matched within the first 10, forbidden ids not matched. |
| `src/advisor/catalogue.py` `search_products` | Keywords are matched in name, brand and description only (not specs): descriptions must name the searchable features. |
| `CLAUDE.md` | "The catalogue is synthetic and committed." |

## Behaviour

**The generator (pure, committed)**

- **B1.** A pure module `src/advisor/catalogue_build.py` exposes
  `build_products(existing, seed) -> list[dict]`: given the hand-written
  products, it returns them unchanged followed by the generated ones, in
  id order. Same input and seed → byte-identical output. No file I/O, no
  randomness outside a seeded `random.Random`, no model.
- **B2.** `uv run python -m advisor.catalogue_build` reads the first 32
  products of `src/advisor/data/catalogue.json`, builds, and rewrites the
  file (UTF-8, the file's current JSON layout). The seed is a constant in
  the module.
- **B3.** **Counts:** 500 products in total. laptop, phone, headphones and
  monitor reach 63 each; tablet, smartwatch, camera and speaker 62 each.
  New ids run P-033 … P-500 with no gap.

**The generated products**

- **B4.** Each new product has every field `load_catalogue` requires and
  these spec keys per category (values are strings, as today):

  | Category | Spec keys |
  | --- | --- |
  | headphones | `type`, `noise_cancelling`, `battery` |
  | laptop | `cpu`, `ram`, `storage`, `screen` |
  | monitor | `size`, `resolution`, `refresh` |
  | phone | `screen`, `storage`, `camera` |
  | smartwatch | `screen`, `battery`, `gps` |
  | tablet | `screen`, `storage`, `stylus` |
  | camera | `sensor`, `video`, `waterproof` |
  | speaker | `type`, `battery`, `waterproof` |

- **B5.** **Prices** are whole euros ending in 9, inside a band per
  category spanning cheap to premium (headphones 19–449, laptop 249–2999,
  monitor 89–1499, phone 99–1799, smartwatch 29–799, tablet 99–1499,
  camera 149–2999, speaker 19–699), spread over the band rather than
  clustered; specs scale with price (more storage, bigger screens, active
  noise cancelling more likely at the top).
- **B6.** **Stock:** between 12% and 18% of the new products are out of
  stock, at least 5 in each category.
- **B7.** **Brands:** the 8 existing brands plus 4 new invented ones
  (12 in total); each category uses at least 4 brands. A new brand must
  not be a real electronics brand (the review checks the names).
- **B8.** **Names** are `<Brand> <Line> <Model>` and unique across the
  catalogue. **Descriptions** are one sentence that names the category in
  plain words and the searchable features of its specs (e.g. "active noise
  cancelling", "waterproof", "built-in GPS", "with stylus support"), so
  keyword searches find them.

**Consequences in the same branch**

- **B9.** Every §8 case that §13's consistency test reports after the
  growth is fixed in this branch: by tightening its `expect_search` (a
  price bound or a keyword) or its expected ids, never by deleting the
  case, each with its `note` saying why ("§14: 63 laptops; P-008 ranked
  beyond 10 on category alone").
- **B10.** Tests that count or depend on the shipped catalogue's size or
  contents are updated; tests over in-test catalogues are untouched.

## Interpretations

- **"Each category has enough to choose from"** (intent) is B3's 62–63
  per category and B5's bands.
- **"~15% out of stock"** is B6's 12–18% range, so the seed need not hit
  an exact count.
- **"Fixed keys per category"** applies to the generated products; the 32
  hand-written ones keep their keys (some have extras, e.g. `gpu`,
  `weight`), since ADR 0003 forbids changing them without cause.

## Acceptance criteria

- **AC1** (B1): the same seed twice gives equal output; a different seed
  differs; the first 32 are returned unchanged. (test)
- **AC2** (B2, B3): the committed catalogue equals `build_products` over
  its own first 32 with the module's seed (so the file is reproducible),
  has 500 products, P-001 … P-500 without gaps, and the per-category
  counts. (test)
- **AC3** (B4–B8): over the generated products: spec keys per category;
  whole prices ending in 9 inside each band; out-of-stock share and
  per-category minimum; brand count and per-category spread; unique names;
  each description contains its category word and its features' phrases.
  (tests)
- **AC4** (B9): §13's consistency test passes; each changed case's note
  names §14 and the reason. (test + review)
- **AC5** (live check, owed by rule 3: model answers on the new
  catalogue): the owner runs `uv run advisor-eval` (Ollama) on `main`
  before and on the branch after, compares the two reports' pass rates and
  failed cases, and spot-checks three answers in Langfuse for sensible
  products.

## Non-functional

- **Boundaries:** `catalogue_build.py` is pure and not imported by the
  advisor at runtime; `catalogue.py`, `agent.py`, the prompt and the
  search contract are unchanged.
- **Data:** synthetic only; invented brands and names.
- **Model use:** none in the generator or tests; the live check runs the
  advisor on the local model.
- **Size:** about 500 × 300 bytes (≈150 KB) of JSON; `load_catalogue`
  stays fast; the model still sees at most 10 products per search.

## Out of scope

- New categories or fields; changing the 32 hand-written products; the 50
  cases (§15); §9's generated questions and their probes; enforcing the
  eval run (§17).

## Assumptions I made

- **The generator's place and name** (`src/advisor/catalogue_build.py`,
  run with `python -m`), not a console script.
- **The exact counts** (B3), **price bands** (B5), **spec keys** (B4,
  taken from today's majority keys; camera and speaker gain
  `waterproof`), **the 12–18% range** (B6) and **4 new brands** (B7).
- **Prices ending in 9**, like most of today's.
- **The live check compares two runs by hand**, since §17's `compare`
  will not exist yet.
- **Waiting for §13:** after `spec_accepted`, `/auto 14` stops with
  `auto_stopped: waiting for 13 to merge` and drafts the plan once §13 has
  shipped.
