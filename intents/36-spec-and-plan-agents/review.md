<!-- generated-by: product-advice-agent/review@0.2.0 -->
# §36 review — Dedicated spec and plan agents on Sonnet

verdict: rework
tier: reviewed
reviewed-commit: 44b7238
main: cfef98f
round: 1
sampled: no
run: auto
live-check: not-needed

Tier: Reviewed by path (`.claude/agents/**`, `.codex/agents/**`,
`.claude/skills/**`, plus `CLAUDE.md` and `AGENTS.md`). The verdict is
`rework` because of one HIGH finding (a test that can never fail) and two
"Needs decision" findings; once they are handled the change still goes to
the owner's diff read.

## Passes

| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | one finding (2): the Codex `sandbox_mode` was left out against the spec |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (2, 6, 7): `sandbox_mode`; `intents/README.md` contradicts B4/B6; the B10 check is a weak backstop |
| 4 | Tests prove the behaviour | findings (1, 3, 4, 5): AC3 can never fail; AC4 for `/auto`, B5 and the AC6 tokens are not pinned |
| 5 | Conventions | pass: no product code, nothing pushed, `main` untouched |
| 6 | Numbers in prose | pass: 64 stats-lib tests, 19 kit-texts tests, 994 pytest, all reproduced |
| 7 | Documentation | findings (6, 8): `intents/README.md` "Who edits what"; `/auto` section 10 |
| 8 | Guardrails and hygiene | one finding (10): control bytes in a test file; no new dependency, no secret |
| 9 | Repo-specific footguns | a new one to list (below) |

## Type check

```
type-check: PASS (intent 36, feature)
  note:  12 file(s), 236 line(s) changed outside intents/.
```

## Findings

1. **HIGH, Needs rework** `scripts/kit-texts.test.mjs:147`: the AC3 check
   ("no `Edit` in the tools line") never fails. The test means `/\bEdit\b/`,
   but the file holds two literal backspace bytes (0x08), not `\b`, so the
   regex only matches "Edit" with a backspace on each side and
   `expect(...).toBe(false)` always passes. The plan's own mutation, adding
   `Edit` to a tools line, survives the full suite in both Claude files.
   Write the regex with a real backslash, check that the file has no byte
   below 0x20 other than tab, newline and carriage return where intended, and
   confirm the mutant is now killed.
2. **MEDIUM, Needs decision (owner)**
   `.codex/agents/product-advice-agent-{spec,plan}.toml`: B2 and AC1 of the
   accepted spec require `sandbox_mode = "workspace-write"`; both files leave
   it out and the test does not assert it. The plan allowed leaving it out
   only if the owner found the value rejected. The omission came from the
   coordinator's brief to the implementer ("follow the plan's fallback"),
   which the plan did not warrant: that was the coordinator's mistake. Without
   the line the agent takes the parent session's sandbox (read-only: it cannot
   write; full access: wider than the spec wants); the mutant that adds
   `sandbox_mode = "read-only"` survives. Options: (a, recommended) add the
   line and an assertion, as the accepted spec says (the key already exists in
   the reviewer's Codex file with "read-only", and workspace-write is the
   documented narrower-than-full value); (b) amend spec B2/AC1 to "no
   `sandbox_mode`, inherits the session's".
3. **MEDIUM, Needs rework** `scripts/kit-texts.test.mjs:159-164`: AC4 is half
   tested for `/auto`: only the two agent names. These mutants survive the full
   suite: deleting `§<id> spec` or `§<id> plan` from `/auto` (SKILL.md:116,
   :139), deleting its "git status --short and git diff --stat check"
   sentences (:116-117, :139-140), deleting "(or replies `INCOMPLETE:`)"
   (:118). Assert that the `/auto` text contains `§<id> spec`, `§<id> plan`,
   `git status --short`, `git diff --stat` and `INCOMPLETE:`.
