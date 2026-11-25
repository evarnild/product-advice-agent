<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §33 plan — Do not invent a price cap the customer never gave

Intent: [intent.md](intent.md) · Spec: none (fix: the intent is the spec)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

The system prompt gains one rule, in the shape of its `in_stock_only` rule:
set `max_price` or `min_price` only when the customer states an amount, and
never turn "cheap", "budget" or "affordable" into a price filter. A wording
test pins the rule. The proof that the model follows it is an eval run on
the default Ollama model (qwen3:8b): `sport-earbuds` and `gaming-monitor`
search without `max_price`, and the 30 cases whose question states an
amount still set one. No change to the tool schema, the agent loop or the
eval cases (intent → Constraints).

## Risks

- **A test that passes whatever the model does.** The wording test only
  proves the sentence is in the file. The model's behaviour is proven by
  the eval evidence under Validation, not by `verify`. The review must not
  treat a green suite as proof of the outcome.
- **Overcorrection.** A rule against price filters can make the model drop
  the cap on stated amounts too ("About 900 euros at most", "Maybe up to
  1000 euros", "budget is 500 max"). 30 of 50 cases expect a price filter
  in `expect_search`; a dropped cap fails their `search` check. Validation
  counts them on the full run.
- **Noise.** `gaming-monitor` set `max_price: 300` in 3 of 10 runs (intent →
  Problem); one passing `--only` run says little. The repetition count is
  fixed below, before the run, so it cannot be chosen after seeing results.
- **Budget talk from another line.** `system.md:21-22` tells the model to
  "suggest how the customer could widen the search (a higher budget, another
  category)". With no cap set, "consider increasing your budget" should not
  arise, but this line may still produce it after an empty search. The
  intent says a separate rule is added only if needed; the live check looks
  for it, and if it shows, it is a finding, not a silent extra rule.
- **Out-of-scope flips.** `sport-earbuds` also sets `in_stock_only: True`
  unasked (intent → Out of scope), and its keywords `running`, `wireless`
  must still surface P-002. It may search without a cap and still fail.
  That is reported with its reason, not reworked here.
- **Stale line citations.** Re-check the lines below before launch;
  `system.md` is short and every line shifts with the insertion.
- REVIEW-POLICY.md pass 9 lists no repository-specific footguns yet. There
  is no lint warning cap.

## Verified against the codebase

Re-read on `main` at `2e3b7f4`.

- `src/advisor/prompts/system.md:6-8` — "Use the `search_products` tool to
  look products up. Call it with the category, price range, keywords and
  stock filter that match what the customer asked for. You may call it more
  than once." (the only place the prompt mentions price filters; unchanged)
- `src/advisor/prompts/system.md:12-14` — "Set `in_stock_only` only when the
  customer asks for products in stock; otherwise leave it off, so an
  out-of-stock match can still be named and flagged." (the shape to copy;
  the new rule goes directly after it, before line 15)
- `src/advisor/prompts/system.md:15-16` — "A row with `keywords_matched` 0
  does not have the features asked for: say so, and do not present it as a
  fit."
- `src/advisor/prompts/system.md:21-22` — "If the tool returns nothing that
  matches, say so plainly and suggest how the customer could widen the search
  (a higher budget, another category)." (left as is; see Risks)
- `src/advisor/agent.py:61-62` — `"min_price": {"type": "number",
  "description": "Minimum price in euros."}`, `"max_price": ... "Maximum
  price in euros."` (the tool schema; not changed, per the intent's
  constraint "No change to the tool schema")
- `src/advisor/agent.py:32` — `SYSTEM_PROMPT_PATH = Path(__file__).parent /
  "prompts" / "system.md"`; `:53-54` `load_system_prompt` reads it.
- `tests/test_agent.py:365-370` —
  `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked`:
  `text = " ".join(load_system_prompt().split())`, then asserts the exact
  sentence is `in text` (the pattern the new test copies; §22).
- `tests/test_agent.py:356-362` and `:453-458` — the two other prompt-wording
  tests, same pattern.
- `src/advisor/evals/score.py:120-131` — `_call_satisfies`: `max_price`
  passes when the call's value is a number `<=` the expected one;
  `min_price` when a number `>=`; a missing key fails. So a stated-amount
  case whose search drops its cap fails `search`.
- `src/advisor/evals/run.py:185` — `--only` "comma-separated case ids to
  run"; `:237-241` rejects unknown ids.
- `src/advisor/evals/baseline.py:15-16` — `EVAL_PATHS` starts with
  `"src/advisor/prompts/"`: the change owes an eval run.
- `src/advisor/tracing.py:88-96` — `tool(...)` writes the tool observation
  with `input=arguments`: the Langfuse trace shows the search's arguments.
