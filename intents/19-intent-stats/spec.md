<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §19 spec — Time, tokens and owner wait per intent and phase

Accepted intent: [intent.md](intent.md)

Written against `main` at `157bd42`.

## Owner's decisions (question round, 2026-11-13)

- **Hook logging:** "Yes, skill + id only": the prompt hook may log the
  skill name and intent id of a prompt that starts with a slash command;
  still no other prompt text.
- **Owner wait:** "Both, gaps capped": gate wait and in-session wait,
  reported separately; a single gap counts at most 2 h, the rest is
  "idle".
- **Storage:** "stats.md written at /ship", plus `npm run stats` for any
  intent live; the grid reads the `stats.md` files.
- **Backfill:** "Best effort, marked partial" for §1–§18; no `stats.md`
  for them.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `scripts/session-event.mjs` | The hook: "prints nothing …, swallows every error, and always exits 0. What gets recorded … is decided by eventRecordFrom in session-lib.mjs." |
| `scripts/session-lib.mjs:142-151` | "Prompts are logged by length": `fields.promptChars = … input.prompt.length`. B1 adds two fields. |
| `.git/product-advice-agent-sessions.jsonl` | One JSON line per event: `ts`, `worktree`, `branch`, `id` (null for the coordinator), `event` (`UserPromptSubmit`, `Stop`, `Notification`, …), `session`, `kind`, `detail`. |
| Claude Code transcripts | `~/.claude/projects/<slug>/<session>.jsonl`, and `<session>/subagents/agent-*.jsonl` with `agent-*.meta.json` (its `description`). Assistant lines carry `message.usage` and `message.model`. The format is not ours: unstable. |
| `CLAUDE.md` → Parallel sessions | "That file is never committed … It holds **no prompt text**: a prompt is logged by its length only." B1 changes this sentence. |
| `scripts/ship.mjs`, `scripts/ship-lib.mjs` | The bookkeeping commit "holds `metadata.yml` only" (`/ship` skill); B9 adds `stats.md` to it. |
| `.claude/skills/grid/SKILL.md`, `docs/sdlc-grid.md` | "Report progress and outcome together"; B11. |
| Commit subjects | Phase milestones: `§N: intent drafted`, `intent accepted`, `spec drafted`, `spec accepted`, `plan drafted`, `plan approved`, `auto round N`, `review round N`, `auto stopped: …`, `auto run resumed`, `merged (…)`. |

## Behaviour

**Attribution inputs**

- **B1.** The `UserPromptSubmit` hook adds `skill` and `skillId` when the
  prompt, trimmed, starts with `/<name>` for a `<name>` in the repo's own
  skills (`.claude/skills/*/`), with `skillId` the first integer argument
  if any (`/spec 17` → `skill: "spec", skillId: 17`). Anything else in the
  prompt is not logged; a prompt not starting that way gets neither field.
  The hook still never prints and never fails. `CLAUDE.md`'s sentence and
  the hook tests say exactly this.
- **B2.** Every agent the coordinator launches for an intent gets a
  description beginning `§<id> <phase>` with phase one of `implement`,
  `rework`, `review` (e.g. `§13 review round 2`). `/spawn`, `/auto` and
  `/review` say so. An agent whose description has no `§<id>` is
  unattributed.

**Phases**

- **B3.** An intent's phases are the spans between its milestone commits
  (on `main` and its branch, by committer time): **intent** (drafted →
  accepted), **spec** (→ spec accepted), **plan** (→ plan approved),
  **build** (→ first `auto round` or `in-review`), **review** (→ the last
  `review round` before the ship, rework included), **live check**
  (→ `live check recorded`), **ship** (→ `merged`). A missing milestone
  merges its span into the next; a type without a spec or plan has no such
  phase.

**What is counted**

- **B4.** **Tokens:** every assistant line with usage in the coordinator's
  and agents' transcripts, per model: input, output, cache read, cache
  write. An agent's tokens go to its `§<id>` and phase (B2). A coordinator
  turn (from a `UserPromptSubmit` to its `Stop`) goes to the `skillId` of
  its prompt (B1); else to the one intent whose `§N:` commits fall inside
  the turn; with several, to a "shared: §a, §b" line; with none,
  unattributed. Nothing is counted twice.
- **B5.** **Elapsed:** wall-clock per phase from B3. Overlapping intents
  each count their own wall-clock (time is not shared out).
