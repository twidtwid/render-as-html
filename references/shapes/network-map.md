# Network-map Shape Reference

Load before authoring or changing a `network-map`-shape artifact, or `examples/network-map.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail. **The graph is the primary view** — if you find yourself rendering a table of names with "connections: X, Y, Z", you've built a dashboard.

- **Register:** Instrument (sans display + sans body; see §Design system / Density).
- **Use for:** people/relationships, brain backlinks, dependencies — anything where the *connections* carry the meaning.
- **Layout:** a big graph canvas center (60–70% width), an entity-detail right rail (~280px), filter chips along the top. The right rail follows the sticky-rail/scrollbox invariants in §Layout principles.
- **First viewport:** the graph fitted to the viewport, filter chips above, a "click for details" hint.
- **Required primitives:** an SVG canvas with positioned nodes (hand-positioned for ≤30; a small vanilla force-directed sim only at 30+); edges; node sizing by importance; cluster color-coding (paired with label/shape, never color-only); a right-rail entity card that updates on click; top filter chips; search to focus; click-node-to-focus (dim non-neighbors, highlight direct edges). See `references/primitives/topology.md` for the inline-graph contract.
- **Focus-state invariant (load-bearing):** search-to-focus and click-to-focus MUST write the *same* focused-node state — both dim non-neighbors, highlight direct edges, and update the right-rail inspector. A search result that only highlights the SVG while leaving stale inspector text is broken. A visible `× clear focus` resets it.
- **HTML-native ≥3:** click-to-focus; hover-edge-highlight; search-to-focus; cluster toggle; optional shortest-path finder.
- **Avoid:** rendering as a table of names with a connections column (that's a dashboard); force-directed wiggle on small graphs; edges drawn center-to-center poking out of nodes; an unstyled SVG with no surrounding chrome.
