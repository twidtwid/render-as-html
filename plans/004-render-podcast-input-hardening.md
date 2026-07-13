# Plan 004: Give bin/render-podcast a clean error contract and safe URL handling

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat e0278cb..HEAD -- bin/render-podcast tests/test_render_podcast.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: correctness + security
- **Planned at**: commit `e0278cb`, 2026-07-12

## Why this matters

`bin/render-podcast` is the repo's one deterministic CLI, consumed by the podcastextract pipeline. Two input-handling gaps: (1) a malformed `episode.package.json`, or one missing the top-level `"episode"` key, aborts with a raw Python traceback instead of the friendly one-line errors the CLI already prints for missing files — a truncated or schema-drifted package is exactly the most likely bad input; (2) every substituted field is HTML-escaped via `esc()`, which prevents markup breakout, but URL fields go into live `href` attributes with **no scheme restriction** — a `javascript:` (or `data:text/html`) URL in a term link, episode source link, or read-next link becomes a clickable script-executing anchor. The package is built from scraped publisher show-notes, and rendered artifacts get published to shared origins, so link fields are the remaining untrusted-data sink (the JSON data island is already hardened and tested against `</script>` breakout at `tests/test_render_podcast.py:103-108`).

## Current state

- `bin/render-podcast:34-35` — unguarded parse:
  ```python
  def load_package(package_path: Path) -> dict:
      return json.loads(package_path.read_text(encoding="utf-8"))
  ```
- `bin/render-podcast:358-359` and `:523-524` — unguarded key access: `ep = pkg["episode"]` in both `render_transcript` and `render_briefing`.
- `bin/render-podcast:740-747` — `main()` already has the friendly-error convention to match:
  ```python
  if not package_path.exists():
      print(f"not found: {package_path}", file=sys.stderr)
      return 1
  if not TEMPLATE_PATH.exists():
      print(f"template not found: {TEMPLATE_PATH}", file=sys.stderr)
      ...
      return 1
  ```
- `bin/render-podcast:227-228` — the escaper: `def esc(s): return html.escape(s or "", quote=True)`.
- The three href sink sites (all verified):
  - `bin/render-podcast:280-282` (term link): `name_html = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{name}<span class="ext">↗</span></a>'`
  - `bin/render-podcast:408-410` (transcript Source tab) and the equivalent briefing Source tab (~line 572): `source_tab = f'<a class="folder-tab external listen" href="{esc(episode_url)}" …>'`
  - `bin/render-podcast:603-608` (read-next links): `url = esc(link.get("url") or "#")` then `f'<li><a href="{url}" …>'`
  Find every sink with: `grep -n 'href="{' bin/render-podcast` — handle all hits.
- Test conventions: `tests/test_render_podcast.py` imports the hyphenated script via `SourceFileLoader` (`_load_renderer`, lines 22-30) and calls `rp.main([str(FIXTURE), "-o", str(tmp_path)])`. Note `main()` **returns** an int (no `sys.exit` in library use), so tests assert on the return value. Fixture: `tests/fixtures/episode.package.json`.
- Repo conventions: stdlib only; error messages are lowercase one-liners to stderr; `esc()` naming style for small helpers.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Targeted tests | `uv run --with pytest pytest tests/test_render_podcast.py -q` | all pass (7 now; 11+ after) |
| Full tests | `uv run --with pytest pytest tests/ -q` | all pass |
| Perf gate (times this CLI) | `uv run python scripts/perf_harness.py --check --no-report` | exit 0 |
| Manual smoke | `bin/render-podcast tests/fixtures/episode.package.json -o /tmp/rp-smoke` | prints both output paths, exit 0 |

## Scope

**In scope** (the only files you should modify):
- `bin/render-podcast`
- `tests/test_render_podcast.py`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `examples/podcast.html` / `examples/podcast-transcript.html` — canonical artifacts; the renderer reads the example's `<style>` at runtime but this plan changes no styling.
- `tests/fixtures/episode.package.json` — the shared fixture other tests depend on; craft bad inputs inline in `tmp_path`, don't mutate the fixture.
- The data-island escaping (`episode_data_island`, `bin/render-podcast:47-50`) — already correct and tested.
- Output structure/markup beyond dropping an href on unsafe URLs.

## Git workflow

- Branch: `advisor/004-render-podcast-input-hardening`
- One commit, imperative subject, e.g. `render-podcast: friendly errors on bad packages, scheme allow-list on hrefs`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Guard package loading

In `main()` (matching the existing friendly-error style at `:740-747`):

- Wrap the `load_package(package_path)` call: on `json.JSONDecodeError as e`, print `f"invalid JSON in {package_path}: {e}"` to stderr, return 1.
- After loading, validate: `if not isinstance(pkg, dict) or "episode" not in pkg:` → print `f"package missing top-level 'episode' object: {package_path}"` to stderr, return 1.

Do this in `main()` (not inside `load_package`) so `render_briefing`/`render_transcript` keep their current signatures for the tests that call them via a pre-loaded `pkg`.

**Verify**: `echo 'not json' > /tmp/bad.json && bin/render-podcast /tmp/bad.json; echo "exit=$?"` → one-line stderr message, `exit=1`, no traceback. Same for `echo '{}' > /tmp/noep.json`.

### Step 2: Add a `safe_url()` helper and route every href sink through it

