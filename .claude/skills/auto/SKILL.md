---
name: auto
description: Carry one accepted product-advice-agent intent from acceptance to a merge-ready branch without a prompt between the steps, stopping only for the owner's questions and decisions, the feature's spec acceptance, the live check and the ship. Use only when the owner types /auto <id> in the coordinator session. Invoke as /auto <id>.
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/auto@0.1.0
---

# /auto — one intent, from acceptance to "ready: /ship"

You are the **coordinator** (the main checkout, on `main`). This skill runs
the existing steps in order: `/spec`, the plan, `/spawn`, the implementer,
`/review` and rework. Read `intents/README.md` → "Who edits what" and
`REVIEW-POLICY.md` before you start, every time: they change.

## What the owner's message authorises

`/auto <id>` is the owner's request, in this conversation and for intent
§id only, to record **that intent's `plan_approved`**. That is
the whole authorisation. It is not a standing instruction, it does not carry
to another id, and it covers none of these, which stay the owner's:

- `intent_accepted` (the run starts from an accepted intent);
- `spec_accepted` (a feature stops once for it, step 2);
- `live_checked` (the owner runs the check, step 7);
- `/ship` and every merge, push, branch deletion and worktree removal.

You never run `/ship` or `npm run ship` except `npm run ship -- <id>
--dry-run` at step 8. A subagent never records a gate: you write the one gate
this skill allows, in this conversation.

## 0. Check the preconditions, and stop with the reason if one fails

- You are the coordinator: `git rev-parse --show-toplevel` is the first
  entry of `git worktree list`, and `git branch --show-current` is `main`.
- The owner gave an id. With no id, stop and say so; do not guess one from
  `npm run queue`.
