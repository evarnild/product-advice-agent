<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §28 spec — Two machines can give two intents the same number

Accepted intent: [intent.md](intent.md)

Written against `main` at `ffa0082`.

The spec decides **what** gets built. It points at existing sources rather
than repeating them, and records the decisions that have no other home.

## Sources that apply

| Source | What it settles |
| --- | --- |
| The owner, this conversation (2026-11-24), relayed by the coordinator | The number is reserved early, by a push: "So to avoid the number clashing, we should push the intent early in the cycle", then "yes, draft it with the standing exception" (quoted in `intent.md`). The exception's scope, as the owner set it: `/intent` may push what reserves a new draft intent's number, and nothing else; every other push stays on request; "If the push would carry anything else (for example local `main` ahead of `origin/main` with other work, as happened on 2026-11-24 with 15 unpushed commits) or would be rejected, the agent doesn't push and asks." |
| `intent.md` → Constraints | "**What may be pushed:** only what reserves the number (the new draft intent's folder). Never code, never another intent's files, never a merge, a force push or a branch deletion." "`--next-id` must still work with no remote, and offline. The fetch is bounded in time, and its failure is a warning, not an error." "Tests use local bare repositories as the remote (as `scripts/deliver.test.mjs` does), never GitHub." "The kit needs Node ≥ 22 and nothing else. No new dependency." |
| `REVIEW-POLICY.md` → "Merging" | The rule the exception amends: "An agent merges into `main`, pushes, deletes a branch or removes a worktree **only when the owner explicitly asks for that action in the current conversation**, never on its own initiative. A request covers the change it names and does not carry over to the next one. [...] A standing instruction from an earlier session, a memory or a `CLAUDE.local.md` brief does not." Changing this file is "itself a **Reviewed**-tier change". |
| `CLAUDE.md`, `AGENTS.md:27-29`, `intents/README.md` → "Who edits what" | The mirrored lines: "An agent merges, pushes, deletes a branch or removes a worktree only when the owner explicitly asks for that action in the current conversation, never on its own initiative, and only after the preconditions in `REVIEW-POLICY.md` → "Merging"." (`CLAUDE.md`); "Merge into `main`, push, delete a branch or remove a worktree only when the owner explicitly asks for that action in the current conversation, and only after the preconditions in `REVIEW-POLICY.md` → "Merging"." (`AGENTS.md`). `intents/README.md` → "Who edits what": "A subagent [...] never records a gate: your request is not in its conversation." |
| `intents/README.md` → Layout | "**The id is the next `§` number.** [...] Take the number `npm run queue -- --next-id` prints: one more than the highest used in `OVERVIEW.md` and the `intents/` folders on `main` and on every local branch." |
| `docs/decisions/0003-catalogue-changes.md` | "Ids only grow. [...] An id is never reused or renumbered." (said of catalogue ids; the intent applies the same idea to `§` numbers, see Assumptions) |
| `scripts/queue.mjs:80-91` (`allIntentIds`) and `scripts/queue-lib.mjs:167` (`nextId`) | Today's `--next-id`: `for-each-ref ... refs/heads` plus `MAIN`, each ref's `intents/` folders, the folders on disk, and `OVERVIEW.md`'s `§N`. Nothing under `refs/remotes`, no fetch. |
| `scripts/deliver.mjs:139-144` (`checkStart`) | "`--dry-run` does not fetch (it changes nothing, remote-tracking refs included): origin/main is as last fetched." and the stop "origin/main has commits that main lacks, so the push would be rejected." `deliver` fetches with `git fetch -q origin` (default refspec) on a real run. |
| `scripts/session-io.mjs:54-78` (`readIntentMetadataFromBranch`), `scripts/intent-check-lib.mjs:28` (`BRANCH_RE`) | An intent's branch is found among `refs/heads` only, by `BRANCH_RE = /^(?:codex\/)?(feat\|fix\|refactor\|adjust\|exp)\/(\d+)-([a-z0-9][a-z0-9-]*)$/`. A name like `intent/28` does not match it, and remote-tracking refs are never read. |
| `scripts/spawn-intent.mjs:134-138` | Spawn creates or reuses the local branch `branchFor({type, id, slug})` (`feat/<id>-<slug>`, ...) from `--base` (default `main`). |
| `.claude/skills/intent/SKILL.md` step 4 | "**Id:** the next `§` number, from `npm run queue -- --next-id` [...]" then the files; "There is no queue row to add". It commits and pushes nothing today. |
| `scripts/deliver.test.mjs`, `scripts/update-branch.test.mjs` | The test pattern: a throwaway main checkout plus `git init --bare` origin in the OS temp dir, `GIT_*` variables stripped, and (update-branch) a before/after snapshot of `ls-remote origin` and `refs/remotes` to prove what did not change. |

