<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §7 plan — Product search misses matches when a keyword and the catalogue differ only by a hyphen

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`search_products` treats a hyphen as a space in both the keywords and the
product text. So `keywords=["noise-cancelling"]` finds "noise cancelling",
and `["in ear"]` finds "in-ear". Every keyword search that matched before
still returns the same products. The change is one normalisation step in
`src/advisor/catalogue.py`, with failing-first tests. The rule is
documented in the function's docstring and in this intent's folder. §1's
spec is left as it is (the owner's instruction, below).

## Owner's decision

- **"Do not change the old intent"** (`/auto 7`, 2026-11-10). The intent's
  third Outcome bullet ("§1's spec B4 says how hyphens are treated") and
  its Assumption "B4 wording … updated in §1's folder" are replaced: §1's
  `spec.md` is not edited. The behaviour is recorded in:
  - the `search_products` docstring;
  - `CLAUDE.md` → "Architecture" (the `catalogue.py` line);
  - this intent's folder, which states it as an addition to §1 B4.

  This follows `intents/README.md` ("forward-fix with a new one. Don't
  rewrite the old folder").

## Risks

- **A test that passes whatever the code does** (§1's recurring class).
  - The new tests must fail on today's `main`. The implementer runs them
    once before the fix.
  - The fixture must differ from the keyword only by the hyphen: a
    hyphenated keyword against spaced text, and the reverse. A case where
    both are already spaced proves nothing.
- **Changed results for existing searches.** The rule only adds matches
  (see Goal). The existing `tests/test_catalogue.py` and
  `tests/test_agent.py` stay green unchanged, and they are the regression
  proof.
- **A keyword that is only hyphens** (`"-"`, `"--"`) becomes blank after
  normalisation. Today a blank keyword is ignored (`if k.strip()`), so this
  one is ignored too, which follows from "a hyphen is a space". Before, `"-"`
  matched any product with a hyphen in its text. That match was accidental,
  but it is a behaviour change. A test pins it.
- **Overlap with §2** (`feat/2-local-model`, in review): §2 does not touch
  `catalogue.py` or `tests/test_catalogue.py`. `CLAUDE.md` may need a
  textual rebase.
- **Stale line citations:** read at `9c3c375`.

## Verified against the codebase

Re-read on `main` at `9c3c375`.

- `src/advisor/catalogue.py:109-138` — `search_products(catalogue, category, min_price, max_price, keywords, in_stock_only, limit)`; docstring `:118-122` ("Keywords all have to appear, case-insensitively, in the name, brand or description").
- `src/advisor/catalogue.py:124` — `words = [k.lower() for k in keywords or [] if k.strip()]`.
- `src/advisor/catalogue.py:135-136` — `haystack = f"{p.name} {p.brand} {p.description}".lower()`; `return all(w in haystack for w in words)`.
- `src/advisor/data/catalogue.json` — "active noise cancelling" in P-001 (`:14`), P-004 (`:56`) and P-005 (`:70`); "in-ear" (`:28`); "two-day battery" (`:204`). 32 products.
- `tests/test_catalogue.py:131-145` — the `CAT` fixture: P-003 "Has NOISE cancelling", P-004 "noise cancelling and light"; `:167-172` `test_keywords_case_insensitive_all_must_match`.
- `src/advisor/agent.py:101-105` — the tool's `keywords` check (a list of strings); unchanged.
- `intents/1-stack-and-skeleton/spec.md:54` — B4; not edited.
- `CLAUDE.md` → "Architecture": "`catalogue.py`: … `search_products` (AND of filters, price-then-id order, limit clamped to 1..10)".

## Subtasks

1. **Failing tests first** (`tests/test_catalogue.py`). Run them once
   against today's `search_products` and record in `## Progress` that each
   fails:
   - `test_hyphenated_keyword_matches_spaced_text`: on `CAT`,
     `keywords=["noise-cancelling"]` gives the same ids as `["noise
     cancelling"]`, namely `["P-003", "P-004"]`.
   - `test_spaced_keyword_matches_hyphenated_text`: on a small local
     fixture (one product, description "compact in-ear buds"),
     `keywords=["in ear"]` finds it, and so does `["IN-EAR"]`.
   - `test_committed_catalogue_noise_cancelling_headphones_under_200`: on
     `load_catalogue()`, `category="headphones", max_price=200,
     keywords=["noise-cancelling"]` gives ids `["P-005", "P-004", "P-001"]`
     (price order: 129, 159, 189). This is the intent's reproduction.
   - `test_hyphen_only_keyword_is_ignored`: `keywords=["-"]` gives the same
     as no keywords. It does not fail on `main` (today `"-"` matches only
     texts with a hyphen, and `CAT` has none, so `main` returns `[]`), and
     the progress note says so.
2. **The fix** (`src/advisor/catalogue.py`). Add a module-level helper,
   `_norm(text: str) -> str`, returning `text.lower().replace("-", " ")`.
   Use it for each keyword, keeping keywords that are non-blank *after*
   normalising, and for the haystack. Extend the docstring: "A hyphen
   counts as a space, in keywords and product text alike, so
   'noise-cancelling' finds 'noise cancelling' (§7)." Nothing else changes:
   no stemming, no other punctuation, no whitespace collapsing.
3. **Docs.**
   - `CLAUDE.md` → "Architecture": the `catalogue.py` line adds
     "keywords case-insensitive, a hyphen counts as a space".
   - In this folder, nothing beyond this plan. The rule is stated in Goal
     and in the docstring.
   - §1's `spec.md` stays untouched.
4. **Status.** Set `status: in-review` and append to `## Progress`.

## Tests

| Intent item | Test | Fails on `main` / when mutated |
| --- | --- | --- |
| Outcome 1 (failing first) | `test_hyphenated_keyword_matches_spaced_text` | fails on `main` (`[]`); fails if the keyword side isn't normalised |
| Outcome 1 (reverse) | `test_spaced_keyword_matches_hyphenated_text` | fails on `main`; fails if the haystack side isn't normalised |
| Reproduction | `test_committed_catalogue_noise_cancelling_headphones_under_200` | fails on `main` (`[]`) |
| Risk: hyphen-only keyword | `test_hyphen_only_keyword_is_ignored` | fails if blank-after-normalising keywords are kept (then `" "` must appear in every text, which it does, so this mutant would pass; the test pins the result, not the mechanism) |
| Outcome 2 (no regressions) | existing `tests/test_catalogue.py`, `tests/test_agent.py` unchanged | any search whose results change |

The implementer runs these mutants once each against the full suite:
`_norm` without `.replace(...)`; normalising only the keyword side; only
the haystack side; `.replace("-", "")` instead of `" "`. It records the
killing test for each, backs up and restores by copy, and finishes with
`git status --short` clean.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (fix with test changes; `catalogue.py` is
  core code).
- Live check: none by path. `catalogue.py` is not a rule-1 path (rule 1
  names `cli.py`, `models/`, `tracing.py`, `prompts/`, `infra/`). The
  reviewer decides rule 3. The end-to-end symptom ("no headphones") also
  depends on the model's tool call, so an optional owner run of `uv run
  advisor "I need noise-cancelling headphones under 200 euros"` after §2
  ships is worth doing, but is not a gate here.

## Assumptions I made

- **ASCII hyphen only,** as the intent assumes: no `–`, `—` or `/`, and no
  joined words.
- **No whitespace collapsing:** `"noise  cancelling"` (two spaces) still
  doesn't match. That is today's behaviour, and out of scope.
- **A hyphen-only keyword is ignored** (Risks). If you'd rather it match
  nothing, that is a one-line change; say so.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-10 — implementation (commits d5f4cc1, plus the bookkeeping commit after it)

- Shipped: the four tests in `tests/test_catalogue.py`, `_norm` in `src/advisor/catalogue.py` (keywords kept only if non-blank after normalising; haystack normalised), the docstring sentence, and the `catalogue.py` line in `CLAUDE.md`. No other intent folder touched; §1's spec untouched.
- Failing first, against the unfixed `search_products`: all four failed. The three expected ones returned `[]` (wanted `["P-003","P-004"]`; `["P-001"]` for `"in ear"`; `["P-005","P-004","P-001"]` for the committed catalogue). `test_hyphen_only_keyword_is_ignored` also failed, not as the plan guessed: it returned `[]` for `["-"]` where no keywords gives all four products (the plan's own reasoning, `main` returns `[]`, is why it fails against "same as no keywords").
- Mutants, full suite, each restored by copy; killing tests:
  - no `.replace`: all four new tests.
  - keyword side only (haystack not normalised): `test_spaced_keyword_matches_hyphenated_text`.
  - haystack side only (keywords not normalised): all four new tests.
  - `.replace("-", "")`: the hyphenated-keyword, spaced-keyword and committed-catalogue tests (the hyphen-only test passes, as the plan predicted, it pins the result and not the mechanism).
- `npm run verify`: 122 passed (was 118), ruff and mypy clean.
- Divergences: none. Test count before was 118 (122 minus four new).
