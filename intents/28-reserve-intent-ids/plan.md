<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §28 plan — Two machines can give two intents the same number

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md) (feature only)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A new intent's number is claimed on `origin` the moment `/intent` writes the
draft, and every machine's `npm run queue -- --next-id` sees the claims of
the others. Concretely (spec B1–B24): a new script `npm run reserve-id --
<id>` pushes one parentless commit holding only the draft's `intent.md` and
`metadata.yml` to a new branch `intent/<id>` on `origin`, refusing anything
else; `--next-id` fetches `origin` (bounded at 10 s, a warning and never an
error when it fails) and counts the `intents/<n>-*` folders and `intent/<n>`
refs found there, and reports a same-number/different-folder clash on
stderr; `/deliver` stops early, with a clear message, when `origin/main`
already holds another folder with the intent's number, and notes a foreign
reservation; the policy texts gain the one standing exception to "push only
on request", and the `/intent` skill runs the reservation for a new draft.
The 2026-11-24 collision, replayed in a kit test, gives the second machine
§24 or reports the clash at `--next-id` time (spec AC9).

## Amendment after review round 1 (owner, 2026-11-24: "28 D1 b")

Subtask 1 said a failed fetch's reason is "git's last stderr line". For
common failures that line is boilerplate ("and the repository exists.").
**The reason is git's first `fatal:` or `error:` stderr line; if there is
none, the first non-empty line; if there is no output, "git exited <code>".**
A timeout stays "timed out after <n> s". A test pins the AC4 reason, and
the mutant that takes the last line must fail it.

## Risks

- **Bug classes named in `REVIEW-POLICY.md` pass 9.** None yet: the list
  "starts empty and grows from findings" (`REVIEW-POLICY.md:237-239`). The
  classes this repo's kit has hit before and that apply here are the ones its
  test harnesses already guard against: inherited `GIT_*` variables pointing a
  sandbox at the real repository (`scripts/deliver.test.mjs:15-22`), the
  machine's git config changing what git does (`scripts/update-branch.test.mjs:22-32`,
  `GIT_CONFIG_GLOBAL` + `GIT_CONFIG_NOSYSTEM`), and CRLF changing bytes
  (`core.autocrlf false`, `scripts/deliver.test.mjs:104`). All new tests use
  the update-branch form of the environment: it also keeps a global
  credential helper, `url.*.insteadOf` or `core.hooksPath` out of the
  sandboxes, which matters more here than anywhere, because these tests
  fetch and push.
- **Windows: a timed-out fetch that does not return (the main technical
  risk).** `spawnSync(..., { timeout })` kills only the process it started.
  On Windows `git` on `PATH` is usually the `cmd\git.exe` shim, which runs
  `mingw64\bin\git.exe`, which runs `ssh` or the credential helper; those
  grandchildren inherit the stderr pipe, and `spawnSync` waits for every pipe
  to close, so a "killed" fetch still blocks until the grandchild exits (60 s
  in AC5, forever for a waiting credential prompt). The bounded runner must
  therefore (a) kill the whole process tree (Windows: `taskkill /PID <pid> /T
  /F`; POSIX: the child started `detached` as its own process group, then
  `process.kill(-pid, 'SIGKILL')`), and (b) resolve on the child's `exit`
  and destroy its stdio streams, never wait on `close`. Subtask 1 tests this
  directly with a parent that spawns a sleeping grandchild holding stderr.
- **A timeout test that passes without a timeout.** If the fake `ssh` fails
  fast (bad quoting, `node` not found, git probing the ssh variant with `-G`
  first), the fetch fails quickly, the warning prints, and AC5 passes having
  proved nothing. The test asserts the warning says "timed out", that the run
  took at least the configured timeout, and that the fake ssh wrote a
  "started" marker (so it ran) and is dead afterwards (so the tree was killed).
  `ssh.variant=simple` is set so git does not probe the command first.
- **Snapshot tests that are vacuously equal.** A before/after snapshot (AC6,
  AC10, AC11, AC13) proves nothing if the run did nothing at all. Each such
  test has a positive control in the same test: AC6 asserts the
  remote-tracking ref *did* move with the fetch; AC10 asserts the new ref *is*
  on origin; AC8 asserts `FETCH_HEAD` appears after `--next-id`.
- **The text check (AC16) is weak by design**, as the spec says. The
  behavioural weight is on AC10/AC11/AC13 and on a unit test of the pure
  `pushArgs` (exactly one refspec, no `+`, no flag).
- **`origin/HEAD` and short ref names.** `for-each-ref
  --format=%(refname:short) refs/remotes/origin` prints `origin` for the
  `origin/HEAD` symref (this repository has one: `git branch -a` shows
  `remotes/origin/HEAD -> origin/main`), and a local branch `intent/40` next to
  `origin/intent/40` makes short names ambiguous. The remote side reads full
  ref names (`%(refname)`), skips symrefs (`%(symref)` non-empty), and shows
  `origin/<rest>` only in messages.
- **Stale line citations.** The spec was written at `ffa0082`; `main` is now
  `4e2805e`. `git diff --name-only ffa0082 main` touches no file outside
  `intents/`, `src/`, `tests/` and `evals/`, so every kit line the spec cites
  is unchanged; each was re-read below. Line numbers rot; the implementer
  re-checks before each subtask.
- **A stale clash line forever.** Reservations never move (B6). If a draft's
  slug is renamed after it was reserved, every later `--next-id` on every
  machine prints a `§<n> clash` line for it. That is the spec's behaviour
  (B12 compares folder names); it is listed under Assumptions so the owner
  sees it.
