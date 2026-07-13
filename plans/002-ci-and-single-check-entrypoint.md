# Plan 002: Run every quality gate in CI on push/PR, behind a single `make check` entry point

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- scripts/ tests/ Makefile package.json .github/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: plans/001-release-hygiene-v263.md (creates `scripts/check-versions.mjs`, which CI runs)
- **Category**: dx
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

The repo ships six working quality gates — pytest, `perf_harness.py --check`, `check-tokens.mjs`, `check-versions.mjs` (from plan 001), `review-contracts.mjs`, `lint-artifact.mjs` — but **nothing runs them automatically**. There is no `.github/` directory. GitHub Pages serves `main` root and auto-builds on every push, and the install base tracks the repo with `git pull`, so an unchecked push ships instantly to the live site and every user. This is not hypothetical: a dead-script bug shipped on 2026-07-04 (recorded in `SKILL.md:526`), which is why the lint gate exists — but the lint gate still only runs when a human remembers. Additionally there is no single "does the repo pass?" command (six separate incantations across README), and the four Node ESM scripts declare no runtime floor (no `package.json`/engines) despite using version-sensitive APIs (`vm.compileFunction` in `scripts/lint-artifact.mjs:169`). One workflow + one Makefile + one minimal package.json closes all three gaps.

## Current state

- No `.github/`, no `Makefile`, no `justfile`, no `package.json` anywhere (verified at `e0278cb`).
- The gates and their exact current invocations + passing output (verified on a clean tree):
  - `uv run --with pytest pytest tests/ -q` → `21 passed` (22+ after plan 001)
  - `uv run python scripts/perf_harness.py --check --no-report` → exit 0 (the `--no-report` flag suppresses writing gitignored `perf/reports/`; see `scripts/perf_harness.py:738`)
  - `node scripts/check-tokens.mjs` → `check-tokens: clean.`
  - `node scripts/check-versions.mjs` → `check-versions: clean.` (exists only after plan 001)
  - `node scripts/review-contracts.mjs` → `review contracts passed for 25 HTML files`
  - `node scripts/lint-artifact.mjs <files>` → per-file PASS/FAIL, exit 1 on any FAIL (`scripts/lint-artifact.mjs:208`). **Note**: this linter is currently only pointed at *generated* artifacts by hand; it has never been run across all committed examples in one gate. `tests/test_linters.py:61-69` proves `examples/dashboard.html` and `examples/primitives/10-scatter.html` pass individually.
- `tests/test_linters.py` covers `check-tokens.mjs` and `lint-artifact.mjs` but has **no test for `review-contracts.mjs`** — that 169-line a11y/contract linter is wired into nothing automated.
- Node scripts are stdlib-only ESM (`.mjs`), invoked bare. `bin/og-card.mjs:56` additionally shells to Chrome — og-card must NOT be part of CI (needs a browser).
- Python side: `bin/render-podcast` and `scripts/perf_harness.py` use modern syntax (`str | None` unions → needs Python ≥3.10; repo develops on 3.12 per `__pycache__` tags). No `pyproject.toml`; `uv run --with pytest` resolves pytest ephemerally.
- Test-runner conventions: see `tests/test_linters.py:26-32` (`_run` helper: `subprocess.run([NODE, *args], cwd=REPO, capture_output=True, text=True)`), and the module-level skip `pytestmark = pytest.mark.skipif(NODE is None, reason="node not available")` at line 23.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Full gate (after this plan) | `make check` | exit 0, all six gates green |
| Tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Lint all examples | `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` | `24 file(s) · 24 pass · 0 fail` (see step 1) |
| Workflow syntax sanity | `uv run python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"` | exit 0 (add `--with pyyaml` if needed: `uv run --with pyyaml python -c ...`) |

## Scope

**In scope** (the only files you should modify/create):
- `.github/workflows/ci.yml` (create)
- `Makefile` (create)
- `package.json` (create)
- `scripts/lint-artifact.mjs` (two surgical changes authorized after the step-1 STOP — see step 1a)
- `tests/test_linters.py` (append review-contracts + lint-adjustment tests)
- `README.md` (point the "Optimization guard" section at `make check`)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `bin/og-card.mjs` — requires Chrome; belongs to plan 003, and must not run in CI.
- The linters/harness themselves — if a gate FAILS during step 1, that is a STOP, not a license to edit checkers or examples.
- `.gitignore` — already correct.
- No lockfile, no npm dependencies — the zero-dependency posture is deliberate; `package.json` is metadata only.

