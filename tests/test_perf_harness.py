"""Regression gate built on scripts/perf_harness.py.

Run from the repo root:
    python3 -m pytest tests/test_perf_harness.py -v

These assert the publish + perf invariants the harness measures:
  - examples make zero external resource requests (GitHub Pages publish rule),
  - bin/render-podcast stays under its time ceiling and scales,
  - SKILL.md token load has not regressed beyond budget vs the committed baseline.
The committed perf/baseline.json is the reference; refresh it deliberately with
`python3 scripts/perf_harness.py --update-baseline` when an intended change moves
the numbers.
"""
from __future__ import annotations
import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARNESS = REPO / "scripts" / "perf_harness.py"
BASELINE = REPO / "perf" / "baseline.json"


def _load_harness():
    loader = SourceFileLoader("perf_harness", str(HARNESS))
    spec = importlib.util.spec_from_loader("perf_harness", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["perf_harness"] = mod
    loader.exec_module(mod)
    return mod


def test_examples_are_self_contained():
    h = _load_harness()
    sc = h.analyze_self_contained()
    assert sc["clean"], f"examples must make zero external resource requests: {sc['violations']}"


def test_cli_under_ceiling_and_scales():
    h = _load_harness()
    cli = h.analyze_cli()
    assert cli["all_ok"], "bin/render-podcast must render every fixture cleanly"
    assert cli["under_ceiling"], f"slowest render {cli['slowest_seconds']}s exceeds {cli['ceiling_seconds']}s"


def test_skill_token_load_within_budget():
    h = _load_harness()
    if not BASELINE.exists():
        return  # no baseline committed yet — nothing to regress against
    baseline = json.loads(BASELINE.read_text())
    report = {"skill_md": h.analyze_skill(), "cli": h.analyze_cli(),
              "self_contained": h.analyze_self_contained()}
    regs = h.regressions(report, baseline)
    assert not regs, "perf harness hard regressions: " + "; ".join(regs)
