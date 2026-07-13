#!/usr/bin/env python3
"""render-as-html performance + redundancy harness.

The "slow part" of this skill is NOT the one CLI (bin/render-podcast renders in
~0.03s). It is the *agent* path: a ~16k-token SKILL.md loaded in full on every
invocation, then 30-90KB of self-contained HTML emitted token-by-token, ~half of
which is re-derived design-system boilerplate. None of that is directly timeable
in CI, so this harness tracks the measurable *proxies* for it, plus a regression
guard on the CLI and the publish-correctness invariants:

  1. skill_md      — SKILL.md token load by ## section + per-shape/per-primitive
                     #### contract. SKILL.md is loaded in full on every invocation;
                     the deferred load is references/*.md (see `references` below),
                     fetched per-shape/per-primitive via the preflight READ.
  2. boilerplate   — % of each shape artifact's <style> that is boilerplate shared
                     across shapes (proxy for how much the agent re-derives).
  3. output_sizes  — byte size of every examples/*.html.
  4. cli           — bin/render-podcast wall-time + bytes on the repo fixture, a
                     synthetic-scaled fixture, and a complex Lenny-style episode;
                     asserts linear scaling under a ceiling.
  5. self_contained— zero external resource requests in any examples/*.html
                     (GitHub Pages publish invariant).
  6. primitives    — each canonical primitive has a file, gallery link, and contract.
  7. source_doc    — examples keep HTML as the source document: local metadata,
                     blank favicon, no image-card promises without a hosted image,
                     no alternate-format copy affordances.

Usage:
    uv run python scripts/perf_harness.py                 # report vs baseline, markdown to stdout
    uv run python scripts/perf_harness.py --json          # full JSON report to stdout
    uv run python scripts/perf_harness.py --update-baseline
    uv run python scripts/perf_harness.py --check         # CI/pytest mode: exit nonzero on regression
    uv run python scripts/perf_harness.py --fixture PATH  # also time the CLI on an ad-hoc package.json
                                                          # (e.g. a complex real episode)

Token estimate is len(text)//4 — an approximation consistent with the measured
65,140 bytes / ~16,160 tokens of SKILL.md. stdlib only, no dependencies.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "SKILL.md"
EXAMPLES = REPO / "examples"
RENDERER = REPO / "bin" / "render-podcast"
SMALL_FIXTURE = REPO / "tests" / "fixtures" / "episode.package.json"
BASELINE = REPO / "perf" / "baseline.json"
REPORTS = REPO / "perf" / "reports"

# Top-level page-shape artifacts (the agent-authored set). primitives.html is a
# gallery shell and index.html is the nav page — both are size/self-containment
# tracked but excluded from the cross-shape boilerplate comparison.
SHAPE_FILES = [
    "dashboard.html", "document.html", "editorial.html", "timeline.html",
    "runbook.html", "comparison.html", "network-map.html", "triage-board.html",
    "developer.html", "podcast.html", "podcast-transcript.html", "checklist.html",
]

PRIMITIVE_FILES = {
    "donut": {
        "file": "examples/primitives/01-donut.html",
        "href": "primitives/01-donut.html",
        "contract": r"#### Donut\b",
    },
    "bar": {
        "file": "examples/primitives/02-bar.html",
        "href": "primitives/02-bar.html",
        "contract": r"#### Bar\b",
    },
    "sparkline": {
        "file": "examples/primitives/03-sparkline.html",
        "href": "primitives/03-sparkline.html",
        "contract": r"#### Sparkline\b",
    },
    "stacked-bar": {
        "file": "examples/primitives/04-stacked-bar.html",
        "href": "primitives/04-stacked-bar.html",
        "contract": r"#### Stacked bar\b",
    },
    "topology": {
        "file": "examples/primitives/05-topology.html",
        "href": "primitives/05-topology.html",
        "contract": r"#### Topology\b",
    },
    "dense-ops-table": {
        "file": "examples/primitives/06-table-ops.html",
        "href": "primitives/06-table-ops.html",
        "contract": r"#### Dense ops table\b",
    },
    "comparison-matrix": {
        "file": "examples/primitives/07-table-comparison.html",
        "href": "primitives/07-table-comparison.html",
        "contract": r"#### Comparison matrix\b",
    },
    "annotated-diff": {
        "file": "examples/primitives/08-diff.html",
        "href": "primitives/08-diff.html",
        "contract": r"#### Annotated diff\b",
    },
    "log-stream": {
        "file": "examples/primitives/09-logs.html",
        "href": "primitives/09-logs.html",
        "contract": r"#### Log stream\b",
    },
    "scatter": {
        "file": "examples/primitives/10-scatter.html",
        "href": "primitives/10-scatter.html",
        "contract": r"#### Scatter\b",
    },
}

# Public episode metadata, synthetic body text. This exercises a recent,
# long-form Lenny's Podcast episode without copying a transcript.
LENNY_URL = "https://www.lennysnewsletter.com/p/how-to-build-a-company-that-withstands"
LENNY_LABEL = "lenny-eric-ries-complex"
LENNY_TITLE = "How to build a company that withstands any era"
LENNY_PODCAST = "Lenny's Podcast: Product | Career | Growth"
LENNY_HOST = "Lenny Rachitsky"
LENNY_GUEST = "Eric Ries"
LENNY_PUBLISHED_AT = "2026-05-10"
LENNY_DURATION_SECONDS = (1 * 60 * 60) + (39 * 60) + 22

# Regression thresholds. Breaching a HARD one exits nonzero in --check mode.
SKILL_GROWTH_HARD = 0.05          # >5% SKILL.md token growth vs baseline
SHAPE_CONTRACT_WARN_TOK = 1500    # a single shape contract over this is a smell
CLI_CEILING_SECONDS = 0.5         # bin/render-podcast must stay well under this
LONGFORM_FLOOR_BYTES = 30_000     # SKILL's own pre-save heuristic for long-form shapes


def tok(text: str) -> int:
    """Approximate token count (chars / 4)."""
    return len(text) // 4


def _clean_path(p: Path) -> str:
    """Repo-relative path when under the repo, else bare basename. Never emit an
    absolute path — baseline.json is committed to a public repo (no /Users leak)."""
    try:
        return str(p.resolve().relative_to(REPO))
    except ValueError:
        return p.name


# ---------------------------------------------------------------------------
# 1. SKILL.md token load
# ---------------------------------------------------------------------------

# Sections that carry the per-shape / per-primitive #### contracts (used only to
# find the largest contracts within an always-loaded SKILL.md, not to split
# always-loaded vs deferred — every section here loads on every invocation).
_CONTRACT_SECTIONS = {"Page shapes (pick before designing)", "Canonical primitives (charts and tables)"}


def analyze_skill() -> dict:
    text = SKILL.read_text(encoding="utf-8")
    total = tok(text)

    # Split on top-level "## " headings (keep the heading with its body).
    parts = re.split(r"\n(?=## )", text)
    sections = []
    for part in parts:
        m = re.match(r"## (.+)", part)
        name = m.group(1).strip() if m else "(frontmatter)"
        t = tok(part)
        sections.append({"name": name, "tokens": t})

    # Per-#### contract sizes within the shape/primitive sections.
    contracts = []
    for part in parts:
        m = re.match(r"## (.+)", part)
        name = m.group(1).strip() if m else ""
        if name not in _CONTRACT_SECTIONS:
            continue
        subs = re.split(r"\n(?=#### )", part)
        for sub in subs:
            sm = re.match(r"#### (.+)", sub)
            if not sm:
                continue
            label = sm.group(1).strip().strip("`")
            contracts.append({"contract": label, "tokens": tok(sub)})

    oversized = [c for c in contracts if c["tokens"] > SHAPE_CONTRACT_WARN_TOK]
    return {
        "total_bytes": len(text.encode("utf-8")),
        "total_tokens": total,
        "sections": sorted(sections, key=lambda s: -s["tokens"]),
        "contracts": sorted(contracts, key=lambda c: -c["tokens"]),
        "oversized_contracts": oversized,
    }


# ---------------------------------------------------------------------------
# 1b. references/ token load (the actual deferred, per-shape/primitive load)
# ---------------------------------------------------------------------------

def analyze_references() -> dict:
    """references/*.md is fetched per-shape/per-primitive via the preflight READ —
    this is the real on-demand load, as opposed to SKILL.md which loads in full
    on every invocation."""
    files = sorted((REPO / "references").glob("**/*.md"))
    total = sum(tok(p.read_text(encoding="utf-8")) for p in files)
    return {"total_tokens": total, "file_count": len(files)}


