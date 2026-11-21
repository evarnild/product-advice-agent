<!-- generated-by: product-advice-agent/spec@0.2.0 -->
# §20 spec — Bring a branch that is behind main up to date before each review round

Accepted intent: [intent.md](intent.md)

Written against `main` at `d6fb88c`.

The intent asked about a rebase. The owner chose a **merge of `main` into the
branch** instead (decision Q4 below), so this spec says "bring up to date" and
"merge `main` in" throughout; "rebase" survives only where something forbids it.

## Owner's decisions (2026-11-21)

- **Q4, "Merge main in":** a behind branch is brought up to date with
  `git merge main` in its worktree, never a rebase, so no commit is rewritten
  and earlier rounds' `reviewed-commit` hashes stay valid. The reviewer reads
  the change as `git diff main...HEAD` (three-dot), so `main`'s changes stay
  out of the reviewed diff.
- **Q1, "Script, implementer on conflict":** a kit script the coordinator
  runs against an intent's worktree: if the branch is behind local `main`,
  merge `main` (`--no-edit`); on a conflict, abort the merge cleanly and
  report the conflicted files with a distinct exit status; after a clean
  merge, run `npm run verify` in the worktree and report. A conflict goes to
  the implementer when its resolution is mechanical (keep both sides'
  behaviour, tests decide); a conflict needing a behaviour choice, or a red
  verify that can't be traced, is a stop for the owner.
- **Q2, "Update like /auto":** a manual `/review` also brings a behind
  branch up to date the same way before its passes.
- **Q3, "Keep today's rule":** `/ship` still merges and runs `verify` on
  `main`; it does not refuse a branch behind `main`. The report records the
  `main` commit the round was checked against.

## Sources that apply

| Source | What it settles |
| --- | --- |
| `REVIEW-POLICY.md:186-189` "Merging" | "Its `reviewed-commit` is an ancestor of the branch (`git merge-base --is-ancestor`). A rebase since the review means a new round." and "Nothing but that intent's `review.md` or `metadata.yml` differs between `reviewed-commit` and the branch (`git diff --name-only`)." |
| `scripts/ship-lib.mjs:94-103` `checkPreconditions` | the ancestor check (`'reviewed-commit'`, message "rebased since the review: a new round is needed") and the stray-files check (`'unreviewed-changes'`). |
| `scripts/ship.mjs:190-192` | `changedFiles` is `git diff --name-only <rc> <branch>`: a two-dot **tree** comparison, so it lists every file `main` changed once `main` is merged in after `rc`. |
| `REVIEW-POLICY.md:250-260` "The report" | the header lines (`verdict`, `tier`, `reviewed-commit`, `round`, `sampled`, `run`, `live-check`). |
| `scripts/intent-check-lib.mjs:298-306` `parseReviewHeader` | reads every `key: value` line before the first `## ` or `# Round`; unknown keys are kept and ignored by its callers: `check-intent.mjs:68` (uses `live-check`), `ship.mjs:182` (uses `verdict`, `reviewed-commit`), `scan-lib.mjs:151` (uses `run`). A new `main:` line breaks none of them. |
| `.claude/agents/product-advice-agent-reviewer.md:60` | "Run `git diff main...<branch>`": the Claude reviewer already reads the three-dot diff. `.claude/skills/review/SKILL.md` and `.codex/agents/product-advice-agent-reviewer.toml:12` ("re-derive the behaviour from the diff") name no diff command. |
| `scripts/check-intent.mjs:74-77`, `src/advisor/evals/analysis.py:370` | `check:intent` diffs against `git merge-base <base> <branch>` and `owes-run` against `<base>...HEAD`: after `main` is merged in, both still see only the branch's own change. |
| `.claude/skills/review/SKILL.md:30-31` | "**Read-only:** no commits, resets, stashes, merges, or edits to code. The only file you write is `review.md`." |
| `.claude/skills/auto/SKILL.md:170-181` (step 5 items 1-2), `:89-103` (resume table), `:290-295` (other stops), `:345-348` (safety rule "never merge, push, rebase or delete a branch or worktree") | where the update goes and what changes. |
| `.claude/agents/product-advice-agent-implementer.md:33-36`, `.codex/agents/product-advice-agent-implementer.toml:15-17` | "Do NOT push, merge, touch `main` …" / "Do not push, merge, or switch main." |
| `scripts/sessions.mjs:62-65` | prints "Behind main (rebase before review): §n (-N)". |
| `.claude/skills/sessions/SKILL.md:35-37, 48-49` | the drafted notice "main moved (§<merged id> merged). Rebase `<branch>` on main and re-run `npm run verify`." |
| `scripts/session-lib.mjs:335` (the `CLAUDE.local.md` brief) | "If you are told \`main\` moved, rebase this branch on it and re-run \`npm run verify\`." |
| `CLAUDE.md:121, 142` | "sends "main moved, rebase" notices"; "more sessions mostly add rebases". |
| `.claude/skills/spawn/SKILL.md:34-36` (§18) | `--base <ref>` "only when the owner asks for a stacked branch". |
| `REVIEW-POLICY.md:28-30` path table | Reviewed: this file, `scripts/ship-lib.mjs`, `.claude/agents/**`, `.codex/agents/**`, `.claude/skills/**`. |

