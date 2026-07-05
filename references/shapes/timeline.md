# Timeline Shape Reference

Load before authoring or changing a `timeline`-shape artifact, or `examples/timeline.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail.

- **Register:** Reading (serif display + serif body; see §Design system / Density). Mono small-caps for date/kicker lines (e.g. `SAN FRANCISCO · 14 MAY 2021`).
- **Use for:** dated logs, diaries, retrospectives, project histories, trip journals — anything whose primary structure is *when*.
- **Layout:** a vertical spine on the left (~140px column for date markers + dots), event cards on the right (~720px). Max-width ~1000px. Sticky year/month group headers as you scroll.
- **First viewport:** title + a date-range scrubber + a search input + the most recent N events.
- **Required primitives:** the vertical spine line; date-marker dots on the spine; event cards (timestamp / title / body / tags); sticky year/month group headers; a jump-to-date picker; a per-event "copy as quote" button targeting the current `.html` path.
- **Density:** reading defaults; dense event cards (8–10px padding), ~12px gap between events. Cards stay narrow enough not to read as document paragraphs.
- **HTML-native ≥3:** live text search across events with `<mark>` highlight; date-range filter pills; cluster-collapse (month/year → count, expandable); tag-chip filter; per-event copy. Every filter has a visible `× clear`; counts reflect all events, not the filtered view.
- **Avoid:** decorative CV-style scroll animations; a wall of dates with no spine; event cards so wide they read as prose paragraphs.
