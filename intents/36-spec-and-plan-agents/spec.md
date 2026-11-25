<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §36 spec — Dedicated spec and plan agents on Sonnet

Accepted intent: [intent.md](intent.md)

Written against `main` at `ed95277`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `intents/36-spec-and-plan-agents/intent.md` | Outcome: two definitions for Claude and Codex, Sonnet, one file only, skills name the agent, stats attribute `§<id> spec` / `§<id> plan`; the six open design questions |
| `.claude/agents/product-advice-agent-implementer.md` | Precedent: frontmatter `tools: Read, Write, Edit, Bash, Grep, Glob`, `model: sonnet`; "never push", "never record a gate" are instructions only |
| `.claude/agents/product-advice-agent-reviewer.md` | Precedent: `tools: Read, Grep, Glob, Bash`, `model: opus`, "Cannot modify files" |
| `.codex/agents/*.toml` | Codex format: `name`, `description`, optional `sandbox_mode` (the reviewer has `sandbox_mode = "read-only"`; the implementer sets none) and `developer_instructions`. No per-path write restriction exists in either file |
| `intents/README.md` → "Drafting an artefact", "Who edits what" | The eight shared drafting rules; "A subagent ... any `Agent`-tool worker never records a gate" |
| `.claude/skills/spec/SKILL.md`, `.claude/skills/build-plan/SKILL.md` | How to draft (preconditions, read first, template, validate, report); the stamp lines `spec@0.2.0` and `build-plan@0.2.0` |
| `.claude/skills/auto/SKILL.md` step 2/3, `.claude/skills/spawn/SKILL.md` | `/auto` drafts the spec and plan itself today; `/spawn` launches the implementer with a description beginning `§<id> implement` |
| `scripts/stats-lib.mjs` | `AGENT_PHASE = { implement: 'build', rework: 'review', review: 'review' }` and `agentTag`, whose regex is `^§(\d+)\s+(implement\|rework\|review)\b`; `PHASE_ORDER` already has `spec` and `plan` |
| `REVIEW-POLICY.md` path table | `.claude/agents/**`, `.codex/agents/**`, `.claude/skills/**` are Reviewed tier |
| Memory note `delegate-spec-plan-drafting` (outside the repo) | The owner's 2026-11-24 instruction: spec and plan drafting goes to a spawned agent; gates stay with the coordinator |

Checked now, not assumed: the `Agent` tool in this harness lists
`product-advice-agent-implementer` and `product-advice-agent-reviewer` as
`subagent_type` values, both defined only by a file in `.claude/agents/`, so
a new `.claude/agents/<name>.md` file is addressable the same way (a
new file may need a session restart to be listed; the plan must say so).
`.claude/settings.json` holds only the five session-event hooks; there is no
`PreToolUse` hook, and the agents' `tools:` lines name tools, not paths.

## Behaviour

**B1. Two agents, one per artefact.** The kit has a spec agent
(`product-advice-agent-spec`) and a plan agent (`product-advice-agent-plan`),
each as `.claude/agents/<name>.md` and `.codex/agents/<name with underscores>.toml`
(four new files). They differ in what they read and stop for (B6, B7), so each
has its own definition. The rules they share (B2 to B5, B9) are written out in
full in each definition: an agent file cannot include another.

**B2. One file only.** The spec agent writes
`intents/<id>-<slug>/spec.md` and the plan agent `.../plan.md`, and no other
file. The definitions say so as an instruction. Claude tools are
`Read, Write, Grep, Glob, Bash` (no `Edit`; `Bash` is for read-only `git` and
`npm run queue` style reads). The Codex twins set `sandbox_mode =
"workspace-write"`, the narrowest mode that lets them write the file; neither
platform restricts the path, and the kit does not pretend otherwise. The
backstop is the coordinator's check (B10).

**B3. Scratch folder.** If an agent needs scratch space it uses a private
folder with a unique name (for example `<scratchpad>/spec-<id>-<random>`) and
never a shared name such as `copy`, because agents sharing the scratchpad
overwrote each other's `copy` folder on 2026-11-25. It writes nothing outside
its one file and that folder.

**B4. No commit, no gate, no branch.** The agent never runs `git commit`,
`git add`, `git checkout`, `git switch`, `git merge`, `git push` or any
branch or worktree change, never edits `metadata.yml` (a prerequisite it finds is reported, not
written), and never records a gate. The agent works in the checkout it is
given and leaves the file uncommitted for the coordinator.

**B5. Never decide a design point.** When the intent, the spec (for a plan)
and the sources leave a design point open that the template needs, the agent
does not decide it. It replies `INCOMPLETE:` followed by the open points,
each with the options and a recommendation, and writes no file (or leaves the
existing file untouched). This keeps the `/spec` rule of one batched round of
questions: the spec agent may instead write the draft with the recommended
defaults under Behaviour and Assumptions and list the questions in its reply,
which is what `/spec` step 3 asks; `INCOMPLETE:` is for a point it cannot
default.

