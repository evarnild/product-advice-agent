<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §20 plan — Bring a branch that is behind main up to date before each review round

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Before every review round, a branch that is behind local `main` is brought
up to date by **merging `main` into it** in its own worktree, never by a
rebase, so the round reviews the combination that will actually merge and
no earlier `reviewed-commit` is rewritten. A new kit command,
`npm run update-branch -- <id>` (pure decisions in
`scripts/update-branch-lib.mjs`, git and process I/O in
`scripts/update-branch.mjs`), does the merge, aborts cleanly on a conflict,
runs `verify` after a clean merge, and reports with exit 0 / 1 / 2 / 3.
`/auto` runs it at each round start and `/review` before its passes; the
implementers resolve a mechanical conflict only on the coordinator's brief;
the report header gains `main: <hash>`; `ship`'s two refusal messages say
why a rewrite or a merge of `main` after the review means a new round; and
every "rebase" instruction in the kit's texts becomes "update". `/ship` keeps
today's rule (Q3) and `check:intent` is unchanged (Q6).

## Risks

- **Pass 9's footgun list is empty** at `ce2806f`
  (`REVIEW-POLICY.md:229-231`, "This list starts empty and grows from
  findings"), so no named class applies. The classes this kit has met before
  and that this change can hit are named below instead.
- **The real repository touched by a test.** The E2E suite runs `git merge`;
  it must work only in a throwaway sandbox and strip every inherited `GIT_*`
  variable, as `scripts/ship.test.mjs:15-22` does (a hook or `rebase -x`
  would otherwise point git at the real repository; see the comment at
  `scripts/spawn-intent.test.mjs:17`).
- **Recursion into the real `verify`.** If the test forgets the override
  variable, the script runs `npm run verify` inside the sandbox. The test
  helper always sets it (like `ship.test.mjs:35`), and a red/green marker
  file proves which command ran.
- **The machine's git config changing the outcome.** A global
  `merge.ff=only`, `commit.gpgsign=true` or `merge.conflictStyle` changes
  what `git merge` does. The E2E sandbox sets `GIT_CONFIG_GLOBAL` to an empty
  file in the sandbox and `GIT_CONFIG_NOSYSTEM=1`, plus `core.autocrlf
  false` as `ship.test.mjs:104` does.
- **Parsing git's prose.** git's messages are localised; the script must
  classify a merge from facts (exit status, `MERGE_HEAD` present, `HEAD`
  before/after, `git diff --name-only --diff-filter=U`), never from message
  text. git's message is only relayed (B2's "with git's message").
- **Tests that pass whatever the code does.** An E2E case that checks only
  the exit status would pass a script that merged and then reset. Every
  E2E case asserts state: `HEAD`, the merge commit's parents, `main`, every
  other branch, the origin's refs, `MERGE_HEAD`, `git status`.
- **Unreachable refusals.** B1 finds the worktree by branch, so a detached
  `HEAD` (B2) and "the target's branch is `main`" (B2) cannot be found that
  way. See "Assumptions I made" for how the plan reaches the first and why
  the second is a guard proven by a unit test only.
