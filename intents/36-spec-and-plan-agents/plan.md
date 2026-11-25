<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §36 plan — Dedicated spec and plan agents on Sonnet

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Add two drafting agents for Claude and Codex (four files:
`product-advice-agent-spec` and `product-advice-agent-plan`), each on Sonnet
with the shared hand-off rules written out in full; make `/spec`,
`/build-plan` and `/auto` name them and tell the coordinator to check the
draft with `git status` and `git diff --stat`; put the rule in `CLAUDE.md` and
`AGENTS.md`; and make `npm run stats` book agents described `§<id> spec` or
`§<id> plan` to the `spec` and `plan` phases instead of "unattributed". No
product code changes (B1 to B13, AC1 to AC8).

## Risks

- **Tests that pass whatever the text says.** A `toContain` on a phrase the
  definition never needed proves nothing. Each pinned phrase is one rule, the
  test loops over all four files, and each mutation below deletes that one
  phrase from one file.
- **Rule drift between the four copies.** Duplication is the spec's choice
  (B1); the kit-texts test is the only guard, so it must run over all four.
- **Stats regex too loose or too tight.** `§36 specify` and `§36 planning`
  must stay unattributed (the regex's `\b` handles `specify`, but `plan`
  followed by `ning` too: both are tested). `\b` after `spec` also matches
  `§36 spec-draft`; accepted, it is a tag the coordinator writes itself.
- **Stale line citations.** Every line below was read on `main` at `980886f`;
  re-check before launch (the implementer works in a worktree and `main` may
  have moved).
- **A new `.claude/agents/*.md` may not be listed as a `subagent_type` until
  the session restarts.** Not something a test can show; it is a validation
  step for the owner (below).
- **Skill version.** The skills' stamps stay `spec@0.2.0` and
  `build-plan@0.2.0` (B6 and the spec's AC text fix them); the scan reads any
  version (`scripts/scan-lib.test.mjs:45-46`). So no version bump, unlike §28's
  `/intent` change to 0.3.0; see Assumptions.
- **Codex `workspace-write`.** Checked now, see Verified.

## Verified against the codebase

Re-read on `main` at `980886f`.

- `.claude/agents/product-advice-agent-implementer.md:1-6` — frontmatter
  `name`, `description`, `tools: Read, Write, Edit, Bash, Grep, Glob`,
  `model: sonnet`; the body (from `:7`) is the instruction text.
- `.claude/agents/product-advice-agent-reviewer.md` — same shape, `model:
  opus`, tools `Read, Grep, Glob, Bash` (per the spec's Sources; the agent
  listing in the harness shows the same).
- `.codex/agents/product-advice-agent-implementer.toml:1-4` — `name =
  "product_advice_agent_implementer"` (underscores), `description`, then
  `developer_instructions = """ ... """`; no `sandbox_mode`, no `model`.
- `.codex/agents/product-advice-agent-reviewer.toml:1-4` — adds
  `sandbox_mode = "read-only"` between `description` and
  `developer_instructions`.
- **Codex sandbox values.** `codex exec --help` on this machine (the `codex`
  at `~/AppData/Roaming/npm/codex`) lists `-s, --sandbox <SANDBOX_MODE>`
  `[possible values: read-only, workspace-write, danger-full-access]`. So
  `workspace-write` exists as a value. That is the CLI flag; the agent TOML key
  `sandbox_mode` is the repository's own usage (reviewer toml) and cannot be
  run from here, so the Codex file's behaviour is confirmed by the owner (see
  Validation). Fallback if the owner finds `workspace-write` rejected in an
  agent TOML: omit the `sandbox_mode` line, as the implementer does, and keep
  the instruction text; the kit-texts test then drops its `sandbox_mode`
  assertion for the Codex files (the only code change).
- `scripts/stats-lib.mjs:11` — `PHASE_ORDER = ['intent', 'spec', 'plan',
  'build', 'review', 'live check', 'ship']` (already has both phases).
- `scripts/stats-lib.mjs:16` — `AGENT_PHASE = { implement: 'build', rework:
  'review', review: 'review' }` (not exported).
