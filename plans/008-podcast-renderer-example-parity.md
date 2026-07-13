# Plan 008: Enforce parity between bin/render-podcast and its canonical examples; single-source its version string

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- bin/render-podcast tests/test_render_podcast.py examples/podcast.html examples/podcast-transcript.html`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition. (Plans 001 and 004 both touch
> `bin/render-podcast` — expect their diffs; what must still match is the
> structure described below.)

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (touches the one shipped CLI; the existing test suite plus the new parity tests bound the blast radius)
- **Depends on**: plans/001-release-hygiene-v263.md (check-versions gate), plans/004-render-podcast-input-hardening.md (lands first; same file)
- **Category**: tech-debt
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

`bin/render-podcast`'s docstring names `examples/podcast.html` "the visual contract", but only the `<style>` block is actually shared at runtime (`load_template_style()` extracts it) — the entire body structure is re-authored as Python f-strings, and ~90 lines of CSS overrides (`COMMON_OVERRIDES`) are grafted on top. Nothing enforces that the hand-copied body and the override selectors stay faithful to the canonical examples, so the gallery and real generated output can silently diverge (this has already happened once by design: the example uses `prefers-color-scheme`, the renderer strips it and swaps in `body.dark`). Separately the version string is hardcoded twice inside the renderer's f-strings — a bump ritual plan 001's checker can flag but a constant removes. This plan does NOT rewrite the renderer into shared partials (deferred — see Maintenance notes); it adds the missing *enforcement*: a version constant, a structural-parity test, and a dead-override-selector check.

## Current state

- `bin/render-podcast:38-44` — only the style is shared:
  ```python
  def load_template_style() -> str:
      template = TEMPLATE_PATH.read_text(encoding="utf-8")
      style_start = template.find("<style>")
      style_end = template.find("</style>", style_start)
      if style_start == -1 or style_end == -1:
          raise RuntimeError(f"template has no <style> block: {TEMPLATE_PATH}")
      return template[style_start:style_end + len("</style>")]
  ```
- `bin/render-podcast:109-199` — `COMMON_OVERRIDES`: a large CSS string of selector-targeted patches (`.topbar .brand`, `.folder-tab`, `#theme-toggle`, etc.) applied via `transform_style_block()` (:219-224), which also swaps the example's `@media (prefers-color-scheme: dark)` block (`DARK_MEDIA_BLOCK`, :54-62) for `body.dark` (`DARK_CLASS_BLOCK`, :64-70) — a **string-equality replacement**: if the example's dark block drifts by one character, the swap silently no-ops and the renderer ships a double-dark-mode page. That is precisely the divergence this plan makes loud.
- Version hardcodes (after plan 001 these read `2.6.3`): `bin/render-podcast:503` (`… · podcast shape · v2.6.2 · transcript view`) and `:710` (`… · podcast shape · v2.6.2`), inside f-string colophons.
- The canonical pair: `examples/podcast.html` (briefing shape; colophon at :624) and `examples/podcast-transcript.html` (transcript; colophon at :600).
- Existing tests: `tests/test_render_podcast.py` — loads the renderer via `SourceFileLoader` (`_load_renderer`, :22-30), renders the fixture into `tmp_path`, asserts contract elements (e.g. `test_briefing_has_required_contract_elements`, :44-58, checks `class="folder-tab active"`, `id="theme-toggle"`, glyphs, `:focus-visible`). Model new tests on these.
- `scripts/check-versions.mjs` (from plan 001) already asserts `bin/render-podcast` contains the canonical version.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Targeted tests | `uv run --with pytest pytest tests/test_render_podcast.py -q` | all pass |
| Full tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Version gate | `node scripts/check-versions.mjs` | `check-versions: clean.` |
| Perf gate (renders fixtures) | `uv run python scripts/perf_harness.py --check --no-report` | exit 0 |
| Manual render | `bin/render-podcast tests/fixtures/episode.package.json -o /tmp/rp-parity` | both paths printed |

## Scope

