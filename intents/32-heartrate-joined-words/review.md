<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §32 review — Product search treats "heartrate" and "heart-rate" as different words

verdict: attest
tier: attested
reviewed-commit: 6bf7a125cc75c26c4876b1623aedcb62d0b42817
main: 4869771
round: 1
sampled: yes
run: auto
live-check: not-needed

The reviewer examined `37a196d`. Since then the branch gained only two kinds
of change: the merge of `main` (`intents/` files of other intents) and
`63a54f9`, the owner's rewording of the intent's Outcome 3 (`intent.md`
only, see finding 1). `git diff 37a196d HEAD -- src tests` is empty.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass, after the owner's decision on finding 1 |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass: every changed site uses one `fold`; the eval run is below |
| 4 | Tests prove the behaviour | pass: 15 of 15 mutants killed |
| 5 | Conventions | pass |
| 6 | Numbers in prose | one LOW finding |
| 7 | Documentation | pass: `CLAUDE.md:164` claims are true |
| 8 | Guardrails and hygiene | one LOW finding |
| 9 | Repo-specific footguns | pass (the list is empty) |

Tier: the paths decide. `src/advisor/catalogue.py`, `src/advisor/evals/*.py`
and tests are Attested; `CLAUDE.md` and `intents/**` are Automated;
`review_tier` is empty. No CRITICAL or HIGH finding, so nothing raises it.

## Type check

```
type-check: PASS (intent 32, fix)
  note:  8 file(s), 150 line(s) changed outside intents/.
```

## Findings

1. **MEDIUM, resolved by the owner** `src/advisor/catalogue.py:172-173`
   (Outcome 3): "no match is lost" held as a set and on every recorded call
   (927 replayed, 0 lost) but not literally at the result limit. Over
   11,043 probe searches (every description word and adjacent pair, with and
   without a category) 34 change and 9 drop a previously returned product at
   limit 10: `4K` (x2), `6K` (x2), `GB`, `HD`, `TB` (x2), `at` with
   camera. For `["HD"]` with no category, 8 of the old 10 are displaced by
   cheaper smartwatches whose "1.2 inch display" folds to "...hd...". The
   relative order of the old matches is kept. The plan disclosed the extra
   matches but not the displacement.
   Resolution: the owner chose option A on 2026-11-25 ("32 A"): accept it,
   no ranking change. Outcome 3 was reworded in `63a54f9` to "every product
   a keyword search matches today is still matched, whatever the limit",
   and to say that at the limit a cheaper new match can displace an old one.
2. **LOW** `src/advisor/evals/score.py:138` with `cases.py:91-94`: a
   `keywords_any` entry in a case that is only separators (`" "`, `"-"`)
   folds to `""` and now satisfies `_call_satisfies` for any call with a
   string keyword (before, `_norm` gave `" "`, which needed a space or hyphen
   in the call keyword). No committed case has one. Worth a look: `_search`
   could reject a keyword whose fold is empty.
3. **LOW** `plan.md` (Measured, Progress): replay numbers differ between the
   plan and Progress. 44 calls raise, not 43 (Progress says so). The
   five-word heartrate search goes 0 to 10 in the plan and 0 to 5 in
   Progress: the recorded call has no `limit`, so it is 5 under
   `search_products`' default and 10 under the tool's. Both are right.
4. Nits: tests, code, docs and Progress landed in one commit (`f1c595c`);
   `CLAUDE.md:164` is one 235-character line among wrapped neighbours; T9's
   mixed-list assertion gives the same order on `main` (its first assertion
   and T6 carry the proof).

## Mutations

Reviewer: 15 mutants, one per changed behavioural line, each from a byte
backup and the full suite (937 tests); all killed: `fold` as `_norm` (11
tests), `fold` keeping hyphens (22), without `lower()` (14), `keyword_set`
and `keywords_matched` using `_norm` (21, 19), the `""` drop removed (6),
`fits` (x2, 2 each), `_expected_results` (x3, 5, 1, 6), `_call_satisfies`
(x2, 2 each), `_norm` itself dropping spaces (10, the §25 guard) and
`misnamed` reading names through `fold` (13). The tests added are
additions only; no existing test was edited.

## Not checked

- The model's behaviour on the other 49 cases beyond the run below.
- Cross-word matches across the name/brand/description join, probed only by
  the replay and the identity of the committed cases.
- The kit tests under mutation (the Node kit does not import the Python
  package; the full `npm run verify` ran on the unmutated tree).
- `coverage.check_coverage` verdicts on `evals/generated.jsonl` (uncommitted,
  not in the worktree).

## Live check

not-needed: no path of rule 1 is touched (no `cli.py`, `models/`,
`tracing.py`, `prompts/`, `infra/`), and no `.claude/settings.json`. The
change is matching logic, proven deterministically.

## Eval run

- Report: `evals/runs/20261125T091237Z-ollama.json` (ollama, qwen3:8b), made
  by the coordinator in the worktree at 63a54f9, the same `src` as the
  reviewed content. `advisor-analysis hashes` exits 0: cases, prompt and
  catalogue hashes match.
- `compare` against `evals/baseline.json`: 39/50 against 38/50. Regressed
  (0). Fixed (1): `gaming-monitor`, which fails at random on this prompt
  (3 of 10 runs), so it is not this change. Added and removed: none.
- `heartrate-training-zones` still FAILs, as the intent's assumption said it
  might: the model searched `["optical heartrate sensor", "continuous
  logging"]`, which as a whole phrase matches no smartwatch, so `a-match`
  fails ("cites no product"). The `search` check, which failed before, now
  passes. The case flips only when the model sends shorter keywords.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run), in the worktree at 6bf7a12: the
  branch update (`merged main`, `verify` green: 937 pytest, 490 kit tests),
  `npm run check:intent` PASS, the eval run, `hashes`, `compare` and the
  `heartrate-training-zones` result above. No mutant survived, so none to
  re-run.
- Verified by the reviewer: `npm run verify` on `37a196d` after the
  implementer's last edits (937 passed); the 15 mutants; the replay of 978
  recorded calls (2 changed, both empty to rows) and the probe sweep
  behind finding 1; the committed cases (50, 39 with `expect_search`):
  `catalogue_problems` is empty before and after and `_expected_results` is
  identical; the `CLAUDE.md:164` claims; the catalogue counts (`hd` 41 to
  100, `heartrate` 0 to 31, `50mp` 0 to 13).
- Taken on trust: the failing-first claim in Progress (partly corroborated
  by the mutants); the `generated.jsonl` coverage numbers.
- `npm run sdlc:scan -- --sample-due auto --exclude 32`: the 9th attested
  auto change, every 3, so `sampled: yes`: a full read is due after the merge.
