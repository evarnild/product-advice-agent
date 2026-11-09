# Intents

One folder per piece of work. It holds the artefacts that carry the work
from "what do we want" to "merged". This is product-advice-agent's slice of the
AI-native SDLC: each stage ends by writing something the next stage reads,
and the chain is the audit trail of who asked for what and who approved it.

The queue is **generated**: `npm run queue` lists every intent here with its
type, status and gates, reading each `metadata.yml` (from the intent's branch
while unmerged, else from `main`). Nobody edits it. `OVERVIEW.md` at the repo
root is the short, owner-edited snapshot.

## Layout

```
intents/
  <id>-<slug>/
    intent.md      what we want and why: the problem, in the originator's words
    spec.md        what we will build (features only)
    plan.md        how we will build it, approved before code; ends with ## Progress
    review.md      the review report (written by /review, updated in place)
    metadata.yml   id, type, status, gates, links
  _templates/      what the skills fill in; usable raw by hand
```

**The id is the next `§` number.** Commit messages use the same numbering,
so `§2`, `intents/2-…/` and `feat/2-…` all name the same thing. Take the
number `npm run queue -- --next-id` prints: one more than the highest used in
`OVERVIEW.md` and the `intents/` folders on `main` and on every local branch.
§1 is the stack decision.

## Types

Every intent declares a type. The type decides which artefacts and gates
apply, so the heavy path is paid only where it earns its keep. **When in
doubt, it is a feature.**

| Type | Branch | Artefacts | Gates you record | Use for |
| --- | --- | --- | --- | --- |
| feature | `feat/<id>-<slug>` | intent, spec, plan | intent, spec, plan | new behaviour, a new integration, anything with a design question |
| fix | `fix/<id>-<slug>` | intent, plan | intent, plan | a live defect; the intent *is* the spec. The change carries a test that fails first |
| refactor | `refactor/<id>-<slug>` | intent, plan | intent, plan | structure changes that hold behaviour constant |
| adjustment | `adjust/<id>-<slug>` | intent | intent | wording, README, config, constants: at most 5 files and 60 lines, no core code |
| experiment | `exp/<id>-<slug>` | intent | intent | throwaway probes such as a prompt trial or a model comparison; never merged into core code as-is |

The declaration is a claim, and `npm run check:intent` is the evidence. It
compares what arrived against what the type should look like, and reports
`ROUTE` when they disagree. Examples: an "adjustment" that touched core code,
a "fix" with no test, a "refactor" that deleted test lines. A test counts
when its file changed; the check never reads test content. A route is not a
block. Either re-declare the type (and add the missing artefacts), or say in
`review.md` why the mismatch is fine. Expected noise: renaming or moving a
test file shows as lines deleted from the old path, so a refactor that does
it routes. Say so in `review.md`.

What counts as core code, as a test, and as code at all is defined at the
top of `scripts/intent-check-lib.mjs`. The rules are language-neutral until
§1 picks the stack and narrows `CORE_CODE`.

A fix whose defect came from an earlier intent's change records that in
`metadata.yml` as `follows_up: <id>`. That key is what lets
`npm run sdlc:scan` count follow-ups per review tier, so set it only for a
real cause.

If an intent turns out to be wrong after merge, either revert and keep the
original intent, or forward-fix with a new one. Don't rewrite the old
folder.

## Gates

Four of the strategy's six human gates live here, plus the live check when a
review says one is owed. Each is your decision.

| Gate | Recorded as | Meaning |
| --- | --- | --- |
| accept the intent | `intent_accepted: <date>` | the work is worth doing, and the problem statement is right |
| accept the spec | `spec_accepted: <date>` | this is what we will build |
| approve the plan | `plan_approved: <date>` | this is how we will build it; no code before this gate |
| live check, when owed | `live_checked: <date>` | you ran it yourself and saw what `review.md` → `## Live check` said you should; no merge before this gate (`REVIEW-POLICY.md` → "Live checks") |
| approve the change | `review.md` verdict + the merge commit | you read the report (and the diff, at the Reviewed tier) and take responsibility |

The other two gates stay outside `intents/`: authorising a release, and
triaging a finding (turning a defect into a new fix intent).

`check:intent` fails a change whose code moved before the gates its type
needs were recorded.

## Who edits what

- **You** write or accept `intent.md`, `spec.md` and `plan.md`. The skills
  draft; you decide.
