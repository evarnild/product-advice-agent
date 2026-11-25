<!-- generated-by: product-advice-agent/deliver@0.2.0 -->
# §30 stats

Derived totals only (no prompt or response text). Regenerate live with `npm run stats -- 30`.

```text
§30
  phase            elapsed  coord work  agent work   gate wait  in-session        idle
  build              1h27m          1m         48m         33m          0s          0s
      coordinator claude-sonnet-5-5: in 30 out 7.4k cr 2.0M cw 149.0k
      agents claude-sonnet-5-5: in 58 out 15.5k cr 1.1M cw 101.1k
  review             1h25m          2m         45m         38m          0s          0s
      coordinator claude-sonnet-5-5: in 14 out 4.0k cr 2.1M cw 6.3k
      agents claude-opus-5-5: in 192 out 55.9k cr 5.5M cw 296.7k
  live check           27m          8s          0s         18m          0s          0s
      coordinator claude-sonnet-5-5: in 6 out 736 cr 1.1M cw 1.1k
  ship                  4m          4m          0s          7s          0s          0s
      coordinator claude-sonnet-5-5: in 4 out 229 cr 533.2k cw 1.4k
  total              3h24m          8m       1h34m       1h31m          0s          0s
      coordinator claude-sonnet-5-5: in 54 out 12.3k cr 5.7M cw 157.8k
      agents claude-opus-5-5: in 192 out 55.9k cr 5.5M cw 296.7k
      agents claude-sonnet-5-5: in 58 out 15.5k cr 1.1M cw 101.1k
```
