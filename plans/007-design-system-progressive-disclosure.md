# Plan 007: Split SKILL.md §Design system — keep tokens and taste guards inline, defer the deep recipes to references/design.md

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- SKILL.md references/ perf/baseline.json scripts/check-tokens.mjs tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (moving always-loaded guidance out of the skill can degrade generation quality if the READ guard is not honored — mitigations below)
- **Depends on**: plans/005-perf-harness-honest-metrics.md (honest deferral metrics + slim baseline; this plan regenerates the baseline)
- **Category**: perf (context-token load)
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

SKILL.md loads in full on every invocation (~12.3k tokens). Its single largest section is `## Design system` at **3,043 tokens** (`perf/baseline.json` sections list) — and unlike the shapes and primitives sections, it never got the progressive-disclosure split those received in v2.6.1 (compact inline stub + detailed contract in `references/`, fetched via the mandatory preflight `READ:`). Most of §Design system is *build-time recipe detail* (the ~600-token sticky-rail engineering block, mark-search caching rules, density metrics) that an agent needs while *writing* HTML, not while *routing* — exactly the material the references/ mechanism exists for. Target: move ~1.3-1.7k tokens to a new `references/design.md`, keeping inline everything that must be present at routing/scaffolding time (color tokens, register table, performance defaults, anti-patterns).

## Current state

- `SKILL.md` section map (verified): `## Design system` spans lines 366-487, between `## Canonical primitives …` (287) and `## Rendering process` (488). Its subsections:
  - `### Performance defaults` (374-384) — operational, per-render rules (shape-log budget, scaffold-first order, cheap gates). **KEEP inline.**
  - `### Layout principles` (386-393) — max-widths, grids, mobile requirement, and the very large sticky-rail-collapse invariant paragraph (line 393). **MOVE.**
  - `### Density` (395-399) — register metrics. **MOVE.**
  - `### Typography` (401-420) — font-stack code block + register table + three detail bullets. **KEEP the code block and register table inline** (needed to scaffold `:root`); **MOVE the detail bullets** (mono small-caps, serif-in-instrument rules).
  - `### Color` (422-459) — the full light/dark hex block + the AA/ochre rules. **KEEP inline, byte-identical** — two tools depend on its exact location/format: `scripts/check-tokens.mjs:40` splits SKILL.md on `\n### Color` and reads hexes until the next `\n### `, and `tests/test_linters.py:45-56` re-implements that same split. If nothing follows `### Color` inside §Design system after the move, the split still works (it then reads to EOF of the section — confirm the checker still reports the same token count).
  - `### Interactivity` (461-469) — filter-clear/real-controls/copy-fallback/mark-search rules. **MOVE** (build-time recipes).
  - `### Anti-patterns` (471-486) — the taste guard. **KEEP inline** (it polices every write and is cheap, ~250 tok).
- The established split pattern to mirror — shapes/primitives stubs each end with a load-on-demand pointer, and the preflight `READ:` line at `SKILL.md:499` lists what to load:
  ```
  READ:         <reference files to load now: references/shapes/<shape>.md (every shape has one) + references/primitives/<name>.md for each chosen primitive>
  ```
  followed by the enforcement sentence at `SKILL.md:504`: "**Then actually Read the files named in `READ:` before step 3 — this is not optional.**"
- `references/` currently holds `shapes/` (10 files) and `primitives/` (10 files); there is no `references/design.md`. Reference files are plain markdown contracts, ~8-40 lines each — open `references/shapes/editorial.md` as the format exemplar.
- Gates that watch SKILL.md: `check-tokens.mjs` (Color block), `review-contracts.mjs:137-146` (scans SKILL.md for unguarded `navigator.clipboard.writeText` — the *moved* Interactivity text mentions `navigator.clipboard.writeText()` at SKILL.md:467; after the move, references/design.md is NOT scanned, and SKILL.md passes as long as any remaining `writeText` mention is accompanied by a guard-form match — the Copy-as-prompt section (`## Copy-as-prompt`, line 130) contains the guarded example), perf harness token budget (`SKILL_GROWTH_HARD` gates growth only — shrinking always passes, but the baseline should be regenerated to bank the win).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tokens | `node scripts/check-tokens.mjs` | `check-tokens: clean.` |
| Contracts | `node scripts/review-contracts.mjs` | passes for 25 HTML files |
| Harness | `uv run python scripts/perf_harness.py --no-report` | report shows SKILL.md total ↓ and references ↑ |
| Rebank baseline | `uv run python scripts/perf_harness.py --update-baseline` | baseline written |
| Tests | `uv run --with pytest pytest tests/ -q` | all pass |

## Scope

**In scope** (the only files you should modify/create):
- `SKILL.md` (§Design system only — do not touch any other section except the `READ:` line at :499)
- `references/design.md` (create)
- `perf/baseline.json` (regenerate after the move)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `### Color` content — byte-identical stays inline (tooling contract).
- `references/shapes/*.md`, `references/primitives/*.md`, `index.html`, examples.
- The version — content reorganization within a release; the operator decides whether this warrants a bump at merge time (note it in your report).

## Git workflow

- Branch: `advisor/007-design-progressive-disclosure`
- One commit, imperative subject matching the precedent (`68dec82 Release v2.6.1: progressive disclosure of primitive + editorial contracts`): e.g. `Progressive disclosure of the design-system deep contract into references/design.md`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Create `references/design.md` with the moved content VERBATIM

