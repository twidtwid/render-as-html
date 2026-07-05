# Triage-board Shape Reference

Load before authoring or changing a `triage-board`-shape artifact, or `examples/triage-board.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail. **The horizontal columns WITH drag are the shape** — vertical lists with status badges are a dashboard.

- **Register:** Instrument (sans display + sans body; see §Design system / Density).
- **Use for:** bucketing items into 3–5 columns (Now / Next / Later / Cut), inbox triage, GTD reorg.
- **Layout:** title + a brief instruction + 3–5 column boards laid out horizontally, cards inside columns, a sticky export bar at the bottom (a full-width bottom bar is always safe per §Layout principles).
- **Required primitives:** column headers with a live count; draggable cards (HTML5 drag-and-drop, **vanilla — no React-DnD or any framework**); a per-card one-line rationale `<input>`; a pre-sorted suggested distribution at load (don't start with everything in one pile); a sticky copy/export + "copy as prompt" bar; undo.
- **Density:** instrument defaults; cards ~80–120px tall, columns ~240–320px wide.
- **HTML-native ≥3:** drag-between-columns; live column counts; copy-as-prompt exporting the final assignments (names the current `.html` path, delimits state as data, visible textarea fallback); undo; filter/search across all cards.
- **Mobile:** drag is hard on touch — provide a fallback (a per-card column `<select>` or move buttons) so the board is operable under ~700px where columns stack.
- **Avoid:** vertical lists with status badges (dashboard); a framework drag library; starting with no suggested distribution.