**B6. The spec agent follows `/spec`.** It reads
`.claude/skills/spec/SKILL.md`, `intents/README.md` → "Drafting an artefact",
the template and the intent, applies the `/spec` preconditions (type
`feature`, `intent_accepted` recorded; else it replies `INCOMPLETE:` naming
which), uses the stamp `product-advice-agent/spec@0.2.0`, and records the
`main` hash. A hard prerequisite it finds is named in its reply (it does not
edit `blocked_by:`); the coordinator records it.

**B7. The plan agent follows `/build-plan`.** It reads
`.claude/skills/build-plan/SKILL.md`, the same README section, the plan
template, the intent and (for a feature) the accepted spec. If the spec or
intent is incomplete or contradicts itself it replies `INCOMPLETE:` with
options and a recommendation instead of writing a plan (§32's and §35's
drafts did this; it is kept).

**B8. Model.** Both Claude definitions carry `model: sonnet`. The
coordinator may pass a `model` on a spawn to override it (for a plan that
must judge a self-contradicting intent, or a spec with real trade-offs); the
skills say when. The Codex twins carry no model line, as the existing ones
do not.

**B9. The reply.** The agent's reply is short: the file path (or
`INCOMPLETE:` and why), the questions with a recommended default for each,
and the weak points. The brief names a word limit; the default in the
definition is 250 words.

**B10. The coordinator checks every draft.** `/spec`, `/build-plan` and
`/auto` tell the coordinator to take `git status --short` before spawning
the agent (a snapshot) and, after it returns, to run `git status --short`
and `git diff --stat` and compare with the snapshot: only the one file may
be new or changed and `metadata.yml` must be untouched; then read the draft
as today. A draft that changed anything else is discarded and reported.
(Amended 2026-11-25, owner: "36 a, snapshot", after round 1: a new file is
untracked so `git diff --stat` does not show it, and the main checkout
already has unrelated untracked files, so the check needs the snapshot.
Writes to gitignored paths remain invisible to it.)

**B11. The skills name the agent.** `/spec` and `/build-plan` say: spawn
`product-advice-agent-spec` / `product-advice-agent-plan` with the `Agent`
tool and a description beginning `§<id> spec` / `§<id> plan`; the brief is
the intent id, the `main` hash and what is already known (the owner's
answers, prior decisions). `/auto` steps 2 and 3 do the same instead of
drafting inline. The content rules stay in the skills (how to draft); the
hand-off rules live in the agent definitions (B2 to B5, B9). Neither copy
restates the other beyond a pointer.

**B12. A repository rule.** `CLAUDE.md` ("How work flows") and `AGENTS.md`
state that the coordinator drafts a spec or plan by spawning these agents
and not by reading the codebase inline, and that the coordinator keeps the
gates. This replaces the memory note's role as the only record. The note is
outside the repo: this intent does not edit it; the coordinator updates it to
a one-line pointer to `CLAUDE.md` after the merge.

**B13. Stats attribution.** `agentTag` accepts descriptions beginning
`§<id> spec` and `§<id> plan` (alongside `implement|rework|review`), and
`AGENT_PHASE` maps `spec` to the `spec` phase and `plan` to the `plan`
phase. Tokens and agent work time of such an agent then count in that
intent's `spec` and `plan` rows instead of "unattributed". A description
that matches none stays unattributed.

## Interpretations

- **"One file only" is a promise the platform cannot enforce.** The intent
  asks how it is enforced. Reading: instructions plus a sandbox mode on
  Codex plus the coordinator's check (B10); a path-restricting hook is not
  built (see Out of scope). To become a code comment: none (the text lives in
  the definitions).
- **"The agent never decides a design point" versus `/spec` step 3
  ("Otherwise decide, and list the decision under Assumptions").** Reading:
  the skill's rule is about points the sources settle or the intent leaves
  to the drafter; the agent decides those and lists them. A point that
  changes behaviour the owner would care about (an open design question the
  sources leave open) goes to the owner as a question with a default (B5).
- **"Uncommitted file".** The intent says the agent writes its one file and
  nothing else; committing the spec or plan is the coordinator's step (the
  commit subjects `§<id>: spec drafted` are made by it).
- **Codex `sandbox_mode` values.** Only `"read-only"` appears in the
  repository. `workspace-write` is Codex's documented next value; the plan
  must confirm it against the Codex documentation before the file is
  written, since this spec could not.

## Acceptance criteria

