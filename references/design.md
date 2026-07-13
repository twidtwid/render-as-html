# Design System — Detailed Contract

Detailed design-system contract — loaded on demand via the preflight READ; the routing stub lives in SKILL.md §Design system.

### Layout principles

- **Max-width 1280px** on dashboards, 880px on documents, fluid below
- **Multi-column grids** for parallel content, NOT sequential h2 sections
- **Sticky top nav** with section anchors for docs >5 sections
- **Filter bar** when content is filterable — vanilla JS, no framework
- **Mobile is a hard requirement, not an afterthought.** Test by resizing browser to ~375px before saving — and also test the *intermediate* widths (~1100px, ~950px), where multi-zone layouts break worst. Cards stack to single column under ~700px, sticky nav collapses gracefully, touch targets ≥32px, horizontal scroll forbidden on body (tables in scroll containers OK), font sizes adjust down 1-2px.
- **Sticky-rail collapse invariant (any multi-zone shape — editorial, dashboard, document, network-map):** a `position: sticky` rail with a viewport-tall `height` is only safe while it owns a grid column. A sticky element keeps its own scroll box and paint layer even after the grid collapses, so if it stays sticky once its column is gone it renders *on top of* the prose. **Default to mobile-first:** rail is plain in-flow at base; attach `position: sticky` + the grid column together inside the wide `@media (min-width: …)` rule, so the failure state is unreachable by construction. Only if you went desktop-first must you reset to `position: static; height: auto` at every breakpoint the column is lost. A sticky *top/bottom bar* (full-width, no fixed height) is always safe — the hazard is exclusively a tall sticky *side rail* in a collapsing grid. **Footer corollary:** keep the page footer *outside* the grid that contains a sticky rail (a sibling after the grid container, not a `grid-column: 1/-1` child) — the rail's containing block is the grid, so an in-grid footer gets painted over by the still-pinned rail at scroll-bottom. **Scrollbox corollary:** any sticky side rail whose content can exceed the viewport MUST be a bounded scrollbox (`max-height: calc(100dvh - <top>); overflow-y: auto; overscroll-behavior: contain`) added in the same rule that makes it sticky — otherwise content past the fold is unreachable and any programmatic scroll-to-item is forced to drag the whole document. A click that cross-links between panels scrolls *the other* panel (minimally, `block:'nearest'`/no-op-if-visible), never the panel that was clicked. Verify at the breakpoint boundaries *and* at the very bottom of a long page, not just the extremes.

### Density

- **Reading register:** 17–18px serif body, line-height 1.6, prose measure capped at `46rem` (~70ch) even when chrome is wider. Section gap ~2.5rem. Real horizontal rules between sections, not boxed borders.
- **Instrument register:** 14–15px sans body, line-height 1.5, table cell padding `8px 10px`, packed. Stat tiles allowed *only* when the metric is the subject (see Content discipline, in "The bar").
- Headlines line-height 1.2 in both.

### Typography detail

- Mono is metadata/numerics/code in both registers. `font-variant-numeric: tabular-nums` on all tables and numeric columns.
- Reading register may use mono small-caps for kicker/eyebrow lines (e.g. `SAN FRANCISCO · 14 MAY 2021`).
- Instrument register uses serif sparingly or not at all (e.g. a single pull-quote), never for dense tabular content.

### Interactivity

**Every filter needs a visible clear path.** If clicking activates a filter, clicking again has to deactivate it (toggle), and a visible "× clear" affordance has to appear while the filter is active. Never rely on double-click, escape, or "click outside" to reset. Those gestures are undiscoverable.

**Use real controls for real actions.** When something needs to be toggleable, editable, pickable, or clickable, use a control that looks like one: `<input type="checkbox">`, `<input type="range">`, `<select>`, `<button>`. Don't invent gestures on decorative elements ("click this pill", "shift-click this badge", "double-tap this card"). Pills and badges and stat tiles read as static information; making them interactive is invisible and inscrutable. If a pill needs editing, put a real checkbox or button next to it. The pill stays read-only.

**Every copy button needs a fallback.** `navigator.clipboard.writeText()` can fail in local files, hardened browsers, iframes, and permission-restricted contexts. If copy fails, place the exact text in a visible `<textarea>`, focus it, and select it.

**In-text `<mark>` search.** When search filters content, mark the actual occurrences with `<mark>` and scroll to the first match. Never highlight an entire block because the term appears somewhere inside it; the visible part of a long block often does not contain the term. Cache original text (e.g. `data-original`) so clearing search restores cleanly.
