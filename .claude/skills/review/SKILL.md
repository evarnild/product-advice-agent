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
- **Bring the branch up to date first.** If the branch is behind local
  `main` (`git rev-list --count <branch>..main` above 0), the coordinator
  runs `npm run update-branch -- <id>` before any pass. This is the one write
  `/review` makes besides `review.md`, made by the script before the review
  starts; under `/auto` it is already done and the script exits 0 with "contains
  main". Exit 0: review. Exit 2, 3 or 1: no passes and no `review.md`; tell
  the owner the branch is behind `main` by N, the script's report (the
  conflicted files, the red output, or the refusal), and what to do next:
  "send the conflict to the implementer session (or resolve it), then
  `/review` again". A reviewer agent stays read-only and never runs the
  script. Once the update is done and before pass 1, record
  `git rev-parse --short main` for the `main:` header line.
- **The reviewed diff** is `git diff main...<branch>` (three-dot), so
  `main`'s changes stay out of it; mutations are enumerated from that diff.
- **Read-only:** after that, no commits, resets, stashes, merges, or edits to
  code. The only file you write is `review.md`.
- **The intent:** find `intents/<id>-*/` from the branch id. Read
  `intent.md`, `spec.md` (if any), `plan.md` including `## Progress`,
  `metadata.yml`, and any previous `review.md`. If there is one, this run is
  round n+1: put the new report at the top and move earlier rounds below
  `# Round N (history)`, as the policy describes.

For a substantial branch, delegate the passes to the `product-advice-agent-reviewer`
agent (the `Agent` call's description begins `§<id> review`, for example
`§13 review round 2`, so `npm run stats` can attribute it), giving it this
skill's instructions and the policy, then assemble its
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

Eval-run check (`REVIEW-POLICY.md` → "Eval runs", part of pass 3): run
`uv run advisor-analysis owes-run --base main`. When it says "owed", the
change must name an eval run made on the reviewed content. Without one, write
a HIGH finding "Needs rework: make the eval run". When the coordinator runs
this review, it makes the run as `/auto` step 6 describes. A reviewer agent
only checks that the run is named and that `uv run advisor-analysis hashes
<report>`, run in the worktree at the reviewed commit, exits 0 (it hashes
`evals/cases.jsonl`, `src/advisor/prompts/system.md` and
`src/advisor/data/catalogue.json` as the run does and names a field that
differs). `compare`'s hash warnings are against the
baseline: expected differences, not this check. A single run varies: the
coordinator (never a reviewer agent, which calls no model) re-runs a flipped
case with `uv run advisor-eval --only <flipped ids>` and calls it a
regression only if it fails again. The full run stays the report `## Eval
run` names and the baseline source; the `--only` re-run is evidence only,
and its `compare` output shows the other cases as "removed", as expected.

## 4. Write `review.md`

Use exactly the format in `REVIEW-POLICY.md` → "The report", with
`main: <hash>` from step 0.

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
- **`## Eval run`:** after `## Live check`, either `not owed (no listed
  path)` or the run report's name, provider and model, the comparison
  (`advisor-analysis compare`), and your reading of it (the coordinator
  re-runs a flipped case with `--only` before it is called a regression: a
  single run varies; the full run stays the named report).
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

If they ask you to merge, use `/deliver <id>`, which applies
`REVIEW-POLICY.md` → "Merging": its preconditions, then `verify` on `main`,
then the bookkeeping.