# ---------------------------------------------------------------------------
# 2. Boilerplate redundancy
# ---------------------------------------------------------------------------

_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)


def _norm_style_lines(html: str) -> list[str]:
    """All <style> content, normalized to comparable lines (proxy for the
    design-system boilerplate that recurs across artifacts)."""
    out = []
    for block in _STYLE_RE.findall(html):
        for ln in block.splitlines():
            s = ln.strip()
            if s and not s.startswith("/*"):
                out.append(s)
    return out


def analyze_boilerplate() -> dict:
    per_file = {}
    line_sets = {}
    for name in SHAPE_FILES:
        p = EXAMPLES / name
        if not p.exists():
            continue
        lines = _norm_style_lines(p.read_text(encoding="utf-8"))
        line_sets[name] = set(lines)
        per_file[name] = {"style_lines": len(lines), "style_bytes": sum(len(l) for l in lines)}

    # A normalized style line is "boilerplate" if it appears in >=50% of shape files.
    counts: dict[str, int] = {}
    for s in line_sets.values():
        for ln in s:
            counts[ln] = counts.get(ln, 0) + 1
    n = max(len(line_sets), 1)
    common = {ln for ln, c in counts.items() if c >= n / 2}

    for name, s in line_sets.items():
        shared = len(s & common)
        per_file[name]["boilerplate_lines"] = shared
        per_file[name]["boilerplate_pct"] = round(100 * shared / len(s), 1) if s else 0

    avg = round(sum(f["boilerplate_pct"] for f in per_file.values()) / max(len(per_file), 1), 1)
    return {"common_boilerplate_lines": len(common), "avg_boilerplate_pct": avg, "per_file": per_file}


