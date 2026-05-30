# Bar — ranked top-N

Load before implementing or changing the bar primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/02-bar.html`.

- **Pick when:** ≤12 items where order matters and a single magnitude per item is the signal.
- **Required:** name in its own subgrid column to the left of the bar (never on the bar with a text-shadow); ochre marks the current leader, terracotta the rest; bar / name / value / Δ subgrid aligns across rows; secondary dimension (Δ, age, score) gets its own right-edge column.
- **Interaction:** sort dropdown at minimum offers value, alpha, and the secondary dimension; bars re-scale to the new leader when sort changes.
- **Avoid:** text-shadow / outline glow on labels (illegible); per-bar rainbow coloring; bars without a max-width cap.