## Git workflow

- Branch: `advisor/002-ci-single-entrypoint`
- One commit, imperative subject, e.g. `Add CI workflow + make check entry point over the existing gates`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Establish the lint-artifact baseline over committed examples

Run: `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html`

**Execution finding (first dispatch, 2026-07-12):** 6 of 25 files fail on the committed tree. The reviewer investigated and ruled both failure classes gate defects, not content defects: (a) `examples/podcast.html:521` and `examples/primitives.html:247,264` merely *mention* "copy as prompt" in prose/contract text — the linter's `hasCopyPrompt` trigger matches bare prose and then demands the BEGIN/END state delimiter of a control that doesn't exist; (b) `examples/primitives/{02-bar,03-sparkline,04-stacked-bar,05-topology}.html` fail the ≥3 feature floor, which is scoped to full artifacts — the perf harness's own floor check deliberately applies only to shape examples (`scripts/perf_harness.py:616-621`), so single-primitive reference pages were never meant to meet it. Step 1a applies the authorized gate adjustments.

### Step 1a: Two surgical adjustments to `scripts/lint-artifact.mjs` (authorized)

1. **Tighten the copy-as-prompt trigger** (line ~134). Replace the bare-prose alternative with control-context matching, mirroring `review-contracts.mjs:132`'s approach: match identifiers (`copyAsPrompt|copyPrompt|copyRecommendation|generateStuckPrompt|prompt-output`) or "copy as prompt" only inside a `<button…>…</button>` element — a prose `<p>`/`<dd>` mention must NOT trigger the delimiter requirement.
2. **Add a `--reference` flag** (parsed like `--longform`) that skips ONLY the ≥3 feature-floor check; every other check (meta, favicon, self-containment, copy-as-prompt, clipboard guard, dead-script, dead-control, SVG sizing) still runs. Document it in `usage()` as "single-primitive reference pages".

**Verify**: `node scripts/lint-artifact.mjs index.html examples/*.html` → `15 file(s) · 15 pass · 0 fail`; `node scripts/lint-artifact.mjs --reference examples/primitives/*.html` → `10 file(s) · 10 pass · 0 fail`. Also confirm the placeholder/delimiter negative tests still pass: `uv run --with pytest pytest tests/test_linters.py -q`.

### Step 2: Create `Makefile`

```makefile
# Quality gates for render-as-html. `make check` is THE pre-push answer to
# "does the repo pass?" — CI runs exactly this.
SHELL := /bin/bash

.PHONY: check test perf tokens versions contracts lint-examples

check: test perf tokens versions contracts lint-examples
	@echo "make check: all gates green"

test:
	uv run --with pytest pytest tests/ -q

perf:
	uv run python scripts/perf_harness.py --check --no-report

tokens:
	node scripts/check-tokens.mjs

versions:
	node scripts/check-versions.mjs

contracts:
	node scripts/review-contracts.mjs

lint-examples:
	node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html
```

**Verify**: `make check` → exit 0, prints `make check: all gates green`.

### Step 3: Create `package.json`

```json
{
  "name": "render-as-html",
  "private": true,
  "description": "Design-system skill for self-contained HTML artifacts. Node scripts are stdlib-only by design — no dependencies, no lockfile.",
  "engines": { "node": ">=18" }
}
```

Deliberately **no** `version` field (the canonical version lives in `SKILL.md` frontmatter, checked by `scripts/check-versions.mjs` — a second version surface here would drift) and no dependencies.

**Verify**: `node -e "JSON.parse(require('fs').readFileSync('package.json'))"` → exit 0. `make check` still green (adding package.json must not change `.mjs` module resolution — they are ESM by extension).

### Step 4: Add review-contracts tests

Append to `tests/test_linters.py` (uses the existing `_run` helper and `NODE` skip already in the file):

