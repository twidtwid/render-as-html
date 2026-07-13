# Plan 009: Single-source the HTML-invariant vocabulary across the two Node linters, with a Python parity gate

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- scripts/ tests/test_linters.py`
> Plans 002 and 006 intentionally touch these files first — expect their
> diffs. What must still hold: the duplicated tables/helpers described in
> "Current state" exist in both `.mjs` files. On a structural mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (refactors the ship-gates; the tests from plans 002/006 are the required characterization net)
- **Depends on**: plans/002-ci-and-single-check-entrypoint.md (review-contracts tests exist), plans/006-tighten-artifact-quality-gates.md (final vocabulary — consolidate once, after tightening)
- **Category**: tech-debt
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

The same HTML-invariant rules are maintained in three places across two languages: required social-card meta, the HTML-native feature vocabulary, external-resource patterns, and the `hasMeta`/`attrValue`/`hasAccessibleName` helpers exist in `scripts/perf_harness.py`, `scripts/lint-artifact.mjs`, AND `scripts/review-contracts.mjs`. Sync is a comment-level promise (`lint-artifact.mjs:43`: "Same feature vocabulary as perf_harness.py's `_HTML_NATIVE_FEATURES`"). Adding one required meta tag or feature detector means editing three files; a missed copy silently weakens one gate while the others stay green. This plan consolidates the JS side into one shared module and adds a cross-language parity test so JS↔Python drift fails the suite instead of passing silently. (Full unification into one language was considered and rejected: the Python harness deliberately runs without Node, and the linters deliberately run without Python.)

## Current state

Duplication map (all verified at `e0278cb`; plans 002/006 may have shifted line numbers but not the structure):

- `scripts/lint-artifact.mjs`: `REQUIRED_META` (:34-41), `FEATURES` (:44-56), `EXTERNAL_RESOURCE` (:59-67), `hasMeta` (:75-78), `attrValue` (:80-82), `hasAccessibleName` (:84-90).
- `scripts/review-contracts.mjs`: `hasMeta` (:29-32), `attrValue` (:34-37), `hasAccessibleName` (:39-45) — byte-equivalent helpers; meta requirements inlined as literal checks (:53-66: viewport, description, og:title/og:description/og:type/og:site_name, twitter:card, favicon).
- `scripts/perf_harness.py`: `_EXTERNAL_RESOURCE_RES` (:476-484), `_REQUIRED_META` (:543-550), `_HTML_NATIVE_FEATURES` (:552-564), `_has_meta` (:574-575) — the deliberate Python second implementation (kept: the harness must run without Node).
- Regex source portability fact this plan relies on: the JS regex literal `/type=["']search["']/i` and the Python raw string `r"type=[\"']search[\"']"` have the **identical pattern source** once JS's `.source` is read and Python's string is unescaped — so the two vocabularies can be compared textually via `node -e` JSON output against the Python dict's pattern strings.
- Both `.mjs` entry points are ESM (import syntax already in use), so a shared `import { … } from "./lib/html-checks.mjs"` works without any packaging change. `scripts/check-tokens.mjs` shows the repo-root/`fileURLToPath` idiom if pathing is needed.
- Tests that lock current behavior (must all pass unmodified after the refactor): `tests/test_linters.py` — lint-artifact positive/negative cases, check-tokens, review-contracts (from plan 002), tightened-vocabulary negatives (from plan 006).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Full gates | `make check` (plan 002) | exit 0 |
| Tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Lint all examples | `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` | 0 fail |
| Contracts | `node scripts/review-contracts.mjs` | passes for 25 HTML files |
| Dump JS vocab | `node -e "import('./scripts/lib/html-checks.mjs').then(m => console.log(JSON.stringify({meta: m.REQUIRED_META, features: Object.fromEntries(Object.entries(m.FEATURES).map(([k,v]) => [k, v.source]))})))"` | JSON on stdout (after step 1) |

## Scope

**In scope** (the only files you should modify/create):
- `scripts/lib/html-checks.mjs` (create)
- `scripts/lint-artifact.mjs`, `scripts/review-contracts.mjs` (import from the lib; delete their local copies)
- `tests/test_linters.py` (add the parity test)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `scripts/perf_harness.py` — the Python implementation stays; the parity TEST is the bridge, not a code change. (Exception: if the parity test reveals the two vocabularies already differ, STOP — do not "fix" either side unilaterally.)
- `scripts/check-tokens.mjs` — no shared vocabulary with the other two.
- `bin/og-card.mjs` — standalone by design (runs against arbitrary artifacts outside the repo).
- Any check *semantics* — this is a move-only refactor; behavior must be bit-identical.

## Git workflow

- Branch: `advisor/009-single-source-check-vocab`
- One commit, imperative subject, e.g. `Extract shared html-checks module for the linters + JS/Python vocabulary parity test`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Create `scripts/lib/html-checks.mjs`

Move (verbatim) from `lint-artifact.mjs`: `REQUIRED_META`, `FEATURES`, `EXTERNAL_RESOURCE`, `hasMeta`, `attrValue`, `hasAccessibleName`. Export all six. Header comment: this module is the single source for the HTML-invariant vocabulary shared by lint-artifact and review-contracts; `scripts/perf_harness.py` carries a deliberate Python mirror, and `tests/test_linters.py::test_js_python_vocabulary_parity` fails if they drift.

**Verify**: the vocab-dump command from the table prints JSON with 6 meta entries and 11 feature keys.

### Step 2: Point `lint-artifact.mjs` at the lib

Replace the moved definitions with `import { REQUIRED_META, FEATURES, EXTERNAL_RESOURCE, hasMeta, attrValue, hasAccessibleName } from "./lib/html-checks.mjs";` — note lint-artifact is invoked as `node scripts/lint-artifact.mjs`, so the relative specifier resolves from the script file (ESM resolves relative to the importing module, not cwd) — this is why the lib lives in `scripts/lib/`.

**Verify**: `node scripts/lint-artifact.mjs examples/dashboard.html` → PASS; `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` → 0 fail; the plan-006 negative tests still pass: `uv run --with pytest pytest tests/test_linters.py -q`.

### Step 3: Point `review-contracts.mjs` at the lib

Replace its local `hasMeta`/`attrValue`/`hasAccessibleName` (:29-45) with the same import. Then replace the inlined meta literals (:56-66) with a loop over the shared `REQUIRED_META` **plus** its two extra checks that lint-artifact keeps separately (viewport at :53-55, favicon at :67-69) — read both files' meta checks side-by-side first: lint-artifact checks viewport/favicon separately from `REQUIRED_META` too, so the shared table is exactly the six social-card entries; keep viewport/favicon as local checks in both consumers (matching current behavior bit-for-bit).

Note: `review-contracts.mjs` reads files relative to `process.cwd()` (:4) — the import change doesn't alter that; run it from repo root as always.

**Verify**: `node scripts/review-contracts.mjs` → `review contracts passed for 25 HTML files`; plan-002's review-contracts tests pass.

### Step 4: Add the cross-language parity test

Append to `tests/test_linters.py`:

```python
def test_js_python_vocabulary_parity():
    """The JS lib (scripts/lib/html-checks.mjs) and the Python harness carry
    the same REQUIRED_META and feature vocabulary. A change to one without
    the other silently weakens a gate — fail loudly instead."""
    import json
    r = _run("-e",
        "import('./scripts/lib/html-checks.mjs').then(m => console.log(JSON.stringify({"
        "meta: m.REQUIRED_META,"
        "features: Object.fromEntries(Object.entries(m.FEATURES).map(([k,v]) => [k, v.source]))"
        "})))")
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)

    from importlib.machinery import SourceFileLoader
    import importlib.util, sys
    loader = SourceFileLoader("perf_harness", str(REPO / "scripts" / "perf_harness.py"))
    spec = importlib.util.spec_from_loader("perf_harness", loader)
    h = importlib.util.module_from_spec(spec)
    sys.modules["perf_harness"] = h
    loader.exec_module(h)

    assert [list(x) for x in h._REQUIRED_META] == js["meta"]
    assert set(h._HTML_NATIVE_FEATURES) == set(js["features"])
    for key, py_pattern in h._HTML_NATIVE_FEATURES.items():
        assert py_pattern == js["features"][key], (
            f"feature '{key}' diverged:\n  py: {py_pattern}\n  js: {js['features'][key]}")
