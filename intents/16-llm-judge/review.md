<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §16 review — An LLM judge for one failure mode, validated against the owner's labels

verdict: escalate
tier: reviewed
reviewed-commit: 1d79fe95fe21e1a779c0e2d94861a7bbe87f9ed1
round: 5
sampled: no
run: manual
live-check: owed

Tier: Reviewed, never lowered; set by the path table (`src/advisor/tracing.py`
in the branch diff, Reviewed by meaning) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due manual --exclude 16` →
"sample-due manual: nth attested manual change = 1, every 5, sampled: no".

Run: manual (the owner's "16 rework", then a round-5 `/review`).

Scope: `git diff 53a491d..HEAD`: 1d79fe9 (the round-4 rework) and 7ba2fd6
(round-4 `review.md`). Files: `intents/16-llm-judge/plan.md` (Progress
appended, `:230-243`), `intents/16-llm-judge/review.md`,
`tests/test_judge.py`. **No `src/` or `evals/` file changed**; `spec.md`
and `metadata.yml` unchanged; README.md and CLAUDE.md unchanged.

## Resolution of round 4
| Round 4 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| F6 MEDIUM | `_RULES` prefixes; X1, X4, X5, X6 survived (`judge-no-fit.md:11, :19, :21, :22`) | fixed | `tests/test_judge.py:140` "case something fits", `:153` "a implies a fit", `:163` "c invented details", `:167` "d assumed constraint" assert the full text of `:11, :19, :21, :22`; `:158` "b other kind" the full first sentence of `:20`. "a says nothing fits when a result does" folded into `:153`, whose line still holds it (X7 killed). X1, X4, X5, X6 KILLED. Prompt not edited |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the F6 test change and a Progress entry quoting "16 rework"; prompt and spec untouched |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: AC9 at clause level for every B3 clause in lines 8, 10, 11, 13, 15, 17, 19, 21, 22, plus (b)'s first sentence and both examples; runtime unchanged since round 3 |
| 4 | Tests prove the behaviour | findings (1): F7 LOW, two `:20` lead-in survivors, judged not AC9 rule content; every required mutant killed |
| 5 | Conventions | pass: a pure test on the committed file; no model, network or Langfuse |
| 6 | Numbers in prose | pass: "791 after", "792 before", "each fails exactly one test, 790 passed" reproduced; line numbers 11, 19–22 match |
| 7 | Documentation | pass (nothing user-facing changed) |
| 8 | Guardrails and hygiene | pass: ruff, format, mypy strict clean; no dependency, secret, user data or owner label text |
| 9 | Repository-specific footguns | pass (list empty); the round-3 proposal (stale hashes after a rebase) open, the owner's call; no new hash cited |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 16, feature)
  note:  22 file(s), 2258 line(s) changed outside intents/.
```

