# Judge validation: judge-no-fit

**Verdict: not trusted.** true-positive rate 0.60 is below 0.80; 9 judged conversations; at least 30 are needed; 4 owner fails; at least 10 are needed.

- Model: claude-haiku-5-5
- Prompt sha256: d007ff8ce76d290b742b542d1b6ef53f0610e2984b37fefe0c323b34fee3213f
- Few-shot examples: 8
- Held-out conversations: 9 (9 with a verdict, 0 judge errors)
- True-positive rate (owner pass, judge pass / owner pass): 0.60 (3/5)
- True-negative rate (owner fail, judge fail / owner fail): 1.00 (4/4)

| | judge pass | judge fail |
| --- | --- | --- |
| owner pass | 3 | 2 |
| owner fail | 0 | 4 |

## Disagreements and judge errors

- 20261113T072503Z-ollama.jsonl#gen-budget-too-low-11: owner pass, judge fail
  - judge: No search was run, so nothing has been shown to fit, yet the answer never says plainly that nothing fits; it promises to 'check for cheaper options' without checking and only asks for more details.
- 20261113T070516Z-anthropic.jsonl#gen-budget-too-low-5: owner pass, judge fail
  - judge: Nothing under 50 euros with ANC was found, and the answer says so honestly, but it then offers two headphones that do not serve the need: both lack noise cancelling and cost more than the 50 euro ceiling (59 and 79 euros).

## Skipped

- 20261116T094326Z-ollama.jsonl#gen-no-match-1: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-2: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-3: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-4: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-5: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-6: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-7: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-8: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-9: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-no-match-10: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-6: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-7: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-8: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-9: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-10: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-11: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-12: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-13: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-14: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094326Z-ollama.jsonl#gen-budget-too-low-15: no report 20261116T094326Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-budget-too-low-12: no report 20261116T094558Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-budget-too-low-13: no report 20261116T094558Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-no-match-2: no report 20261116T094558Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-no-match-3: no report 20261116T094558Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-no-match-4: no report 20261116T094558Z-ollama.json or no such case in it
- 20261116T094558Z-ollama.jsonl#gen-no-match-5: no report 20261116T094558Z-ollama.json or no such case in it
