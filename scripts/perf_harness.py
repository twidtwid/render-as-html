#!/usr/bin/env python3
"""render-as-html performance + redundancy harness.

The "slow part" of this skill is NOT the one CLI (bin/render-podcast renders in
~0.03s). It is the *agent* path: a ~16k-token SKILL.md loaded in full on every
invocation, then 30-90KB of self-contained HTML emitted token-by-token, ~half of
which is re-derived design-system boilerplate. None of that is directly timeable
in CI, so this harness tracks the measurable *proxies* for it, plus a regression
guard on the CLI and the publish-correctness invariants:

  1. skill_md      — SKILL.md token load by ## section + per-shape/per-primitive
                     #### contract; always-needed vs on-demand-reference split.
  2. boilerplate   — % of each shape artifact's <style> that is boilerplate shared
                     across shapes (proxy for how much the agent re-derives).
  3. output_sizes  — byte size of every examples/*.html.
  4. cli           — bin/render-podcast wall-time + bytes on the repo fixture and a
                     synthetic-scaled fixture; asserts linear scaling under a ceiling.
  5. self_contained— zero external resource requests in any examples/*.html
                     (GitHub Pages publish invariant).

Usage:
    python3 scripts/perf_harness.py                 # report vs baseline, markdown to stdout
    python3 scripts/perf_harness.py --json          # full JSON report to stdout
    python3 scripts/perf_harness.py --update-baseline
    python3 scripts/perf_harness.py --check         # CI/pytest mode: exit nonzero on regression
    python3 scripts/perf_harness.py --fixture PATH  # also time the CLI on an ad-hoc package.json
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

# Sections that fire on every render regardless of shape (the always-loaded tax)
# vs sections that are per-shape / per-primitive reference material a single run
# only partially touches.
_REFERENCE_SECTIONS = {"Page shapes (pick before designing)", "Canonical primitives (charts and tables)"}


def analyze_skill() -> dict:
    text = SKILL.read_text(encoding="utf-8")
    total = tok(text)

    # Split on top-level "## " headings (keep the heading with its body).
    parts = re.split(r"\n(?=## )", text)
    sections = []
    always = reference = 0
    for part in parts:
        m = re.match(r"## (.+)", part)
        name = m.group(1).strip() if m else "(frontmatter)"
        t = tok(part)
        sections.append({"name": name, "tokens": t})
        if name in _REFERENCE_SECTIONS:
            reference += t
        else:
            always += t

    # Per-#### contract sizes within the two reference sections (shapes + primitives).
    contracts = []
    for part in parts:
        m = re.match(r"## (.+)", part)
        name = m.group(1).strip() if m else ""
        if name not in _REFERENCE_SECTIONS:
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
        "always_tokens": always,
        "reference_tokens": reference,
        "reference_pct": round(100 * reference / total, 1) if total else 0,
        "sections": sorted(sections, key=lambda s: -s["tokens"]),
        "contracts": sorted(contracts, key=lambda c: -c["tokens"]),
        "oversized_contracts": oversized,
    }


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


def analyze_cli(extra_fixture: Path | None = None) -> dict:
    runs = [_time_render(SMALL_FIXTURE, "repo-fixture")]
    with tempfile.TemporaryDirectory() as d:
        scaled = _make_scaled_fixture(20, Path(d) / "scaled.package.json")
        runs.append(_time_render(scaled, "synthetic-20x"))
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
    for p in sorted(EXAMPLES.glob("*.html")):
        html = p.read_text(encoding="utf-8")
        hits = []
        for rx in _EXTERNAL_RESOURCE_RES:
            for m in rx.finditer(html):
                hits.append(html[m.start():m.start() + 80].splitlines()[0])
        if hits:
            violations[p.name] = hits
    return {"clean": not violations, "violations": violations}


# ---------------------------------------------------------------------------
# Assemble, diff, report
# ---------------------------------------------------------------------------

def build_report(extra_fixture: Path | None = None) -> dict:
    return {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "skill_md": analyze_skill(),
        "boilerplate": analyze_boilerplate(),
        "output_sizes": analyze_sizes(),
        "cli": analyze_cli(extra_fixture),
        "self_contained": analyze_self_contained(),
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
    return out


def to_markdown(report: dict, baseline: dict | None) -> str:
    s, bp, cli = report["skill_md"], report["boilerplate"], report["cli"]
    L = ["# render-as-html perf harness", f"_generated {report['generated_at']}_", ""]
    delta = ""
    if baseline:
        b = baseline["skill_md"]["total_tokens"]
        if b:
            delta = f" ({'+' if s['total_tokens']>=b else ''}{round(100*(s['total_tokens']-b)/b,1)}% vs baseline)"
    L += [
        "## SKILL.md context load (per-invocation input tax)",
        f"- total: **{s['total_tokens']:,} tok** ({s['total_bytes']:,} B){delta}",
        f"- always-loaded: {s['always_tokens']:,} tok · on-demand reference: {s['reference_tokens']:,} tok ({s['reference_pct']}%)",
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
        BASELINE.write_text(json.dumps(report, indent=2) + "\n")
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
