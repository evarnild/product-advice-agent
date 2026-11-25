<!-- generated-by: product-advice-agent/intent@0.3.0 -->
# §33 — Do not invent a price cap the customer never gave

**Type:** fix
**Originator:** the coordinator's analysis of 10 qwen3:8b eval runs of the
50 cases, for the owner ("write intents")
**Source:** `evals/runs/20261124T215703Z-ollama.json` (latest) and the nine
earlier qwen3:8b runs `evals/runs/2026112*-ollama.json`

## Problem

The model sets `max_price` on `search_products` when the customer gave no
amount, and the cap hides the product that fits.

- `sport-earbuds` ("Cheap wireless earbuds for running?") failed all 10
  runs, each time with the search `{'category': 'headphones', 'keywords':
  ['running', 'wireless'], 'max_price': 50, 'in_stock_only': True}` (latest
  run). The expected P-002 Auralis Pulse Buds ("Compact in-ear wireless
  earbuds for sport, sweat resistant") costs €79, so the cap removes the
  only sport earbuds in the catalogue. The answer lists four budget
  headphones from €19 to €49, none for sport. Check: `expected` "does not
  cite P-002".
- `gaming-monitor` ("I want a monitor for gaming") failed 3 of 10 runs,
  including the last two, each time with `max_price: 300`; the 7 passing
  runs set no cap. The expected P-019 Lumino Game 32 costs €449. The latest
  answer even says "within your price range" and "consider increasing your
  budget", though the customer stated none.

The customer gets cheaper, worse-fitting products and is told about a
budget they never set.

## Outcome

- The system prompt (`src/advisor/prompts/system.md`) tells the model to
  set `max_price` (and `min_price`) only when the customer states an
  amount, in the same shape as its rule for `in_stock_only`.
- An eval run (`REVIEW-POLICY.md` → "Eval runs") shows `sport-earbuds` and
  `gaming-monitor` searching without a `max_price`, and the cases that do
  state an amount (e.g. `nc-headphones-under-200`, `student-laptop`,
  `laptop-uni-backpack-900` "About 900 euros") still setting one.
- Any case that flips is explained in the review.

## Constraints

- The change is the prompt's wording. No change to the tool schema, the
  agent loop or the eval cases.
- `src/advisor/prompts/**` is Reviewed tier by meaning ("model prompts and
  agent instructions the product ships", `REVIEW-POLICY.md` path table),
  and owes a live check under rule 1 ("`src/advisor/prompts/` (the prompt
  the model runs on)"). It also owes an eval run (`src/advisor/prompts/`
  is in `EVAL_PATHS`).
- "Cheap", "budget", "affordable" are not stated amounts: they may order
  or describe the results, never set `max_price`. "About 900 euros",
  "maybe up to 1000", "500 max" are stated amounts and keep their cap.
- Unit tests cannot prove a prompt change: the model's behaviour is not in
  the suite. The failing-first evidence is the two eval cases, run before
  and after the change with `uv run advisor-eval --provider ollama --only
  sport-earbuds,gaming-monitor`; `sport-earbuds` fails on every run today.
  A wording test like
  `test_prompt_tells_the_model_to_set_in_stock_only_only_when_asked`
  (`tests/test_agent.py`) pins the new rule but proves nothing about the
  model.
- The answer must not mention a budget the customer did not give; this
  follows from no cap being set and is not a separate rule unless the plan
  finds it needs one.
- Out of scope: §31 (answers without any search), §30 (out-of-stock
  answers), and the `in_stock_only: True` that `sport-earbuds` also sets
  without being asked (noted, not fixed here).

## Type-specific questions

### Fix
- **What broke:** observed: `max_price: 50` for "cheap" and `max_price:
  300` with no budget at all. Expected: no `max_price` unless the
  customer gives an amount.
- **Since when:** not introduced by a change; the prompt has never said
  when to set a price filter ("Call it with the category, price range,
  keywords and stock filter that match what the customer asked for").
  `sport-earbuds` has failed on every qwen3:8b run kept.
- **Impact:** the customer is steered to cheaper, unsuitable products and
  told about a budget they never set. In the evals, 1 to 2 of 50 cases per
  run. No data leak.
- **Reproduction:** `uv run advisor-eval --provider ollama --only
  sport-earbuds,gaming-monitor`; read `searches` in the report.
- **The test that will fail first:** the eval cases `sport-earbuds`
  (always) and `gaming-monitor` (3 of 10 runs) in the `--only` run above,
  before the change; after it, both search without `max_price`. Plus a
  wording test in `tests/test_agent.py` that the prompt holds the new rule.

## Assumptions I made

- The `sport-earbuds` case stays as it is: P-002 at €79 is a fair answer to
  "cheap" for sport earbuds, since it is the only sport model and "cheap"
  gives no amount. Loosening the case is not part of this fix.
- The same rule covers `min_price`, though no failure shows it today.
- The rule goes in the system prompt, not the tool's `max_price`
  description in `agent.py`; the plan may add a line there too, which
  would make `agent.py` (core code) part of the diff.
- Because `gaming-monitor` fails only some runs, one `--only` run that
  passes is weak evidence for it; the full eval run and the noise rule in
  `REVIEW-POLICY.md` decide.
- `follows_up` is left empty: no earlier intent introduced this.