- **Credentials at the live check.** With `GCM_INTERACTIVE=never` and
  `GIT_TERMINAL_PROMPT=0`, a fetch or push to GitHub with no cached
  credential fails (warning / exit 3) instead of prompting. That is the
  intended behaviour (B8), and only the live check (AC22) can show what the
  owner's machine does.
- **No lint cap** exists for the kit (`npm run verify` runs `node --test` and
  the product half only, `package.json:21-23`), so none can rise.

## Verified against the codebase

Re-read on `main` at `4e2805e` (still true at `49a3dfe`: see the last two items).

The queue and `--next-id`:
- `scripts/queue.mjs:2-13` — header comment: "`--next-id` prints the id
  `/intent` should take next: one more than the highest §N in OVERVIEW.md
  [...] the intents/ of main and of every local branch, and the intents/
  folders on disk here". To be updated.
- `scripts/queue.mjs:19` — `import { git, readIntentMetadataFromBranch } from './session-io.mjs';`
- `scripts/queue.mjs:22` — `const root = git(process.cwd(), 'rev-parse', '--show-toplevel');` (works from a worktree).
- `scripts/queue.mjs:26-32` — `tryGit`, null on failure.
- `scripts/queue.mjs:35-38` — `intentDirs(ref)`: `ls-tree --name-only ${ref}:intents`, filtered by `/^\d+-/`.
- `scripts/queue.mjs:40-45` — `textOf(path)`: main's copy plus the working copy.
- `scripts/queue.mjs:80-91` — `allIntentIds()`: `for-each-ref --format=%(refname:short) refs/heads` plus `MAIN`, each ref's `intentDirs`, and `readdirSync(join(root, 'intents'))` filtered by `/^[0-9]+-/`; returns ids only. No `refs/remotes`, no fetch.
- `scripts/queue.mjs:93-99` — the dispatch: `--next-id` prints `nextId({ overviewText: textOf('OVERVIEW.md'), ids: allIntentIds() })`; `--json` and the listing pass `knownIds: allIntentIds()`.
- `scripts/queue-lib.mjs:161-172` — `nextId({ overviewText = '', ids = [] })`: max of every `§(\d+)` in the text and every id, plus one.
- `scripts/queue.test.mjs:13-20` — `GIT_ENV` strips `GIT_*`; `:22-35` helpers; `:37-57` the sandbox (no remote); `:82-84` `--next-id` → `61`; `:131-150` the disk-draft and OVERVIEW cases, asserting on `stdout.trim()` only (so a new stderr line does not break them).

Shared git helpers and branch parsing:
- `scripts/session-io.mjs:12-14` — `git(cwd, ...args)`: `execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim()`; throws on non-zero.
- `scripts/session-io.mjs:42-47` — `findIntentDir(root, id)`: first `intents/` entry that `startsWith(\`${id}-\`)`, as `intents/<dir>`, or null (`2-` does not match `28-x`).
- `scripts/session-io.mjs:54-78` — `readIntentMetadataFromBranch`: `for-each-ref ... refs/heads`, filtered by `parseBranch(b)?.id`; throws "§<id> is on more than one branch" on two matches.
- `scripts/intent-check-lib.mjs:28` — `BRANCH_RE = /^(?:codex\/)?(feat|fix|refactor|adjust|exp)\/(\d+)-([a-z0-9][a-z0-9-]*)$/` (`intent/28` does not match).
- `scripts/intent-check-lib.mjs:34` — `parseBranch(name)`; `:46` — `parseMetadata(text)` (flat `key: value`, used for `id:`).
- `scripts/intent-check-lib.mjs:155-160` — `CORE_CODE` is `src/advisor/...` only; no kit script is core code.
- `scripts/check-intent.mjs:111-114` — `onSomeBranch`: `for-each-ref ... refs/heads` only (B18 holds as is).
- `scripts/update-branch.mjs:14` — "It never fetches, pushes, [...]"; `:39` its own `spawnSync('git', ...)` (B18 holds as is).

Deliver:
- `scripts/deliver.mjs:10-12` — header: "A repository with no remote named `origin` is shipped without the push [...]; with one, main must not be behind origin/main." To gain one sentence for B14/B15.
- `scripts/deliver.mjs:78` — `hasOrigin = (root) => gitOk(root, 'remote', 'get-url', 'origin')`.
- `scripts/deliver.mjs:108-122` — `locate(root, id)` returns `{ dir, metadata, branch, branchExists }`, `dir` = `intents/<id>-<slug>`.
- `scripts/deliver.mjs:132-145` — `checkStart(root, loc, dryRun)`: `:139` returns when no origin; `:140-141` "--dry-run does not fetch [...]" then `if (!dryRun) gitOk(root, 'fetch', '-q', 'origin');` (default refspec: brings `refs/heads/intent/*` into `refs/remotes/origin/`); `:142-143` the stop "origin/main has commits that main lacks, so the push would be rejected. [...]". B14's check goes between `:141` and `:142`.
- `scripts/deliver.mjs:306-314` — `push(root)`: `git push origin main` only (B16 holds as is).
- `scripts/deliver.mjs:342-349` — deletes the local `refs/heads/${loc.branch}` with `branch -d` only (B16 holds as is).
- `scripts/deliver.mjs:357-358` — `log` and `say(status, id, text)`; `:360-361` the dry run's `note fetch` line (the form B15's note takes).
- `scripts/deliver-lib.mjs:1-170` — pure, no git; exports `STEPS`, `planSteps`, `routeReasonStated`, `checkPreconditions`, `setKeys`, `markMerged`, `markLiveChecked`, `isBookkept`, `commitMessage`, `mergeMessage`.
- `scripts/deliver.test.mjs:15-22` — `GIT_ENV`; `:97-110` sandbox: `git init --bare -b main` origin, `remote add origin`, push; `:70-95` `makeIntent(id)` makes `feat/<id>-t<id>` with `intents/<id>-t<id>/`; `:279-287` `pushFromElsewhere(name)` clones origin and pushes; `:289-297` `catchUpWithOrigin()`; `:469-482` the "origin/main has commits main lacks" test; `:492-505` "does not fetch on --dry-run".

