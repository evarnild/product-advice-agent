# §<id> — <title>

**Type:** <feature | fix | refactor | adjustment | experiment>
**Originator:** <who noticed or asked: "me", a user report, a review finding>
**Source:** <link: an earlier intent, an issue, a review.md finding, or "none">

## Problem

<The problem in the originator's own words. What is wrong or missing, for
whom, and how you know. No solution here.>

## Outcome

<What is true when this is done, stated so a reviewer can check it. One to
three bullets.>

## Constraints

<What binds this: the architecture boundaries in CLAUDE.md, data handling
(personal data, retention), cost and latency budgets, what the agent may or
may not do on its own, and anything out of scope.>

## Type-specific questions

<!-- Keep only the block for this intent's type. -->

### Fix
- **What broke:** <observed vs expected behaviour>
- **Since when:** <commit / § that introduced it, if known>
- **Impact:** <who hits it, how often, whether a user saw something wrong or data leaked>
- **Reproduction:** <steps, or the conversation or fixture that triggers it>
- **The test that will fail first:** <file and what it asserts>

### Feature
- **Users:** <end users, operators, the owner>
- **What exists today:** <current behaviour or workaround, or "nothing">
- **Open design questions:** <for spec.md to settle>

### Refactor
- **What is restructured:** <files or modules>
- **How behaviour is held constant:** <existing tests that must stay green untouched, and any characterisation tests to add first>
- **Why now:** <what this unblocks: a feature, a lint guardrail, parallel work>

### Adjustment
- **Exactly what changes:** <the wording/constant/config>
- **Blast radius:** <files; must stay within 5 files and 60 lines, with no core code>

### Experiment
- **Question:** <what we want to learn>
- **Containment:** <where it runs: a scratch script, a sandbox, a branch never merged into core code>
- **What happens to the result:** <becomes a new intent, a note in docs/, or is thrown away>

## Assumptions I made

<Anything filled in without being told. A skill must list these; a human
should read them before accepting.>