- **Who records a gate.** A gate field is `intent_accepted`, `spec_accepted`,
  `plan_approved` or `live_checked`. You write it directly, or an agent writes
  it **on your request in the current conversation**. A request is an
  explicit instruction naming the gate ("accept §3", "record the live
  check"), or a "yes" (or "go ahead", "ok") in reply to the agent's own
  message that proposed recording it. A "yes" to a message that proposed
  several gates records every gate that message named, and nothing more and
  no later gate.
- **What does not count.** The exclusions of `REVIEW-POLICY.md` →
  "Merging": a standing instruction from an earlier session, a memory, a
  `CLAUDE.local.md` brief, an unprompted "yes" that answers no proposal, a
  request in another session. A subagent (`product-advice-agent-implementer`,
  `product-advice-agent-reviewer`, any `Agent`-tool worker) never records a gate: your
  request is not in its conversation. A spawned session is a conversation
  with you, so the rule applies there.
- **`/auto <id>`.** Your `/auto <id>` message in the coordinator
  conversation, for an intent whose `intent_accepted` is recorded, is a
  request to record that intent's `plan_approved`, and no other gate. The
  coordinator records it as `<date> by-agent` once the plan is drafted, and
  only if the plan finds the spec complete (`/build-plan` step 3), with a
  comment naming the authorisation, for example
  `# auto: owner "/auto 5" (auto_authorized 2026-11-03)`. It covers that one
  intent and that run: a second `/auto <id>` is a new request for the same
  gate and nothing wider. It is not a standing instruction. `intent_accepted`,
  `spec_accepted` (a feature's run stops once for it) and `live_checked`
  stay yours, and so does `/ship` (`REVIEW-POLICY.md` → "Merging"). A
  subagent still never records a gate; the coordinator writes this one, in
  the conversation that holds your message.
- **The decision stays yours.** For `live_checked:` you run the check; an
  agent records it only after you say you ran it. An agent's own run of the
  product, or a passing automated suite, is never the check.
- **The marker.** An agent-recorded gate carries `by-agent` after the date,
  on the same line: `intent_accepted: 2026-11-03 by-agent`. Your own gate
  stays a bare date. The token is part of the value, not a comment; a free
  `# comment` after it is ignored. `check:intent` counts both forms as
  recorded and FAILs any other value (`yes`, `TBD`, `by-claude`);
  `sdlc:scan` lists bad values under "Metadata problems" and counts owner
  and agent gates. `merged:` is bookkeeping, not a gate; `REVIEW-POLICY.md`
  → "Merging" governs it.
- **The auto fields.** `auto_authorized: <date>` records the `/auto <id>`
  message above, with a bare date or `<date> by-agent` like a gate;
  `auto_round: <1-3>` and `auto_stopped: <reason>` record where a stopped
  run stands. None of them is a gate: nothing waits on them, and
  `check:intent` only rejects a malformed value. Write the reason without
  ` #`, which starts a comment.
- **The implementer agent** may only append to the `## Progress` section at
  the end of its item's `plan.md` and set `status: in-review` when done.
- **A spawned session** (`npm run spawn`, `CLAUDE.md` → "Parallel
  sessions") is the implementer for its intent, with one addition: if the
  gates its type needs are not recorded yet, it may draft the missing
  `spec.md` (`/spec`) or `plan.md` (`/build-plan`) with the skills, then
  stops for you to accept it.
- **The reviewer / `/review`** writes `review.md` and nothing else here.

## Drafting an artefact

`/intent`, `/spec` and `/build-plan` draft `intent.md`, `spec.md` and
`plan.md`. What they do the same way is written here once; each `SKILL.md`
points to this section and adds only what is its own.

1. **Gather before asking.** Read what exists first (the intent, the
   template, `OVERVIEW.md`, `README.md`, `docs/`, the code on current
   `main`) and quote what you use.
2. **Ask at most one batched round**, only for what the material leaves
   open. If you skip a question, decide and list the decision, with its
   reason, under "Assumptions I made".
3. **Quote sources at their wording.** A rule, a line of code or an earlier
   decision is cited with its path and the passage as written, not
   paraphrased.
4. **Record the `main` commit** a spec or plan was checked against (short
   hash), in the artefact itself. An intent states a problem and is not
   checked against code, so it records none.
5. **Stamp the first line** of every file you write, in the form under
   "Stamps" with the skill's own name and version.
6. **Validate before handing over.** Check the draft against its template
   and the skill's own checklist.
7. **Report what is weak**, plainly: open assumptions, claims you could not
   verify, anything the owner should look at first.
8. **Stop for the owner.** Never record a gate on your own: see "Who edits
   what". The next step you name is the owner accepting it, or saying yes so
   an agent records it with `by-agent`.

An artefact that already exists is revised in place: read it, keep what
still holds, and say what changed.

## Stamps

A file a skill produced starts with
`<!-- generated-by: product-advice-agent/<skill>@<version> -->`. That line is how
the grid tells "written by hand" (L1) from "produced by a versioned skill"
(L2). Keep it when you edit the file. Remove it only if you rewrote the file
from scratch.

## Status values

`draft` → `accepted` → `in-progress` → `in-review` → `done`, or `abandoned`
or `deferred`. The status here is the source of truth; `npm run queue` reads
it, and there is no other copy.