- `intents/<id>-*/metadata.yml` exists (on `main`, or on the intent's
  branch in its worktree once spawned: read the worktree's copy then) and
  `intent_accepted` is recorded, as a bare date or `<date> by-agent`. If
  not, stop: a run starts from an accepted intent (`/intent` drafts one).
- `npm run sessions` shows fewer than three other open intent sessions or
  runs (`CLAUDE.md`, "about three"). If a fourth would open, stop.
- The worktree, once it exists, is not held by a session you didn't start
  (`npm run sessions`: its row is not `working`, `idle` or `needs you`). If it
  is, stop.

## 1. Start or resume

1. Read `metadata.yml`: `auto_authorized`, `auto_round`, `auto_stopped`.
2. Write `auto_authorized: <today> by-agent`, with the owner's words in a
   comment, the way a gate is recorded:
   `auto_authorized: 2026-11-03 by-agent    # owner: "/auto 5"`.
   This is written on every `/auto <id>`, including a second one that
   resumes a stopped run; the owner's new message is the new request.
3. Keep `auto_round`: a resumed run continues from the recorded round and
   does not get a fresh budget. Keep `auto_stopped` too, until the
   resumed step has moved on: clear it (empty) in the first commit that step
   makes, such as the round-start write of step 5, the record of a passed
   live check, or the ship stop of step 8. A session that closes right
   after the resume then still finds the reason.
4. Commit it (on `main` before the branch exists, on the branch after), with
   a subject `§<id>: auto run started` or `§<id>: auto run resumed`.

Where the metadata lives: write only while no implementer is running in the
worktree. All of this skill's writes happen at a stop, a start or a round
boundary, never while the implementer works.

Then resume by the recorded `auto_stopped`, not by "the first step not done".
The reason text is the one the stop wrote (step 9); an
empty `auto_stopped` means the session closed mid-run, and falls back to
**the first step whose work is not done**: spec, plan, worktree, build, then
the review loop. In the review loop, a close mid-rework is told by round
`auto_round`'s `review.md` and the implementer's `## Progress` entry in
`plan.md`, whether or not the implementer has committed yet. While that
`review.md` says `rework` (step 5 resumes the implementer without a stop, so
`auto_stopped` is empty) and the Progress entry for that rework is missing,
the rework is unfinished: relaunch the implementer with round `auto_round`'s
findings (a new `product-advice-agent-implementer` if it cannot be resumed) and wait.
**A new round starts only once that Progress entry exists.** Otherwise (that
verdict is not `rework`, or no `review.md` exists for the round) the round's
review is redone as the same round. An empty `auto_round` (a close before round 1) is round 0:
the build step, then round 1.

| `auto_stopped` | Resume |
| --- | --- |
| spec questions, spec drafted | step 2: the owner's answers or yes, then step 3 |
| plan found the spec incomplete, plan.md exists unapproved | step 3 again, only after the owner has settled it; never approve a plan this run did not draft |
| decision needed, spec or plan amendment needed | give the implementer the owner's answer (a new `product-advice-agent-implementer` if it cannot be resumed), wait, then **a new round** `auto_round` + 1 (step 5, item 1) |
| re-check mismatch | redo the re-check (step 6) for round `auto_round` and write that round's `review.md`; **no new round**. If the reviewer's report is not in this conversation (a new session), redo the review as the same round, then the re-check |
| escalate | the owner's `/auto <id>` means "diff read": go on to the live-check stop (step 7) or the ship stop (step 8) from that review's `live-check:`; **no new round** |
| live check owed | step 7: if the owner says it passed and `live_checked` is recorded, step 8; a defect they describe goes to the implementer, then a new round |
| out of rounds | report the open findings again; the intent continues by hand |
| ready for /ship | run the dry-run (step 8) again and report |
| critical finding | like a decision: give the implementer the owner's answer, wait, then **a new round** (never a re-review of an unchanged branch) |
| red verify, red check:intent, agent error, worktree held, too many sessions | clear the cause (the owner says it is), then redo the step that stopped; a failed implementer is relaunched, a failed review is redone as the same round |

A new round always passes the cap in step 5, item 1. Never redo a recorded
gate or a finished step.

## 2. The spec stop — features only

A fix or refactor has no spec, and an adjustment or experiment has no plan:
skip to step 3 (fix, refactor) or step 4 (adjustment, experiment).

- If `spec.md` is missing, draft it as `/spec` does, including its single
  question round. If it asks the owner questions, **stop** with
  `auto_stopped: spec questions` and wait.
- With the spec drafted and `spec_accepted` not recorded, **stop once**:
  `auto_stopped: spec drafted, waiting for spec_accepted`. Report the
  spec's weak points as `/spec` does.
- `spec_accepted` is the owner's, recorded as today: their own date, or
  `<date> by-agent` on their yes **to this stop's message**. The `/auto`
  authorisation does not cover it. On the yes, record it, then continue by
  yourself to step 3.

## 3. The plan

Skip when `plan_approved` is already recorded, or for an adjustment or
experiment.

0. If a `plan.md` already exists and `plan_approved` is not recorded, this
   run did not draft it (it may be hand-edited or from an earlier session):
   **stop** with `auto_stopped: plan exists unapproved, owner decides`
   and ask the owner to approve it themselves or to say to redraft. Record
   `plan_approved` only for a `plan.md` this run drafted.
1. Draft the plan as `/build-plan` does. If `/build-plan` step 3 finds the
   spec (or, for a fix or refactor, the intent) incomplete, **stop** with
   `auto_stopped: plan found the spec incomplete`. Never decide a design
   point.
2. Otherwise record, in `metadata.yml`, only when step 1 recorded
   `auto_authorized` for this id in this run (and, for a feature,
   `spec_accepted` is recorded):
   `plan_approved: <today> by-agent    # auto: owner "/auto <id>" (auto_authorized <date>)`.
   The `by-agent` form is the one `check:intent` accepts; do not invent any
   other value.
3. Commit the plan and the metadata on `main`: `§<id>: plan drafted (by
   /build-plan)` and `§<id>: plan approved (auto: owner "/auto <id>")`.

## 4. Build

Run `/spawn <id>` (its steps 1 to 5): check the load, `npm run spawn --
<id>`, then launch `product-advice-agent-implementer` with `run_in_background: true` in
the worktree. The brief carries what `/spawn` step 5 lists and the safety
rules (step 9). Wait for it; you are notified when it ends. Do not poll.

## 5. The review loop, at most three rounds

A round is one `/review`. The rounds are counted across the whole run,
including a rework after a live-check defect (step 7), and across resumed
sessions (`auto_round`).

For each new round `n` (the recorded `auto_round`, plus one; a resume that the
table marks "no new round" does not come through here):

1. **The cap.** If `n` would be 4, **stop** with
   `auto_stopped: out of rounds, open findings below` and list the open
   findings. The intent continues by hand. `auto_round` stays at 3 (the
   most `check:intent` accepts): at this stop, step 9 writes 3, never 4.
2. Write `auto_round: <n>` into the branch's `metadata.yml` and commit it
   (the implementer has finished; the worktree is yours). Writing it at
   each round start means a closed session resumes at the right round. The
   same commit clears
   `auto_stopped` if a resume left it set (step 1, item 3).
3. Delegate `/review` to `product-advice-agent-reviewer`, telling it `run: auto` and
   that every finding needing rework must say "Needs rework:" or "Needs
   decision:" (`REVIEW-POLICY.md` → "The report").
4. **Re-check (step 6) before writing `review.md`.** Then read
   `.claude/skills/review/SKILL.md` and write `review.md` as its step 4 does:
   its stamp line as the first line (`<!-- generated-by:
   product-advice-agent/review@<the version that skill states> -->`, copied from the
   skill, never remembered), the format of `REVIEW-POLICY.md` → "The report",
   including `## Type check` with the pasted `npm run check:intent` output and
   the `## Verified myself vs. taken on trust` heading, with `run: auto`.
   Commit it on the branch.
5. Act on the verdict:
   - **`escalate`**: always stop, `auto_stopped: escalate, owner reads the
     diff`. The Reviewed tier needs the owner's diff read. The owner's next
     `/auto <id>` means "diff read" and goes on to the live-check or ship
     stop with no new round.
   - **`rework`**: every finding needing rework must be "Needs rework:"
     (step 7 defines mechanical). Resume the implementer with the findings
     (same agent if it can be resumed, else a new `product-advice-agent-implementer`
     with the findings and the same brief), wait for it, then start round
     `n+1` at item 1. A single "Needs decision:" finding stops the run.
   - **`attest`**: `live-check: owed` goes to the live-check stop (step 7);
     `live-check: not-needed` goes to the ship stop (step 8).

## 6. The coordinator's re-check

Before writing each round's `review.md`, re-run in the worktree, yourself:

- `npm run verify` and `npm run check:intent`;
- the project's end-to-end suite, once it has one, when the changed paths
  call for it (`REVIEW-POLICY.md` → "Live checks");
- **every mutant the review lists as surviving**;
- **every mutant the round's resolutions say a rework now kills**, from the
  implementer's report and the previous round's findings.

For a mutant: back up the target file by copy, apply the one-line change, run
the full suite, restore by copy (never `git checkout --`), and end with `git
status --short` clean.

Compare what you got with what the reviewer and the implementer quoted:
files, tests, lint warnings, end-to-end passes, and each mutant's result (killed or
survived, and by which test). **Any mismatch stops the run**, with
`auto_stopped: re-check mismatch` and every mismatch listed in the stop
report. Do not write a green `review.md` over a mismatch.

