# Plan 003: Make bin/og-card.mjs fail safely, inject reliably, and gain test coverage

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- bin/og-card.mjs tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (composes with plan 002's CI; its tests must skip without Chrome)
- **Category**: bug
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

`bin/og-card.mjs` is a hard gate in the publish flow (`SKILL.md:527-533`: generate the card, `--inject`, then `lint-artifact --published` *requires* og:image) and it is the only tool in the repo that rewrites a finished artifact in place — yet it has zero tests and four verified defects: (1) the Chrome path is hardcoded macOS-only with no env override, so it hard-crashes with a raw spawn error anywhere else; (2) on any Chrome failure it leaks its temp file and dies with an uncaught stack trace; (3) the temp path is predictable (`os.tmpdir() + fixed name`), a classic insecure-temp-file pattern; (4) `--inject` on an artifact lacking a `twitter:card` meta silently injects nothing while logging success — the exact gap the tool exists to close.

## Current state

`bin/og-card.mjs` is 73 lines; the relevant parts as they exist today:

```js
// bin/og-card.mjs:49-59
const tmp = path.join(os.tmpdir(), 'og-card-' + path.basename(file) + '.html');
fs.writeFileSync(tmp, card);
// Per-artifact name so a shared reports dir doesn't collide (report-portal
// copies this to og-card.png inside each published slug dir.)
const stem = path.basename(file).replace(/\.html?$/i, '');
const out = path.join(path.dirname(path.resolve(file)), `${stem}.og.png`);
const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
  '--window-size=1200,630', `--screenshot=${out}`, `file://${tmp}`], { stdio: 'ignore' });
fs.unlinkSync(tmp);
console.log('wrote ' + out);
```

```js
// bin/og-card.mjs:61-73
if (inject) {
  if (!/property=["']og:image["']/i.test(html)) {
    const tags = `<meta property="og:image" content="og-card.png">\n<meta name="twitter:image" content="og-card.png">\n`;
    // upgrade twitter:card to large image
    html = html.replace(/<meta\s+name=["']twitter:card["']\s+content=["'][^"']*["']\s*>/i,
      '<meta name="twitter:card" content="summary_large_image">');
    html = html.replace(/(<meta\s+name=["']twitter:card["'][^>]*>)/i, `$1\n${tags.trim()}`);
    fs.writeFileSync(file, html);
    console.log('injected og:image + twitter:image into ' + path.basename(file) + '; twitter:card → summary_large_image');
  } else {
    console.log('og:image already present — not re-injecting');
  }
}
```

Failure modes, precisely: `execFileSync` throws if the binary is absent or exits nonzero → uncaught → `unlinkSync` at :58 never runs (temp leak) and the user sees a Node stack, not a message. In the inject branch, if no `twitter:card` tag exists both `replace` calls are no-ops, but `writeFileSync` + the success log still run.

Test conventions to follow: `tests/test_linters.py` runs Node scripts by subprocess with `NODE = shutil.which("node")` and `pytestmark = pytest.mark.skipif(NODE is None, ...)` (lines 21-23) and a `_run(*args)` helper (lines 26-32). Renderer tests build fixture HTML inline in `tmp_path` (e.g. `tests/test_linters.py:72-89`). Chrome-dependent assertions must skip when Chrome is unavailable — no existing example of that skip exists; create it analogously to the node skip.

Design constraint from SKILL.md (`SKILL.md:57-62`): injected paths are relative (`og-card.png` sibling), `twitter:card` upgrades to `summary_large_image`. Do not change the injected tag values.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Targeted | `uv run --with pytest pytest tests/test_og_card.py -q` | all pass (new file) |
| Manual card run (macOS w/ Chrome) | `node bin/og-card.mjs examples/editorial.html` | `wrote …/editorial.og.png`; then delete the PNG — do not commit it |
| Full gates | `uv run python scripts/perf_harness.py --check --no-report && node scripts/review-contracts.mjs` | both exit 0 |

## Scope

**In scope** (the only files you should modify/create):
- `bin/og-card.mjs`
- `tests/test_og_card.py` (create)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `scripts/lint-artifact.mjs` — its `--published` og:image requirement is the consumer of this tool, not part of it.
- `SKILL.md` step 8 — the documented CLI surface (`og-card.mjs <file> --inject`) must keep working unchanged.
- Any committed example HTML. If your manual run injects tags into an example, `git checkout -- <file>` it — examples are self-contained by contract and MUST NOT gain og:image (`scripts/perf_harness.py:601-602` fails the build on image-card metadata in examples).

## Git workflow

- Branch: `advisor/003-og-card-hardening`
- One commit, imperative subject, e.g. `Harden og-card.mjs: browser discovery, safe temp dir, honest --inject, tests`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Restructure og-card.mjs for safety (single file, stdlib-only, same CLI)

Apply all four fixes:

1. **Browser discovery.** Replace the hardcoded `chrome` const with a resolver: use `process.env.OG_CARD_CHROME` if set; else probe an ordered candidate list with `fs.existsSync` — macOS Google Chrome (current path), macOS Chromium (`/Applications/Chromium.app/Contents/MacOS/Chromium`), macOS Edge (`/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`), Linux `google-chrome`, `chromium`, `chromium-browser` resolved via PATH probing or well-known `/usr/bin` paths. If none found: print `og-card: no Chrome/Chromium found — set OG_CARD_CHROME to a browser binary` to stderr and `process.exit(1)`.
2. **Safe temp handling.** `const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'og-card-'))` and write the card HTML inside it; wrap the screenshot call in `try { … } catch (e) { console.error('og-card: screenshot failed: ' + e.message); process.exitCode = 1; } finally { fs.rmSync(tmpDir, { recursive: true, force: true }); }`. On screenshot failure, do not proceed to inject.
3. **Honest inject.** In the inject branch, after the two `replace` calls, check whether `html` actually changed (compare against the pre-replace string). If `twitter:card` was absent, fall back to inserting the two meta tags (plus a fresh `<meta name="twitter:card" content="summary_large_image">`) immediately after `</title>` (or after `<head…>` if no title). Only `writeFileSync` + log success when the content changed; otherwise print an error to stderr and exit 1.
4. **Testability without Chrome.** Support a `--no-screenshot` flag (document it in the usage comment as "for tests/CI") that skips browser resolution and the screenshot entirely, but still performs `--inject`. Keep the flag out of SKILL.md — it is a test affordance, not part of the publish contract.

Keep the card-HTML template, token extraction (`bin/og-card.mjs:22-32`), and injected tag values byte-identical.

**Verify**: `node bin/og-card.mjs` (no args) → usage + exit 2 (unchanged). `node --check bin/og-card.mjs` → exit 0.

### Step 2: Write `tests/test_og_card.py`

Follow the subprocess pattern from `tests/test_linters.py` (copy the `_run`-style helper; module-level `pytest.mark.skipif(NODE is None, …)`). A minimal valid fixture (reuse the meta-complete head from `tests/test_linters.py:74-85`, plus a `<title>`). Cases:

1. **inject adds tags**: run `node bin/og-card.mjs <tmp fixture> --no-screenshot --inject` on a fixture *with* `twitter:card content="summary"`; assert exit 0, file now contains `property="og:image" content="og-card.png"`, `name="twitter:image"`, and `twitter:card` content is `summary_large_image`.
2. **inject without twitter:card falls back**: fixture with full og:* meta but no `twitter:card` tag; assert exit 0 and all three tags present after `</title>`.
3. **already-injected is a no-op**: run inject twice; second run prints `already present` and exits 0; file unchanged (`read before == read after`).
4. **missing browser fails cleanly**: run *without* `--no-screenshot` and with `OG_CARD_CHROME=/nonexistent/browser` in the subprocess env; assert exit 1 and a message containing `og-card` on stderr — not a Node stack trace (assert `Traceback`-equivalent `at Object.` stack lines absent from stderr, or simply assert the friendly message is present).
5. **screenshot path (conditional)**: only if the real default Chrome path exists (`Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome').exists()`), run a full non-inject invocation on the fixture and assert the `.og.png` sibling exists and is >10_000 bytes; `pytest.mark.skipif` otherwise.

**Verify**: `uv run --with pytest pytest tests/test_og_card.py -v` → 4-5 pass (5th may skip off-macOS).

### Step 3: Full-suite regression pass

**Verify**: `uv run --with pytest pytest tests/ -q` → all pass; `uv run python scripts/perf_harness.py --check --no-report` → exit 0; `git status` → only in-scope files modified (in particular NO modified files under `examples/`).

## Test plan

Covered by step 2 — five cases: inject-happy-path, inject-fallback (the silent-no-op bug this plan fixes), idempotence, clean failure without a browser, and a conditional real-screenshot smoke test. Model the file on `tests/test_linters.py`; keep every case runnable without Chrome except the explicitly-skipped smoke test.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `uv run --with pytest pytest tests/test_og_card.py -q` → all pass (Chrome-dependent case may skip)
- [ ] `uv run --with pytest pytest tests/ -q` → all pass
- [ ] `OG_CARD_CHROME=/nonexistent node bin/og-card.mjs <some tmp .html>` → exit 1 with a one-line stderr message, and `ls "$TMPDIR" | grep og-card-` shows no leftover og-card temp entries from the run
- [ ] `node bin/og-card.mjs <fixture> --no-screenshot --inject` on a twitter:card-less fixture → tags present afterward (the old code silently skipped this)
- [ ] `git status` shows no modified files outside the in-scope list; no `.og.png` files staged
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `bin/og-card.mjs` no longer matches the excerpts above (drifted since planning).
- Any fix requires adding an npm dependency (e.g. a browser-discovery package) — the repo is deliberately zero-dependency; report instead.
- The full-screenshot smoke test fails **with Chrome present** — the card template may have regressed; report rather than tweaking the template.
- You find yourself editing `scripts/lint-artifact.mjs` or SKILL.md to make something pass.

## Maintenance notes

- Plan 002's CI runs the pytest suite; these tests are Chrome-free by design (`--no-screenshot`), so they'll run in CI. The conditional smoke test self-skips there.
- If report-portal's og-card handling changes (it copies `<stem>.og.png` → `og-card.png` in the slug dir, per the comment at `bin/og-card.mjs:51-52` and `SKILL.md:531`), the injected relative `content="og-card.png"` value must be revisited in both places.
- Reviewer should scrutinize: the inject fallback insertion point (after `</title>`) against a real artifact head, and that `--no-screenshot` cannot leak into documented usage.
- Deferred deliberately: cross-platform screenshot support beyond browser discovery (Windows paths), and any retry logic — out of scope for a publish-time dev tool.
