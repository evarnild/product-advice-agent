<!-- generated-by: product-advice-agent/deliver@0.2.0 -->
# §31 stats

Derived totals only (no prompt or response text). Regenerate live with `npm run stats -- 31`.

```text
§31
  phase            elapsed  coord work  agent work   gate wait  in-session        idle
  build                12m         18s         32m          3m          0s          0s
      coordinator claude-sonnet-5-5: in 8 out 1.1k cr 505.3k cw 3.6k
      agents claude-sonnet-5-5: in 42 out 12.0k cr 729.4k cw 85.5k
  review               47m          9m         10m         12m          1m          0s
      coordinator claude-sonnet-5-5: in 20 out 7.2k cr 1.9M cw 7.6k
      agents claude-opus-5-5: in 100 out 33.9k cr 2.5M cw 125.5k
  live check           28m          3m          0s         20m          0s          0s
      coordinator claude-sonnet-5-5: in 14 out 2.3k cr 1.8M cw 12.6k
  ship                  4m          3m          0s         36s          0s          0s
      coordinator claude-sonnet-5-5: in 4 out 229 cr 377.8k cw 1.8k
  total              1h33m         17m         43m         36m          1m          0s
      coordinator claude-sonnet-5-5: in 46 out 10.9k cr 4.5M cw 25.6k
      agents claude-opus-5-5: in 100 out 33.9k cr 2.5M cw 125.5k
      agents claude-sonnet-5-5: in 42 out 12.0k cr 729.4k cw 85.5k
```