## Behaviour

### The reservation

- **B1. What carries it.** A reservation of intent `<id>` is a branch
  `intent/<id>` on `origin` (ref `refs/heads/intent/<id>`, the id with no
  slug and no leading zeros). It points at one commit with **no parent**
  whose tree holds exactly `intents/<id>-<slug>/metadata.yml` and, when it
  exists, `intents/<id>-<slug>/intent.md`, as they are on disk at that
  moment, and nothing else. Its subject is `§<id>: number reserved
  (intents/<id>-<slug>)`. It never touches `main`, local or on `origin`.
- **B2. The command.** `npm run reserve-id -- <id>` (new script
  `scripts/reserve-id.mjs`, run from the main checkout or a worktree)
  makes and pushes the reservation. It builds the commit with git plumbing
  (no checkout, no change to any local branch, the index or the working
  tree) and pushes it with exactly one refspec,
  `<commit>:refs/heads/intent/<id>`: never `--force`, never a `+` refspec,
  never `main`, never a deletion.
- **B3. Order of checks.** The command:
  1. finds the folder `intents/<id>-*` on disk and reads its
     `metadata.yml`; its `id:` must equal `<id>` (else exit 1, nothing
     pushed);
  2. if there is no remote named `origin`, prints that nothing was reserved
     and exits **2**;
  3. fetches `origin` (B8's bounded fetch); if the fetch fails or times
     out, prints why and exits **3**, nothing pushed;
  4. if `origin/main` holds `intents/<id>-<slug>/` (the same folder), prints
     "already on origin/main" and exits **0**, nothing pushed;
  5. if `origin/main` holds an `intents/<id>-<other>/`, or `origin/intent/<id>`
     exists and holds a different folder name, prints "§<id> is taken on
     origin by intents/<id>-<other> (<where>); take `npm run queue --
     --next-id` and renumber the draft" and exits **1**, nothing pushed;
  6. if `origin/intent/<id>` exists and holds the same folder name, prints
     "already reserved" and exits **0**, nothing pushed (a retry is
     idempotent);
  7. builds the commit, then checks before pushing that it has no parent and
     that every path in its tree is under `intents/<id>-<slug>/` and is one
     of the two files of B1 (else exit 1, nothing pushed);
  8. pushes (bounded like the fetch). A rejection (the ref appeared on
     origin since the fetch, a hook refused it) or a timeout prints git's
     reason and exits **3**. On success it sets the local remote-tracking ref
     `refs/remotes/origin/intent/<id>` to the pushed commit and prints
     "reserved §<id> on origin as intent/<id> (<short hash>)", exit **0**.
- **B4. Local `main` ahead of `origin/main` does not stop it.** The
  reservation commit has no parent, so no commit of local `main` (or of any
  other branch) can travel with it (Interpretation I1). The command does not
  look at how far `main` is ahead.
- **B5. Atomic by id.** Because the ref name is the id alone, two machines
  reserving the same id race on one ref: the second push is a
  non-fast-forward of an existing ref and git rejects it (B3.8, exit 3), so
  at most one reservation per id ever lands.
- **B6. Kept for good.** Nothing in the kit deletes or moves a reservation:
  not `/deliver` (it keeps deleting only the local intent branch), not
  spawn, not abandonment. An abandoned draft's number stays reserved, as ids
  only grow.

### When `/intent` reserves

- **B7. At draft.** `.claude/skills/intent/SKILL.md` step 4 gains a step
  after the files are written: for a **new** intent (not when sharpening one
  that already exists), the session that ran `/intent` runs `npm run
  reserve-id -- <id>` at once, without asking, and reports the outcome:
  - exit 0: "reserved on origin as `intent/<id>`" (or "already ...");
  - exit 2: "no remote: the number is not reserved";
  - exit 1 or 3: it says why, pushes nothing by any other means (no `git
    push` by hand, no retry under another number, no renumbering on its
    own), and asks the owner what to do (retry later, renumber the draft,
    or leave it).

  A subagent that drafts an intent never runs it; the session that
  delegated the draft runs it after reading the draft (Interpretation I2).

### `--next-id`

- **B8. It fetches, bounded.** `npm run queue -- --next-id` first fetches
  from `origin` with the refspec `+refs/heads/*:refs/remotes/origin/*` (no
  `--prune`, no tags), with `GIT_TERMINAL_PROMPT=0` and `GCM_INTERACTIVE=never`
  so no credential prompt can wait, and stdin closed. The fetch is killed
  after 10 s (`SDLC_FETCH_TIMEOUT_MS` overrides it, for tests). It changes
  nothing but remote-tracking refs under `refs/remotes/origin/` (and git's
  own `FETCH_HEAD`): no local branch, index or working-tree change, no
  merge.
- **B9. `--no-fetch`** skips the fetch and reads `origin` as last fetched.
- **B10. What it counts.** The highest of: everything counted today
  (`OVERVIEW.md`, `main`, every local branch, the folders on disk) and, from
  `origin` as fetched (or as last fetched), the `intents/<n>-*` folders in
  every ref under `refs/remotes/origin/` and the `<n>` of every
  `refs/remotes/origin/intent/<n>`. It prints that plus one.
- **B11. Never fails for `origin`.** With no remote named `origin` it prints
  the local answer and, on stderr, "no remote named origin: counted local
  intents only". When the fetch fails or times out it prints, on stderr,
  "could not fetch origin (<reason>): counted origin as last fetched", then
  the answer. stdout is always the number alone; the exit code is 0 in all
  three cases.
- **B12. It reports a clash.** When an id has a folder `intents/<n>-<a>`
  locally (main, a local branch or disk) and `intents/<n>-<b>` on origin
  (a ref under `refs/remotes/origin/`, including a reservation), with
  `<a>` ≠ `<b>`, it prints on stderr one line per clash, "§<n> clash:
  intents/<n>-<a> here, intents/<n>-<b> on origin (<ref>)". The number on
  stdout is still the highest plus one, and the exit code still 0.
- **B13. The rest of `queue` is unchanged.** The listing and `--json` do not
  fetch and do not read `origin`; `knownIds` stays local.

### `/deliver`

- **B14. A clash on `origin/main` stops it early.** In `checkStart`, after
  the existing fetch (real run) or as last fetched (`--dry-run`), and
  **before** the "origin/main has commits that main lacks" check: if
  `origin/main` holds an `intents/<id>-<other>/` for the intent being shipped
  with a folder name other than its own, deliver stops at `start` with
  "§<id> is also intents/<id>-<other> on origin/main (another machine's
  intent). Renumber this intent before shipping." Nothing is changed. This
  applies to the dry run too (it stops as today's origin check does).
- **B15. A foreign reservation is a note, not a stop.** If
  `origin/intent/<id>` holds a folder name other than the intent's own, both
  the dry run and the real run add a `note` line "origin's reservation
  intent/<id> holds intents/<id>-<other>" and go on (Interpretation I5).
- **B16. Deliver never touches a reservation.** It pushes `main` only, as
  today, and never deletes or moves `intent/<id>` on origin.

### Spawn and the other scripts

- **B17. Spawn ignores reservations.** A reservation is a remote-tracking
  ref, not a local branch, and `intent/<n>` does not match `BRANCH_RE`. Spawn
  keeps creating or reusing `feat/<id>-<slug>` from `--base` (default
  `main`) and neither reuses, replaces, creates nor deletes `intent/<id>`,
  local or remote. A local branch named `intent/<id>`, should one exist, is
  not an intent branch: it never triggers "§<id> is on more than one
  branch".
- **B18. `check:intent`, `sessions`, `stats` and `update-branch` are
  unchanged.** They read `refs/heads` or `main` only, where no reservation
  lives.

### The policy texts

- **B19. `REVIEW-POLICY.md` → "Merging"**: after the first paragraph's last
  sentence ("A standing instruction from an earlier session, a memory or a
  `CLAUDE.local.md` brief does not."), a new paragraph:

  > **One standing exception: reserving a new intent's number.** Right after
  > `/intent` writes a new intent, the session that ran it runs `npm run
  > reserve-id -- <id>` without being asked. That pushes one parentless
  > commit, holding only that intent's `intent.md` and `metadata.yml`, to a
  > new branch `intent/<id>` on `origin`. It covers that push and nothing
  > else: never `main`, never code or another intent's files, never a merge,
  > a force push, a branch deletion or a push under another number, and
  > never a subagent. If the script does not reserve the number (no remote,
  > `origin` unreachable, the number taken there, the push rejected), the
  > agent pushes nothing by any other means, says why and asks the owner.
  > Every other push stays on request.

  And in the Tiers table, the Reviewed row's kit-enforcement list gains
  "the reservation push in `scripts/reserve-id.mjs`".
- **B20. `CLAUDE.md`**, "How work flows": the bullet "Merges into `main` are
  local. [...] the preconditions in `REVIEW-POLICY.md` → "Merging"." gains a
  last sentence:

  > The one standing exception, also there: `/intent` reserves a new
  > intent's number with `npm run reserve-id -- <id>` (a branch
  > `intent/<id>` on `origin` holding only that draft), and asks the owner
  > when that fails.

  The Commands block gains `npm run reserve-id -- <id>  # reserve a new
  intent's number on origin (the one push /intent makes unasked)`.
- **B21. `AGENTS.md`**, the "Merge into `main`, push, ..." bullet gains:

  > The one exception is `npm run reserve-id -- <id>` for the intent
  > `/intent` just wrote (`REVIEW-POLICY.md` → "Merging").
- **B22. `intents/README.md`**:
  - "Who edits what" gains a bullet after "The decision stays yours":

    > - **The number's reservation.** `/intent` reserves a new intent's
    >   number on `origin` with `npm run reserve-id -- <id>` as soon as it
    >   writes the draft, without asking: the one push that needs no request
    >   (`REVIEW-POLICY.md` → "Merging"). A subagent never runs it.
  - Layout's id paragraph becomes: "Take the number `npm run queue --
    --next-id` prints: one more than the highest used in `OVERVIEW.md`, the
    `intents/` folders on `main`, on every local branch and on disk, and
    those on `origin` (fetched first; reservations `intent/<n>` included).
    `/intent` then reserves it on `origin` (`npm run reserve-id`)."
- **B23. `sdlc.md`**: step 1 gains "and reserves its number on `origin` (a
  branch `intent/<id>`), the one push Claude makes without being asked";
  the sentence "You can ask Claude to do the merge, the push or the removal,
  each only when you ask for it [...]" gains "(the number reservation of
  step 1 is the one exception)".
- **B24. `.claude/skills/intent/SKILL.md`** step 4.1 names the fetch and
  `origin` in its description of `--next-id`, and the new step of B7 is
  written there; its version goes to `0.3.0` (stamp line included).

## Interpretations

- **I1. "If the push would carry anything else (for example local `main`
  ahead of `origin/main` ...)".** A push carries the objects origin
  receives and the refs it changes. The reservation commit has no parent,
  so what it carries is one commit, one tree, two blobs and one new ref,
  whatever local `main` holds. Local `main` being ahead was the owner's
  example of how a push *of `main`* would carry other work; it is not a
  reason to stop a push that cannot carry it. B3.7 checks the carried
  content directly instead. (This is the coordinator's lean, adopted.)
- **I2. "`/intent` may push".** Read as: the session in which the owner ran
  `/intent` (main checkout or a spawned session). A subagent drafting an
  intent does not push, consistent with "A subagent [...] never records a
  gate: your request is not in its conversation" and the implementer's
  "Never pushes". The delegating session reserves after reading the draft.
- **I3. "a new draft intent".** The intent `/intent` created in this run,
  whose folder is not yet on `origin/main`. A retry of the same reservation
  (same id, same folder) is the same push. Reserving an intent that already
  existed before this run (e.g. today's unpushed §24–§28) is an ordinary
  push and needs the owner's request; the script itself allows it.
- **I4. "counts intents on `origin`, after fetching".** Only `--next-id`
  fetches; it fetches every time (decision, not a flag) because the number
  is wrong precisely when origin moved since the last fetch, and `--next-id`
  runs once per new intent, not per queue listing. `--no-fetch` exists for
  offline speed and tests.
- **I5. Deliver: stop for `origin/main`, note for a reservation.** A folder
  on `origin/main` is a certain clash, and merging would push a second
  folder with the same number. A reservation with another folder name may
  be this machine's own, made before the slug was renamed; stopping on it
  would block a legitimate ship with no way out (reservations never move,
  B6). The note puts the owner in the loop.
- **I6. "The fetch is bounded in time".** 10 s, killing git (and so any
  credential helper waiting on it); prompts are disabled so a failure is
  quick rather than a wait.
- **I7. Outcome bullet 4, "the second `/intent` getting §24, or the clash
  reported".** Both are built: the replay test (AC9) shows §24 and the
  clash line.
- **I8. Orphan rather than a child of `origin/main`.** A parentless commit
  makes "carries nothing else" provable with one check (no parent) and
  works on an empty `origin`. GitHub will show the branch as unrelated
  history; nobody merges it.

## Acceptance criteria

All automated ones are kit tests run by `npm run verify` (`npm run
test:kit`), each against throwaway repositories in the OS temp dir with a
`git init --bare` origin, `GIT_*` variables stripped, never GitHub.

- **AC1** (B8, B10) `--next-id` fetches: origin's `main` holds
  `intents/30-x/` that the local clone has never fetched → prints `31`
  (test: `scripts/queue.test.mjs`).
- **AC2** (B10) origin holds `refs/heads/intent/40` (and nothing else new)
  → prints `41` (test: `scripts/queue.test.mjs`).
- **AC3** (B11) no remote → prints the local answer, the "no remote named
  origin" line on stderr, exit 0 (test: `scripts/queue.test.mjs`).
- **AC4** (B11) `origin` points at a path that does not exist → the "could
  not fetch origin" line on stderr, the answer still counts origin's
  remote-tracking refs as last fetched, exit 0 (test:
  `scripts/queue.test.mjs`).
- **AC5** (B8, I6) a fetch that hangs (remote URL `ssh://...` with
  `core.sshCommand` a `node -e` that sleeps 60 s; no network involved) and
  `SDLC_FETCH_TIMEOUT_MS=1000` → returns within 10 s with the warning and
  the local answer, exit 0 (test: `scripts/queue.test.mjs`).
