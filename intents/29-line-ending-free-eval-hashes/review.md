<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §29 review — An eval run's content hashes depend on the checkout's line endings

verdict: escalate
tier: reviewed
reviewed-commit: daaa924
main: 0e61f5f
round: 2
sampled: yes
run: auto
live-check: not-needed

No finding needs rework. The tier is Reviewed (it edits two skills and
REVIEW-POLICY.md), so **you read the diff**
(`git diff main...fix/29-line-ending-free-eval-hashes`) before `/deliver 29`.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: the rework (cf444aa) adds two tests, a one-line `rehash` change and a Progress entry |
| 2 | Type check | pass |
| 3 | Behaviour against the intent | pass: round 1's checks hold; the baseline was re-checked |
| 4 | Tests prove the behaviour | pass: M10 and M19 are now killed; no survivor remains |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass: Progress now says 880 → 902; HEAD runs 926 (924 + 2) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check
```
type-check: PASS (intent 29, fix)
  note:  13 file(s), 525 line(s) changed outside intents/.
```

- **Round 1 resolved:**
  - M10 is killed by `test_rehash_accepts_a_report_made_on_mixed_ending_bytes`;
  - M19 is killed by `test_compare_model_difference_is_not_blamed_on_hash_forms`;
  - `rehash` now writes `content_sha256(data)`, the one shared definition;
  - Progress records the baseline's provenance: from the merge cb627b7,
    byte-identical to `--rehash` of §24's run.
- **The committed `evals/baseline.json` is still byte-identical** (`cmp`) to
  `baseline …/20261124T215703Z-ollama.json --rehash --out <scratch>`, and
  `hashes evals/baseline.json` exits 0.

## Findings
None open. Round 1's nits remain, worth a look only:
- `content_check` treats an unknown `hash_form` as raw;
- `hashes` with no file prints its fields out of `HASH_FIELDS` order;
- `baseline --cases` is accepted silently without `--rehash`;
- `baseline` is missing from `tests/test_boundaries.py`'s pure-module list
  (this predates §29).

## Not checked
- A real `advisor-eval` report carrying `hash_form: "lf"`: only the fake-model
  test covers that path.
- An LF-only checkout (`core.autocrlf=false`).
- The historical hashes quoted in intent.md.

## Live check
- not needed: no rule-1 path and not `.claude/settings.json`.

## Eval run
- not owed (no listed path): `uv run advisor-analysis owes-run --base main`
  prints "not owed (no listed path changed)".

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at daaa924:
  - `npm run verify`: exit 0, 926 passed.
  - `npm run check:intent`: PASS.
  - A full read of the cf444aa diff.
  - Mutants M10, M11–M15 and M19 all killed.
  - The baseline `cmp` and `hashes` exit 0.
  - Clean worktree at the end.
- **Coordinator, re-run**, at daaa924:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **926 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 29, fix)`, which matches.
  - Mutants the rework says it kills, against the full suite:
    - M10 (`baseline.py:91`): **killed**, 1 failed.
    - M19 (`:177`): **killed**, 1 failed.
    - Both match. Restored by copy; `git status --short` was clean.
  - `uv run advisor-analysis hashes evals/baseline.json`: 3 × matches, exit 0.
  - `npm run sdlc:scan -- --sample-due auto --exclude 29`: "nth attested auto change = 9, every 3, sampled: yes".
- Taken on trust: that the §24 run report in the main checkout is the run main's baseline names (its hashes match).

---

# Round 1

verdict: rework
tier: reviewed
reviewed-commit: 039f878
main: 0e61f5f
round: 1
sampled: no
run: auto
live-check: not-needed

**Tier.** Reviewed by path: the change edits `.claude/skills/auto/SKILL.md`,
`.claude/skills/review/SKILL.md` and REVIEW-POLICY.md. Its HIGH finding
would raise it there anyway (rule 3).

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass: all five subtasks, no unplanned scope; `run.content_files` is explained in Progress |
| 2 | Type check | pass |
| 3 | Behaviour against the intent | pass |
| 4 | Tests prove the behaviour | findings (2 surviving mutants) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1 LOW) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass |
| 9 | Repo footguns | pass |

## Type check
```
type-check: PASS (intent 29, fix)
  note:  13 file(s), 507 line(s) changed outside intents/.
