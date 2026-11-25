<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §36 — Dedicated spec and plan agents

**Type:** feature
**Originator:** the owner ("when you do a spec or a plan, you spawn a general
purpose agent. Should we create a dedicated spec and plan agent that would run
on Sonnet", 2026-11-25; "draft the intent for the spec and plan agents")
**Source:** the §30–§35 session of 2026-11-25, where the coordinator spawned
eight general-purpose agents to draft specs and plans, and
`.claude/agents/product-advice-agent-implementer.md` (already `model: sonnet`)

## Problem

The coordinator drafts a spec or a plan by spawning a general-purpose agent
(the owner asked for that on 2026-11-24, so the coordinator's context is not
filled with a whole codebase read). It has no definition of its own, so:

- **The brief is retyped each time.** Every brief repeats the same rules:
  follow `.claude/skills/spec` or `build-plan`, never decide a design point
  (reply `INCOMPLETE:` instead), never commit, never touch `metadata.yml` or
  record a gate, write only the one file, reply in under N words. A line left
  out is a rule not applied, and nothing checks it.
- **The model and tools are not chosen.** A general-purpose agent has every
  tool, including Edit on code and `metadata.yml`, and runs on the session's
  model. Drafting is reading code and filling a template, which the
  implementer already does on Sonnet.
- **It is invisible to the kit.** `npm run stats` attributes agent tokens and
  time only to a description starting `§<id> implement|rework|review`
  (`scripts/stats-lib.mjs`, `AGENT_PHASE`), so spec and plan drafting count
  as unattributed. The skills (`/spec`, `/build-plan`, `/auto`) and
  `CLAUDE.md` say nothing about who drafts; the owner's instruction lives
  only in a memory note.

## Outcome

- Two agent definitions exist for Claude (`.claude/agents/`) and Codex
  (`.codex/agents/`), beside the implementer and the reviewer: one that
  drafts `spec.md` for one intent, one that drafts `plan.md`. Each runs on
  Sonnet, follows its skill, and carries the rules above in its own
  definition instead of in every brief.
- A spec or plan agent cannot change code or a gate: its tools and its
  instructions allow it to write its one file and nothing else (how that is
  enforced is a question for the spec).
- `/spec`, `/build-plan` and `/auto` name the agent to spawn, and the
  coordinator's brief shrinks to the intent id, the hash of `main` and what
  is already known.
- `npm run stats` attributes a spec or plan agent to the intent's `spec` or
  `plan` phase (descriptions `§<id> spec`, `§<id> plan`).
- A spec or plan drafted by the new agent is checked by the coordinator as
  today; the agent never records a gate.

## Constraints

- `.claude/agents/**`, `.codex/agents/**` and `.claude/skills/**` are
  Reviewed tier (`REVIEW-POLICY.md`, the path table), so the owner reads the
  diff. `scripts/stats-lib.mjs` is kit code with its own tests.
- No change to the product (`src/advisor/`), so no eval run is owed and no
  live check is owed by path.
- No new dependency. A subagent cannot spawn another; the coordinator stays
  the only one that spawns.
- Out of scope: the intent drafting (`/intent`), which the coordinator does
  itself or delegates as it does today.

## Type-specific questions

### Feature
- **Users:** the owner and the coordinator session (`/spec`, `/build-plan`,
  `/auto`).
- **What exists today:** general-purpose agents with a hand-written brief; a
  memory note (`delegate-spec-plan-drafting`) as the only record of the rule.
- **Open design questions for the spec:**
  1. **One agent or two.** A spec and a plan differ in what they read and
     what they stop for (a plan stops when the spec is incomplete; a spec
     asks the owner one round of questions). Two agents with a shared core,
     or one agent that takes the skill as its input?
  2. **How "one file only" is enforced.** The Claude tool list gives `Write`
     for any path. Options: instructions only (as the implementer's "never
     push"), a hook that refuses another path, or no `Write` at all and the
     agent returns the draft for the coordinator to save. Which does the
     kit trust, and what does Codex's `sandbox_mode` allow?
  3. **Sonnet for both?** A plan that must find a self-contradicting intent
     (§32's round 1) or a spec that must judge design trade-offs may need
     more than the implementer's model. Sonnet by default, with the
     coordinator free to pass a model per spawn?
  4. **Where the rules live.** In the agent definition, in the skills'
     `SKILL.md`, or both. Today `/spec` and `/build-plan` say how to
     draft; the new part is the hand-off rules (`INCOMPLETE:`, no gate, one
     file, the reply format).
  5. **Stats.** `AGENT_PHASE` gains `spec` and `plan`; do those map to the
     existing `spec` and `plan` phases of the stats table?
  6. **The memory note** becomes a repository rule (in `CLAUDE.md` or the
     skills) and the note is deleted, or it stays as a pointer.

## Assumptions I made

- It is a feature, not an adjustment: it touches more than 5 files (two
  Claude agents, two Codex agents, three skills, `CLAUDE.md`/`AGENTS.md`,
  `stats-lib.mjs` and its tests) and has open design questions.
- The owner's "a dedicated spec and plan agent" means one definition per
  artefact, and Sonnet is the default, as for the implementer.
- A plan agent that finds the intent incomplete replies `INCOMPLETE:` with
  options and a recommendation, as the §32 and §35 drafts did; that is kept.
- No `blocked_by`: nothing here waits on §30–§35. `links` names §19, whose
  stats read the agent description prefix this intent extends.
