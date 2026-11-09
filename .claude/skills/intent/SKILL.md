---
name: intent
description: Draft or sharpen a product-advice-agent intent (intents/<id>-<slug>/intent.md + metadata.yml) for a fix, feature, refactor, adjustment or experiment. Use when starting any new piece of product-advice-agent work, turning a defect or a review finding into work, or backfilling an intent for a plan that came first. Invoke as /intent --fix|--feature|--refactor|--adjust|--exp <what you have>.
metadata:
  owner: eric.varnild
  version: 0.2.0
  scope: repository
  status: experimental
  review-tier: reviewed
  ported-from: heraklios/intent@0.1.5
---

# /intent — draft and validate an intent

You are running the refinement interview asynchronously: turn whatever the
user has into an intent good enough to accept. Follow `intents/README.md` →
"Drafting an artefact" for what the drafting skills share; this file adds
only what is the intent's own.

Stamp: `<!-- generated-by: product-advice-agent/intent@0.2.0 -->` as line 1 of
`intent.md`, and `# generated-by: product-advice-agent/intent@0.2.0` as line 1 of
`metadata.yml`.

## 1. Settle the type

Take the type from the flag (`--fix`, `--feature`, `--refactor`,
`--adjust`, `--exp`). Without a flag, infer it from the material. If it is
ambiguous, it is a **feature**: say so, and why. The rules for each type are
in `intents/README.md`; read it.

## 2. Gather what already exists, before asking anything

Look in this order, and quote what you use:

- the user's message and anything pasted or linked (an issue via `gh`, a
  `review.md` finding, a user report);
- `OVERVIEW.md` and `npm run queue` (once an intent is committed, the queue
  lists it under Queued) for an existing entry that describes this work;
- earlier `intents/*/` for prior attempts or related decisions (grep the
  topic);
- `docs/` for architecture decisions and constraints that bind the work;
- for a fix: the code path, so that the reproduction and the failing-first
  test are concrete, not guessed.

## 3. Ask only the missing questions, by type

Ask at most one round of questions, batched together. Use the type's
question set from `intents/_templates/intent.md`:

- **fix**: what broke, since when, the impact (did a user see something
  wrong, did data leak?), the reproduction, which test will fail first.
- **feature**: the outcome, the users, what exists today, the open design
  questions for the spec.
- **refactor**: what is restructured, how behaviour is held constant, what
  it unblocks.
- **adjustment**: exactly what changes. Confirm that it stays within 5 files
  and 60 lines with no core code; otherwise propose fix or feature instead.
- **experiment**: the question, the containment, and what happens to the
  result.

Skip any question the material already answers. If the user says "just
draft it", fill the gaps with your best reading and list each one under
**Assumptions I made**.

## 4. Write the artefacts

1. **Id:** the next `§` number, from `npm run queue -- --next-id`: one more
   than the highest `§N` in `OVERVIEW.md` and the `intents/` folders on
   `main`, on every local branch and on disk here, so an id taken on an
   unmerged branch or in an uncommitted draft is not taken twice. Slug:
   short kebab-case.
2. Create `intents/<id>-<slug>/intent.md` from the template, keeping only
   this type's question block.
3. Create `metadata.yml` from `intents/_templates/metadata.yml` with:
   - id, slug, type, `status: draft` and the title;
   - `review_tier`: from `REVIEW-POLICY.md`'s path table for the files the
     work will likely touch. Raise it to `reviewed` for anything in the
     table's "by meaning" list (prompts, user-facing output,
     credentials, personal data). Otherwise leave it empty so that the path
     table decides;
   - links;
   - for a fix, `follows_up: <id>` naming the intent whose change introduced
     the defect, when you can tell (check `git log -S` or `git blame` on the
     faulty line). That key, not `links:`, is how the scan counts follow-ups
     per review tier, so set it only for a real cause.

   **Leave every gate empty.**
4. There is no queue row to add: `npm run queue` is generated from the
   `metadata.yml` you just wrote, and lists the intent under Queued once it
   is committed.
5. If the material came from an issue, offer to post the sharpened problem
   statement back to it. Don't post without a yes.

## 5. Validate against the template

Check the draft, and tell the user plainly what is still weak:

- The problem states a problem, not a solution.
- Someone else can check the outcome.
- The constraints name the data, cost and autonomy limits that apply.
- A fix has a reproduction and names the failing-first test.
- An adjustment's blast radius really is small.
- The assumptions are listed, not buried.

End with:
- the folder path;
- the type, and why;
- the open assumptions;
- the next step: "accept by setting `intent_accepted: <date>` in
  metadata.yml, or say yes and I record it". After that comes `/spec <id>`
  for a feature, or `/build-plan <id>` for a fix or refactor.
