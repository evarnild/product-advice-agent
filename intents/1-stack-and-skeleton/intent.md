<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §1 — Stack and project skeleton

**Type:** feature
**Originator:** me (the owner), via `/intent 1 setup project`
**Source:** `OVERVIEW.md` → "Next"; `docs/sdlc-grid.md` → "The two we move — Q4 2026"

## Problem

The repository holds only the process kit. `CLAUDE.md` says: "Until §1
merges, there is no product code, and no section below describes any." The
product is described in one line (`README.md`): "A small product-advice
agent for a synthetic electronics catalogue, with evaluation, tracing and
guardrails." The intended stack is "Python + Langfuse (self-hosted),
confirmed by §1", but nothing confirms it yet.

With no product code and no product test suite, every later intent is
blocked or costs more than it should:

- `REVIEW-POLICY.md`: "**Until §1 adds the product's test suite, only the
  kit itself (`scripts/`) meets this**, so any `src/` change before then is
  reviewed as Reviewed." Nothing in the product can be attested.
- `npm run verify` is `"npm run test:kit"` (`package.json`). It checks the
  kit, not the product.
- `scripts/intent-check-lib.mjs` still has `export const CORE_CODE =
  [/^src\//];`, so `check:intent` cannot tell core modules from the rest.
- Live-check rule 1 "names nothing", and the Reviewed tier's "by meaning"
  list has no paths. `/review` has to guess which changes touch prompts,
  user-facing output, credentials or personal data.
- `CLAUDE.md` → "Architecture" says "None yet". An implementer has no
  module boundary to respect.

## Outcome

- The stack is decided and written down in `docs/`, with reasons:
  language, package manager, test, lint and type-check tools, the model
  provider, and how Langfuse runs (self-hosted).
- A skeleton runs end to end on one fixed question against a tiny synthetic
  catalogue and sends a trace to Langfuse. Its tests fake the model call.
  `npm run verify` runs the kit's tests **and** the product's lint,
  type-check and tests as one command, and it is green on a fresh clone.
- The kit's §1 hand-offs are done, and a reviewer can tick each one:
  `CLAUDE.md` → "Architecture" is written; `CORE_CODE` is narrowed;
  `REVIEW-POLICY.md` names the live-check runtime paths and the "by
  meaning" paths; `npm run setup:worktree` is defined, so a fresh worktree
  from `npm run spawn` passes `npm run verify`; `README.md` says how to run
  the agent.

## Constraints

- **Conventions already in force** (`CLAUDE.md`): "Model calls and external
  APIs are faked or recorded in tests, never called live from the suite";
  "No secret, token or real user data is committed, including in fixtures
  and logs"; "No new dependency arrives without a line in the intent's
  `plan.md` saying why."
- **One command.** `npm run verify` stays the single check ("Keep it
  **one** command"). The kit still needs only Node ≥ 22. The product adds
  its own toolchain, which `setup:worktree` installs.
- **Data.** The catalogue is synthetic and committed. There is no real user
  data. Traces sent to Langfuse hold only synthetic conversations. API keys
  live in an uncommitted `.env`, next to a committed `.env.example`.
- **Cost.** The suite costs nothing to run because it makes no live model
  calls. A manual live run uses a small model and costs at most a few cents.
- **Autonomy.** The agent only answers questions about the catalogue. It
  takes no action outside the conversation: no purchases, no email, no
  external writes other than traces to the self-hosted Langfuse.
- **Review tier.** This change edits `REVIEW-POLICY.md` and
  `scripts/intent-check-lib.mjs` (both Reviewed by path) and creates the
  product's first prompt, so it is **Reviewed**.
- **Out of scope:** advice quality, the evaluation suite, guardrails beyond
  a placeholder seam, a UI and any deployment. Those are later intents. §1
  only leaves room for them in the architecture.

## Type-specific questions

### Feature
- **Users:** first the owner, as developer and operator. Later, end users
  asking for product advice in a chat; this intent does not serve them yet.
- **What exists today:** nothing beyond the kit. There is no `src/`, no
  `pyproject.toml`, no catalogue and no Langfuse setup.
- **Open design questions** (for `spec.md`):
  1. The model provider and default model (assumed Anthropic Claude; see
     below).
  2. The agent loop: a hand-written tool-use loop over a catalogue-search
     tool, or a framework? How much of it is pure, testable logic, and how
     much is I/O?
  3. The catalogue's format and size (JSON or CSV, how many products, which
     attributes), and how it is searched (filters, keywords, embeddings).
  4. Langfuse: self-hosted via a Docker Compose file in the repo, or an
     instance that already runs? Is tracing on by default, and does the
     suite run with it off?
  5. The entry point: a CLI first, or an HTTP API?
  6. Tooling: `uv`, `ruff`, `pytest`, `mypy` or `pyright`, and how
     `npm run verify` calls them.
  7. Where the seams for later evaluation and guardrails sit: input and
     output check hooks around the agent call, a dataset format for evals.
  8. Which paths become `CORE_CODE`, the live-check runtime paths and the
     Reviewed "by meaning" paths.

## Assumptions I made

- **Id 1, though `npm run queue -- --next-id` prints `2`.** `OVERVIEW.md`
  line 19 contains "confirmed by §1", and `nextId` counts every `§N` in
  `OVERVIEW.md`. `OVERVIEW.md`, `intents/README.md` ("§1 is the stack
  decision") and your argument all name this intent §1, so I used 1. Once
  this folder exists, the generator is consistent again: the next id is 2.
- **Type is feature.** No flag was given. It is new behaviour with open
  design questions, and `OVERVIEW.md` says "Start it with `/intent
  --feature`".
- **Scope is a walking skeleton**, not a useful agent: one question in, one
  answer grounded in the catalogue out, traced. Advice quality, evals and
  guardrails are separate intents.
- **The model provider is Anthropic Claude.** The stack line names only
  Python and Langfuse. The spec settles it.
- **Langfuse runs locally via Docker Compose** for the live check. The
  suite never needs it.
- **The cost and autonomy limits** above are mine, not stated by you.
- **The Python toolchain** (`uv`, `ruff`, `pytest`, a type checker) is my
  default reading, left to the spec.