- `src/advisor/cli.py:42-55, 65-70` — `--debug` only sets up logging (root
  WARNING to stderr, `advisor` logger DEBUG); `agent.py` logs nothing, so
  `--debug` does **not** show the search arguments. The live check reads
  them from the trace or an eval report instead.
- `src/advisor/config.py:22` — `DEFAULT_MODELS = {"ollama": "qwen3:8b", ...}`.
- `evals/cases.jsonl:2` — `sport-earbuds`: "Cheap wireless earbuds for
  running?", `expect_ids ["P-002"]`, `expect_search {"category":
  "headphones"}`.
- `evals/cases.jsonl:7` — `gaming-monitor`: "I want a monitor for gaming",
  `expect_ids ["P-019"]`, `expect_search {"category": "monitor",
  "keywords_any": ["gaming"]}`.
- `evals/cases.jsonl:1, 3, 21` — `nc-headphones-under-200` (`max_price
  200`), `student-laptop` (`max_price 700`), `laptop-uni-backpack-900`
  ("About 900 euros at most.", `max_price 900`); 30 of the 50 cases carry
  `max_price` or `min_price` in `expect_search` (counted on this commit).
- `evals/cases.jsonl:40` — `norvik-fold-cheap-student` ("im a student so i
  cant really spend much, is it cheap?", `expect_ids ["P-017"]`): set
  `max_price: 200` in each of the 6 qwen3:8b full runs of 2026-11-24 checked. Not named in
  the intent; watched as a likely flip.
- `src/advisor/data/catalogue.json` — P-002 Auralis Pulse Buds €79 in stock;
  P-019 Lumino Game 32 €449 in stock; P-017 Norvik Fold €1499, out of stock.
- `evals/runs/20261124T215703Z-ollama.json` (qwen3:8b, 38/50) —
  `sport-earbuds` FAIL with `{'category': 'headphones', 'keywords':
  ['running', 'wireless'], 'max_price': 50, 'in_stock_only': True}`;
  `gaming-monitor` FAIL with `{'category': 'monitor', 'keywords':
  ['gaming'], 'max_price': 300}`, answer "within your price range".
- `evals/baseline.json` — source `20261124T215703Z-ollama.json`,
  `prompt_sha256 071fd576…`, which is the LF hash of today's `system.md`:
  the kept runs were made on the prompt this fix changes, so they are the
  "before" evidence.

## Subtasks

1. **Wording test, failing first, then the rule** (one commit, verify
   green).
   - Add to `tests/test_agent.py`, after
     `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked`:
     `test_prompt_tells_the_model_to_set_a_price_filter_only_for_a_stated_amount`,
     same normalisation (`" ".join(load_system_prompt().split())`),
     asserting the exact sentence below is `in text`.
   - Run `uv run pytest tests/test_agent.py -k stated_amount` and see it
     fail on the unchanged prompt; note it in Progress.
   - Insert after `system.md:14` (inside the first bullet, two-space
     indent like its neighbours):

     ```
       Set `max_price` or `min_price` only when the customer states an
       amount, such as "under 200 euros", "about 900 euros" or "500 max";
       otherwise leave both off. Words such as "cheap", "budget" or
       "affordable" are not an amount and never set a price filter.
     ```

     The test asserts the whole four-line sentence pair as one normalised
     string. Lines 6-8 ("price range ... that match what the customer asked
     for") stay as they are.
   - `npm run verify` green; commit.
2. **Hand over.** Append the Progress entry (commit, the failing-first
   output, test count), set `status: in-review` in `metadata.yml`, commit.
   The implementer does not run the evals or call a model; the coordinator
   does (REVIEW-POLICY.md → "Eval runs" → "Who runs it").

## Tests

- **Failing-first (fix):** the new wording test fails on `main`'s prompt
  (the sentence is absent) and passes after subtask 1. The behavioural
  failing-first is the eval case `sport-earbuds`, which set `max_price: 50`
  on every kept qwen3:8b run of today's prompt, and `gaming-monitor`
  (`max_price: 300` in 3 of 10); see Validation.
- **Mutations, per changed line:**
  - delete or reword any of the four new prompt lines (e.g. drop "only",
    drop "or `min_price`", drop "cheap", change "never" to "may") → killed
    by the new wording test (exact substring).
  - move the lines out of the `search_products` bullet → survives the
    wording test (it ignores layout); accepted, layout is not behaviour the
    suite can judge.
  - the model ignoring the rule → not killable in `verify`; only the eval
    evidence and the live check show it.
- Existing tests stay unchanged: `test_system_prompt_file_content`
  (`tests/test_agent.py:177-180`) and the three wording tests still pass.
- No fake or socket is needed; the test reads the shipped file.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS (a fix with a test changed).
- **Eval run (coordinator, owed: `src/advisor/prompts/` is in
  `EVAL_PATHS`).** In the worktree at the reviewed commit, Ollama with the
  default model `qwen3:8b`:
  1. Full run: `uv run advisor-eval --provider ollama`; copy the report to
     the main checkout's `evals/runs/`. Then `uv run advisor-analysis hashes
     <report>` (must match) and `uv run advisor-analysis compare <report>`
     (list every flip).
  2. Repetitions: `uv run advisor-eval --provider ollama --only
     sport-earbuds,gaming-monitor` **10 times**. Reason: `gaming-monitor`
     capped in 3 of 10 runs before; 0 caps in 10 runs has about a 3% chance
     (0.7^10) if nothing changed, 0 in 5 about 17%. Each run is two cases,
     about 20 to 110 s by the kept runs' timings.
  3. Read the caps per report:
     `uv run python -c "import json,sys; r=json.load(open(sys.argv[1],encoding='utf-8')); [print(c['id'], c['status'], [{k: s[k] for k in ('max_price','min_price') if k in s} for s in c['searches']]) for c in r['cases']]" <report>`
  4. Stated amounts keep their cap (on the full run):
     `uv run python -c "import json,sys; cs={d['id']: d for d in map(json.loads, filter(str.strip, open('evals/cases.jsonl',encoding='utf-8')))}; r=json.load(open(sys.argv[1],encoding='utf-8')); p=('max_price','min_price'); want=lambda i: any(k in (cs[i].get('expect_search') or {}) for k in p); cap=lambda c: any(k in s for s in c['searches'] for k in p); print('stated, no cap:', [c['id'] for c in r['cases'] if want(c['id']) and not cap(c)]); print('no amount, cap:', [c['id'] for c in r['cases'] if not want(c['id']) and cap(c)])" <report>`
  - **Pass for the outcome:** no search of `sport-earbuds` or
    `gaming-monitor` carries `max_price` or `min_price` in any of the 11
    observations (full run + 10 `--only`); "stated, no cap" is empty, or
    each case in it is re-run with `--only` per the noise rule and explained
    in the review; "no amount, cap" is empty or explained (watch
    `norvik-fold-cheap-student`). PASS/FAIL of the two cases is reported
    separately: a FAIL without a cap (for example from `in_stock_only` or
    the keywords) is explained, not reworked under this intent.
  - Every PASS→FAIL flip in `compare` is re-run with `--only` before it is
    called a regression, and a confirmed one is a "Needs decision" finding.
- **Live check (owed: rule 1, `src/advisor/prompts/`).** The owner, in the
  worktree, with Ollama running the default model and the local Langfuse up
  (`docker compose -f infra/langfuse/docker-compose.yml up -d`, the three
  `LANGFUSE_*` variables in `.env`). `--debug` does not show the search, so
  read the `search_products` tool observation's input in each run's trace at
  http://localhost:3000.
  1. `uv run advisor "Cheap wireless earbuds for running?"` — the search has
     no `max_price`/`min_price`; the answer does not speak of "your budget"
     or "your price range"; ideally it names Auralis Pulse Buds (P-002) at
     €79.
  2. `uv run advisor "I want a monitor for gaming"` — no price filter; no
     budget talk; ideally Lumino Game 32 (P-019) at €449 among the options.
  3. `uv run advisor "Any affordable bluetooth speaker for the kitchen?"` (a
     phrasing not in the evals) — no price filter.
  4. `uv run advisor "A tablet for drawing, about 300 euros"` — the search
     **does** carry a `max_price` (at or near 300).
  - If Langfuse is not running: run step 2 of the eval list once and read
    `searches` with the command in step 3; that shows the arguments for the
    two eval questions, but not for live steps 3 and 4.
  - You should see: no invented cap in 1 to 3, a cap in 4, no mention of a
    budget the question did not give. Then `live_checked` is recorded at
    your word.

## Assumptions I made

- The rule goes only in `system.md`. The intent allows a line in the
  `max_price` description in `agent.py`, but its constraint "No change to
  the tool schema" rules that out, and keeping `agent.py` out of the diff
  keeps core code untouched.
- The same sentence covers `min_price` (intent → Assumptions), though no
  failure shows an invented minimum.
- No separate "do not mention a budget" rule (intent: "not a separate rule
  unless the plan finds it needs one"); `system.md:21-22` stays. The live
  check and the eval answers decide whether a follow-up is needed.
- The examples in the rule ("under 200 euros", "about 900 euros", "500
  max") are taken from the intent's constraint and cases; they are not the
  eval questions verbatim, so the model is not being fed answers to
  `sport-earbuds` or `gaming-monitor`.
- The kept qwen3:8b runs (prompt hash equal to `evals/baseline.json`) serve
  as the "before" evidence; no fresh run on `main` is needed.
- 10 `--only` repetitions, chosen before the run (reason under Validation).

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
