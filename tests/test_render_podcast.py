"""Smoke tests for bin/render-podcast against the fixture episode package.

Run from the repo root:
    uv run --with pytest pytest tests/test_render_podcast.py -v

These are intentionally low-cardinality assertions — they check that the
renderer produces both expected files, that the file contracts the SKILL.md
documents are present (folder-tabs, theme toggle, focus-visible, sr-only h1),
and that the a11y gotchas we've already burned a PR fixing don't regress
(role="tablist", color: var(--muted) on the tab strip, missing h1, etc.).
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "episode.package.json"
RENDERER = REPO / "bin" / "render-podcast"


def _load_renderer():
    """Import bin/render-podcast as a module despite the hyphen + no .py suffix."""
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("render_podcast", str(RENDERER))
    spec = importlib.util.spec_from_loader("render_podcast", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_podcast"] = mod
    loader.exec_module(mod)
    return mod


def test_renderer_produces_both_files(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    briefing = tmp_path / "podcast-at-a-glance.html"
    transcript = tmp_path / "annotated-transcript.html"
    assert briefing.exists(), "renderer should write podcast-at-a-glance.html"
    assert transcript.exists(), "renderer should write annotated-transcript.html"
    assert briefing.stat().st_size > 5_000, "briefing should be a real page, not a stub"
    assert transcript.stat().st_size > 5_000, "transcript should be a real page, not a stub"


def test_briefing_has_required_contract_elements(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    html = (tmp_path / "podcast-at-a-glance.html").read_text(encoding="utf-8")
    # Contract: folder-tabs with the briefing tab marked active
    assert 'class="folder-tab active"' in html
    assert 'aria-current="page"' in html
    # Contract: theme toggle present, light-default (no body class on initial render)
    assert 'id="theme-toggle"' in html
    # Contract: SVG glyphs (Unicode ☾/☀ rendered as { on iOS Safari)
    assert "glyph-light" in html and "glyph-dark" in html
    # Contract: WCAG fix — inactive folder-tab uses --ink-soft, not --muted
    assert ".folder-tab:not(.active) { color: var(--ink-soft)" in html
    # Contract: focus-visible outlines exist
    assert ":focus-visible" in html


def test_transcript_has_h1_and_chapter_rail(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    html = (tmp_path / "annotated-transcript.html").read_text(encoding="utf-8")
    # a11y regression guard: transcript MUST have an h1 (was missing pre-v2.4.0)
    assert "<h1" in html, "transcript must have an h1 for heading hierarchy"
    assert 'class="sr-only"' in html, "h1 should be screen-reader-only"
    # Chapter rail present + each fixture chapter renders
    assert 'class="chapter-rail"' in html
    assert "Apps vs instruments" in html
    assert "Round-trip editing" in html
    # Chapter rail + chapter breaks both render fixture timestamps
    assert "00:00" in html and "21:15" in html
    # Speaker text rendered (uppercase per .speaker style is CSS — assert raw casing)
    assert "Mara Ito" in html and "Vikram Shah" in html


def test_no_dead_aria_tab_roles(tmp_path):
    """role='tablist'/'tab' are wrong here — these are page nav links, not in-page tabs."""
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    for name in ("podcast-at-a-glance.html", "annotated-transcript.html"):
        html = (tmp_path / name).read_text(encoding="utf-8")
        assert 'role="tablist"' not in html, f"{name}: stripped in v2.4.0 — these are nav, not tabs"
        assert 'role="tab"' not in html, f"{name}: stripped in v2.4.0 — these are nav, not tabs"
        assert "aria-selected" not in html, f"{name}: aria-selected belongs to tabs only"


def test_outputs_are_self_contained_source_documents(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    for name in ("podcast-at-a-glance.html", "annotated-transcript.html"):
        html = (tmp_path / name).read_text(encoding="utf-8")
        assert '<link rel="icon" href="data:,">' in html, f"{name}: must suppress favicon network requests"
        assert 'type="application/json" id="episode-data"' in html, f"{name}: must embed the source package data"
        assert "podcast-transformer/package-v1" in html, f"{name}: data island should include fixture schema"
        assert '<meta name="twitter:card" content="summary">' in html, f"{name}: default social card is summary"
        assert "summary_large_image" not in html, f"{name}: large image card needs an actual hosted image"
        assert "og:image" not in html, f"{name}: generated output is self-contained by default"
        assert "twitter:image" not in html, f"{name}: generated output is self-contained by default"


def test_episode_data_island_escapes_script_delimiters():
    rp = _load_renderer()
    island = rp.episode_data_island({"episode": {"title": "</script><script>alert(1)</script>"}})
    assert 'type="application/json" id="episode-data"' in island
    assert "</script><script>" not in island
    assert "\\u003c/script" in island


def test_inspector_toggle_dead_below_breakpoint(tmp_path):
    """Inspector toggle is hidden at ≤820 (shared) and ≤1180 (briefing only)."""
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    briefing = (tmp_path / "podcast-at-a-glance.html").read_text(encoding="utf-8")
    transcript = (tmp_path / "annotated-transcript.html").read_text(encoding="utf-8")
    # Shared rule
    for html in (briefing, transcript):
        assert "@media (max-width: 820px) { #inspector-toggle { display: none; } }" in html
    # Briefing-only extension to 1180 (transcript chapter rail is collapsible ≥821)
    assert "@media (max-width: 1180px) { #inspector-toggle { display: none; } }" in briefing
    assert "@media (max-width: 1180px) { #inspector-toggle { display: none; } }" not in transcript


def test_briefing_renders_fixture_terms_and_read_next_links(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    html = (tmp_path / "podcast-at-a-glance.html").read_text(encoding="utf-8")

    assert "When memory is the moat, durable instruments win over ephemeral apps." in html
    assert '<div class="name">File of record</div>' in html
    assert 'Vikram Shah<span class="ext">↗</span>' in html
    assert 'Notion<span class="ext">↗</span>' in html
    assert 'Figma<span class="ext">↗</span>' in html
    assert 'Why workflows beat apps' in html
    assert 'https://example.invalid/workflows-beat-apps' in html


def test_malformed_json_fails_cleanly(tmp_path, capsys):
    rp = _load_renderer()
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    rc = rp.main([str(bad), "-o", str(tmp_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "invalid JSON" in captured.err
    assert "Traceback" not in captured.err


def test_missing_episode_key_fails_cleanly(tmp_path, capsys):
    rp = _load_renderer()
    noep = tmp_path / "noep.json"
    noep.write_text("{}", encoding="utf-8")
    rc = rp.main([str(noep), "-o", str(tmp_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "'episode'" in captured.err
    assert "Traceback" not in captured.err


def test_javascript_urls_are_not_linked(tmp_path):
    rp = _load_renderer()
    pkg = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pkg["terms"][1]["url"] = "javascript:alert(1)"
    pkg["read_next"][0]["url"] = "JAVASCRIPT:alert(1)"
    pkg["episode"]["episode_url"] = "data:text/html,x"
    tainted = tmp_path / "tainted.json"
    tainted.write_text(json.dumps(pkg), encoding="utf-8")

    rc = rp.main([str(tainted), "-o", str(tmp_path)])
    assert rc == 0
    for name in ("podcast-at-a-glance.html", "annotated-transcript.html"):
        html_lower = (tmp_path / name).read_text(encoding="utf-8").lower()
        assert 'href="javascript' not in html_lower, f"{name}: javascript: URL became a live href"
        assert 'href="data:text/html' not in html_lower, f"{name}: data: URL became a live href"


def test_https_urls_still_linked(tmp_path):
    rp = _load_renderer()
    rp.main([str(FIXTURE), "-o", str(tmp_path)])
    briefing = (tmp_path / "podcast-at-a-glance.html").read_text(encoding="utf-8")
    assert 'href="https://example.invalid' in briefing
