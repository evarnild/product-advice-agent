<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §11 review — Choose the eval's model provider with a flag on advisor-eval

verdict: attest
tier: attested
reviewed-commit: 1b32ece4679207464f420685e03ae78bd943cc16
round: 2
sampled: no
run: auto
live-check: not-needed

Tier: Attested, set by input 1 (the path table): `run.py` is `src/**` not
on the Reviewed list; the test file is Attested; `README.md` and
`intents/**` are Automated. `review_tier:` is empty; no finding raised it.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 11` → "nth
attested auto change = 4, every 3, sampled: no".

Round 1's Needs decision is settled: the owner chose (a), de14d8b amended
the Outcome to match, and the code already did (a). 3fb0fe9 adds two tests
that pin it, one per provider; they kill M9, and round 1's sampled mutants
stay killed. The ROUTE has round 1's cause. No finding needs rework.

## Round-1 findings: resolution
| Round 1 | Finding | Resolution |
| --- | --- | --- |
| MEDIUM | `run.py:134-137`: Outcome and Assumptions disagreed when `--provider` names the env's provider; M9 survived. Needs decision | **Resolved.** Owner: "a". de14d8b amended the Outcome ("whenever `--provider` is given, even if it names the provider the environment already selects"); code unchanged; 3fb0fe9 adds `test_provider_flag_naming_the_env_provider_still_takes_the_default_model` and `test_provider_flag_naming_the_env_provider_ignores_env_model_for_ollama`; M9 KILLED by both; README 118-120 already states (a) |
| Note | overlap with §9 in `run.py` | unchanged; information only |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (since 39f5031: the authorised Outcome amendment, metadata, review.md and `tests/test_evals_run.py` +22; `src/` unchanged since 00a7432) |
| 2 | Type check | ROUTE, exit 2; reason below, still holds at 114 lines |
| 3 | Behaviour against the intent | pass (`run.py:134-139` applies the default whenever `--provider` is given; `--model` layered after; README 118-120 unconditional, matching (a)) |
| 4 | Tests prove the behaviour | pass (M9 and two one-sided variants killed; M1, M2, M3, M5 still killed) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (README defaults match `config.py:22`; "290 passed" reproduced; 114 = +113/−1) |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (no dependency; only the fake key) |
| 9 | Repository-specific footguns | pass (list empty) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: ROUTE (intent 11, adjustment)
  route: Declared adjustment, but 3 files / 114 lines changed (limit 5 / 60). Route to fix or feature.
  note:  3 file(s), 114 line(s) changed outside intents/.
```
Exit 2.

**Why this ROUTE is fine:** `checkShape` counts test and `.md` lines with
code. `git diff --numstat main...HEAD` outside `intents/`:

| File | Added | Deleted |
| --- | --- | --- |
| `tests/test_evals_run.py` | 93 | 0 |
| `src/advisor/evals/run.py` | 14 | 1 |
| `README.md` | 6 | 0 |

Without tests the change is 21 lines in 2 files, with no core code
(`run.py` is I/O). The 22 lines added since round 1 are the two tests round
1 asked for. Re-declaring as a feature would add a spec and plan for
behaviour the intent already pins down.

## Findings
No findings.
- **Note (carried):** §9 (`feat/9-error-analysis`) edits `run.py` next to
  this change's import line; the second branch to merge rebases and
  re-runs verify.

**Mutants** (reviewer's harness outside the repo: backup by copy, one
CRLF-aware replacement asserted once, `git diff --quiet` non-zero, full
pytest, restore by copy in `finally`; `git status --short` empty after):