Spawn:
- `scripts/spawn-intent.mjs:29-36` — `branchExists`: `show-ref --verify refs/heads/${branch}`.
- `scripts/spawn-intent.mjs:128` — `readIntentMetadata(root, id) ?? readIntentMetadataFromBranch(root, id)`.
- `scripts/spawn-intent.mjs:134-138` — `branch = branchFor({ type, id, slug })`; reuse it if it exists, else `worktree add -b <branch> <path> <--base, default main>`.
- `scripts/spawn-intent.test.mjs:80-84` — spawning `98` gives `fix/98-probe-thing` (the harness to extend for AC19).

Test harness patterns:
- `scripts/update-branch.test.mjs:22-33` — `gitEnv()` with `GIT_CONFIG_GLOBAL: emptyConfig`, `GIT_CONFIG_NOSYSTEM: '1'`; `git` with `stdio: ['ignore', 'pipe', 'pipe']`.
- `scripts/update-branch.test.mjs:71-80` — `snapshot(target)`: main, other `refs/heads`, `ls-remote origin`, `refs/remotes`, `FETCH_HEAD` existence.
- `scripts/expect.mjs:96` — `expect(actual, message)`; matchers include `toBe`, `toEqual`, `toMatch`, `toContain`, `toBeLessThan`, `toBeGreaterThanOrEqual`.
- `scripts/kit-texts.test.mjs:30-55` — the "written down where each reader looks" checks; `:57-84` scans every non-test `scripts/*.mjs` (so the new scripts too) for old "rebase" wordings.
- `package.json:10-24` — scripts; `test:kit` is `node --test "scripts/*.test.mjs"` (new test files are picked up with no change); no `reserve-id` yet.

