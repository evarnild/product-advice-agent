<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §19 plan — Time, tokens and owner wait per intent and phase

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

`npm run stats` (spec B8) joins git milestones, the session log and the
Claude Code transcripts into per-phase elapsed time, owner wait (gate and
in-session, capped, B6) and tokens per model (coordinator vs agents, B4),
never guessing (B4, B7); the hook logs `skill`/`skillId` for slash prompts
(B1); agents are tagged `§<id> <phase>` (B2); `/ship` commits `stats.md`
without ever being blocked by it (B9); `/grid` reads it (B11).

## Risks

- **Prompt text leaking** into the log, a stats output or `stats.md` (B1,
  B10). Every test fixture carries a sentinel prompt string; tests assert
  it never appears in any output or log line.
- **A hook that prints or fails** in every session. `eventRecordFrom` stays
  pure and total; tests feed it malformed input; `session-event.mjs` is
  unchanged except through `eventRecordFrom`.
- **Ship blocked by stats** (B9): collection runs in a `try`; a throwing
  collector is tested to still ship (temp repo).
- **Double counting tokens** across coordinator and agents, or a turn in two
  intents; tests sum per source and compare with the fixture total.
- **Transcript format drift** (intent constraint): unknown shapes are
  skipped and counted; tests include garbage lines.
- **Reading real transcripts in tests**: forbidden; synthetic fixtures under
  `scripts/fixtures/stats/` only, and the transcript root is a parameter.
- **Merge overlap with §18**, which also edits `.claude/skills/{auto,spawn,intent,…}`;
  this plan edits different paragraphs (agent descriptions) and the
  coordinator resolves any conflict at merge.
- Reviewed tier; live check owed. Pass 9's list is empty.

## Verified against the codebase

Re-read on `main` at `5dabf91`.

- `scripts/session-event.mjs:14-20` — reads stdin, `eventRecordFrom(...)`, `appendEvent`, swallows errors, `process.exit(0)`.
- `scripts/session-lib.mjs:136-160` — `eventRecordFrom(input, env, fallbackCwd)`: for `UserPromptSubmit`, `fields.promptChars = … input.prompt.length` and `fields.detail = \`${…} chars\``; comment "Prompts are logged by length only".
- `scripts/session-lib.test.mjs:174` — `describe('eventRecordFrom', …)`.
- `.git/product-advice-agent-sessions.jsonl` — lines like `{"ts","worktree","branch","id","event","session","promptChars","detail"}`; `Notification` lines carry `kind` (`permission_prompt`, `idle_prompt`).
- `~/.claude/projects/C--Users-eric-src-product-advice-agent/<session>.jsonl` and `<session>/subagents/agent-*.jsonl` + `agent-*.meta.json` exist (layout seen on disk; content not read into the repo).
- `scripts/ship.mjs:252-275` — `bookkeepMetadata` and `bookkeeping(root, loc, trailers)`: `edits = [bookkeepMetadata(...)]`, all-or-nothing write and commit `§${id}: merged (${hash}); status done`. B9 appends a second edit.
- `scripts/ship-lib.mjs:12` — step label `'bookkeeping commit (metadata.yml)'`.
- `package.json` scripts — `queue`, `sessions`, `ship` as `node scripts/<x>.mjs`; `stats` goes beside them.
- `.claude/skills/grid/SKILL.md` — Measures section; `.claude/skills/{spawn,auto,review}/SKILL.md` — where agents are launched (B2).
- `CLAUDE.md` → Parallel sessions: "It holds **no prompt text**: a prompt is logged by its length only."

## Subtasks

1. **Hook fields (B1)**: `eventRecordFrom` gains `skill`/`skillId` for a
   prompt starting `/<name>` with `<name>` in a skill list passed in
   (`session-event.mjs` reads `.claude/skills/*/` names from the project
   dir, cheaply, inside its existing `try`). Tests (AC1) with the sentinel.
   `CLAUDE.md` sentence updated. Commit.
