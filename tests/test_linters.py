"""Tests for the two Node companion linters that cover surfaces the Python
perf harness can't:

  - scripts/check-tokens.mjs  — palette drift between DESIGN.md / SKILL.md / index.html
  - scripts/lint-artifact.mjs — mechanical pre-save checklist against a generated artifact

Run from the repo root:
    uv run --with pytest pytest tests/test_linters.py -v

Node is required (the repo already ships scripts/review-contracts.mjs); the tests
skip cleanly if node is unavailable.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not available")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


# --- check-tokens.mjs ---------------------------------------------------------

def test_check_tokens_clean():
    """DESIGN.md is the canonical source; SKILL.md §Color must match it exactly.
    A clean tree exits 0."""
    r = _run("scripts/check-tokens.mjs")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SKILL.md §Color matches DESIGN.md exactly" in r.stdout


def test_design_and_skill_share_canonical_palette():
    """The property check-tokens.mjs enforces: every canonical hex in DESIGN.md's
    frontmatter also lives in SKILL.md's §Color block."""
    import re

    design = (REPO / "DESIGN.md").read_text()
    fm = design.split("---", 2)[1]
    canonical = set(re.findall(r"#[0-9a-fA-F]{6}", fm))
    skill = (REPO / "SKILL.md").read_text()
    color_block = skill.split("\n### Color", 1)[1].split("\n### ", 1)[0]
    skill_hexes = set(re.findall(r"#[0-9a-fA-F]{6}", color_block))
    assert canonical and canonical == skill_hexes


# --- lint-artifact.mjs --------------------------------------------------------

def test_lint_artifact_passes_on_example():
    r = _run("scripts/lint-artifact.mjs", "examples/dashboard.html")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


def test_lint_artifact_passes_on_scatter_primitive():
    r = _run("scripts/lint-artifact.mjs", "examples/primitives/10-scatter.html")
    assert r.returncode == 0, r.stdout + r.stderr


def test_lint_artifact_fails_on_external_resource(tmp_path):
    bad = tmp_path / "bad.html"
    bad.write_text(
        '<!doctype html><html lang="en"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        '<meta name="description" content="x">'
        '<meta property="og:title" content="x">'
        '<meta property="og:description" content="x">'
        '<meta property="og:type" content="article">'
        '<meta property="og:site_name" content="x">'
        '<meta name="twitter:card" content="summary">'
        '<script src="https://cdn.example.com/x.js"></script>'
        '</head><body><svg></svg><input type="search"><table></table></body></html>'
    )
    r = _run("scripts/lint-artifact.mjs", str(bad))
    assert r.returncode == 1
    assert "external resource" in r.stdout


def test_lint_artifact_fails_on_missing_meta_and_features(tmp_path):
    bad = tmp_path / "thin.html"
    bad.write_text('<!doctype html><html lang="en"><head><title>t</title></head><body><p>hi</p></body></html>')
    r = _run("scripts/lint-artifact.mjs", str(bad))
    assert r.returncode == 1
    out = r.stdout
    assert "social-card meta" in out
    assert "HTML-native feature" in out
    assert "favicon" in out


def test_lint_artifact_flags_placeholder_path(tmp_path):
    bad = tmp_path / "ph.html"
    bad.write_text(
        '<!doctype html><html lang="en"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        '<meta name="description" content="x">'
        '<meta property="og:title" content="x">'
        '<meta property="og:description" content="x">'
        '<meta property="og:type" content="article">'
        '<meta property="og:site_name" content="x">'
        '<meta name="twitter:card" content="summary">'
        '</head><body><svg></svg><input type="search"><table></table>'
        '<textarea id="prompt-output"></textarea>'
        '<script>const p="In <artifact.html>, do x"; BEGIN ARTIFACT STATE DATA</script>'
        '</body></html>'
    )
    r = _run("scripts/lint-artifact.mjs", str(bad))
    assert r.returncode == 1
    assert "<artifact.html>" in r.stdout


def test_lint_artifact_longform_floor(tmp_path):
    small = tmp_path / "small.html"
    small.write_text(
        '<!doctype html><html lang="en"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        '<meta name="description" content="x">'
        '<meta property="og:title" content="x">'
        '<meta property="og:description" content="x">'
        '<meta property="og:type" content="article">'
        '<meta property="og:site_name" content="x">'
        '<meta name="twitter:card" content="summary">'
        '</head><body><svg></svg><input type="search"><table></table></body></html>'
    )
    ok = _run("scripts/lint-artifact.mjs", str(small))
    assert ok.returncode == 0  # passes without --longform
    flagged = _run("scripts/lint-artifact.mjs", "--longform", str(small))
    assert flagged.returncode == 1
    assert "long-form floor" in flagged.stdout


# --- check-versions.mjs -------------------------------------------------------

def test_check_versions_clean():
    """SKILL.md frontmatter is the canonical version; every release surface
    (README, index.html, gallery + podcast example footers, bin/render-podcast)
    must carry the same string."""
    r = _run("scripts/check-versions.mjs")
    assert r.returncode == 0, r.stdout + r.stderr


