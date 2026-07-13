# Plan 006: Tighten the HTML-native feature gate, dead-control scan, and hex matching so the QA gates can't pass vacuously

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- scripts/perf_harness.py scripts/lint-artifact.mjs scripts/check-tokens.mjs tests/ perf/baseline.json`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (stricter patterns may reclassify existing artifacts — the steps below verify against every committed example before landing)
- **Depends on**: plans/005-perf-harness-honest-metrics.md (lands a slim baseline this plan regenerates); do BEFORE plans/009 (which consolidates the vocabulary this plan finalizes)
- **Category**: correctness
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

The "≥3 HTML-native features" floor is the load-bearing "is this a real artifact or styled prose" test, enforced by both `scripts/lint-artifact.mjs` (hard FAIL) and `scripts/perf_harness.py` (feature counts + warnings). But several feature detectors are bare word matches: the word "search", "toggle", or "highlight" in prose, a CSS `filter:` declaration, or a `.chip` class name each count as an interactive feature. A document that merely *mentions* these words clears the floor with zero actual interactivity — the gate gives more assurance than it earns. Two adjacent blind spots in the same tools: the dead-control scan misses `querySelectorAll` and compound selectors (`querySelector('#a .b')` is silently unchecked), and `check-tokens.mjs` only sees 6-digit hex, so a shorthand/alpha token could drift invisibly.

## Current state

- `scripts/perf_harness.py:552-564` — the Python vocabulary:
  ```python
  _HTML_NATIVE_FEATURES = {
      "search": r"type=[\"']search[\"']|\bsearch\b",
      "inline_svg": r"<svg\b",
      "table": r"<table\b",
      "copy_as_prompt": r"copy as prompt|copyPrompt|prompt-output",
      "sorting": r"\bsort(?:able|ing)?\b|data-sort",
      "filtering": r"\bfilter(?:ed|ing)?\b|chip\b",
      "local_storage": r"localStorage",
      "drag": r"\bdraggable\b|dragstart|dragover|drop\(",
      "toggle": r"aria-pressed|type=[\"']checkbox[\"']|\btoggle\b",
      "textarea": r"<textarea\b",
      "cross_highlight": r"highlight|scrollIntoView|IntersectionObserver|scroll-spy|scrollspy",
  }
  ```
- `scripts/lint-artifact.mjs:43-56` — the JS mirror, prefixed by the comment `// Same feature vocabulary as perf_harness.py's _HTML_NATIVE_FEATURES.` Keep that sync (both files change identically in this plan; plan 009 later single-sources it).
- Consumers of the vocabulary:
  - `scripts/lint-artifact.mjs:129-131` — hard FAIL below 3 features.
  - `scripts/perf_harness.py:578-579` (`_feature_hits`), `:590-592` (per-file counts), `:616-621` (`low_feature_files` for shape examples, surfaced as warnings at `:679-680`, NOT hard violations).
  - `tests/test_perf_harness.py:79` asserts counts exist; `tests/test_linters.py` fixtures rely on `type="search"`+`<svg>`+`<table>` totaling ≥3 (e.g. lines 84-85: `<svg></svg><input type="search"><table></table>`) — these remain detected under the tightened vocabulary below.