- **AC1.** The four files exist, are valid (YAML frontmatter with `name`,
  `description`, `tools`, `model: sonnet`; TOML with `name`, `description`,
  `sandbox_mode`, `developer_instructions`) and the Claude files are
  listable as `subagent_type` (test: a kit test parses the frontmatter/TOML;
  manual: the coordinator sees both names in the `Agent` tool listing).
- **AC2.** Each of the four definitions contains the shared rules: the
  one-file rule, the private-scratch-folder rule, "never commit", "never
  touch `metadata.yml` or record a gate", `INCOMPLETE:`, and the reply
  format (test: `scripts/kit-texts.test.mjs`, a `SPEC_PLAN_AGENTS` list
  beside `IMPLEMENTERS`/`REVIEWERS`).
- **AC3.** The Claude definitions' `tools:` line has no `Edit`, and both
  have `model: sonnet` (test: kit-texts).
- **AC4.** `/spec`, `/build-plan` and `/auto` name `product-advice-agent-spec`
  / `product-advice-agent-plan`, the `§<id> spec|plan` description and the
  B10 check; `CLAUDE.md` and `AGENTS.md` carry the B12 rule (test:
  kit-texts, `toContain` on the agent names and the description prefix).
- **AC5.** `agentTag('§36 spec')` and `agentTag('§36 plan')` return
  `{id: 36, phase: 'spec'|'plan'}`; `agentTag('§36 specify')` and
  `agentTag('36 spec')` stay `null`; usage of such an agent is booked in the
  intent's `spec` / `plan` phase (test: `scripts/stats-lib.test.mjs`).
- **AC6.** Agent time booked to `spec` or `plan` is not lost when a
  phase of that name does not exist in the intent's git phases (an intent
  without a spec commit): the test uses a synthetic intent and expects the
  tokens present in a row, not dropped (test: `stats-lib.test.mjs`).
- **AC7.** `npm run verify` and `npm run check:intent` pass; no file under
  `src/advisor/` changed (check: `git diff main...` lists none).
- **AC8.** Manual, owner: a real `/spec` or `/build-plan` run spawns the new
  agent, which writes only its file and leaves `metadata.yml` untouched
  (the coordinator's B10 check shows it). Not a policy live check.

## Non-functional

- **Boundaries:** no product code. Kit code is `scripts/stats-lib.mjs`
  (pure); agent files and skills are Reviewed tier, so the owner reads the
  diff (`REVIEW-POLICY.md`).
- **Data:** none personal. The agents read the repository only.
- **Model use:** Sonnet by default, overridable per spawn (B8). No product
  prompt changes, so no eval run is owed (`npm run … owes-run` on the diff
  should say none).
- **Autonomy:** the agents draft only. They record no gate, commit nothing,
  spawn nothing (a subagent cannot).

## Out of scope

- A hook that refuses a write to any other path (settings change in every
  session; Reviewed tier; unverified that agent-level hooks exist here).
- Dedicated agents for `/intent`, `/review` (the reviewer exists) or `/konmari`.
- Changing what `/spec` and `/build-plan` ask or produce.
- Editing the memory note (B12: the coordinator does it).
- Any change to `src/advisor/`.

## Assumptions I made

The six design questions, answered with the defaults below. The owner is
asked once, in the reply, and may overturn any of them.

1. **Two agents, not one** (B1), with the shared rules duplicated and pinned
   by a test (AC2) so they cannot drift apart. Reason: different reads and
   different stops; one agent taking "the skill as input" is a brief again.
2. **Enforcement: instructions, no `Edit`, Codex `workspace-write`, and the
   coordinator's `git status` check** (B2, B10). Reason: it is what the
   implementer's "never push" already relies on; a hook is a Reviewed-tier
   settings change affecting every session, and "no Write, the agent returns
   the draft" puts the whole spec back in the coordinator's context, which is
   what the owner wanted to avoid.
3. **Sonnet for both, per-spawn `model` override allowed** (B8).
4. **Rules in both places** (B11): the hand-off rules in the agent
   definitions, the drafting rules in the skills, a pointer each way.
5. **Stats: `spec` → `spec`, `plan` → `plan`** (B13).
6. **The memory note stays as a pointer** after `CLAUDE.md` carries the rule
   (B12), rather than being deleted; the coordinator edits it.
7. A prerequisite found while drafting is reported, not written to
   `blocked_by:` by the agent (B4/B6): `metadata.yml` stays untouched by
   subagents, which is stricter than `/spec` step 6 and keeps B4 one rule.
8. The agent files are named `product-advice-agent-spec` and
   `product-advice-agent-plan` after the existing `-implementer` and
   `-reviewer`.
9. `Bash` stays in the tool list because the agents need `git rev-parse`,
   `git log` and `npm run queue`; it can write files, which is why B2 rests
   on instructions and B10 on the check.