```python
# --- review-contracts.mjs -----------------------------------------------------

def test_review_contracts_clean():
    """The repo-wide contract/a11y linter must pass on the committed tree.
    It scans index.html + examples/**/*.html (25 files)."""
    r = _run("scripts/review-contracts.mjs")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "review contracts passed" in r.stdout


def test_review_contracts_catches_missing_meta(tmp_path, monkeypatch):
    """Negative case: a file in examples/ missing required meta must fail.
    review-contracts globs examples/ relative to cwd, so run it from a
    synthetic tree."""
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "primitives").mkdir()
    (tmp_path / "index.html").write_text(
        '<!doctype html><html><head><title>t</title></head><body></body></html>'
    )
    r = subprocess.run(
        [NODE, str(REPO / "scripts" / "review-contracts.mjs")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert r.returncode == 1
    assert "missing" in r.stderr
```

Note: `review-contracts.mjs` resolves everything from `process.cwd()` (`scripts/review-contracts.mjs:4-13`) and unconditionally reads `examples/runbook.html` at line 149 — if the negative test errors on that read instead of failing cleanly, assert on the nonzero exit code only and drop the stderr assertion (an uncaught ENOENT still exits nonzero; capturing the contract "bad tree ⇒ nonzero" is the point).

**Verify**: `uv run --with pytest pytest tests/test_linters.py -q` → all pass.

### Step 5: Create `.github/workflows/ci.yml`

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - run: make check
```

**Verify**: the YAML-parse sanity command from the table exits 0, and `make check` (which is all CI runs) is green locally.

### Step 6: Point README at the entry point

In `README.md`'s "Optimization guard" section (currently begins `Run `uv run python scripts/perf_harness.py --check` before changing…` at line ~113), reword the opening to: run `make check` before changing the skill contract, examples, primitives, or `bin/render-podcast` — it runs the pytest suite, the perf harness, and the three Node linters; CI runs the same command on every push. Keep the rest of the section (the harness description) intact.

**Verify**: `grep -c "make check" README.md` → ≥1.

## Test plan

- New: `test_review_contracts_clean` + `test_review_contracts_catches_missing_meta` (step 4), modeled on `tests/test_linters.py:37-42`.
- The Makefile itself is exercised by running `make check` (step 2) — its six targets are the six commands already verified individually.
- CI cannot be executed locally; the workflow runs `make check` verbatim, so local green + YAML-parses is the achievable verification. Flag in your report that the first real CI run on GitHub must be watched.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `make check` exits 0
- [ ] `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` → 0 fail
- [ ] `uv run --with pytest pytest tests/ -q` → all pass, including 2 new review-contracts tests
- [ ] `.github/workflows/ci.yml` exists and YAML-parses; its only build step is `make check`
- [ ] `package.json` exists with `engines.node >= 18` and **no** `version` field
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Step 1 finds any committed example failing `lint-artifact.mjs` — report the file and failing check; the operator decides whether to fix the example or adjust the gate.
- `scripts/check-versions.mjs` does not exist (plan 001 has not landed) — report BLOCKED on dependency.
- `make check` fails on the unmodified tree for any gate.
- Adding `package.json` changes any script's behavior (it must not — `.mjs` is ESM regardless; if anything breaks, report rather than patching scripts).

## Maintenance notes

- The first push after merge is the real CI verification — watch the Actions tab; likely first-run issues are uv/python resolution (the harness needs only stdlib, so `python-version: "3.12"` via setup-uv should suffice) and glob behavior (the Makefile globs are expanded by the shell, which exists on ubuntu-latest).
- `perf_harness.py --check` compares SKILL.md tokens against the committed `perf/baseline.json` with a 5% growth budget (`scripts/perf_harness.py:131`) — a PR that legitimately grows SKILL.md must include a deliberate `--update-baseline` regeneration, which will now be enforced by CI rather than by memory.
- og-card (Chrome) is intentionally NOT in CI. If plan 003 adds og-card tests, they must keep their Chrome-dependent parts skippable (the pattern is `tests/test_linters.py:23`).
- Branch protection on `main` (require the `ci / check` status) is an operator setting in GitHub, not a repo file — recommend enabling it after the first green run.