## Behaviour

**The script**

- **B1. Command.** `npm run update-branch -- <id>` (`scripts/update-branch.mjs`,
  pure logic in `scripts/update-branch-lib.mjs`, Node ≥ 22, no dependency).
  It finds intent §id's worktree from `git worktree list --porcelain` and
  works only there (`git -C <worktree>`). It can be run from any checkout of
  the repository; the coordinator runs it from the main checkout.
- **B2. Refusals, before any change.** It refuses, exit status 1, worktree
  untouched, naming the reason, when: no worktree has §id's branch checked
  out; the target worktree is the main checkout or its branch is `main`;
  `HEAD` is detached; a merge, rebase or cherry-pick is in progress there;
  tracked files are modified or staged (`git status --porcelain
  --untracked-files=no` not empty). A merge that git itself refuses to
  start (for example an untracked file in the way) is reported the same
  way, with git's message, worktree as before.
- **B3. Behind means** `git rev-list --count <branch>..main` > 0, against
  local `main`. Never a fetch, never `origin/main`.
- **B4. Up to date.** Not behind: it prints that the branch contains `main`
  at `<short hash>`, changes nothing, runs no `verify`, exit 0.
- **B5. Clean merge.** Behind by N: it prints "behind main by N", runs
  `git merge --no-edit main` in the worktree (a merge commit, or a
  fast-forward when the branch has no commits of its own), then runs
  `npm run verify` there. Green: prints the new `HEAD` and `main` short
  hashes and "verify green", exit 0.
- **B6. Red verify after a clean merge.** Prints the tail of the output and
  "verify red after merging main", **keeps the merge commit** (nothing is
  undone), exit 3.
- **B7. Conflict.** On a merge conflict it lists the conflicted files
  (`git diff --name-only --diff-filter=U`), then `git merge --abort`, and
  checks the worktree is back at the same `HEAD` with nothing staged or
  modified. Exit 2. If the abort leaves anything behind, exit 1 with what is
  left, and changes nothing more.
- **B8. Never** rebases, pushes, fetches, resets, stashes, commits anything
  but git's own merge commit, or touches `main` or another worktree.

**`/auto`** (`.claude/skills/auto/SKILL.md`)

- **B9. When.** In step 5, for each new round `n`, after the cap (item 1) and
  before the `auto_round: <n>` commit (item 2), the coordinator runs
  `npm run update-branch -- <id>`. So the round's reviewed commit contains
  the merge. Not before the build, not at the ship stop (Q3).
