<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §9 — Error analysis on top of the eval suite: synthetic questions by dimension, a trace viewer and pass/fail labels with critiques

**Type:** feature
**Originator:** the owner, 2026-11-11: "Let's implement evaluation like
described in https://hamel.dev/blog/posts/field-guide/", then "a new intent,
… on top of intent 8"
**Source:** Hamel Husain, "A Field Guide to Rapidly Improving AI Products"
(2025-03-24), quoted below; `intents/8-offline-evals/intent.md`

## Problem

§8 gives the advisor a fixed question set and deterministic checks that are
chosen up front: cited ids exist at the stated price, expected products
cited, forbidden ones not, off-topic declined, out of stock flagged. Those
checks catch the failures we already thought of. They can't show the
failures nobody has thought of yet, or which failures matter most.

The field guide says that is the wrong starting point on its own. It calls
error analysis "the single most valuable activity in AI development", warns
that "Generic metrics are worse than useless", and says "it is impossible
to completely determine evaluation criteria prior to human judging of LLM
outputs". It also says to "let metrics naturally emerge" from reading real
outputs. The one advice defect found so far (§7's hyphen) was found exactly
like that: by reading an answer during a live check, not by a check.

Today nobody can read the advisor's answers in bulk, record a judgement on
each, or count how it fails. With no users, there are also no real
conversations to read: the questions have to be synthetic, and §8's small
hand-written set doesn't cover the variety the guide asks for.

## Outcome

The field guide's first loop works end to end on top of §8, from questions to
counted failure modes.

- **Synthetic questions by dimension.** A command generates user
  *questions* (inputs only: "Generate user inputs, not outputs") across the
  dimensions *feature*, *scenario* and *persona*, and adds them to §8's
  question set in §8's format, tagged with their dimensions.
  - Feature is the catalogue category or ask.
  - Scenario is exact match, several matches, no match, budget too low, out
    of stock, off-topic, or spelling that differs from the catalogue.
  - Every no-match and out-of-stock question is checked against the
    catalogue with `search_products`, so "no match" really has none ("Verify
    scenario coverage").
  - The owner reviews the generated questions before they are committed.
- **Runs that keep everything.** §8's runner stores the full context of each
  conversation locally: the question and its dimensions, every model turn,
  each tool call with its arguments and results, the answer, the guardrail
  verdicts, §8's check results, the model and the prompt version.
- **A simple viewer for labelling.** A local viewer shows one run's
  conversations with all context on one screen. The owner gives each a
  **pass or fail** with a free-text **critique**, in one keystroke plus
  typing ("One-click correct/incorrect buttons beat lengthy forms."). There
  are hotkeys for next and previous, filters by dimension, by label and by
  §8 check result, and labels are saved as they are made.
- **Failure modes counted.** From the critiques, a command proposes a
  taxonomy of failure modes. The owner edits and accepts it, each failed
  conversation is mapped to one or more modes, and a table gives the count
  per mode and per dimension. The table also shows where §8's checks agree
  with the owner's labels and where they miss. That table is what the next
  intents start from.
- **Tests without a model.** `npm run verify` covers the generator's
  coverage check, the recorder, label storage, the taxonomy mapping and the
  counts, using the scripted fake. The live run, the labelling and the
  analysis are the owner's, outside verify.

## Constraints

- **§8 first.** This intent starts after §8 is merged. It extends §8's
  question format, runner and report, and does not fork them. §8's checks
  and their pass or fail meaning stay as §8 specifies them. If §9 needs a
  field in §8's format, it adds one without changing the old ones.
- **Architecture (`CLAUDE.md`).** The run drives the advisor through
  `answer_question` and the `ModelClient` protocol, and builds providers
  with `make_client`. Nothing imports `anthropic`, `httpx` or `langfuse`
  outside their one module each (`tests/test_boundaries.py`). Recording
  goes through the `Tracer` protocol or the agent's results, not through
  patching. The shipped behaviour of the advisor is unchanged.
- **Data.** Only the synthetic catalogue and generated questions; no real
  user data. Runs, labels and critiques are kept out of git by default.
  Which of them are committed (the question set and the accepted taxonomy at
  least) is the spec's decision.
- **Cost.** Generation and the run default to the local model (Ollama) and
  cost nothing. Anthropic is used only when the owner selects it with the
  existing `ADVISOR_MODEL_PROVIDER` / key. Tests never call a model
  (`tests/conftest.py` blocks sockets).
- **Autonomy.** The tooling proposes and the owner decides. The owner labels
  every conversation: no model grades the advisor's answers here (the
  guide warns against "automating too much, too quickly"). A model may
  propose questions and draft the taxonomy, and only the owner's accepted
  version counts. Nothing runs on a schedule. Nothing changes the prompt,
  catalogue or code.
- **Leave alone:** `src/advisor/prompts/`, `guardrails.py`, `cli.py`,
  `tracing.py` and the catalogue data.
- **The viewer is local only.** It binds to localhost on the worktree's port
  (`npm run spawn` reserves 5200 + id mod 100). There is no authentication
  and no deployment.
- **Out of scope**, each its own later intent once this loop has produced
  counts:
  - new code checks for the top failure modes;
  - an LLM-as-judge with binary output and the owner's critiques as few-shot
    examples, measured against the owner's labels;
  - prompt or guardrail fixes;
  - a model comparison, as an experiment;
  - Langfuse datasets, scores or annotation queues;
  - an admin UI for editing the prompt.
- No new dependency without a line in `plan.md` saying why. A web framework
  for the viewer is the likely candidate.

## Type-specific questions

### Feature
- **Users:** the owner, as both domain expert and developer. They label,
  read the counts, and choose what to check or fix next.
- **What exists today:**
  - **After §8:** a fixed question set, a runner, deterministic checks and
    a pass/fail report.
  - **From §1:** the scripted fake (`src/advisor/models/fake.py`), the
    `Tracer` protocol (`begin`, `check`, `generation`, `tool`, `finish`,
    `fail`), and Langfuse traces when Langfuse is configured.
  - **Missing:** a way to read many answers, labels, critiques and
    failure-mode counts.
- **Open design questions:**
  1. **Viewer technology.** The owner decided on 2026-11-11: "go with a
     custom viewer". It reads §8's local run files, not Langfuse. Labelling
     in Langfuse annotation queues is its own intent, §10. Left for the
     spec: the stack (stdlib `http.server`, or a small framework such as
     FastHTML, which the guide's author uses) and the label file format,
     which §10 will also write.
  2. **Generation.** A model writes the questions from a dimension grid
     (which model, and how many per cell), or the owner writes them with
     model help. Also the size of the first set: roughly 50 to 100 is a
     guess, because the guide gives no number.
  3. **What is committed.** The generated questions, labels and critiques
     (as future few-shot examples for a judge), the taxonomy, or run files.
  4. **Recording.** Whether §8's runner already keeps enough (tool results
     especially), or needs a recording `Tracer`.
  5. **Taxonomy.** Model-drafted from the critiques and then edited, or
     written by the owner. Its storage format, and whether a conversation
     can have several modes.
  6. **Repeats.** One answer per question, or several per question to show
     how much the local model varies.
  7. **Disagreement.** What happens when the owner fails a conversation that
     passes §8's checks, or the other way round: only reported, or does it
     open a fix intent for the check?

## Assumptions I made

- **On top of §8, not replacing it.** §8's fixed checks stay. They are the
  guide's cheap "specific tests", and §9's labels show where they miss. The
  guide's ordering (read first, test second) is honoured from here on: new
  checks come from §9's counts.
- **Scope is the first loop.** Automated evals for new failure modes, the
  LLM judge and its alignment are follow-ups shaped by the counts.
- **The owner is the domain expert.** There is no separate expert, so the
  owner labels, with tooling that keeps that fast.
- **Binary labels, with the nuance in critiques.** Pass or fail plus free
  text, never a 1–5 scale, following "Favor Binary Decisions Over
  Arbitrary Scales".
- **The guide's sections 3 and 6 are not built here.** Section 3 is domain
  experts writing prompts, which is moot when the owner is both expert and
  developer. Section 6 is an experiment-based roadmap, a way of working.
  Follow-ups that test feasibility can be typed `--exp`.
- **Tier.** New `src/**` code, tests and data put this at Attested by the
  path table, as long as it stays out of `cli.py` and `tracing.py`.
  `review_tier` is left empty.