Next to `esc()` (`bin/render-podcast:227`), add:

```python
_SAFE_URL_SCHEMES = ("http://", "https://", "mailto:")

def safe_url(url: str | None) -> str:
    """Only http(s)/mailto URLs may become live hrefs. Anything else
    (javascript:, data:, vbscript:, protocol-relative tricks) renders as
    plain text instead of a link."""
    u = (url or "").strip()
    return u if u.lower().startswith(_SAFE_URL_SCHEMES) else ""
```

At each sink found by `grep -n 'href="{' bin/render-podcast`:

- **Term links** (`render_term`, :278-282): `url = safe_url(term.get("url"))` — the existing `if url:` branch then naturally falls back to the plain-text `name_html = name` path for unsafe URLs.
- **Source tabs** (transcript ~:397/:408-410, briefing equivalent ~:572): apply `safe_url()` to `episode_url` where it's read from the package; the existing `if episode_url:` guard then skips the tab entirely for unsafe values.
- **Read-next links** (:603-608): `raw = safe_url(link.get("url") or "")`; if empty, render the `<li>` with the label as plain text (no `<a>`), keeping the note span.
- Relative in-bundle links (`href="annotated-transcript.html"`, `href="podcast-at-a-glance.html"`) are literals, not package data — leave them.

Keep `esc()` applied ON TOP of `safe_url()` at the attribute site (escape-then-emit is unchanged; `safe_url` only decides *whether* it becomes an href).

**Verify**: `grep -n 'href="{' bin/render-podcast` — every hit whose value originates from `pkg` now passes through `safe_url`. `bin/render-podcast tests/fixtures/episode.package.json -o /tmp/rp-smoke` still exits 0 and `grep -c 'https://example.invalid' /tmp/rp-smoke/podcast-at-a-glance.html` ≥1 (https URLs still linked).

### Step 3: Add tests

Append to `tests/test_render_podcast.py` (reuse `_load_renderer`; build bad inputs in `tmp_path`):

1. `test_malformed_json_fails_cleanly`: write `not json` to `tmp_path/"bad.json"`; `rc = rp.main([str(bad), "-o", str(tmp_path)])`; assert `rc == 1`. Capture stderr via `capsys` and assert `"invalid JSON"` in it and `"Traceback"` not in it.
2. `test_missing_episode_key_fails_cleanly`: `{}` package → `rc == 1`, stderr mentions `'episode'`.
3. `test_javascript_urls_are_not_linked`: copy the fixture dict (`json.loads(FIXTURE.read_text())`), set one term's `url` to `javascript:alert(1)`, one `links`/`read_next` entry's `url` to `JAVASCRIPT:alert(1)` (case test), and `episode["episode_url"]` to `data:text/html,x`; write to `tmp_path`, render, and assert `javascript:` and `data:text/html` do NOT appear inside any `href="` in either output file (a plain-text occurrence inside the JSON data island is expected and fine — assert specifically `'href="javascript' not in html.lower()` etc.).
4. `test_https_urls_still_linked`: unmodified fixture render — assert `'href="https://example.invalid'` present (guards against an over-strict allow-list).

**Verify**: `uv run --with pytest pytest tests/test_render_podcast.py -q` → all pass (11).

### Step 4: Full gates

**Verify**: `uv run --with pytest pytest tests/ -q` → all pass; `uv run python scripts/perf_harness.py --check --no-report` → exit 0 (the harness renders three fixtures through this CLI — a crash here means step 2 broke a render path).

## Test plan

Step 3's four tests: two error-contract cases (malformed JSON, missing key), one XSS-vector case covering all three sink types with case-variant schemes, one no-false-positive case. Pattern: existing tests in the same file (e.g. `test_briefing_renders_fixture_terms_and_read_next_links`, lines 125-137, shows fixture-driven assertions on rendered href content).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `bin/render-podcast /tmp/bad.json` (non-JSON content) → exit 1, single-line stderr, no traceback
- [ ] Rendering a package containing `javascript:`/`data:` URLs yields no `href="javascript…"`/`href="data:text/html…"` in either output
- [ ] Rendering the unmodified fixture still links `https://example.invalid/...` term/read-next URLs
- [ ] `uv run --with pytest pytest tests/ -q` → all pass (4 new)
- [ ] `uv run python scripts/perf_harness.py --check --no-report` → exit 0
- [ ] `git status` shows no modified files outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The excerpts in "Current state" don't match the live file (drift).
- `grep -n 'href="{' bin/render-podcast` reveals a sink whose data flow you cannot trace to either package data or a literal — report it rather than guessing.
- The fixture legitimately contains a URL scheme outside http/https/mailto (it shouldn't — all fixture URLs are `https://example.invalid/...`); if it does, the allow-list decision needs the operator.
- Any existing test fails after step 2 for a reason other than an assertion you expected to update (none should need updating).

## Maintenance notes

- If podcastextract's package schema ever legitimately carries other schemes (e.g. `spotify:` deep links), extend `_SAFE_URL_SCHEMES` deliberately — never by removing the check.
- Plan 008 refactors this file's version strings and adds a structural parity test; land this plan first (both touch `bin/render-podcast`; this one is smaller).
- Reviewer should scrutinize: that `safe_url` is applied where the value *enters* the href decision (so fallback-to-text paths engage), not merely wrapped around `esc()` at the emit site.
