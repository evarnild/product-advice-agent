<!-- generated-by: product-advice-agent/intent@0.2.0 -->
# §3 — Close the LOW review findings left open by §1

**Type:** fix
**Originator:** the owner ("fix for the low findings"), from §1's reviews
**Source:** `intents/1-stack-and-skeleton/review.md`: round 4's Findings and
its "Round-3 findings: resolution" table (all LOW, "Worth a look")

## Problem

§1 merged with five LOW findings open, carried through review rounds 2 to 4.
Each is either a gap between what `CLAUDE.md` says about the code and what
the code does, or behaviour the suite does not prove:

1. **The pure core loads the tracing SDK.** `CLAUDE.md` → "Architecture"
   lists `agent.py` as pure, tested logic and says `langfuse` is imported
   only in `tracing.py`. But `src/advisor/agent.py:20` imports
   `advisor.tracing.Tracer`, and `src/advisor/tracing.py:16` imports
   `langfuse` at module load. So importing the agent loads the Langfuse SDK
   (and OpenTelemetry), and the "pure" claim is false.
   `tests/test_boundaries.py` checks only who imports `langfuse` directly,
   so it does not catch this.
2. **The stderr line could read like an advisor error.** With Langfuse
   unreachable, a run that answers correctly also prints the OpenTelemetry
   line "Failed to export spans batch due to timeout, max retries or
   shutdown." to stderr. Spec B17 says a tracing failure never changes the
   run. Exit code and stdout hold, but a user reading stderr sees an error
   the advisor did not have. Seen in the round-1 probe; the live check's
   step 8 allowed "at most one export-failure line".
3. **The blocked path through `SafeTracer.check` is untested** (mutant R20,
   `src/advisor/tracing.py:148`). A `SafeTracer` that always forwarded
   `allowed=True` would pass the suite. It is unreachable while both
   guardrails always allow, but the first intent that adds a blocking check
   would trace a block as allowed and nothing would fail.
4. **Two CLI lines are untested** (mutants L5, L6, `src/advisor/cli.py`):
   - `--debug` raising the `advisor` logger to DEBUG;
   - the UTF-8 reconfigure of stdout.

   Removing either leaves the suite green. On Windows the second is what
   lets an answer with "€" print.
5. **One catalogue check can be removed without a failure** (mutant C13,
   `src/advisor/catalogue.py:103`). Removing the "catalogue must be a JSON
   list" check leaves the suite green: a non-list catalogue still fails
   later, but with a different, less clear message.

## Outcome

- Importing `advisor.agent` (and `advisor.catalogue`, `advisor.guardrails`)
  does not import `langfuse` or `opentelemetry`, and a test proves it: it
  fails on today's `main`.
- A run with Langfuse unreachable prints nothing about span export on
  stderr unless `--debug` is given; stdout and the exit code are unchanged.
  A test proves both cases.
- Mutants R20, L5, L6 and C13, re-applied to the fixed code, are each killed
  by a named test.

## Constraints

- Behaviour stays as spec §1 defines it (B1–B26). This fix adds tests and
  moves code; it changes no answer, refusal, exit code or trace content.
- Architecture boundaries in `CLAUDE.md` hold; `tests/test_boundaries.py`
  keeps enforcing that `langfuse` is imported only in `tracing.py`. If the
  fix moves the `Tracer` protocol, `CLAUDE.md` → "Architecture" says where.
- No live network in the suite (`tests/conftest.py` blocks sockets); the
  stderr case is tested with a faked or refused exporter, not a real
  Langfuse.
- No new dependency.
- Out of scope:
  - `plan.md` in `intents/1-stack-and-skeleton/` still naming
    `models/anthropic.py` (round 4, LOW): an old intent folder is not
    rewritten (`intents/README.md` → "Types").
  - The pass-9 rule round 4 proposed for `REVIEW-POLICY.md`: a policy edit,
    not a product defect.
  - Moving to Langfuse v4 (§4).
  - Recording the model input on traces.

## Type-specific questions

### Fix
- **What broke:** see Problem items 1–5. Observed: the agent module pulls in
  the Langfuse SDK, and a successful run prints an export error when
  Langfuse is down. Untested: the three surviving mutant groups. Expected:
  the pure modules import no SDK; stderr is quiet unless `--debug`; every
  changed behavioural line has a test that fails without it.
- **Since when:** §1 (merge 21578e4); the lines come from its build, and
  the findings from its review rounds 1–4.
- **Impact:** no user saw a wrong answer and no data leaked. The cost:
  - a misleading stderr line when Langfuse is down;
  - an architecture claim the next intent would rely on but that isn't true;
  - a guardrail block that a future intent could mis-trace without any test
    failing.
- **Reproduction:**
  1. `uv run python -c "import advisor.agent, sys; print('langfuse' in sys.modules)"`
     prints `True`.
  2. With `LANGFUSE_*` set and no Langfuse listening on `LANGFUSE_HOST`,
     `uv run advisor "test"` prints the export-failure line on stderr.
  3. For each of R20, L5, L6 and C13, apply the mutant (in round 3's
     `review.md` history, and round 1's for L5, L6 and C13), run
     `uv run pytest -q`: green.
- **The test that will fail first:**
  - `tests/test_boundaries.py`: a new test that imports `advisor.agent` in a
    fresh interpreter and asserts `langfuse` is not in `sys.modules`;
  - then a CLI test asserting stderr has no export-failure text without
    `--debug`.

## Assumptions I made

- **Type fix, not refactor or feature.** Items 1 and 2 are live gaps between
  the documented and actual behaviour, each with a test that fails first.
  Items 3 to 5 are test gaps fixed in the same change. If you'd rather keep
  "fix" for user-visible defects only, item 1 alone is a refactor.
- `follows_up: 1`: all five come from §1's change, so the scan counts this as
  a follow-up of an auto-run, Reviewed-tier change.
- Item 2's expected behaviour is "silent unless `--debug`", not "replace the
  line with our own one-line warning". The spec has no rule either way; the
  plan can choose, or you can.
- The plan picks how to break the import (move `Tracer`/`NoopTracer` to an
  SDK-free module, or import `Langfuse` lazily inside `tracing.py`).
- Out of scope as listed: the stale path in §1's `plan.md` and the pass-9
  policy rule. If you want the pass-9 rule, it fits a separate `--adjust`
  intent.
