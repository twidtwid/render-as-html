# Plan 001: Release v2.6.3 — bump all version surfaces, add CHANGELOG, add a version-drift checker, fix gallery/README drift

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- SKILL.md README.md index.html examples/index.html examples/podcast.html examples/podcast-transcript.html bin/render-podcast scripts/ tests/test_linters.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

Commit `e0278cb` shipped a substantial feature set (artifact lint gate, og-card generator, scatter primitive, per-shape reference contracts, DESIGN.md, check-tokens) **past** the `v2.6.2` tag, but every version string in the repo still reads 2.6.2 and no new tag exists. GitHub Pages serves `main` directly and users install by `git clone` / `git pull`, so the live site and every install currently run post-2.6.2 code while advertising 2.6.2. The maintainer has a standing "always bump version on release" rule, and git history shows the manual 8-file sync slips repeatedly (`652a27f "Sync v2.4.0 → v2.4.1 across release surfaces"`). This plan bumps to 2.6.3, adds a CHANGELOG so `git pull` users can see what changed, and adds a mechanical checker so a half-stamped release can never pass the gates again. It also fixes two verified doc drifts: the public gallery still says "Nine canonical primitives" (there are ten — scatter is missing from the list), and README's "What's in here" omits `bin/og-card.mjs`.

## Current state

Files and their version sites (all verified at commit `e0278cb`):