- **AC6** (B8, B9) a before/after snapshot as in
  `scripts/update-branch.test.mjs` (local branches, `HEAD`, `git status
  --porcelain`, the index) is unchanged by `--next-id`; only
  `refs/remotes/origin/*` moved. With `--no-fetch`, `refs/remotes` is
  unchanged too (test: `scripts/queue.test.mjs`).
- **AC7** (B12) local disk has `intents/23-a/`, origin's main has
  `intents/23-b/` → stderr has "§23 clash: intents/23-a here,
  intents/23-b on origin (origin/main)", stdout `24` (test:
  `scripts/queue.test.mjs`).
- **AC8** (B13) the listing and `--json` make no fetch: `FETCH_HEAD` is not
  created by them in a clone that never fetched (test:
  `scripts/queue.test.mjs`).
- **AC9** (Outcome bullet 4; B1, B4, B10, B12) **the 2026-11-24 replay**:
  two clones A and B of one bare origin.
  - (a) A's local `main` is 15 commits ahead of `origin/main`; A drafts
    `intents/23-a/` on disk and runs `reserve-id 23` → exit 0; origin's
    `main` is unchanged, origin has `intent/23`, and A's `main` is unchanged
    and still 15 ahead. B then runs `--next-id` → `24`.
  - (b) A's draft `intents/23-a/` is never reserved (offline at draft); B
    pushes `intents/23-b/` to origin's `main`; A's `--next-id` prints `24`
    and the §23 clash line.

  (test: new `scripts/reserve-id.test.mjs`)