Policy texts:
- `REVIEW-POLICY.md:30` — the Reviewed row: "the kit's enforcement (`scripts/intent-check-lib.mjs`, `scripts/check-intent.mjs`, and the merge preconditions in `scripts/deliver-lib.mjs`, `scripts/deliver.mjs`)".
- `REVIEW-POLICY.md:169-174` — "An agent merges into `main`, pushes, deletes a branch or removes a worktree **only when the owner explicitly asks** [...] A standing instruction from an earlier session, a memory or a `CLAUDE.local.md` brief does not." B19's paragraph goes after `:174`.
- `CLAUDE.md:23` — `npm run queue # ... (--next-id, --json)`; `:26-28` the deliver / update-branch / stats command lines (the `reserve-id` line goes after `deliver`); `:82-85` the bullet "Merges into `main` are local. [...] the preconditions in `REVIEW-POLICY.md` → "Merging"." (B20).
- `AGENTS.md:27-29` — "Merge into `main`, push, delete a branch or remove a worktree only when the owner explicitly asks [...] `REVIEW-POLICY.md` → "Merging"." (B21).
- `intents/README.md:26-30` — "Take the number `npm run queue -- --next-id` prints: one more than the highest used in `OVERVIEW.md` and the `intents/` folders on `main` and on every local branch." (B22, Layout); `:100-106` "A subagent [...] never records a gate"; `:120-122` "**The decision stays yours.**" (B22's new bullet goes after it).
- `sdlc.md:12-13` — "The id is the next `§` number, which `npm run queue -- --next-id` prints."; `:19-21` step 1, "It creates `intents/<id>-<slug>/` with `intent.md` and `metadata.yml`, and proposes a type." (B23); `:91-92` "You can ask Claude to do the merge, the push or the removal, each only when you ask for it, for that change, in the current conversation." (B23).
- `.claude/skills/intent/SKILL.md:6` — `version: 0.2.0`; `:20-22` the two stamp lines naming `intent@0.2.0`; `:67-71` step 4.1 (the `--next-id` description: "`OVERVIEW.md` and the `intents/` folders on `main`, on every local branch and on disk here"); `:92-94` step 4.4 "There is no queue row to add". B7's step goes after 4.4.
- `OVERVIEW.md:9,25` — mention `--next-id`; owner-edited (`AGENTS.md:15-16`), not changed by this plan.
- `src/advisor/evals/baseline.py:14-25` — `EVAL_PATHS`: prompts, agent, models, guardrails, catalogue, data, config, evals cases/score, `evals/cases.jsonl`. This change touches none.

The state of `origin` (local, as last fetched; no fetch made):
- `refs/remotes/origin/main` = `a1ea20a` (§29's push, made while this plan was drafted); `git ls-tree origin/main:intents` holds `23-langfuse-web-worker-memory`, `24-judge-structured-output`, `25-cited-id-name-mismatch`, `26-loosen-two-headphone-cases`, `27-typed-anthropic-adapter`, `28-reserve-intent-ids` and `29-line-ending-free-eval-hashes`. Local `main` (`49a3dfe`) is 1 commit ahead.
- `main` moved from `4e2805e` to `49a3dfe` while this plan was drafted; `git diff --name-only 4e2805e 49a3dfe` is `intents/29-line-ending-free-eval-hashes/{intent.md,metadata.yml}` only, so no citation above changed.

## Subtasks

Each ends with `npm run verify` green and a commit (subjects `§28: ...`). The
implementer works in the `feat/28-reserve-intent-ids` worktree and never
pushes; every test uses local bare repositories in the OS temp dir.

1. **The bounded runner** — new `scripts/remote-io.mjs` (git and process I/O,
   no decisions):
   - `remoteTimeoutMs(env)`: `SDLC_FETCH_TIMEOUT_MS` when it is a positive
     integer, else `10_000`.
   - `runBounded(command, args, { cwd, timeoutMs, env })` → `Promise<{ code,
     timedOut, stdout, stderr }>`: `spawn` with `stdio: ['ignore', 'pipe',
     'pipe']` (stdin closed), `windowsHide: true`, `detached: true` on POSIX
     only; on timeout, kill the tree (`taskkill /PID <pid> /T /F` on Windows,
     `process.kill(-pid, 'SIGKILL')` on POSIX), destroy the stdio streams and
     resolve on `exit` without waiting for `close`. Never rejects.
   - `runGitBounded(root, args, opts)`: `runBounded('git', ...)` with env
     `GIT_TERMINAL_PROMPT=0` and `GCM_INTERACTIVE=never` added (B8).
   - `fetchOrigin(root)`: `git fetch --quiet --no-tags origin
     +refs/heads/*:refs/remotes/origin/*` (no `--prune`) through
     `runGitBounded` → `{ ok: true }` or `{ ok: false, reason }`, reason "timed
     out after <n> s" or git's last stderr line.
   - `hasOrigin(root)`: `git remote get-url origin` succeeds.
   - Tests: new `scripts/remote-io.test.mjs` (below). No new dependency:
     `taskkill` is part of Windows, everything else is Node built-ins.
2. **`--next-id` reads `origin`** (B8–B13, AC1–AC8):
   - `scripts/queue-lib.mjs`: `idOfDir(dir)`; `reservationIds(refNames)` (the
     `<n>` of each `refs/remotes/origin/intent/<n>`, digits only); `findClashes({
     local: [dir], remote: [{ ref, dir }] })` → `[{ id, here, there, ref }]`
     sorted by id, one per (local folder, remote folder) pair with equal id and
     different names, de-duplicated; `clashLine(c)` → `§<n> clash:
     intents/<n>-<a> here, intents/<n>-<b> on origin (<ref>)`; `nextId` keeps
     its signature (the caller passes local and origin ids together).
   - `scripts/queue.mjs`: `allIntentIds()` becomes a thin wrapper over a new
     `localIntentDirs()` (folder names from `MAIN`, `refs/heads` and disk, as
     today) so the listing and `--json` are unchanged (B13). `--next-id`
     (top-level `await`, in that branch only): no origin → the B11 line on
     stderr; else unless `--no-fetch`, `await fetchOrigin(root)` and the B11
     warning on failure; then read the remote refs (`for-each-ref
     --format=%(refname) %(symref) refs/remotes/origin`, symrefs skipped), each
     ref's `intentDirs`, and the reservation ids; print the clash lines on
     stderr, then `nextId(...)` alone on stdout; exit 0 in every case. Update
     the header comment.
   - Tests: `scripts/queue-lib.test.mjs` and a new `describe` in
     `scripts/queue.test.mjs` with its own sandbox (bare origin, a main clone
     and a second clone; update-branch's `gitEnv`).
3. **`npm run reserve-id -- <id>`** (B1–B6, AC9–AC16):
   - New `scripts/reserve-id-lib.mjs` (pure): `parseReserveArgs(argv)` (one
     id matching `/^[1-9]\d*$/`, else a usage error); `RESERVE_FILES =
     ['intent.md', 'metadata.yml']`; `reservationRef(id)` →
     `refs/heads/intent/<id>`; `reservationSubject(id, dir)` → `§<id>: number
     reserved (<dir>)`; `decide({ id, dir, originMainDirs, reservationDirs })`
     (B3.4–B3.6: `already-on-main` exit 0, `taken` exit 1 with the B3.5 text
     and `<where>`, `already-reserved` exit 0, or `reserve`); `checkCarried({
     parents, paths, dir })` (B3.7: no parent, every path is
     `<dir>/intent.md` or `<dir>/metadata.yml`, `metadata.yml` present) →
     null or the reason; `pushArgs(commit, id)` → `['push', 'origin',
     \`${commit}:refs/heads/intent/${id}\`]`; exit-code constants `OK 0`,
     `REFUSED 1`, `NO_REMOTE 2`, `REMOTE_FAILED 3`.
   - New `scripts/reserve-id.mjs` (I/O), the B3 order exactly: root from
     `rev-parse --show-toplevel` (main checkout or worktree); `findIntentDir`
     and `parseMetadata` (B3.1: no folder, or `id:` ≠ `<id>` → 1); `hasOrigin`
     (B3.2 → 2); `fetchOrigin` (B3.3 → 3); `decide` on `ls-tree
     origin/main:intents` and `ls-tree refs/remotes/origin/intent/<id>:intents`
     (B3.4–B3.6); build with plumbing only (B2): `git hash-object -w
     --path=<dir>/<file> <file>` for each of the files that exist (so
     `.gitattributes`/autocrlf apply as `git add` would), `git mktree` three
     times (folder, `intents`, root, input on stdin), `git commit-tree <tree>
     -m <subject>` with no `-p`; `checkCarried` on `rev-list --parents -n 1`
     and `ls-tree -r --name-only` (B3.7 → 1); `runGitBounded(root,
     pushArgs(...))` (B3.8: rejection or timeout → 3 with git's reason); on
     success `git update-ref refs/remotes/origin/intent/<id> <commit>` and the
     B3.8 line. Outcome lines on stdout for exit 0, on stderr otherwise. Never
     `--force`, `+`, `--delete`, `main` (B2).
   - `package.json`: `"reserve-id": "node scripts/reserve-id.mjs"`.
   - Tests: `scripts/reserve-id-lib.test.mjs`, new `scripts/reserve-id.test.mjs`.
4. **`/deliver` sees a clash early** (B14–B16, AC17–AC18):
   - `scripts/deliver-lib.mjs`: `otherFolder({ id, ownDir, dirs })` → the
     first `<id>-<other>` in `dirs` whose name differs from `ownDir`'s
     basename, or null; `originClashMessage(id, other)` (B14 text) and
     `reservationNote(id, other)` (B15 text).
   - `scripts/deliver.mjs` `checkStart`: between the fetch (`:141`) and the
     origin/main ancestry stop (`:142`), when `origin/main` resolves, read its
     `intents/` and throw `Stop('start', originClashMessage(...))` on a
     clash; when `refs/remotes/origin/intent/<id>` resolves, read its
     `intents/` and `say('note', 'reservation', reservationNote(...))` on a
     foreign folder. Both run on the dry run too (as last fetched). Push and
     cleanup are untouched (B16). One sentence added to the header comment.
   - Tests: `scripts/deliver-lib.test.mjs`, two `it`s in `scripts/deliver.test.mjs`.
5. **Spawn ignores reservations** (B17, AC19): no code change; one `it` in
   `scripts/spawn-intent.test.mjs`. If it fails, stop and report: B17 says
   nothing in spawn changes.
6. **The policy texts and the skill** (B19–B24, AC20–AC21):
   - `REVIEW-POLICY.md`: B19's paragraph verbatim after `:174`; in `:30`,
     the kit-enforcement list gains "the reservation push in
     `scripts/reserve-id.mjs`".
   - `CLAUDE.md`: B20's sentence at the end of the `:82-85` bullet; the
     Commands block gains B20's `reserve-id` line after `deliver` (`:26`), and
     the `queue` line (`:23`) names `--no-fetch` beside `--next-id`.
   - `AGENTS.md`: B21's sentence at the end of the `:27-29` bullet.
   - `intents/README.md`: B22's bullet after "The decision stays yours"
     (`:120-122` block) and B22's Layout sentence replacing `:28-30`'s.
   - `sdlc.md`: B23's two insertions (`:19-21` step 1, `:91-92`).
   - `.claude/skills/intent/SKILL.md`: step 4.1 names the fetch and `origin`
     (and `--no-fetch` for offline); a new step after 4.4 with B7's text
     (new intent only; run at once without asking; the four outcomes; on 1 or
     3 say why, push nothing by other means, do not retry under another
     number or renumber, ask the owner: retry later, renumber, or leave it;
     a subagent never runs it, the delegating session does after reading the
     draft); version `0.3.0` in the frontmatter (`:6`) and both stamp lines
     (`:20-22`).
   - Tests: `scripts/kit-texts.test.mjs` (AC20).
7. **Hand-over**: append to `## Progress`, set `status: in-review` in
   `metadata.yml` (the implementer's usual last commit). No gate.

**After the merge (not the implementer's; each push only on the owner's
request, as an ordinary push, I3 and owner's answer Q3):**
- §24–§28 (and §29, drafted and pushed while this plan was written): the
  owner asks, and the coordinator runs `npm run reserve-id -- <n>` for n =
  24…29 in the main checkout. By B3.4 each is expected to print "already on
  origin/main" and push nothing, because their folders are already on
  `origin/main` (verified above at `a1ea20a`). That is already a
  reservation in substance: `--next-id` counts those folders (B10) and
  `reserve-id` refuses the numbers to any other folder (B3.5). If the owner
  still wants the `intent/<n>` branches themselves, they are outside the
  script (it will not make them, by B3.4): the coordinator, on the owner's
  explicit request, builds each as B1 describes from `origin/main`'s two files
  (`git hash-object`/`mktree`/`commit-tree` as in subtask 3, no parent) and
  pushes `<commit>:refs/heads/intent/<n>`, one push per number, never forced.
  Which of the two the owner meant is the owner's call; see the report.

## Tests

All kit tests run under `npm run verify` (`npm run test:kit`), in throwaway
repositories in `os.tmpdir()` with `git init --bare` origins, `GIT_*` stripped,
`GIT_CONFIG_GLOBAL` an empty file and `GIT_CONFIG_NOSYSTEM=1`, `core.autocrlf
false`, author/committer set by env. Nothing reaches GitHub or the network.
Sandboxes are removed with `rmSync(..., { recursive: true, force: true,
maxRetries: 5 })`.

`scripts/remote-io.test.mjs` (subtask 1):
- `remoteTimeoutMs`: unset → 10000; `"1500"` → 1500; `"0"`, `"-5"`, `"abc"`
  → 10000. Fails if the default or the parse is mutated.
- Tree kill: `runBounded(process.execPath, [parent.mjs], { timeoutMs: 500 })`
  where `parent.mjs` (written to the sandbox) spawns `child.mjs` with
  `stdio: 'inherit'`, writes the child's pid to a file, and both sleep 60 s.
  Asserts: resolves within 10 s with `timedOut: true`; the pid file exists
  (the grandchild ran); after up to 2 s, `process.kill(childPid, 0)` throws
  (the grandchild is dead). Kills: dropping `/T` or the process-group kill
  (grandchild alive), resolving on `close` (takes 60 s, test timeout), not
  destroying the streams.
- Exit passthrough: a command that writes "boom" to stderr and exits 3 →
  `{ code: 3, timedOut: false }`, stderr contains "boom".

`scripts/queue-lib.test.mjs` (subtask 2):
- `reservationIds` takes `refs/remotes/origin/intent/40` → 40, ignores
  `refs/remotes/origin/intent/abc`, `refs/remotes/origin/main`,
  `refs/heads/intent/41`.
- `findClashes`: same id, different names → one clash; same id, same name →
  none; a pair seen on two refs → one line per ref, no duplicates of a pair on
  one ref.
  `clashLine` matches AC7's text exactly.
- `nextId` existing tests stay.

`scripts/queue.test.mjs`, new `describe('--next-id and origin')` (subtask 2):
- **AC1**: origin's `main` gets `intents/30-x/` from a second clone; the
  main clone never fetched it → stdout `31`. Fails if the fetch is removed or
  remote refs are not read.
- **AC2**: a parentless commit with `intents/40-r/metadata.yml` pushed to
  origin as `refs/heads/intent/40` from the second clone → `41`. A second
  case pushes `intent/45` whose tree has no `intents/` folder → `46`, so the
  ref-name path (`reservationIds`) is proved separately from the tree path.
- **AC3**: in the existing no-remote sandbox, stdout unchanged and stderr
  contains "no remote named origin: counted local intents only", status 0.
- **AC4**: after a successful fetch, `remote set-url origin
  <sandbox>/missing.git` → stderr matches `/could not fetch origin \(.+\):
  counted origin as last fetched/`, stdout still counts §30/§40/§45 from the
  remote-tracking refs, status 0. Restores the URL in `finally`.
- **AC5** (the Windows-sensitive one): a third repo whose origin is
  `ssh://example.invalid/r.git`, with `core.sshCommand` set to
  `"<process.execPath, forward slashes>" "<sandbox>/hang.mjs"` (both quoted:
  the sandbox and `Program Files` paths can hold spaces) and `ssh.variant
  simple`; `hang.mjs` writes a "started" marker and its pid, then sleeps 60 s.
  Env `SDLC_FETCH_TIMEOUT_MS=1000`. Asserts: status 0, stdout is the local
  answer, stderr matches `/could not fetch origin \(timed out/`, elapsed ≥
  1000 ms and < 10 000 ms, the marker exists, and the `hang.mjs` pid is dead
  within 2 s of return. Kills: a missing or unbounded timeout (60 s → over
  the limit), a timeout not passed to the fetch, an unkilled tree.
- **AC6**: snapshot before/after (`for-each-ref refs/heads`, `rev-parse
  HEAD`, `status --porcelain`, `ls-files --stage`, `for-each-ref
  refs/remotes`): with origin moved, `--next-id` leaves everything equal but
  `refs/remotes`, which did move (positive control); `--next-id --no-fetch`
  leaves `refs/remotes` equal too and prints the count as last fetched.
- **AC7**: disk `intents/23-a/`, origin's main `intents/23-b/` → stderr has
  "§23 clash: intents/23-a here, intents/23-b on origin (origin/main)",
  stdout `24` (in a repo whose other ids are below 23).
- **AC8**: a repo with `remote add origin` and no fetch: the listing and
  `--json` leave `FETCH_HEAD` absent and `refs/remotes` empty; then
  `--next-id` creates `FETCH_HEAD` (positive control). Fails if the listing
  path fetches.

`scripts/reserve-id-lib.test.mjs` (subtask 3):
- `parseReserveArgs`: `['28']` ok; `[]`, `['028']`, `['x']`, `['1','2']` → error.
- `decide` for each B3.4–B3.6 row, including the B3.4-before-B3.5 order and
  the `<where>` text (`origin/main` vs `origin/intent/<id>`).
- `checkCarried`: a parent → reason; a path outside `<dir>/` → reason;
  `<dir>/spec.md` → reason; only `intent.md` (no metadata) → reason; the two
  files or `metadata.yml` alone → null.
- `pushArgs('abc', 7)` equals `['push', 'origin', 'abc:refs/heads/intent/7']`
  exactly (no `+`, no flag). `reservationSubject(7, 'intents/7-x')` equals
  `§7: number reserved (intents/7-x)`.

`scripts/reserve-id.test.mjs` (subtask 3; clones A and B of one bare origin):
- **AC9 (a)**: A makes 15 commits on local `main` not pushed; writes
  `intents/23-a/{intent.md,metadata.yml}` on disk; `reserve-id 23` → exit 0;
  origin's `main` unchanged; origin has `intent/23`; A's `main` unchanged
  and `rev-list --count origin/main..main` still 15. Then B's `--next-id` →
  `24`.
- **AC9 (b)**: A's draft `intents/23-a/` never reserved; B commits
  `intents/23-b/` and pushes `main`; A's `--next-id` → `24` and the §23 clash
  line. (Uses fresh A/B clones so (a)'s reservation is not in play.)
- **AC10**: with `spec.md` also in the folder and an unrelated modified
  tracked file and an untracked file in A: `ls-remote origin` before/after
  differs by exactly `refs/heads/intent/<id>`; `rev-list --parents -n 1` has
  one field (no parent); `ls-tree -r --name-only` is exactly the two paths;
  the subject equals `reservationSubject`; `refs/heads`, `ls-files --stage`
  and `status --porcelain` unchanged; local `refs/remotes/origin/intent/<id>`
  equals the pushed commit; stdout matches `reserved §<id> on origin as
  intent/<id> \([0-9a-f]{7,}\)`. A second case with only `metadata.yml` gives
  one path.
- **AC11**: origin's main holds `intents/<id>-other/` → exit 1, "taken on
  origin by intents/<id>-other (origin/main)", `ls-remote` unchanged; and,
  separately, origin holds `intent/<id>` with `intents/<id>-other/` → exit 1,
  "(origin/intent/<id>)".
- **AC12**: the AC10 run repeated → exit 0, "already reserved", `ls-remote`
  unchanged; a folder already on origin's main under the same name → exit 0,
  "already on origin/main", unchanged.
- **AC13**: origin gets `hooks/pre-receive` (`#!/bin/sh`, echo "refused by
  test hook" to stderr, `exit 1`; `chmod 0o755` on POSIX) → exit 3, output
  contains "refused by test hook", `ls-remote` unchanged, no local
  `refs/remotes/origin/intent/<id>`. The hook is removed in `finally`.
- **AC14**: a repo with no remote → exit 2, "nothing was reserved"; origin
  set to a missing path → exit 3; in both `ls-remote`/refs unchanged.
- **AC15**: no `intents/<id>-*` → exit 1; `metadata.yml` with `id: 99` in
  `intents/98-x/` → exit 1; nothing pushed.
- **AC16**: the source of `reserve-id.mjs` and `reserve-id-lib.mjs` contains
  none of `--force`, `force-with-lease`, `--delete`, `'+`, `"+`, `` `+ ``,
  `:refs/heads/main`, `'main'` (weak by design; the behavioural tests above
  carry the weight).

`scripts/deliver-lib.test.mjs` (subtask 4): `otherFolder` returns
`61-other` for own `intents/61-t61` and dirs `['61-other', '6-x', '610-y']`,
null for `['61-t61']` and for `['610-y']` (prefix must be `<id>-`); the two
message texts equal B14's and B15's.

`scripts/deliver.test.mjs` (subtask 4):
- **AC17**: `makeIntent(61)`; a second clone pushes `intents/61-other/` to
  origin's main; the repo fetches; `--dry-run` → status 1, stdout matches
  `STOPPED\s+start\s+§61 is also intents/61-other on origin\/main` and not
  "origin/main has commits that main lacks"; the real run → the same; the
  `snapshot()` (main, origin, branch) is unchanged by both. `catchUpWithOrigin`
  in `finally`. Kills: the check placed after the ancestry stop, or skipped on
  the dry run.
- **AC18**: `makeIntent(62)`; a parentless commit with `intents/62-other/`
  pushed to origin as `intent/62`; `--dry-run` and the real run both print
  `note\s+reservation\s+origin's reservation intent/62 holds intents/62-other`
  and the real run ships (status 0, origin's main = main). Then
  `makeIntent(63)` with its own reservation (`intents/63-t63/`) at commit X:
  the ship prints no reservation note, and origin's `intent/63` is still X
  afterwards (B16).

`scripts/spawn-intent.test.mjs` (subtask 5): **AC19**: an uncommitted
intent `97` (fix type), `git update-ref refs/remotes/origin/intent/97 HEAD` and
`git branch intent/97`; spawn → status 0, worktree on `fix/97-<slug>`, no
"more than one branch" text, and both `intent/97` refs at the same commits as
before.

`scripts/kit-texts.test.mjs` (subtask 6): **AC20**: `npm run reserve-id` is
in `REVIEW-POLICY.md`, `CLAUDE.md`, `AGENTS.md`, `intents/README.md`,
`sdlc.md` and `.claude/skills/intent/SKILL.md`; `REVIEW-POLICY.md` contains
"Every other push stays on request" and "scripts/reserve-id.mjs"; the skill
contains `intent@0.3.0` and not `intent@0.2.0`.

**AC21** is a manual check by `/review` (the skill's new step against B7).
**AC22** is the live check below.

## Validation

- `npm run verify` green (kit tests, then ruff, mypy, pytest; the product
  half is untouched).
- `npm run check:intent` PASS (feature: intent, spec, plan; no `CORE_CODE`
  path touched).
- End-to-end suite: none exists (`REVIEW-POLICY.md:90-97`); the kit tests
  above are the integration tests.
- Eval run: **not owed**. No path in `EVAL_PATHS`
  (`src/advisor/evals/baseline.py:14-25`) is touched; `uv run
  advisor-analysis owes-run --base main` should list none.
- Tier: **Reviewed** (`review_tier: reviewed` in `metadata.yml`;
  `REVIEW-POLICY.md`, `.claude/skills/**` and the merge preconditions in
  `scripts/deliver*.mjs` are on the Reviewed row, `REVIEW-POLICY.md:30`). The
  owner reads the full diff.
- Live check: **owed** by rule 3 (`REVIEW-POLICY.md:85-87`): a real remote,
  its credential helper and a real network outage are runtime behaviour no
  kit test shows (spec AC22). The owner runs, in the main checkout, after the
  merge (or in the worktree before it; the script is the same):
  1. Online: `npm run queue -- --next-id`. You should see one number (with
     today's `main`, at least 30, because of §29), no credential
     prompt or window, no "could not fetch" line, and no `§<n> clash` line
     (every local folder name matches origin's). It should return in a few
     seconds.
  2. Network off (Wi-Fi off or cable out): the same command. You should see,
     within about 10 s, "could not fetch origin (…): counted origin as last
     fetched" on the terminal and still one number.
  3. Network back on. On the first real `/intent` after the merge: the
     session reports "reserved on origin as `intent/<n>`" without asking you;
     on GitHub the branch `intent/<n>` exists, shows as unrelated history (no
     parent), and its files are exactly `intents/<n>-<slug>/intent.md` and
     `metadata.yml`; `main` on GitHub did not move.

## Assumptions I made

- **One shared helper module, `scripts/remote-io.mjs`**, holds the bounded
  fetch and push (the spec leaves "where" to the plan). `deliver.mjs` keeps its
  own unbounded `git fetch -q origin` (`:141`): B14 says "after the existing
  fetch", and bounding deliver's fetch is not in the spec.
- **The tree kill (`taskkill /T` / process group) is implementation, not
  design.** I6 says the 10 s bound kills git "and so any credential helper
  waiting on it"; on Windows only a tree kill does that.
- **`reserve-id` prints its exit-0 outcomes on stdout and the others on
  stderr.** The spec gives the texts, not the stream; tests read both.
- **An id argument with a leading zero is a usage error** (exit 1), because
  B1 names the ref "with no leading zeros" and `findIntentDir` matches on the
  literal prefix.
- **When two folders on disk share the id, `reserve-id` takes the first**, as
  `findIntentDir` does for spawn; the spec does not address it, and
  `--next-id`'s clash line is local-vs-origin only.
- **`--next-id` reads the remote refs even with `--no-fetch`** (B9 "as last
  fetched"), and prints the "no remote" line whether or not `--no-fetch` was
  given.
- **The B11 lines and clash lines go to stderr before the number** on stdout;
  nothing else is printed.
- **The `README.md` "Check" block (`README.md:371-376`) is unchanged.** It lists
  `npm run queue` without flags, and the spec names no README change;
  `CLAUDE.md`'s Commands block carries the new command.
- **A stale clash line after a slug rename is accepted** (B12 compares names,
  B6 never moves a reservation); the owner sees it on every `--next-id`. A
  rename after reservation should be rare: the slug is fixed at draft.
- **The post-merge reservations for §24–§28 are not built by this change.** By
  B3.4 the script refuses to push for a number whose folder is already on
  `origin/main`, and all of §24–§29 are (as last fetched). The plan gives the owner
  both readings of Q3 (above) and does not add a flag to the script, since
  that would be a design point the spec does not make.
- **No new dependency.** Node ≥ 22 built-ins (`node:child_process`,
  `node:fs`, `node:path`, `node:os`, `node:test`) and git; `taskkill.exe`
  ships with Windows.
- **Nothing blocks this.** No open intent (§24, §25 in flight) touches
  `scripts/`, the policy texts or the intent skill.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-24: subtasks 1 to 6 (implementer)

Commits: 21bc30e (bounded runner), 6a909a6 (`--next-id` reads origin), 4239ce6
(`reserve-id`), 2891a1d (`/deliver` clash and note, spawn test), 3026f28 (policy
texts and the intent skill), and this hand-over commit. Kit tests 485 pass,
product 863 pass, `npm run check:intent` PASS.

Shipped: `scripts/remote-io.mjs` (`runBounded` kills the process tree and resolves
on `exit`, never `close`, after a timeout), `scripts/reserve-id.mjs` and
`reserve-id-lib.mjs`, `--next-id` (fetch, reservations, clash lines,
`--no-fetch`), `/deliver` stop and note, the policy texts and the intent skill
(`0.3.0`). Tests: remote-io (4), queue-lib (+5), queue.test AC3, new
queue-origin.test (AC1, 2, 4 to 8), reserve-id-lib (11), reserve-id.test (AC9 to
AC16, 11 tests), deliver-lib (+2), deliver.test AC17 and AC18, spawn AC19,
kit-texts AC20 (3). Not done here: the owner's post-merge step for §24 to §29.

Divergences from the plan:
- The tree-kill test's grandchild is spawned `detached` on Windows. Without it
  libuv's job object kills a node grandchild with its parent, so removing
  `/T` from `taskkill` did not fail the test (checked by mutation); with it,
  it does. (git's real ssh grandchild is not in that job.)
- AC1, 2, 4 to 8 live in a new `scripts/queue-origin.test.mjs` (AC3 is in
  `queue.test.mjs`) and share `scripts/test-git-sandbox.mjs`, a non-test helper
  with the update-branch environment, instead of a new `describe` in
  `queue.test.mjs` (whose sandbox has no remote).
- `reserve-id` also keeps its own `git update-ref refs/remotes/origin/intent/<id>`
  (B3.8), although git's push already updates it; a mutation removing it
  survives. Kept, since B3.8 asks for it and a different fetch refspec would
  not.
- `sdlc.md` step 1 also names `npm run reserve-id` (B23 gives no command there;
  AC20 requires the phrase in `sdlc.md`). REVIEW-POLICY.md's paragraph is
  re-wrapped so the phrase sits on one line; wording unchanged.
- `deliver.test.mjs` keeps its existing `GIT_ENV` (no empty global config) for
  the two new tests; the new reserve/queue tests use the isolated environment.
