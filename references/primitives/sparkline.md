# Sparkline — stat-tile cluster

Load before implementing or changing the sparkline primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/03-sparkline.html`.

- **Pick when:** 2–4 hero metrics where each metric IS the subject (not an artifact count), current value + recent-trend shape is the one-glance read.
- **Required:** single accent color for the spark line across all tiles; delta carries direction-of-good (ok / accent / muted); latest-point dot is hollow (paper fill, accent stroke) so it reads as a marker, not a glitch; faint area fill (`opacity ~0.08`) is optional weight, not a true area chart.
- **Interaction:** hover the spark drops a vertical guide + value/time tooltip at the nearest data point.
- **Avoid:** 4+ tiles (cross into dashboard territory); stat tiles that count the artifact itself; axis tick marks per data point (tooltip carries precision).