Put the results in the report's "Verified myself" section, each line marked
**Coordinator, re-run**, as `/review` does for the commands it re-runs.

## 7. The stop rules

**Needs rework or needs decision.** "Needs rework:" is mechanical: the
spec, the plan or a test determines the fix. "Needs decision:" is the
choice between behaviours, or a change to what the spec or plan says. Stop
on any "Needs decision:" finding, with `auto_stopped: decision needed`. Also
stop when a mechanical fix would edit `spec.md` or `plan.md` above its
Progress marker: any amendment is the owner's (`auto_stopped: spec or plan
amendment needed`). If you doubt a finding's kind, treat it as a decision.

**The live check.** On `live-check: owed`, stop with `auto_stopped: live
check owed`, and give the owner the report's `## Live check` steps. The
owner runs them.
- Pass: the owner says so, and `live_checked` is recorded as today, on the
  owner's request (`ship` also takes it with `--live-checked`). Then
  continue to step 8.
- Defect: the owner describes it and says to rework. Resume the implementer
  with that description and continue the loop at step 5 (it is the next
  round, against the same cap).

**Other stops.** Stop on: a CRITICAL finding (`critical finding`); a
red `verify` or `check:intent` you cannot trace to a finding the implementer
is fixing (`red verify` or `red check:intent`); an agent error or a stopped
agent (`agent error`); a worktree held by a session you didn't start
(`worktree held by another session`); a fourth open intent session or run
(`too many sessions`).

