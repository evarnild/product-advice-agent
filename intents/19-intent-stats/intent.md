<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §19 — Time, tokens and owner wait per intent and phase

**Type:** feature
**Originator:** me (owner), in the coordinator session: "I would like to
collect statistics about each intent. How much time and tokens for each
phase, also how much time waiting for my input"
**Source:** none (prompted by the parallel `/auto` runs on §13–§17)

## Problem

The kit can't say what an intent cost or where its time went. I can't
answer:

- how long each phase of an intent took (intent → spec → plan → build →
  review → ship);
- how many tokens each phase used, per model, including the implementer and
  reviewer agents;
- how much of an intent's elapsed time was spent waiting for me, at a gate
  or in a session, as opposed to agents working.

Without these numbers I can't tell whether `/auto` actually saves my time,
which phase is expensive, or whether a change to a skill made things
cheaper or dearer. The grid's Measures (`docs/sdlc-grid.md`) count changes,
reverts and tiers, but no time or cost: "Report progress and outcome
together, never one without the other."

The data mostly exists but nothing joins it, and the coordinator's work
can't be attributed to an intent:

- `.git/product-advice-agent-sessions.jsonl` has timestamps for prompts,
  turn ends, notifications, spawn and ship, but the coordinator's events
  carry `"id": null`, because one session in `main` works on many intents.
- Claude Code transcripts (`~/.claude/projects/<repo>/*.jsonl`, and
  `subagents/agent-*.jsonl` with `.meta.json`) hold `usage` per model call.
  The subagent meta names the intent only in free text (`"description":
  "Implement §12 trace evals"`).
- Phase boundaries exist only as commit subjects (`§17: spec drafted (by
  /spec)`, `§17: spec accepted …`).

## Outcome

- For any intent, and for all of them together, I can see each phase's
  elapsed time, the time it waited for me (at gates and in sessions,
  reported separately), and its tokens per model (input, output, cache read,
  cache write), with agent work separate from coordinator work.
- Work that can't be attributed to an intent or phase is reported as
  unattributed, with its size, and never guessed.
- A shipped intent's totals are kept in the repo, so the grid can track
  them over time.

## Constraints

- **Privacy.** No prompt or response text leaves the transcripts or goes
  into a commit. CLAUDE.md: "That file … holds **no prompt text**: a prompt
  is logged by its length only." Any change to what the hook logs, such as a
  skill name and intent id, is my decision (open question 1), and
  CLAUDE.md and the hook tests change with it.
- **Raw data stays local.** Transcripts and the session log are read in
  place and never copied into the repo. Only derived totals are committed.
- **No new dependency.** Kit code, Node ≥ 22 only.
- **Treat the transcript format as unstable.** The parser skips and counts
  lines it can't read, rather than failing or inventing numbers. Tests use
  synthetic fixtures, never real transcripts.
- **Read-only.** Collecting stats never changes a gate, a branch or a
  session, and a failure in it never blocks `/ship` or a hook.
- **Cost:** none. No model calls.
- **Review tier:** Reviewed whenever it touches `.claude/settings.json`,
  `scripts/session-event.mjs` or `.claude/skills/**` (REVIEW-POLICY.md path
  table); Attested otherwise.
- **Out of scope:** dollar pricing beyond an optional per-model rate table,
  stats for other repositories, and dashboards outside the terminal.

## Type-specific questions

### Feature
- **Users:** the owner. The `/grid` skill reads the totals.
- **What exists today:** nothing reports these. The session log, the
  transcripts and git hold the raw data, unjoined.
- **Open design questions:**
  1. **Attributing coordinator work:** may the `UserPromptSubmit` hook also
     log the skill name and intent id when a prompt starts with a slash
     command (`/spec 17` → `skill: spec, id: 17`)? It would still log no
     other text. If not, coordinator tokens are attributed only through gate
     commits and time windows, or left unattributed.
  2. **Attributing agents:** parse `§<id>` from the subagent's description,
     or have `/spawn`, `/review` and `/auto` put a fixed tag in the
     description so it can be read reliably?
  3. **Phase boundaries:** from gate commit times (git), from the gate dates
     in `metadata.yml` (day resolution only), or from skill events?
  4. **What counts as "waiting for me":** gate wait (from a drafted artefact
     or an `/auto` stop to my acceptance or my next `/auto`), in-session wait
     (from a turn end or permission prompt to my next prompt), or both? How
     are overnight gaps handled: a cap, or business hours?
  5. **Where totals land:** a `stats.md` written by `/ship`, a `stats:` block
     in `metadata.yml`, or generated only (`npm run stats`) with the grid
     reading it?
  6. **Parallel phases:** when several intents' sessions overlap, does
     wall-clock time count for each intent, or is it shared out?
  7. **Backfill:** report §1–§18 with what is recoverable (git timings and
     agent tokens), or start counting from this change?

## Assumptions I made

- **Feature, not adjustment or experiment:** a new script, possibly hook
  and skill changes, and a committed format.
- **A Claude Code session's own data is the source.** The session log, the
  transcripts and git. Not Langfuse: that traces the product, not the SDLC.
- **Tokens, not dollars, are the main unit,** because prices change and the
  model mix shows in the per-model split.
- **The command name `npm run stats`** is a placeholder.
- **Codex sessions** (`.codex/agents/**`) are out of scope unless the
  spec finds their usage is easy to read.