- `scripts/stats-lib.mjs:164-168` — `agentTag`, regex
  `/^§(\d+)\s+(implement|rework|review)\b/` on the trimmed description, returns
  `{ id: Number, phase: m[2] }` or `null`; the doc comment at `:164` lists the
  three words.
- `scripts/stats-lib.mjs:344-348` — `phase(id, name)` creates the phase entry
  on demand (`tokens: bucket()`, `agentWorkMs: 0`), so a `spec` or `plan` phase
  that has no git span is created, not dropped (AC6).
- `scripts/stats-lib.mjs:399-410` — the agent loop: `agentTag`, `agentSpans`,
  `agentWork.push({ name: AGENT_PHASE[tag.phase], span })`, and
  `addTokens(phase(tag.id, AGENT_PHASE[tag.phase]).tokens, 'agents', ...)`;
  untagged goes to `unattributed`.
- `scripts/stats-lib.mjs:464` — `order(name)` sorts by `PHASE_ORDER`, so
  `spec` and `plan` rows sort where expected.
- `scripts/stats-io.mjs:63-70` — the agent description is read from
  `agent-*.meta.json` and passed on; no regex there, no change.
- `scripts/stats-lib.test.mjs:129-138` — `describe('agentTag (B2)')` with the
  positive cases (`:131-133`) and the loose list (`:136`), which includes
  `'§13 explore'`.
- `scripts/stats-lib.test.mjs:478-481` — helpers `run`, `i7`, `agentRun(desc,
  from, to)`; `:549-553` — the "books agent work by tag" test is the model for
  the new phase test; `ph(it, name)` is used at `:525-528`.
- `scripts/kit-texts.test.mjs:27-28` — `IMPLEMENTERS` and `REVIEWERS` lists;
  `:32-` the first `describe`; `:56-72` a `describe` for §28 that checks the
  skill's `intent@0.3.0` and `read(f)` over several files; `:11-12` `read`.
  The file's `walk` at `:14-22` already covers `.claude` and `.codex` (the
  "no rebase wording" test at `:74-98` reads the new files too, so the new
  agent texts must not contain the old wordings; they will not).
- `.claude/skills/spec/SKILL.md:14-19` — "Follow `intents/README.md` ...";
  the stamp line at `:18-19` (`spec@0.2.0`); `:21` step 1; `:39` step 3
  (Questions); `:67` step 6 (Report, including the `blocked_by:` write).
- `.claude/skills/build-plan/SKILL.md:14-20` — same, stamp
  `build-plan@0.2.0`; step 3 "No question round"; step 6 writes `blocked_by:`.
- `.claude/skills/auto/SKILL.md:110-124` — step 2 "draft it as `/spec` does";
  `:126-139` — step 3 item 1 "Draft the plan as `/build-plan` does"; `:94-96`
  the resume table naming `plan found the spec incomplete`.
- `.claude/skills/spawn/SKILL.md:43-48` — the implementer's description
  `§<id> implement`; spawn says nothing about drafting agents (no change).
- `CLAUDE.md:44-60` — "How work flows" bullets; `:57-61` the bullet "`/intent`
  drafts an intent, `/spec` a feature's spec, `/build-plan` a plan, ..." and
  `:62` "The `product-advice-agent-implementer` agent builds an approved plan,
  and the" (the sentence continues with the reviewer): the new bullet goes
  right after it.
- `AGENTS.md:12-14` — names the skills Codex follows; `:32-33` the gate rule.
  The new rule goes in "Shared Project Context" after `:14`.
- `intents/README.md:90-108` — "Who edits what", `:105-106` "A subagent
  (`product-advice-agent-implementer`, `product-advice-agent-reviewer`, any
  `Agent`-tool worker) never records a gate"; `:166-195` "Drafting an
  artefact" (eight rules the agents' texts point to, not copy).
- `REVIEW-POLICY.md:30` — the Reviewed row lists `.claude/agents/**`,
  `.codex/agents/**`, `.claude/skills/**`. `scripts/stats-lib.mjs` is kit code
  with tests, not on the row by path; `CLAUDE.md` and `AGENTS.md` are not on
  it either.
