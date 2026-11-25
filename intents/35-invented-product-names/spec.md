<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §35 spec — Catch an answer that names a product the catalogue does not have

Accepted intent: [intent.md](intent.md)

Written against `main` at `ac69f5b`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Questions for the owner (one round)

Each has a recommended default; the behaviours below are written with the
defaults. Answer "defaults" or name the ones to change (e.g. "Q3 b").

1. **What counts as a name (the intent's "scope" and "what is a product
   name").**
   (a, recommended) The **name slot**: the run of capitalised words (at
   most 5, a number counts) that sits directly before a cited id, with at
   most `(`, `**`, `[` or spaces between, after the last list marker, lead-in
   word or sentence break ("I recommend the", "1.", "GPS."). Names written
   with no id near them are not read.
   (b) Any capitalised phrase anywhere in the answer, id or not. Not
   advised: the replay below shows the id-anchored form has no false
   positive on 989 answers; an unanchored form has to guess at ordinary
   capitalised words.
2. **Brands and short forms.**
   (a, recommended) A run is fine when it is a whole catalogue name (that
   is `names`' business), the **own name of the cited id** or its tail
   without the brand ("Go 13" for P-009 Pelagic Go 13), or one word. A
   catalogue brand with an invented model ("Norvik Flex (P-123)") is
   invented; a brand alone ("a Kestrel model (P-123)") is one word and
   passes.
   (b) Also fail a tail without the brand.
3. **The customer's own misspelling.**
   (a, recommended) A run whose letters are within edit tolerance of the
   **cited id's own name** passes, with the model number equal ("Aurelis
   Home 1 (P-032)" passes: P-032 is the Auralis Home 1). The same
   misspelling next to a different id fails ("Aurelis Home 1 (P-012)").
   The question text is not read.
   (b) Pass any run that appears in the customer's question, whatever id
   it sits with.
4. **Extend `names` or add a check.**
   (a, recommended) A new check, `invented`, right after `names`, with its
   own reason. `names` keeps its §25 meaning ("another catalogue product's
   name") and labels, `compare` and the viewer can tell the two apart. The
   report's check list gains a name for every case.
   (b) A second failure kind inside `names`.
5. **Which cases.**
   (a, recommended) Every case, like `grounded` and `names`: it needs no
   case data, and the cases that expose it are out-of-stock ones with no
   `expect_properties`.
   (b) Opt-in with a new `expect_properties` entry. Not advised: it would
   need an edit of `PROPERTIES` and of every case that should have it, and
   the two failing cases would stay silent until someone adds it.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intent.md` | "An answer that presents a product name the catalogue does not have next to a cited id fails a deterministic check. The reason names the id, that id's real name and the name the answer used (e.g. "P-012 is the Tolvane Chrome 11, cited as Aurelis Home 2")." |
| `intent.md` | "It must not fail ordinary prose: brands, categories, feature words, bullet labels and the customer's own words." |
| `intents/25-cited-id-name-mismatch/plan.md` | `names` is a separate check from `grounded` ("A separate name lets labels, `compare` and the viewer tell an invented id from a misattributed one"); D1 (b): "a name right before the next id belongs to the next id"; D2 (b): case is folded "without changing the text's length". |
| `src/advisor/evals/score.py` | `misnamed` only sees catalogue names (`mentions` are matches of catalogue names), so a name the catalogue lacks leaves `near` empty. `score()` runs `grounded`, then `names`, then `prices`; check names are `grounded`, `names`, `prices`, `expected`, `forbidden`, `declines`, `stock`, `search`, `a-match`, `only-matches`. |
| `src/advisor/evals/cases.py` | `PROPERTIES = ("cites_a_match", "cites_only_matches")`: the only per-case switches. |
| `REVIEW-POLICY.md` → "Eval runs" | `src/advisor/evals/score.py` owes a run; "Regressions are reported, never blocking"; "The baseline moves after the merge." |
| `docs/decisions/0003-catalogue-changes.md` (via the intent) | Old run reports and labels are not re-scored or edited. |

## Evidence: replay over every stored answer

A prototype of the rule below (not the implementation) was run offline over
all 31 reports in `evals/runs/` (989 answers with text, `catalogue.json` at
`ac69f5b`; 8 reports predate the committed catalogue hash, so a name or id
may have moved: checked below).

- **41 answers in 11 reports are flagged**, naming 75 (id, name) pairs. The
  other 20 reports, **including all three Anthropic (Haiku) reports**,
  `20261124T192816Z-anthropic.json` among them,, flag none.
- I read all 41. **All 41 present a name no catalogue has**: none of the 75
  names is a product name in either committed revision of `catalogue.json`
  (checked with `git show`). None is a correct answer: all 41 already FAIL
  on `expected`, `prices` or `stock`. By case: `aurelis-home-gift-mum` 10,
  `norvik-fold-brother-gift` 6, `video-editing-laptop`, `voice-speaker` and
  `monitor-room-500` 2 each, and 19 cases once. Most of the 19 come from one
  run (`20261124T175356Z-ollama`, granite3.3:8b) that cites real ids next
  to Dell, Sony, Acer, JBL and similar products.
- In the latest run `20261124T215703Z-ollama.json` it flags exactly the
  four lines quoted by the intent: "Aurelis Home 2 (P-012)", "Aurelis Home
  3 (P-013)" (`aurelis-home-gift-mum`), "Acme Foldable (P-004)" and
  "TechFold Pro (P-007)" (`norvik-fold-brother-gift`). Both cases fail on
  `prices` and `expected` there already, so the totals (38 of 50) do not
  move on that run.
- **Four false positives were found and fixed by refining the rule** (an
  answer that is correct and was flagged by the first draft): a sentence
  lead-in taken as part of the name ("I recommend the Kestrel Air Plus
  (P-005)"), a leading article ("The Norvik Fold (P-017)"), a short form
  of the cited product's own name ("Go 13 (P-009)", "Slate 14 (P-007)"),
  and a run that began at the end of the previous sentence ("... GPS. The
  Auralis Tick S (P-025)", a PASS case). Each is a test in AC4. The rule
  is tuned on this data, so the 0 false positives is a floor on what this
  data shows, not a measure of what other models do.
- **Misses by design:** a name with no id beside it, a name in a table cell
  separated from the id by a pipe, and `P-012: Aurelis Home 2` (name after
  the id) are not read (B1). A looser first prototype (any capitalised run before an id) flagged 54
  answers, 13 more than the final rule, from lead-in words, generic labels
  ("Product ID") and short forms; those are the false positives above.

## Behaviour

- **B1. Where a name is read.** For each occurrence of a **known** cited id,
  the *name slot* is the run of words directly before it: at most 5, each
  starting with a capital letter or a digit, ending right before the id
  with only spaces, `(`, `[`, `**` and quotes between. The run stops at the
  start of the line, at a word ending in `. ! ? : ; ,`, and at any word that
  does not start with a capital or a digit. A leading "The", "A" or "An"
  and a leading list number ("1", "2") are dropped. Another cited id is
  never part of a slot. Nothing after the id is read.
- **B2. A run is not invented**, and the occurrence passes, when it has
  fewer than two words; or it is a whole catalogue name (case and hyphen
  rules of `names`); or it is the cited id's own name, or a tail of it
  made of whole words ("Go 13"); or it is within edit tolerance of the
  cited id's own name (B3).
- **B3. The customer's misspelling.** Letters may differ from the cited
  id's own name by edit similarity of at least 0.85 on the case-folded
  text, and every number in the run must equal the number in the name
  ("Aurelis Home 1 (P-032)" passes; "Aurelis Home 2 (P-032)" fails). The
  question is not an input.
- **B4. Otherwise it is invented**: a name of two to five words that is
  neither a catalogue name nor the cited product's. It fails for a catalogue
  brand with an invented model ("Norvik Flex (P-123)"), for a made-up brand
  ("Acme Foldable (P-004)") and for another maker's product ("Dell XPS 15
  (P-009)").
- **B5. The check.** `score()` adds `invented` right after `names`, for every
  case. It is `ok` when no occurrence is invented. When it fails the reason
  is "P-012 is the Tolvane Chrome 11, cited as Aurelis Home 2", several
  joined with "; ", each id once, in order of first occurrence. When it is
  `ok` the reason is "no invented product name next to a cited id".
- **B6. Independent of `names`.** An occurrence that `names` already fails
  (the run is another catalogue name) is never also `invented`. An unknown
  id (`grounded`) is not read. An answer with no id has no occurrence and
  passes.
- **B7. Pure and deterministic.** The helper (say `invented_names(answer,
  by_id)`) takes the answer text and the catalogue and nothing else: no
  model, no files, no question.
- **B8. Reports and docs.** Old run reports are not re-scored. README's
  check list gets an **invented** bullet. The case JSON, `PROPERTIES` and
  the judge are unchanged.

## Interpretations

- **"Next to a cited id" is "directly before it".** The intent's rough scan
  and its four quoted lines all put the name right before the id; a name
  after the id would also be matched by `names`' 80-character window, but
  the shape for invented names is unobserved. Code comment at the helper.
- **"Name" is a capitalised run, not a brand match.** A brand list would
  miss "Aurelis" and "Acme". The two-word minimum and the own-name rule are
  what keep brands alone and short forms out. Code comment at the slot
  regex.
- **Edit tolerance 0.85 and equal digits.** `difflib` ratio on the folded
  names: "aurelis home 1" vs "auralis home 1" is above it; the digits rule
  stops "Aurelis Home 2" slipping through on P-032, where the ratio alone
  (about 0.86) would pass it. Code comment at the comparison.
- **A trailing sentence break ends the run** ("GPS. The Auralis Tick S"),
  so a run never joins two sentences.
- **"Product name the catalogue does not have"** is read as "not a whole
  catalogue name today". A name that existed in an older catalogue is
  invented against today's (decisions/0003, old records are not re-scored).

## Acceptance criteria

- **AC1 (B1, B4, B5).** The four intent lines ("1. **Acme Foldable
  (P-004)** - 399.00", "2. **TechFold Pro (P-007)**", "- **Aurelis Home 2
  (P-012)**", "- **Aurelis Home 3 (P-013)**") each fail `invented` with the
  reason "P-004 is the Sonavo Quiet Pro, cited as Acme Foldable" and so on
  (test: `tests/test_evals_score.py`, new tests quoting the two answers of
  `20261124T215703Z-ollama.json`).
- **AC2 (B2, B3).** "Auralis Home 1 (P-032)", "Kestrel Calm 46 (P-123)",
  the customer-echo "Aurelis Home 1 (P-032)", "Go 13 (P-009)", "a Kestrel
  model (P-123)", an id with no name near it, and a name differing only in
  case or a hyphen all pass; "Aurelis Home 1 (P-012)" and "Aurelis Home 2
  (P-032)" fail (test: `tests/test_evals_score.py`).
- **AC3 (B1).** Slot edges: "I recommend the Kestrel Air Plus (P-005)",
  "The Norvik Fold (P-017)", "GPS. The Auralis Tick S (P-025)", "1. Acme
  Foldable (P-004)", a name after the id, a table cell, and a bold label
  "**Price:** (P-004)" each give the stated result (tests, each naming its
  shape).
- **AC4 (B6).** An answer that `names` fails does not also fail `invented`;
  an unknown id is left to `grounded`; no id passes (tests).
- **AC5 (B5).** `score()` returns `invented` right after `names` for every
  case, and the four lists of check names in `tests/test_evals_score.py`
  and the run tests are updated, not deleted (tests).
- **AC6 (replay).** A test reads the committed catalogue and two literal
  answers, one correct and one invented, and asserts the verdict. The
  replay over `evals/runs/` is **not** a test (the directory is gitignored);
  the review repeats it and reports the flagged count against the 41 above.
- **AC7 (B8).** README's check list has the **invented** bullet (manual
  check at review).
- **AC8 (eval run).** The 50 cases are scored with a real model per
  `REVIEW-POLICY.md` → "Eval runs"; `advisor-analysis compare` lists every
  flipped case, each explained in the review. Expected: none flips on
  qwen3:8b, since all 41 flagged answers already fail on other checks.
  A case that flips PASS to FAIL because the answer really names an
  invented product is reported as a "Needs decision", per the policy.

## Non-functional

- **Boundaries:** `src/advisor/evals/score.py` only (a pure helper next to
  `misnamed`, no new import beyond `difflib` from the standard library);
  `cases.py`, `run.py`, the judge and `tracing.py` are not touched. README's
  check list changes.
- **Data:** none; the catalogue is synthetic. Replay evidence reads only
  the committed, gitignored-by-design run reports.
- **Model use:** none in the check. The eval run owed is a model run, made
  by the coordinator on the local model.
- **Autonomy:** the check only reports a failure; it never blocks an
  answer or changes the agent.

## Out of scope

- Stopping the agent from inventing names (§31 and prompt work).
- The judge's scope (`judge-no-fit`).
- Names with no id beside them, names after the id, table cells.
- Re-scoring or editing old reports and labels.
- Reading the customer's question.

## Assumptions I made

- **The baseline.** The review's eval run stands as the new baseline after
  the merge per "The baseline moves after the merge"; the review says so.
  I expect no flip on the committed qwen3:8b reports (replay above).
- **Replay catalogue.** The 31 reports were replayed against today's
  catalogue; 8 predate its hash. Since none of the 75 flagged names is in
  any committed revision of the catalogue, a stale catalogue does not
  explain a flag. A stale catalogue could hide an old-catalogue name that
  was real then; that is not an invented name today.
- **Name length.** Two to five words; a one-word name ("Zephra") is never
  read. A real invented one-word name is missed.
- **No new dependency.** `difflib` is standard library.
- **`review_tier`** left empty: `score.py` is under `src/**` and not in the
  "by meaning" list (same as §25).
- **Feature.** The type stays as the intent set it.
