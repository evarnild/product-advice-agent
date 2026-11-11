<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §10 — Label eval runs in Langfuse annotation queues as an alternative to the custom viewer

**Type:** feature
**Originator:** the owner, 2026-11-11: "go with a custom viewer, accept
intent 9 but create an intent to be able to do it in langfuse too"
**Source:** `intents/9-error-analysis/intent.md` (design question 1, decided
for a custom viewer); Langfuse docs on annotation queues, score configs and
the Scores API v3 (read 2026-11-11, quoted below)

## Problem

§9 labels the advisor's answers in a custom local viewer that reads §8's run
files. That is the right first tool, but it keeps the labels away from the
place where the traces already live. The self-hosted Langfuse (v4, §4)
receives a trace for every run when it is configured. It has annotation
queues, which the docs describe as "a manual evaluation method which is built
for domain experts to add scores and comments to traces, observations or
sessions". In the open-source self-hosted edition they have no limits. The
pricing table lists "Human annotation queues: Yes", and the licence-key page
says "All core Langfuse features and APIs are available in Langfuse OSS (MIT
licensed) without any limits."

Today those traces can't be labelled usefully in Langfuse, for two reasons
in `src/advisor/tracing.py`:

- a tool call is traced with its arguments, but its output is only
  `{"result_count": n}` (`tracing.py:71-76`). A reviewer can't see which
  products the search returned, so they can't judge whether the answer
  recommended the right one;
- a trace carries only the `provider:` and `model:` tags
  (`tracing.py:43-47`), not the question's §9 dimensions, so traces can't be
  picked or filtered by scenario or persona.

Labels made in Langfuse also never reach §9's failure-mode counts, which
read §9's label files only. And the later LLM-as-judge intent could use
Langfuse's human-vs-AI agreement view (Cohen's kappa and a confusion matrix,
per the docs), but only if the human labels are there.

## Outcome

- **Traces worth judging.** With tracing configured, an eval run's traces in
  Langfuse show what is needed to judge an answer without leaving Langfuse:
  - each tool call's results (the products returned: at least id, name,
    price and stock);
  - the case id and §9 dimensions as tags or metadata, which can be filtered
    in the Tracing table.

  Runs of `uv run advisor` outside the eval suite are traced as before, with
  tool results added.
- **A ready-made queue.** One command makes sure the score config exists (a
  boolean `pass`, with the critique in the score's `comment`, or what the
  spec settles) and creates or reuses a queue. It adds a chosen eval run's
  traces to the queue, all of them or a filter by dimension or §8 check
  result. The owner then labels in Langfuse's queue UI.
- **Labels come back.** A command reads the annotation scores of a queue
  through the Scores API (`GET /api/public/v3/scores` with
  `source=ANNOTATION` and `queueId`). It writes them in §9's label format,
  matched to the run's cases. §9's taxonomy and counts then work the same
  whether a run was labelled in the custom viewer or in Langfuse.
- **Tests without a network.** `npm run verify` covers the tracer's new
  output, the queue set-up and the label import against a faked Langfuse
  client or recorded API responses. The real round trip (send a run, label
  five traces in the queue, import them, count them) is the live check.

## Constraints

- **§9 first.** This intent starts after §9 is merged. It reuses §9's label
  format and taxonomy, and does not create a second one. The custom viewer
  stays the default and keeps working with Langfuse off.
- **Architecture (`CLAUDE.md`).** `langfuse` is imported only in
  `tracing.py` (`tests/test_boundaries.py`), so the queue and import code
  either lives there or goes through a protocol it implements. The pure
  modules still load no `langfuse` or `opentelemetry`. "Tracing never changes
  a run": every Langfuse call stays wrapped and swallowed in the advisor. Only
  the explicit queue and import commands may report a Langfuse error to the
  owner.
- **Data.** Tool results are synthetic catalogue rows, and questions and
  labels are synthetic or owner-written. Sending tool results still widens
  what `tracing.py` sends to Langfuse. That is why the change is Reviewed by
  meaning ("storage or logging of users' personal data
  (`src/advisor/tracing.py`, which decides what is sent to Langfuse)"), so
  the spec must say exactly what is sent.
- **Self-hosted only.** It targets the local stack in `infra/langfuse/` with
  the existing `LANGFUSE_*` keys. Nothing is sent to Langfuse Cloud, and no
  new secret is added.
- **Cost.** No paid tier and no model calls. Tests make no network calls
  (`tests/conftest.py`).
- **Autonomy.** The commands create queues, add items and read scores. They
  never write scores themselves and never delete queues or traces.
- **Live check owed:** `src/advisor/tracing.py` is a live-check path
  (`REVIEW-POLICY.md` rule 1).
- **Out of scope:**
  - Langfuse LLM-as-a-judge evaluators and the agreement view (the later
    judge intent);
  - Langfuse datasets and experiments;
  - pushing labels from the custom viewer *into* Langfuse;
  - changing `infra/langfuse/`.

## Type-specific questions

### Feature
- **Users:** the owner, labelling in Langfuse instead of the custom viewer
  when the traces are already there, and later comparing a judge with their
  labels in Langfuse.
- **What exists today:**
  - Traces of every run when Langfuse is configured, with tool arguments but
    not tool results, and `provider:` / `model:` tags.
  - After §9: local runs, a custom viewer, label files, a taxonomy and
    counts.
  - No score configs, queues or label import.
- **Open design questions:**
  1. Score shape: a boolean with the critique in `comment`, or a boolean
     plus a separate TEXT score (1-500 characters), or categorical.
  2. How much of each tool result is traced, and whether its size is capped.
  3. Tags or metadata for the dimensions, and which of them the Tracing
     table and queue screen can filter on (the queue docs don't document
     filters).
  4. How a trace is matched back to a §9 case: trace id stored in the run
     file, or the case id in metadata.
  5. The API for adding items to a queue. The docs link the annotation-queue
     endpoints, but the read did not confirm the item endpoints. The spec
     must check them in the API reference, along with the v4 SDK's helpers.
  6. Where the queue and import code lives, given the one-module rule for
     `langfuse`.
  7. Whether the reviewer screen shows nested tool-call observations clearly
     enough. The docs don't describe the layout, so this is the live check's
     first question.

## Assumptions I made

- **An alternative, not a replacement.** The owner chose the custom viewer
  for §9. This adds Langfuse as a second place to label, feeding the same
  counts.
- **Reviewed tier.** `review_tier: reviewed` is set, because the change
  decides what is sent to Langfuse. A live check is owed.
- **Labels flow one way, Langfuse to local files.** Two-way sync is left
  out.
- **Tool results are traced for every run**, not only eval runs, because
  they matter for reading any trace, and the catalogue is synthetic. If you
  want them only for eval runs, the spec makes it a switch.
- **The self-hosted stack's version has the features above.** The docs read
  are current; §4's stack is v4 (4.78.0). The spec should confirm the Scores
  API v3 and queue endpoints on that version.
