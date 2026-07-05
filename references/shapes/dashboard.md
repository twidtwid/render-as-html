# Dashboard Shape Reference

Load before authoring or changing a `dashboard`-shape artifact, or `examples/dashboard.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail.

- **Register:** Instrument (sans display + sans body; see §Design system / Density).
- **Use for:** network scans, system reports, device lists, ops data — anything tabular with categories that benefit from filtering.
- **Layout:** max-width 1280px; a `1.4fr / 1fr` two-column grid (dense table left, charts/inspector right); a sticky controls row pinned at the top holding search + chip filters. Drops to single column under ~820px — and a sticky top bar is always safe, but any tall sticky side rail must follow the sticky-rail/scrollbox invariants in §Layout principles.
- **First viewport:** hero with stats tiles + search + chip filters + a one-line TL;DR. The tiles are content only when the metric *is* the subject (open ports, devices on file) — never artifact-production counts.
- **Required primitives:** search input; toggleable category chips (each with a visible active state + a global `× clear`); dense ops table with a mono first column; stat tiles; an inline-SVG donut; status pills (outline + dot + label, never color-only); one inline-SVG topology/diagram. Reach for the matching `references/primitives/*.md` when implementing one you're unsure of.
- **Density:** instrument defaults; `8px 10px` table cell padding, or `4–8px` for the compact variant.
- **HTML-native ≥3:** live filter; clickable cross-highlights (click a donut slice or chip → filter the table); inline charts; column-sort; copy buttons. Counts always reflect the underlying data, not the filtered view.
- **Avoid:** narrow centered column; generous whitespace; single-column scroll; generic h2/p/`<table>` layout with no interaction. If flattening to static text only loses an SVG, it's styled prose — add real filtering/cross-highlight.
