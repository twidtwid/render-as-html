# Comparison Shape Reference

Load before authoring or changing a `comparison`-shape artifact, or `examples/comparison.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail. **The axis flip is the shape** — get it wrong and you've built a dashboard.

- **Register:** Instrument (sans display + sans body; see §Design system / Density).
- **Use for:** "X vs Y vs Z" decision matrices, model comparisons, vendor pickers — a trade-off across >2 options against shared criteria.
- **Layout:** items as **columns**, criteria as **rows** (this is the inversion vs dashboard, which puts entities in rows). A sticky header row carries the item names; a weight column sits on the far left; an aggregate-winner row sits at the bottom. Max-width 1280px.
- **First viewport:** title + TL;DR + the matrix with the weight column visible and the aggregate row in view.
- **Required primitives:** column-header item cards; criterion rows with a per-item value in each cell; per-row winner highlighting (background tint + ★); a weight input per criterion with a full-height +/− stepper flanking it; an aggregate-score footer that **live-recomputes** as weights change; a red→amber→green value scale for numerics (paired with text/position so it's not color-only); a "copy as recommendation" round-trip prompt with a visible textarea fallback. See `references/primitives/comparison-matrix.md`.
- **Density:** instrument defaults; dense cells (6–10px padding).
- **HTML-native ≥3:** live weight tuning recomputes per-row and overall winners; column sort by aggregate; a "must-have" criterion toggle that disqualifies failing items; copy-as-recommendation.
- **Avoid:** dashboard-style layout (entities as rows) — the axis flip *is* the point; tiny native spinner buttons; unbounded weights; "copy as markdown" implying another canonical format.