- **A grep test that proves less than it looks.** The docs test in subtask 5
  is a denylist of the old phrasings plus required phrases; it cannot prove
  that no *new* rebase instruction exists. The review's full grep (AC6)
  stays the proof (the spec's amendment A3 reads AC6 this way).
- **Doc-only rules.** B9-B13, B15-B17, B20, B22-B23 and B14 are agent
  instructions; nothing executes them in `verify`. They are proven by
  reading (passes 1 and 3), by the cheap grep test, and by the live check
  (AC9).
- **Stale line citations.** Every `path:line` below was re-read at
  `ce2806f`; `main` moves while §20 waits. The implementer re-checks the
  ones a subtask edits before editing.
- **Lint cap:** none exists for the kit (`.mjs` is not linted by ruff), so
  none can rise.

## Verified against the codebase

Re-read on `main` at `ce2806f`.

**Merge preconditions (`ship`)**

- `REVIEW-POLICY.md:186-187` — "Its `reviewed-commit` is an ancestor of the branch (`git merge-base --is-ancestor`). A rebase since the review means a new round." (B20 rewrites it.)
- `REVIEW-POLICY.md:188-189` — "Nothing but that intent's `review.md` or `metadata.yml` differs between `reviewed-commit` and the branch (`git diff --name-only`)."
- `scripts/ship-lib.mjs:95-99` — the `reviewed-commit` refusal; message at `:98`: "`reviewed-commit ${…} is not an ancestor of the branch (rebased since the review: a new round is needed).`"
- `scripts/ship-lib.mjs:101-105` — the `unreviewed-changes` refusal; message at `:104`: "`changed since the reviewed commit besides review.md and metadata.yml: ${stray.join(', ')}.`"
- `scripts/ship.mjs:188-194` — `preconditionInputs`; `:192` `git diff --name-only <rc> <branch>` (two-dot tree diff, so a merged-in `main` file counts as stray).
- `scripts/ship.mjs:17-18` — "SDLC_SHIP_VERIFY, when set, is a command line that runs in place of `npm run verify`".
- `scripts/ship.mjs:236-242` — `runVerify`: `spawnSync(command, { cwd, shell: true, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 })`, tail of the last 25 lines at `:240`.
- `scripts/ship.mjs:223-234` — `mergeBranch` aborts a failed merge with `gitOk(root, 'merge', '--abort')`: the precedent for B7.
- `scripts/ship.test.mjs:15-22` — `GIT_ENV` strips `GIT_*` and sets author/committer; `:23-24` `VERIFY_OK` / `VERIFY_RED`; `:32-37` the `ship()` runner with `SDLC_SHIP_VERIFY`; `:70-95` `makeIntent` (worktree under `product-advice-agent-wt/<id>-t<id>`, work commit, review commit); `:97-110` sandbox with a bare `origin`; `:104` `core.autocrlf false`; `:112-124` cleanup; `:299-303` `snapshot`.
- `scripts/ship.test.mjs:305-320` — the `unreviewed-changes` E2E case; `:323-336` the `reviewed-commit` case, asserting `/not an ancestor/` at `:329` (the new message keeps that phrase).
- `scripts/ship.test.mjs` — ids used by `makeIntent` run 11-52; 53 and up are free.
- `scripts/ship-lib.test.mjs:36-49` — `checkPreconditions` unit cases for `reviewed-commit` and `unreviewed-changes` (match `failed`, not the message).

**Report header readers**

- `REVIEW-POLICY.md:250-260` — the header block; `:256` `reviewed-commit: <hash>` (B18 adds `main: <hash>` after it); `:297-298` the paragraph explaining `run:`.
- `scripts/intent-check-lib.mjs:298-306` — `parseReviewHeader` keeps every `^[a-z][\w-]*:` line before `## ` / `# Round`.
- `scripts/intent-check-lib.test.mjs:272-307` — its tests (exact `toEqual` of the parsed object).
- `scripts/check-intent.mjs:68` — reads the header (uses `live-check`); `:74-77` diffs from `git merge-base <base> <branch>`.
- `scripts/scan-lib.mjs:149-158` — `parseReviewFields`: `^verdict:` etc. by regex, `run` via `parseReviewHeader`; `scripts/scan-lib.test.mjs:196-221` its tests.
- `scripts/intent-check-lib.mjs:263-266` — `auto_round` must be 1..3 when present; an empty value is not present (`:264`), so B11's "left empty" passes.

**Worktrees, sessions, brief**

- `scripts/session-io.mjs:12-14` — `git(cwd, ...args)` (`execFileSync`, throws on non-zero); `:22-25` `mainCheckout` = first `git worktree list` entry.
- `scripts/session-lib.mjs:45-47` — `pathKey`; `:50-66` `parseWorktreeList` → `{path, head, branch|null, bare}`; `:31-35` `worktreePathFor` (`<parent>/product-advice-agent-wt/<id>-<slug>`).
- `scripts/intent-check-lib.mjs:28` — `BRANCH_RE` (`feat|fix|refactor|adjust|exp`, optional `codex/`); `:34-38` `parseBranch` → `{prefix, type, id, slug}`.
- `scripts/sessions.mjs:60-66` — `printTable`; `:62-65` prints "Behind main (rebase before review): …" for rows with `behind > 0` and a session not `closed`.
- `scripts/session-lib.mjs:314-337` — `sessionBrief`; `:332` "**Do not merge into \`main\`** and do not rebase other branches." (a prohibition, stays); `:335` "If you are told \`main\` moved, rebase this branch on it and re-run \`npm run verify\`." (B22 rewrites it).
- `scripts/session-lib.test.mjs:392-415` — the `sessionBrief` test.
- `package.json:10-23` — `scripts`; `:11` `test:kit` is `node --test "scripts/*.test.mjs"` (a new `*.test.mjs` runs in `verify` with no wiring); no `dependencies` key.
- `scripts/intent-check-lib.mjs:155-160` — `CORE_CODE` holds only `src/advisor/...`, so no kit change is core code.

**Skills, agents, policy, CLAUDE.md**

- `.claude/skills/auto/SKILL.md:89-103` — the resume table; `:105` "A new round always passes the cap in step 5, item 1."
- `.claude/skills/auto/SKILL.md:170-181` — step 5 items 1 (the cap) and 2 (write and commit `auto_round: <n>`); `:182-192` items 3-4 (delegate the review; re-check, write `review.md`); `:193-204` item 5 (act on the verdict). Only "item 1" is cross-referenced (`:94`, `:105`, `:202`), so inserting a new item 2 renumbers nothing that is referenced.
- `.claude/skills/auto/SKILL.md:290-295` — "Other stops"; `:291-292` "a red `verify` … you cannot trace to a finding the implementer is fixing".
- `.claude/skills/auto/SKILL.md:322-327` — step 9 item 1: "Write `auto_round: <n>` (the number of the round in progress or just finished, never above 3)".
- `.claude/skills/auto/SKILL.md:345-348` — safety rule "never merge, push, rebase or delete a branch or worktree".
- `.claude/skills/auto/SKILL.md:69-71` — "write only while no implementer is running in the worktree".
- `.claude/skills/review/SKILL.md:22-36` — step 0 "Orient"; `:30-31` "**Read-only:** no commits, resets, stashes, merges, or edits to code. The only file you write is `review.md`."; `:93-95` step 4 "Use exactly the format in `REVIEW-POLICY.md` → "The report"."
- `.claude/skills/sessions/SKILL.md:33-34` — "Each merge makes the others rebase, so the cheap ones go first."; `:35-39` the notice "main moved (§<merged id> merged). Rebase `<branch>` on main and re-run `npm run verify`."; `:48-49` "send or draft the rebase notice".
- `.claude/agents/product-advice-agent-implementer.md:3` — description "… Never pushes, merges, touches main, or records a gate."; `:32-36` "Do NOT push, merge, touch `main` …".
- `.codex/agents/product-advice-agent-implementer.toml:15-17` — "Do not push, merge, or switch main. … an implementer never merges."
- `.claude/agents/product-advice-agent-reviewer.md:60-61` — "Run `git diff main...<branch>`"; `:65-66` "**Enumerate mutations from `git diff`, one per changed behavioural line**".
- `.codex/agents/product-advice-agent-reviewer.toml:12-13` — "re-derive the behaviour from the diff, the tests, and spec.md's acceptance criteria." (no diff command).
- `REVIEW-POLICY.md:30` — Reviewed row: this file, `scripts/ship-lib.mjs`, `.claude/agents/**`, `.codex/agents/**`, `.claude/skills/**`.
- `REVIEW-POLICY.md:76-89` — live-check rules; rule 3 at `:85-87`.
- `CLAUDE.md:19-35` — the Commands block (`npm run ship` at `:26`, `npm run stats` at `:27`); `:121` "sends "main moved, rebase" notices"; `:126` "It never edits the queue (it is generated), never merges, and sets `status: in-review` when done."; `:142` "more sessions mostly add rebases".
- `grep -rn -i rebase` over `.claude/ .codex/ REVIEW-POLICY.md CLAUDE.md scripts/*.mjs` at `ce2806f`: the instructions are `sessions/SKILL.md:34,36,48`, `CLAUDE.md:121,142`, `session-lib.mjs:335`, `sessions.mjs:65`, `REVIEW-POLICY.md:187`; prohibitions `auto/SKILL.md:348`, `session-lib.mjs:332`; the ship message `ship-lib.mjs:98`; descriptive mentions that are no instruction: `stats-lib.mjs:22`, `spawn-intent.test.mjs:17`, `ship.test.mjs:84,324-330`, `stats.test.mjs:174-201`.
- Skill versions: `auto`, `review` and `sessions` are `0.2.0`; `git log` shows no version bump on any earlier skill edit (§17, §18, §19), so this plan bumps none.

## Subtasks

Each ends with `npm run verify` green and is its own commit (`§20: …`).

1. **Pure decisions** (B2-B8 decisions, AC1). Add `scripts/update-branch-lib.mjs`
   (imports only `intent-check-lib.mjs` / `session-lib.mjs`; no
   `node:child_process`, no `node:fs`) and `scripts/update-branch-lib.test.mjs`.
   Exports, roughly:
   - `EXIT = { OK: 0, REFUSED: 1, CONFLICT: 2, RED: 3 }`;
   - `parseUpdateArgs(argv)` → one all-digits id, else a usage error;
   - `findTarget(worktrees, id, mainPath)` → the worktree whose branch's
     `parseBranch(...).id` is `id`; else a refusal: "§id is on more than one
     worktree" when two match, "HEAD is detached in <path>" when no branch
     matches but a worktree whose folder name starts with `<id>-` has no
     branch, otherwise "no worktree has §id's branch checked out";
   - `preflight({ path, branch, mainPath, inProgress, dirty })` → ok or a
     refusal, in this order: an operation in progress (`merge`, `rebase`,
     `cherry-pick`, named), the main checkout (by `pathKey`), branch `main`,
     detached, tracked changes (listing them);
   - `planUpdate(behindCount)` → `up-to-date` or `merge` (B3: `> 0`);
   - `classifyMerge({ status, mergeHead, headBefore, headAfter, unmerged })`
     → `merged` (status 0), `conflict` (`MERGE_HEAD` present and `unmerged`
     non-empty), `refused` (no `MERGE_HEAD`, `HEAD` unchanged), else
     `unexpected`;
   - `classifyAbort({ headBefore, headAfter, mergeHead, dirty })` → clean or
     the list of what is left;
   - `formatReport(outcome)` → `{ exit, lines }` for up-to-date, merged
     green, merged red (with the output tail), conflict (files), abort left
     something, refusal (reason, plus git's message when there is one);
   - `outputTail(text, n = 25)`.
2. **The command** (B1-B8, AC2, AC8). Add `scripts/update-branch.mjs` and
   `"update-branch": "node scripts/update-branch.mjs"` to `package.json`.
   Flow: parse args → `git worktree list --porcelain` from `process.cwd()`
   (any checkout; main = first entry) → `findTarget` → gather `inProgress`
   from `git -C <wt> rev-parse --git-path MERGE_HEAD|rebase-merge|rebase-apply|CHERRY_PICK_HEAD`
   + `existsSync`, `dirty` from `git status --porcelain --untracked-files=no`
   → `preflight` → `git rev-list --count <branch>..main` → up to date: print
   "contains main at <short>", exit 0 → else print "behind main by N", record
   `HEAD`, `spawnSync('git', ['-C', wt, 'merge', '--no-edit', 'main'])` →
   `classifyMerge`: refused → exit 1 with git's stderr; conflict → list
   `git diff --name-only --diff-filter=U`, `git merge --abort`,
   `classifyAbort` → 2 or 1; merged → run the verify command
   (`SDLC_UPDATE_BRANCH_VERIFY` or `npm run verify`, `shell: true`, `cwd`
   the worktree, as `ship.mjs:236-242`) → 0 or 3 (merge kept). Never fetch,
   push, reset, stash, rebase, write a file, or append to the session log.
   Header comment in the style of `ship.mjs:1-18`. E2E tests in
   `scripts/update-branch.test.mjs` (see Tests).
3. **Ship messages and the `main:` header** (B18 parsing, B19, AC3, AC4).
   Change `ship-lib.mjs:98` to "… is not an ancestor of the branch (rewritten
   since the review, by a rebase or an amend: a new round is needed)." and
   `:104` to append " (a merge of main since the review counts: a new round
   is needed)". Add unit cases to `ship-lib.test.mjs`, the merge-of-main E2E
   case to `ship.test.mjs`, and `main:` header cases to
   `intent-check-lib.test.mjs` and `scan-lib.test.mjs`. No reader changes.
