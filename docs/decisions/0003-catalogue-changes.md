# 0003 — Rules for changing the catalogue

Status: accepted with intent §13 (2026-11-13). Spec: `intents/13-catalogue-change-rules/spec.md`.

Adds rules to the "small committed JSON catalogue" of [0001](0001-stack.md);
supersedes nothing.

## Decision

| Question | Rule |
| --- | --- |
| Ids | Ids only grow. A new product takes the next free `P-NNN`. An id is never reused or renumbered. |
| Retiring a product | Delete it from `src/advisor/data/catalogue.json`. Its id is retired for good. There is no tombstone or `retired` field. |
| Size of a change | A change to a few products' price, stock, specs or wording is an **adjustment**. Adding many products, a category or a field is a **feature** (a category or a field touches core code). |
| Cases | The change that breaks a case fixes the case in the same branch. `tests/test_evals_cases.py::test_committed_cases_are_consistent_with_the_catalogue` runs `catalogue_problems` and fails `npm run verify` naming the case and the product. |
| Old records | Run reports, labels and taxonomies are records of their run and are not redone. A report's `catalogue_sha256` (bytes of the catalogue file) says which catalogue it saw; reports without it predate this rule. |
| Eval run | A catalogue change owes an `advisor-eval` run whose report the review names. Enforcing it is intent §17 (evals on every change); until then the reviewer checks. |

## Consequences

- The check covers `evals/cases.jsonl` only, and only cases with
  `expect_search`. An expected product must be matched by the case's filters
  and rank within the first 10 results; a forbidden one must not be matched.
- A case that relies on stock without `in_stock_only` is not checked for it.
- Growing the catalogue (§14) is checked by the same test.
