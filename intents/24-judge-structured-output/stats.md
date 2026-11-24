<!-- generated-by: product-advice-agent/deliver@0.2.0 -->
# §24 stats

Derived totals only (no prompt or response text). Regenerate live with `npm run stats -- 24`.

```text
§24
  phase            elapsed  coord work  agent work   gate wait  in-session        idle
  spec               2h41m         52s          0s       2h00m          0s         38m
      coordinator claude-opus-5-5: in 22 out 6.4k cr 1.9M cw 26.1k
  plan                 10m         18s          0s          1s          0s          0s
  build                15m          4m         43m          0s          0s          0s
      coordinator claude-opus-5-5: in 26 out 15.7k cr 4.2M cw 43.9k
      agents claude-sonnet-5-5: in 72 out 21.7k cr 1.6M cw 120.6k
  review             1h27m          8m         46m          0s          0s          0s
      coordinator claude-opus-5-5: in 34 out 13.8k cr 8.2M cw 22.7k
      agents claude-opus-5-5: in 118 out 43.4k cr 4.3M cw 359.6k
  live check            0s          0s          0s          0s          0s          0s
  ship                  3m          6s          0s          0s          0s          0s
  total              4h38m         14m       1h29m       2h00m          0s         38m
      coordinator claude-opus-5-5: in 82 out 35.9k cr 14.3M cw 92.7k
      agents claude-opus-5-5: in 118 out 43.4k cr 4.3M cw 359.6k
      agents claude-sonnet-5-5: in 72 out 21.7k cr 1.6M cw 120.6k
```
