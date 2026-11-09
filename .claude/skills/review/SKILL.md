---
name: review
description: Run product-advice-agent's review policy against a branch and write the review report (intents/<id>-<slug>/review.md) with passes, findings, a Not-checked section and an attest/escalate/rework verdict. Use before merging any product-advice-agent branch into main, or to re-review after rework. Invoke as /review [branch].
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/review@0.1.5
---

# /review — the agentic review before you merge

`REVIEW-POLICY.md` is the policy, and this skill is how to run it. Read the
policy first, every time: it changes, and the version you remember may not
be current.

Stamp: put `<!-- generated-by: product-advice-agent/review@0.2.0 -->` as the first
line of `review.md`.

## 0. Orient

- **Branch:** the argument, or else the current branch. Run
  `git rev-parse HEAD`, `git branch --show-current` and `git worktree list`.
- **Where to work:** if the branch is checked out in another worktree,
  review it there, or use `git checkout --detach <branch>` in a scratch
  worktree. Never `git checkout` in the main checkout: another session may
  be working there.
- **Read-only:** no commits, resets, stashes, merges, or edits to code. The
  only file you write is `review.md`.
- **The intent:** find `intents/<id>-*/` from the branch id. Read
  `intent.md`, `spec.md` (if any), `plan.md` including `## Progress`,
  `metadata.yml`, and any previous `review.md`. If there is one, this run is
  round n+1: put the new report at the top and move earlier rounds below
  `# Round N (history)`, as the policy describes.

For a substantial branch, delegate the passes to the `product-advice-agent-reviewer`
agent, giving it this skill's instructions and the policy, then assemble its
output into the report. Do not trust an implementer's self-report, and do
not trust a sub-agent's either: re-run the commands whose results you quote.

## 1. Mechanical checks first

```bash
npm run verify          # must be green
npm run check:intent    # PASS / ROUTE / FAIL; paste the output
```

A red `verify` or a FAIL type check means an immediate `rework` verdict.
Still run the remaining passes you can, so that one round catches as much as
possible.

**One exception:** a FAIL whose only error is "A live check is owed and not
recorded" (set by an earlier round) is the owner's to clear, not rework. Note
it and carry on.

## 2. Decide the tier

Apply the policy's three inputs in order: the path table, then
`review_tier` and type in the metadata, then this run's findings. Write down
which input set the tier. Never lower a tier.

## 3. Run the passes

Run all nine passes from `REVIEW-POLICY.md`, in order. For each, record
`pass`, `findings (n)`, or `not run — <why>`.

Pass 4 (mutations) is the expensive one, and the one that matters most:
- make one mutation per changed behavioural line, and run the full suite for
  each;
- back up and restore files yourself (never `git checkout --`);
- end with `git status --short` clean.

## 4. Write `review.md`

Use exactly the format in `REVIEW-POLICY.md` → "The report".

- **Findings** carry a severity, `file:line`, what is wrong, and one of:
  - "Needs rework: <minimal fix>" (mechanical: the spec, the plan or a test
    determines the fix);
  - "Needs decision: <the choice>" (the fix picks between behaviours, or
    changes what the spec or plan says);
  - "Worth a look".

  When unsure, write "Needs decision:". A wrong "Needs rework:" lets an
  auto run decide for the owner.
- **Not checked** is honest and specific: untested paths, behaviour that
  depends on a live model or external API, mutants you didn't run and why.
  An empty Not-checked section is almost always wrong.
- **Verified myself vs. taken on trust** lists the commands you actually
  ran, with their results.
- **Verdict:** `rework` if any finding needs rework; otherwise `escalate` if
  the tier is Reviewed; otherwise `attest`.
- **`live-check:`** decide it after the passes, using the three rules in
  `REVIEW-POLICY.md` → "Live checks".
  - When `owed`: the `## Live check` section gives steps the owner can follow
    without asking: the exact command, the input or fixture, what to do, and
    what they should see.
  - When `not-needed`: one line saying why. The one exception the policy
    allows ("When an end-to-end suite stands in") needs your own passing run
    of the suite, with the scenario named.
  - If you ran the thing yourself, list what you saw under "Verified myself".
    That never replaces the owner's check, and you never write
    `live_checked:` unless the owner asks you to, after running the check
    themselves.
- **`run:`** `auto` when `/auto` called this review (its brief says so),
  otherwise `manual`.
- **`sampled:`** run `npm run sdlc:scan -- --sample-due <run> --exclude <id>`
  (this review's run kind and intent id). It counts the attested reviews of
  that run kind in `intents/*/review.md`, leaving this intent out: every 5th
  attested manual change and every 3rd attested auto-run change is due.
  When it prints `sampled: yes`, and only if the verdict is `attest`, set
  `sampled: yes` and tell the user a post-merge full read is due.

Write nothing but `review.md`. The implementer sets `status: in-review`. If
the status is still something else, say so in the report rather than fixing
it.

## 5. Tell the user

Give one short block:
- the verdict;
- the tier, and why;
- the count of findings by severity, and the top finding if there is one;
- the Not-checked headline;
- "live check owed: <one-line summary>", when one is;
- what they do next: "read the report and merge", "read the diff too
  (Reviewed)", or "rework, then /review again".

An owed live check comes before the merge: "do the live check, record
`live_checked:`, then merge".

If they ask you to merge, use `/ship <id>`, which applies
`REVIEW-POLICY.md` → "Merging": its preconditions, then `verify` on `main`,
then the bookkeeping.