# --- review-contracts.mjs -----------------------------------------------------

def test_review_contracts_clean():
    """The repo-wide contract/a11y linter must pass on the committed tree.
    It scans index.html + examples/**/*.html."""
    r = _run("scripts/review-contracts.mjs")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "review contracts passed" in r.stdout


def test_review_contracts_nonzero_on_bad_tree(tmp_path):
    """Negative case: review-contracts resolves everything from cwd, so run it
    from a synthetic tree missing required files. It dies on the SKILL.md read
    before reaching the per-file meta checks (uncaught ENOENT), so the contract
    we can assert is "bad tree => nonzero exit" — which is what CI needs."""
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


# --- lint-artifact.mjs gate scoping (artifact vs reference page) ---------------

def test_lint_artifact_reference_flag_skips_feature_floor():
    """Single-primitive reference pages showcase one feature in isolation;
    --reference skips ONLY the >=3 feature floor. 02-bar.html must fail
    without the flag and pass with it (all other checks still run)."""
    without = _run("scripts/lint-artifact.mjs", "examples/primitives/02-bar.html")
    assert without.returncode == 1
    assert "HTML-native feature" in without.stdout
    with_flag = _run("scripts/lint-artifact.mjs", "--reference", "examples/primitives/02-bar.html")
    assert with_flag.returncode == 0, with_flag.stdout + with_flag.stderr


_META_HEAD = (
    '<!doctype html><html lang="en"><head>'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<link rel="icon" href="data:,">'
    '<meta name="description" content="x">'
    '<meta property="og:title" content="x">'
    '<meta property="og:description" content="x">'
    '<meta property="og:type" content="article">'
    '<meta property="og:site_name" content="x">'
    '<meta name="twitter:card" content="summary">'
    '</head><body>'
)


def test_lint_artifact_copy_prompt_trigger_needs_a_control(tmp_path):
    """A prose mention of "copy as prompt" is not a control and must not demand
    the BEGIN/END state delimiter; an actual <button>copy as prompt</button>
    without the delimiter must still fail."""
    prose = tmp_path / "prose.html"
    prose.write_text(
        _META_HEAD
        + '<p>hits "copy as prompt," and pastes a paragraph</p>'
        + '<svg></svg><input type="search"><table></table></body></html>'
    )
    r = _run("scripts/lint-artifact.mjs", str(prose))
    assert r.returncode == 0, r.stdout + r.stderr

    button = tmp_path / "button.html"
    button.write_text(
        _META_HEAD
        + '<button>Copy as prompt</button>'
        + '<svg></svg><input type="search"><table></table></body></html>'
    )
    r = _run("scripts/lint-artifact.mjs", str(button))
    assert r.returncode == 1
    assert "BEGIN/END ARTIFACT STATE DATA" in r.stdout


# --- tightened feature vocabulary: markup/behavior only, never prose words -----

def test_lint_artifact_prose_mentions_dont_count(tmp_path):
    """The feature floor is the load-bearing "is this a real artifact" test, so a
    detector must match MARKUP or BEHAVIORAL JS — never a prose word. This page
    says "search", "filter", "toggle", "sort", "highlight" and declares a CSS
    filter:, but has zero interactive markup. Under the old word-matching
    vocabulary it cleared the floor with 5 phantom features; it must now FAIL."""
    prose = tmp_path / "phantom.html"
    prose.write_text(
        _META_HEAD
        + "<style>p{filter:blur(0)}</style>"
        + "<p>You can search the archive, filter by team, toggle dark mode, "
        + "sort the sorted results, and we highlight the important bits.</p>"
        + "</body></html>"
    )
    r = _run("scripts/lint-artifact.mjs", str(prose))
    assert r.returncode == 1
    assert "HTML-native feature" in r.stdout


def test_lint_artifact_catches_compound_selector_dead_control(tmp_path):
    """querySelector('#a .b') — the old pattern's closing-quote anchor made the
    whole call invisible, so a dead compound reference shipped unchecked."""
    bad = tmp_path / "compound.html"
    bad.write_text(
        _META_HEAD
        + '<svg></svg><input type="search"><table></table>'
        + "<script>document.querySelector('#ghost .row');</script>"
        + "</body></html>"
    )
    r = _run("scripts/lint-artifact.mjs", str(bad))
    assert r.returncode == 1
    assert "#ghost" in r.stdout


def test_lint_artifact_catches_querySelectorAll_dead_control(tmp_path):
    """querySelectorAll was not scanned at all by the old pattern."""
    bad = tmp_path / "qsa.html"
    bad.write_text(
        _META_HEAD
        + '<svg></svg><input type="search"><table></table>'
        + "<script>document.querySelectorAll('#phantom');</script>"
        + "</body></html>"
    )
    r = _run("scripts/lint-artifact.mjs", str(bad))
    assert r.returncode == 1
    assert "#phantom" in r.stdout