- `src/advisor/evals/baseline.py:14-25` (as §28's plan cites) — `EVAL_PATHS`
  holds product files only; this change touches none, so no eval run is owed;
  the live-check paths in `CLAUDE.md` (cli, models, tracing, prompts, infra) are
  not touched either.
- `intents/28-reserve-intent-ids/plan.md:261-280` — the precedent for a
  Reviewed kit change to skills and policy files, with its text tests in
  `scripts/kit-texts.test.mjs`. This plan follows the same shape.

## Subtasks

Each ends with `npm run verify` green and its own commit. The order matters:
tests go with the code they pin, and a commit never leaves a kit test
pointing at a file that does not exist yet.

1. **Stats attribution (B13, AC5, AC6).** In `scripts/stats-lib.mjs`:
   extend `AGENT_PHASE` (`:16`) with `spec: 'spec'` and `plan: 'plan'`, the
   regex at `:166` to `(implement|rework|review|spec|plan)`, and the doc
   comment at `:164`. Tests first in `scripts/stats-lib.test.mjs`: the
   `agentTag` cases and the phase tests listed under Tests. Commit
   `§36: stats book spec and plan agents to their phase`.
2. **The four agent definitions and their pins (B1 to B9, AC1 to AC3).**
   Write, as one commit with the test that pins them:
   - `.claude/agents/product-advice-agent-spec.md` and
     `.claude/agents/product-advice-agent-plan.md`: frontmatter `name`,
     `description` (what it drafts, "never decides a design point, never
     commits, never records a gate"), `tools: Read, Write, Grep, Glob, Bash`,
     `model: sonnet`.
   - `.codex/agents/product-advice-agent-spec.toml` and
     `.codex/agents/product-advice-agent-plan.toml`: `name =
     "product_advice_agent_spec"` / `"product_advice_agent_plan"`,
     `description`, `sandbox_mode = "workspace-write"`,
     `developer_instructions = """ ... """`.
   - Body of each (the same sentences in all four, so the test can pin them;
     the Claude and Codex variants differ only in what the platforms differ
     in): "You draft ONE artefact for ONE intent named in the brief";
     "Read `CLAUDE.md`, then `.claude/skills/<spec|build-plan>/SKILL.md`,
     `intents/README.md` → "Drafting an artefact", the template, the intent
     (and, for the plan, `spec.md`)" and follow the skill for how to draft;
     the preconditions of the skill (B6, B7); the stamp line (exact string
     `product-advice-agent/spec@0.2.0` or `build-plan@0.2.0`) and the `main`
     hash; the rules, each as its own numbered sentence containing the pinned
     phrase from the table below; and the reply format (B9: the path or
     `INCOMPLETE:` and why; the questions with a recommended default; the
     weak points; at most 250 words unless the brief says otherwise).
   - The pinned phrases (the single source for the text and the test):
     `Write exactly one file`, `private folder with a unique name`,
     `Never commit`, `Never edit metadata.yml`, `Never record a gate`,
     `INCOMPLETE:`, `250 words`. The spec agent also contains `product-advice-agent/spec@0.2.0`;
     the plan agent `product-advice-agent/build-plan@0.2.0`.
   - In `scripts/kit-texts.test.mjs` add `SPEC_PLAN_AGENTS` (the four paths)
     beside `IMPLEMENTERS`/`REVIEWERS` (`:27-28`) and the new `describe` (see
     Tests). Commit `§36: spec and plan agents for Claude and Codex`.
3. **Skills, guides and the rule (B10 to B12, AC4).**
   - `.claude/skills/spec/SKILL.md`: after the stamp paragraph (`:18-19`) add a
     short section "Who drafts": the coordinator spawns
     `product-advice-agent-spec` with the `Agent` tool and a description
     beginning `§<id> spec`; the brief is the intent id, the `main` hash and
     what is already known; the hand-off rules are in that agent's
     definition; the coordinator may pass `model` for a spec with real
     trade-offs; after the agent returns, run `git status --short` and
     `git diff --stat`, confirm only `spec.md` changed and `metadata.yml` is
     untouched, else discard and report. Add to step 6 that an agent
     reports a prerequisite and the coordinator writes `blocked_by:`.
     Frontmatter version and stamp unchanged.
   - `.claude/skills/build-plan/SKILL.md`: the same, for
     `product-advice-agent-plan`, description `§<id> plan`, `plan.md`, and
     the `model` override "for a plan that must judge a self-contradicting
     intent"; step 3's stop is the agent's `INCOMPLETE:` reply.
   - `.claude/skills/auto/SKILL.md`: step 2 (`:115-117`, "draft it as `/spec` does") and step 3 item 1
     (`:136-139`): "spawn `product-advice-agent-spec` /
     `product-advice-agent-plan` as `/spec` / `/build-plan` say and run their
     `git status` check" instead of "draft it as `/spec` does"; an
     `INCOMPLETE:` reply from the plan agent is the existing stop
     `plan found the spec incomplete`; from the spec agent, `spec questions`.
   - `CLAUDE.md`: a bullet after `:62`'s sentence block: the coordinator
     drafts a spec or plan by spawning `product-advice-agent-spec` /
     `product-advice-agent-plan` (descriptions `§<id> spec` / `§<id> plan`),
     not by reading the codebase inline, and keeps every gate; the agents
     write one file, commit nothing. Mention both agents in the existing list
     of agents. `AGENTS.md`: the same rule after `:14` (Codex drafts with the
     `.codex/agents` twins).
   - Add the AC4 tests (below). Commit `§36: skills, CLAUDE.md and AGENTS.md
     name the spec and plan agents`.
4. **Hand-over.** Set `status: in-review` in `metadata.yml` (the only
   metadata edit, the implementer's one allowed), append a `## Progress`
   entry, and run the Validation commands.

## Tests

All kit tests are plain `node --test` files run by `npm run test:kit`
(inside `npm run verify`). Mutations are meant literally: the implementer
applies each once, sees the named test fail, and reverts it.

`scripts/stats-lib.test.mjs` (subtask 1):

- **AC5, `agentTag` positive.** `agentTag('§36 spec')` equals
  `{ id: 36, phase: 'spec' }`; `agentTag('  §36 plan the build')` equals
  `{ id: 36, phase: 'plan' }`. Mutation: drop `spec|plan` from the regex ->
  both fail.
- **AC5, `agentTag` negative.** `'§36 specify'`, `'§36 planning'`, `'36 spec'`,
  `'spec §36'`, `'§ 36 plan'` return `null` (added to the loose list at
  `:136`). Mutation: remove the `\b` -> the first two fail.
- **B13, phase mapping.** `i7(run({ agents: [agentRun('§7 spec', 7, 8),
  agentRun('§7 plan', 8, 9.5)] }))` has `ph(it, 'spec').agentWorkMs = 1 * H`,
  `ph(it, 'plan').agentWorkMs = 1.5 * H`, totals `2.5 * H`, and the agent
  tokens (`agentRun` gives each two assistant turns of 1,1,1,1) are in those
  phases, not in `unattributed`. Mutation: `AGENT_PHASE.spec = 'build'` (or
  missing) -> the phase assertion fails (the row would be `build` or the
  lookup `undefined`).
- **AC6, no spec phase in git.** With the existing synthetic life used at
  `:478` (no `§7: spec` commit), the same runs still produce a `spec` and a
  `plan` row (`ph(...)` is defined, tokens non-zero) and
  `it.phases.reduce(agentWorkMs)` equals `it.totals.agentWorkMs`: nothing is
  dropped. Mutation: have the loop `continue` when `getIntent(id).spans` has no
  phase of that name -> the test fails.
- **Untagged stays out.** An `agentRun('Explore', ...)` next to a
  `§7 spec` run is still in `unattributed` (the existing test at `:553` stays
  green; add the `spec` run to one assertion). Mutation: make the regex
  accept any word after `§7` -> that assertion fails.

`scripts/kit-texts.test.mjs`, new `describe('kit texts: spec and plan agents
(§36)')` (subtasks 2 and 3):

- **AC1, files exist and parse.** For each Claude file: the text starts with
  `---`, the frontmatter has `name: product-advice-agent-spec|plan` equal to
  the file's name, a `description:` line and a `tools:` line. For each Codex
  file: `name = "product_advice_agent_spec|plan"`, `description =`,
  `sandbox_mode = "workspace-write"`, `developer_instructions = """` and a
  closing `"""`. (A hand parse by regex, no TOML dependency.) Mutation: rename
  one `name:` -> that file's assertion fails.
- **AC2, shared rules in all four.** For every phrase of the pinned list
  (`Write exactly one file`, `private folder with a unique name`,
  `Never commit`, `Never edit metadata.yml`, `Never record a gate`,
  `INCOMPLETE:`, `250 words`) and each of the four files:
  `expect(read(f), `${f}: ${phrase}`).toContain(phrase)`. Mutation: delete
  one phrase from one file -> exactly that (file, phrase) fails.
- **AC2, stamp per agent.** The spec files contain
  `product-advice-agent/spec@0.2.0` and the plan files
  `product-advice-agent/build-plan@0.2.0`, and the spec files do not contain
  `build-plan@` as a stamp (and vice versa). Mutation: swap the stamp in one
  file -> fail. A second assertion ties the stamp to the skill: the string
  appears in `.claude/skills/spec/SKILL.md` / `build-plan/SKILL.md` too, so a
  skill version bump without the agents fails here.
- **AC3, tools and model.** For both Claude files: the `tools:` line does not
  match `/\bEdit\b/`, contains `Write` and `Bash`; the text contains `model:
  sonnet`. Mutation: add `Edit` to a tools line, or set `model: opus` -> fail.
- **B4, no git writes named as allowed.** The text of every agent contains
  `Never commit` (covered above) and none of the four contains
  `git commit` outside that sentence: assert the count of `git commit` is at
  most the one inside the prohibition. Mutation: a line telling the agent to
  commit -> fails. (Weak by design; the coordinator's check B10 is the real
  backstop.)
- **AC4, skills and guides name the agents.**
  `/spec` contains `product-advice-agent-spec`, `§<id> spec`,
  `git status --short`, `git diff --stat`; `/build-plan` contains
  `product-advice-agent-plan`, `§<id> plan`, the same two commands; `/auto`
  contains both agent names; `CLAUDE.md` and `AGENTS.md` contain both agent
  names. Mutation: delete the name from one file -> that file fails.
- **B11, pointer each way.** Each agent file contains
  `.claude/skills/spec/SKILL.md` (spec agent) or
  `.claude/skills/build-plan/SKILL.md` (plan agent), and each skill contains
  `.claude/agents/product-advice-agent-` ... the agent name (covered above).
  Mutation: remove the pointer from an agent -> fails.
- **B12 text.** `CLAUDE.md` contains `not by reading the codebase inline`
  (the exact wording the implementer writes in subtask 3) next to the agent
  names. Mutation: remove it -> fails.
- **B8 override.** `/spec` and `/build-plan` each contain `model` in the
  "Who drafts" section: assert `toContain('pass a `model`')`. Mutation:
  delete -> fails.
- **AC7, no product code.** Not a unit test: `git diff --name-only main...`
  has no path under `src/advisor/`; run in Validation. Mutation: not
  applicable (a check, named as such).
- **AC8.** Manual, in Validation (the owner).

The existing "old rebase wordings are gone" test (`:74-98`) runs over the new
files by `walk`; it must stay green (a mutation: add "rebase before review"
to an agent text -> it fails; not repeated).

## Validation

- `npm run verify` green after each subtask (kit tests, ruff, mypy, pytest).
- `npm run check:intent` PASS. Size budget: about 10 files and a few hundred
  lines; if `check:intent` flags the size, the review records ROUTE with the
  reason (the intent's own Assumptions say more than 5 files).
- `git diff --name-only main...` lists no path under `src/advisor/` (AC7).
- `uv run advisor-analysis owes-run --base main` says none is owed (no
  product file in `EVAL_PATHS` changes). No eval run is owed.
- **Live check: none by path.** The paths `src/advisor/cli.py`,
  `models/`, `tracing.py`, `prompts/` and `infra/` are untouched
  (`REVIEW-POLICY.md` "Live checks", rule 1), so none is owed. Instead of a
  live check the owner does AC8 and the diff read below.
- **Owner steps after merge (AC8, not a gate):**
  1. Restart the Claude Code session (or open a new one): a new
     `.claude/agents/*.md` may not appear as a `subagent_type` until then;
     confirm `product-advice-agent-spec` and `product-advice-agent-plan` are
     listed in the `Agent` tool.
  2. Run a real `/spec <id>` or `/build-plan <id>`: the coordinator spawns the
     agent with a `§<id> spec|plan` description, and the coordinator's
     `git status --short` shows only the one file, `metadata.yml` untouched.
  3. Run `npm run stats -- <id>` and see the agent's tokens in the `spec` or
     `plan` row, not "unattributed".
  4. In a Codex session, spawn `product_advice_agent_spec` once to confirm
     `sandbox_mode = "workspace-write"` is accepted in an agent file; if not,
     use the fallback under Verified.
- **What the owner should look at in the diff (Reviewed tier,
  `REVIEW-POLICY.md:30`).** The four agent texts: that the rules read right
  and that `tools:` has no `Edit`; the skills' new "Who drafts" sections and
  `/auto` steps 2 and 3 (that nothing there lets an agent record a gate or
  write `metadata.yml`, and that the coordinator's `git status` check is
  mandatory); the new `CLAUDE.md` and `AGENTS.md` lines. The kit code change
  (`stats-lib.mjs`) is two lines and its tests.

## Assumptions I made

- **No skill version bump.** The spec fixes the stamps as `spec@0.2.0` and
  `build-plan@0.2.0` (B6), the scan reads any version
  (`scripts/scan-lib.test.mjs:45-46`), and no test pins a skill's version
  except §28's `intent@0.3.0` (`scripts/kit-texts.test.mjs:68-72`). The
  skills do gain text; if the owner wants `0.3.0`, the stamp lines in the
  skills and in both agents' texts change with it (the stamp test ties them).
- **`/auto` reuses the existing stop names** (`spec questions`,
  `plan found the spec incomplete`) for an `INCOMPLETE:` reply; no new stop
  reason, so the resume table at `auto/SKILL.md:89-105` is unchanged.
- **Pinned phrases are mine.** The spec says what the rules are, not their
  wording; the wording in subtask 2 is the plan's, and the test pins that
  wording. The spec's AC2 asks for these rules in all four files, which the
  test does.
- **The spawn skill is not edited.** It only launches the implementer; the
  drafting hand-off lives in `/spec`, `/build-plan` and `/auto` (B11).
- **`sdlc.md` is not edited** (not in B11 or B12); it keeps saying "Run
  `/spec <id>`", which still holds.
- **The memory note** is outside the repository and untouched (B12); the
  coordinator turns it into a pointer after the merge.
- **Codex `workspace-write` is confirmed as a CLI value only** (see Verified);
  the agent-file key is confirmed by the owner's step 4, with a stated
  fallback.
- The implementer (Sonnet, cannot spawn agents) can do all of this from the
  files above; nothing needs a second agent.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-25 — implementation (subtasks 1 to 4)

- Commits: `c7330b7` (stats regex and AGENT_PHASE with tests; it also swept
  in the four agent files, because a background `verify && git add -A`
  ran while they were being written), then the commit with the kit-texts
  pins, the skills, `CLAUDE.md` and `AGENTS.md`, then the hand-over.
- Shipped: `agentTag` and `AGENT_PHASE` accept `spec` and `plan`; the four
  agent files; "Who drafts" in `/spec` and `/build-plan`; `/auto` steps 2
  and 3; the rule in `CLAUDE.md` and `AGENTS.md`.
- Tests: kit tests now 64 in stats-lib (2 new, the agentTag cases extended) and 19 in kit-texts (8 new
  in the §36 describe); `npm run verify` green (994 pytest). Mutations
  tried: rename an agent `name:`, drop `Never commit` from one Codex file,
  change the `CLAUDE.md` wording: each failed the named test, then restored
  by copy.
- Divergences: (1) the Codex TOMLs omit `sandbox_mode`, as the implementer
  toml does (the brief chose the plan's fallback), so the kit-texts test
  does not assert it; the owner's step 4 should confirm the default sandbox
  lets the Codex agent write its file. (2) The three "Never ..." phrases
  appear once per file (as the bold rule heading) so a deletion is caught.
  (3) The `/auto` AC text mutation list (delete a name from `/auto`) was not
  run by hand; the test loops over it.

### 2026-11-25 — rework, review round 1

- Commit: see `git log` (one rework commit after `4d7b716`).
- Owner decisions applied: finding 2 (a), both Codex TOMLs now carry
  `sandbox_mode = "workspace-write"` (reviewer's form), asserted in kit-texts;
  finding 7, the before-snapshot (`git status --short` before spawning, compare
  after) in `/spec`, `/build-plan` and `/auto`, pinned by the word `snapshot`.
- Mechanical: (1) the AC3 regex now holds `\bEdit\b` with a real backslash (the
  two 0x08 bytes came from an escaping layer in my shell tool; I wrote the
  fix with `bytes([92])`); byte scan of every changed file: no control byte.
  (3) `/auto` pins `§<id> spec`, `§<id> plan`, both git commands, `INCOMPLETE:`,
  the snapshot and the two single-line step 2 and 3 phrases (the bare names also
  occur in section 10 and elsewhere, so only line-specific phrases kill).
  (4) PHRASES gained `Never decide a design point`, `options and a recommendation`
  and the `blocked_by` sentence. (5) both stats tests assert the agents' tokens
  per phase and that only the Explore run is unattributed. (6) `intents/README.md`
  `blocked_by` bullet and a role bullet (not in the plan's file list: a
  divergence, owner-approved in review finding 6). (8) `/auto` section 10 prefix
  list. (9) `not by reading` (AGENTS.md), `keeps every gate` (both guides),
  `Confirm that only` (both skills). (10) `[ \t]*` as escapes. (11) and (12) done.
- Tests: kit suite 500 of 500 (kit-texts 19, stats-lib 64; assertions added, no
  new test names); `npm run verify` green.
- Mutants hand-run, each restored by copy: Edit added to the tools line in the
  spec and the plan Claude file (both killed now); sandbox read-only and sandbox
  line deleted; snapshot deleted in `/spec` and `/auto`; `Confirm that only`
  changed; `§<id> spec`, `§<id> plan`, `(or replies INCOMPLETE:)` and `If the
  agent replies INCOMPLETE:` in `/auto`; the git diff comparison deleted in
  `/auto`; the `blocked_by` sentence, `options and a recommendation` and
  `Never decide a design point` in agents; `not by reading` and `keeps every
  gate` in the guides; spec and plan tokens routed to unattributed in
  `stats-lib.mjs`: all killed. The first two `/auto` mutants survived with the
  bare pins and were killed after the line-specific pins were added.
- Note for the owner (AC8 step 4): once, spawn `product_advice_agent_spec` in
  Codex and confirm that `sandbox_mode = "workspace-write"` is accepted in an
  agent file and lets the agent write its one file; if rejected, use the
  plan's fallback (omit the line and drop the assertion).

### 2026-11-25 — rework, review round 2

- Commit: see `git log` (one commit after `8a472c6`).
- Findings 1 to 4 done, text only (no behaviour change in the agent files):
  skills pin `Before spawning, run`, the diff-and-compare sentence and
  `discard it and report`; `/auto` counts `snapshot before`, `comparison after`
  and `git diff --stat` comparison after (2 each), and pins the section 10 prefix
  list; the forbidden-git phrase joins `PHRASES` (all four agent files);
  `intents/README.md` pins both phrases; the backstop-not-a-fence sentence is in
  `/spec` and `/build-plan`; `CLAUDE.md` and `AGENTS.md` say the coordinator
  compares `git status --short` before and after (and `git diff --stat`). The AC3
  regex is now `/\bEdit\b|MultiEdit|NotebookEdit/` (finding 5, optional).
- Tests: `kit-texts` and `stats-lib` together 83 of 83 (19 and 64; assertions
  added, no new test names). Control-byte scan of every changed file: clean.
- Mutants hand-run, restored by copy: all killed: snapshot clause, compare
  sentence, discard sentence in both skills; the `/auto` step 2 and 3 snapshot and
  comparison clauses; the section 10 list (drop `plan`, drop `spec` and `plan`);
  the git list in each of the four agent files; both README phrases;
  `MultiEdit` in a tools line. Two rounds of survivors: the "`git diff --stat` and"
  clause in both skills and the `/auto` diff comparisons survived the first pins
  (the neighbouring words stayed) and were killed after pinning the whole clause.
