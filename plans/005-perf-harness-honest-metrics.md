# Plan 005: Make the perf harness report deferred tokens honestly and slim the committed baseline to gated fields

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- scripts/perf_harness.py perf/baseline.json tests/test_perf_harness.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (do BEFORE plan 007, which relies on these corrected metrics)
- **Category**: perf (measurement integrity)
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

The harness is the tool the maintainer uses to reason about the per-invocation context tax, and its headline metric is wrong: it labels the "Page shapes" and "Canonical primitives" sections of SKILL.md (4,207 tokens) as "on-demand reference", but those sections live **inside SKILL.md** and load on every invocation — only the *detailed contracts* were moved to `references/`. The report therefore claims a 34.2% deferral that doesn't exist, hiding real always-loaded growth and making further disclosure work (plan 007) look already-done. Separately, `perf/baseline.json` commits ~100 lines of volatile data (timestamp, per-machine CLI timings, output bytes) that **no assertion consumes** — `regressions()` reads exactly one baseline field (`skill_md.total_tokens`) — so every `--update-baseline` produces a noisy diff on a public repo that buries the one number that matters.

## Current state

- `scripts/perf_harness.py:155-178` — the misclassification:
  ```python
  # Sections that fire on every render regardless of shape (the always-loaded tax)
  # vs sections that are per-shape / per-primitive reference material a single run
  # only partially touches.
  _REFERENCE_SECTIONS = {"Page shapes (pick before designing)", "Canonical primitives (charts and tables)"}

  def analyze_skill() -> dict:
      ...
      for part in parts:
          ...
          if name in _REFERENCE_SECTIONS:
              reference += t
          else:
              always += t
  ```
  `analyze_skill()` returns (see `perf/baseline.json:3-10`): `total_bytes: 49560, total_tokens: 12298, always_tokens: 8085, reference_tokens: 4207, reference_pct: 34.2`, plus `sections[]` and `contracts[]` breakdowns.
- The truly on-demand material is the `references/` tree: `references/shapes/*.md` (10 files) + `references/primitives/*.md` (10 files) + (after plan 007) `references/design.md`. The harness currently measures none of it.
- `scripts/perf_harness.py:648-670` — `regressions()` consumes from baseline ONLY `baseline["skill_md"]["total_tokens"]` (line 666-669). CLI timing gates use the fixed constant `CLI_CEILING_SECONDS = 0.5` (line 133), never baseline values.
- `scripts/perf_harness.py:745-748` — `--update-baseline` writes the **entire report** (timestamp `generated_at`, `cli.runs[].seconds`, `output_bytes`, everything) to `perf/baseline.json`.
- `scripts/perf_harness.py:684-698` — `to_markdown()` prints the misleading line:
  ```python
  f"- always-loaded: {s['always_tokens']:,} tok · on-demand reference: {s['reference_tokens']:,} tok ({s['reference_pct']}%)",
  ```
- `tests/test_perf_harness.py:52-60` — `test_skill_token_load_within_budget` loads the baseline JSON and passes a partial report (`{"skill_md": …, "cli": …, "self_contained": …}`) to `regressions()`; it touches no other baseline field, so slimming the baseline to `{"skill_md": {…}}` keeps this test working unchanged.
- Docstring `scripts/perf_harness.py:11-13` describes the old split; update it.
- `tok()` (line 137-139) is `len(text) // 4` — reuse it for the references measurement.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Harness report | `uv run python scripts/perf_harness.py --no-report` | markdown report, exit 0 |
| Check mode | `uv run python scripts/perf_harness.py --check --no-report` | exit 0 |
| Regenerate baseline | `uv run python scripts/perf_harness.py --update-baseline` | `baseline written: …/perf/baseline.json` |
| Tests | `uv run --with pytest pytest tests/test_perf_harness.py -q` | all pass |
| Full tests | `uv run --with pytest pytest tests/ -q` | all pass |

## Scope

**In scope** (the only files you should modify):
- `scripts/perf_harness.py`
- `perf/baseline.json` (regenerated in the new slim format)
- `tests/test_perf_harness.py` (only if an assertion references a renamed field — none do at plan time)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `SKILL.md`, `references/` — measurement change only; moving content is plan 007.
- `scripts/lint-artifact.mjs`, `scripts/review-contracts.mjs` — untouched by this metric fix.
- The regression thresholds (`SKILL_GROWTH_HARD`, `CLI_CEILING_SECONDS`) — unchanged semantics.

## Git workflow

- Branch: `advisor/005-perf-harness-honest-metrics`
- One commit, imperative subject, e.g. `perf harness: measure references/ as the deferred load, slim baseline to gated fields`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Reclassify — SKILL.md is all always-loaded; references/ is the deferred load

In `analyze_skill()`:

- Remove the `_REFERENCE_SECTIONS` split. Report `always_tokens = total` (or simply drop `always_tokens` and keep `total_tokens` — pick dropping only if nothing else reads it; `to_markdown` does, so update together).
- Keep the per-section `sections[]` and per-contract `contracts[]` breakdowns exactly as-is (they answer "what's big inside the always-loaded file" — that's the useful part of the old split).
- Add a new measurement: walk `REPO / "references"` for `**/*.md`, sum `tok()` per file, and report `references: {"total_tokens": N, "file_count": M}` (as a sibling key in the report next to `skill_md`, or inside `skill_md` as `deferred_reference_tokens` — sibling key preferred; wire it in `build_report()` at line 635-645).
- Update the module docstring (lines ~5-15) and the comment block at 155-157 to describe the corrected model: "SKILL.md is loaded in full on every invocation; the deferred load is references/*.md, fetched per-shape/per-primitive via the preflight READ."

**Verify**: `uv run python scripts/perf_harness.py --json --no-report | uv run python -c "import json,sys; r=json.load(sys.stdin); print(r['skill_md']['total_tokens'], r['references']['total_tokens'], r['references']['file_count'])"` → prints three numbers; file_count = 20 (10 shapes + 10 primitives at plan time).

### Step 2: Fix the markdown report labels

In `to_markdown()` replace the always/on-demand line with two honest lines, e.g.:

```
- always-loaded (all of SKILL.md): 12,298 tok
- deferred to references/ (loaded per-shape/primitive on demand): N tok across 20 files
```

**Verify**: `uv run python scripts/perf_harness.py --no-report` shows the new lines; the string `on-demand reference:` with a SKILL-internal token count no longer appears.

### Step 3: Slim what `--update-baseline` writes

In `main()` (lines 745-748), write only the gated slice plus provenance that doesn't churn per-machine:

```python
if args.update_baseline:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    slim = {"skill_md": report["skill_md"], "references": report["references"]}
    BASELINE.write_text(json.dumps(slim, indent=2) + "\n")
```

No `generated_at`, no `cli` timings, no `output_sizes`, no per-run seconds. (`regressions()` reads only `baseline["skill_md"]["total_tokens"]` — verify it still does and leave it; the extra `sections`/`contracts`/`references` context in the baseline is stable content-derived data, useful for review diffs, and only changes when the docs actually change.)

**Verify**: `uv run python scripts/perf_harness.py --update-baseline && uv run python -c "import json; b=json.load(open('perf/baseline.json')); assert set(b) == {'skill_md','references'}, set(b); assert 'generated_at' not in b; print('slim ok', b['skill_md']['total_tokens'])"` → `slim ok <N>`.

### Step 4: Regenerate + full gates

Commit the regenerated `perf/baseline.json`. Then:

**Verify**: `uv run python scripts/perf_harness.py --check --no-report` → exit 0 (baseline token count equals current, so growth = 0%); `uv run --with pytest pytest tests/ -q` → all pass, in particular `test_skill_token_load_within_budget` (which loads the slim baseline and calls `regressions()`).

## Test plan

- Existing `tests/test_perf_harness.py` is the regression net — all five tests must pass unmodified against the new report shape (they read `analyze_*()` results and the baseline only through `regressions()`).
- Add one new test in `tests/test_perf_harness.py`:
  ```python
  def test_references_dir_is_measured():
      h = _load_harness()
      report = h.build_report()
      assert report["references"]["file_count"] >= 20
      assert report["references"]["total_tokens"] > 0
      # The committed baseline must stay slim: only content-derived fields.
      baseline = json.loads(BASELINE.read_text())
      assert "generated_at" not in baseline and "cli" not in baseline
  ```
  (Note: `build_report()` runs the CLI timings — if that makes the test slow, call `h.analyze_skill()` + the new references function directly instead; keep the baseline-shape assertions either way.)

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `perf/baseline.json` contains only `skill_md` + `references` top-level keys; `git diff --stat` for it shows the volatile fields gone
- [ ] Harness markdown output no longer labels SKILL-internal sections as "on-demand"
- [ ] `report["references"]["file_count"] >= 20` per the new test
- [ ] `uv run python scripts/perf_harness.py --check --no-report` exits 0
- [ ] `uv run --with pytest pytest tests/ -q` → all pass including the new test
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `regressions()` at lines 648-670 reads any baseline field beyond `skill_md.total_tokens` (drift since planning — the slim format would then break gating).
- Any existing test in `tests/test_perf_harness.py` asserts on `always_tokens`/`reference_tokens`/`reference_pct` (none do at plan time; if one appeared, the rename decision needs the operator).
- `--check` fails after regeneration — baseline and current should be identical-by-construction; a failure means the slimming changed something it shouldn't have.

## Maintenance notes

- Plan 007 (SKILL.md design-system split) moves ~1-2k tokens from SKILL.md into `references/design.md` — after this plan, that move will show up honestly as always-loaded ↓ / references ↑, and 007 must re-run `--update-baseline` and commit it.
- Plan 002's CI runs `--check`; the slim baseline means future baseline diffs in PRs are reviewable at a glance (token deltas only).
- If a future gate wants to bound CLI latency against history rather than the fixed 0.5s ceiling, that data now lives only in gitignored `perf/reports/` — a deliberate trade; revisit only with a machine-normalized metric.