2. **Pure stats core** (`scripts/stats-lib.mjs`): `milestones(commits)` →
   phases (B3); `usageLines(jsonlText)` → per-model usage + skipped count
   (B4, B7); `attribute(turns, agents, commits)` → per intent/phase,
   shared, unattributed (B4); `ownerWait(events, milestones, agentSpans)`
   with the 2 h cap and idle (B6); `formatStats` / JSON (B8). Tests over
   fixtures (AC2–AC5 logic). Commit.
3. **I/O** (`scripts/stats.mjs`, `package.json` `stats`): reads `git log`
   (`--format=%H %ct %s` over `main` and local branches), the session log,
   and transcripts under `~/.claude/projects/` for the main checkout's and
   worktrees' slugs (root overridable by `--transcripts <dir>` for tests);
   `-- <id>`, `--all` (with `partial` for intents merged before this
   change), `--json`. Tests on fixtures in a temp dir. Commit.
4. **Ship (B9)**: `bookkeeping` adds `intents/<id>/stats.md` (stamped,
   generated) when collection succeeds; on failure, no file and a report
   line; the step label says "(metadata.yml, stats.md)". Temp-repo tests:
   written; collector throws → still ships. Commit.
5. **Skills and docs (B2, B11)**: `/spawn`, `/auto`, `/review` say agent
   descriptions start `§<id> implement|rework|review`; `/grid` reads
   `intents/*/stats.md` for Measures; README/CLAUDE.md Commands line for
   `npm run stats`. Commit.
6. **Finish**: verify, check:intent, `npm run stats -- --all` run once on
   the real repo **printing only to the terminal** (quote the totals line
   and skipped counts in Progress, no prompt text), `status: in-review`,
   Progress entry.

## Tests

| Spec | Test | Mutation it kills |
| --- | --- | --- |
| B1 | `/spec 17`, `/auto 13`, `/review`, `/unknown 3`, `yes to 16`, `accept 15 and /auto 15`, leading spaces, non-string prompt; sentinel never logged | regex unanchored; any `/x` accepted; text logged |
| B2 | description `§13 review round 2` → 13/review; none → unattributed | loose `§` parse |
| B3 | full milestone set; a missing spec milestone merges into plan; a fix (no spec) | wrong ordering; dropping a phase |
| B4 | coordinator turn by skillId; by single-intent commits; two intents → shared; none → unattributed; agent by tag; sum of all = fixture total | double counting; guessing |
| B5 | overlapping intents each get full wall-clock | sharing out |
| B6 | gate wait from `auto stopped:` to `auto run resumed`; in-session wait from `Stop` to next prompt; 3 h gap → 2 h wait + 1 h idle; agent span not wait | cap off by one; counting agent time |
| B7 | garbage and unknown lines skipped and counted | throwing; silently dropping |
| B8 | text and JSON shapes; `--all` marks `partial` | missing columns |
| B9 | stats.md in the bookkeeping commit; collector throws → ship completes, report line | ship stops on stats |
| B10 | sentinel prompt absent from every output | leaking text |

## Validation

- `npm run verify` green; `npm run check:intent` PASS (FAIL only on the
  owed live check).
- Live check (owed): the owner runs `npm run stats -- 13` (or the latest
  shipped intent) and `npm run stats -- --all`, checks the figures against
  the run, and after typing `/sessions`, sees `skill`/`skillId` and nothing
  else of the prompt in `.git/product-advice-agent-sessions.jsonl`.

## Assumptions I made

- The skill list for B1 is read by the hook at each prompt from
  `.claude/skills/*/` (a directory listing, no file reads).
- "Merged before this change" for `partial` (B8) is decided by comparing
  the intent's `merged:` commit date with §19's merge, known at run time
  from git (the first commit containing `scripts/stats-lib.mjs` on main).
- Fixtures live in `scripts/fixtures/stats/` (kit tests read them).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
