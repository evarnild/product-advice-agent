<!-- generated-by: product-advice-agent/deliver@0.2.0 -->
# §28 stats

Derived totals only (no prompt or response text). Regenerate live with `npm run stats -- 28`.

```text
§28
  phase            elapsed  coord work  agent work   gate wait  in-session        idle
  intent                0s          0s          0s          0s          0s          0s
  spec                 24m          6s          0s         17m          0s          0s
      coordinator claude-opus-5-5: in 6 out 1.8k cr 839.9k cw 9.8k
  plan                 19m         14s          0s          1s          0s          0s
  build                36m          0s       2h13m          0s          0s          0s
      agents claude-sonnet-5-5: in 248 out 94.1k cr 16.5M cw 363.6k
  review             2h11m          2m         19m          0s          0s          0s
      coordinator claude-opus-5-5: in 14 out 5.3k cr 4.4M cw 5.0k
      agents claude-opus-5-5: in 128 out 52.3k cr 6.8M cw 714.2k
  live check         7h31m         28s          0s         52s          0s          0s
      coordinator claude-opus-5-5: in 10 out 1.7k cr 414.7k cw 66.7k
  ship                  2m          2m          0s         30s         30s          0s
      coordinator claude-opus-5-5: in 4 out 237 cr 100.8k cw 1.4k
  total             11h05m          5m       2h32m         18m         30s          0s
      coordinator claude-opus-5-5: in 34 out 9.0k cr 5.8M cw 82.8k
      agents claude-opus-5-5: in 128 out 52.3k cr 6.8M cw 714.2k
      agents claude-sonnet-5-5: in 248 out 94.1k cr 16.5M cw 363.6k
```