## 8. The ship stop

The run ends at a merge-ready branch: the verdict is `attest`, or
`escalate` after the owner's diff read (`/auto <id>` after an escalate
stop), the live
check is recorded or `not-needed`, and `npm run ship -- <id> --dry-run`
(run from the main checkout) shows nothing in the way. It changes nothing
and does not even fetch. Report:

> ready: `/ship <id>`

with the verdict, tier, round count, the dry-run's report, and the
sampling line (`sampled: yes` means a post-merge full read is due). If the
dry-run shows something in the way, stop with `auto_stopped: ship dry-run
blocked` and relay it. Set `auto_stopped: ready for /ship` and commit it, so
`npm run sessions` shows the end state.

Never run `/ship`, `npm run ship` without `--dry-run`, or any merge, push,
branch deletion or worktree removal, even if the owner seems to imply it:
only a `/ship <id>` message does.

## 9. Every stop is visible

On each stop, before you report:

1. Write `auto_round: <n>` (the number of the round in progress or just
   finished, never above 3) and `auto_stopped: <reason>` into the branch's
   `metadata.yml` (on `main` before the branch exists) and commit it,
   subject `§<id>: auto stopped: <reason>`. **No `#` in the reason**: a `#`
   starts a comment in `metadata.yml` and would cut the reason short. Keep it
   short; the stop report carries the detail.
2. If your session has a push-notification tool, send one naming the intent
   and the reason. If not, `npm run sessions` is enough.
3. Report to the owner: the reason, what is open, and exactly what to say or
   do next (for example "answer the question, then `/auto <id>`").

`npm run sessions` and `npm run queue` then show `auto · r<n> · <reason>`.
The run lives in this coordinator session: closing it pauses the run,
and a later `/auto <id>` resumes from the recorded `auto_round` and
`auto_stopped`.

## 10. The safety rules in every brief (and kept by you)

Put these in the brief of each agent you launch, and keep them yourself:

- never run `npm run ship` (the coordinator alone runs `--dry-run` at step
  8), never merge, push, rebase or delete a branch or worktree;
- never record a gate: only this skill's coordinator writes `plan_approved`
  (step 3), `auto_authorized`, `auto_round` and `auto_stopped`;
- never touch real user data or a live external system;
- never raise a lint warning cap;
- restore mutants by copy, never `git checkout --`, and finish with `git
  status --short` clean;
- never kill a process the run didn't start;
- the implementer sets `status: in-review` and appends to `## Progress` only.

## 11. Counting

Every `review.md` of a run says `run: auto`. `sampled:` comes from
`npm run sdlc:scan -- --sample-due auto --exclude <id>`: every third
attested auto-run change gets a post-merge full read. `npm run sdlc:scan`
splits follow-up fixes and reverts by tier and run kind.