- **AC10** (B1, B2, B3.7) after a successful reservation, `git ls-remote
  origin` differs from before only by the new `refs/heads/intent/<id>`; that
  commit has no parent; `git ls-tree -r --name-only` lists exactly
  `intents/<id>-<slug>/intent.md` and `.../metadata.yml`, even when the
  folder on disk also holds a `spec.md` and the working tree has other
  uncommitted changes; local branches, index and working tree are unchanged
  (test: `scripts/reserve-id.test.mjs`).
- **AC11** (B3.5) origin's `main` holds `intents/<id>-other/`, and,
  separately, origin holds `intent/<id>` with `intents/<id>-other/` → exit
  1, the "taken on origin" message, `ls-remote origin` unchanged (test:
  `scripts/reserve-id.test.mjs`).
- **AC12** (B3.4, B3.6) a second run for the same folder, and a run for a
  folder already on origin's `main` → exit 0, "already ...", `ls-remote`
  unchanged (test: `scripts/reserve-id.test.mjs`).
- **AC13** (B3.8, B5) origin's bare repo has a `pre-receive` hook that
  exits 1 → exit 3 with git's reason, `ls-remote` unchanged, no local
  remote-tracking ref `origin/intent/<id>` written (test:
  `scripts/reserve-id.test.mjs`).
