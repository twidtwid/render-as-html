# Scatter — two-dimension trade-off

Load before implementing or changing the scatter primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/10-scatter.html`.

- **Pick when:** two genuinely independent dimensions, both well-spread, across ≥10 points, where the *relationship* (correlation, trade-off, outliers, quadrants) is the signal — not a ranking. The classic case: cost vs. quality, latency vs. throughput, risk vs. reward.
- **Do NOT pick when:** points cluster tight on one or both axes, or there are ≤8 points — labels collide into an unreadable pile and the chart lies about spread. That is the 2026-05-25 omega-3 failure (8 supplements clustered in EPA 1860–2580 mg / $0.50–$3, five labels stacked on top of each other). **Rank them with `bar` instead.** A scatter is only honest when the cloud actually fills the plane.
- **Required:**
  - Both axes labeled with units and direction-of-good (e.g. `cheaper ← x → pricier`, `worse ↓ y ↑ better`); a log scale when one dimension spans >2 orders of magnitude (mark it `(log)` on the axis title).
  - **Median crosshair guides** splitting the cloud into four quadrants, with the median values labeled — this is what turns a dot soup into "cheap-and-good lives top-left."
  - Marker identity carried by **shape AND color**, never color alone (circle / square / triangle / diamond per group) so the plot survives colorblind viewing and greyscale screenshots.
  - Hover/focus detail: a point reveals name + both coordinates; a `<title>` child on each marker gives the same text to assistive tech and native tooltips. Points are keyboard-focusable (`tabindex="0"`).
- **Interaction:** toggle always-on labels (on for ≤15 points, off when dense so hover carries identity); toggle the median guides; hover or focus a point to pin a readout. Optional: brush/lasso to filter a region when the point count is high.
- **Avoid:** scatter for ranking (that is `bar`); always-on labels on a dense cloud (they collide — switch to hover-only); a third dimension smuggled in as bubble area unless it is genuinely needed and legended; an unscaled axis that crushes a long-tailed dimension into the corner (use log).

**Self-check before drawing:** plot the points mentally — if any two labels would overlap at always-on, either the data is too clustered for scatter (use `bar`) or labels must be hover-only. If the cloud hugs one axis, the second dimension isn't earning its place; rank instead.