- **B10. Outcomes.** Exit 0: go on to item 2. Exit 2 (conflict): the
  coordinator reads the conflicted files' two sides (read-only:
  `git diff <merge-base> main -- <files>` and `git diff main...<branch> -- <files>`)
  and decides the kind as for a finding (step 7). **Mechanical** (keeping
  both sides' behaviour resolves it, and the tests decide): resume or launch
  the implementer to merge and resolve (B14), wait, then run the script again
  (it must now exit 0, else this table again). **Needs a behaviour choice,
  or in doubt, or the implementer aborted the merge and reported a choice:**
  stop with `auto_stopped: main merge conflict`. Exit 3 (red verify): if the
  failure traces mechanically to `main`'s change meeting the branch's (the
  test or the spec says what is right), resume the implementer with the
  failure, wait, and go on to item 2 (the round's re-check runs `verify`);
  otherwise stop with `auto_stopped: red verify after merging main`. Exit 1:
  stop with `auto_stopped: branch update refused`.
- **B11. Not a round.** The update, its implementer resolution and its stops
  consume no round: a stop here writes `auto_round` unchanged (the last
  finished round, left empty before round 1; never `0`, which
  `check:intent` rejects at `intent-check-lib.mjs:263-266`).
- **B12. Resume rows** added to step 1's table:
  `main merge conflict` → give the implementer the owner's answer (resolve
  the merge as decided), wait, then step 5 at item 1 for round
  `auto_round` + 1, which runs the update again; **no round consumed**.
  `red verify after merging main`, `branch update refused` → once the owner
  says the cause is cleared, step 5 at item 1 for round `auto_round` + 1;
  **no round consumed**. The three reasons are listed in step 7's "Other
  stops".
- **B13. Safety rule** (step 10) becomes: never run `npm run ship` …, never
  merge into `main`, push, rebase, or delete a branch or worktree; the
  implementer merges `main` into its own branch only when the coordinator's
  brief asks for it (B14), and the coordinator brings a branch up to date
  only through `npm run update-branch`.

**The implementers**

- **B14.** Both implementer definitions
  (`.claude/agents/product-advice-agent-implementer.md`,
  `.codex/agents/product-advice-agent-implementer.toml`) say: when the
  brief asks you to bring the branch up to date after a conflict, run
  `git merge main` in your worktree (never rebase), resolve each conflict
  keeping both sides' behaviour, run `npm run verify`, and commit the
  merge; if any resolution needs a choice between behaviours, `git merge
  --abort`, leave the worktree as it was, and report the files and the
  choice. Otherwise the existing "do not merge" rule stands.

**`/review`** (`.claude/skills/review/SKILL.md`)

- **B15. Before the passes.** Step 0 gains: if the branch is behind `main`
  (B3), the coordinator runs `npm run update-branch -- <id>` before any
  pass. This is the one write `/review` makes besides `review.md`, made by
  the script, before the review starts; the read-only rule covers
  everything after it. Under `/auto` it is already done by B9 and the
  script exits 0 at B4.
- **B16. Manual outcomes.** Exit 0: review. Exit 2, 3 or 1: no passes, no
  `review.md`; tell the owner the branch is behind `main` by N, the script's
  report (conflicted files, the red output, or the refusal), and what to do
  next: "send the conflict to the implementer session (or resolve it), then
  `/review` again". A reviewer agent stays read-only and never runs the
  script.
- **B17. The reviewed diff.** The review skill (step 0) and the Codex
  reviewer name the change as `git diff main...<branch>` (three-dot), as
  the Claude reviewer already does (`product-advice-agent-reviewer.md:60`);
  mutations are enumerated from that diff.

**The report and the merge**

- **B18. `main:` header line.** `REVIEW-POLICY.md` → "The report" adds
  `main: <hash>` after `reviewed-commit:`: the short hash of local `main`
  when the round's passes started (after the update). On a branch brought
  up to date it is an ancestor of `reviewed-commit`. No script requires or
  validates it; `parseReviewHeader` keeps it as an unused key.
- **B19. A merge of `main` after the final review forces a new round, by the
  existing check.** It leaves `reviewed-commit` an ancestor, but `main`'s
  changed files then differ between `reviewed-commit` and the branch, so
  `checkPreconditions` refuses with `unreviewed-changes`. No new check. The
  two messages say why: `reviewed-commit` → "… is not an ancestor of the
  branch (rewritten since the review, by a rebase or an amend: a new round
  is needed)"; `unreviewed-changes` → the file list plus "(a merge of main
  since the review counts: a new round is needed)".
- **B20. Policy wording.** `REVIEW-POLICY.md:187` "A rebase since the review
  means a new round." becomes: a rewrite of the branch (rebase, amend) fails
  the ancestor check and a merge of `main` fails the next one; either means a
  new round. "Merging" adds: a branch behind `main` is not refused (Q3);
  before each review round it is brought up to date with
  `npm run update-branch` (never a rebase).

**Sessions and docs**

- **B21.** `npm run sessions` prints "Behind main (update before review):
  §n (-N)" (was "rebase before review"). `check:intent` is unchanged.
- **B22.** The `/sessions` notice (`SKILL.md:35-37, 48-49`) becomes: *"main
  moved (§<merged id> merged). Bring `<branch>` up to date: `npm run
  update-branch -- <id>` (merges main, never rebases), then resolve any
  conflict and re-run `npm run verify`."* It stays for sessions not under
  `/auto`. Step 2's "Each merge makes the others rebase" says "update".
  The `CLAUDE.local.md` brief (`session-lib.mjs:335`) says the same.
- **B23.** `CLAUDE.md` lists `npm run update-branch -- <id>` under Commands
  and says "main moved, update" (`:121`) and "add updates" (`:142`).
  `README.md` lists no kit command (`npm run ship`, `sessions`) at `d6fb88c`,
  so it gains none.

## Interpretations

- **I1. "Abort the merge cleanly (worktree as before)"** is read as: same
  `HEAD`, nothing staged or modified in tracked files. Untracked files were
  never touched (B2 refuses if git would). (B7)
- **I2. "A red verify that can't be traced"** (Q1) is read with `/auto`'s
  existing test (`SKILL.md:291-292`, "a red `verify` … you cannot trace to a
  finding the implementer is fixing"): traceable here means the failure
  follows mechanically from `main`'s change meeting the branch's, and a test
  or the spec says which side is right. (B10)
- **I3. "Not a review round"** (Q5) is read as: it neither increments
  `auto_round` nor counts against the cap, even when it needs the
  implementer. (B11)
- **I4. "The `main` commit the round was checked against"** is `main` at the
  start of the passes, not at the end: `main` may move during a review, and
  the round is a check of the branch as updated. (B18)
- **I5. "Refuses to run on the main checkout / `main` branch"** is read as the
  **target** worktree, not where it is invoked: the coordinator runs it from
  the main checkout. (B1, B2)

## Acceptance criteria

- **AC1** (B3-B7) the pure decisions — behind or not, the outcome and exit
  status for up-to-date / merged-green / merged-red / conflict / refusal, and
  the printed report — are unit-tested. *Proof: `scripts/update-branch-lib.test.mjs`.*
- **AC2** (B1, B2, B4-B8) end to end against throwaway git repositories (a
  main checkout and a worktree beside it, as `ship.test.mjs` does; `verify`
  replaced by an environment-variable command as `SDLC_SHIP_VERIFY` does):
  up to date → exit 0, no commit; behind with no conflict → a merge commit
  whose parents are the old tip and `main`, green → 0, red → 3 with the merge
  kept; conflict → 2, conflicted files listed, `HEAD` unchanged, `git status`
  clean, no `MERGE_HEAD`; each refusal of B2 → 1 with nothing changed; the
  target `main` / main checkout refused; `main`, the old tip's commits and
  every other branch unchanged in every case; no remote touched. *Proof:
  `scripts/update-branch.test.mjs`, run by `npm run test:kit`.*
- **AC3** (B19) a branch reviewed at `rc`, then `main` merged in: `ship`
  refuses with `unreviewed-changes` and the new message, merges nothing;
  a rebased branch still refuses with `reviewed-commit` and its new message.
  *Proof: `scripts/ship-lib.test.mjs` (messages) and `scripts/ship.test.mjs`
  (the merge-of-main case, end to end).*
- **AC4** (B18) a review whose header has `main: <hash>` parses as before:
  `check:intent`, `ship` and `sdlc:scan` read the same `verdict`,
  `reviewed-commit`, `live-check` and `run`. *Proof: a case in
  `scripts/intent-check-lib.test.mjs` (`parseReviewHeader`) and
  `scripts/ship-lib.test.mjs` or `scan-lib.test.mjs`.*
- **AC5** (B21, B22) the sessions line and the brief say "update", not
  "rebase". *Proof: `scripts/session-lib.test.mjs` for the brief; the
  sessions line by a test if the plan moves it into `session-lib.mjs`,
  otherwise by a read of `scripts/sessions.mjs`.*
- **AC6** (B9-B13, B15-B17, B20, B22, B23) the skill, agent and policy texts
  say what these B's say, with no remaining instruction to rebase a branch
  (`grep -rn -i rebase` over `.claude/`, `.codex/`, `REVIEW-POLICY.md`,
  `CLAUDE.md`, `scripts/*.mjs` shows only prohibitions and the ship
  message). *Proof: the review's pass 1 and 3 read; the grep in "Verified
  myself".*
- **AC7** (B14) both implementer definitions carry the merge-on-request rule
  and its abort path. *Proof: read.*
- **AC8** (all) `npm run verify` green; `package.json` has the
  `update-branch` script and no new dependency. *Proof: verify; read.*
- **AC9** (B9, B10, B15, B16) **live check, owed under rule 3** (the skills'
  flow in a real coordinator session is runtime behaviour that only a live
  run shows). Proposed steps: with a spawned worktree behind `main`, run
  `npm run update-branch -- <id>` from the main checkout and see the merge
  and the verify result; then run `/review <branch>` on a branch behind
  `main` and see it update first and write `main:` in the header. A
  conflict case may be shown in a scratch intent. *Proof: the owner's run,
  `live_checked:`.*

## Non-functional

- **Boundaries:** kit only. Pure logic in `scripts/update-branch-lib.mjs`
  (no `child_process`, no `fs`), git and process I/O in
  `scripts/update-branch.mjs`, reusing `session-io.mjs` / `session-lib.mjs`
  helpers (`parseWorktreeList`, `findIntentDir`) where they fit. No product
  code (`src/`) changes, so no eval run is owed.
- **Data:** none. The script prints git facts and `verify`'s output tail;
  nothing is written outside the target worktree's git state.
- **Model use:** none.
- **Autonomy:** the coordinator runs the script without asking, under `/auto`
  (B9) and `/review` (B15). The implementer merges `main` into its own branch
  only on the coordinator's brief (B14). Choosing a conflict's behaviour is
  never an agent's: it is a stop. The coordinator runs the script only while
  no implementer is running in the worktree (`auto` step 1: "write only
  while no implementer is running").

## Out of scope

- Making `/ship` refuse a branch behind `main` (Q3: today's rule stays).
- Any change to `check:intent` (Q6).
- Rebasing, pushing, fetching, or comparing with `origin/main`.
- Stacked branches (`spawn --base`, §18) before their base merges: their
  `main...HEAD` diff still includes the base branch's commits, as today.
  Once the base merges, the update merges `main` like any other branch.
- Updating branches at the ship stop or on every `main` move; only before a
  review round.
- Renaming the intent folder, slug or `metadata.yml` title ("Rebase …").

## Assumptions I made

- **Q5 (not asked; the intent presumed it):** bringing the branch up to date
  is not a review round and does not count against `/auto`'s three rounds
  (B11, I3).
- **Q6:** `npm run sessions` already warns ("Behind main …",
  `sessions.mjs:62-65`); only its wording changes (B21). `check:intent` is
  unchanged.
- **No `verify` when nothing was merged** (B4): the review's own step 1 and
  `/auto`'s re-check run `verify` anyway.
- **A red `verify` keeps the merge commit** (B6), as `ship` keeps a merge
  after a red `verify` on `main` ("undoing a merge is the owner's call"); the
  implementer fixes on top of it.
- **Exit statuses** 0 / 1 / 2 / 3 as in B2-B7. 2 and 3 are the "distinct"
  statuses Q1 asked for; 1 is every refusal or unexpected git failure with
  nothing changed.
- **Dirty or mid-operation worktrees are refused** (B2): a merge on top of
  uncommitted work would mix it into the merge commit.
- **Default merge message** (`--no-edit`, "Merge branch 'main' into …"), no
  trailers. It has no `§<id>:` prefix, so `npm run stats` (`stats-lib.mjs:33`,
  `intentOf`) treats it as no milestone, and `git log --branches` dedupes
  `main`'s commits by hash.
- **The stop happens before the `auto_round` commit** (B9, B11), so a stop at
  the update leaves `auto_round` as the last finished round and a resume
  re-enters step 5 at item 1 without consuming a round.
- **A manual `/review` stops on every non-zero exit** (B16) rather than
  reviewing a red or behind branch; the intent's Outcome allows "saying it is
  behind and by how much", which B16 does.
- **"Behind" and the `main:` line use local `main`** (the intent's
  assumption; merges here are local).