**In scope** (the only files you should modify):
- `bin/render-podcast`
- `tests/test_render_podcast.py`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `examples/podcast.html`, `examples/podcast-transcript.html` — the parity tests READ them; a parity failure is information for the operator, never a reason to edit the canonical examples in this plan.
- Rewriting body-markup generation into shared partials/templates — explicitly deferred (see Maintenance notes).
- `scripts/check-versions.mjs` — already covers this file.

## Git workflow

- Branch: `advisor/008-podcast-renderer-parity`
- One commit, imperative subject, e.g. `render-podcast: VERSION constant, style-swap hard-fail, structural parity tests`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Single-source the version

Near the top of `bin/render-podcast` (after the imports), add `VERSION = "2.6.3"` (whatever the current canonical version is per SKILL.md frontmatter at execution time) with a comment `# Must match SKILL.md frontmatter — enforced by scripts/check-versions.mjs`. Replace the two hardcoded `v2.6.2`/`v2.6.3` occurrences in the colophon f-strings (:503, :710) with `v{VERSION}`.

**Verify**: `node scripts/check-versions.mjs` → clean; `bin/render-podcast tests/fixtures/episode.package.json -o /tmp/rp-parity && grep -c "v$(grep '^version:' SKILL.md | awk '{print $2}')" /tmp/rp-parity/podcast-at-a-glance.html` → ≥1.

### Step 2: Make the dark-block contract fail loudly (AMENDED after execution discovery, 2026-07-12)

**Execution finding**: the original premise was already false when this plan was written — `examples/podcast.html` no longer contains any `@media (prefers-color-scheme: dark)` block; it authors `body.dark { … }` directly (deliberate: inline comment in the example says `prefers-color-scheme` surprised users on dark-OS setups). The renderer's media→class swap has therefore been a silent no-op on every render, and the render only works because the example happens to carry the exact `DARK_CLASS_BLOCK` already. Reviewer ruling: the example is authoritative; the swap is dead code.

Amended instructions for `bin/render-podcast`:
1. Delete the `DARK_MEDIA_BLOCK` constant and the media→class replacement branch in `transform_style_block()`.
2. Keep `DARK_CLASS_BLOCK` as the parity reference. In `transform_style_block()`, assert `DARK_CLASS_BLOCK in style_block`; if absent, `raise RuntimeError("examples/podcast.html no longer carries the body.dark block bin/render-podcast expects — update DARK_CLASS_BLOCK and the example together")`.
3. Update the comment above the constants (currently describes the v2.2.0 swap behavior) to describe the new invariant.

**Verify**: `uv run --with pytest pytest tests/test_render_podcast.py -q` → all pass (the fixture render exercises the assertion). Manual negative: temporarily edit one character of `DARK_CLASS_BLOCK`, re-run one test, confirm the RuntimeError fires with the message, revert.

### Step 3: Add a structural parity test (renderer output vs canonical example)

Append to `tests/test_render_podcast.py`:

```python
def test_rendered_briefing_structurally_matches_canonical_example(tmp_path):
    """examples/podcast.html is the visual contract (renderer docstring).
    The renderer re-authors the body in Python, so enforce that the load-
    bearing structural hooks of the canonical example all appear in real
    output — divergence here means gallery and reality have split."""
    import re
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    rendered = (tmp_path / "podcast-at-a-glance.html").read_text(encoding="utf-8")
    example = (REPO / "examples" / "podcast.html").read_text(encoding="utf-8")

    # Every id= the canonical example wires up must exist in rendered output
    # (renderer may add extras like #theme-toggle; the example is the floor).
    example_ids = set(re.findall(r'\bid="([^"]+)"', example)) - {"episode-data"}
    rendered_ids = set(re.findall(r'\bid="([^"]+)"', rendered))
    missing = example_ids - rendered_ids
    assert not missing, f"canonical ids absent from rendered output: {sorted(missing)}"

    # Every class the example's OWN <style> block targets must be used by the
    # rendered body too (shared stylesheet, re-authored body — dead classes in
    # rendered output mean structural drift).
    style = example[example.find("<style>"):example.find("</style>")]
    styled_classes = set(re.findall(r"\.([a-z][a-z0-9-]{2,})\b", style))
    rendered_classes = set(re.findall(r'class="([^"]+)"', rendered))
    rendered_class_tokens = set(t for cs in rendered_classes for t in cs.split())
    dead = {c for c in styled_classes if c not in rendered_class_tokens}
    # Allowlist: state classes toggled by JS at runtime + transcript-only chrome.
    allowed_dead = {"dark", "inspector-hidden", "active"}
    dead -= allowed_dead
    assert not dead, f"classes styled by the shared stylesheet but absent from rendered briefing: {sorted(dead)}"
```

