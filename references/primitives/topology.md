# Topology — inline service graph

Load before implementing or changing the topology primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/05-topology.html`.

- **Pick when:** connections are the point and node count is ≤30 (≤10 sits comfortably inline; 10–30 still works hand-positioned).
- **Required:** hand-positioned coordinates (force-directed wiggle earns its place at 30+); mono-uppercase node labels; paper-card node fill with a cluster-colored dot (never fill the node with category color — doesn't scale when clusters grow); edges meet rect boundaries (clip via center-offset math); right-rail inspector matching the editorial-shape entity pattern.
- **Interaction:** click a node to focus its neighborhood (dim others, light direct edges, update inspector); search ochre-highlights matches independently of focus; `× clear focus` resets.
- **Avoid:** force-directed simulations on small graphs; edges drawn center-to-center poking through node rects; SVG with no surrounding tile chrome.
