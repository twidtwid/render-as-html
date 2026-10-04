# Agent-friendly architecture spikes (throwaway)

These scripts are decision instruments for Phase 1. They are not production code and they are not a refactor.

## What they proved

`replay-failures.mjs` reconstructs 14 historical failure fixtures and runs `scripts/lint-artifact.mjs` against today's gates.

- 12 mechanical cases failed the lint, as required.
- 2 judgment cases (wrong shape, wrong chart primitive) passed the lint. That gap is real.

`measure-contracts.mjs` sizes SKILL.md, `references/`, and examples.

- SKILL.md is 12241 approx tokens, matching `perf/baseline.json`.
- 8 of 12 shape references are 13-line stubs.
- 4 shape references are thick (editorial, podcast, execution-log, deck-review).
- `check-versions.mjs` does not watch `examples/execution-log.html` or `examples/deck-review.html`, both of which stamp v2.8.0.
- Plan 009 already shipped as `5b4af3f` while `plans/README.md` still says TODO.

`lint-against.mjs` is a sketch of `lint-artifact --against <prior.html>`.

- Same file vs itself exits 0.
- A dashboard copy that drops `id="search"` and `id="donut-svg"` exits 1 with those dropped ids.
- A dashboard copy that removes copy-as-prompt wording exits 1.

Rerun from repo root.

```
node spikes/agent-friendly/replay-failures.mjs
node spikes/agent-friendly/measure-contracts.mjs
node spikes/agent-friendly/lint-against.mjs examples/dashboard.html examples/dashboard.html
```