- **AC14** (B3.2, B3.3) no remote → exit 2; unreachable origin → exit 3;
  nothing written in either (test: `scripts/reserve-id.test.mjs`).
- **AC15** (B3.1) no folder for the id, and a `metadata.yml` whose `id:`
  differs → exit 1, nothing pushed (test: `scripts/reserve-id.test.mjs`).
- **AC16** (B2) the script's source contains no `--force`, no
  `force-with-lease`, no `+` refspec, no `--delete` and no `main` in a push
  argument (test: `scripts/reserve-id.test.mjs`, a text check; weak by
  design, the behavioural tests above carry the weight).
- **AC17** (B14) origin's `main` holds `intents/<id>-other/` (pushed from a
  second clone, fetched) → `deliver -- <id> --dry-run` and `deliver -- <id>`
  stop at `start` with the new message and not with "origin/main has
  commits that main lacks"; main, the branch and origin are unchanged
  (test: `scripts/deliver.test.mjs`).
- **AC18** (B15, B16) origin holds `intent/<id>` with another folder name →
  the dry run and the real run print the note and ship; after a ship whose
  own reservation exists, `intent/<id>` on origin still points at the same
  commit (test: `scripts/deliver.test.mjs`).
- **AC19** (B17) with `refs/remotes/origin/intent/<id>` present, and with a
  local branch `intent/<id>` present, `npm run spawn -- <id>` creates the
  worktree on `feat/<id>-<slug>` from `main` as today, and neither
  `intent/<id>` ref changed (test: `scripts/spawn-intent.test.mjs`).
