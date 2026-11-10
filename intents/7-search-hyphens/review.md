<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §7 review — Product search misses matches when a keyword and the catalogue differ only by a hyphen

verdict: attest
tier: attested
reviewed-commit: d12bd285045245cb60cbc93e1db55999882fab95
round: 1
sampled: yes
run: auto
live-check: not-needed

Tier: set by the path table. `src/advisor/catalogue.py` is `src/**`, not on
the Reviewed list. `tests/test_catalogue.py`, `CLAUDE.md` and the intent
folder raise nothing. `review_tier` is empty, and no CRITICAL or HIGH
finding or user-data item raises it.

**Sampling:** `npm run sdlc:scan -- --sample-due auto --exclude 7` →
"nth attested auto change = 3, every 3, sampled: yes". A full read of the
diff is due after the merge.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | pass |
| 3 | Behaviour against the spec (fix: reproduction) | pass |
| 4 | Tests prove the behaviour, not only pass | pass (7 of 7 mutants killed, including failing-first) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1) |
| 7 | Documentation | findings (1) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass |

**Pass 1.** `git diff main...HEAD --stat` lists five files: `CLAUDE.md`,
`intents/7-search-hyphens/{metadata.yml,plan.md}`,
`src/advisor/catalogue.py` and `tests/test_catalogue.py`.
- No other intent folder changed, and §1's `spec.md` B4 (`:54-60`) is
  untouched. The owner's "do not change the old intent" is honoured: the
  rule lives in the docstring, `CLAUDE.md` and this intent's plan.
- `_norm` is exactly `text.lower().replace("-", " ")`. Keywords are kept if
  non-blank after normalising, and the haystack is normalised.
- The tool schema, `agent.py`, the prompt and the data are unchanged.
- The existing tests are unmodified; four tests are appended at
  `tests/test_catalogue.py:196-219`.

**Pass 3.**
- **Reproduction:** `search_products(load_catalogue(),
  category="headphones", max_price=200, keywords=["noise-cancelling"])` →
  `['P-005', 'P-004', 'P-001']` on the branch, `[]` with `main`'s
  `catalogue.py`.
- `"in ear"` → `['P-002']` (`main`: `[]`); `"two day"` → `['P-014']`
  (`main`: `[]`).
- **"Every keyword search that works today returns the same results"**
  holds as a superset guarantee:
  - **Argument:** `.replace("-", " ")` maps characters one by one, so a
    substring stays a substring after normalising. Dropping keywords that
    are blank after normalising only loosens the filter.
  - **Probe 1:** `main` vs branch over 547 keywords (every token, adjacent
    token pair and lowercased token in the committed catalogue's texts):
    identical match sets and limited results, with 0 differences.
  - **Probe 2:** over 292 hyphen/space variants, 291 changed, all as
    additions involving a hyphen. None was a removal.

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 7, fix)
  note:  3 file(s), 37 line(s) changed outside intents/.
```

## Findings
- **LOW** `intents/7-search-hyphens/plan.md` (Subtask 1, last bullet; the
  "Risk: hyphen-only keyword" row) — the plan's predictions about
  `test_hyphen_only_keyword_is_ignored` are wrong on both counts:
  - it does fail on `main` (`main` returns `[]` for `["-"]`);
  - the keep-blank-keywords mutant is killed, by the second assertion
    `["--", "noise"]`.

  The Progress entry records the first divergence correctly. Its wording for
  the `.replace("-", "")` mutant ("as the plan predicted") attributes a
  prediction the plan made about a different mutant. The plan text is above
  the Progress marker. Worth a look.
- **LOW** `CLAUDE.md:153` — the new `catalogue.py` bullet is one line of
  about 120 characters, where the file wraps at about 78. The content is
  accurate. Worth a look.

## Not checked
- **The end-to-end symptom:** `uv run advisor "I need noise-cancelling
  headphones under 200 euros"` was not run (no live model). Whether the
  answer now names P-005 and P-001 depends on the model emitting the same
  tool call (seen in 3 of 3 runs during §2's live check) and using the
  result. This diff changes neither the prompt nor the schema.
- **Other punctuation** (en and em dashes, slashes, joined words,
  whitespace runs): out of scope by the intent's assumptions.
- **Unicode edge cases of `str.lower()`:** unchanged from `main`, not
  probed.
- **Arbitrary catalogue data:** the probes cover the committed catalogue;
  the superset property for other data rests on the argument.
- **The merge with `main` now that §2 is merged:** see the coordinator's
  re-run below (clean, 186 passed).

## Live check
- not needed: no rule-1 or rule-2 path is touched (`catalogue.py` is core
  code, not `cli.py`, `models/`, `tracing.py`, `prompts/` or `infra/`). On
  rule 3, the change is a pure, deterministic function proved in full by
  the offline tests and probes, and the model's tool call is unchanged by
  this diff. The optional owner run, `uv run advisor "I need
  noise-cancelling headphones under 200 euros"` (expect P-005 at €129 and
  P-001 at €189), is worth doing now that §2 has shipped, but is not a
  gate.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/7-search-hyphens` at d12bd28, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "71 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "122 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS. Matches.
- **Coordinator, re-run:** mutants with my harness (backup by copy, one
  replacement, file-changed assertion, full `pytest -q -x`, restore by
  copy):
  - M2 (haystack not normalised) KILLED by
    test_catalogue::test_spaced_keyword_matches_hyphenated_text;
  - M4 (`.replace("-", "")`) KILLED by
    test_catalogue::test_hyphenated_keyword_matches_spaced_text.

  Both match the reviewer.
- **Coordinator, re-run:** `git merge-tree --write-tree main
  fix/7-search-hyphens` with `main` at 474e066 (§2 merged) → clean. Pytest
  on the merged tree, from a scratch `git archive` export → "186 passed"
  (`main`'s 182 plus §7's 4).

**Reviewer, verified:**
- `verify`, `check:intent` and `sdlc:scan` (sampled: yes).
- The reproduction and equivalence probes, against `main`'s `catalogue.py`
  imported side by side (scratchpad `mut7r/probe.py`, `probe2.py`).
- Failing-first and 7 mutants (`mut7r/mut.py`), all killed:
  - M0, `main`'s file: 4 failed;
  - M1, no `.replace`;
  - M2, keyword side only;
  - M3, haystack side only;
  - M4, `.replace("-", "")`;
  - M5, keep blank keywords;
  - M6, no `lower()`.
- The plan's line citations and the Progress numbers.
- The docstring, `CLAUDE.md` and the `agent.py:60` schema text.

**Taken on trust:** §2's live-check observation of the model's tool call.