- **B6.** **Owner wait**, two kinds, each gap capped at 2 h with the excess
  reported as **idle**:
  - **gate wait:** from an `auto stopped:` or `… drafted` commit of the
    intent to the next commit that records the owner's answer (a gate, an
    `auto run resumed`, `auto run started`);
  - **in-session wait:** in a session attributed to the intent, from a
    `Stop` or a permission `Notification` to the next `UserPromptSubmit`.
- **B7.** Lines the parser cannot read are skipped and counted, per file,
  and shown; never a failure, never an invented number.

**Outputs**

- **B8.** `npm run stats -- <id>` prints, per phase: elapsed, gate wait,
  in-session wait, idle, and tokens per model split coordinator / agents;
  then totals; then unattributed and shared lines and the skipped-line
  count. `--json` gives the same data. `npm run stats -- --all` prints one
  line per intent, marking every figure for an intent merged before this
  change as `partial`.
- **B9.** `/ship` writes `intents/<id>/stats.md` (the B8 table, generated,
  stamped) into its bookkeeping commit. If collecting fails, ship writes
  nothing, says why in its report, and goes on: stats never block a ship.
- **B10.** Only derived totals are committed. Transcripts and the session
  log are read in place; no prompt or response text appears in any output.
- **B11.** `/grid` reads the committed `stats.md` files for its Measures
  (median elapsed, owner wait and tokens per shipped intent).

## Interpretations

- **"Never guessed"** (intent Outcome): a coordinator turn touching several
  intents is reported as shared, not split by a ratio.
- **"Waiting for me"** excludes agent run time: an agent running while I am
  away is not owner wait.
- **Transcript location:** the project directories whose slug is the main
  checkout's or one of its worktrees' paths (from the session log's
  `worktree` values), transformed as Claude Code names them.

## Acceptance criteria

- **AC1** (B1): hook tests: `/spec 17` → skill and id; `/auto 13` →
  `auto`, 13; `/review` → skill only; `/unknown 3`, `yes to 16`,
  `accept 15 and /auto 15` → neither; never any other text; output empty,
  exit 0 on bad input. (kit tests)
- **AC2** (B3, B5): milestone fixtures (a synthetic git log) → phase spans,
  missing milestones merged, a fix without spec/plan. (kit tests)
- **AC3** (B4, B7): synthetic transcripts → per-model token sums; agent
  attribution by tag; coordinator turn by skillId, by single-intent
  commits, shared, unattributed; unreadable lines counted. (kit tests)
- **AC4** (B6): gate and in-session waits, the 2 h cap and idle, agent
  time excluded. (kit tests)
- **AC5** (B8–B10): `stats` text and JSON on fixtures; `--all` with
  `partial`; ship writes `stats.md` in the bookkeeping commit on a temp
  repo and still ships when collection throws; no prompt text in any
  output (a fixture prompt string never appears). (kit tests)
- **AC6** (B2, B11): the skills say B2's description format and B11's
  reading. (review)
- **AC7** (live check, owed: real transcripts and the hook): the owner runs
  `npm run stats -- 13` (or the latest shipped intent) and `-- --all`, and
  checks the figures against their memory of the run; a prompt typed after
  the change logs `skill`/`skillId` and nothing else in the session log.

## Non-functional

- **Boundaries:** kit only: a pure `scripts/stats-lib.mjs`, I/O in
  `scripts/stats.mjs`, `session-lib.mjs` (B1), `ship.mjs`/`ship-lib.mjs`
  (B9), skills, `CLAUDE.md`, `package.json` (`stats` script). No
  `src/advisor/` change. Node ≥ 22, no dependency.
- **Data:** transcripts and the log stay local; committed `stats.md` holds
  numbers and ids only.
- **Model use:** none.
- **Autonomy:** read-only except `/ship`'s `stats.md`.
- **Tier:** Reviewed (`scripts/session-event.mjs`'s logic, the skills,
  ship). Live check owed (rule 3, and the hook runs in every session).

## Out of scope

- Dollar pricing; Codex sessions; other repositories; dashboards beyond
  the terminal; changing what other hooks log; rewriting past session-log
  lines.

## Assumptions I made

- **Agent tagging** (intent question 2): a fixed `§<id> <phase>` prefix
  in the description, set by the skills.
- **Phase boundaries** (question 3): commit times from git, since gate
  dates in `metadata.yml` are day-resolution.
- **Parallel time** (question 6): each intent counts its own wall-clock.
- **The 2 h cap** and the phase list (B3).
- **Skill names come from `.claude/skills/*/`** so the hook never logs
  arbitrary slash text.