- `SKILL.md:3` — frontmatter `version: 2.6.2` ← this is the **canonical** version
- `README.md:7` — `**Version 2.6.2** · live design system at …`
- `index.html:324` — `v2.6.2 · 2026-05-30` (TOC meta)
- `index.html:332` — `<p class="byline">v2.6.2 · 2026-05-30 · informed by Thariq's …`
- `index.html:1073` — `<span>design system v2.6.2 · 2026-05-30 · inspiration from …`
- `examples/index.html:84` — `<footer><span>examples/index.html · v2.6.2</span>…`
- `examples/podcast.html:624` — `<span class="path">examples/podcast.html · v2.6.2 · fictional episode for the gallery</span>`
- `examples/podcast-transcript.html:600` — `<span class="path">~/Reports/tests/annotated-transcript.html · podcast shape · v2.6.2 · transcript view</span>`
- `bin/render-podcast:503` — f-string colophon `… · podcast shape · v2.6.2 · transcript view`
- `bin/render-podcast:710` — f-string colophon `… · podcast shape · v2.6.2`
- `examples/primitives.html:309` — footer `<span>examples/primitives.html · v2.6.2</span>` (added during execution: the original plan enumerated ten sites; the executor's STOP correctly surfaced this eleventh)

Doc drift sites:

- `examples/index.html:82` (verified excerpt):
  ```html
  <a class="card" href="primitives.html"><span class="tag">primitives · reference</span><div class="ct">Nine canonical chart and table primitives</div><p class="cd">The bones the page shapes are built on — donut, ranked bar, sparkline cluster, stacked bar, topology, dense table, comparison matrix, annotated diff, log stream — each with contract, when-to-pick, and anti-patterns.</p></a>
  ```
  There are TEN primitives now — `scatter` (10th) was added in `e0278cb` (`examples/primitives/10-scatter.html`, `references/primitives/scatter.md`) and `tests/test_perf_harness.py:67` asserts `len(audit["primitives"]) == 10`.
- `README.md:60-72` "What's in here" lists every script (`perf_harness.py`, `lint-artifact.mjs`, `check-tokens.mjs`, `review-contracts.mjs`) but NOT `bin/og-card.mjs`, even though `SKILL.md:527-533` hard-requires og-card in the publish flow.

No `CHANGELOG.md` exists. Existing node-linter test conventions live in `tests/test_linters.py` — pattern to copy:

```python
# tests/test_linters.py:26-32
def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
# tests/test_linters.py:37-42
def test_check_tokens_clean():
    r = _run("scripts/check-tokens.mjs")
    assert r.returncode == 0, r.stdout + r.stderr
```

Existing script conventions: `scripts/check-tokens.mjs` is the exemplar — stdlib-only Node ESM, resolves the repo root from its own location (`scripts/check-tokens.mjs:23`: `const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")`), prints a human report, exits 1 on drift, 2 on structural error. Match it.

Recent release-note prose already exists in commit subjects (`git log --oneline v2.5.0..HEAD`) — use them for the CHANGELOG backfill.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `uv run --with pytest pytest tests/ -q` | all pass (21 at plan time; more after this plan) |
| Perf gate | `uv run python scripts/perf_harness.py --check --no-report` | exit 0, no REGRESSIONS section |
| Token drift | `node scripts/check-tokens.mjs` | `check-tokens: clean.` |
| Contracts | `node scripts/review-contracts.mjs` | `review contracts passed for 25 HTML files` |
| New version gate | `node scripts/check-versions.mjs` | `check-versions: clean.` (after step 1) |

## Scope

**In scope** (the only files you should modify/create):
- `SKILL.md` (line 3 only), `README.md` (line 7 + one new bullet), `index.html` (3 version/date strings), `examples/index.html` (lines 82 and 84), `examples/podcast.html` (line 624), `examples/podcast-transcript.html` (line 600), `examples/primitives.html` (line 309, footer version only), `bin/render-podcast` (2 version strings)
- `CHANGELOG.md` (create)
- `scripts/check-versions.mjs` (create)
- `tests/test_linters.py` (append one test)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `.claude.local.md` — gitignored maintainer notes; never edit or commit.
- `perf/baseline.json` — the version-string change does not move token counts enough to matter; do not regenerate.
- Git tags — tags are cut on `main` by the operator after merge, not on your branch.
- Any other content in `index.html` / the examples — these are canonical artifacts; change only the exact strings named above.

## Git workflow

- Branch: `advisor/001-release-hygiene-v263`
- One commit, imperative subject matching repo style (cf. `652a27f Sync v2.4.0 → v2.4.1 across release surfaces`): e.g. `Release v2.6.3: version sync, CHANGELOG, check-versions gate, gallery/README drift fixes`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Create `scripts/check-versions.mjs`

Stdlib-only Node ESM, modeled on `scripts/check-tokens.mjs` (same repo-root resolution, same output style). Behavior:

1. Read `SKILL.md`, extract the canonical version from the frontmatter line matching `/^version:\s*(\d+\.\d+\.\d+)\s*$/m`. If absent, print an error and exit 2.
2. For each of these files, assert the file content includes the canonical version string (as `2.6.3` or `v2.6.3` — search for the bare `X.Y.Z` substring):
   `README.md`, `index.html`, `examples/index.html`, `examples/podcast.html`, `examples/podcast-transcript.html`, `examples/primitives.html`, `bin/render-podcast`.
3. Additionally assert **no stale version remains**: for each file above plus `SKILL.md`, flag any regex match of `/\bv?\d+\.\d+\.\d+\b/` that looks like a render-as-html version (matches `2.` major) and differs from canonical. Exclude URLs (skip matches inside `http…` substrings) — `index.html` and examples contain external links but no other dotted versions at plan time; if this exclusion proves too fiddly, checking "canonical present in each file + no `2.6.2` anywhere once bumped" is an acceptable simpler implementation, as long as the checker fails when any listed file lacks the canonical version.
4. Print per-file OK/STALE lines; exit 1 on any failure, else print `check-versions: clean.`

**Verify**: `node scripts/check-versions.mjs` → exits 0 and reports all files OK against version `2.6.2` (nothing is bumped yet — the checker must pass on the current consistent state).

### Step 2: Bump every version site to 2.6.3

Edit exactly the ten sites listed in "Current state": `2.6.2` → `2.6.3`. In `index.html` (three sites) also update the date `2026-05-30` → the current date (`YYYY-MM-DD`).

**Verify**: `node scripts/check-versions.mjs` → `check-versions: clean.` AND `grep -rn "2\.6\.2" --include="*.md" --include="*.html" --include=render-podcast . | grep -v CHANGELOG | grep -v plans/ | grep -v .git` → no matches.

### Step 3: Fix the gallery primitives card

In `examples/index.html:82`: change `Nine canonical chart and table primitives` → `Ten canonical chart and table primitives`, and in the same card's description change `… annotated diff, log stream — each with …` → `… annotated diff, log stream, scatter — each with …`.

**Verify**: `grep -c "Ten canonical" examples/index.html` → `1`; `node scripts/review-contracts.mjs` → passes for 25 HTML files.

### Step 4: Add the og-card bullet to README

In `README.md` "What's in here" (after the `bin/render-podcast` bullet at line 66), add:

```markdown
- `bin/og-card.mjs` — renders a 1200×630 social-card PNG from an artifact's own title/description/design tokens via headless Chrome, and with `--inject` writes `og:image`/`twitter:image` into the artifact `<head>` (`node bin/og-card.mjs <artifact.html> --inject`). Required by the publish flow in `SKILL.md` step 8.
```

**Verify**: `grep -c "og-card.mjs" README.md` → `1` (or more).

### Step 5: Create `CHANGELOG.md`

Keep-a-changelog-ish, newest first. Entries:

- `## 2.6.3 — <today's date>`: version-drift checker (`scripts/check-versions.mjs`), CHANGELOG introduced, gallery primitives card corrected to ten (scatter), README documents `bin/og-card.mjs`. **Also note**: this version stamps the previously-unversioned `e0278cb` feature set — artifact lint gate (dead-script + dead-control + og:image checks in `scripts/lint-artifact.mjs`), `bin/og-card.mjs` social-card generator, scatter primitive (10th), per-shape reference contracts (`references/shapes/*.md`), `DESIGN.md` canonical tokens + `scripts/check-tokens.mjs`.
- Backfill `2.6.2`, `2.6.1`, `2.6.0`, `2.5.0` from the corresponding commit subjects (`git log --oneline v2.4.1..v2.6.2`); one or two lines each is enough.
- End with a line noting older history lives in git tags.

**Verify**: `head -5 CHANGELOG.md` shows the 2.6.3 heading.

### Step 6: Add the pytest gate

Append to `tests/test_linters.py`, following the `_run` pattern already in that file:

```python
# --- check-versions.mjs -------------------------------------------------------

def test_check_versions_clean():
    """SKILL.md frontmatter is the canonical version; every release surface
    (README, index.html, gallery + podcast example footers, bin/render-podcast)
    must carry the same string."""
    r = _run("scripts/check-versions.mjs")
    assert r.returncode == 0, r.stdout + r.stderr
```

**Verify**: `uv run --with pytest pytest tests/test_linters.py -q` → all pass (was 7 in this file, now 8).

### Step 7: Run the full gate set

**Verify**:
- `uv run --with pytest pytest tests/ -q` → all pass (22 total)
- `uv run python scripts/perf_harness.py --check --no-report` → exit 0
- `node scripts/check-tokens.mjs` → `check-tokens: clean.`
- `node scripts/review-contracts.mjs` → `review contracts passed for 25 HTML files`

## Test plan

- New: `test_check_versions_clean` in `tests/test_linters.py` (step 6), modeled on `test_check_tokens_clean` (`tests/test_linters.py:37-42`).
- Manual negative check (do not commit): temporarily revert one string to `2.6.2`, run `node scripts/check-versions.mjs`, confirm exit 1 naming the stale file, then restore.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `node scripts/check-versions.mjs` exits 0 printing `check-versions: clean.`
- [ ] `grep -rn "2\.6\.2" SKILL.md README.md index.html examples/index.html examples/podcast.html examples/podcast-transcript.html bin/render-podcast` → no matches
- [ ] `grep -c "Ten canonical" examples/index.html` → 1; the card lists `scatter`
- [ ] `CHANGELOG.md` exists with a 2.6.3 entry
- [ ] `uv run --with pytest pytest tests/ -q` → 22 passed
- [ ] `uv run python scripts/perf_harness.py --check --no-report` exits 0; `node scripts/check-tokens.mjs` and `node scripts/review-contracts.mjs` exit 0
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Any version site listed in "Current state" does not contain `2.6.2` where stated (drift since planning).
- `check-versions.mjs` at step 1 fails on the *unmodified* tree for a reason other than a bug in your script — that means a surface already drifted and the operator should see it.
- `review-contracts.mjs` or the perf harness fails after your edits — your string edits should be invisible to both; a failure means you changed more than a version string.
- You find additional `2.6.2` occurrences beyond the ten listed sites (report them; do not guess whether they are version strings).

## Maintenance notes

- **After merge, the operator (not the executor) must**: cut the `v2.6.3` tag on `main`, and propagate to the two installed copies (`~/.claude/skills/render-as-html` via the home-state symlink target, `~/.codex/skills/render-as-html` as a real rsync copy) per the maintainer's release workflow.
- Plan 002 wires `check-versions.mjs` into CI and a `make check` entry point — after that lands, a half-stamped release cannot merge.
- Plan 008 replaces the two hardcoded strings in `bin/render-podcast` with a single `VERSION` constant; `check-versions.mjs` already covers that file, so 008 needs no checker change.
- Every future release: bump SKILL.md frontmatter first (canonical), then run `node scripts/check-versions.mjs` to find the rest, then add a CHANGELOG entry.
