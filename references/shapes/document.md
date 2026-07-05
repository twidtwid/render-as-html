# Document Shape Reference

Load before authoring or changing a `document`-shape artifact, or `examples/document.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail.

- **Register:** Reading (serif display + serif body, warm cream paper, terracotta accent; see §Design system / Density).
- **Use for:** plans, specs, briefings, essays, brainstorms, meeting notes — prose-heavy reference read paragraph-to-paragraph and navigated by section. (For a *sustained argument* with named entities worth a reference rail, use `editorial` instead.)
- **Layout:** max-width 880px, single column, with a sticky TOC sidebar on desktop. Prose measure capped at `46rem` (~70ch) even when chrome is wider. Real horizontal rules between sections, not boxed borders.
- **First viewport:** title, byline, a required TL;DR block, and a visible TOC.
- **Required primitives:** TL;DR block; sticky TOC sidebar with scroll-spy (the TOC follows the sticky-rail/scrollbox invariants in §Layout principles); footnote pattern (click-to-expand); inline dense tables where data is genuinely tabular; callouts (note/warn); a per-section copy-as-prompt button hover-revealed on each `h2`, targeting the current `.html` path.
- **Density:** reading defaults — 17–18px serif body, line-height 1.6, section gap ~2.5rem.
- **HTML-native ≥3:** TOC scroll-spy; per-section copy buttons; collapsible appendix; click-to-expand footnotes; optional in-text `<mark>` search (with prev/next nav if a count is shown).
- **Avoid:** dashboard-style multi-column grid; line length past ~70ch; corporate "executive summary card" headers; left-handle accent bars; category-label section titles ("Overview", "Key Points") — headlines should argue a position.