4. **Sessions line and brief** (B21, B22 brief part, AC5). Move the line at
   `sessions.mjs:62-65` into `session-lib.mjs` as `behindLine(rows)`
   (returns the text or `null`), wording "Behind main (update before
   review): §n (-N)", and call it from `sessions.mjs`. Rewrite
   `session-lib.mjs:335` to: "If you are told \`main\` moved, bring this
   branch up to date: \`npm run update-branch -- ${id}\` (merges main, never
   rebases), then resolve any conflict and re-run \`npm run verify\`." Tests
   in `session-lib.test.mjs`.
5. **Policy, skills, agents, CLAUDE.md** (B9-B17, B18 policy part, B20, B22
   skill part, B23, AC6, AC7). Edit, keeping each file's style:
   - `REVIEW-POLICY.md`: `:186-187` per B20 (a rewrite fails the ancestor
     check, a merge of `main` fails the next; either means a new round);
     add to "Merging" that a branch behind `main` is not refused (Q3) and is
     brought up to date before each round with `npm run update-branch`
     (never a rebase); add `main: <hash>` after `:256` and a sentence after
     `:297-298` saying what it is (B18, I4).
   - `.claude/skills/auto/SKILL.md`: new step 5 item 2 "Bring the branch up
     to date" (B9, B10 table of exits, I2) between the cap and the
     `auto_round` write (old items 2-5 become 3-6; B10's "go on to item 2"
     is written as "go on to the round-start write"); three rows in the
     resume table (B12); the three reasons in step 7 "Other stops"; step 9
     item 1 says a stop at the update leaves `auto_round` unchanged (empty
     before round 1, never `0`) (B11); the safety rule at `:345-348` per
     B13; item 4's `review.md` carries `main:`.
   - `.claude/skills/review/SKILL.md`: step 0 gains the update (B15), the
     manual outcomes (B16), the three-dot diff and that mutations come from
     it (B17), and recording `main:` as `git rev-parse --short main` once
     the update is done, before pass 1 (B18, I4); the read-only bullet
     `:30-31` names the script's merge as the one exception, made before
     the review starts.
   - `.claude/skills/sessions/SKILL.md:33-39, 48-49`: "update" and the B22
     notice text.
   - Both implementer definitions: the B14 rule as an explicit exception to
     "do not merge"; the Claude one's description (`:3`) says "never merges
     into main" so it does not contradict the rule (see Assumptions).
   - `.codex/agents/product-advice-agent-reviewer.toml`: name the change as
     `git diff main...<branch>` and mutations from it (B17);
     `.claude/agents/product-advice-agent-reviewer.md:65`: "from
     `git diff main...<branch>`".
   - `CLAUDE.md`: `npm run update-branch -- <id>` in Commands after
     `npm run ship` (`:26`), with a one-line comment; `:121` "main moved,
     update"; `:126` "never merges into `main`" (amendment A4); `:142` "add
     updates" (B23).
   - Add `scripts/kit-texts.test.mjs`, the grep test below.
6. **Progress entry and `status: in-review`** (the implementer's own
   bookkeeping; no gate).

## Tests

All in `npm run test:kit` (so in `verify`). Faked: `verify` is an
environment-variable command; no network, no real repository.

**`scripts/update-branch-lib.test.mjs` (AC1; B2-B7 decisions)**

| Behavioural line | Test that fails if it is mutated |
| --- | --- |
| `parseUpdateArgs`: digits only, exactly one | "rejects no id, two ids, `--x`, `20a`" |
| `findTarget` by `parseBranch(...).id` | "finds `feat/20-x` and `codex/fix/20-y`, not `feat/200-z` or `feat/2-x`" (kills `startsWith`-style matches) |
| `findTarget`: two matches refused | "two worktrees for §20 → refusal naming both" |
| `findTarget`: detached by folder | "worktree `…/20-x` with branch null → 'HEAD is detached'"; "`…/200-x` detached → 'no worktree'" |
| `preflight` order and each reason | one case per reason (merge, rebase, cherry-pick in progress; main checkout by `pathKey` with different case and slashes; branch `main`; detached; tracked changes); a case with two faults asserts the in-progress reason wins |
| `planUpdate`: `> 0` | 0 → `up-to-date`, 1 → `merge` (kills `>= 0` and `> 1`) |
| `classifyMerge` | status 0 → merged; status 1 + `MERGE_HEAD` + unmerged → conflict; status 1, no `MERGE_HEAD`, same `HEAD` → refused; status 1, no `MERGE_HEAD`, `HEAD` moved → unexpected |
| `classifyAbort` | clean only when `HEAD` same, no `MERGE_HEAD`, nothing dirty; each fault alone → listed |
| `formatReport` exits and lines | each outcome's exit (0/0/3/2/1/1) and its key text: "contains main at abc1234", "behind main by 2", "verify green", "verify red after merging main" + tail, conflicted file names |
| `outputTail` | 30 lines → last 25 |
| Boundary (Non-functional) | "the lib imports no `node:child_process` / `node:fs`": reads its own source and asserts no such import |

**`scripts/update-branch.test.mjs` (AC2; B1, B2, B4-B8; E2E)**

Sandbox as `ship.test.mjs:97-110`: a main checkout, a bare `origin`, worktrees
under `product-advice-agent-wt/`; `GIT_ENV` without `GIT_*`,
`GIT_CONFIG_GLOBAL` = an empty sandbox file, `GIT_CONFIG_NOSYSTEM=1`;
verify commands that write a marker file (absolute sandbox path) holding
`process.cwd()` and exit 0 or print `boom` and exit 3. A `snapshot()` holds
`main`, every `refs/heads/*` but the target, `git ls-remote origin`, the
`refs/remotes/*` list and whether `FETCH_HEAD` exists in the common dir.

| Case | Asserts (what a mutant would break) |
| --- | --- |
| up to date (B4) | exit 0; "contains main at <short main>"; `HEAD` unchanged; no marker (no verify ran); snapshot equal |
| behind, own commits, green (B5) | exit 0; "behind main by N"; `git rev-list --parents -n1 HEAD` = new, old tip, `main`; new and `main` short hashes and "verify green" printed; marker holds the worktree path (verify ran there); snapshot equal |
| behind, no own commits (B5 fast-forward) | exit 0; `HEAD` = `main`; no merge commit |
| red verify (B6) | exit 3; "verify red after merging main" and `boom`; `HEAD^2` = `main` (merge kept); snapshot equal |
| conflict (B7) | exit 2; the conflicted file named; `HEAD` = old tip; `git status --porcelain --untracked-files=no` empty; no `MERGE_HEAD`; no marker; snapshot equal |
| run from the worktree itself (B1) | same result as from the main checkout |
| refusals (B2), each: exit 1, reason named, `HEAD`, status and snapshot unchanged | no worktree for the id; §id branch checked out in the main checkout (sandbox only); detached worktree at `…/<id>-x`; a merge in progress (a real conflicted merge left in place); a cherry-pick in progress (real); a rebase in progress (real; see Assumptions); a modified tracked file; a staged new file; an untracked file in the way of `main`'s change (git's refusal relayed, untracked file intact) |
| never a rebase or remote (B8) | across all cases: origin refs, `refs/remotes`, no `FETCH_HEAD`, `main` and other branches unchanged; old tip's commits still ancestors of `HEAD` |
| usage | no id → exit 1, "usage" |

Not proven end to end: "the abort left something behind" (exit 1 after an
abort). git does not leave state behind on a plain `merge --abort`, so the
path is proven by `classifyAbort` and `formatReport` unit cases only.

**`scripts/ship-lib.test.mjs` and `scripts/ship.test.mjs` (AC3; B19)**

- `ship-lib.test.mjs`: the `reviewed-commit` refusal message contains
  "rewritten since the review, by a rebase or an amend"; the
  `unreviewed-changes` message contains the stray file and "a merge of main
  since the review counts" (kills reverting either string).
- `ship.test.mjs`, new case (id 53): `makeIntent(53)`; commit
  `docs/main-moved.md` on `main` and push it to the sandbox `origin`;
  `git merge --no-edit main` in the worktree; `ship(['53'])` → exit 1,
  `STOPPED preconditions unreviewed-changes`, names `docs/main-moved.md` and
  "a merge of main since the review counts"; `snapshot(w)` unchanged; the
  worktree still exists. The existing `:323-336` case keeps proving the
  rewrite path (`/not an ancestor/`).

**Header parsing (AC4; B18)**

- `intent-check-lib.test.mjs`: a header with `main: abc1234` between
  `reviewed-commit:` and `round:` parses to the same `verdict`,
  `reviewed-commit`, `live-check` and `run` plus `main`.
- `scan-lib.test.mjs`: `parseReviewFields` with a `main:` line returns the
  same `verdict`, `tier`, `round`, `sampled`, `run`.
- `ship` reads the header through the same `parseReviewHeader`: `makeIntent`
  (`ship.test.mjs:70-95`) gains an optional `main` value written as a
  `main:` line after `reviewed-commit:`, and case 53 uses it, so `ship`
  reads `verdict` and `reviewed-commit` with the line present (a refusal
  by `unreviewed-changes`, not `verdict` or `reviewed-commit`, proves it).

**`scripts/session-lib.test.mjs` (AC5; B21, B22 brief)**

- `behindLine`: rows behind 2 and open → "Behind main (update before
  review): §27 (-2)"; a closed row and a row behind 0 are left out; no rows
  → `null`; never matches `/rebase/i`.
- `sessionBrief`: contains "`npm run update-branch -- 28`" and "never
  rebases"; does not contain "rebase this branch".

**`scripts/kit-texts.test.mjs` (AC6, AC7; cheap grep, weak by design)**

- Required: `npm run update-branch` in `auto/SKILL.md`, `review/SKILL.md`,
  `sessions/SKILL.md`, `REVIEW-POLICY.md`, `CLAUDE.md`; `git merge main` and
  `git merge --abort` in both implementer definitions; `main...` in both
  reviewer definitions and `review/SKILL.md`; `main: <hash>` in
  `REVIEW-POLICY.md`; the three stop reasons in `auto/SKILL.md`.
- Denylist over `.claude/**`, `.codex/**`, `REVIEW-POLICY.md`, `CLAUDE.md`
  and non-test `scripts/*.mjs`: none of "rebase before review", "main moved,
  rebase", "Rebase \`<branch>\`", "rebase this branch", "A rebase since the
  review means", "others rebase", "add rebases".
- It cannot prove the absence of a new rebase instruction worded otherwise;
  the review's grep (AC6) does that.

**Proven by reading only:** B9-B13 and B15-B17 as agent behaviour (what the
coordinator and reviewer do), B14's resolution rule, B20's policy meaning,
B23's placement. The grep test proves the words are there; passes 1 and 3
and the live check (AC9) prove the flow.

**B/AC → subtask → proof**

| Item | Subtask | Proof |
| --- | --- | --- |
| B1 | 1, 2 | `findTarget` unit; E2E "run from the worktree", "no worktree" |
| B2 | 1, 2 | `preflight`/`findTarget` units; E2E refusals |
| B3 | 1, 2 | `planUpdate` unit; E2E up-to-date vs behind |
| B4 | 1, 2 | unit `formatReport`; E2E up to date (no marker) |
| B5 | 1, 2 | unit; E2E green and fast-forward |
| B6 | 1, 2 | unit; E2E red verify |
| B7 | 1, 2 | `classifyMerge`/`classifyAbort` units; E2E conflict |
| B8 | 2 | E2E snapshot in every case |
| B9-B13 | 5 | read; `kit-texts.test.mjs` required phrases; AC9 |
| B14 | 5 | read; `kit-texts.test.mjs` |
| B15-B16 | 5 | read; `kit-texts.test.mjs`; AC9 |
| B17 | 5 | read; `kit-texts.test.mjs` (`main...`) |
| B18 | 3, 5 | header parse tests; read; `kit-texts.test.mjs`; AC9 |
| B19 | 3 | `ship-lib.test.mjs` messages; `ship.test.mjs` case 53 |
| B20 | 5 | read; denylist ("A rebase since the review means") |
| B21 | 4 | `behindLine` test |
| B22 | 4, 5 | `sessionBrief` test; read; denylist |
| B23 | 5 | read; `kit-texts.test.mjs` |
| AC1 | 1 | `update-branch-lib.test.mjs` |
| AC2 | 2 | `update-branch.test.mjs` |
| AC3 | 3 | `ship-lib.test.mjs`, `ship.test.mjs` |
| AC4 | 3 | `intent-check-lib.test.mjs`, `scan-lib.test.mjs`, `ship.test.mjs` |
| AC5 | 4 | `session-lib.test.mjs` |
| AC6 | 5 | review read + grep; `kit-texts.test.mjs` (partial) |
| AC7 | 5 | read; `kit-texts.test.mjs` |
| AC8 | 2, all | `npm run verify`; `package.json` read (no `dependencies` key) |
| AC9 | — | the owner's live check below |

## Validation

- `npm run verify` green (kit tests incl. the three new test files, then the
  product half, untouched).
- `npm run check:intent` PASS: feature, no `CORE_CODE` path, tests changed.
- `uv run advisor-analysis owes-run --base main`: not owed (no `src/`
  change).
- The review's own grep: `grep -rn -i rebase .claude/ .codex/ REVIEW-POLICY.md CLAUDE.md scripts/*.mjs`
  shows only prohibitions, the ship message and descriptive mentions
  (`stats-lib.mjs:22` and test comments).
- **Live check, owed under rule 3 (AC9).** The owner runs, from the main
  checkout:
  1. With §20's worktree (or any spawned intent's) behind `main` (`npm run
     sessions` shows "Behind main (update before review): §n (-N)"):
     `npm run update-branch -- <id>`. See "behind main by N", then `verify`'s
     output, then the new `HEAD` and `main` hashes and "verify green", exit
     0 (`echo $?`). `git -C <worktree> log --oneline --graph -3` shows
     "Merge branch 'main' into <branch>" with `main` as second parent.
  2. Run it again: "contains main at <hash>", no `verify`, exit 0.
  3. Move `main` again (any commit), then `/review <branch>` in the
     coordinator: see it run `npm run update-branch` before any pass, and
     the new `review.md` header carry `main: <hash>` equal to
     `git rev-parse --short main` at that moment.
  4. Optional, in a scratch intent: a branch and `main` editing the same
     line. `npm run update-branch -- <scratch id>` exits 2 and names the
     file; `git -C <worktree> status` is clean and `git -C <worktree>
     rev-parse -q --verify MERGE_HEAD` prints nothing.
  Then `live_checked:` is recorded by the owner, or by an agent on their
  word.

## Assumptions I made

- **The detached refusal (B2) is reached by folder name** (the spec's
  amendment A1). B1 finds the
  worktree by branch, and a detached worktree has none. When no branch
  matches, a worktree whose folder name starts with `<id>-` (the name
  `npm run spawn` gives, `session-lib.mjs:31-35`) and has no branch is
  refused as "HEAD is detached in <path>"; otherwise "no worktree". This
  also covers a rebase in progress, during which `HEAD` is detached: the
  in-progress check runs first, so the reason names the rebase. If git
  lists the branch during a rebase instead, the same reason comes from the
  branch match. Either way exit 1, nothing changed.
- **Two worktrees for one id are refused** (exit 1, naming both), as
  `session-io.mjs:58-61` refuses two branches for one id: the spec's
  amendment A2.
- **"Its branch is `main`" is a guard** proven by a `preflight` unit case
  only: an id lookup can never select `main`.
- **In progress means** `MERGE_HEAD`, `rebase-merge`, `rebase-apply` or
  `CHERRY_PICK_HEAD` under the worktree's git dir (`git rev-parse
  --git-path`), the three operations B2 names. A revert in progress is not
  named by B2; a conflicted one is caught by the tracked-changes check.
- **The verify override is `SDLC_UPDATE_BRANCH_VERIFY`**: the spec's
  amendment A6.
- **The red-verify tail is 25 lines**, as `ship.mjs:240`.
- **No session-log event** is appended: the spec's "Data" line says nothing
  is written outside the target worktree's git state.
- **The sessions line moves into `session-lib.mjs`** so AC5 has a test
  rather than a read (the AC allows either).
- **The Claude implementer's description** (`:3`, "Never pushes, merges,
  …") is narrowed to "never merges into main" (the spec's amendment A5). The Codex description names no merge.
- **No skill version bump**: no earlier skill edit bumped one.
- **The grep test file is new** (`scripts/kit-texts.test.mjs`) rather than
  part of an existing test, since it reads texts no script owns.
- **CLAUDE.md:126** ("never merges", about a spawned session) becomes
  "never merges into `main`": the spec's amendment A4 (2026-11-22).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-22 — subtasks 1-6

Commits: 83b1e5f (pure decisions), b7bec3a (the command, E2E), e6aef2a (ship messages, `main:` header tests), 1873299 (sessions line, brief), 79c685e (policy, skills, agents, CLAUDE.md, grep test); this entry and `status: in-review` follow in the sixth commit.

Shipped: `scripts/update-branch-lib.mjs` and `scripts/update-branch.mjs`, `npm run update-branch`; new `ship-lib.mjs` messages; `behindLine` in `session-lib.mjs` and the brief's update wording; the policy, `/auto`, `/review`, `/sessions`, both implementer and both reviewer definitions, `CLAUDE.md`; `scripts/kit-texts.test.mjs`.

Tests (kit): 434 pass, 0 fail, up from 382 at the start. New: `update-branch-lib.test.mjs` 20, `update-branch.test.mjs` 17 (E2E, sandbox repos, `SDLC_UPDATE_BRANCH_VERIFY`), `kit-texts.test.mjs` 7; added cases: `ship-lib.test.mjs` 2, `intent-check-lib.test.mjs` 1, `scan-lib.test.mjs` 1, `session-lib.test.mjs` 3 (brief 1, `behindLine` 2), `ship.test.mjs` 1 (id 53). pytest 859 passed, ruff and mypy clean. `check:intent` PASS.

Divergences: (1) `findTarget(worktrees, id)` takes no `mainPath` (only `preflight` needs it) and returns `detachedPath` on the detached refusal, so `update-branch.mjs` can name a rebase in progress (HEAD is detached then) as "a rebase is in progress", as the plan's assumption says. (2) `formatReport` prints "behind main by N" itself, after the merge, with the result; the script prints nothing before the merge, and `verify`'s output is shown only as the tail on red (not streamed), so the live check's "then verify's output" is the tail on a red run only. (3) The E2E "id checked out in the main checkout" case commits on that branch in the sandbox. (4) No mutation testing was run.