| # | Mutant (`run.py`) | Result | Killing tests |
| --- | --- | --- | --- |
| M9 | l.136: default only when the provider changes | KILLED | test_provider_flag_naming_the_env_provider_still_takes_the_default_model, test_provider_flag_naming_the_env_provider_ignores_env_model_for_ollama |
| M9a | keep `settings.model` only when flag == env == anthropic | KILLED | test_provider_flag_naming_the_env_provider_still_takes_the_default_model |
| M9b | keep `settings.model` only when flag == env == ollama | KILLED | test_provider_flag_naming_the_env_provider_ignores_env_model_for_ollama |
| M1 | `if args.provider:` → `if False:` | KILLED | 6 tests incl. both new ones |
| M2 | default → `settings.model` | KILLED | both new tests, test_provider_flag_uses_the_anthropic_default_model_and_key, test_provider_flag_wins_over_the_environment_and_uses_its_default_model |
| M3 | `if args.model:` → `if False:` | KILLED | test_model_flag_alone_overrides_only_the_model, test_provider_and_model_flags_together |
| M5 | the two blocks swapped | KILLED | test_provider_and_model_flags_together |

Survived: none.

## Not checked
- **`.env` precedence through a real file:** tests pass an `env` mapping
  (`config.py:57-58`); by reading, the flags apply after `load_settings`,
  so they win over `.env` the same way.
- **A real model run with either flag:** not run; `make_client` and the
  adapters are unchanged.
- **The missing-key path through the real console script:** not run (a
  key found by `find_dotenv` in a parent would start a paid run).
- **The key on stderr or in the report:** only stdout is asserted; by
  reading, the message names only the variable (`run.py:151`), the total
  line prints provider and model (`:196`), the report holds no env values
  (`:198-210`).
- **Round-1 mutants M4, M6, M7, M8, M10:** not re-run; `run.py` is
  byte-identical since round 1.

## Live check
Not needed: rule 1 (none of `cli.py`, `models/`, `tracing.py`, `prompts/`,
`infra/`), rule 2 (no `.claude/settings.json`), rule 3 (the new wiring is
covered with the fake factory; the real-model path is unchanged). Optional
sanity run: `uv run advisor-eval --provider ollama`.

## Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/11-eval-provider-flag` at 1b32ece; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `pass 255, fail
  0`; ruff "All checks passed!"; "94 files already formatted"; mypy
  "Success: no issues found in 17 source files"; pytest "290 passed".
  Matches the reviewer and the implementer. (Round 1 recorded "93 files";
  the rework added no file, and ruff counts formatted files, so 94 is
  today's count; the difference is not a code change.)
- **Coordinator, re-run:** `npm run check:intent` → ROUTE, exit 2, 114
  lines, as above. Matches.
- **Coordinator, re-run:** M9 with my own harness (backup by copy, one
  replacement, file-changed assertion, full pytest, restore by copy):
  KILLED, 2 failed, 288 passed, first failure
  `test_provider_flag_naming_the_env_provider_still_takes_the_default_model`.
  Matches the reviewer and the implementer.

**Reviewer, verified:**
- HEAD 1b32ece on `adjust/11-eval-provider-flag`; `main` untouched; not
  pushed.
- `npm run verify` exit 0 (290 passed); `npm run check:intent` ROUTE.
- `git diff --numstat main...HEAD` as tabled.
- The diffs 39f5031..HEAD and main...HEAD; `run.py:131-160`, `196-218`;
  `config.py:22`, `55-68`; README 105-125.
- 7 mutants as tabled; `git status --short` empty after each.

**Taken on trust:**
- that `make_client` and the adapters behave live as §8's live check found;
- that the owner's "a" is what de14d8b records (the reviewer saw the
  commit; the coordinator heard it).

# Round 1 (history)

- verdict: rework
- tier: attested
- reviewed-commit: 39f50311142ba6afb83a9ec1d99c2c76f278398d
- round: 1
- sampled: no
- run: auto
- live-check: not-needed

Tier: Attested, set by input 1 (the path table): `src/advisor/evals/run.py`
is `src/**` not on the Reviewed list; `tests/test_evals_run.py` is
Attested; `README.md` Automated. `review_tier:` is empty; no finding is
CRITICAL or HIGH, so nothing raised it.

Sampling: `npm run sdlc:scan -- --sample-due auto --exclude 11` → "nth
attested auto change = 4, every 3, sampled: no".

The flags work as built, and 9 of 10 mutants are killed. The verdict is
rework because of one **Needs decision:** finding: the intent's Outcome and
its Assumptions disagree on the model when `--provider` names the provider
the environment already selects, and no test pins either reading (M9
survives). The ROUTE is explained below and needs no re-declaration.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (only `run.py`, its test file and the README, the blast radius the intent named) |
| 2 | Type check | ROUTE, reason stated below; no re-declaration recommended |
| 3 | Behaviour against the intent | findings (1 MEDIUM) |
| 4 | Tests prove the behaviour | findings (M9 survives; same issue) |
| 5 | Conventions | pass (no SDK or `httpx` import; fake factory; sockets blocked) |
| 6 | Numbers in prose | pass (README's `qwen3:8b` / `claude-haiku-5-5` match `config.py:22`; the implementer's "+16/−1, 22 lines" is really +14/−1, 21) |
| 7 | Documentation | pass (README "Evaluating answers", lines 114-120) |
| 8 | Guardrails and hygiene | pass (ruff, mypy clean; no dependency; the only key is the fake `"test-key-not-real"`, asserted absent from stdout) |
| 9 | Repository-specific footguns | pass (list empty) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: ROUTE (intent 11, adjustment)
  route: Declared adjustment, but 3 files / 92 lines changed (limit 5 / 60). Route to fix or feature.
  note:  3 file(s), 92 line(s) changed outside intents/.
```
Exit 2.

**Why this ROUTE is fine:** `checkShape` in `scripts/intent-check-lib.mjs`
(around lines 291-301) sums added and deleted lines over every path
outside `intents/`, tests and `.md` included. `git diff --numstat
main...HEAD`:

| File | Added | Deleted |
| --- | --- | --- |
| `tests/test_evals_run.py` | 71 | 0 |
| `src/advisor/evals/run.py` | 14 | 1 |
| `README.md` | 6 | 0 |

Without the tests the change is 21 lines in 2 files; no core code
(`CORE_CODE` names only `evals/(cases|score).py`, and says "the runner
(run.py) is I/O"); the overshoot is the tests the intent's Outcome asks
for. Re-declaring as a feature would add a spec and plan for behaviour the
intent already pins down.

### Findings
- **MEDIUM** `src/advisor/evals/run.py:134-137` — `--provider` without
  `--model` always takes the provider's default model, even when the flag
  names the provider the environment already selects. The intent's
  Outcome says the default applies "when the flag changes the provider,
  else `ADVISOR_MODEL` as today"; its Assumptions say "even if
  `ADVISOR_MODEL` is set", without that exception. With
  `ADVISOR_MODEL_PROVIDER=anthropic`, `ADVISOR_MODEL=claude-<other>` and
  `--provider anthropic`, the run uses `claude-haiku-5-5`. No test pins
  either reading: M9 (the Outcome's reading) survives.
  Needs decision: (a) the Assumptions' rule (current code): add a test with
  the same provider in the flag and the env, asserting the default model;
  or (b) the Outcome's rule: keep `ADVISOR_MODEL` when the flag names the
  env's provider, add the matching test, and reword README line 117.
  Either test must kill M9 (or its inverse).
- **Note (not a finding against §11):** §9 (`feat/9-error-analysis`, in
  progress) edits `run.py` too; its `from advisor.agent import …` line is
  next to this change's `from advisor.config import …` line, so the second
  branch to merge rebases and re-runs verify.

**Mutants** (reviewer's harness outside the repo: one replacement, `git
diff --quiet` non-zero, full pytest, restore by copy in `finally`; `git
status --short` empty after):

| # | Mutant | Result | Killing tests |
| --- | --- | --- | --- |
| M1 | `if args.provider:` → `if False:` (l.134) | KILLED | test_provider_flag_wins_over_the_environment_and_uses_its_default_model, test_provider_flag_uses_the_anthropic_default_model_and_key, test_provider_and_model_flags_together, test_anthropic_flag_without_a_key_exits_2 |
| M2 | default → `settings.model` (l.136) | KILLED | test_provider_flag_wins_…, test_provider_flag_uses_the_anthropic_default_model_and_key |
| M3 | `if args.model:` → `if False:` (l.138) | KILLED | test_model_flag_alone_overrides_only_the_model, test_provider_and_model_flags_together |
| M4 | `choices=KNOWN_PROVIDERS` removed (l.79) | KILLED | test_unknown_provider_flag_exits_2_listing_the_known_ones |
| M5 | `--provider` and `--model` blocks swapped | KILLED | test_provider_and_model_flags_together |
| M6 | default of `settings.provider` (l.136) | KILLED | test_provider_flag_wins_…, test_provider_flag_uses_the_anthropic_default_model_and_key |
| M7 | `if args.model and not args.provider:` | KILLED | test_provider_and_model_flags_together |
| M8 | key check bypassed (l.147, unchanged line) | KILLED | test_anthropic_flag_without_a_key_exits_2, test_config_errors_exit_2, … |
| M9 | default only when the provider changes (l.136) | **SURVIVED** | none |
| M10 | `model=""` (l.136) | KILLED | test_provider_flag_wins_…, test_provider_flag_uses_the_anthropic_default_model_and_key |

### Not checked
- **`.env` precedence through a real file:** tests pass an `env` mapping, so
  `load_env` skips `.env` (`config.py:55-56`); the `.env` merge itself is
  unchanged.
- **A real model run with either flag:** not run; `make_client` and the
  adapters are unchanged.
- **The missing-key path through the real console script:** not run
  (`find_dotenv` searches parents; a key found there would start a paid
  run).
- **The key on stderr or in the report:** only stdout is asserted; by
  reading, the message names only the variable and the report holds no env
  values.

### Live check
Not needed: rule 1 (none of `cli.py`, `models/`, `tracing.py`, `prompts/`,
`infra/`), rule 2 (no `.claude/settings.json`), rule 3 (the new wiring is
covered with the fake factory; the real-model path is unchanged). A sanity
run, `uv run advisor-eval --provider ollama`, is optional.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/11-eval-provider-flag` at 39f5031; `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `pass 255, fail
  0`; ruff "All checks passed!"; "93 files already formatted"; mypy
  "Success: no issues found in 17 source files"; pytest "288 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → ROUTE, exit 2, the
  output above. Matches.
- **Coordinator, re-run:** M9 with my own harness (backup by copy, one
  replacement, file-changed assertion, full pytest, restore by copy):
  SURVIVED, 288 passed. Matches.
- **Coordinator, read:** `run.py:133-139` as quoted in the finding.

**Reviewer, verified:**
- HEAD 39f5031 on `adjust/11-eval-provider-flag`; `git log main..HEAD` =
  00a7432, e4b46c9, 39f5031; nothing touched `main`, nothing pushed.
- `npm run verify` exit 0 (288 passed); `npm run check:intent` ROUTE.
- `git diff --numstat main...HEAD` as tabled; `cli.py`, `config.py`,
  `pyproject.toml`, `uv.lock`, `cases.py`, `score.py` unchanged.
- 10 mutants as tabled.
- `advisor-eval --help` shows both flags; `advisor-eval --provider nope`
  exits 2 with "invalid choice: 'nope' (choose from ollama, anthropic)".
- `sdlc:scan` sampling as above; the overlap with §9 read from its branch.

**Taken on trust:**
- the implementer's "281 before" (consistent with 7 added tests);
- that `make_client` and the adapters behave live as §8's live check found.
