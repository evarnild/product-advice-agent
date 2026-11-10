<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §2 review — Locally run model (Ollama) as the advisor's default

verdict: rework
tier: reviewed
reviewed-commit: ad535f21d4436858caced525abfb48baaaf0f04f
round: 4
sampled: no
run: manual
live-check: owed

A manual round (the owner's "rebase 2") reviewing the coordinator's rebase
of `feat/2-local-model` from `dfb0811` onto `96ff0cf` (`main` with §3 at
9ea17ad and §4 at 8b9294a).

**The rebase itself is faithful:**
- all 19 commits carried over;
- only 20c9316 → 653a984 changed in content, by the `tests/test_cli_stderr.py`
  probe adaptation;
- every file §3 or §4 changed gained exactly what `main` gained;
- `npm run verify` passes with 180 tests;
- 11 of 12 mutants killed; the survivor is a test-side parity line, as
  expected.

**Why the verdict is still rework:** `main` moved again after the rebase
base. §5 merged at b6766f9 after the rebased tip ad535f2. `git merge-tree
main HEAD` now conflicts in `tests/test_models.py`, and keeping both sides
leaves 1 test failing. The fix is mechanical, but it means another rebase,
and so a round 5.

Tier: Reviewed, set by the path table (`cli.py`, `config.py`, `tracing.py`,
`.env.example` by meaning). `review_tier: reviewed` agrees.

## Round-3 findings: resolution
| Round-3 finding | Resolution |
| --- | --- |
| LOW: the rename is unplanned and has no Progress line | open, Worth a look (now 7ac0fb7 / a98204d) |
| LOW: §3's branch still used `key_variable` | resolved: §3 is merged; the rebased tree has no `key_variable` in `src` or `tests` except the accurate test name; mypy clean |
| Nit: `plan.md:284` "162 pytest tests" | open, nit (the suite is 180) |
| Round 2: LOW "also guards M02" attribution | open, Worth a look |
| Round 2: LOW private attributes in wiring tests | open, Worth a look |
| Round 1: M42 (`"tool_calls": null`) | open, Worth a look (near-equivalent) |
| Round 1: tags via private `_otel_span` | resolved for the pre-rebase code by the owner's live check; `tracing.py:47` unchanged by the rebase |
| Round 1: default URL defined twice | open, Worth a look |
| Round 1: every 404 → B11 | open, Worth a look (plan-settled) |
| Pass 9 candidate (wiring every test bypasses with a fake) | open: an owner edit to `REVIEW-POLICY.md` |
| M40 | equivalent; no action |

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1, LOW): no Progress line for the rebase and probe adaptation; the range-diff shows no other scope change |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (§2's patches byte-identical apart from import context and the probe; 180 pass; AC10 is the live check) |
| 4 | Tests prove the behaviour, not only pass | pass (12 mutants: 11 killed; N11 survived, a test-side parity line, expected) |
| 5 | Conventions | pass (the boundaries test runs §3's subprocess test and §2's `httpx` test side by side) |
| 6 | Numbers in prose | pass ("162" nit carried) |
| 7 | Documentation | pass (`CLAUDE.md` holds §3's and §2's text; README and 0001 match the expected merge) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | findings (1): `main` moved after the rebase base; and a candidate rule (below) |

## Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 2, feature)
  note:  27 file(s), 1036 line(s) changed outside intents/.
```
The note counts against the current local `main` (with §5), so it is
inflated. Against the merge base 96ff0cf, the branch changes 22 files
outside `intents/` (+928/−66).

## Findings
- **MEDIUM** `tests/test_models.py` (branch vs `main` b6766f9) — §5 merged
  after the rebase base. `git merge-tree --write-tree main HEAD` gives
  `CONFLICT (content): Merge conflict in tests/test_models.py`, because both
  sides append tests after `test_make_client_anthropic_does_not_connect`.
  - Keeping both sides gives `1 failed, 181 passed`:
    `test_sdk_tracing_stays_off_even_if_the_environment_enables_it`, with
    `TypeError: make_client() takes 2 positional arguments but 3 were
    given`. §5's test calls `make_client("anthropic", "m",
    "placeholder-key")`, and §2 made `api_key` keyword-only.
  - With `api_key="placeholder-key"`: `182 passed`.
  - `anthropic_model.py` and `CLAUDE.md` auto-merge.

  Needs rework: rebase onto `main`; in `tests/test_models.py`, keep §5's
  two tests, then §2's; change §5's call to `api_key="placeholder-key"`; run
  `npm run verify`; then `/review` round 5.
- **MEDIUM** `intents/2-local-model/metadata.yml` (`live_checked:
  2026-11-10 by-agent`) — the recorded check ran on the pre-rebase code. It
  does not cover §2 running alongside §3's runtime changes, or §5's after
  the next rebase:
  - `cli._configure_logging`'s root `NullHandler` beside §2's B10/B11 error
    paths;
  - the `tracer.py` split;
  - `agent.py`'s import change;
  - §5's `open_telemetry=False` on the Anthropic run.

  `check:intent` passes only because a date is present; it cannot tell that
  the date predates the rebase. Needs decision: does the recorded check
  stand for the rebased code, or does the owner re-run the minimal steps
  under `## Live check` after the rebase and re-record `live_checked:`? The
  reviewer recommends the re-run: minutes of work, and the combined code has
  never run live.
- **LOW** `intents/2-local-model/plan.md` `## Progress` — the rebase is not
  recorded:
  - 653a984 keeps 20c9316's subject but also edits §3's
    `tests/test_cli_stderr.py:28,33-35` (`make_tracer` takes `tags`, the
    factory is keyword-only, the env pins `anthropic`);
  - the conflict resolutions in `tracing.py:13-14`, `test_boundaries.py`
    and `test_tracing.py`.

  Worth a look: a Progress line naming the rebase, its bases and the probe
  adaptation.
- **LOW** (pass 9 candidate) — a rebase that brings another intent's
  rule-1 runtime changes leaves `live_checked:` in place, and `check:intent`
  still passes. Worth a look, as an owner edit to `REVIEW-POLICY.md` → "Live
  checks": "a rebase across another intent's rule-1 paths re-opens the live
  check", or record in `metadata.yml` the commit the check ran on.

Mutants (backup by copy; one CRLF-aware match; `git diff --quiet`
non-zero; full `pytest -q`, no `-x`; restore by copy in `finally`):

| id | target | change | result | killing tests |
| --- | --- | --- | --- | --- |
| N01 | `cli.py:52` (§3) | `logging.basicConfig(handlers=[logging.NullHandler()])` → `pass` | KILLED (1) | test_cli_stderr::test_library_log_lines_are_silent_without_debug |
| N02 | `cli.py:48` (§3) | `if debug:` → `if True:` | KILLED (1) | test_cli_stderr::test_library_log_lines_are_silent_without_debug |
| N03 | `cli.py:48` (§3) | `if debug:` → `if False:` | KILLED (2) | test_cli::test_debug_sets_advisor_logger_to_debug; test_cli_stderr::test_library_log_lines_show_with_debug |
| N04 | `cli.py:82` (§2) | `if settings.api_key_variable is not None:` → `if True:` | KILLED (12) | test_cli_ollama::test_default_provider_is_ollama_without_a_key, … |
| N05 | `cli.py` | `make_tracer(full_env, tags)` → `make_tracer(full_env)` | KILLED (3) | test_cli_ollama::test_tracer_gets_provider_and_model_tags[…] |
| N06 | `cli.py` | `tags` → provider tag only | KILLED (3) | test_cli_ollama::test_tracer_gets_provider_and_model_tags[…] |
| N07 | `tracing.py:36` | `self._tags = list(tags)` → `[]` | KILLED (3) | test_tracing::test_root_span_carries_provider_and_model_tags[…]; ::test_make_tracer_passes_tags_to_the_langfuse_tracer |
| N08 | `tracing.py:43` | `if self._tags:` → `if False:` | KILLED (2) | test_tracing::test_root_span_carries_provider_and_model_tags[…] |
| N09 | `tracing.py:142` | `LangfuseTracer(client, tags)` → `LangfuseTracer(client)` | KILLED (1) | test_tracing::test_make_tracer_passes_tags_to_the_langfuse_tracer |
| N10 | `tracing.py:47` | set only the last tag | KILLED (2) | test_tracing::test_root_span_carries_provider_and_model_tags[…] |
| N12 | `tests/test_cli_stderr.py:28` | revert the probe to `lambda env: …` | KILLED (3) | all three test_cli_stderr tests: the adaptation was necessary |
| N11 | `tests/test_cli_stderr.py:33` | drop `"ADVISOR_MODEL_PROVIDER": "anthropic"` | SURVIVED (180 passed) | expected: the logging behaviour doesn't depend on the provider; the line keeps parity with `main`'s case |

For round 5: re-run N01, N04, N07, and §5's `open_telemetry=False` →
`True` on `anthropic_model.py` (must be killed by
`test_anthropic_adapter_turns_off_sdk_tracing`).

## Not checked
- **The merged tree under the full `verify`:** on a scratch resolution with
  b6766f9, only pytest was run (182 passed after the keyword fix).
- **Live behaviour of the rebased combination** (rule 3):
  - a real Ollama run under §3's root `NullHandler`;
  - whether `langfuse`'s own `httpx` stderr handler lets an `httpx` WARNING
    from the Ollama adapter show without `--debug` when tracing is on.
    Before §2, `httpx` was used only inside the SDKs;
  - one trace per Anthropic run once §5 is on the branch.
- **Carried from round 3:**
  - Ollama 0.40.9 specifics;
  - Langfuse not pricing `qwen3:8b`;
  - the 5 GB figure;
  - the `--debug` traceback with `user:pw@`;
  - proxy settings.
- **Round 1–3 mutants on §2's own lines:** not re-run; their patches are
  byte-identical in the range-diff.
- **Platforms:** Windows only.

## Live check
- owed: rule 1 (`src/advisor/cli.py`, `src/advisor/models/`,
  `src/advisor/tracing.py`), and rule 3 (the rebased combination). The
  recorded check covers §2's own lines on the pre-rebase code, not §3's
  logging and `tracer.py` changes running beside them, and not §5's adapter
  change after the next rebase. Run the steps below after the round-5
  rebase, then re-record `live_checked:` (finding 2 is the owner's
  decision).
- prepare as round 3, step 0:
  - the worktree's `.env` copied from `main`, with `ADVISOR_MODEL_PROVIDER=`
    and `ADVISOR_MODEL=` commented out;
  - `infra/langfuse/.env` copied;
  - the v4 stack up, with the `LANGFUSE_*` values in `.env`;
  - `Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL,
    Env:ANTHROPIC_API_KEY, Env:ADVISOR_OLLAMA_URL -ErrorAction
    SilentlyContinue`.
- steps:
  1. Start Ollama, then:
     ```
     cd C:\Users\eric\src\product-advice-agent-wt\2-local-model
     uv run advisor "I need noise-cancelling headphones under 200 euros" 2> err.txt; $LASTEXITCODE; Get-Content err.txt
     ```
  2. Quit Ollama; repeat step 1.
  3. Start Ollama; `$env:ADVISOR_MODEL_PROVIDER = "anthropic"`; repeat
     step 1; `Remove-Item Env:ADVISOR_MODEL_PROVIDER`.
  4. Langfuse → Traces: look at the newest.
  5. Delete `err.txt`.
- you should see:
  - **Step 1:** an answer naming catalogue products by name and id, exit
    `0`, and `err.txt` **empty**. Until §7 ships, the hyphen in the question
    may still yield "no headphones"; that is §7's defect, not §2's.
  - **Step 2:** `err.txt` holds exactly `Ollama is not reachable at
    http://localhost:11434. Start Ollama (the Ollama app, or "ollama
    serve") and try again.`, nothing else. Exit `1`.
  - **Step 3:** an answer, exit `0`, `err.txt` empty.
  - **Step 4:**
    - one `advisor-run` trace tagged `provider:ollama` and `model:qwen3:8b`
      from step 1;
    - exactly one trace tagged `provider:anthropic` and
      `model:claude-haiku-5-5` from step 3, with **no** separate
      `anthropic.messages.create` trace (§5);
    - each with a `model-call` showing model and token counts.
  - A stray stderr line, a missing tag or an extra Anthropic trace is a
    defect: leave `live_checked:` empty.

## Verified myself vs. taken on trust

**Coordinator, re-run:**
- **Coordinator, re-run:** before this review, on the rebased branch at
  ad535f2: `npm run verify` → exit 0; kit `tests 255, pass 255, fail 0`;
  ruff "All checks passed!"; "72 files already formatted"; mypy "Success: no
  issues found in 13 source files"; pytest "180 passed". `npm run
  check:intent` → PASS. Matches the reviewer.
- **Coordinator, re-run:** `git merge-tree --write-tree main
  feat/2-local-model` (main at a08430e) → conflict in `tests/test_models.py`
  only. `tests/test_models.py:43` on `main` reads `make_client("anthropic",
  "m", "placeholder-key")`, the positional call the reviewer names. Matches.
- **Coordinator:** no mutant survived on code (N11 is a test-side line), so
  none is owed a re-run this round.

**Reviewer, verified:**
- `verify` and `check:intent` at ad535f2.
- `sdlc:scan --sample-due manual --exclude 2` → "nth attested manual change
  = 1, every 5, sampled: no".
- `git range-diff dfb0811..39aa2a0 96ff0cf..HEAD`: 19↔19, with 17 `=`,
  653a984 `!` (the probe only) and f21c77b `!` (`CLAUDE.md` context).
- Per-file comparison of §3's and §4's 14 files: identical except the
  probe.
- 12 mutants (harness `…/scratchpad/mut2r4/mut.py`).
- The scratch test-merge: 1 failed, 181 passed; 182 after the keyword fix.
- Nothing pushed or merged.

**Taken on trust:**
- the coordinator's account of the conflicts (agrees with the range-diff);
- the owner's recorded live check;
- the Ollama, Langfuse v4 and Anthropic API behaviour.

# Round 3 (history)

- verdict: escalate
- tier: reviewed
- reviewed-commit: 462c9b1fd096ee9daff53175dd33f59d21b6b9c2
- round: 3
- sampled: no
- run: auto
- live-check: owed

Round 3 covers what changed after the owner read the round-2 diff:
- 79cf6b9, the owner's rename `Settings.key_variable` → `api_key_variable`;
- 5511a2d, the coordinator's line wrap for ruff E501;
- 5bf64a4, 8f64463 and 462c9b1, intent artefacts only.

The rename and the wrap change no behaviour; the user-facing missing-key
message is byte-identical. All 9 mutants on the renamed lines are killed. No
finding needs rework, and the tier is Reviewed, so the verdict is escalate.
The owner has already read the diff ("read the diff for 2 and did a small
change", then "go"), so the run goes on to the live check.

Tier: Reviewed, set by the path table (`src/advisor/cli.py`, `config.py`
by meaning). `review_tier: reviewed` agrees.

Scope: `git diff 40314e0 HEAD -- . ':!intents'` is exactly 3 files:
`src/advisor/cli.py` (+4/−2), `src/advisor/config.py` (+2/−2),
`tests/test_config.py` (+3/−3). Inside `intents/`, only `metadata.yml` and
`review.md` changed.

### Round-2 findings: resolution
| Round-2 finding | Resolution |
| --- | --- |
| LOW `plan.md:319-320`: "also guards M02" attribution | open, Worth a look |
| LOW `tests/test_models.py:43-58`: wiring tests read private attributes | open, Worth a look |
| Nit: build entry's "162 pytest tests" | open, nit (the suite is 168) |
| From round 1: M42 (`"tool_calls": null`) | open, Worth a look (near-equivalent) |
| From round 1: tags via private `_otel_span` | open, Worth a look: live check step 6, now on Langfuse v4 |
| From round 1: default URL defined twice | open, Worth a look |
| From round 1: every 404 → B11 | open, Worth a look (plan-settled) |
| Pass 9 candidate (wiring every test bypasses with a fake) | open: an owner edit to `REVIEW-POLICY.md` |
| M40 | equivalent; no action |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1, LOW, Worth a look): the rename is unplanned and not in Progress, but deliberate and the owner's |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear) |
| 3 | Behaviour against the spec | pass (B1–B21 unchanged; the missing-key message byte-identical; AC10 is the live check) |
| 4 | Tests prove the behaviour, not only pass | pass (9 mutants, 9 killed) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | pass (round-2 LOW carried) |
| 7 | Documentation | pass (`README.md`, `CLAUDE.md` never named the property) |
| 8 | Guardrails and hygiene | pass |
| 9 | Repository-specific footguns | pass (list empty; round-1 candidate waits for the owner) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 2, feature)
  error: A live check is owed and not recorded. Do the steps in intents/2-local-model/review.md → ## Live check, then set live_checked: <date> in intents/2-local-model/metadata.yml.
  note:  26 file(s), 1029 line(s) changed outside intents/.
```
The only error is the owed live check. The note's rise from round 2's 21
files and 977 lines is `main` moving (§4 merged), not this branch: against
the merge base dfb0811, the branch still changes 21 files outside
`intents/`.

### Findings
- **LOW** `src/advisor/config.py:39`, `src/advisor/cli.py:71,75`,
  `tests/test_config.py:9,18,44` (79cf6b9) — the rename is unplanned scope:
  it renames a name that has existed on `main` since §1, which pass 1 counts
  as refactoring mixed into a feature. The owner made it deliberately after
  the diff read (`metadata.yml` records it). `plan.md` `## Progress` has no
  line for it. `intent.md:15`, `spec.md:31` and `plan.md:70,75` describe the
  code as it was; `plan.md:164` is a design line and now uses the old name.
  None of this misleads about behaviour. Worth a look: a Progress line
  naming 79cf6b9 and 5511a2d.
- **LOW** branch `fix/3-low-findings-from-1` (§3) — its `cli.py:74`,
  `config.py:28,32` and `tests/test_config.py:8,19` still use
  `key_variable`. Whichever of §2 and §3 merges second applies the rename;
  both change `cli.py`, so a textual conflict is likely anyway. A missed
  spot cannot ship green: mypy --strict and `test_config.py` would fail.
  Worth a look.
- Nit (carried): `plan.md:284`'s "162 pytest tests".

Mutants this round (backup by copy, one CRLF-aware match, `git diff
--quiet` non-zero asserted, full `pytest` without `-x`, restore by copy in
`finally`):

| id | target | change | result | killing tests |
| --- | --- | --- | --- | --- |
| K01 | `cli.py:71` | `if settings.api_key_variable is not None:` → `if True:` | KILLED (12 failed) | test_cli_ollama::test_default_provider_is_ollama_without_a_key, ::test_ollama_never_receives_an_anthropic_key, … |
| K02 | `cli.py:71` | → `if False:` | KILLED (5) | test_cli::test_missing_key_exit_1_names_variable_no_client, ::test_happy_path_prints_answer_exit_0, test_cli_ollama::test_anthropic_gets_its_key_and_no_base_url, … |
| K03 | `cli.py:75` | `Missing {settings.api_key_variable}` → `Missing {settings.provider}` | KILLED (3) | test_cli::test_missing_key_…, test_cli_ollama::test_anthropic_without_key_keeps_the_missing_key_message |
| K04 | `cli.py:75` | "set it in the environment or in .env." → "set it in .env." | KILLED (1) | test_cli_ollama::test_anthropic_without_key_keeps_the_missing_key_message |
| K05 | `config.py:40` | `return PROVIDER_KEY_ENV.get(self.provider)` → `return None` | KILLED (6) | test_config::test_anthropic_still_selectable, test_cli::test_happy_path_prints_answer_exit_0, … |
| K06 | `config.py:40` | → `return "ANTHROPIC_API_KEY"` | KILLED (14) | test_cli_ollama::test_default_provider_is_ollama_without_a_key, test_config::test_defaults_are_local, … |
| K07 | `config.py:50` | `var = self.api_key_variable` → `var = None` | KILLED (10) | test_cli::test_happy_path_prints_answer_exit_0, … |
| K08 | `cli.py:73` | `if not api_key:` → `if False:` | KILLED (3) | test_cli::test_missing_key_…, test_cli_ollama::test_anthropic_without_key_keeps_the_missing_key_message |
| K09 | `cli.py:72` | `api_key = settings.api_key()` → `api_key = None` | KILLED (9) | test_cli::test_happy_path_prints_answer_exit_0, … |

Round 1's L01 and L02 were recorded by name only. K01, K02, K08 and K09
re-derive them on the same block, which moved from lines 59-60 to 71-75.
Other round-1 and round-2 mutants were not re-run: their targets did not
change.

### Not checked
- **Carried** (`src/advisor/models/`, `tracing.py` and the Ollama path are
  unchanged):
  - real Ollama 0.40.9: `tool_name`, `think`, `num_ctx`, the usage counts,
    and `qwen3:8b`'s tool calls (rule 3);
  - whether the Langfuse server, **now v4 (4.78.0)**, reads
    `langfuse.trace.tags` from a `start_observation` root (rule 3). Round 1
    reasoned against v3, so this is new;
  - Langfuse not pricing `qwen3:8b`;
  - the "about 5 GB" figure;
  - the `--debug` traceback with `user:pw@` in the URL;
  - proxy settings on the `httpx.Client`.
- **The merge with `main`:** `git merge-tree --write-tree main HEAD` was
  clean, and `pytest` on that tree gave "173 passed" (168 plus §4's 5). The
  full `npm run verify` was not run on the merged tree.

### Live check
- owed: rule 1 (`src/advisor/cli.py`, `src/advisor/models/`,
  `src/advisor/tracing.py`), and rule 3 (the real Ollama `/api/chat` round
  trip; the server reading `langfuse.trace.tags`, now on Langfuse v4).
- **New since round 2:** `main` has a root `.env` and `infra/langfuse/.env`
  for the running v4 stack; the worktree has neither. Both are gitignored.
  The root `.env` sets both `ADVISOR_MODEL_PROVIDER` **and**
  `ADVISOR_MODEL`, and both must be off for steps 1–5. If only the provider
  is commented out, `ADVISOR_MODEL` sends the Anthropic model id to Ollama,
  and step 3 fails with "Model '…' is not available".
- steps (Windows PowerShell):
  0. ```
     cd C:\Users\eric\src\product-advice-agent-wt\2-local-model
     Copy-Item ..\..\product-advice-agent\.env .env
     Copy-Item ..\..\product-advice-agent\infra\langfuse\.env infra\langfuse\.env
     ```
     In the worktree's `.env`, put `#` before the `ADVISOR_MODEL_PROVIDER=`
     and `ADVISOR_MODEL=` lines. Keep `ANTHROPIC_API_KEY` and `LANGFUSE_*`.
  1. ```
     Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL, Env:ANTHROPIC_API_KEY, Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue
     ```
  2. Start Ollama (the app, or `ollama serve`); run `ollama pull qwen3:8b`,
     then `ollama list`.
  3. `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
     then `$LASTEXITCODE`.
  4. Quit Ollama; repeat step 3.
  5. Start Ollama; `$env:ADVISOR_MODEL = "nonexistent:1b"`; repeat step 3;
     `Remove-Item Env:ADVISOR_MODEL`.
  6. Tags on Langfuse v4:
     1. With the stack up (http://localhost:3000) and the `LANGFUSE_*`
        values from the `.env`, run the README's 5 "Comparing providers"
        questions with the default.
     2. Set `$env:ADVISOR_MODEL_PROVIDER = "anthropic"` and run the 5 again.
     3. `Remove-Item Env:ADVISOR_MODEL_PROVIDER`.
     4. In Langfuse → Traces, filter by `provider:ollama`, then
        `provider:anthropic`.
  7. Optional (B16): during step 3, `Get-NetTCPConnection -State Established
     | Where-Object OwningProcess -eq (Get-Process python).Id`.
  8. Afterwards, keep or delete the worktree's copied `.env` files (both
     gitignored).
- you should see:
  - **Step 2:** `qwen3:8b` listed.
  - **Step 3:** an answer naming catalogue headphones by name and id
    (P-0xx), exit `0`. The first run can take tens of seconds.
  - **Step 4:** exactly `Ollama is not reachable at http://localhost:11434.
    Start Ollama (the Ollama app, or "ollama serve") and try again.`, no
    traceback, exit `1`.
  - **Step 5:** exactly `Model 'nonexistent:1b' is not available in Ollama.
    Run: ollama pull nonexistent:1b`, exit `1`.
  - **Step 6:**
    - 5 traces under each filter, tagged `provider:<p>` and
      `model:qwen3:8b` / `model:claude-haiku-5-5`;
    - each `model-call` with model and token counts;
    - no cost on the Ollama ones.
    - Until §5 ships, each Anthropic run also shows extra
      `anthropic.messages.create` traces, which §5 removes. They are not a
      §2 defect.
  - **Step 7:** only `127.0.0.1:11434`, plus the Langfuse port when tracing
    is on.
  - **If something differs:**
    - Tool calls failing in step 3 (no products named, or an Ollama 400
      about `tool_name`) is a defect.
    - Traces without tags in step 6 is a defect in the tag mechanism.

    Either way, leave `live_checked:` empty.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/2-local-model` at 462c9b1, `git status --short` showing only `?? .idea/` before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "61 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "168 passed".
  Matches the reviewer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL, exit 1, with only
  the owed-live-check error. Matches.
- **Coordinator, re-run:** K01, K02, K04 and K05 with my harness (backup by
  copy, one replacement, file-changed assertion, full `pytest -q -x`,
  restore by copy), each KILLED:
  - K01 by test_cli_ollama::test_default_provider_is_ollama_without_a_key;
  - K02 by test_cli::test_happy_path_prints_answer_exit_0;
  - K04 by test_cli_ollama::test_anthropic_without_key_keeps_the_missing_key_message;
  - K05 by test_cli::test_happy_path_prints_answer_exit_0.

  Each matches the reviewer's killed result. With `-x` I see the first
  failing test, which is among those the reviewer lists.
- **Coordinator:** before the review, `verify` failed on ruff E501 at
  `cli.py:74` after 79cf6b9. Fixed in 5511a2d (line wrap only), and green
  again.

**Reviewer, verified:**
- HEAD 462c9b1, merge base dfb0811; nothing pushed.
- The scoped diff read in full.
- No leftover `key_variable` in `src`/`tests` (except an accurate test
  name).
- The missing-key message is byte-identical (`cli.main` probe: rc 1,
  `'Missing ANTHROPIC_API_KEY: set it in the environment or in .env.\n'`).
- `verify` and `check:intent`.
- `sdlc:scan --sample-due auto --exclude 2` → "nth attested auto change =
  1, every 3, sampled: no".
- 9 mutants (harness `…/scratchpad/mut2r3/mut.py`).
- The merge-tree test-merge: 173 passed.
- The `.env` files on `main`: variable names only.

**Taken on trust:**
- the Ollama API shape;
- the Langfuse v4 server's handling of `langfuse.trace.tags`;
- the 5 GB size;
- the plan's `qwen3:8b` check;
- the earlier rounds' kills on unchanged targets.

# Round 2 (history)

- verdict: escalate
- tier: reviewed
- reviewed-commit: 40314e0be83a808ade4a40aaa8ea6c5a1c0833da
- round: 2
- sampled: no
- run: auto
- live-check: owed

The rework closes every round-1 rework finding with tests and Progress text
only (`git diff a7ff0fe HEAD -- src` is empty). No finding needs rework,
and the tier is Reviewed, so the verdict is escalate: the owner reads the
diff. The live check is still owed.

Tier: Reviewed, set by the path table (input 1). The branch diff touches
`src/advisor/cli.py`, `config.py`, `.env.example` and `tracing.py`.
`review_tier: reviewed` agrees.

Scope: a7ff0fe..40314e0 — c32fbc6 (the rework: `tests/test_models.py`,
`tests/test_ollama_model.py`, plan Progress), 80a34c7 (the round-1 review),
40314e0 (`auto_round: 2`).

### Round-1 findings: resolution
| Round-1 finding | Resolution |
| --- | --- |
| HIGH `models/__init__.py:31,:35`: `make_client` wiring unproven (M02, R03, R04) | resolved: M02 and R04 killed by `test_make_client_ollama_passes_model_and_base_url_through` (`tests/test_models.py:43`); R04 also by `…_defaults_the_base_url` (`:49`); R03 by `test_make_client_anthropic_passes_the_key_to_the_sdk` (`:55`) |
| LOW `base.py:21,:25`: error types not pinned as `ModelError` (B01, B02) | resolved: `test_ollama_error_types_are_model_errors` (`tests/test_models.py:61`) |
| LOW `ollama_model.py:135`: only a 500 tested (M25) | resolved: a 400 with a `message` body; killed by `test_other_failures_are_plain_model_errors[response1]` |
| LOW `ollama_model.py:46`: IPv6 branch unexercised (M39) | resolved: `test_ipv6_host_keeps_its_brackets_in_the_message` |
| LOW Progress "was 128" | resolved: "was 104" (`plan.md:285`); `main` collects 104 |
| LOW ca0eca7 not verify-green | resolved by recording: Progress (`plan.md:311-314`) names the commit, what was red, and that 20c9316 restores green. History not rewritten |
| LOW M42 (`"tool_calls": null`) | open, Worth a look (near-equivalent) |
| LOW tags via private `_otel_span` | open, Worth a look: the live check (step 6) settles it |
| LOW default URL defined twice | open, Worth a look |
| LOW every 404 → B11 | open, Worth a look (settled by the plan) |
| Pass 9 candidate (wiring every test bypasses with a fake) | open: an owner edit to `REVIEW-POLICY.md` |
| M40 | equivalent; no action |

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass (tests and Progress only, as round 1 asked) |
| 2 | Type check | pass (FAIL only on the owed live check: the owner's to clear) |
| 3 | Behaviour against the spec | pass (`src` unchanged since round 1; AC10 is the live check) |
| 4 | Tests prove the behaviour, not only pass | pass (7 round-1 survivors killed, 7 extra mutants killed; M42, M40 equivalent) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1, LOW, Worth a look) |
| 7 | Documentation | pass (no behaviour change, nothing to document) |
| 8 | Guardrails and hygiene | pass (no new dependency; placeholders only) |
| 9 | Repository-specific footguns | pass (round-1 candidate stands for the owner) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: FAIL (intent 2, feature)
  error: A live check is owed and not recorded. Do the steps in intents/2-local-model/review.md → ## Live check, then set live_checked: <date> in intents/2-local-model/metadata.yml.
  note:  21 file(s), 977 line(s) changed outside intents/.
```
The only error is the owed live check (`live_checked:` empty): the owner's
to clear, not rework.

### Findings
- **LOW** `intents/2-local-model/plan.md:320-321` (Progress, rework entry) —
  it says `test_make_client_ollama_defaults_the_base_url` "also guards
  M02". Under M02 the full suite without `-x` gives "1 failed, 167 passed",
  and the failure is only the passes-through test. The defaults test guards
  R04 (2 failures without `-x`), X01 and X02. "1 failure each" holds only
  under `-x`. Coverage is not overstated. Worth a look: reword to "also
  guards R04 and the default URL" (the implementer's to edit).
- **LOW** `tests/test_models.py:43-58` — the wiring tests read private
  attributes (`client._model`, `client._base_url`, `client._sdk.api_key`):
  fragile against a rename, but a rename fails loudly. Building the real
  `anthropic.Anthropic` has precedent on `main` and does not connect. Worth
  a look.
- Nit: the build entry's "162 pytest tests" was true of the build commit;
  the suite is now 168.

Mutants this round (backup by copy, exactly-once binary replacement,
`git diff --quiet` non-zero asserted, full `pytest -q -x`, restore by copy
in `finally`):

| id | change | result | killing test |
| --- | --- | --- | --- |
| M02 | `base_url=base_url or DEFAULT_BASE_URL` → `base_url=DEFAULT_BASE_URL` | KILLED | test_models::test_make_client_ollama_passes_model_and_base_url_through |
| R03 | `api_key=api_key or ""` → `api_key=""` | KILLED | test_models::test_make_client_anthropic_passes_the_key_to_the_sdk |
| R04 | `OllamaClient(model=model,` → `model="qwen3:8b",` | KILLED | test_make_client_ollama_passes_model_and_base_url_through (also …_defaults_the_base_url) |
| B01 | `ModelUnreachableError(ModelError)` → `(Exception)` | KILLED | test_models::test_ollama_error_types_are_model_errors |
| B02 | `ModelNotAvailableError(ModelError)` → `(Exception)` | KILLED | test_models::test_ollama_error_types_are_model_errors |
| M25 | `if not response.is_success:` → `if response.status_code >= 500:` | KILLED | test_ollama_model::test_other_failures_are_plain_model_errors[response1] |
| M39 | `if ":" in host:` → `if False:` | KILLED | test_ollama_model::test_ipv6_host_keeps_its_brackets_in_the_message |
| M42 | `.get("tool_calls") or []` → `.get("tool_calls", [])` | survived (near-equivalent) | — |
| M40 | `parts.path.rstrip('/')` → `parts.path` | survived (equivalent) | — |
| X01 | `or DEFAULT_BASE_URL` → `or ""` | KILLED | test_make_client_ollama_defaults_the_base_url |
| X02 | `DEFAULT_BASE_URL` → `…:11435` | KILLED | test_make_client_ollama_defaults_the_base_url |
| X03 | `base_url.rstrip("/")` → `base_url` | KILLED | test_make_client_ollama_passes_model_and_base_url_through |
| X04 | `Anthropic(api_key=api_key)` → `api_key="placeholder"` | KILLED | test_make_client_anthropic_passes_the_key_to_the_sdk |
| X05 | `host = f"[{host}]"` → `host = host` | KILLED | test_ipv6_host_keeps_its_brackets_in_the_message |
| X06 | `== 404` → `in (400, 404)` | KILLED | test_other_failures_are_plain_model_errors[response1] |
| X07 | `AnthropicClient(…, model=model)` → `model="zz"` | KILLED | test_make_client_anthropic_passes_the_key_to_the_sdk |

The round-1 table's 65 kills were not re-run: `src` is unchanged and tests
were only added, so an added test cannot un-kill a mutant.

### Not checked
Carried from round 1 (`src` unchanged):
- **Real Ollama 0.40.9** (rule 3):
  - `tool_name` on tool messages, and `think` and `num_ctx` honoured;
  - the usage counts' shape;
  - whether `qwen3:8b` emits tool calls and names catalogue products.
- **Whether the Langfuse server reads `langfuse.trace.tags`** from a
  `start_observation` root (rule 3).
- **Smaller items:**
  - Langfuse not pricing `qwen3:8b`;
  - the "about 5 GB" figure;
  - the real `--debug` traceback with `user:pw@` in the URL;
  - proxy settings on the `httpx.Client`.
- **Ship preconditions after `main` moved:** `main` changed in `intents/`
  only, so there is no code conflict, but no test-merge was done.

### Live check
- owed: rule 1 (`src/advisor/cli.py`, `src/advisor/models/`,
  `src/advisor/tracing.py`), and rule 3 (the real Ollama `/api/chat` round
  trip; the server reading `langfuse.trace.tags`). Unchanged since round 1.
  The rework is done, so it can be run now.
- steps (Windows PowerShell, in the worktree):
  1. ```
     cd C:\Users\eric\src\product-advice-agent-wt\2-local-model
     Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL, Env:ANTHROPIC_API_KEY, Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue
     ```
     No `.env` in this folder or a parent (`…\product-advice-agent-wt\`,
     `C:\Users\eric\src\`) may set `ADVISOR_MODEL_PROVIDER`.
  2. Start Ollama (the app, or `ollama serve`); run `ollama pull qwen3:8b`,
     then `ollama list`.
  3. `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
     then `$LASTEXITCODE`.
  4. Quit Ollama; repeat step 3.
  5. Start Ollama; `$env:ADVISOR_MODEL = "nonexistent:1b"`; repeat step 3;
     then `Remove-Item Env:ADVISOR_MODEL`.
  6. Tags:
     1. Start the local Langfuse (README).
     2. Set `$env:LANGFUSE_HOST`, `$env:LANGFUSE_PUBLIC_KEY` and
        `$env:LANGFUSE_SECRET_KEY`.
     3. Run the README's 5 "Comparing providers" questions with the default.
     4. Set `$env:ADVISOR_MODEL_PROVIDER = "anthropic"` and
        `$env:ANTHROPIC_API_KEY`, and run the 5 again.
     5. In Langfuse → Traces, filter by `provider:ollama`, then
        `provider:anthropic`.
  7. Optional (B16): during step 3, `Get-NetTCPConnection -State Established
     | Where-Object OwningProcess -eq (Get-Process python).Id`.
- you should see:
  - **Step 2:** `qwen3:8b` listed.
  - **Step 3:** an answer naming catalogue headphones by name and id
    (P-0xx), exit `0`. The first run can take tens of seconds.
  - **Step 4:** exactly `Ollama is not reachable at http://localhost:11434.
    Start Ollama (the Ollama app, or "ollama serve") and try again.`, no
    traceback, exit `1`.
  - **Step 5:** exactly `Model 'nonexistent:1b' is not available in Ollama.
    Run: ollama pull nonexistent:1b`, exit `1`.
  - **Step 6:**
    - 5 traces under each filter, tagged `provider:<p>` and
      `model:qwen3:8b` / `model:claude-haiku-5-5`;
    - each `model-call` with model and token counts;
    - no cost on the Ollama ones.
  - **Step 7:** only `127.0.0.1:11434`, plus the Langfuse port when tracing
    is on.
  - **If something differs:**
    - Tool calls failing in step 3 (no products named, or an Ollama 400
      about `tool_name`) is a defect.
    - Traces without tags in step 6 is a defect in the tag mechanism.

    Either way, leave `live_checked:` empty.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/2-local-model` at 40314e0, `git status --short` empty before and after):
- **Coordinator, re-run:** `git diff a7ff0fe HEAD -- src` → empty;
  `--stat` → `plan.md`, `review.md`, `tests/test_models.py`,
  `tests/test_ollama_model.py` (plus `metadata.yml`). Matches.
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "61 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "168 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → FAIL, exit 1, with only
  the owed-live-check error. Matches.
- **Coordinator, re-run:** the nine round-1 survivors with my round-1
  harness (backup by copy, one replacement, file-changed assertion, full
  `pytest -q -x`, restore by copy):
  - M02 killed by test_make_client_ollama_passes_model_and_base_url_through;
  - R03 killed by test_make_client_anthropic_passes_the_key_to_the_sdk;
  - R04 killed by test_make_client_ollama_passes_model_and_base_url_through;
  - B01 and B02 killed by test_ollama_error_types_are_model_errors;
  - M25 killed by test_other_failures_are_plain_model_errors[response1];
  - M39 killed by test_ipv6_host_keeps_its_brackets_in_the_message;
  - M40 and M42 SURVIVED ("168 passed").

  Matches the reviewer on all nine, and the implementer's report.

**Reviewer, verified:**
- HEAD 40314e0, merge base dfb0811; nothing pushed.
- `verify` and `check:intent` as above.
- `sdlc:scan --sample-due auto --exclude 2` → "nth attested auto change =
  1, every 3, sampled: no".
- 16 mutants (harness `…/scratchpad/mut2r2/mut.py`).
- The 7 rework mutants also without `-x`: 1 failure each, except R04 with 2.
- The Progress numbers from `git archive` snapshots: 104 at `main`; 13
  failed and 91 passed, plus the mypy error, at ca0eca7; 168 now.
- A grep of the diff for secrets found placeholders only.

**Taken on trust:**
- the Ollama API shape per the spec;
- the server's handling of `langfuse.trace.tags`;
- the 5 GB size;
- the plan's `qwen3:8b` library check;
- the round-1 table's 65 kills.

No real Ollama, Anthropic or Langfuse was contacted; Docker was not started.

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: a7ff0feb8dbfc398b903fafdbddf7d9064516ec8
- round: 1
- sampled: no
- run: auto
- live-check: owed

Tier: Reviewed, set by the path table (input 1). The diff touches
`src/advisor/cli.py`, `src/advisor/config.py`, `.env.example` and
`src/advisor/tracing.py`, all Reviewed by meaning. `review_tier: reviewed`
in `metadata.yml` (input 2) agrees, and the HIGH finding (input 3) would
escalate anyway. Status is `in-review`.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1): commit ca0eca7 not verify-green, against the plan's "each … with `npm run verify` green" |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | pass (B1–B21, AC1–AC9 in code and tests; AC10 is the live check) |
| 4 | Tests prove the behaviour, not only pass | findings (5): 74 mutants, 65 killed, 9 survived (1 equivalent) |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1): Progress says "was 128", `main` has 104 |
| 7 | Documentation | pass |
| 8 | Guardrails and hygiene | pass (`httpx` moved to runtime deps with the plan's why-line; placeholders only) |
| 9 | Repository-specific footguns | pass (list empty; candidate below) |

### Type check
```
> product-advice-agent@0.0.0 check:intent
> node scripts/check-intent.mjs

type-check: PASS (intent 2, feature)
  note:  21 file(s), 936 line(s) changed outside intents/.
```

### Findings

- **HIGH** `src/advisor/models/__init__.py:31`, `:35` — no test proves
  `make_client` passes its arguments to the adapter.
  - Survivors:
    - M02: `base_url=base_url or DEFAULT_BASE_URL` → `base_url=DEFAULT_BASE_URL`;
    - R04: `OllamaClient(model=model, …)` → `model="qwen3:8b"`;
    - R03: `api_key=api_key or ""` → `api_key=""`.
  - Why the suite misses it: every CLI test injects a fake
    `client_factory`, and `tests/test_models.py:28` asserts only
    `isinstance`.
  - What could ship green: `ADVISOR_OLLAMA_URL` ignored (B5),
    `ADVISOR_MODEL` ignored for Ollama (B1, and AC10's `nonexistent:1b`
    step), or the Anthropic key dropped (§1 B7).
  - The code is correct today; a probe confirmed the wiring. The gap is the
    tests: the plan's first named risk.
  - Needs rework: in `tests/test_models.py`, assert:
    - `make_client("ollama", "m-x", base_url="http://box:9/")` yields a
      client with model `m-x` and base URL `http://box:9`, via its
      attributes or one `complete` over `httpx.MockTransport`;
    - `make_client("ollama", "m")` with no `base_url` uses
      `http://localhost:11434`;
    - `make_client("anthropic", "m", api_key="placeholder-key")` gives an
      SDK client whose `api_key == "placeholder-key"`, built without
      connecting.

    Kills M02, R03, R04.
- **LOW** `src/advisor/models/base.py:21`, `:25` — no test asserts that
  `ModelUnreachableError` and `ModelNotAvailableError` subclass
  `ModelError`; mutants B01 and B02 (base changed to `Exception`) survive.
  Plan subtask 2 makes this the contract. Needs rework: `assert
  issubclass(ModelUnreachableError, ModelError) and
  issubclass(ModelNotAvailableError, ModelError)`. Kills B01, B02.
- **LOW** `src/advisor/models/ollama_model.py:135` — only a 500 is tested as
  "other HTTP error" (B12). M25 (`not response.is_success` →
  `status_code >= 500`) survives: a non-404 4xx with a `message` body
  would be read as a turn. Needs rework: add `httpx.Response(400,
  json={"message": {"role": "assistant", "content": "x"}})` to
  `test_other_failures_are_plain_model_errors`. Kills M25.
- **LOW** `src/advisor/models/ollama_model.py:46` — the IPv6 bracket branch
  of `_display_url` is never exercised; M39 (branch removed) survives. The
  URL is the user-facing B10 text. Needs rework: a connect-error test with
  base `http://[::1]:11434` asserting the message contains
  `http://[::1]:11434`. Kills M39.
- **LOW** `intents/2-local-model/plan.md` (Progress) — "162 pytest tests
  (was 128 …)". 162 is right; `main` at dfb0811 collects **104** (a `git
  archive` snapshot, `--collect-only`). Needs rework: change "was 128" to
  "was 104" (below the Progress marker: the implementer's to edit).
- **LOW** commit `ca0eca7` — not verify-green on its own. A `git archive`
  snapshot gives pytest "13 failed, 91 passed" and one mypy error
  (`cli.py:36`, incompatible default for `client_factory`). It hurts only
  bisecting after the `--no-ff` merge; HEAD is green. Needs rework: record
  the deviation in `## Progress` (which commit, what was red, that 20c9316
  restores green). Rewriting history instead is the owner's choice and not
  required.
- **LOW** `src/advisor/models/ollama_model.py:141` — M42 (`.get("tool_calls")
  or []` → `.get("tool_calls", [])`) survives; it differs only on
  `"tool_calls": null`, which Ollama does not send (it omits the field).
  Worth a look: a one-line `null` fixture would pin it.
- **LOW** `src/advisor/tracing.py:93` — tags are set through the SDK's
  private `_otel_span`. The in-memory exporter test runs the real SDK, so an
  SDK change that drops it fails a test rather than silently; in production
  `SafeTracer` would drop only the tags. Whether the server reads
  `langfuse.trace.tags` from a `start_observation` root is the live check's.
  Worth a look.
- **LOW** `src/advisor/models/ollama_model.py:36` vs `src/advisor/config.py:25`
  — the default URL is defined twice (`DEFAULT_BASE_URL`,
  `DEFAULT_OLLAMA_URL`). The spec's single-place rule covers only the model
  id, which holds. Worth a look.
- **LOW** `src/advisor/models/ollama_model.py:132` — every HTTP 404 becomes
  the B11 "pull the model" message; spec B11 says "HTTP 404 naming the
  model", and the approved plan narrowed it to "HTTP 404". With
  `ADVISOR_OLLAMA_URL` at a non-Ollama server, the user is told to pull a
  model. Settled by the plan: Worth a look.
- **Pass 9 candidate:** "factory or registry wiring that every test
  bypasses with an injected fake" — the plan's first risk recurred as the
  HIGH above. An owner edit to `REVIEW-POLICY.md`, not part of this rework.

Mutants (74; full `pytest -q -x` each; backup by copy, `git diff --quiet`
non-zero asserted, restore by copy). Survivors: M02, R03, R04 (HIGH); B01,
B02, M25, M39 (LOW); M42 (near-equivalent); M40 (`parts.path.rstrip('/')` →
`parts.path`, equivalent: `__init__` already strips). The other 65 are
killed:
- the request body (M01, M03–M10);
- the message mapping (M11–M19);
- the error mapping (M20–M24, M26–M28);
- the response mapping (M29–M37);
- `_display_url` (M38, M41);
- the registry (R01, R02);
- config (C01–C08);
- the CLI (L01–L13);
- tracing (T01–T05).

The full table is in the reviewer's report. The plan's named risks were
handled well otherwise:
- request bodies are compared whole;
- fixtures differ from the outputs (served model name, string arguments,
  reversed result order);
- the existing CLI tests now set `ADVISOR_MODEL_PROVIDER=anthropic`, so they
  kept their meaning.

### Not checked
- Real Ollama:
  - whether 0.40.9 accepts `tool_name` on tool messages, and honours `think`
    and `num_ctx`;
  - the `prompt_eval_count`/`eval_count` shape;
  - whether `qwen3:8b` emits tool calls and names catalogue products.

  Rule 3.
- Whether the Langfuse server reads `langfuse.trace.tags` from a
  `start_observation` root and shows it as filterable tags. Rule 3.
- Langfuse not pricing `qwen3:8b` (only "no cost attribute sent" is shown).
- The README's "about 5 GB" for `qwen3:8b`.
- The real `--debug` traceback for a connect error with `user:pw@` in the
  URL: the chained httpx exception may show it, in debug output only.
- Proxy settings (`HTTP_PROXY`, `trust_env`) on the `httpx.Client`, which
  could route localhost traffic through a proxy.
- Ship preconditions after `main` moved (dfb0811 → 82bb545, intent
  artefacts of §3 and §4 only): not test-merged.

### Live check
- owed:
  - rule 1: the diff touches `src/advisor/cli.py`, `src/advisor/models/` and
    `src/advisor/tracing.py`;
  - rule 3: the real Ollama `/api/chat` tool-call round trip, and the
    server reading `langfuse.trace.tags`.

  Run after the rework.
- steps (Windows PowerShell, in the worktree):
  1. ```
     cd C:\Users\eric\src\product-advice-agent-wt\2-local-model
     Remove-Item Env:ADVISOR_MODEL_PROVIDER, Env:ADVISOR_MODEL, Env:ANTHROPIC_API_KEY, Env:ADVISOR_OLLAMA_URL -ErrorAction SilentlyContinue
     ```
     No `.env` in this folder or a parent (`…\product-advice-agent-wt\`,
     `C:\Users\eric\src\`) may set `ADVISOR_MODEL_PROVIDER`; the worktree
     has none today.
  2. Start Ollama (the app, or `ollama serve`); run `ollama pull qwen3:8b`,
     then `ollama list`.
  3. `uv run advisor "I need noise-cancelling headphones under 200 euros"`,
     then `$LASTEXITCODE`.
  4. Quit Ollama; repeat step 3.
  5. Start Ollama; `$env:ADVISOR_MODEL = "nonexistent:1b"`; repeat step 3;
     then `Remove-Item Env:ADVISOR_MODEL`.
  6. Tags:
     1. Start the local Langfuse (README).
     2. Set `$env:LANGFUSE_HOST`, `$env:LANGFUSE_PUBLIC_KEY` and
        `$env:LANGFUSE_SECRET_KEY`.
     3. Run the README's 5 "Comparing providers" questions with the default.
     4. Set `$env:ADVISOR_MODEL_PROVIDER = "anthropic"` and
        `$env:ANTHROPIC_API_KEY`, and run the 5 again.
     5. In Langfuse → Traces, filter by `provider:ollama`, then
        `provider:anthropic`.
  7. Optional (B16): during step 3, `Get-NetTCPConnection -State Established
     | Where-Object OwningProcess -eq (Get-Process python).Id`.
- you should see:
  - **Step 2:** `qwen3:8b` listed.
  - **Step 3:** an answer naming catalogue headphones by name and id
    (P-0xx), exit `0`. The first run can take tens of seconds.
  - **Step 4:** exactly `Ollama is not reachable at http://localhost:11434.
    Start Ollama (the Ollama app, or "ollama serve") and try again.`, no
    traceback, exit `1`.
  - **Step 5:** exactly `Model 'nonexistent:1b' is not available in Ollama.
    Run: ollama pull nonexistent:1b`, exit `1`.
  - **Step 6:**
    - 5 traces under each filter, tagged `provider:<p>` and
      `model:qwen3:8b` / `model:claude-haiku-5-5`;
    - each `model-call` with model and token counts;
    - no cost on the Ollama ones.
  - **Step 7:** only `127.0.0.1:11434`, plus the Langfuse port when tracing
    is on.
  - **If something differs:**
    - Tool calls failing in step 3 (no products named, or an Ollama 400
      about `tool_name`) is a defect.
    - Traces without tags in step 6 is a defect in the tag mechanism
      (`_otel_span` attribute vs `propagate_attributes`).

    Either way, leave `live_checked:` empty.

### Verified myself vs. taken on trust

**Coordinator, re-run** (in `C:/Users/eric/src/product-advice-agent-wt/2-local-model` at a7ff0fe, `git status --short` empty before and after):
- **Coordinator, re-run:** `npm run verify` → exit 0; kit `tests 255, pass
  255, fail 0`; ruff "All checks passed!"; "60 files already formatted";
  mypy "Success: no issues found in 12 source files"; pytest "162 passed".
  Matches the reviewer and the implementer.
- **Coordinator, re-run:** `npm run check:intent` → PASS, exit 0 (above).
  Matches.
- **Coordinator, re-run:** the 9 survivors with my own harness (backup by
  copy, exactly one replacement, file-changed assertion, full `pytest -q
  -x`, restore by copy).
  - M02, R03, R04, B01, B02, M25, M39 (`if ":" in host:` → `if False:`),
    M40 and M42 each SURVIVED, with "162 passed".
  - Matches the reviewer on all 9.
- **Coordinator, re-run:** `git status --short` empty after the mutants.

**Reviewer, verified:**
- HEAD a7ff0fe, merge base dfb0811, nothing pushed.
- `npm run verify` and `check:intent`, as above.
- `sdlc:scan --sample-due auto --exclude 2` → "nth attested auto change = 1,
  every 3, sampled: no".
- `agent.py`, `catalogue.py`, `guardrails.py` and `prompts/` are unchanged;
  `infra/` and `.claude/` are untouched.
- 74 mutants (harness `…/scratchpad/mut2/mut.py`, CRLF-aware).
- `main` snapshot collects 104 tests.
- `ca0eca7` snapshot: 13 failed, 91 passed, plus 1 mypy error.
- An end-to-end probe against the real modules:
  - `make_client` wiring returns `m-x http://box:9`;
  - the real CLI with `ADVISOR_OLLAMA_URL=http://usr:pw@127.0.0.1:1` (a
    refused local port) printed the B10 text with credentials stripped, rc 1;
  - a MockTransport 404 printed the B11 text;
  - a 500 printed the generic text.
- The AC9 docs were read.
- A grep of the diff for secrets found placeholders only.

**Taken on trust:**
- the Ollama API shape (`tool_name`, `think`, the 404 body), per the
  spec's citation;
- the server's handling of `langfuse.trace.tags`;
- the 5 GB model size;
- the plan's library check for `qwen3:8b`.

No real Ollama, Anthropic or Langfuse was contacted; Docker was not started.