**Run it before finalizing the allowlist**: the first run will likely surface legitimately-runtime-only or transcript-only classes — extend `allowed_dead` ONLY with classes you can justify in a comment (state classes, transcript-page classes not used by the briefing). If the missing-ids assertion fails, that is a real divergence: STOP and report the ids instead of allowlisting them.

**Verify**: `uv run --with pytest pytest tests/test_render_podcast.py -q` → all pass, with every `allowed_dead` entry justified by an inline comment.

### Step 4: Same parity test for the transcript pair

Mirror step 3 for `annotated-transcript.html` vs `examples/podcast-transcript.html` (its own id floor and styled-class check; the transcript example's `<style>` is self-contained in that file). Same allowlist discipline.

**Verify**: full file passes: `uv run --with pytest pytest tests/test_render_podcast.py -q`.

### Step 5: Add a dead-override check on COMMON_OVERRIDES

Append one more test: extract every class/id selector token from `rp.COMMON_OVERRIDES` (regex `[.#]([a-zA-Z][\w-]*)`), render the fixture, and assert each token appears in at least one of the two rendered files (as `class="…"`/`id="…"` token or in the inline `<style>`). An override targeting nothing is graft rot.

**Verify**: test passes; if a genuinely dead override selector surfaces, REMOVE that selector block from `COMMON_OVERRIDES` (that is in-scope cleanup) and note it in the report.

### Step 6: Full gates

**Verify**: `uv run --with pytest pytest tests/ -q` → all pass; `uv run python scripts/perf_harness.py --check --no-report` → exit 0; `node scripts/check-versions.mjs` → clean.

## Test plan

Steps 3-5 add three parity tests (briefing structure, transcript structure, override liveness) modeled on the existing fixture-render pattern (`tests/test_render_podcast.py:44-58`). Step 2's hard-fail is exercised by every existing render test. The negative case for step 2 is manual (documented in the step) because committing a mutated `DARK_MEDIA_BLOCK` fixture would mean duplicating the example.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -c "v2\." bin/render-podcast` shows version interpolation only via `{VERSION}` (the literal appears exactly once, in the constant)
- [ ] `transform_style_block` raises with a "has drifted" message when its string replacements don't match (verified manually per step 2)
- [ ] Three new parity tests exist and pass; every `allowed_dead` entry carries a justification comment
- [ ] `uv run --with pytest pytest tests/ -q` → all pass
- [ ] `node scripts/check-versions.mjs` and `uv run python scripts/perf_harness.py --check --no-report` → clean
- [ ] `git status` shows no modified files outside the in-scope list (examples untouched)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The missing-ids parity assertion fails on first run — that is a live, real divergence between gallery and renderer; the operator must decide which side is right. Report the id list.
- `DARK_MEDIA_BLOCK` does not currently match `examples/podcast.html`'s dark block byte-for-byte (the silent no-op has ALREADY happened) — report before adding the hard-fail, since the hard-fail would then break every render.
- Plans 001/004 have not landed and their pending diffs to this file would conflict (check `plans/README.md` status).
- You find yourself editing either canonical example to make parity pass.

## Maintenance notes

- **Deferred deliberately**: refactoring the body markup into shared partials both the example and renderer consume. That is the *real* fix but a large, risky rewrite of the one shipped CLI; these enforcement tests make the current duplication safe-by-alarm and are the prerequisite characterization net for any future refactor.
- When the canonical podcast examples are restyled, expect: the dark-block hard-fail (update `DARK_MEDIA_BLOCK`/`DARK_CLASS_BLOCK` together), then the parity tests naming any new/removed hooks. The failure messages tell the maintainer exactly which side moved.
- Reviewer should scrutinize the `allowed_dead` allowlists — every entry is a place gallery and renderer intentionally differ; an entry without a crisp justification is drift being grandfathered.