# ---------------------------------------------------------------------------
# 3. Output sizes
# ---------------------------------------------------------------------------

def analyze_sizes() -> dict:
    sizes = {p.name: p.stat().st_size for p in sorted(EXAMPLES.glob("*.html"))}
    longform = {"document.html", "editorial.html"}
    thin = {n: sizes[n] for n in longform if n in sizes and sizes[n] < LONGFORM_FLOOR_BYTES}
    return {"sizes": sizes, "longform_below_floor": thin}


# ---------------------------------------------------------------------------
# 4. CLI scaling
# ---------------------------------------------------------------------------

def _time_render(fixture: Path, label: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        t0 = time.perf_counter()
        r = subprocess.run(
            [sys.executable, str(RENDERER), str(fixture), "-o", d],
            capture_output=True, text=True,
        )
        elapsed = time.perf_counter() - t0
        out = Path(d)
        out_bytes = sum(f.stat().st_size for f in out.glob("*.html"))
    turns = 0
    try:
        turns = len(json.loads(fixture.read_text())["turns"])
    except Exception:
        pass
    return {
        "label": label, "fixture": _clean_path(fixture), "ok": r.returncode == 0,
        "seconds": round(elapsed, 4), "output_bytes": out_bytes, "turns": turns,
        "bytes_per_turn": round(out_bytes / turns, 1) if turns else None,
        "stderr": r.stderr.strip()[:400] if r.returncode != 0 else "",
    }


def _make_scaled_fixture(factor: int, dest: Path) -> Path:
    """Replicate the repo fixture's turns `factor`x to stress CLI scaling without
    shipping any external/branded content."""
    data = json.loads(SMALL_FIXTURE.read_text())
    base_turns = data["turns"]
    data["turns"] = [dict(t) for _ in range(factor) for t in base_turns]
    dest.write_text(json.dumps(data))
    return dest


def _fmt_ts(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _make_lenny_fixture(dest: Path) -> Path:
    """Build a synthetic stress package for the recent Lenny/Eric Ries episode.

    Only public episode metadata is real. The turn text below is synthetic
    scaffolding designed to exercise renderer size, chapters, terms, links, and
    repeated-speaker handling without copying a paid or copyrighted transcript.
    """
    themes = [
        ("era change", "A durable company has to keep learning when the market, capital environment, or platform shifts underneath it."),
        ("founder control", "The operating system matters more than the slogan because decisions reveal the actual company values."),
        ("customer gravity", "Teams withstand volatility when they stay close enough to customers to notice weak signals before they harden."),
        ("finance discipline", "Runway is a strategic variable: it buys time to compound insight and avoid reactive pivots."),
        ("mission clarity", "A mission only helps if it makes tradeoffs easier when growth, morale, or timing gets messy."),
        ("product cadence", "The best product loops turn experiments into institutional memory instead of one-off launches."),
        ("talent density", "Hiring for judgment compounds when people can disagree clearly and still commit to the operating rhythm."),
        ("board design", "Governance should create useful pressure without turning every uncertain quarter into theater."),
        ("brand trust", "Trust accumulates slowly across product decisions, support choices, pricing, and how leaders explain hard calls."),
        ("systems thinking", "Resilience comes from connected loops: strategy, execution, feedback, and capital have to reinforce each other."),
    ]
    prompts = [
        "Let me make that concrete.",
        "The pattern I keep seeing is this.",
        "There is a tactical version and a philosophical version.",
        "A lot of teams miss the sequencing.",
        "This is where incentives get very real.",
    ]
    turn_count = 220
    turns = []
    for i in range(turn_count):
        seconds = round(i * LENNY_DURATION_SECONDS / max(turn_count - 1, 1))
        theme, sentence = themes[i % len(themes)]
        speaker = LENNY_HOST if i % 5 in (0, 3) else LENNY_GUEST
        if speaker == LENNY_HOST:
            text = (
                f"{prompts[i % len(prompts)]} On {theme}, what should a founder "
                f"watch for before the obvious metrics start moving?"
            )
        else:
            text = (
                f"{sentence} The practical move is to write down the assumption, "
                f"assign an owner, and revisit it after the next customer or team signal."
            )
        turns.append({
            "id": f"turn-{i:03d}",
            "speaker": speaker,
            "timestamp": _fmt_ts(seconds),
            "text": text,
            "word_count": len(text.split()),
        })

    chapter_specs = [
        (0, "Why era-proofing is the job"),
        (24, "Mission as a decision system"),
        (52, "Customer gravity and weak signals"),
        (80, "Capital discipline without fear"),
        (108, "Product loops that remember"),
        (136, "Governance that creates useful pressure"),
        (164, "Hiring for judgment"),
        (192, "Trust as accumulated behavior"),
    ]
    chapters = []
    for ix, (turn_index, title) in enumerate(chapter_specs, start=1):
        chapters.append({
            "anchor_id": f"ch-{ix:02d}",
            "timestamp": turns[turn_index]["timestamp"],
            "title": title,
            "turn_index": turn_index,
            "turn_id": turns[turn_index]["id"],
        })

    data = {
        "schema_version": "podcast-transformer/package-v1",
        "schema": "podcast-transformer/package-v1",
        "episode": {
            "title": LENNY_TITLE,
            "short_title": "Company durability with Eric Ries",
            "podcast_title": LENNY_PODCAST,
            "episode_number": None,
            "episode_url": LENNY_URL,
            "description": "A complex synthetic fixture based on public metadata for Lenny Rachitsky's conversation with Eric Ries about company durability.",
            "published_at": LENNY_PUBLISHED_AT,
            "duration_seconds": LENNY_DURATION_SECONDS,
            "hosts": [LENNY_HOST],
            "guests": [LENNY_GUEST],
        },
        "bottom_line": "Companies withstand changing eras when mission, capital discipline, customer learning, and governance form one operating system.",
        "built_for": ["founders", "product leaders", "operators"],
        "takeaways": [
            "Treat durability as an operating system, not a motivational phrase.",
            "Use customer proximity to catch weak signals while they are still cheap to act on.",
            "Keep enough financial slack to choose deliberately under pressure.",
            "Turn experiments into institutional memory so learning compounds.",
            "Design governance that creates clarity instead of quarterly panic.",
            "Hire for judgment and disagreement quality, not just execution speed.",
            "Protect trust through repeated product and communication choices.",
            "Make mission specific enough to decide what not to do.",
        ],
        "claims": [
            {
                "topic": "Durability is designed",
                "claim": "Company resilience depends on connected operating loops, not a single heroic decision.",
                "evidence": "Synthetic fixture derived from the public episode title and guest context.",
            },
            {
                "topic": "Capital creates options",
                "claim": "Runway gives leaders time to preserve learning and avoid reactive pivots.",
                "evidence": "Synthetic fixture derived from the public episode title and guest context.",
            },
            {
                "topic": "Mission must decide",
                "claim": "A mission earns its keep only when it clarifies tradeoffs under pressure.",
                "evidence": "Synthetic fixture derived from the public episode title and guest context.",
            },
            {
                "topic": "Learning must persist",
                "claim": "Experiments matter most when their results change future decisions.",
                "evidence": "Synthetic fixture derived from the public episode title and guest context.",
            },
        ],
        "terms": [
            {"category": "People", "name": LENNY_HOST, "notes": "Host of Lenny's Podcast.", "url": "https://www.lennysnewsletter.com/"},
            {"category": "People", "name": LENNY_GUEST, "notes": "Entrepreneur and author associated with Lean Startup ideas.", "url": "https://theleanstartup.com/"},
            {"category": "Concepts", "name": "Mission clarity", "notes": "A decision filter that survives hard tradeoffs."},
            {"category": "Concepts", "name": "Customer gravity", "notes": "Staying close enough to customers for weak signals to matter."},
            {"category": "Concepts", "name": "Runway", "notes": "Time and capital available for deliberate choices."},
            {"category": "Concepts", "name": "Governance pressure", "notes": "Board and leadership structures that sharpen decisions."},
            {"category": "Books", "name": "The Lean Startup", "notes": "Eric Ries's book on validated learning.", "url": "https://theleanstartup.com/"},
            {"category": "Organizations", "name": "Lenny's Newsletter", "notes": "Publisher of the public episode page.", "url": LENNY_URL},
        ],
        "chapters": chapters,
        "turns": turns,
        "links": [
            {"url": LENNY_URL, "label": "Public episode page", "note": "Episode metadata and source page."},
            {"url": "https://www.lennysnewsletter.com/", "label": "Lenny's Newsletter", "note": "Podcast and newsletter home."},
            {"url": "https://theleanstartup.com/", "label": "The Lean Startup", "note": "Eric Ries's related work."},
        ],
        "outputs": {
            "summary_html": "podcast-at-a-glance.html",
            "annotated_transcript_html": "annotated-transcript.html",
        },
    }
    dest.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    return dest


def analyze_cli(extra_fixture: Path | None = None) -> dict:
    runs = [_time_render(SMALL_FIXTURE, "repo-fixture")]
    with tempfile.TemporaryDirectory() as d:
        scaled = _make_scaled_fixture(20, Path(d) / "scaled.package.json")
        runs.append(_time_render(scaled, "synthetic-20x"))
        lenny = _make_lenny_fixture(Path(d) / "lenny-eric-ries.package.json")
        runs.append(_time_render(lenny, LENNY_LABEL))
    if extra_fixture and extra_fixture.exists():
        runs.append(_time_render(extra_fixture, "ad-hoc"))
    slowest = max((r["seconds"] for r in runs), default=0)
    return {"runs": runs, "slowest_seconds": slowest, "ceiling_seconds": CLI_CEILING_SECONDS,
            "all_ok": all(r["ok"] for r in runs), "under_ceiling": slowest < CLI_CEILING_SECONDS}


# ---------------------------------------------------------------------------
# 5. Self-containment (publish invariant)
# ---------------------------------------------------------------------------

# Resource-LOADING external refs are violations. Anchor href="https://..." is
# navigation, not a request, so it is allowed and not matched here.
_EXTERNAL_RESOURCE_RES = [
    re.compile(r"<script[^>]+src=['\"]https?:", re.I),
    re.compile(r"<link[^>]+href=['\"]https?:", re.I),
    re.compile(r"<img[^>]+src=['\"]https?:", re.I),
    re.compile(r"<source[^>]+src=['\"]https?:", re.I),
    re.compile(r"@import\s+['\"]?https?:", re.I),
    re.compile(r"url\(\s*['\"]?https?:", re.I),
    re.compile(r"fetch\(\s*['\"]https?:", re.I),
]


def analyze_self_contained() -> dict:
    violations = {}
    for p in _html_artifact_files():
        html = p.read_text(encoding="utf-8")
        hits = []
        for rx in _EXTERNAL_RESOURCE_RES:
            for m in rx.finditer(html):
                hits.append(html[m.start():m.start() + 80].splitlines()[0])
        if hits:
            violations[_clean_path(p)] = hits
    return {"clean": not violations, "violations": violations}


# ---------------------------------------------------------------------------
# 6. Primitive registry coverage
# ---------------------------------------------------------------------------

def analyze_primitives() -> dict:
    skill = SKILL.read_text(encoding="utf-8")
    gallery = (EXAMPLES / "primitives.html").read_text(encoding="utf-8")
    violations: list[str] = []
    rows = []
    for name, spec in PRIMITIVE_FILES.items():
        file_path = REPO / spec["file"]
        has_file = file_path.exists()
        has_gallery_link = spec["href"] in gallery
        has_contract = re.search(spec["contract"], skill, re.I) is not None
        if not has_file:
            violations.append(f"{name}: missing {spec['file']}")
        if not has_gallery_link:
            violations.append(f"{name}: gallery missing link {spec['href']}")
        if not has_contract:
            violations.append(f"{name}: SKILL.md missing contract {spec['contract']}")
        rows.append({
            "name": name,
            "file": spec["file"],
            "has_file": has_file,
            "has_gallery_link": has_gallery_link,
            "has_contract": has_contract,
        })

    candidates = []
    if re.search(r"\bscatter\b", skill, re.I) and "scatter" not in PRIMITIVE_FILES:
        candidates.append("scatter")
    return {
        "clean": not violations,
        "violations": violations,
        "primitives": rows,
        "candidate_new_primitives": candidates,
    }


# ---------------------------------------------------------------------------
# 7. HTML-as-source-document audit
# ---------------------------------------------------------------------------

_REQUIRED_META = [
    ("name", "description"),
    ("property", "og:title"),
    ("property", "og:description"),
    ("property", "og:type"),
    ("property", "og:site_name"),
    ("name", "twitter:card"),
]

_HTML_NATIVE_FEATURES = {
    "search": r"type=[\"']search[\"']",
    "inline_svg": r"<svg\b",
    "table": r"<table\b",
    "copy_as_prompt": r"copy as prompt|copyPrompt|prompt-output",
    "sorting": r"data-sort|aria-sort=",
    "filtering": r"data-filter|class=[\"'][^\"']*\bchip\b",
    "local_storage": r"localStorage",
    "drag": r"\bdraggable\b|dragstart|dragover|drop\(",
    "toggle": r"aria-pressed|type=[\"']checkbox[\"']",
    "textarea": r"<textarea\b",
    "cross_highlight": r"scrollIntoView|IntersectionObserver|classList\.(?:add|toggle)\(",
}


def _html_artifact_files() -> list[Path]:
    files = [REPO / "index.html"]
    files.extend(sorted(EXAMPLES.glob("*.html")))
    files.extend(sorted((EXAMPLES / "primitives").glob("*.html")))
    return sorted(files)


def _has_meta(html: str, attr: str, value: str) -> bool:
    return re.search(rf"<meta\b[^>]*{attr}=[\"']{re.escape(value)}[\"'][^>]*>", html, re.I) is not None


def _feature_hits(html: str) -> list[str]:
    return [name for name, pattern in _HTML_NATIVE_FEATURES.items() if re.search(pattern, html, re.I)]


def analyze_source_document() -> dict:
    violations: list[str] = []
    feature_counts = {}
    feature_hits = {}

    for p in _html_artifact_files():
        rel = _clean_path(p)
        html = p.read_text(encoding="utf-8")
        hits = _feature_hits(html)
        feature_hits[rel] = hits
        feature_counts[rel] = len(hits)

        if not re.search(r"<html\b[^>]*\blang=[\"']en[\"']", html, re.I):
            violations.append(f"{rel}: missing <html lang=\"en\">")
        if not re.search(r"<link\b[^>]*\brel=[\"']icon[\"'][^>]*\bhref=[\"']data:,[\"'][^>]*>", html, re.I):
            violations.append(f"{rel}: missing blank data favicon")
        for attr, value in _REQUIRED_META:
            if not _has_meta(html, attr, value):
                violations.append(f"{rel}: missing {value} meta")
        if re.search(r"\bog:image\b|\btwitter:image\b|summary_large_image", html, re.I):
            violations.append(f"{rel}: image-card metadata in self-contained artifact")
        if re.search(r"<(?:button|a)\b[^>]*>[^<]*copy as markdown", html, re.I):
            violations.append(f"{rel}: copy-as-markdown control implies a non-HTML canonical format")
        if "<artifact.html>" in html:
            violations.append(f"{rel}: placeholder artifact path leaked into generated HTML")

    for file, hits in analyze_self_contained()["violations"].items():
        violations.append(f"{file}: external resource refs: {hits[:2]}")

    renderer_source = RENDERER.read_text(encoding="utf-8")
    for bad in ("summary_large_image", "og:image", "twitter:image"):
        if bad in renderer_source:
            violations.append(f"bin/render-podcast: generated renderer contains {bad}")

    low_feature_files = {
        name: count for name, count in feature_counts.items()
        if name.startswith("examples/")
        and Path(name).name in SHAPE_FILES
        and count < 3
    }
    return {
        "clean": not violations,
        "violations": violations,
        "html_native_feature_counts": feature_counts,
        "html_native_feature_hits": feature_hits,
        "low_feature_files": low_feature_files,
    }


# ---------------------------------------------------------------------------
# Assemble, diff, report
# ---------------------------------------------------------------------------

def build_report(extra_fixture: Path | None = None) -> dict:
    return {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "skill_md": analyze_skill(),
        "references": analyze_references(),
        "boilerplate": analyze_boilerplate(),
        "output_sizes": analyze_sizes(),
        "cli": analyze_cli(extra_fixture),
        "self_contained": analyze_self_contained(),
        "primitives": analyze_primitives(),
        "source_document": analyze_source_document(),
    }


def regressions(report: dict, baseline: dict | None) -> list[str]:
    """Hard regressions -> nonzero exit in --check mode."""
    out = []
    cli = report["cli"]
    if not cli["all_ok"]:
        out.append("CLI: bin/render-podcast failed on at least one fixture")
    if not cli["under_ceiling"]:
        out.append(f"CLI: slowest render {cli['slowest_seconds']}s exceeds {CLI_CEILING_SECONDS}s ceiling")
    if not report["self_contained"]["clean"]:
        files = ", ".join(report["self_contained"]["violations"])
        out.append(f"SELF-CONTAINMENT: external resource refs in {files}")
    prim = report.get("primitives")
    if prim and not prim["clean"]:
        out.append("PRIMITIVES: " + "; ".join(prim["violations"]))
    src = report.get("source_document")
    if src and not src["clean"]:
        out.append("SOURCE-DOCUMENT: " + "; ".join(src["violations"]))
    if baseline:
        b = baseline["skill_md"]["total_tokens"]
        c = report["skill_md"]["total_tokens"]
        if b and (c - b) / b > SKILL_GROWTH_HARD:
            out.append(f"SKILL.md token load grew {round(100*(c-b)/b,1)}% ({b}->{c}), > {int(SKILL_GROWTH_HARD*100)}% budget")
    return out


def warnings(report: dict) -> list[str]:
    out = []
    for c in report["skill_md"]["oversized_contracts"]:
        out.append(f"oversized contract: {c['contract']} = {c['tokens']} tok (> {SHAPE_CONTRACT_WARN_TOK})")
    for name, sz in report["output_sizes"]["longform_below_floor"].items():
        out.append(f"long-form {name} = {sz}B below {LONGFORM_FLOOR_BYTES}B floor (possible feature loss)")
    for name, count in report["source_document"].get("low_feature_files", {}).items():
        out.append(f"{name} has only {count} HTML-native feature hits (<3 source-document heuristic)")
    return out


def to_markdown(report: dict, baseline: dict | None) -> str:
    s, bp, cli = report["skill_md"], report["boilerplate"], report["cli"]
    refs = report["references"]
    prim, src = report["primitives"], report["source_document"]
    L = ["# render-as-html perf harness", f"_generated {report['generated_at']}_", ""]
    delta = ""
    if baseline:
        b = baseline["skill_md"]["total_tokens"]
        if b:
            delta = f" ({'+' if s['total_tokens']>=b else ''}{round(100*(s['total_tokens']-b)/b,1)}% vs baseline)"
    L += [
        "## SKILL.md context load (per-invocation input tax)",
        f"- total: **{s['total_tokens']:,} tok** ({s['total_bytes']:,} B){delta}",
        f"- always-loaded (all of SKILL.md): {s['total_tokens']:,} tok",
        f"- deferred to references/ (loaded per-shape/primitive on demand): {refs['total_tokens']:,} tok across {refs['file_count']} files",
        "- largest contracts:",
    ]
    L += [f"    - {c['contract']}: {c['tokens']} tok" for c in s["contracts"][:6]]
    L += ["", "## Boilerplate redundancy (agent re-derivation proxy)",
          f"- shared-across-shapes style lines: {bp['common_boilerplate_lines']}",
          f"- avg shape artifact is **{bp['avg_boilerplate_pct']}%** boilerplate", ""]
    L += ["## CLI scaling (bin/render-podcast)"]
    for r in cli["runs"]:
        L.append(f"- {r['label']}: {r['seconds']}s · {r['output_bytes']:,}B · {r['turns']} turns"
                 + (f" · {r['bytes_per_turn']}B/turn" if r["bytes_per_turn"] else ""))
    L.append(f"- slowest {cli['slowest_seconds']}s vs {cli['ceiling_seconds']}s ceiling: "
             + ("OK" if cli["under_ceiling"] else "FAIL"))
    L += ["", "## Self-containment",
          "- " + ("clean — zero external resource requests" if report["self_contained"]["clean"]
                  else f"VIOLATIONS: {report['self_contained']['violations']}")]
    L += ["", "## Primitive coverage",
          f"- registry: {sum(1 for p in prim['primitives'] if p['has_file'] and p['has_gallery_link'] and p['has_contract'])}/{len(prim['primitives'])} complete",
          "- " + ("clean — every primitive has a file, gallery link, and contract" if prim["clean"]
                  else f"VIOLATIONS: {prim['violations']}")]
    if prim["candidate_new_primitives"]:
        L.append(f"- candidate new primitives: {', '.join(prim['candidate_new_primitives'])}")
    medianish = sorted(src["html_native_feature_counts"].values())
    median_count = medianish[len(medianish) // 2] if medianish else 0
    L += ["", "## HTML source-document contract",
          "- " + ("clean — metadata, favicon, source-document copy controls, and image-card rules hold" if src["clean"]
                  else f"VIOLATIONS: {src['violations']}"),
          f"- median HTML-native feature hits per artifact: {median_count}"]
    w = warnings(report)
    if w:
        L += ["", "## Warnings"] + [f"- {x}" for x in w]
    r = regressions(report, baseline)
    if r:
        L += ["", "## REGRESSIONS"] + [f"- {x}" for x in r]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="render-as-html perf + redundancy harness")
    ap.add_argument("--json", action="store_true", help="emit full JSON report to stdout")
    ap.add_argument("--update-baseline", action="store_true", help="write perf/baseline.json from this run")
    ap.add_argument("--check", action="store_true", help="CI mode: exit nonzero on hard regression")
    ap.add_argument("--no-report", action="store_true", help="do not write perf/reports/<date>.json")
    ap.add_argument("--fixture", type=Path, default=None, help="ad-hoc package.json to also time the CLI on")
    args = ap.parse_args(argv)

    report = build_report(args.fixture)
    baseline = json.loads(BASELINE.read_text()) if BASELINE.exists() else None

    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        slim = {"skill_md": report["skill_md"], "references": report["references"]}
        BASELINE.write_text(json.dumps(slim, indent=2) + "\n")
        print(f"baseline written: {BASELINE}")
        return 0

    if not args.no_report:
        REPORTS.mkdir(parents=True, exist_ok=True)
        stamp = report["generated_at"].replace(":", "").replace("-", "")
        (REPORTS / f"{stamp}.json").write_text(json.dumps(report, indent=2) + "\n")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(to_markdown(report, baseline))

    regs = regressions(report, baseline)
    if args.check and regs:
        print("\nperf harness: HARD REGRESSIONS — failing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