4. **MEDIUM, Needs rework** `scripts/kit-texts.test.mjs:107,130-132`: B5 and
   B6 are not pinned in the agent files. `INCOMPLETE:` also appears elsewhere,
   so deleting all of rule 8 ("Never decide a design point ... options and a
   recommendation") survives in all four files; deleting rule 6's "name it in
   your reply; the coordinator records `blocked_by:`" and rule 5's list of
   forbidden git commands survive too. Add `Never decide a design point`,
   `options and a recommendation` and the `blocked_by` sentence to `PHRASES`.
5. **MEDIUM, Needs rework** `scripts/stats-lib.test.mjs:562-575`: AC5 and AC6
   (tokens) are not proven. Both new tests assert only `agentWorkMs`; the
   mutant that routes the spec and plan runs' tokens to "unattributed"
   survives. Assert non-zero `tokens` for the `spec` and `plan` phases under
   `agents`, and that the unattributed bucket holds only the `Explore` run.
6. **MEDIUM, Needs rework** `intents/README.md:142-146` (the `blocked_by`
   bullet) says "any agent drafting or revising an intent, spec or plan writes
   it without your yes"; the new agents' rule 6 and the spec (B4, B6) say the
   agent reports a prerequisite and the coordinator writes it. `CLAUDE.md`
   says `intents/README.md` wins on a conflict, so the stricter rule can be
   overridden as written. "Who edits what" (:155-164) also has no line for the
   spec and plan agents. Add "except the spec and plan subagents, which report
   it; the coordinator writes it" to that bullet, and a role bullet: "The spec
   and plan agents write their one `spec.md` or `plan.md`, nothing else, and
   record no gate."
7. **MEDIUM, Needs decision (owner)** `.claude/skills/spec/SKILL.md:31-34` and
   `build-plan/SKILL.md:32-35`: the B10 after-check is a weak backstop. A
   freshly drafted `spec.md` or `plan.md` is untracked, so `git diff --stat`
   shows nothing for it or for any other new file; in the main checkout
   `git status --short` already lists unrelated untracked files (`.idea/`,
   `.vscode/`, `counts.md`, `evals/generated*.jsonl`, `generated
   questions.md`), so "only the one file changed" cannot be judged without a
   before-snapshot; writes to gitignored paths (`.env`, `CLAUDE.local.md`)
   are invisible. Option (recommended): take `git status --short` before the
   spawn and compare after, in B10 and both skills (this changes the spec's
   procedure); the alternative is to leave B10 as accepted and note the
   limit in the skills.
8. **LOW, Needs rework** `.claude/skills/auto/SKILL.md:377-379` (section 10):
   the prefix list still says `§<id> implement`, `§<id> rework` or
   `§<id> review`; add `§<id> spec` and `§<id> plan`.
9. **LOW, Needs rework** `AGENTS.md:15-20`, `CLAUDE.md:64-67` and the skills:
   B12 is half pinned: deleting "not by reading the codebase inline" from
   `AGENTS.md`, "keeps every gate" or "(descriptions ...)" from `CLAUDE.md`,
   the skills' "Confirm that only ... changed" sentence, the step-6
   parenthetical and build-plan's step-3 "this stop is its `INCOMPLETE:`
   reply" all survive. Pin `not by reading` in `AGENTS.md`, `keeps every
   gate` in both guides and `Confirm that only` in both skills.
10. **LOW, Needs rework** `scripts/kit-texts.test.mjs:117`: the character class
    holds a literal tab and a literal carriage return; git classifies the file
    as binary (`git ls-files --eol` gives `i/-text`) so autocrlf skips it.
    Write `[ \t]*` with escapes or drop the class.
11. **LOW, Needs rework** `.claude/skills/auto/SKILL.md:115-118`: "...run its
    `git status --short` and `git diff --stat` check, including its single
    question round" attaches the question round to the check; move
    "including its single question round" after "as `/spec` says".
12. **LOW, Needs rework** `.codex/agents/*-{spec,plan}.toml` rule 5: "Use
    `Bash` for read-only reads only": Codex has a shell tool, not one called
    `Bash`; say "the shell".
13. **LOW, no action**: commit `c7330b7` also holds the first version of the
    four agent files (a background `verify && git add -A`), rewritten by
    `0e8497b`. The final diff is correct.

Footgun for pass 9: control bytes (0x00-0x08, 0x0b-0x1f) in a changed test or
text file. An escaping layer can turn a regex `\b`, `\t` or `\r` into a raw
byte, which makes a test a no-op and which the diff display hides. Check:
scan the bytes of every changed file.

## Mutations

Reviewer: on `git archive HEAD` copies (never the worktree), the full kit
suite (500 tests) or `kit-texts.test.mjs`. Killed: the stats regex without
`spec`, without `plan`, without `\b`, with `spec\w*|plan\w*` and with
`(\w+)`; `AGENT_PHASE` spec to build, plan to build, spec to plan, and with
either dropped; the AC6 mutant that skips a run when git has no phase of
that name; all 7 pinned phrases deleted from each of the 4 agent files; the
skill pointer, the stamp, `name:` or `name =` renamed and the description
deleted in each file; `Write` or `Bash` removed and `model: opus` in both
Claude files; in `/spec` and `/build-plan` the agent name, `§<id> spec|plan`,
`git status --short`, `git diff --stat`, and ``pass a `model` ``; in `/auto`
each agent name and reverting step 2; in `CLAUDE.md` each agent name and
"not by reading the codebase inline"; in `AGENTS.md` each Codex name.
Survived: those named in findings 1 to 5, 8 and 9, plus deleting the reply
line "the file path, or `INCOMPLETE:` and why" (not required to kill).

## Agent definitions: usable?

- Claude files: the frontmatter parses as YAML with exactly `name`,
  `description`, `tools`, `model`, the same shape as the implementer and
  reviewer; tools `Read, Write, Grep, Glob, Bash` (no `Edit`); model `sonnet`.
- Codex files: both parse with `tomllib`; keys `name`, `description`,
  `developer_instructions`, as the implementer's file (no `sandbox_mode`,
  finding 2); names use underscores like the existing ones.
- Hand-off rules (B1) are present in all four files: follow the skill; reply
  `INCOMPLETE:` with options and a recommendation; never commit; never edit
  `metadata.yml` or record a gate; write exactly one file; a private uniquely
  named scratch folder; a reply of at most 250 words; a prerequisite is
  reported, not written. Not enforced: `Bash` can write anywhere; the
  statement that the coordinator checks afterwards lives in the skills (and
  finding 7 shows the check is weak).

## Line endings

No `.gitattributes`, `core.autocrlf=true`, every file in the index is LF. New
files are LF in the worktree, existing ones kept CRLF; a fresh checkout gives
CRLF and the kit tests pass on a CRLF copy (500 of 500). The one exception is
`kit-texts.test.mjs` (finding 10).

## Not checked

- Whether Claude Code lists `product-advice-agent-spec` and `-plan` as
  `subagent_type` (it may need a session restart); not spawned.
- Whether Codex accepts these files and whether its default sandbox lets the
  agent write its file (finding 2).
- How a real Sonnet agent behaves under these rules (AC8).

## Live check

not-needed: no path of rule 1 is touched, and `git diff --name-only main...`
lists nothing under `src/advisor/`. AC8 is the owner's manual step.

## Eval run

not owed (no listed path): `uv run advisor-analysis owes-run --base main`
prints "not owed (no listed path changed)".

## Owner checklist for the diff read (after the rework)

1. The four agent files: `tools:` has no `Edit`; `model: sonnet`; rules 3 and
   5 to 8; the spec agent's rule 8 lets it write a draft with defaults plus
   questions, the plan agent's never does; the Codex sandbox line.
2. `/spec` and `/build-plan` "Who drafts": the after-check and the `model`
   override wording; the step-6 parenthetical about `blocked_by`.
3. `/auto` steps 2 and 3: nothing lets an agent record a gate; `INCOMPLETE:`
   maps to the existing stops.
4. `CLAUDE.md:64-67`, `AGENTS.md:15-20` and `intents/README.md`.

Owner steps after the merge (AC8): restart Claude Code (or open a new
session) and confirm `product-advice-agent-spec` and `-plan` appear in the
`Agent` tool listing; run a real `/spec` or `/build-plan` and take
`git status --short` before and after; run `npm run stats -- <id>` and see
the agent's tokens in the `spec` or `plan` row; spawn the Codex agent once and
confirm it can write its file; then the coordinator updates the memory note
`delegate-spec-plan-drafting` to a one-line pointer to `CLAUDE.md`.

## Verified myself vs. taken on trust

- Verified myself (Coordinator, re-run): the branch update (`update-branch`
  exit 0, merged `main` at `9b9e9ac`, `verify` green at the merge: 994 pytest
  and the kit tests); no mutant survives that a rework in this round would
  not re-test: the survivors are re-run after the rework.
- Verified by the reviewer: `npm run verify` exit 0 (kit 500 of 500, ruff,
  mypy, 994 pytest), `npm run check:intent` PASS, `npm run test:kit` twice
  (500 of 500), YAML and TOML parsing, the byte scan, the CRLF run,
  `owes-run`, the Progress numbers and all the mutants above.
- Taken on trust: the plan's claim that `codex exec --help` lists
  `workspace-write`; the implementer's account of how `c7330b7` came to hold
  the agent files.
