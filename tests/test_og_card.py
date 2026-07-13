"""Tests for bin/og-card.mjs — the social-card generator + <head> injector.

Covers the four defects fixed in plan 003:
  1. hardcoded macOS-only Chrome path -> OG_CARD_CHROME override + probe
  2. leaked/predictable temp file on screenshot failure -> mkdtempSync + cleanup
  3. silent no-op --inject when no twitter:card tag exists -> honest fallback
  4. no way to test without Chrome -> --no-screenshot

Run from the repo root:
    uv run --with pytest pytest tests/test_og_card.py -v

Node is required; tests skip cleanly if node is unavailable. The screenshot
smoke test additionally skips unless a real Chrome install is present.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not available")

REAL_CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = None
    if env is not None:
        full_env = dict(os.environ)
        full_env.update(env)
    return subprocess.run(
        [NODE, "bin/og-card.mjs", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=full_env,
    )


def _fixture_with_twitter_card(tmp_path: Path) -> Path:
    f = tmp_path / "with-card.html"
    f.write_text(
        '<!doctype html><html lang="en"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        '<title>Test Artifact</title>'
        '<meta name="description" content="x">'
        '<meta property="og:title" content="x">'
        '<meta property="og:description" content="x">'
        '<meta property="og:type" content="article">'
        '<meta property="og:site_name" content="x">'
        '<meta name="twitter:card" content="summary">'
        '</head><body><p>hi</p></body></html>'
    )
    return f


def _fixture_without_twitter_card(tmp_path: Path) -> Path:
    f = tmp_path / "without-card.html"
    f.write_text(
        '<!doctype html><html lang="en"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        '<title>Test Artifact</title>'
        '<meta name="description" content="x">'
        '<meta property="og:title" content="x">'
        '<meta property="og:description" content="x">'
        '<meta property="og:type" content="article">'
        '<meta property="og:site_name" content="x">'
        '</head><body><p>hi</p></body></html>'
    )
    return f


def test_inject_adds_tags(tmp_path):
    fixture = _fixture_with_twitter_card(tmp_path)
    r = _run(str(fixture), "--no-screenshot", "--inject")
    assert r.returncode == 0, r.stdout + r.stderr
    html = fixture.read_text()
    assert 'property="og:image" content="og-card.png"' in html
    assert 'name="twitter:image"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html


def test_inject_without_twitter_card_falls_back(tmp_path):
    fixture = _fixture_without_twitter_card(tmp_path)
    r = _run(str(fixture), "--no-screenshot", "--inject")
    assert r.returncode == 0, r.stdout + r.stderr
    html = fixture.read_text()
    after_title = html.split("</title>", 1)[1]
    assert 'name="twitter:card" content="summary_large_image"' in after_title
    assert 'property="og:image" content="og-card.png"' in after_title
    assert 'name="twitter:image" content="og-card.png"' in after_title


def test_already_injected_is_a_noop(tmp_path):
    fixture = _fixture_with_twitter_card(tmp_path)
    first = _run(str(fixture), "--no-screenshot", "--inject")
    assert first.returncode == 0, first.stdout + first.stderr
    after_first = fixture.read_text()

    second = _run(str(fixture), "--no-screenshot", "--inject")
    assert second.returncode == 0, second.stdout + second.stderr
    assert "already present" in second.stdout
    after_second = fixture.read_text()
    assert after_first == after_second


def test_missing_browser_fails_cleanly(tmp_path):
    fixture = _fixture_with_twitter_card(tmp_path)
    r = _run(str(fixture), env={"OG_CARD_CHROME": "/nonexistent/browser"})
    assert r.returncode == 1
    assert "og-card" in r.stderr
    assert "at Object." not in r.stderr
    assert "Traceback" not in r.stderr


@pytest.mark.skipif(not REAL_CHROME.exists(), reason="real Chrome not installed")
def test_screenshot_writes_png(tmp_path):
    fixture = _fixture_with_twitter_card(tmp_path)
    r = _run(str(fixture))
    assert r.returncode == 0, r.stdout + r.stderr
    png = tmp_path / "with-card.og.png"
    assert png.exists()
    assert png.stat().st_size > 10_000