Header comment stating what it is ("Detailed design-system contract — loaded on demand via the preflight READ; the routing stub lives in SKILL.md §Design system"). Then move, verbatim and in this order, from SKILL.md:

1. `### Layout principles` — the whole subsection including the sticky-rail-collapse invariant paragraph (SKILL.md:386-393).
2. `### Density` (395-399).
3. The three Typography detail bullets (418-420: tabular-nums note, mono small-caps, serif-in-instrument).
4. `### Interactivity` — whole subsection (461-469).

Verbatim means verbatim: these paragraphs encode hard-won incident knowledge (dates, ratios, breakpoints) — do not summarize, reword, or "clean up".

**Verify**: `wc -l references/design.md` → roughly 40-60 lines; spot-check that the sticky-rail paragraph and the `<mark>` search rule are present byte-identical (`grep -c "Sticky-rail collapse invariant" references/design.md` → 1).

### Step 2: Replace the moved content in SKILL.md with compact stubs

§Design system after the edit keeps: intro paragraph (368-372), `### Performance defaults`, the Typography font-stack code block + register table, `### Color` (untouched), `### Anti-patterns` (untouched), plus a stub block where the moved subsections were, in the established stub voice, e.g.:

```markdown
### Layout, density, and interactivity (detailed contract on demand)

Compact rules: max-width 1280px instrument / 880px reading; mobile is a hard
requirement (~375px, no body horizontal scroll); every filter has a visible
clear; real controls for real actions; every copy button has a visible
textarea fallback; sticky side rails are mobile-first and bounded.
**Before building any multi-zone layout, sticky rail, in-text search, or
filter UI: Read `references/design.md` — it carries the full contract
(sticky-rail collapse invariant, density metrics, `<mark>` search rules).
Building from this stub alone reintroduces documented failure modes.**
```

Also update the preflight `READ:` template at SKILL.md:499 to include the new file:

```
READ:         <reference files to load now: references/shapes/<shape>.md (every shape has one) + references/primitives/<name>.md for each chosen primitive + references/design.md for any multi-zone/sticky-rail/search-heavy build>
```

**Verify**: `node scripts/check-tokens.mjs` → `check-tokens: clean.` with the SAME canonical/SKILL token counts as before (Color untouched). `grep -c "Sticky-rail collapse invariant" SKILL.md` → 0.

### Step 3: Measure the win and rebank the baseline

Run the harness report; SKILL.md total should drop by ~1.3-1.7k tokens vs the pre-move 12,298 (the stub adds back ~150). Then `--update-baseline` and commit the regenerated `perf/baseline.json`.

**Verify**: `uv run python scripts/perf_harness.py --check --no-report` → exit 0; the report's always-loaded number is ≥1,200 tokens lower than the committed pre-plan value; `references` file_count is now 21.

### Step 4: Full gates

**Verify**: `uv run --with pytest pytest tests/ -q` → all pass (in particular `test_design_and_skill_share_canonical_palette` — the `### Color` split — and `test_check_tokens_clean`); `node scripts/review-contracts.mjs` → passes (its SKILL.md clipboard scan must still be satisfied; if it fails on SKILL.md after the move, see STOP conditions).

## Test plan

No new tests — this is guarded by the existing net: `tests/test_linters.py` (Color-block parity, check-tokens), `tests/test_perf_harness.py` (token budget vs regenerated baseline, primitive-contract regexes in the untouched Canonical-primitives section), and `review-contracts.mjs` (SKILL.md clipboard scan). Content-completeness check (manual, include in report): `diff` the concatenation of moved subsections against `references/design.md` to prove verbatim transfer — e.g. extract the four ranges from the pre-edit SKILL.md (`git show HEAD:SKILL.md`) and diff against the new file's corresponding blocks.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `references/design.md` exists and contains the sticky-rail invariant, density metrics, typography detail bullets, and Interactivity rules verbatim
- [ ] SKILL.md no longer contains those blocks; its §Design system keeps Performance defaults, font stack + register table, Color (byte-identical), Anti-patterns, and the new stub
- [ ] The preflight `READ:` line names `references/design.md`
- [ ] Harness: SKILL.md total tokens ≤ 11,100 (≥1.2k reduction from 12,298); baseline regenerated and committed
- [ ] `node scripts/check-tokens.mjs`, `node scripts/review-contracts.mjs`, full pytest suite all green
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The §Design system line ranges don't match the section map above (drift).
- `check-tokens.mjs` reports different SKILL token counts after step 2 — you moved something out of (or into) the Color block.
- `review-contracts.mjs` fails on SKILL.md after the move — the guarded/unguarded `writeText` balance changed in a way this plan didn't predict; report the exact failure line rather than editing the Copy-as-prompt section (out of scope).
- The token reduction comes out under ~800 (the move didn't capture what the plan expected — the section boundaries may have shifted).

## Maintenance notes

- **The load-bearing assumption**: agents actually honor the `READ:` guard. The guard text at SKILL.md:504 is the enforcement; if generated-artifact quality regresses on multi-zone layouts after this lands (sticky-rail bugs reappearing), the right fix is strengthening the stub's trigger list, not moving everything back.
- Plan 005's `references` metric now shows this file's tokens as deferred load — the honest accounting this split relies on.
- Any future SKILL.md section growth gets caught by the 5% budget vs the newly-banked (lower) baseline — intentional ratcheting.
- The operator may fold this into the next release bump (plan 001's checker + CHANGELOG make that a two-line follow-up).