## Findings
- **F7 LOW** `tests/test_judge.py:161-162` (AC9, B3 b): two mutants
  survive, each dropping a lead-in of `judge-no-fit.md:20` and keeping its
  example in lowercase: B1b ("Another kind that does serve the need passes:
  "), B2b ("Another kind that does not serve it fails: "); 791 passed each.
  Judged not separate rule content: AC9 asks for "each fail reason (a) to
  (e), with the two alternative examples of (b)"; without the lead-ins the
  rule sentence and both examples are still asserted, and each example
  carries its own verdict ("… passes", "… fail"). Worth a look: asserting
  all of `:20` as one line would kill both (test-only).

**Mutants** (`src/advisor/evals/prompts/judge-no-fit.md`; byte-exact
replace asserted once, CRLF handled; backed up and restored by copy;
`git diff --quiet` ≠ 0 before and = 0 after each; full product suite, no
`-x`):

| Id | Target | Result | Killed by |
| --- | --- | --- | --- |
| X1 | `:11` "as asked." → "." | KILLED (1 failed, 790 passed) | `test_the_shipped_template_states_each_rule_of_b3[case something fits]` |
| X4 | `:19` drop the (a) parenthetical | KILLED | `…[a implies a fit]` |
| X5 | `:21` drop " (a feature, a spec, stock or a price)" | KILLED | `…[c invented details]` |
| X6 | `:22` drop " and answers within it" | KILLED | `…[d assumed constraint]` |
| P1 | `:10` drop ", or no search was run" | KILLED | `…[case nothing fits]` |
| P5 | `:8` drop "First decide…" | KILLED | `…[decide the case]` |
| X7 | `:19` drop ", or it says nothing fits when a search result does" | KILLED | `…[a implies a fit]` |
| B4 | `:20` drop " that does not serve the customer's need" | KILLED | `…[b other kind]` |
| B3 | `:20` drop the tablet sentence | KILLED | `…[b tablet example]` |
| B1 | `:20` lead-in → "A tablet" | KILLED (through the capital letter) | `…[b tablet example]` |
| B2 | `:20` lead-in → "Smartwatches" | KILLED (through the capital letter) | `…[b smartwatch example]` |
| B1b | `:20` drop the "passes" lead-in, lowercase kept | **SURVIVED** (791 passed) | F7 |
| B2b | `:20` drop the "fails" lead-in, lowercase kept | **SURVIVED** (791 passed) | F7 |
| E1 | `:23` drop the (e) line | KILLED | `…[e hides]` |
| E2 | `:23` "It hides that nothing fits." → "It hides that." | KILLED | `…[e hides]` |

The tests prove AC9's B3 rules at clause level; the only exceptions are
`:20`'s two lead-ins (F7), framing rather than rule content.

## Not checked
- P2, P4, P6 not re-run this round (killed in round 4 by the reviewer and
  the coordinator; their assertions unchanged in 1d79fe9).
- Judge output on real input: the owner's 2026-11-21 live check; no model
  called.
- `evals/judge/validation.md`, judgements and labels not recounted
  (unchanged since 241dfd9; round 3 recounted them).
- The "empty `reason` counts as a verdict" behaviour (the owner's call,
  round 2).
- `main` has moved (merge-base `480a676`; `main` now has §21 and the §15
  plan); no rebase or trial merge (read-only).
- Remote state (no upstream; not checked over the network).

## Live check
- owed: rule 1 (the branch diff touches `src/advisor/tracing.py`).
- recorded: `live_checked: 2026-11-21 by-agent` (owner: "live check
  passed") at 241dfd9. Since then only `tests/test_judge.py` and
  `intents/16-llm-judge/` changed, so **the recorded check still covers the
  reviewed runtime content**; `check:intent` passes with it.

## Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

## Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 1d79fe9; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "170 files already formatted"; mypy "Success: no
  issues found in 31 source files"; "791 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "22 file(s), 2258
  line(s)". Matches.
- **Coordinator, re-run:** the kills the rework claims: X1, X4, X5, X6 each
  KILLED (1 failed, 790 passed). Matches the reviewer and the implementer.
- **Coordinator, re-run:** survivors B1b, B2b each SURVIVED (791 passed).
  Matches the reviewer.

**Reviewer, verified:** HEAD 1d79fe9; the diff scope (3 files; nothing in
`src/` or `evals/`; spec.md and metadata.yml unchanged); verify,
check:intent, sampling, `owes-run`; the 15 mutants; no upstream; `main`
untouched.

**Taken on trust:** the P2, P4, P6 kills (round 4); the owner's
2026-11-21 live check as `metadata.yml` records it; round 3's recount of
validation.md, judgements and labels; that the §16 commits on `main` are
intent bookkeeping only (round 4).
# Round 4 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 53a491d0d3869afb38cb8eed186f7c71a8f7d2d9
- round: 4
- sampled: no
- run: manual
- live-check: owed

Tier: Reviewed, never lowered; set by the path table (`src/advisor/tracing.py`
in the branch diff, Reviewed by meaning) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due manual --exclude 16` →
"sample-due manual: nth attested manual change = 1, every 5, sampled: no".

Run: manual (the owner's `/review 16`, round 4).

Scope: `git diff 241dfd9..HEAD`: dc6e615 (round-3 `review.md`) and 53a491d
(the round-3 rework). Files: `intents/16-llm-judge/{metadata.yml,plan.md,review.md,spec.md}`
and `tests/test_judge.py`. **No `src/` and no `evals/` file changed** (`git
diff --name-only 241dfd9..HEAD -- src evals` is empty); README.md and
CLAUDE.md unchanged.

### Resolution of round 3
| Round 3 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| F1 MEDIUM | AC7: `20261116T094558Z` judgements from the pre-amendment prompt | accepted by the owner ("1. accept old files"); AC7 read as met | `plan.md:214`; file untouched since 241dfd9 |
| F2 MEDIUM | AC8: 31 of 43 refs without a post-amendment label line | accepted by the owner ("2. accept current labels") | `plan.md:215`; `evals/labels` untouched since 241dfd9 |
| F3 MEDIUM | AC9 clause survivors P1, P2, P4, P5, P6 | fixed | `tests/test_judge.py:134-158`: full sentences for `judge-no-fit.md:10, :13, :15`, new entries for `:8`, `:17`; all five KILLED. Same class, missed by round 3: X1, X4, X5, X6 survive (F6) |
| F4 LOW | E4 `"undefined"` → `"n/a"` survives | fixed | `tests/test_judge.py:375-383` `test_markdown_rate_is_undefined_with_no_owner_pass`; E4 KILLED |
| F5 LOW | stale hashes after the 2026-11-18 rebase | fixed (spec.md edit approved: "3. update them") | spec.md: exactly 4 lines (`:7, :13, :223, :230`) `403b4b5`→`aad9a13` (ancestor, same subject); metadata.yml `:9` comment only, `60635df`→`9f46347` (ancestor, same subject), gate values unchanged; plan.md `:156` five hashes, all ancestors with matching subjects. The only non-ancestor hashes left are the old→new mapping at `plan.md:218` (intended history) |
| Proposed footgun | stale cited hashes after a rebase | open, the owner's call (a policy edit is Reviewed tier) | — |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the F3/F4 tests, the F5 hash edits, a Progress entry with the owner's decisions; nothing else |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: AC7, AC8 as the owner decided; AC9 at rule level; runtime unchanged since round 3 |
| 4 | Tests prove the behaviour | findings (1): F6, clause survivors X1, X4, X5, X6 |
| 5 | Conventions | pass: no `src/` change; the new tests are pure |
| 6 | Numbers in prose | pass: "789 before, 792 after"; "each fails exactly one test, 791 passed" reproduced for P1, P2, P4, P5, P6, E4; spec line numbers match the hunks; "12 of 43 … 31" carried from round 3 |
| 7 | Documentation | pass (unchanged since round 3) |
| 8 | Guardrails and hygiene | pass: ruff, format, mypy strict clean; no dependency, secret, user data or owner label text in the diff |
| 9 | Repository-specific footguns | pass (list empty); the round-3 proposal is open |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 16, feature)
  note:  22 file(s), 2245 line(s) changed outside intents/.
```

### Findings
- **F6 MEDIUM** `tests/test_judge.py:140, :151, :156, :157` (AC9, B3; the
  same class as round-3 F3, which round 3's list missed): four `_RULES`
  entries are still prefixes of their template line, so dropping a B3 clause
  after the prefix passes the full suite (792 passed each):
  - X1 `judge-no-fit.md:11` drop " as asked" from "Something fits"
    (spec.md:98-99, "meets the request as asked");
  - X4 `:19` drop the (a) parenthetical "(it names a product that no search
    returned, or one outside the stated budget or requirement, as if it met
    the request)" (spec.md:103-105);
  - X5 `:21` drop the (c) list " (a feature, a spec, stock or a price)"
    (spec.md:111-112);
  - X6 `:22` drop " and answers within it" from (d) (spec.md:113-114).

  **Needs rework:** make the `_RULES` entries "case something fits", "a
  implies a fit" (with "a says nothing fits when a result does" folded in or
  kept), "c invented details" and "d assumed constraint" the full line text
  of `judge-no-fit.md:11, :19, :21, :22`, and the same for `:20`'s "b other
  kind" (its first sentence, "…does not serve the customer's need."), so X1,
  X4, X5, X6 are killed. Do not edit the prompt (that would owe a new live
  check). Mechanical, following the F3 precedent. If the owner reads AC9's
  "one assertion per rule" as enough, that is a decision to accept the four
  survivors instead.

**Mutants** (one change each; byte-exact replace asserting one match;
backed up and restored by copy; `git diff --quiet` ≠ 0 before each run; full
product suite `uv run pytest -q`, no `-x`):

| Id | Target | Result | Killed by |
| --- | --- | --- | --- |
| P1 | `judge-no-fit.md:10` drop ", or no search was run" | KILLED (1 failed, 791 passed) | `test_the_shipped_template_states_each_rule_of_b3[case nothing fits]` |
| P2 | `:13` drop the alternatives clause | KILLED | `…[pass when nothing fits]` |
| P4 | `:17` drop "In either case, answer FAIL…" | KILLED | `…[in either case fail]` |
| P5 | `:8` drop "First decide…" | KILLED | `…[decide the case]` |
| P6 | `:15` drop ", as the search results show them" | KILLED | `…[pass when something fits]` |
| E4 | `judge.py:266` `"undefined"` → `"n/a"` | KILLED | `test_markdown_rate_is_undefined_with_no_owner_pass` |
| X2 | `judge.py:266` guard `total == 0` → `hits == 0` | KILLED | `tests/test_analysis_judge_validate.py::test_the_report_has_the_table_both_rates_and_the_disagreements` |
| X3 | `:13` drop "plainly" | KILLED | `…[pass when nothing fits]` |
| X1 | `:11` drop " as asked" | **SURVIVED** (792 passed) | F6 |
| X4 | `:19` drop the (a) parenthetical | **SURVIVED** | F6 |
| X5 | `:21` drop the (c) list | **SURVIVED** | F6 |
| X6 | `:22` drop " and answers within it" | **SURVIVED** | F6 |

The rework must kill X1, X4, X5, X6.

### Not checked
- Clause drops inside `judge-no-fit.md:20` ((b), beyond its two examples)
  and `:23` ((e)); `:20` is covered by F6's fix.
- Judge output on real input: the owner's live check (2026-11-21); no model
  called.
- `evals/judge/validation.md`, the judgements and labels were not recounted
  (unchanged since 241dfd9; round 3 recounted them).
- The "empty `reason` counts as a verdict" behaviour (the owner's call, round
  2).
- `main` has moved (merge-base `480a676`, `main` at `eea23ee`); no rebase or
  trial merge (read-only). The `§16` commits on `main` are intent
  bookkeeping in `intents/16-llm-judge/` only.
- Remote state (no upstream; not checked over the network).

### Live check
- owed: rule 1 (the branch diff touches `src/advisor/tracing.py`).
- recorded: `live_checked: 2026-11-21 by-agent` (owner: "live check
  passed") at 241dfd9. Since then only `tests/test_judge.py` and
  `intents/16-llm-judge/` changed, so **the recorded check covers the
  reviewed runtime content**. A test-only F6 rework keeps it covered; a
  prompt edit would not.

### Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)".

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 53a491d; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "170 files already formatted"; mypy "Success: no
  issues found in 31 source files"; "792 passed". Matches the reviewer and
  the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "22 file(s), 2245
  line(s)". Matches the reviewer.
- **Coordinator, re-run:** the kills the rework claims: P1, P2, P4, P5, P6,
  E4 each KILLED (1 failed, 791 passed). Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** survivors X1, X4, X5, X6 each SURVIVED (792
  passed). Matches the reviewer.

**Reviewer, verified:** HEAD 53a491d; verify, check:intent, sampling,
`owes-run`; every F5 hash with `git cat-file -e`, `merge-base --is-ancestor`
and its subject; `git diff -U0` of spec.md and metadata.yml; the 12 mutants,
restored byte-identical (`cmp`).

**Taken on trust:** the owner's decisions as quoted in `plan.md:211`; round
3's counts behind F1 and F2; that the owner ran the 2026-11-21 live check as
the metadata records.
# Round 3 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 241dfd988e432fb18ba6256e0694531f6820bcd3
- round: 3
- sampled: no
- run: manual
- live-check: owed

Tier: Reviewed, never lowered; set by the path table (`src/advisor/tracing.py`,
Reviewed by meaning) and `review_tier: reviewed`.

Sampling: `npm run sdlc:scan -- --sample-due manual --exclude 16` →
"sample-due manual: nth attested manual change = 1, every 5, sampled: no".

Run: manual (the owner's `/review 16`); the `/auto 16` run stays at round 2,
stopped at "live check owed".

Scope: the whole change against the amended spec (B1–B11, AC1–AC9), focused
on `git diff 50887b2..HEAD`: the round-2 rework (af036fe), the widened prompt
and the AC9 test (140467c), the rate-count fix (e172c01), the live-check data
(aad9a13, 798fc74, 241dfd9) and the spec amendment (9f46347, bbde313).

The branch was rebased again after round 2 (main 480a676; every branch
commit's committer date 2026-11-18 13:58). The §16 patch on `src`, `tests`,
`CLAUDE.md` and `README.md` is identical before (`1687047..28aa68c`) and
after (`480a676..50887b2`): 1975 added and removed lines each, `diff` empty.

### Resolution of round 2
| Round 2 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| LOW | M10b chained replace survives | fixed | `tests/test_judge.py:109-115`; M10b KILLED by `test_a_slot_inside_a_conversation_is_not_filled_again` |
| LOW | stale docstrings (`analysis.py`, `annotate.py:3`) | fixed | module docstring, exit codes and `_LANGFUSE_ENV` comment (`:76-77`) name `judge`; `annotate.py:3-7` names the judge score config and batch writes |
| LOW (worth a look) | `judging.LANGFUSE_ENV` a third copy | taken | `tests/test_boundaries.py:211-215`; L1 (drop `LANGFUSE_HOST`) KILLED by `test_judging_langfuse_variables_match_the_tracing_module` |
| LOW (worth a look) | empty `reason` counts as a verdict | left, the owner's call (plan.md, round-2 rework entry) | `judge.py` unchanged; under Not checked |
| LOW (worth a look) | `plan.md:156` pre-rebase hashes | fixed in af036fe, **stale again** after the 2026-11-18 rebase | F5 |
| Needs decision | live check before round 3 | resolved: live check first (owner: "16 live check first", ce05c08) | this round reviews the LOW fixes and the live-check files together |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the four rework items, the B3 template plus AC9 test and README paragraph, the `_rate` fix, the live-check data, gates and metadata; no unplanned scope |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (2): F1 (AC7, the 094558Z judgements), F2 (AC8 relabel evidence) |
| 4 | Tests prove the behaviour | findings (2): F3 (prompt clauses P1, P2, P4, P5, P6), F4 (E4 `"undefined"`) |
| 5 | Conventions | pass: `langfuse` only in `tracing.py`; the model faked in every test; no network in verify |
| 6 | Numbers in prose | findings (1): F5 cited hashes not on the branch |
| 7 | Documentation | pass: README "LLM judge" describes the nothing-fits / something-fits split; CLAUDE.md already describes the judge |
| 8 | Guardrails and hygiene | pass: ruff, format, mypy strict clean; no new dependency; no key, token or email in the data files; no model text reaches a shell, SQL or HTML |
| 9 | Repository-specific footguns | pass (list empty); proposed addition under Findings |

Pass 3 detail: B1–B2, B4–B6, B8–B11 unchanged since round 2. B3/AC9: the
template (`src/advisor/evals/prompts/judge-no-fit.md:8-22`) states both
cases, both pass rules, fail reasons (a)–(e) and both (b) examples. B7:
`judge.py:264-266`, `:294-297` print each rate from the table's counts. The
committed `validation.md` is consistent with the labels: 35 held out, 33 with
a verdict, 2 errors; TPR 0.52 (11/21), TNR 0.75 (9/12); a recount of the
current owner labels of the 35 held-out refs gives 23 pass, 12 fail; verdict
"not trusted" with both reasons (AC7 allows either); B7's minimums hold (33 ≥
30, 12 ≥ 10). Prompt hash `a6cff797…005f`, recomputed from the committed
template, `split.json` and labels, equals `validation.md`'s and every line of
`evals/judgements/20261116T094326Z-ollama.jsonl`.

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 16, feature)
  note:  22 file(s), 2223 line(s) changed outside intents/.
```

### Findings
- **F1 MEDIUM** `evals/judgements/20261116T094558Z-ollama.jsonl`: amended AC7
  says "`judge` on both 2026-11-16 reports … run again and the new …
  judgements are committed". This file was last changed in aad9a13: its 6
  lines have `judged_at` 2026-11-16T11 and `prompt_sha256` `f491bbc2…9461`,
  the pre-amendment prompt; the current one is `a6cff797…`. Only
  `20261116T094326Z` was re-judged on 2026-11-21. So 6 committed verdicts,
  and their `judge-no-fit` scores in Langfuse, come from the old criterion;
  `judge-validate` is unaffected (it re-judges the held-out set itself).
  **Needs decision:** re-run `uv run advisor-analysis judge
  evals/runs/20261116T094558Z-ollama.json` and commit the file (another
  review round: ship refuses changed files), or accept the stale file and
  read AC7 as met, saying so in metadata or the plan.
- **F2 MEDIUM** `evals/labels/*.jsonl` against amended AC8 ("the owner
  relabels the 43 conversations in `split.json` … the new label lines are
  committed"). Only 12 of the 43 refs have a label line written after the
  amendment was accepted (bbde313, 2026-11-16 13:09 +0100): the 12 in
  `20261113T072503Z-ollama.jsonl` (798fc74). The other 31: 5 in
  `20261113T070516Z-anthropic.jsonl` (1 few-shot, 4 held out; no traces, so a
  relabel would go through `view`, which appends a line) have only their
  2026-11-13 lines; 26 in the two 2026-11-16 reports have only lines from
  11:02–11:17Z, before the amendment draft, and `import` skips a score equal
  to the current label (`annotate.py:224-227`), so an unchanged relabel
  leaves no trace. **Needs decision:** confirm whether these 31 were judged
  again under amended B3; if not, relabel them (then a new `judge-validate`
  and another round), or accept the current labels and note it against AC8.
- **F3 MEDIUM** `tests/test_judge.py:134-152` (AC9): dropping a whole rule
  line is killed (P3, P7 and the implementer's 12 drops); dropping a clause
  inside a rule survives the full suite. These clauses are B3 content:
  - P1 ", or no search was run" (`judge-no-fit.md:10`);
  - P2 "and offers only alternatives that serve the customer's need, or
    none" (`:13`, the nothing-fits pass rule);
  - P6 ", as the search results show them" (`:15`);
  - P4 the "In either case, answer FAIL…" line (`:17`), which applies
    (a)–(e) to both cases;
  - P5 "First decide from the search results which case you are in" (`:8`).

  **Needs rework:** make the `_RULES` phrases for "case nothing fits", "pass
  when nothing fits" and "pass when something fits" the full sentences of
  `judge-no-fit.md:10`, `:13` and `:15`, and add one entry each for the `:8`
  and `:17` lines, so P1, P2, P4, P5 and P6 are killed.
- **F4 LOW** `src/advisor/evals/judge.py:266`: mutant E4 (`"undefined"` →
  `"n/a"`) survives (789 passed); no test asserts what `validation.md` prints
  for a rate without a denominator (removing the guard, E4b, is killed by a
  ZeroDivisionError). **Needs rework:** in `test_judge.py`, call
  `validation_markdown` on a table with no owner pass and assert `"owner
  pass): undefined"` is in the text.
- **F5 LOW** stale commit hashes after the 2026-11-18 rebase; none is an
  ancestor of HEAD (post-rebase equivalents by subject in brackets):
  - `plan.md:156` (Progress): `a98c115`→`5fa5f52`, `4f16caa`→`611d990`,
    `8c24a35`→`ea6d6a0`, `8e6fbac`→`5e2c032`, `97f7cf6`→`8b1e194`.
    **Needs rework** (below the Progress marker, mechanical).
  - `spec.md:7, :13, :223, :230`: `403b4b5`→`aad9a13`; `metadata.yml:9`
    (comment): `60635df`→`9f46347`. **Needs decision** for `spec.md` (above
    Progress, owner-accepted): leave as history, or update.
- **Proposed footgun** (pass 9, the owner's: a policy edit is Reviewed
  tier): "commit hashes cited in intent artefacts go stale when a branch is
  rebased" (recurred in §16 rounds 2 and 3). One option: a `check:intent`
  note for cited hashes that are not ancestors of the branch.

**Mutants** (one change each, backed up and restored by copy; full product
suite, `uv run pytest -q`, `-x` unless noted; `git diff --quiet` ≠ 0 asserted
before each run):

| Id | Target | Result | Killed by |
| --- | --- | --- | --- |
| E1 | `judge.py:266` print the reduced `Fraction` (reverts e172c01) | KILLED (no `-x`: 2 failed, 787 passed) | `test_markdown_rates_show_the_table_counts_not_a_reduced_fraction`, `test_trusted_at_exactly_0_8_30_and_10` |
| E2 | `judge.py:297` TNR denominator `a.judged` | KILLED | `test_the_report_has_the_table_both_rates_and_the_disagreements` |
| E3 | `judge.py:295` TPR denominator `pp+fp` | KILLED | same |
| **E4** | `judge.py:266` `"undefined"` → `"n/a"` | **SURVIVED** | F4 |
| E4b | `judge.py:266` no zero guard | KILLED | `test_a_held_out_conversation_without_its_run_report_is_skipped_not_judged` |
| E5 | `judge.py:266` `.2f` → `.1f` | KILLED | `test_the_report_has_the_table_both_rates_and_the_disagreements` |
| M10b | `judge.py:96` chained replace, conversation first (round-2 survivor) | KILLED | `test_a_slot_inside_a_conversation_is_not_filled_again` |
| L1 | `judging.py:41` drop `LANGFUSE_HOST` | KILLED | `test_judging_langfuse_variables_match_the_tracing_module` |
| **P1** | `judge-no-fit.md:10` drop ", or no search was run" | **SURVIVED** | F3 |
| **P2** | `judge-no-fit.md:13` drop the alternatives clause | **SURVIVED** | F3 |
| P3 | `judge-no-fit.md` drop the (c) line | KILLED | `test_the_shipped_template_states_each_rule_of_b3[c invented details]` |
| **P4** | `judge-no-fit.md:17` drop "In either case…" | **SURVIVED** | F3 |
| **P5** | `judge-no-fit.md:8` drop "First decide…" | **SURVIVED** | F3 |
| **P6** | `judge-no-fit.md:15` drop ", as the search results show them" | **SURVIVED** | F3 |
| P7 | `judge-no-fit.md` drop the (d) line | KILLED | `test_the_shipped_template_states_each_rule_of_b3[d assumed constraint]` |

The rework must kill P1, P2, P4, P5, P6 (`judge-no-fit.md:10, :13, :17, :8,
:15`) and E4 (`judge.py:266`). The e172c01 fix is proved (E1); the round-2
rework is proved (M10b, L1).

### Not checked
- The model's judgements: no model was called; that Haiku's committed
  verdicts are its replies, and that Langfuse showed scores, comments and no
  duplicates, are the owner's live-check claims.
- Whether the 6 traces of `20261116T094558Z` still carry old-prompt
  `judge-no-fit` scores in Langfuse (not queried).
- Whether the owner relabelled the 31 refs without changing them (F2; git
  can't show it).
- The amendment's "4 of 26 verdicts flipped between two `judge` runs": only
  the last run's file is committed.
- The amendment's list of budget-too-low cases where a fitting product was
  returned: the run reports' tool rows were not opened per case.
- Still open from round 2: an empty `reason` (the owner's call); `system=""`
  and `tools=[]` with Anthropic; the server-side upsert on score `id`;
  non-`ModelError` client exceptions.
- Round-1 and round-2 killed mutants other than M10b: not re-run (code
  unchanged; the rebase kept the patch identical).
- What `1687047..480a676` brought in from main: reviewed under its own
  intents; only `verify` covers the interaction.

### Live check
- owed: rule 1 (the change touches `src/advisor/tracing.py`) and rule 3 (paid
  model output, the Langfuse batch-score endpoint); spec AC7, AC8.
- **recorded:** `live_checked: 2026-11-21 by-agent` (owner: "live check
  passed") in 241dfd9 (HEAD). e172c01, the last code change, precedes it;
  241dfd9 changes only `evals/judge/validation.md`,
  `evals/judgements/20261116T094326Z-ollama.jsonl` and `metadata.yml`.
  `validation.md` shows the unreduced counts (11/21, 9/12), so
  `judge-validate` ran on the e172c01 code, with the prompt hash recomputed
  from the committed template and split.
- **Coverage:** the code, yes. The data has one gap: the 094558Z judgements
  were not re-run under the widened prompt (F1). A rework that changes only
  tests and `plan.md` leaves the recorded check covering the runtime; a
  re-run of `judge` on 094558Z is part of AC7 and its file needs review.
- steps (only if the owner closes the F1 gap):
  1. In `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge`, with
     `.env` holding `ANTHROPIC_API_KEY` and the three `LANGFUSE_*`, and
     Langfuse up: `uv run advisor-analysis judge
     evals/runs/20261116T094558Z-ollama.json`.
  2. You should see 6 `PASS|FAIL|ERROR` lines and `judge-no-fit: 6 scored, 0
     no trace` (or the actual count); in Langfuse, one `judge-no-fit` score
     per trace with the new reason as its comment; in
     `evals/judgements/20261116T094558Z-ollama.jsonl`, `prompt_sha256`
     `a6cff79749036f5a24cd6f6bacf3cc43101d04ebdc24dfdee13933a56e9f005f` on
     every line.
  3. Commit the file.

### Eval run
not owed (no listed path): `uv run advisor-analysis owes-run --base main` →
"not owed (no listed path changed)". The judge prompt is under
`src/advisor/evals/prompts/`, not `src/advisor/prompts/`.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in the worktree at 241dfd9; `git status --short`
clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit "tests 298", "fail 0";
  "All checks passed!"; "170 files already formatted"; mypy "Success: no
  issues found in 31 source files"; "789 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "22 file(s), 2223
  line(s)". Matches.
- **Coordinator, re-run:** survivors P1, P2, P4, P5, P6
  (`judge-no-fit.md`) and E4 (`judge.py:266`) each SURVIVED the full product
  suite (789 passed). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, `owes-run`, sampling; the
rebase patch comparison; commit order (e172c01 09:37 before 241dfd9 09:47);
main 480a676 an ancestor of HEAD; no remote branch for `feat/16-llm-judge`;
label timestamps per split ref (counts only) and the held-out owner totals
against `validation.md`; `judged_at`, model and `prompt_sha256` of both
judgements files; the prompt hash recomputed (run reports read-only from the
main checkout's `evals/runs/`); 15 mutants as tabled; no model, Langfuse or
network call.

**Taken on trust:** the owner's live-check observations in Langfuse; that
the committed verdicts are Haiku's replies; the amendment's flip count;
rounds 1 and 2's kills on unchanged code; Anthropic accepting `system=""`;
Langfuse upserting on score `id`.
# Round 2 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 28aa68c1138c56c2f79d91ba295bf651d26cd8ce
- round: 2
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed (path table: `src/advisor/tracing.py` by meaning;
`review_tier: reviewed`).

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 16` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Scope: the rework 6eb1645 and 28aa68c (`auto_round: 2`). The branch was
rebased onto `main` (1687047) before this round, which brought in §13's
merged code; `git range-diff` and a normalised patch comparison show the
§16 `src`/`tests` patches unchanged by the rebase. 699 tests = 624 on
`main` + 70 (round 1) + 5 (rework).

### Round-1 findings: resolution
| Round 1 | Finding | Resolution | Evidence |
| --- | --- | --- | --- |
| HIGH | M30 undefined TPR could come out trusted | fixed | `test_no_owner_pass_means_undefined_tpr_and_not_trusted` (`tests/test_judge.py:268`); M30, M30b KILLED |
| MEDIUM | few-shot scope not enforced | fixed | `judging.py:133-137` `InputError`; `test_an_out_of_scope_few_shot_case_exits_2_before_any_call`; FS KILLED |
| MEDIUM | G12 partial Langfuse config | fixed | `test_a_partial_langfuse_configuration_writes_the_file_only`; G12 KILLED |
| LOW | M15 `parse_ref` empty parts | fixed | `#c`, `f#` in `test_duplicates_and_bad_refs_are_errors`; M15, M15a, M15b KILLED |
| LOW | stale texts (CLAUDE.md, two tracing.py docstrings) | fixed | all three mention `judge` and the score writes; more of the same class remains (below) |
| worth a look | M10 slot order | taken, partly proved | one `re.sub` pass at `judge.py:94-96`; M10a KILLED, M10b SURVIVED (below) |
| worth a look | `prompt_sha256` per run | taken | README states it |
| worth a look | verdict without `reason` | taken | `judge.py:123-126` → `JudgeError`; consistent with B4 ("anything else is a judge error") and AC3; R1-R3 KILLED |
| worth a look | `CLAUDE.md` prompt path | taken | `src/advisor/evals/prompts/*.md` |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| 2 | Type check | FAIL on the owed live check only (the owner's) |
| 3 | Behaviour against the spec | pass (B6 scope enforced; B4 reason rule) |
| 4 | Tests prove the behaviour | findings (1): M10b |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (624 + 75 = 699) |
| 7 | Documentation | findings (1): stale docstrings |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 16, feature)
  error: A live check is owed and not recorded. Do the steps in intents/16-llm-judge/review.md → ## Live check, then set live_checked: <date> in intents/16-llm-judge/metadata.yml.
  note:  16 file(s), 1998 line(s) changed outside intents/.
```
FAIL only on the owed live check.

### Findings
- **LOW** `tests/test_judge.py:109-112`: M10b (chained replace,
  conversation first, at `judge.py:96`) survives; the comment at
  `judge.py:95` claims a slot-like string inside the conversation is never
  replaced, but no test puts `[[examples]]` in a conversation. **Needs
  rework:** add `[[examples]]` to the conversation in
  `test_a_slot_inside_a_conversation_is_not_filled_again` and assert the
  text appears exactly once, unchanged.
- **LOW** stale docstrings still naming only `queue` and `import`:
  `src/advisor/evals/analysis.py:5-7`, `:9-12` (Langfuse-error exit codes;
  `judge` exits 2 too), `:65`, and `src/advisor/evals/annotate.py:3` (the
  protocol now has the judge-score methods). **Needs rework:** name
  `judge` and the judge score in those four places.
- **LOW** (worth a look) `judging.py:41`: `LANGFUSE_ENV` is a third copy of
  the variable names with no test against `tracing.REQUIRED_ENV`; reuse
  `analysis._LANGFUSE_ENV` or add it to `tests/test_boundaries.py`.
- **LOW** (worth a look) `judge.py:124-126`: an empty or whitespace
  `reason` is still a verdict.
- **LOW** (worth a look) `plan.md:156`: the Progress entry cites the
  pre-rebase hashes.
- **Coordinator, sequencing.** Needs decision: the live check's step 7
  commits `evals/judge/split.json` (with the new held-out labels),
  `validation.md` and the judgements to the branch, and ship refuses files
  changed after the reviewed commit, so they must be reviewed. Round 3 is
  the last `/auto` round. Either round 3 now reviews only the two LOW
  fixes and the live-check files later need a review by hand, or the
  owner does the live check first and round 3 reviews the LOW fixes and
  the live-check files together.

**Mutants** (one change each, full suite, backup and restore by copy):

| Id | Target | Result | Killed by |
| --- | --- | --- | --- |
| M30 / M30b | `judge.py:239-241` | KILLED | test_no_owner_pass_means_undefined_tpr_and_not_trusted |
| G12 | `judging.py:258` | KILLED | test_a_partial_langfuse_configuration_writes_the_file_only |
| M15 / M15a / M15b | `judge.py:154` | KILLED | test_duplicates_and_bad_refs_are_errors |
| FS | `judging.py:133` | KILLED | test_an_out_of_scope_few_shot_case_exits_2_before_any_call |
| M10a | `judge.py:96` examples first | KILLED | test_a_slot_inside_an_example_is_not_filled_either |
| **M10b** | `judge.py:96` conversation first | **SURVIVED** | (finding) |
| M10c | regex only `[[examples]]` | KILLED | many test_analysis_judge tests |
| M10d | conversation stripped | SURVIVED, equivalent in effect | – |
| R1 / R2 / R3 | `judge.py:124-126` | KILLED | test_anything_else_is_a_judge_error, test_valid_verdicts |

### Not checked
- Real Haiku output (how often a reply lacks `reason`, now an ERROR);
  `system=""`, `tools=[]` with Anthropic.
- The Langfuse batch score `POST`, upsert on `id`, server-side
  `config_id` validation, §10's `import` ignoring judge scores live.
- `validation.md` (not produced; 9 held out, 6 pass / 3 fail).
- `judge` over a few-shot example's own report; non-`ModelError` client
  exceptions; an empty `reason`.
- Round 1's 66 killed mutants not re-run (code unchanged across the
  rebase); §13's code brought in by the rebase (reviewed under §13).

### Live check
- owed: rule 1 (`src/advisor/tracing.py`) and rule 3 (paid model output;
  the Langfuse batch-score endpoint and upsert). Spec AC7, AC8.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge`: `.env`
     with `ANTHROPIC_API_KEY` and the three `LANGFUSE_*`; Langfuse up; pass
     `--runs-dir ../product-advice-agent/evals/runs` (or copy
     `20261113T072503Z-ollama.json` and `20261113T070516Z-anthropic.json`
     into the worktree's `evals/runs/`).
  2. Label more in-scope conversations: `uv run advisor-eval` (Langfuse
     on); `uv run advisor-analysis queue evals/runs/<report>.json --scenario
     no-match`, then `--scenario budget-too-low`; label in Langfuse; `uv run
     advisor-analysis import …`; until `held_out` in `evals/judge/split.json`
     holds ≥30 conversations with ≥10 fails.
  3. `uv run advisor-analysis judge evals/runs/<traced report>.json`.
  4. The same command again.
  5. `uv run advisor-analysis import evals/runs/<that report>.json`.
  6. `uv run advisor-analysis judge-validate`.
  7. Commit `evals/judge/split.json`, `evals/judge/validation.md`,
     `evals/judgements/<report>.jsonl` before the final review round.
- you should see: step 3, one `PASS|FAIL|ERROR <case>: <reason>` line per
  no-match / budget-too-low case (a reply without `reason` shows as an
  ERROR saying the JSON has no string reason; note how many), `wrote N
  verdicts …`, `judge-no-fit: K scored, k no trace`, no key printed; in
  Langfuse one BOOLEAN `judge-no-fit` score per judged trace (source API,
  reason as comment), in no queue, and one `judge-no-fit` config. Step 4:
  still one score per trace. Step 5: no label from a judge score. Step 6:
  the table, both rates `0.xx (a/b)`, errors, model, prompt hash, ≥30
  held out, trusted or not with the reason, every disagreement. A
  score-batch 4xx (`Langfuse score-write failed: …`, keys as `***`) or a
  high ERROR rate is a defect.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge` at 28aa68c; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "158 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "699 passed". Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL only on the owed
  live check, "16 file(s), 1998 line(s)". Matches.
- **Coordinator, re-run:** M30 KILLED by
  test_no_owner_pass_means_undefined_tpr_and_not_trusted; G12 KILLED by
  test_a_partial_langfuse_configuration_writes_the_file_only; M15 KILLED by
  test_duplicates_and_bad_refs_are_errors; FS KILLED by
  test_an_out_of_scope_few_shot_case_exits_2_before_any_call ("1 failed,
  698 passed" each); M10b SURVIVED ("699 passed"). Matches the reviewer
  and the implementer.

**Reviewer, verified:** verify, check:intent, the rebase (range-diff and
patch comparison), the 624 base on `main`, the rework diff in full, the
intent folder edits, 14 mutants, B4/AC3 against the spec and the prompt.

**Taken on trust:** round 1's 66 kills on unchanged code; Anthropic
accepting `system=""`; the Langfuse server upserting on score `id`.

# Round 1 (history)


- verdict: rework
- tier: reviewed
- reviewed-commit: 7f4a05313038cda2ec761ed28f4ae3cc0367b3b6
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, by the path table (`src/advisor/tracing.py`, by meaning)
and `review_tier: reviewed`; the HIGH finding would raise it anyway.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 16` →
"sample-due auto: nth attested auto change = 5, every 3, sampled: no".

Divergences from the plan, all acceptable (no decision needed): the prompt
sits at `src/advisor/evals/prompts/judge-no-fit.md` beside §9's prompts
(`evals/prompts/` does not exist; the intent says "like §9's"); command
bodies in a new `judging.py` (`judge.py` stays pure, `langfuse` stays in
`tracing.py`); test-seam options `--labels-dir`, `--runs-dir`,
`--judgements-dir` with the repo paths as defaults; B7's minimums count
conversations with a verdict (stricter than the spec's wording).

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (divergences above) |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (1): B6 few-shot scope |
| 4 | Tests prove the behaviour | findings (3 non-equivalent survivors, 1 equivalent) |
| 5 | Conventions | pass (injected client and annotations factories; sockets blocked) |
| 6 | Numbers in prose | pass (608 → 678; split 8 + 9) |
| 7 | Documentation | findings (stale texts) |
| 8 | Guardrails and hygiene | pass (fake keys only; redaction proven) |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 16, feature)
  note:  16 file(s), 1935 line(s) changed outside intents/.
```

### Findings
- **HIGH** `src/advisor/evals/judge.py:236-237`: M30 survives. Without the
  "true-positive rate is undefined" reason, a held-out set with ≥30 owner
  fails and no owner pass comes out **trusted**. **Needs rework:** add to
  `tests/test_judge.py` an agreement over 30 owner fails and 0 owner passes
  that asserts not trusted and "undefined" among the reasons.
- **MEDIUM** `src/advisor/evals/judging.py:123-135`: B6 "Only in-scope
  conversations with a current owner label are used", but `_examples` never
  checks scope for a few-shot entry, so an out-of-scope entry in the
  hand-edited `split.json` enters the prompt silently. **Needs rework:** in
  `_examples`, an out-of-scope few-shot case is an `InputError` (exit 2),
  like a missing report; add a test.
- **MEDIUM** `src/advisor/evals/judging.py:253`: G12 (`all` → `any` over the
  three `LANGFUSE_*` variables) survives. With a partial configuration B8
  wants the file only and the "not configured" line. **Needs rework:** a
  judge test with two of the three variables set: exit 0, the "Langfuse is
  not configured" line, annotations factory never called.
- **LOW** `src/advisor/evals/judge.py:151`: M15 (`parse_ref` accepting `#c`
  or `f#`) survives. **Needs rework:** `#c` and `f#` → `SplitError` in
  `test_duplicates_and_bad_refs_are_errors`.
- **LOW** stale texts: `CLAUDE.md:182-183` (analysis imports
  `advisor.tracing` "only inside `queue` and `import`", now also `judge`);
  `tracing.py:195-197` `LangfuseAnnotations` docstring ("never updates or
  deletes anything"; it now writes scores, replaced by id on rerun);
  `tracing.py:402` `make_annotations` docstring ("`queue` and `import`").
  **Needs rework:** mention `judge` and the score writes in all three.
- **LOW** (worth a look) `judge.py:93-95`: the comment says the slot order
  keeps a slot-like string in a conversation from being replaced, but a
  few-shot example containing `[[conversation]]` would be (M10 equivalent
  for the tests). Fill both slots in one pass or reword the comment.
- **LOW** (worth a look) `judging.py:146-149`: `prompt_sha256` hashes the
  template with the examples and an open conversation slot (one hash per
  run), not B5's per-case filled template; sensible for B7, but not listed
  as a divergence or in README.
- **LOW** (worth a look) `judge.py:122-123`: `{"pass": true}` without a
  `reason` is a verdict with an empty reason; B4 reads "anything else is a
  judge error".
- **LOW** (worth a look, pre-existing) `CLAUDE.md:186` says the prompts are
  `evals/prompts/*.md`; they are under `src/advisor/evals/prompts/`.

**Mutants** (70; one change each, full suite, backup and restore by copy):
66 KILLED, 4 SURVIVED. Survivors: M30 `judge.py:237` (HIGH), G12
`judging.py:253` (MEDIUM), M15 `judge.py:151` (LOW), M10 `judge.py:95`
(equivalent for the tests). Killed, among others: scope widened/narrowed
(M01-M03); conversation rows/answer/failed call/no search (M04-M07);
critique and label in examples (M08-M09); verdict non-boolean/non-object
(M11-M12); random or stamp-less score id (M13-M14, T04); split rules
(M16-M21); error counted as fail (M22, G09, G18); every 0.8/30/10 boundary
(M23-M29); undefined TNR (M31); provider not pinned, key check moved or
dropped, `--model` ignored (G01-G04); few-shot leaking held-out (G07);
`ModelError` uncaught (G08); untraced or errored cases scored (G10-G11);
jsonl appended (G13); validate inversions (G15-G17); dispatch (A01-A02);
tracing score fields, name, `queue_id`, data type, source, config, batch
size, rejected>0, `_call` and redaction (T01-T16).

### Not checked
- Real Haiku output on the prompt; `system=""` and `tools=[]` with
  Anthropic (the same call shape as `generate`/`taxonomy`).
- Whether self-hosted Langfuse accepts the SDK 5.2.0 batch score `POST`
  and upserts on a repeated `id` (B9); server-side `config_id` validation.
- Whether §10's `import` ignores `judge-no-fit` scores on a live server
  (reasoned from the code: no queue, another name).
- `validation.md` (not yet produced); the held-out set is 9 conversations
  (6 pass, 3 fail), so "trusted" needs ~21 more labels with ≥7 fails (AC8).
- `judge` over the report a few-shot example came from (the judge sees its
  own example); non-`ModelError` exceptions from a client.

### Live check
- owed: rule 1 (`src/advisor/tracing.py`) and rule 3 (paid model output;
  the Langfuse batch-score endpoint and upsert). Spec AC7, AC8.
- steps:
  1. In `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge`, `.env`
     with `ANTHROPIC_API_KEY` and the three `LANGFUSE_*`; Langfuse up. Use
     `--runs-dir ../product-advice-agent/evals/runs` (the few-shot reports
     `20261113T072503Z-ollama.json` and `20261113T070516Z-anthropic.json`
     are there) or copy them into the worktree's `evals/runs/`.
  2. Label more in-scope conversations: `uv run advisor-eval` (Langfuse
     on), `uv run advisor-analysis queue evals/runs/<report>.json --scenario
     no-match` and `--scenario budget-too-low`, label in Langfuse, `uv run
     advisor-analysis import …`; repeat until `held_out` in
     `evals/judge/split.json` holds ≥30 conversations with ≥10 fails
     (`<labels file>#<case id>` entries).
  3. `uv run advisor-analysis judge evals/runs/<traced report>.json`.
  4. The same command again.
  5. `uv run advisor-analysis import evals/runs/<that report>.json`.
  6. `uv run advisor-analysis judge-validate`.
  7. Commit `evals/judge/split.json`, `evals/judge/validation.md`,
     `evals/judgements/<report>.jsonl` (before the final round, so they are
     reviewed content).
- you should see: step 3, one `PASS|FAIL|ERROR <case>: <reason>` line per
  no-match / budget-too-low case, `wrote N verdicts …`, `judge-no-fit: K
  scored, k no trace`, no key printed; in Langfuse one BOOLEAN
  `judge-no-fit` score (source API, reason as comment) per judged trace,
  in no queue, and one `judge-no-fit` config. Step 4: still one score per
  trace, same `K scored`. Step 5: no label line from a judge score. Step
  6: the table, both rates as `0.xx (a/b)`, errors, model, prompt hash,
  ≥30 held out, trusted or not trusted with the reason, every
  disagreement. A score-batch 4xx shows as `Langfuse score-write failed:
  …` with `***` for keys, and is a defect.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/16-llm-judge` at 7f4a053; `git status --short` clean before and after):
- **Coordinator, re-run:** `npm run verify` → kit 255 tests, 0 fail; "All
  checks passed!"; "144 files already formatted"; mypy "Success: no issues
  found in 29 source files"; "678 passed". Matches the reviewer and the
  implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, "16 file(s), 1935
  line(s)". Matches.
- **Coordinator, re-run:** M30, G12, M15 and M10 each SURVIVED ("678
  passed"). Matches the reviewer.

**Reviewer, verified:** verify, check:intent, 70 mutants, the SDK 5.2.0
`CreateScoreRequest` fields and `ScoresClient.create` return types, the
split (17 in-scope conversations, 8 + 9, no shared question text), the
608 baseline on `main` by `pytest --collect-only`, no real client in any
test, plan.md edits below Progress only.

**Taken on trust:** Anthropic accepting `system=""` live; the Langfuse
server upserting on score `id`.