```

If any pattern pair differs only by an escaping artifact (e.g. JS `\/` vs Python `/`), normalize *in the test* (document the normalization) — do not change either implementation to satisfy the test.

**Verify**: `uv run --with pytest pytest tests/test_linters.py -q` → all pass. Manual negative: temporarily change one JS pattern, confirm the parity test fails naming the key, revert.

### Step 5: Full gates

**Verify**: `make check` → exit 0 (or the six individual gates if 002 hasn't landed — but 002 is a declared dependency); `git status` → only in-scope files.

## Test plan

- The refactor itself is characterization-tested by the entire existing `tests/test_linters.py` suite (positive + negative cases from plans 002/006) — zero behavior change is the requirement.
- New: `test_js_python_vocabulary_parity` (step 4) — the drift alarm this plan exists to install. One manual negative run documented in step 4.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `scripts/lib/html-checks.mjs` exists; `grep -c "REQUIRED_META" scripts/lint-artifact.mjs scripts/review-contracts.mjs` shows imports, not local definitions (the table is defined exactly once in JS: `grep -rn "og:site_name" scripts/*.mjs scripts/lib/*.mjs` → one definition site + consumers)
- [ ] `node scripts/lint-artifact.mjs index.html examples/*.html examples/primitives/*.html` → 0 fail
- [ ] `node scripts/review-contracts.mjs` → passes for 25 HTML files, output identical to pre-refactor
- [ ] `test_js_python_vocabulary_parity` passes; full pytest suite passes
- [ ] `make check` exits 0
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The parity test reveals the JS and Python vocabularies ALREADY differ on the unmodified tree — that is a live enforcement gap (exactly what this plan predicts can happen); report the diff, don't pick a winner.
- `review-contracts.mjs` output changes in any way after step 3 (a meta check got looser/stricter in the move).
- Plans 002/006 are not DONE in `plans/README.md` — consolidating before the vocabulary is final means doing this twice.
- The import fails under `node` invoked from a different cwd than repo root in any existing caller (check `tests/test_linters.py` `_run` uses `cwd=REPO` — it does).

## Maintenance notes

- Future vocabulary changes: edit `scripts/lib/html-checks.mjs` + `scripts/perf_harness.py` together; the parity test enforces the pair. The Python mirror is deliberate (harness must run Node-free) — do not "simplify" it away by shelling out, or the harness grows a Node dependency.
- If a fourth checker ever appears, it imports the lib — never copies.
- Reviewer should scrutinize step 3's meta-loop replacement in review-contracts against the old inlined literals line-by-line: this is the one place the refactor could silently change which tags are required.
