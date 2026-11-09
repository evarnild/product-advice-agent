# product-advice-agent

A small product-advice agent for a synthetic electronics catalogue, with evaluation, tracing and guardrails.

Run with the AI-native SDLC from the start.

So far the repository holds only the process kit. What gets built, and with
which stack, is decided by §1. See [`sdlc.md`](sdlc.md) for how a change
moves from intent to merge, [`OVERVIEW.md`](OVERVIEW.md) for the snapshot,
and `npm run queue` for what is queued.

```
npm run verify        # the one check before a change is done
npm run check:intent  # does this branch match its intent?
npm run queue         # every intent by status, generated from metadata.yml
```

The kit needs Node ≥ 22 and nothing else.