- `scripts/lint-artifact.mjs:175-181` — dead-control scan:
  ```js
  const idAttrs = new Set([...html.matchAll(/\bid\s*=\s*["']([^"']+)["']/g)].map(m => m[1]));
  const referenced = new Set();
  for (const m of scriptSrc.matchAll(/getElementById\(\s*['"]([^'"]+)['"]\s*\)/g)) referenced.add(m[1]);
  for (const m of scriptSrc.matchAll(/querySelector\(\s*['"]#([A-Za-z][\w-]*)['"]\s*\)/g)) referenced.add(m[1]);
  ```
  Misses: `querySelectorAll('#x …')`, and any `querySelector('#a .b')` (the character class stops at the space, so the whole call silently doesn't match).
- `scripts/check-tokens.mjs:27` — `const hexes = (text) => new Set((text.match(/#[0-9a-fA-F]{6}\b/g) || []).map((h) => h.toLowerCase()));` — blind to `#fff`, `#ffff`, 8-digit alpha.
- Baseline: `perf/baseline.json` (slim format after plan 005) carries `skill_md` token counts only — feature-count changes do NOT touch it, but re-run `--update-baseline` only if step 5 says so.
- 24 committed artifact pages: `index.html`, `examples/*.html` (13), `examples/primitives/*.html` (10). Current median feature hits: 5 (harness output).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Per-file feature counts | `uv run python scripts/perf_harness.py --json --no-report \| uv run python -c "import json,sys; print(json.load(sys.stdin)['source_document']['html_native_feature_counts'])"` | dict of file → count |
| Lint all examples | `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` | `… 0 fail` |
| Tokens | `node scripts/check-tokens.mjs` | `check-tokens: clean.` |
| Tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Harness gate | `uv run python scripts/perf_harness.py --check --no-report` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `scripts/perf_harness.py` (the `_HTML_NATIVE_FEATURES` dict only)
- `scripts/lint-artifact.mjs` (the `FEATURES` table + the dead-control scan)
- `scripts/check-tokens.mjs` (the `hexes` pattern only)
- `tests/test_linters.py` (new negative tests)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- Any committed example HTML. If an example drops below the floor under the new vocabulary, that is a STOP — the operator decides whether the example needs real feature markup or the vocabulary is too strict. Do not add markup to examples to make gates pass.
- The ≥3 threshold itself, `REQUIRED_META`, `EXTERNAL_RESOURCE` — unchanged.
- `SKILL.md` prose about the feature floor.

## Git workflow

- Branch: `advisor/006-tighten-quality-gates`
- One commit, imperative subject, e.g. `Tighten feature-floor vocabulary, dead-control scan, and hex matching in the QA gates`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Record the before-state

Run the per-file feature counts command and save the dict (e.g. to `/tmp/features-before.json`). Also run the lint-all-examples command and confirm `0 fail`.

**Verify**: every committed artifact currently counts ≥3.

### Step 2: Tighten the vocabulary in BOTH files identically

Replace the five over-broad detectors (leave the other six keys untouched). New patterns — Python raw-string form shown; the JS regex literals use the identical source with `i` flag:

| Key | New pattern | Rationale |
|---|---|---|
| `search` | `type=[\"']search[\"']` | an actual search input, not the word "search" |
| `sorting` | `data-sort\|aria-sort=` | sort wiring/state markup, not prose "sorted" |
| `filtering` | `data-filter\|class=[\"'][^\"']*\bchip\b` | filter-chip markup, not CSS `filter:` or prose |
| `toggle` | `aria-pressed\|type=[\"']checkbox[\"']` | real toggle state/control, not the word |
| `cross_highlight` | `scrollIntoView\|IntersectionObserver\|classList\.(?:add\|toggle)\(` | behavioral JS, not the word "highlight" |

Update the sync comment in `lint-artifact.mjs:43` to keep saying the vocabularies match.

**Verify**: `node --check scripts/lint-artifact.mjs` → exit 0; `uv run python -c "import re; import runpy"`-level syntax: `uv run python scripts/perf_harness.py --no-report >/dev/null` → exit 0.

### Step 3: Re-measure and compare

Re-run the per-file counts and diff against `/tmp/features-before.json`. Counts will drop (that's the point). Requirements:

- Every **shape artifact** in `examples/*.html`, and the root `index.html`, must still count **≥3**.
- `examples/primitives/*.html` are single-primitive reference pages, linted with `--reference` (floor skipped).
- **Gallery/index pages are reference surfaces, not artifacts (ruling added during execution, 2026-07-12).** The first run correctly dropped `examples/index.html` 5→0 and `examples/primitives.html` 6→1. The reviewer inspected both: `examples/index.html` contains zero `<script>`/`<button>`/`<input>` elements (a pure static link gallery) and `examples/primitives.html` likewise carries no interactive markup — its single remaining hit came from the phrase "copy as prompt" in contract prose. They were clearing the floor purely on phantom prose matches, which is precisely the false-pass class this plan closes. **Do not add markup to them and do not weaken a pattern**; instead move both into the `--reference` lint set (see step 3a).

Include the before/after count table in your final report.

### Step 3a: Reclassify the two gallery pages as reference surfaces

In the `Makefile`'s `lint-examples` target (added by plan 002), split the globs so the two gallery pages lint with `--reference`:

```makefile
lint-examples:
	node scripts/lint-artifact.mjs index.html $(filter-out examples/index.html examples/primitives.html,$(wildcard examples/*.html))
	node scripts/lint-artifact.mjs --reference examples/index.html examples/primitives.html examples/primitives/*.html
```

(If the `$(filter-out …)` form proves awkward, an explicit list of the 13 shape examples is equally acceptable — the requirement is that the two gallery pages get `--reference` and every shape artifact keeps the full gate.)

`Makefile` is therefore IN SCOPE for this change only.

**Verify**: `make check` → all gates green, and the lint output shows the shape artifacts under the full gate (each ≥3) with the gallery + primitive pages under `--reference`.

**Verify**: lint-all-examples `0 fail`; `uv run python scripts/perf_harness.py --check --no-report` → exit 0 (feature drops appear as warnings only if any shape example goes under 3 — which would also be a STOP).

### Step 4: Extend the dead-control scan

In `scripts/lint-artifact.mjs` replace the two `referenced`-building loops with a single broader one that also covers `querySelectorAll` and compound selectors whose *leading* token is an id:

```js
for (const m of scriptSrc.matchAll(/getElementById\(\s*['"]([^'"]+)['"]\s*\)/g)) referenced.add(m[1]);
for (const m of scriptSrc.matchAll(/querySelector(?:All)?\(\s*['"]#([A-Za-z][\w-]*)/g)) referenced.add(m[1]);
```

(The second pattern intentionally drops the closing-quote anchor so `'#chart .bar'` still yields `chart`. Dynamic ids — `getElementById(varName)` — remain unverifiable by a static scan; add a one-line comment saying so.)

**Verify**: `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` → still `0 fail` (if a previously-invisible dead reference surfaces in a committed example, that is a STOP — report the file and id).

### Step 5: Widen check-tokens hex matching

In `scripts/check-tokens.mjs:27` change the pattern to `/#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g`. All three surfaces (DESIGN.md frontmatter, SKILL.md §Color, index.html) currently use only 6-digit hex, so the sets must not change.

**Verify**: `node scripts/check-tokens.mjs` → `check-tokens: clean.` with the same token counts as before the change (`DESIGN.md canonical tokens: N` unchanged).

### Step 6: Add negative tests

Append to `tests/test_linters.py` (existing `_run` helper + fixture-building style at lines 72-100):

1. `test_lint_artifact_prose_mentions_dont_count`: a meta-complete fixture whose body is prose containing the words "search", "filter", "toggle", "sort", "highlight" and a `<style>p{filter:blur(0)}</style>` — but **no** table/svg/controls. Assert exit 1 and `"HTML-native feature"` in stdout (under the old vocabulary this fixture passed with 5 phantom features).
2. `test_lint_artifact_catches_compound_selector_dead_control`: meta-complete fixture with ≥3 real features plus `<script>document.querySelector('#ghost .row');</script>` and no `id="ghost"`. Assert exit 1 and `#ghost` in stdout.
3. `test_lint_artifact_catches_querySelectorAll_dead_control`: same but `querySelectorAll('#phantom')`. Assert exit 1 and `#phantom` in stdout.

**Verify**: `uv run --with pytest pytest tests/test_linters.py -q` → all pass.

### Step 7: Full gates

**Verify**: `uv run --with pytest pytest tests/ -q` → all pass; `make check` if plan 002 has landed, else the individual gate commands; `uv run python scripts/perf_harness.py --check --no-report` → exit 0. `perf/baseline.json` needs regeneration **only** if the harness `--check` reports a change in gated fields (it should not — this plan doesn't move SKILL.md tokens); if `--check` fails on token counts, STOP.

## Test plan

Step 6's three negative tests are the core: they encode the exact false-pass modes this plan closes. Existing positive tests (`test_lint_artifact_passes_on_example`, `test_lint_artifact_passes_on_scatter_primitive`, plus every fixture in `tests/test_linters.py` using `type="search"`/`<svg>`/`<table>`) double as the no-false-positive net and must pass unmodified.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] The five detectors match the table in step 2, byte-identical semantics in both `scripts/perf_harness.py` and `scripts/lint-artifact.mjs`
- [ ] `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` → 0 fail
- [ ] The 3 new negative tests pass; full suite passes
- [ ] `node scripts/check-tokens.mjs` → clean with unchanged token counts
- [ ] `uv run python scripts/perf_harness.py --check --no-report` → exit 0
- [ ] Before/after feature-count table included in the completion report
- [ ] `git status` shows no modified files outside the in-scope list; no example HTML modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Any committed artifact drops below 3 features, or gains a dead-control FAIL, under the tightened gates — name the file and detector; the operator decides example-fix vs vocabulary-adjustment. **Do not weaken a pattern to get back to green.**
- The vocabularies in the two files have already diverged from the excerpt (drift).
- `check-tokens` reports different token counts after step 5 (means a non-6-digit hex already exists somewhere — a real drift the operator should see).

## Maintenance notes

- Plan 009 single-sources this vocabulary into a shared JS module with a Python-parity test — land THIS plan first so 009 consolidates the final patterns.
- Future feature detectors should follow the rule this plan establishes: match **markup or behavioral JS**, never prose words.
- Reviewer should scrutinize the before/after count table for any artifact that dropped from 5+ to exactly 3 — those are one weak detector away from failing and may deserve genuine feature work (as content improvements, separately).