- **AC20** (B19-B23) the exception's key phrase `npm run reserve-id` is in
  `REVIEW-POLICY.md`, `CLAUDE.md`, `AGENTS.md`, `intents/README.md`,
  `sdlc.md` and `.claude/skills/intent/SKILL.md`, and `REVIEW-POLICY.md`
  contains "Every other push stays on request" (test:
  `scripts/kit-texts.test.mjs`).
- **AC21** (B7, B24) the skill's step 4 runs the script for a new intent
  only, names the four outcomes and says the agent asks on 1 or 3 (manual
  check: `/review` reads `.claude/skills/intent/SKILL.md` against B7).
- **AC22** (live, `REVIEW-POLICY.md` → "Live checks" rule 3: a real remote
  and its credential helper are runtime behaviour no test shows) the owner
  runs, in the main checkout: `npm run queue -- --next-id` online (prints a
  number, no prompt) and with the network off (the warning within about
  10 s, still a number); then, on the first real `/intent` after the merge,
  sees `intent/<n>` on GitHub holding only that draft.

## Non-functional

- **Boundaries:** git and file I/O in `scripts/reserve-id.mjs`,
  `scripts/queue.mjs` and `scripts/deliver.mjs`; the decisions that can be
  tested without a repository (which ids are counted, what is a clash,
  which outcome and exit code a reserve-id state gives, which tree paths
  are allowed) in the `-lib.mjs` files (`queue-lib.mjs`, a new
  `reserve-id-lib.mjs` or `deliver-lib.mjs`), with unit tests. Node ≥ 22
  built-ins only; no npm dependency. The bounded fetch and push are one
  shared helper (where is the plan's call).
- **Data:** the reservation puts the draft's `intent.md` and `metadata.yml`
  on `origin` earlier than today (at draft, not at `/deliver`). The same
  text reaches `origin` at `/deliver` anyway; an abandoned draft's text now
  stays on `origin` too. Intent drafts must hold no secret or personal data,
  as every committed file already must.
- **Model use:** none.
- **Autonomy:** one new unasked action, the reservation push of B7, bounded
  by B2-B3 and B19. Everything else stays as it is: the owner asks for every
  other push, merge, deletion and gate. `/auto` drafts no intent and gains
  nothing.

## Out of scope

- Renumbering existing intents, rewriting the "§23:" commit subjects in
  §27's history (from the intent).
- Pulling or merging `origin/main` automatically (from the intent).
- Reserving the intents that exist before this lands (§24-§28 are on
  local `main`, not on `origin`); the owner can ask for `npm run reserve-id
  -- <n>` for each, as an ordinary requested push.
- Deleting or pruning reservation branches, and showing reserved-only
  intents in the queue listing.
- Renumbering a draft automatically when its number is taken (the agent
  asks).

## Assumptions I made

- **Design question 1 (what carries it): (b), a per-id branch
  `intent/<id>`**, not the coordinator's `intent/<id>-<slug>`: with the slug
  in the name, two machines picking the same id with different slugs would
  both push successfully; with the id alone, git's refusal of a
  non-fast-forward makes the second one fail (B5). A branch (not a tag or a
  custom `refs/` namespace) because a default `git fetch origin`, which
  `deliver` already runs, brings it in, and GitHub surely accepts branches.
- **Design question 2 (when): at draft**, the owner's "early in the cycle";
  an abandoned draft keeps its number either way.
- **Design question 3 (fetch every time): yes, for `--next-id` only**, with
  `--no-fetch` (I4). The listing never fetches.
- **Design question 4 (`/deliver`): yes**, a stop for a clash on
  `origin/main` and a note for a foreign reservation, both in the dry run
  and the real run (B14, B15, I5).
- **Design question 5 (spawn): spawn ignores the reservation**; nothing in
  spawn changes, and a test pins that (B17, AC19).
- **A subagent never runs `reserve-id`** (I2).
- **Ids never reused.** `intents/README.md` does not say it in those
  words; the rule is taken from `docs/decisions/0003-catalogue-changes.md`
  ("An id is never reused or renumbered") as the intent does, and B6 keeps
  every reservation.
- **The reservation snapshots the draft** and is never updated: it is a
  claim on a number, not a copy of the intent. Later edits live on `main`
  or the intent branch as today.
- **10 s** is the fetch and push bound (I6).
- **Exit codes 0/1/2/3** for `reserve-id` follow `update-branch`'s habit of
  distinct codes per outcome.
- **The script name `reserve-id`** is fixed here because the policy text
  quotes it.
- **`OVERVIEW.md`'s `§`-numbers stay counted** (from the intent).
- **Nothing blocks this**: no open intent changes `scripts/queue*.mjs`,
  `scripts/deliver*.mjs`, `scripts/spawn-intent.mjs` or the intent skill.