```

What the change does, checked on real data:
- **`content_sha256`** folds only `\r\n` → `\n`. A lone `\r`, trailing space
  or a missing final newline still changes the hash. It is the one
  definition behind the report and the `hashes` check.
- **`compare`:**
  - same-form warnings are unchanged;
  - mixed forms say "hashed differently (… before §29) …";
  - equal hashes across forms don't warn.
- **`advisor-analysis hashes`** exits 0 on a match, 1 naming the field, 2 on
  bad input. An old report is checked against raw bytes, and says so.
- **`baseline --rehash`** reproduces the committed file from §24's run. It
  refuses a report made on other content (`20261124T183001Z`, from before
  §26's cases) and refuses an `lf` report.
- **The committed `evals/baseline.json`** came out of the automatic merge
  cb627b7: main's §24 baseline combined with §29's rehash. It is
  **byte-identical** (`cmp`) to `baseline …/20261124T215703Z-ollama.json
  --rehash --out <scratch>`, as both the coordinator and the reviewer
  checked. So it is not hand-edited: it is exactly what the proving command
  writes. `hashes evals/baseline.json` exits 0, and its three LF hashes
  equal the git blobs' sha256 (90a614f9…, 071fd576…, b3640395…).
- **The skills** now say: run `uv run advisor-analysis hashes <report>` in
  the worktree at the reviewed commit, and expect exit 0. REVIEW-POLICY.md
  gains only that parenthesis. There is no textual overlap with §28's edits.

## Findings
- **HIGH** `src/advisor/evals/baseline.py:91` and
  `tests/test_analysis_baseline_cli.py` — mutant M10 (drop
  `raw_sha256(data)`, the "bytes as they are" form, from what `rehash`
  accepts) survives.
  - The test is parametrised over LF and CRLF only, where the raw hash
    always equals one of the other two.
  - The raw form matters exactly for a mixed-ending working copy (§26's
    case), and the plan says "parametrised over the three forms".
  - Needs rework: add a mixed case. Disk bytes like `b'{"id": "a"}\r\n{"id":
    "b"}\n'`, with the report's `cases_sha256` equal to `sha256` of those
    exact bytes. Expect exit 0, a written `cases_sha256` equal to
    `content_sha256` of the LF form, and `hash_form: "lf"`. M10 must be
    killed.
- **MEDIUM** `src/advisor/evals/baseline.py:177` — mutant M19 (`if form_a !=
  form_b:`, dropping `key in HASH_FIELDS`) survives. It would add the
  "hashed differently" note to a `provider` or `model` warning too, though
  the plan scopes it to hash fields. Needs rework: a test with a raw-form
  baseline and an `lf` report whose `model` differs, asserting the warning is
  exactly `model differs: baseline m, report <other>`. M19 must be killed.
- **LOW** `intents/29-line-ending-free-eval-hashes/plan.md` (Progress) —
  "883 -> 902" should be 880 → 902 (+22); after main's merge HEAD runs 924.
  Correct it in the next Progress entry. Also record there that the
  committed baseline came from the merge and equals `--rehash` of §24's
  run, since the 8b02d8a commit names §25's run.
- **LOW (nits)** — worth a look, no rework:
  - `rehash` writes `raw_sha256(folded)` rather than calling
    `content_sha256`, a second spelling of the same definition;
  - `content_check` treats an unknown `hash_form` as raw while `compare`
    names it;
  - `hashes` with no file prints cases, catalogue, prompt, not the
    `HASH_FIELDS` order;
  - `baseline --cases` is accepted silently without `--rehash`;
  - `baseline` is still missing from `tests/test_boundaries.py`'s pure-module
    list (already so before §29; covered through `run`).

## Not checked
- A real `advisor-eval` report carrying `hash_form: "lf"`. Only the faked-model
  test covers that path. No eval run is owed, and no model was called.
- Behaviour on an LF-only checkout (`core.autocrlf=false`), beyond the
  blob-hash comparison.
- The historical hashes quoted in intent.md (20ba79fc, a81f06ad, b7a88ce6)
  were not recomputed.

## Live check
- not needed: no rule-1 path, not `.claude/settings.json`, and no
  Not-checked item needs a live run.

## Eval run
- not owed (no listed path): `uv run advisor-analysis owes-run --base main`
  prints "not owed (no listed path changed)".

## Verified myself vs. taken on trust
- Reviewer (product-advice-agent-reviewer), at 039f878:
  - `npm run verify`: exit 0, 924 passed.
  - `npm run check:intent`: PASS.
  - `owes-run`, `hashes` with and without a file, `--rehash` on two real
    runs, and the `cmp` byte-identity of the baseline.
  - `compare` on real reports.
  - Blob sha256s on main and HEAD.
  - Test counts at the fork, dcd4250, main and HEAD.
  - 35 mutants: 33 killed, M10 and M19 survived. Restored by copy; clean.
- **Coordinator, re-run**, at 039f878:
  - `npm run verify`: kit 0 fail; ruff "All checks passed!"; mypy "Success: no issues found in 31 source files"; pytest **924 passed**, which matches.
  - `npm run check:intent`: `type-check: PASS (intent 29, fix)`, which matches.
  - Surviving mutants against the full suite: M10 (`baseline.py:91`) and M19 (`:177`) each **survived** (924 passed), which matches. Restored by copy; `git status --short` was clean.
  - Before the round: the merged `evals/baseline.json` equals a fresh `--rehash --out` of §24's run, ignoring line endings.
- Taken on trust: that the §24 run report in the main checkout is the run main's baseline names. Its hashes match.
